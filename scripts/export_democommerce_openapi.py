"""Export the live backend document without rewriting its API schema."""

import argparse
import json
from pathlib import Path
from urllib.request import urlopen


EXPECTED = {
    '/health': {'get'},
    '/api/v1/users/me': {'get'},
    '/api/v1/orders': {'get', 'post'},
    '/api/v1/orders/{order_id}': {'get'},
    '/api/v1/payments/simulate': {'post'},
}


def validate(document):
    if not document.get('openapi', '').startswith('3.'):
        raise ValueError('Expected an OpenAPI 3 document')
    for path, methods in EXPECTED.items():
        if not methods <= document.get('paths', {}).get(path, {}).keys():
            raise ValueError(f'Missing actual backend operation: {path}')

    def walk(node):
        if isinstance(node, dict):
            ref = node.get('$ref')
            if ref and ref.startswith('#/'):
                target = document
                for segment in ref[2:].split('/'):
                    target = target[segment.replace('~1', '/').replace('~0', '~')]
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(document)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', default='http://localhost:8000/openapi.json')
    parser.add_argument('--output', type=Path,
                        default=Path('infrastructure/wso2/democommerce-openapi.json'))
    parser.add_argument('--check', action='store_true', help='Check the saved document only')
    args = parser.parse_args()
    if args.check:
        raw = args.output.read_bytes()
    else:
        with urlopen(args.url, timeout=15) as response:
            raw = response.read()
    document = json.loads(raw)
    validate(document)
    if not args.check:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(raw)
    print(f"PASS: OpenAPI {document['openapi']}; {len(document['paths'])} paths; "
          'all six required operations and local references present')
    print('This is a structural check; WSO2 import validation is a separate requirement.')


if __name__ == '__main__':
    main()
