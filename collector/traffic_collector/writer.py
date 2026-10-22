"""A committed batch is the only signal permitting collector checkpoint advance."""
import time

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import OperationalError

from sentinelapi.db.models import APIService, TrafficEvent
from sqlalchemy.orm import Session

from .normalizer import normalize


def persist(engine, flows, config, *, attempts=4, pause=time.sleep):
    for attempt in range(attempts):
        try:
            with Session(engine) as session, session.begin():
                statement = insert(APIService).values(name=config.api_name, version=config.version,
                    context=config.context, gateway_api_id=config.api_id).on_conflict_do_nothing()
                session.execute(statement)
                service = session.scalar(select(APIService).where(APIService.gateway_api_id == config.api_id))
                if service is None or (service.name, service.version, service.context) != (config.api_name, config.version, config.context):
                    raise ValueError('Existing API identity conflicts with collector configuration')
                values = []
                for flow in flows:
                    try:
                        event = normalize(flow, config, service.id)
                        if event:
                            values.append(event.model_dump())
                    except (ValueError, KeyError, TypeError):
                        # Reject untrusted malformed flow; never print its contents.
                        continue
                inserted = 0
                for offset in range(0, len(values), config.batch_size):
                    result = session.execute(insert(TrafficEvent).values(values[offset:offset+config.batch_size])
                        .on_conflict_do_nothing(index_elements=['event_id']).returning(TrafficEvent.id))
                    inserted += len(result.all())
            return inserted
        except OperationalError:
            if attempt + 1 == attempts:
                raise RuntimeError('Database unavailable; batch and checkpoint retained') from None
            pause(min(2 ** attempt, 8))
