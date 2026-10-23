"""Bounded read-only simulation through the configured local WSO2 gateway.

Requires an existing subscribed token in WSO2_SIMULATION_TOKEN; never prints it.
Outcomes are observations, not proof of collection or detection. Stops at 429.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import time
from urllib.parse import urlsplit
from uuid import uuid4

from wso2_http import Client

ROOT = Path(__file__).resolve().parents[1]


def run(client, gateway, token, scenario, pause=time.sleep):
    url = urlsplit(gateway)
    if (url.scheme != 'https' or url.hostname not in {'localhost', '127.0.0.1'}
            or url.port != 8243 or url.username or url.password or url.query or url.fragment
            or url.path != '/democommerceapi/1.0.0'):
        raise ValueError('Only the configured local DemoCommerce gateway is allowed')
    if scenario not in {'normal', 'error-rate'}:
        raise ValueError('Unknown scenario')
    if not token:
        raise ValueError('Provide an existing subscribed simulation token in the environment')
    outcomes = []
    for index in range(24):
        path = '/api/v1/orders/2147483647' if scenario == 'error-rate' and index >= 4 else '/api/v1/orders'
        activity = str(uuid4())
        issued = datetime.now(timezone.utc).isoformat()
        status, _ = client.request('GET', gateway+path, token=token, headers={'activityid': activity})
        outcomes.append({'issued_at_utc': issued, 'method': 'GET', 'path': path,
                         'activity_id': activity, 'status': status})
        if status in {401, 403, 429}:
            break
        pause(2)
    return {'scenario': scenario, 'synthetic_replay': False, 'requests': outcomes,
            'note': 'Actual gateway outcomes only. Correlate BASIC logs, database event UUIDs and alert evidence separately.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('scenario', choices=['normal', 'error-rate'])
    parser.add_argument('--ca-file', default=os.getenv('WSO2_CA_FILE'))
    args = parser.parse_args()
    settings = json.loads((ROOT/'infrastructure/database/gateway-precheck.json').read_text())
    result = run(Client(args.ca_file), settings['gateway_url'], os.getenv('WSO2_SIMULATION_TOKEN'), args.scenario)
    target = ROOT/'infrastructure/threat-detection'
    target.mkdir(exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')
    (target/f'{args.scenario}-{stamp}.json').write_text(json.dumps(result, indent=2)+'\n')
    print(f'Recorded {len(result["requests"])} actual local gateway outcomes; ingestion/detection not asserted.')


if __name__ == '__main__':
    main()
