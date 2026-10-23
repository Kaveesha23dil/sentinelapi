"""Independent ML transaction invoked by the existing asynchronous worker."""
import os
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from uuid import UUID, uuid4
from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert
from sentinelapi.db.models import (MLWindow, SecurityAlert, AlertEvidence,
                                   TrafficEvent, DetectionCheckpoint)
from sentinelapi.db.session import transaction
from .features import SCHEMA, Event, aggregate, floor_minute


def configured_model():
    from .model import load
    path, digest = os.getenv('ML_MODEL_DIR'), os.getenv('ML_APPROVED_SHA256')
    if not path or not digest:
        raise ValueError('No approved model')
    model, metadata = load(path, digest)
    if not metadata['production_ready'] and os.getenv('ML_ALLOW_EXPERIMENTAL') != 'true':
        raise ValueError('Experimental deployment not enabled')
    return model, metadata


def persist(db, window, result, metadata, now):
    row_id = uuid4()
    inserted = db.scalar(insert(MLWindow).values(id=row_id,
        api_service_id=UUID(window.api_id), window_id=window.identifier,
        window_start=window.start, window_end=window.end, schema_version=SCHEMA,
        model_version=metadata['version'], decision_score=result['decision_score'],
        anomaly=result['anomaly'], features=window.summary, provenance=metadata['provenance'])
        .on_conflict_do_nothing(index_elements=['window_id', 'model_version']).returning(MLWindow.id))
    if inserted is None:
        return False
    if result['anomaly']:
        incident = sha256(f"ml|{window.identifier}|{metadata['version']}".encode()).hexdigest()
        alert_id = uuid4()
        correlated = db.scalars(select(SecurityAlert.id).where(
            SecurityAlert.api_service_id == UUID(window.api_id), SecurityAlert.rule_id.is_not(None),
            SecurityAlert.window_start < window.end, SecurityAlert.window_end > window.start).limit(20)).all()
        db.add(SecurityAlert(id=alert_id, api_service_id=UUID(window.api_id), severity='medium',
            status='open', risk_score=50, title='Unusual API traffic window',
            description=f"Isolation Forest {metadata['version']} measured decision score "
                f"{result['decision_score']:.8f} below zero in a finalized 60-second window. "
                f"Model provenance: {metadata['provenance']}. Unusual behavior does not establish malicious intent.",
            first_detected_at=now, last_detected_at=now, incident_fingerprint=incident,
            window_start=window.start, window_end=window.end,
            measured_value=result['decision_score'], threshold=0))
        db.flush()
        details = dict(model_version=metadata['version'], window_id=window.identifier,
            schema=SCHEMA, features=window.summary, decision_score=result['decision_score'],
            model_provenance=metadata['provenance'], traffic_source='wso2-gateway',
            correlated_rule_alerts=[str(i) for i in correlated], evidence_limit=100)
        # Summary remains present even where event links are unavailable.
        db.add(AlertEvidence(alert_id=alert_id, evidence_type='ml_window', details=details))
        for event_id in window.event_ids[:100]:
            db.add(AlertEvidence(alert_id=alert_id, event_id=UUID(event_id),
                evidence_type='ml_underlying_event', details={'window_id': window.identifier}))
        db.get(MLWindow, row_id).alert_id = alert_id
    return True


def run_once(engine, now=None):
    if not os.getenv('ML_MODEL_DIR'):
        return {'state':'unconfigured','processed':0}
    from .model import score
    model, metadata = configured_model()
    now = now or datetime.now(timezone.utc)
    finalized = floor_minute(now-timedelta(seconds=120))
    with transaction(engine) as db:
        if not db.scalar(text('SELECT pg_try_advisory_xact_lock(7072026)')):
            return {'state':'busy','processed':0}
        name = 'ml-'+metadata['version']
        checkpoint = db.get(DetectionCheckpoint, name)
        if checkpoint is None:
            checkpoint = DetectionCheckpoint(name=name, watermark=finalized-timedelta(minutes=5))
            db.add(checkpoint)
        start = checkpoint.watermark
        end = min(start+timedelta(minutes=1), finalized)
        if end <= start:
            return {'state':'caught-up','processed':0}
        rows = db.scalars(select(TrafficEvent).where(TrafficEvent.source == 'wso2-gateway',
            TrafficEvent.api_service_id == UUID(metadata['api_id']),
            TrafficEvent.timestamp >= start, TrafficEvent.timestamp < end)
            .order_by(TrafficEvent.timestamp,TrafficEvent.event_id).limit(10001)).all()
        if len(rows) > 10000:
            raise ValueError('ML window capacity exceeded; watermark unchanged')
        windows = aggregate([Event(str(r.event_id),str(r.api_service_id),r.timestamp,
            r.status_code,r.http_method,r.endpoint) for r in rows],
            coverage_start=start,complete_through=end)
        processed = 0
        for window in windows:
            if window.eligible:
                processed += persist(db,window,score(model,metadata,window),metadata,now)
        checkpoint.watermark = end
        return {'state':'processed','processed':processed}
