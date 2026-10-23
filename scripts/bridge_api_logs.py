"""Explicit host bridge: bounded read-only Docker exec -> sanitized named spool.

Run --follow for continuous local transport. No raw logs are saved on Windows.
The collector container itself never receives Docker access or WSO2 credentials.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from contextlib import contextmanager

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'collector'))
from traffic_collector.checkpoint import atomic_json
from traffic_collector.config import Config
from traffic_collector.parser import parse

ROOT = Path(__file__).resolve().parents[1]
LOGS = '/home/wso2carbon/wso2am-4.5.0/repository/logs'


def docker(*args):
    return subprocess.run(['docker', *args], check=True, capture_output=True).stdout


@contextmanager
def exclusive(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a+b') as lock:
        if lock.tell() == 0:
            lock.write(b'0')
            lock.flush()
        lock.seek(0)
        if os.name == 'nt':
            import msvcrt
            msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            yield
        finally:
            lock.seek(0)
            if os.name == 'nt':
                msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


def poll(config, checkpoint=ROOT / '.runtime/telemetry/source-checkpoint.json'):
    with exclusive(checkpoint.with_suffix('.lock')):
        return _poll(config, checkpoint)


def _poll(config, checkpoint):
    states = json.loads(checkpoint.read_text()) if checkpoint.exists() else {}
    # Rotated filenames are validated before becoming arguments, never shell code.
    listing = docker('exec', 'sentinelapi-wso2', 'find', LOGS, '-maxdepth', '1', '-type', 'f',
                     '-name', 'api*.log', '-printf', '%i %s %f\n').decode()
    files = []
    for line in listing.splitlines():
        inode, size, name = line.split(maxsplit=2)
        if re.fullmatch(r'api(?:-\d{2}-\d{2}-\d{4}-\d+)?\.log', name):
            files.append((name == 'api.log', name, inode, int(size)))
    if not files:
        raise RuntimeError('No source logs found')
    if len(files) > 256:
        raise RuntimeError('Source inventory limit exceeded; review log retention')
    present = {inode for _, _, inode, _ in files}
    for inode, previous in list(states.items()):
        if inode not in present:
            if previous.get('observed_size', previous['offset']) > previous['offset']:
                raise RuntimeError('Unread source rotation disappeared; operator review required')
            del states[inode]
    for _, name, inode, size in sorted(files):
        path = LOGS + '/' + name
        fingerprint = hashlib.sha256(docker('exec', 'sentinelapi-wso2', 'head', '-c', '64', path)).hexdigest()
        previous = states.get(inode, {})
        offset = previous.get('offset', 0)
        if previous.get('fingerprint') != fingerprint or size < offset:
            offset = 0  # new generation / copytruncate; DB UUIDs still deduplicate replay
        raw = docker('exec', 'sentinelapi-wso2', 'dd', 'if=' + path, 'bs=1',
                     'skip=' + str(offset), 'count=65536', 'status=none')
        actual_inode, actual_size = docker('exec', 'sentinelapi-wso2', 'stat', '-c', '%i %s', path).decode().split()
        if actual_inode != inode or int(actual_size) < offset + len(raw):
            raise RuntimeError('Source rotated while reading; retry without checkpoint advancement')
        end = raw.rfind(b'\n') + 1
        if raw and end == 0:
            if len(raw) == 65536:
                raise RuntimeError('Oversized source record requires operator review; checkpoint retained')
            continue  # truncated final line: wait for completion
        complete = raw[:end]
        flows, rejected = [], 0
        for line in complete.decode('utf-8', errors='replace').splitlines():
            flow = parse(line, config)
            if flow:
                flows.append(flow)
            else:
                rejected += 1
        payload = json.dumps({'flows': flows, 'source_bytes': end, 'rejected_records': rejected}).encode()
        result = subprocess.run(['docker', 'compose', 'run', '--rm', '-T', '--no-deps', 'log-transport'],
                                input=payload, capture_output=True, cwd=ROOT)
        if result.returncode:
            raise RuntimeError('Spool rejected batch; source checkpoint retained')
        states[inode] = {'offset': offset + end, 'fingerprint': fingerprint, 'observed_size': int(actual_size)}
        # Only durable transport acceptance permits the host source checkpoint.
        atomic_json(checkpoint, states)
        print(f'Safely transported {len(flows)} flow records; rejected {rejected}', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--follow', action='store_true')
    args = parser.parse_args()
    report = json.loads((ROOT / 'infrastructure/database/gateway-precheck.json').read_text())
    config = Config(report['api_id'], report['name'], report['context'], report['version'])
    while True:
        try:
            poll(config)
        except Exception:
            print('Bridge failed; retry required. No raw input or credentials displayed.', flush=True)
            if not args.follow:
                return 1
        if not args.follow:
            return 0
        time.sleep(15)


if __name__ == '__main__':
    raise SystemExit(main())
