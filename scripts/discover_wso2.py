"""Read authenticated Publisher inventory and validate the actual OpenAPI export."""

import argparse
import getpass
import json
import os
from pathlib import Path
from uuid import uuid4

from wso2_http import Client


def multipart(fields):
    boundary = 'SentinelAPI' + uuid4().hex
    data = b''
    for name, value in fields.items():
        data += (f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"'
                 '\r\n\r\n').encode() + value.encode() + b'\r\n'
    return data + f'--{boundary}--\r\n'.encode(), {'Content-Type': f'multipart/form-data; boundary={boundary}'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ca-file', default=os.getenv('WSO2_CA_FILE'))
    parser.add_argument('--spec', type=Path,
                        default=Path('infrastructure/wso2/democommerce-openapi.json'))
    args = parser.parse_args()
    client = Client(args.ca_file)
    token = os.getenv('WSO2_PUBLISHER_TOKEN') or getpass.getpass('Publisher OAuth token (hidden): ')
    base = 'https://localhost:9443/api/am/publisher/v4'
    # Paginate the entire authorized catalog to avoid missing unpublished APIs.
    offset = 0
    matches = []
    while True:
        page = client.json('GET', base + f'/apis?limit=100&offset={offset}', token=token)
        for api in page['list']:
            if api['name'] == 'DemoCommerceAPI' or api.get('context', '').startswith('/democommerce'):
                matches.append({key: api.get(key) for key in
                                ['id', 'name', 'version', 'context', 'lifeCycleStatus']})
        offset += len(page['list'])
        if not page['list'] or offset >= page.get('pagination', {}).get('total', offset):
            break
    print(json.dumps({'matching_apis': matches}, indent=2))
    data, headers = multipart({'inlineAPIDefinition': args.spec.read_text(encoding='utf-8-sig')})
    validation = client.json('POST', base + '/apis/validate-openapi', token=token,
                             data=data, headers=headers)
    print(json.dumps({'wso2_openapi_valid': validation.get('isValid')}, indent=2))
    if not validation.get('isValid'):
        raise RuntimeError('Installed WSO2 rejected the export; inspect validation in Publisher')


if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, ValueError, OSError):
        print('FAIL: authenticated discovery/validation incomplete; no API was modified.')
        raise SystemExit(1)
