"""Atomic, bounded delivery ledger. Replayed pruned entries remain DB-idempotent."""
import json
import os
from pathlib import Path


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    with temporary.open('w') as stream:
        json.dump(value, stream)
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)
    if os.name == 'posix':
        descriptor = os.open(path.parent, os.O_DIRECTORY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)


class Checkpoints:
    def __init__(self, directory):
        self.path = Path(directory) / 'completed.json'
        self.completed = json.loads(self.path.read_text()) if self.path.exists() else []

    def commit(self, filename):
        self.completed = (self.completed + [filename])[-4096:]
        atomic_json(self.path, self.completed)


if __name__ == '__main__':
    import sys
    raise SystemExit(0 if sys.argv[1] in Checkpoints('/state').completed else 1)
