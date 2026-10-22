"""Inspect real log structure without emitting source addresses, IDs or secrets."""
import json
import subprocess
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'collector'))
from traffic_collector.parser import parse
from traffic_collector.config import Config

LOG = '/home/wso2carbon/wso2am-4.5.0/repository/logs/api.log'


def main():
    raw = subprocess.run(['docker', 'exec', 'sentinelapi-wso2', 'tail', '-n', '200', LOG],
                         capture_output=True, check=True, text=True).stdout
    observations = []
    settings = json.loads(Path('infrastructure/database/gateway-precheck.json').read_text())
    config = Config(settings['api_id'], settings['name'], settings['context'], settings['version'])
    for line in raw.splitlines():
        try:
            flow = parse(line, config)
            if not flow:
                continue
            prefix, data = line.split(' - ', 1)
            body = json.loads(data)
            observations.append({'prefix': prefix,
                                 'fields': [key for key in body if key in ['sourceIP', 'verb', 'correlationId', 'apiTo', 'flow', 'statusCode']],
                                 'safe': {'flow': flow['flow'], 'verb': flow['method'],
                                          'statusCode': flow['status_code'], 'endpoint_template': flow['endpoint']}})
        except (ValueError, TypeError):
            continue
    report = {'log_path': LOG, 'observations': observations}
    path = Path('infrastructure/telemetry/log-format-observations.json')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
