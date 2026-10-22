"""Verify the retained Step 4 marker without updating historical evidence."""
import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID
from sqlalchemy import select, text
from .config import Settings
from .models import TrafficEvent
from .session import make_engine


def main():
    old = json.loads(Path('/prior/database-verification.json').read_text())
    if not old['test_database'].startswith('sentinelapi_test_'):
        raise ValueError('Expected prior disposable test database')
    engine = make_engine(Settings.from_environment().model_copy(update={'database': old['test_database']}))
    try:
        with engine.connect() as connection:
            marker = connection.scalar(select(TrafficEvent.event_id).where(
                TrafficEvent.event_id == UUID(old['marker_event_id']), TrafficEvent.source == 'demo-test'))
            assert marker is not None
    finally:
        engine.dispose()
    engine = make_engine()
    try:
        with engine.connect() as connection:
            revision = connection.scalar(text('SELECT version_num FROM alembic_version'))
    finally:
        engine.dispose()
    report = {'checked_at_utc': datetime.now(timezone.utc).isoformat(), 'step4_marker_still_present': True,
              'prior_test_database': old['test_database'], 'marker_event_id': str(marker),
              'main_migration_revision': revision, 'step3_3_complete': False}
    Path('/evidence/prerequisite-verification.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        print('FAIL: prior marker check; details redacted.')
        raise SystemExit(1)
