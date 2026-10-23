"""Inspect/enable BASIC logs only for the already-discovered DemoCommerce API."""
import argparse
import json
import os
from pathlib import Path

from wso2_http import Client
from wso2_local_auth import basic, container_admin


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ca-file', default=os.getenv('WSO2_CA_FILE'))
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--report', type=Path, default=Path('infrastructure/telemetry/logging-configuration.json'))
    args = parser.parse_args()
    previous = json.loads(Path('infrastructure/database/gateway-precheck.json').read_text())
    if previous['name'] != 'DemoCommerceAPI':
        raise ValueError('Unexpected API identity')
    client = Client(args.ca_file)
    username, password = container_admin()
    headers = {'Authorization': basic(username, password)}
    url = 'https://localhost:9443/api/am/devops/v0/tenant-logs/carbon.super/apis/' + previous['api_id']
    before = client.json('GET', url, headers=headers)
    if args.apply:
        client.json('PUT', url, headers=headers, payload={'logLevel': 'BASIC'})
    after = client.json('GET', url, headers=headers)
    report = {'api_id': previous['api_id'], 'before': before, 'after': after, 'applied': args.apply}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print(f'FAIL: BASIC log configuration ({type(error).__name__}); secrets withheld.')
        raise SystemExit(1)
