"""Out-of-band worker: bounded event-time slices, overlap and atomic checkpoints."""
import asyncio
import logging
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert

from sentinelapi.db.models import (AlertEvidence, DetectionCheckpoint, DetectionRule,
                                    SecurityAlert, TrafficEvent)
from sentinelapi.db.session import make_engine, transaction
from .rules import DEFAULTS, Observation, configuration, evaluate, fingerprint

LOG = logging.getLogger('sentinelapi.detector')
MAX_EVENTS = 10000
LATENESS = timedelta(seconds=120)
SLICE = timedelta(seconds=60)
HISTORY = timedelta(seconds=300)


class WindowCapacityError(RuntimeError):
    pass


def seed_rules(db):
    for kind, defaults in DEFAULTS.items():
        db.execute(insert(DetectionRule).values(id=uuid4(), name=kind, rule_type=kind,
            configuration=configuration(kind, defaults).model_dump(), enabled=kind == 'error_rate')
            .on_conflict_do_nothing(index_elements=['name']))


def persist(db, rule, config, finding, now):
    incident = fingerprint(rule.id, config.version, finding, config.window_seconds)
    alert_id = uuid4()
    created = db.scalar(insert(SecurityAlert).values(id=alert_id, api_service_id=finding.api_id,
        rule_id=rule.id, rule_version=config.version, incident_fingerprint=incident,
        severity='medium', status='open', risk_score=50, title='Observed API error-rate spike',
        description=finding.explanation, first_detected_at=now, last_detected_at=now,
        window_start=finding.start, window_end=finding.end,
        measured_value=finding.measured, threshold=finding.threshold)
        .on_conflict_do_nothing(index_elements=['incident_fingerprint']).returning(SecurityAlert.id))
    if created is None:
        return False
    for event_id in finding.event_ids:
        db.add(AlertEvidence(alert_id=alert_id, event_id=event_id, evidence_type='observed_http_error',
            details={'request_count': finding.count, 'evidence_limit': 100,
                     'source': 'wso2-gateway', 'rule_version': config.version}))
    return True


def run_once(engine, now=None):
    """Commit alerts + watermark together. Caller retry is safe after any failure.

    Replay the previous 120 seconds at each pass. Events arriving more than 120
    seconds behind the watermark need an explicit historical replay; they are
    never claimed to be covered. Capacity overflow rolls back instead of truncating.
    """
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError('Aware execution timestamp required')
    with transaction(engine) as db:
        # Transaction-scoped PostgreSQL lock serializes seeding, alerts and checkpoint.
        if not db.scalar(text('SELECT pg_try_advisory_xact_lock(6062026)')):
            return {'state': 'busy', 'created': 0}
        seed_rules(db)
        checkpoint = db.get(DetectionCheckpoint, 'live-v1')
        if checkpoint is None:
            # Explicit bounded bootstrap; historical data requires operator replay.
            checkpoint = DetectionCheckpoint(name='live-v1', watermark=now-HISTORY-LATENESS)
            db.add(checkpoint)
        start = checkpoint.watermark - LATENESS
        end = min(checkpoint.watermark+SLICE, now-LATENESS)
        if end <= checkpoint.watermark:
            return {'state': 'caught-up', 'created': 0}
        rows = db.scalars(select(TrafficEvent).where(TrafficEvent.source == 'wso2-gateway',
            TrafficEvent.timestamp > start-HISTORY, TrafficEvent.timestamp <= end)
            .order_by(TrafficEvent.timestamp, TrafficEvent.event_id).limit(MAX_EVENTS+1)).all()
        if len(rows) > MAX_EVENTS:
            raise WindowCapacityError('Bounded window capacity exceeded; checkpoint unchanged')
        observations = [Observation(row.event_id, row.api_service_id, row.timestamp, row.status_code) for row in rows]
        ends = sorted({row.timestamp for row in observations if row.timestamp > start})
        created = 0
        for rule in db.scalars(select(DetectionRule).where(DetectionRule.enabled.is_(True))):
            if rule.rule_type != 'error_rate':
                # Deliberately fail closed: no identity/route/auth/baseline adapter exists.
                LOG.warning('detector_rule_unsupported rule_id=%s', rule.id)
                continue
            config = configuration(rule.rule_type, rule.configuration)
            for window_end in ends:
                for finding in evaluate(rule.rule_type, config, observations, window_end):
                    created += persist(db, rule, config, finding, now)
        checkpoint.watermark = end
        return {'state': 'processed', 'created': created, 'observed': len(rows), 'watermark': end.isoformat()}


async def serve():
    engine = make_engine()
    try:
        while True:
            try:
                result = await asyncio.to_thread(run_once, engine)
                LOG.info('detector_cycle state=%s created=%s', result['state'], result['created'])
            except Exception:
                # Do not log SQL, parameters, source records or driver exception text.
                LOG.error('detector_cycle_failed checkpoint_not_advanced')
            await asyncio.sleep(5)
    finally:
        engine.dispose()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    asyncio.run(serve())
