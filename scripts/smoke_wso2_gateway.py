"""Verify OAuth enforcement and backend routing; never prints bearer tokens."""

import argparse
import getpass
import json
import os
from pathlib import Path
from urllib.parse import urlsplit
from uuid import uuid4

from wso2_http import Client


def validate_gateway_url(url):
    parsed = urlsplit(url)
    if (parsed.scheme != 'https' or not parsed.hostname or parsed.username
            or parsed.password or parsed.query or parsed.fragment):
        raise ValueError('Use an HTTPS API base URL without credentials, query or fragment')
    return url.rstrip('/')


def run_smoke(client, gateway_url, token, backend_url=None):
    base = validate_gateway_url(gateway_url)
    if not token or any(c.isspace() for c in token):
        raise ValueError('A nonempty bearer token without whitespace is required')
    results = []

    def check(name, method, path, expected, *, authenticated=True, payload=None):
        status, body = client.request(
            method, base + path, token=token if authenticated else None,
            payload=payload, headers={'X-SentinelAPI-Smoke-ID': str(uuid4())},
        )
        result = {'test': name, 'expected': expected, 'actual': status,
                  'passed': status == expected}
        results.append(result)
        print(f'{name}: HTTP {status}; expected {expected}')
        if status != expected:
            raise AssertionError(f'{name} failed (HTTP {status})')
        return body

    check('orders_without_token', 'GET', '/api/v1/orders', 401, authenticated=False)
    orders = check('orders_with_token', 'GET', '/api/v1/orders', 200)
    if not isinstance(orders, list):
        raise AssertionError('Orders response is not a JSON array')
    payload = {'user_id': 1, 'items': [{'product_id': 101, 'quantity': 2}]}
    created = check('create_order', 'POST', '/api/v1/orders', 201, payload=payload)
    if (not isinstance(created, dict) or not isinstance(created.get('id'), int)
            or created.get('user_id') != 1 or created.get('items') != payload['items']
            or str(created.get('total_amount')) != '99.98'):
        raise AssertionError('Created order does not match the backend contract')
    # A valid integer outside the backend's current order ID range.
    missing_id = max([created['id']] + [o['id'] for o in orders]) + 1000000
    missing = check('nonexistent_order', 'GET', f'/api/v1/orders/{missing_id}', 404)
    if missing != {'detail': 'Order not found'}:
        raise AssertionError('404 response did not originate from the expected backend')
    fetched = check('read_created_order', 'GET', f"/api/v1/orders/{created['id']}", 200)
    if fetched != created:
        raise AssertionError('Gateway read-back differs from the created order')
    if backend_url:
        status, direct = client.request(
            'GET', backend_url.rstrip('/') + f"/api/v1/orders/{created['id']}")
        passed = status == 200 and direct == created
        results.append({'test': 'backend_read_back', 'actual': status, 'passed': passed})
        if not passed:
            raise AssertionError('Direct backend read-back did not match gateway-created order')
        print('backend_read_back: HTTP 200; matches gateway-created order')
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--gateway-url', default=os.getenv('WSO2_GATEWAY_URL'),
                        help='Actual API base URL from Developer Portal, including context/version')
    parser.add_argument('--ca-file', default=os.getenv('WSO2_CA_FILE'))
    parser.add_argument('--backend-url', default='http://localhost:8000')
    parser.add_argument('--results', type=Path, help='Optional redacted JSON result file')
    args = parser.parse_args()
    if not args.gateway_url:
        parser.error('--gateway-url or WSO2_GATEWAY_URL is required; do not guess the route')
    validate_gateway_url(args.gateway_url)
    token = os.getenv('WSO2_TEST_TOKEN') or getpass.getpass('Short-lived API token (hidden): ')
    results = run_smoke(Client(args.ca_file), args.gateway_url, token, args.backend_url)
    if args.results:
        args.results.write_text(json.dumps({'passed': True, 'tests': results}, indent=2) + '\n')
    print(f'PASS: {len(results)} gateway/backend checks. One in-memory test order was created.')


if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, ValueError, AssertionError, OSError):
        # Avoid printing exceptions that could include headers or credentials.
        print('FAIL: gateway verification incomplete. Check status lines, TLS trust, token and deployment.')
        raise SystemExit(1)
