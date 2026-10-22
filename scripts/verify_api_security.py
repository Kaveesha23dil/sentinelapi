"""Read-only local gateway security checks. Tokens stay in process memory."""
import argparse
import getpass
import json
import os
import socket
import errno
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode, urlsplit

from smoke_wso2_gateway import validate_gateway_url
from wso2_http import Client
from wso2_local_auth import basic


def check_oauth(client, base, token):
    results = []
    for name, credential, expected in [
        ('no_token', None, 401), ('malformed_token', 'invalid.local.test', 401),
        ('valid_token', token, 200),
    ]:
        status, body = client.request('GET', base + '/api/v1/orders', token=credential)
        passed = status == expected and (name != 'valid_token' or isinstance(body, list))
        results.append({'test': name, 'actual': status, 'expected': expected, 'passed': passed})
    return results


def check_throttle(client, base, token, *, limit=25, pause=time.sleep):
    statuses = []
    for _ in range(limit):
        status, _ = client.request('GET', base + '/api/v1/orders', token=token)
        statuses.append(status)
        if status == 429:
            return {'test': 'throttling', 'statuses': statuses, 'passed': 200 in statuses}
        if status != 200:
            break
        pause(0.25)
    return {'test': 'throttling', 'statuses': statuses, 'passed': False}


def check_isolation():
    # Refusal alone is insufficient: require no published Docker bindings and
    # successful health from the actual WSO2 container as well.
    bindings = subprocess.run(
        ['docker', 'inspect', 'sentinelapi-democommerce', '--format',
         '{{json .NetworkSettings.Ports}}'], capture_output=True, check=True, text=True)
    ports = json.loads(bindings.stdout)
    with socket.socket() as connection:
        connection.settimeout(3)
        host_closed = connection.connect_ex(('127.0.0.1', 8000)) in {errno.ECONNREFUSED, 10061}
    internal = subprocess.run(
        ['docker', 'exec', 'sentinelapi-wso2', 'curl', '--fail', '--silent',
         '--show-error', '--max-time', '15', 'http://democommerce:8000/health'],
        capture_output=True, check=True, text=True)
    healthy = json.loads(internal.stdout).get('status') == 'healthy'
    return {'test': 'backend_isolation', 'host_connection_refused': host_closed,
            'no_published_ports': not any(ports.values()), 'internal_health': healthy,
            'passed': host_closed and not any(ports.values()) and healthy}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--gateway-url', required=True)
    parser.add_argument('--ca-file', default=os.getenv('WSO2_CA_FILE'))
    parser.add_argument('--results', type=Path, required=True)
    parser.add_argument('--throttle', action='store_true',
                        help='Use only with a dedicated low-quota application (max 25 GETs)')
    args = parser.parse_args()
    base = validate_gateway_url(args.gateway_url)
    parsed = urlsplit(base)
    if parsed.hostname != 'localhost' or parsed.port != 8243:
        parser.error('This test is restricted to HTTPS localhost:8243')
    client = Client(args.ca_file)
    report = {'checked_at_utc': datetime.now(timezone.utc).isoformat(),
              'passed': False, 'tests': [], 'optional': {}}
    token = None
    client_id = os.getenv('WSO2_CLIENT_ID') or getpass.getpass('OAuth client ID (hidden): ')
    secret = os.getenv('WSO2_CLIENT_SECRET') or getpass.getpass('OAuth client secret (hidden): ')
    try:
        issued = client.json('POST', 'https://localhost:9443/oauth2/token',
                             headers={'Authorization': basic(client_id, secret),
                                      'Content-Type': 'application/x-www-form-urlencoded'},
                             data=urlencode({'grant_type': 'client_credentials'}).encode())
        token = issued['access_token']
        report['tests'].extend(check_oauth(client, base, token))
        report['tests'].append(check_isolation())
        for name, variable, expected in [('expired_token', 'WSO2_EXPIRED_TOKEN', 401),
                                         ('unsubscribed_token', 'WSO2_UNSUBSCRIBED_TOKEN', 403)]:
            optional = os.getenv(variable)
            if optional:
                status, _ = client.request('GET', base + '/api/v1/orders', token=optional)
                report['tests'].append({'test': name, 'actual': status,
                                        'expected': expected, 'passed': status == expected})
            else:
                report['optional'][name] = 'pending: runtime token not supplied'
        if args.throttle:
            report['tests'].append(check_throttle(client, base, token))
        else:
            report['tests'].append({'test': 'throttling', 'passed': False,
                                    'reason': 'not requested; low-quota application required'})
        report['passed'] = all(row['passed'] for row in report['tests'])
    except Exception:
        report['failure'] = 'Check Docker access, TLS trust, OAuth credentials and deployment. Secrets withheld.'
    finally:
        if token:
            try:
                client.json('POST', 'https://localhost:9443/oauth2/revoke',
                            headers={'Authorization': basic(client_id, secret),
                                     'Content-Type': 'application/x-www-form-urlencoded'},
                            data=urlencode({'token': token}).encode())
                report['token_revocation_submitted'] = True
            except Exception:
                report['token_revocation_submitted'] = False
                report['passed'] = False
        args.results.write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps(report, indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
