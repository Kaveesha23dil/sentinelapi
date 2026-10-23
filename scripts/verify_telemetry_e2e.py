"""Real local gateway -> BASIC log -> spool -> PostgreSQL -> authenticated API proof."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from urllib.parse import urlencode, urlsplit
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'collector'))
from traffic_collector.config import Config
from traffic_collector.identity import event_id
from traffic_collector.parser import parse
from bridge_api_logs import LOGS, poll
from wso2_http import Client
from wso2_local_auth import basic, management_token

ROOT = Path(__file__).resolve().parents[1]
DEV = 'https://localhost:9443/api/am/devportal/v3'


def compose(*arguments, data=None, check=True):
    return subprocess.run(['docker', 'compose', *arguments], input=data,
                          capture_output=True, check=check, cwd=ROOT)


def drain(config):
    # A running host bridge may briefly own the source-checkpoint lock.
    for attempt in range(15):
        try:
            return poll(config)
        except OSError:
            if attempt == 14:
                raise
            time.sleep(1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ca-file', default=os.getenv('WSO2_CA_FILE'))
    args = parser.parse_args()
    evidence = ROOT/'infrastructure/telemetry/e2e-verification.json'
    report = {'passed': False, 'started_at_utc': datetime.now(timezone.utc).isoformat()}
    evidence.write_text(json.dumps(report) + '\n')
    settings = json.loads((ROOT/'infrastructure/database/gateway-precheck.json').read_text())
    config = Config(settings['api_id'], settings['name'], settings['context'], settings['version'])
    gateway = settings['gateway_url']
    if urlsplit(gateway).hostname != 'localhost' or urlsplit(gateway).port != 8243:
        raise ValueError('Local gateway only')
    private = dict(line.split('=', 1) for line in (ROOT/'.env').read_text().splitlines() if '=' in line and not line.startswith('#'))
    monitoring_token = os.getenv('MONITORING_API_TOKEN') or private['MONITORING_API_TOKEN']
    client = Client(args.ca_file)
    management, _ = management_token(client, from_container=True)
    app_id = settings['application_id']
    key_list = client.json('GET', DEV+f'/applications/{app_id}/oauth-keys', token=management)['list']
    mappings = [key for key in key_list if key['keyType'] == 'PRODUCTION']
    if len(mappings) != 1:
        raise ValueError('Expected one existing production key mapping')
    key = client.json('GET', DEV+f'/applications/{app_id}/oauth-keys/'+mappings[0]['keyMappingId'], token=management)
    issued = client.json('POST', 'https://localhost:9443/oauth2/token',
        headers={'Authorization': basic(key['consumerKey'], key['consumerSecret']),
                 'Content-Type': 'application/x-www-form-urlencoded'},
        data=urlencode({'grant_type': 'client_credentials'}).encode())
    token = issued['access_token']
    try:
        start = datetime.now(timezone.utc).isoformat()
        correlations, statuses = [], []
        for path, authenticated, expected in [('/api/v1/orders', True, 200)]*4 + [
            ('/api/v1/orders/2147483647', True, 404), ('/api/v1/orders', False, 401)]:
            correlation = str(uuid4())
            correlations.append(correlation)
            status, _ = client.request('GET', gateway+path, token=token if authenticated else None,
                                       headers={'activityid': correlation})
            statuses.append(status)
            if status != expected:
                raise AssertionError('Gateway status mismatch')
        source = []
        for _ in range(15):
            raw = subprocess.run(['docker', 'exec', 'sentinelapi-wso2', 'tail', '-c', '65536', LOGS+'/api.log'],
                                 capture_output=True, check=True, text=True).stdout
            source = [flow for line in raw.splitlines() if (flow := parse(line, config))
                      and flow['correlation_id'] in correlations]
            completed = [flow for flow in source if flow['flow'] == 'RESPONSE_OUT']
            if len(completed) == 6:
                break
            time.sleep(1)
        expected_ids = {str(event_id(flow, config.api_id)) for flow in completed}
        if len(expected_ids) != 6:
            raise AssertionError('Six unique gateway response records not observed')
        drain(config)
        end = datetime.now(timezone.utc).isoformat()
        params = urlencode({'start': start, 'end': end, 'page_size': 100})
        base = 'http://127.0.0.1:8010/api/v1/monitoring'
        for _ in range(30):
            page = client.json('GET', base+'/events?'+params, token=monitoring_token)
            api_ids = {row['event_id'] for row in page['events']}
            if expected_ids <= api_ids:
                break
            time.sleep(1)
        if api_ids != expected_ids or page['total'] != 6:
            raise AssertionError('Source and monitoring API counts differ')
        before = client.json('GET', base+'/overview?'+params, token=monitoring_token)
        if before['request_count'] != 6:
            raise AssertionError('Overview count differs')
        no_auth, _ = client.request('GET', base+'/events')
        invalid_auth, _ = client.request('GET', base+'/events', token='invalid-local-test')
        if (no_auth, invalid_auth) != (401, 401):
            raise AssertionError('Monitoring authentication failed')
        db = json.loads(compose('run', '--rm', '-T', '--no-deps', 'telemetry-tests',
            'python', '-m', 'traffic_collector.verify_db', data=json.dumps(sorted(expected_ids)).encode()).stdout)
        if set(db['event_ids']) != expected_ids:
            raise AssertionError('Database event identities differ')
        compose('restart', 'collector')
        payload = json.dumps({'flows': completed}).encode()
        compose('run', '--rm', '-T', '--no-deps', 'log-transport', data=payload)
        chunk_data = ''.join(json.dumps(flow, sort_keys=True)+'\n' for flow in completed).encode()
        filename = hashlib.sha256(chunk_data).hexdigest()+'.ndjson'
        for _ in range(30):
            acknowledgment = compose('exec', '-T', 'collector', 'python', '-m',
                                      'traffic_collector.checkpoint', filename, check=False)
            if acknowledgment.returncode == 0:
                break
            time.sleep(1)
        if acknowledgment.returncode != 0:
            raise AssertionError('Replay batch not checkpointed')
        after = client.json('GET', base+'/events?'+params, token=monitoring_token)
        after_db = json.loads(compose('run', '--rm', '-T', '--no-deps', 'telemetry-tests',
            'python', '-m', 'traffic_collector.verify_db', data=json.dumps(sorted(expected_ids)).encode()).stdout)
        if after['total'] != 6 or after_db['count'] != 6:
            raise AssertionError('Collector restart/replay changed request count')
        report.update(passed=True, gateway_statuses=statuses, source_flow_counts=dict(Counter(flow['flow'] for flow in source)),
            source_unique_response_count=len(expected_ids), database=db, monitoring_event_count=page['total'],
            overview=before, restart_replay_checkpointed=True, post_restart_database_count=after_db['count'],
            post_restart_api_count=after['total'], monitoring_no_token_status=no_auth,
            monitoring_invalid_token_status=invalid_auth, event_ids=sorted(expected_ids))
    finally:
        client.json('POST', 'https://localhost:9443/oauth2/revoke',
            headers={'Authorization': basic(key['consumerKey'], key['consumerSecret']),
                     'Content-Type': 'application/x-www-form-urlencoded'},
            data=urlencode({'token': token}).encode())
        report['token_revocation_submitted'] = True
        evidence.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print(f'FAIL: real telemetry proof ({type(error).__name__}); no secrets displayed. Check saved incomplete report and service health.')
        raise SystemExit(1)
