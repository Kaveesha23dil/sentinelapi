import json
import time
from pathlib import Path


def healthy(path=Path('/state/health.json')):
    try:
        value = json.loads(path.read_text())
        return value['ok'] and time.time() - value['checked_at'] < 60
    except (OSError, ValueError, KeyError):
        return False


if __name__ == '__main__':
    raise SystemExit(0 if healthy() else 1)
