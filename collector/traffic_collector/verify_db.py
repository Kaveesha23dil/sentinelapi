"""Owner-side verification of selected non-secret event UUIDs, no raw data."""
import json
import sys
from uuid import UUID
from sqlalchemy import select, text
from sentinelapi.db.models import TrafficEvent
from sentinelapi.db.session import make_engine

if __name__ == '__main__':
    identifiers = [UUID(value) for value in json.loads(sys.stdin.read(65536))]
    if len(identifiers) > 1000:
        raise SystemExit(1)
    engine = make_engine()
    try:
        with engine.connect() as connection:
            rows = connection.execute(select(TrafficEvent.event_id, TrafficEvent.status_code,
                TrafficEvent.latency_ms, TrafficEvent.client_identifier, TrafficEvent.source)
                .where(TrafficEvent.event_id.in_(identifiers))).all()
            print(json.dumps({'count': len(rows), 'event_ids': sorted(str(row.event_id) for row in rows),
                'statuses': [row.status_code for row in rows],
                'measurements_null': all(row.latency_ms is None and row.client_identifier is None for row in rows),
                'all_real_gateway_source': all(row.source == 'wso2-gateway' for row in rows),
                'revision': connection.scalar(text('SELECT version_num FROM alembic_version'))}))
    finally:
        engine.dispose()
