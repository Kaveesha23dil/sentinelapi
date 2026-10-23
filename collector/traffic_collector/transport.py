"""Host-invoked spool writer. No Docker socket, network or gateway credentials."""
import hashlib
import json
import os
import sys
import time
from pathlib import Path
from uuid import UUID
from datetime import datetime

from .checkpoint import atomic_json
from .sanitizer import ROUTES
from .parser import FLOWS, METHODS


def publish(payload, spool=Path('/spool'), state=Path('/state')):
    flows = payload['flows']
    if not isinstance(flows, list) or len(flows) > 1000:
        raise ValueError('Oversized batch')
    for flow in flows:
        if set(flow) != {'timestamp', 'flow', 'correlation_id', 'method', 'endpoint', 'status_code'}:
            raise ValueError('Unexpected transport field')
        UUID(flow['correlation_id'])
        if flow['flow'] not in FLOWS or flow['method'] not in METHODS:
            raise ValueError('Unknown flow/method')
        if datetime.fromisoformat(flow['timestamp']).tzinfo is None:
            raise ValueError('Timestamp must be aware')
        if flow['flow'].startswith('RESPONSE') and (type(flow['status_code']) is not int or not 100 <= flow['status_code'] <= 599):
            raise ValueError('Invalid response status')
        if flow['endpoint'] not in ROUTES + ['/api/v1/orders/{order_id}', '/{unmapped}']:
            raise ValueError('Unsafe route')
    completed_path = state / 'completed.json'
    completed = json.loads(completed_path.read_text()) if completed_path.exists() else []
    for path in spool.glob('*.ndjson'):
        if path.name in completed:
            path.unlink()
    data = ''.join(json.dumps(flow, sort_keys=True) + '\n' for flow in flows).encode()
    if len(list(spool.glob('*.ndjson'))) >= 4096:
        raise ValueError('Spool file limit; source checkpoint not advanced')
    if len(data) > 131072 or sum(path.stat().st_size for path in spool.iterdir() if path.is_file()) + len(data) > 64 * 1024 * 1024:
        raise ValueError('Spool full; source checkpoint not advanced')
    if flows:
        path = spool / (hashlib.sha256(data).hexdigest() + '.ndjson')
        if path.name not in completed and not path.exists():
            temporary = path.with_suffix('.tmp')
            with temporary.open('wb') as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            temporary.replace(path)
            descriptor = os.open(spool, os.O_DIRECTORY)
            try:
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
    atomic_json(spool / 'bridge-health.json', {'checked_at': time.time(),
                'source_bytes': payload.get('source_bytes', 0), 'rejected_records': payload.get('rejected_records', 0)})


if __name__ == '__main__':
    try:
        data = sys.stdin.buffer.read(131073)
        if len(data) > 131072:
            raise ValueError('Oversized input')
        publish(json.loads(data))
        print('Sanitized spool batch durably accepted')
    except Exception:
        print('Transport failed; do not advance source checkpoint. Details redacted.')
        raise SystemExit(1)
