"""Authenticated loopback probe with allowlisted, credential-free diagnostics."""
import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def check_health():
    token = os.getenv('MONITORING_API_TOKEN', '')
    if len(token) < 32 or token.startswith('REPLACE_WITH_'):
        return 'authentication-not-configured'
    request = Request('http://127.0.0.1:8001/api/v1/monitoring/health',
                      headers={'Authorization': 'Bearer ' + token})
    try:
        try:
            response = urlopen(request, timeout=5)
        except HTTPError as error:
            response = error
        with response:
            if response.status in (401, 403):
                return 'authentication-rejected'
            if response.status not in (200, 503):
                return 'http-error'
            body = json.loads(response.read(4096))
            if not isinstance(body, dict):
                return 'unexpected-response'
            if (response.status == 200 and body.get('database') == 'available'
                    and body.get('collector') == 'healthy'):
                return 'healthy'
            if body.get('database') == 'available' and body.get('collector') == 'stale-or-unavailable':
                return 'collector-stale'
            return 'database-or-service-unavailable'
    except (URLError, OSError):
        return 'connection-failed'
    except (ValueError, TypeError):
        return 'unexpected-response'


def main():
    state = check_health()
    print('monitoring_health state=' + state)
    return 0 if state == 'healthy' else 1


if __name__ == '__main__':
    raise SystemExit(main())
