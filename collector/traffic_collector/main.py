import signal
import time
import json

from sqlalchemy import text
from sentinelapi.db.session import make_engine

from .checkpoint import Checkpoints, atomic_json
from .config import Config
from .reader import chunks
from .writer import persist


def cycle(engine, config, checkpoints):
    count = 0
    # A quiet spool must still report loss of database connectivity.
    with engine.connect() as connection:
        connection.execute(text('SELECT 1'))
    for filename, flows in chunks(config.spool, checkpoints.completed):
        count += persist(engine, flows, config)
        checkpoints.commit(filename)  # strictly after transaction commit
    return count


def main():
    config = Config.env()
    engine = make_engine()
    checkpoints = Checkpoints(config.state)
    stopping = False

    def stop(*_):
        nonlocal stopping
        stopping = True

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    try:
        while not stopping:
            try:
                inserted = cycle(engine, config, checkpoints)
                try:
                    bridge = json.loads((config.spool / 'bridge-health.json').read_text())
                    source_fresh = time.time() - bridge['checked_at'] < 60
                except (OSError, ValueError, KeyError):
                    source_fresh = False
                atomic_json(config.state / 'health.json', {'ok': source_fresh,
                            'source_fresh': source_fresh, 'checked_at': time.time()})
                if inserted:
                    print(f'Committed {inserted} gateway events', flush=True)
            except Exception:
                atomic_json(config.state / 'health.json', {'ok': False, 'checked_at': time.time()})
                print('Collector cycle failed; retrying with checkpoint retained. Details redacted.', flush=True)
            time.sleep(2)
    finally:
        engine.dispose()


if __name__ == '__main__':
    main()
