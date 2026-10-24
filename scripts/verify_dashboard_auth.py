"""Read-only live auth/data checks. Never emit tokens, response bodies or driver errors."""
import argparse
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import subprocess
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from uuid import UUID

ROOT = Path(__file__).resolve().parents[1]


def private_environment():
    values = {}
    for line in (ROOT / '.env').read_text().splitlines():
        if line and not line.startswith('#') and '=' in line:
            key, value = line.split('=', 1)
            values[key] = value.strip().strip('\"\'')
    return values


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--docker', default='docker')
    parser.add_argument('--origin', default='http://localhost:8010')
    args = parser.parse_args()
    values = private_environment()
    for key in ['MONITORING_API_TOKEN', 'SECURITY_READER_TOKEN']:
        token = values.get(key, '')
        valid = len(token) >= 32 and not token.startswith('REPLACE_WITH_')
        print(key + ': ' + ('CONFIGURED' if valid else 'MISSING'))
        assert valid

    def docker(*command, data=None):
        result = subprocess.run([args.docker, *command], input=data, capture_output=True, text=True)
        if result.returncode:
            raise RuntimeError('Docker verification failed; diagnostics withheld')
        return result.stdout.strip()

    def sql(query):
        return json.loads(docker('exec', '-i', 'sentinelapi-postgres', 'psql', '-X', '-q', '-tA',
            '-v', 'ON_ERROR_STOP=1', '-U', values['POSTGRES_USER'], '-d', values['POSTGRES_DB'],
            data='BEGIN READ ONLY; ' + query + '; COMMIT;'))

    def request(path, token=None, expected=200, patch=None):
        headers = {'Authorization': 'Bearer ' + token} if token else {}
        if patch is not None:
            headers['Content-Type'] = 'application/json'
        req = Request(args.origin + path, headers=headers,
                      data=json.dumps(patch).encode() if patch is not None else None,
                      method='PATCH' if patch is not None else 'GET')
        try:
            response = urlopen(req, timeout=15)
        except HTTPError as error:
            response = error
        with response:
            print(req.method, path.split('?')[0], response.status)
            assert response.status == expected
            return json.load(response)

    monitor, reader = values['MONITORING_API_TOKEN'], values['SECURITY_READER_TOKEN']
    for path in ['/api/v1/monitoring/session', '/api/v1/security/session']:
        request(path, expected=401)
        request(path, 'invalid', expected=401)
    request('/api/v1/monitoring/session', monitor)
    assert request('/api/v1/security/session', reader)['role'] == 'reader'
    request('/api/v1/security/session', monitor, expected=401)
    request('/api/v1/monitoring/session', reader, expected=401)
    request('/api/v1/monitoring/health', monitor)
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=30)
    params = '?' + urlencode({'start': start.isoformat(), 'end': end.isoformat()})
    summary = request('/api/v1/monitoring/overview' + params, monitor)
    events = request('/api/v1/monitoring/events' + params, monitor)
    alerts = request('/api/v1/security/alerts' + params, reader)
    rules = request('/api/v1/security/rules', reader)
    services = request('/api/v1/monitoring/services' + params, monitor)
    windows = request('/api/v1/ml/anomalies' + params, reader)
    model = request('/api/v1/ml/model', reader)
    query = f"""SELECT json_build_object(
        'requests',(SELECT count(*) FROM traffic_events WHERE source='wso2-gateway'
          AND timestamp >= '{start.isoformat()}' AND timestamp < '{end.isoformat()}'),
        'alerts',(SELECT count(*) FROM security_alerts WHERE last_detected_at >= '{start.isoformat()}'
          AND last_detected_at < '{end.isoformat()}'),
        'events_all',(SELECT count(*) FROM traffic_events),
        'evidence_all',(SELECT count(*) FROM alert_evidence),
        'ml_windows',(SELECT count(*) FROM ml_windows))"""
    counts = sql(query)
    assert summary['request_count'] == events['total'] == counts['requests']
    assert alerts['total'] == counts['alerts']
    for alert in alerts['alerts']:
        identity = str(UUID(alert['id']))
        detail = request('/api/v1/security/alerts/' + identity, reader)
        linked = request('/api/v1/security/alerts/' + identity + '/events', reader)
        request('/api/v1/security/alerts/' + identity + '/history', reader)
        assert len(detail['evidence']) == sql(
            f"SELECT count(*) FROM alert_evidence WHERE alert_id='{identity}'")
        print('Alert origin:', detail['origin'], 'evidence:', len(detail['evidence']),
              'linked events:', len(linked['events']))
        request('/api/v1/security/alerts/' + identity, reader, expected=403, patch={'status': 'resolved'})
    if rules['rules']:
        identity = str(UUID(rules['rules'][0]['id']))
        request('/api/v1/security/rules/' + identity, reader, expected=403, patch={'enabled': False})
    print('Read-only SQL cross-check:', json.dumps(counts))
    print('Services:', ', '.join(item['name'] for item in services['services']))
    print('Rules:', rules['total'], 'ML anomalies:', windows['total'], 'ML model:', model['state'])
    print(docker('exec', 'sentinelapi-monitoring', 'python', '-m', 'sentinelapi.monitoring.healthcheck'))
    print('Docker monitoring health:', docker('inspect', 'sentinelapi-monitoring',
                                             '--format', '{{.State.Health.Status}}'))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        print('FAIL: live verification incomplete; diagnostics withheld to protect credentials.')
        raise SystemExit(1)
