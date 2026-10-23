"""Controlled local PostgreSQL outage; always restart the existing database."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from urllib.parse import urlencode
from uuid import uuid4

from bridge_api_logs import LOGS, poll
from verify_telemetry_e2e import compose, DEV
from traffic_collector.config import Config
from traffic_collector.identity import event_id
from traffic_collector.parser import parse
from wso2_http import Client
from wso2_local_auth import basic, management_token

ROOT = Path(__file__).resolve().parents[1]


def checkpoint_digest():
    return compose('exec', '-T', 'collector', 'python', '-c',
                   "import hashlib;from pathlib import Path;print(hashlib.sha256(Path('/state/completed.json').read_bytes()).hexdigest())").stdout.decode().strip()


def main():
    report = {'passed': False}
    evidence = ROOT/'infrastructure/telemetry/outage-verification.json'
    evidence.write_text(json.dumps(report)+'\n')
    config_data = json.loads((ROOT/'infrastructure/database/gateway-precheck.json').read_text())
    config = Config(config_data['api_id'], config_data['name'], config_data['context'], config_data['version'])
    private = dict(line.split('=', 1) for line in (ROOT/'.env').read_text().splitlines() if '=' in line and not line.startswith('#'))
    client = Client(os.getenv('WSO2_CA_FILE'))
    management, _ = management_token(client, from_container=True)
    app = DEV+'/applications/'+config_data['application_id']
    mappings = client.json('GET', app+'/oauth-keys', token=management)['list']
    mapping = [key for key in mappings if key['keyType'] == 'PRODUCTION'][0]
    key = client.json('GET', app+'/oauth-keys/'+mapping['keyMappingId'], token=management)
    token = client.json('POST', 'https://localhost:9443/oauth2/token',
        headers={'Authorization': basic(key['consumerKey'], key['consumerSecret']),
                 'Content-Type': 'application/x-www-form-urlencoded'},
        data=urlencode({'grant_type': 'client_credentials'}).encode())['access_token']
    try:
        # Drain and checkpoint existing input before comparing the outage ledger.
        poll(config)
        time.sleep(3)
        before = checkpoint_digest()
        compose('stop', '-t', '5', 'postgres')
        correlation = str(uuid4())
        status, _ = client.request('GET', config_data['gateway_url']+'/api/v1/orders', token=token,
                                   headers={'activityid': correlation})
        if status != 200:
            raise AssertionError('Gateway invocation failed during database outage')
        completed = []
        for _ in range(15):
            raw = subprocess.run(['docker', 'exec', 'sentinelapi-wso2', 'tail', '-c', '65536', LOGS+'/api.log'], capture_output=True, check=True, text=True).stdout
            completed = [flow for line in raw.splitlines() if (flow := parse(line, config))
                         and flow['correlation_id'] == correlation and flow['flow'] == 'RESPONSE_OUT']
            if len(completed) == 1:
                break
            time.sleep(1)
        if len(completed) != 1:
            raise AssertionError('Real response not observed')
        identifier = str(event_id(completed[0], config.api_id))
        poll(config)
        time.sleep(5)
        unavailable, _ = client.request('GET', 'http://127.0.0.1:8010/api/v1/monitoring/events',
                                        token=private['MONITORING_API_TOKEN'])
        unchanged = checkpoint_digest() == before
        if unavailable != 503 or not unchanged:
            raise AssertionError('Outage did not preserve checkpoint or return 503')
        compose('start', 'postgres')
        for _ in range(45):
            status, body = client.request('GET', 'http://127.0.0.1:8010/api/v1/monitoring/events?page_size=100',
                                          token=private['MONITORING_API_TOKEN'])
            if status == 200 and identifier in {row['event_id'] for row in body['events']}:
                break
            time.sleep(1)
        if status != 200 or identifier not in {row['event_id'] for row in body['events']}:
            raise AssertionError('Queued gateway event not recovered')
        database = json.loads(compose('run', '--rm', '-T', '--no-deps', 'telemetry-tests',
            'python', '-m', 'traffic_collector.verify_db', data=json.dumps([identifier]).encode()).stdout)
        if database['count'] != 1:
            raise AssertionError('Recovered database event count mismatch')
        report.update(passed=True, gateway_status_during_outage=200, monitoring_status_during_outage=unavailable,
                      collector_checkpoint_unchanged=unchanged, recovered_event_id=identifier, recovered_database_count=1,
                      recovered_monitoring_status=status)
    finally:
        compose('start', 'postgres', check=False)
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
        print(f'FAIL: outage proof ({type(error).__name__}); existing PostgreSQL restart attempted, details redacted.')
        raise SystemExit(1)
