"""Collect bounded, sanitized runtime evidence; never dump container environments."""
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import time
import tempfile

from bridge_api_logs import Config, LOGS
from traffic_collector.identity import event_id
from traffic_collector.parser import parse
from verify_telemetry_e2e import compose
from wso2_http import Client

ROOT = Path(__file__).resolve().parents[1]


def main():
    settings = json.loads((ROOT/'infrastructure/database/gateway-precheck.json').read_text())
    config = Config(settings['api_id'], settings['name'], settings['context'], settings['version'])
    private = dict(line.split('=', 1) for line in (ROOT/'.env').read_text().splitlines() if '=' in line and not line.startswith('#'))
    token = private['MONITORING_API_TOKEN']
    client = Client()
    base = 'http://127.0.0.1:8010/api/v1/monitoring'
    statuses = []
    gateway_client = Client(str(Path(tempfile.gettempdir())/'sentinelapi-wso2-public.pem'))
    for credential in [None, 'invalid-local-test']:
        status, _ = gateway_client.request('GET', settings['gateway_url']+'/api/v1/orders', token=credential)
        statuses.append(status)
    if statuses != [401, 401]:
        raise AssertionError('Gateway negative authentication regression')
    raw = subprocess.run(['docker', 'exec', 'sentinelapi-wso2', 'tail', '-c', '65536', LOGS+'/api.log'],
                         capture_output=True, check=True, text=True).stdout
    flows = [flow for line in raw.splitlines() if (flow := parse(line, config))]
    expected = {str(event_id(flow, config.api_id)) for flow in flows if flow['flow'] == 'RESPONSE_OUT'}
    for _ in range(45):
        health, _ = client.request('GET', base+'/health', token=token)
        seen = set()
        if health == 200:
            for page in range(1, 11):
                response = client.json('GET', base+f'/events?page_size=100&page={page}', token=token)
                seen.update(event['event_id'] for event in response['events'])
                if expected <= seen or page*100 >= response['total']:
                    break
        if expected and expected <= seen:
            break
        time.sleep(1)
    if health != 200 or not expected or not expected <= seen:
        raise AssertionError('Source/monitoring matching or freshness failed')
    database = json.loads(compose('run', '--rm', '-T', '--no-deps', 'telemetry-tests', 'python', '-m',
                                  'traffic_collector.verify_db', data=json.dumps(sorted(expected)).encode()).stdout)
    if database['count'] != len(expected):
        raise AssertionError('Source/database mismatch')
    containers = {}
    for name in ['sentinelapi-wso2', 'sentinelapi-democommerce', 'sentinelapi-postgres', 'sentinelapi-collector', 'sentinelapi-monitoring']:
        state = json.loads(subprocess.run(['docker', 'inspect', name, '--format', '{{json .State}}'], capture_output=True, check=True, text=True).stdout)
        containers[name] = {'running': state['Running'], 'health': state.get('Health', {}).get('Status', 'not-configured')}
    ports = json.loads(subprocess.run(['docker', 'inspect', 'sentinelapi-postgres', '--format', '{{json .NetworkSettings.Ports}}'], capture_output=True, check=True, text=True).stdout)
    if any(ports.values()):
        raise AssertionError('Database host port exposed')
    if not all(state['running'] for state in containers.values()):
        raise AssertionError('Expected container is stopped')
    report = {'checked_at_utc': datetime.now(timezone.utc).isoformat(), 'passed': True,
              'source_scope': 'last 64 KiB of current api.log; configured API only',
              'source_flow_counts': dict(Counter(flow['flow'] for flow in flows)),
              'unique_completed_source_records': len(expected), 'matched_database_records': database['count'],
              'matched_monitoring_records': len(expected & seen), 'all_measurements_null': database['measurements_null'],
              'monitoring_health_status': health, 'overview': client.json('GET', base+'/overview', token=token),
              'gateway_no_token_and_malformed_statuses': statuses, 'containers': containers,
              'postgres_published_ports': ports}
    (ROOT/'infrastructure/telemetry/runtime-status.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print(f'FAIL: runtime telemetry status ({type(error).__name__}); details redacted.')
        raise SystemExit(1)
