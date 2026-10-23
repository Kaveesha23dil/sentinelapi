"""Query local monitoring without putting a bearer value into shell history."""
import argparse
import getpass
import json
import os
from urllib.parse import urlencode
from uuid import UUID

from wso2_http import Client


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('view', choices=['overview', 'events', 'health', 'stats'])
    parser.add_argument('--api-id', type=UUID)
    parser.add_argument('--start')
    parser.add_argument('--end')
    parser.add_argument('--page', type=int, default=1)
    parser.add_argument('--page-size', type=int, default=50)
    args = parser.parse_args()
    if args.view == 'stats' and args.api_id is None:
        parser.error('--api-id is required for stats (use database API service UUID)')
    path = f'apis/{args.api_id}/stats' if args.view == 'stats' else args.view
    params = {key: str(value) for key, value in vars(args).items() if key in ['start', 'end', 'page', 'page_size', 'api_id'] and value is not None}
    token = os.getenv('MONITORING_API_TOKEN') or getpass.getpass('Monitoring token (hidden): ')
    status, body = Client().request('GET', 'http://127.0.0.1:8010/api/v1/monitoring/'+path+'?'+urlencode(params), token=token)
    print(f'HTTP {status}')
    print(json.dumps(body, indent=2))
    return 0 if status == 200 else 1


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception:
        print('FAIL: local monitoring query; details and credentials withheld.')
        raise SystemExit(1)
