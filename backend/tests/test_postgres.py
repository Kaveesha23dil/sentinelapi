"""Real PostgreSQL checks, guarded against running on the project database."""
import os
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from sentinelapi.db.config import Settings
from sentinelapi.db.models import (APIService, AlertEvidence, AuditLog, DetectionRule,
                                   SecurityAlert, TrafficAggregate, TrafficEvent)
from sentinelapi.db.repository import DuplicateEventConflict, Repository
from sentinelapi.db.schemas import AlertInput, EventInput, EvidenceDetails, ServiceInput
from sentinelapi.db.session import PersistenceError, make_engine, transaction


@pytest.fixture(scope='module')
def engine():
    settings = Settings.from_environment()
    if not settings.database.startswith('sentinelapi_test_'):
        pytest.fail('Refusing PostgreSQL integration tests outside sentinelapi_test_* database')
    engine = make_engine(settings)
    yield engine
    engine.dispose()


@pytest.fixture
def session(engine):
    with engine.connect() as connection:
        outer = connection.begin()
        with Session(bind=connection, join_transaction_mode='create_savepoint') as session:
            yield session
        outer.rollback()


def service(repository, name='demo-test-service'):
    return repository.create_service(ServiceInput(name=name, version='test-1', context='/demo-test'))


def example(api_id, **changes):
    return EventInput(**(dict(api_service_id=api_id, event_id=uuid4(),
        timestamp=datetime.now(timezone.utc), client_identifier='demo:test-client',
        http_method='GET', endpoint='/api/v1/orders', status_code=200,
        latency_ms='12.500', source='demo-test') | changes))


def test_connection_utc_and_indexes(engine):
    with engine.connect() as connection:
        assert connection.scalar(text('SELECT 1')) == 1
        assert connection.scalar(text('SHOW timezone')) == 'UTC'
    inspector = inspect(engine)
    assert set(inspector.get_table_names()) == {'api_services', 'traffic_events', 'traffic_aggregates',
        'detection_rules', 'security_alerts', 'alert_evidence', 'audit_logs', 'alembic_version', 'detection_checkpoints', 'ml_windows'}
    assert 'ix_traffic_events_api_timestamp' in {x['name'] for x in inspector.get_indexes('traffic_events')}


def test_create_query_deduplicate_and_filter(session):
    repo = Repository(session)
    api = service(repo)
    other = service(repo, 'other-demo-service')
    data = example(api.id)
    row, created = repo.add_event(data)
    duplicate, created_again = repo.add_event(data)
    assert created and not created_again and duplicate.id == row.id
    repo.add_event(example(other.id, timestamp=data.timestamp))
    repo.add_event(example(api.id, timestamp=data.timestamp - timedelta(days=2)))
    rows = repo.events(api_service_id=api.id, start=data.timestamp-timedelta(seconds=1),
                       end=data.timestamp+timedelta(seconds=1))
    assert [r.event_id for r in rows] == [data.event_id]
    with pytest.raises(DuplicateEventConflict):
        repo.add_event(data.model_copy(update={'status_code': 500}))


def test_alert_evidence_relationship(session):
    repo = Repository(session)
    api = service(repo)
    row, _ = repo.add_event(example(api.id))
    rule = DetectionRule(name='demo-rule', rule_type='demo-test', configuration={'demonstration': True})
    session.add(rule)
    session.flush()
    alert = repo.create_alert(AlertInput(api_service_id=api.id, rule_id=rule.id,
        severity='high', risk_score='70', first_detected_at=row.timestamp, last_detected_at=row.timestamp),
        EvidenceDetails(demonstration=True, reason_code='demo-example', observed_count=1), row.event_id)
    session.expire_all()
    loaded = session.get(SecurityAlert, alert.id)
    assert loaded.evidence[0].event_id == row.event_id
    assert loaded.evidence[0].alert.id == alert.id
    assert loaded.rule_id == rule.id


def test_cross_api_evidence_rejected(session):
    repo = Repository(session)
    api = service(repo)
    other = service(repo, 'other-demo-service')
    row, _ = repo.add_event(example(other.id))
    with pytest.raises(ValueError, match='alert API'):
        repo.create_alert(AlertInput(api_service_id=api.id, severity='low', risk_score=1,
            first_detected_at=row.timestamp, last_detected_at=row.timestamp),
            EvidenceDetails(demonstration=True, reason_code='demo-example', observed_count=1), row.event_id)


@pytest.mark.parametrize('field,value', [('status_code', 99), ('latency_ms', -1), ('api_service_id', uuid4())])
def test_database_constraints(session, field, value):
    api = service(Repository(session))
    values = example(api.id).model_dump() | {field: value}
    with pytest.raises(IntegrityError):
        with session.begin_nested():
            session.add(TrafficEvent(**values))
            session.flush()


def test_aggregate_and_audit(session):
    api = service(Repository(session))
    now = datetime.now(timezone.utc)
    aggregate = TrafficAggregate(api_service_id=api.id, window_start=now,
        window_end=now+timedelta(minutes=1), request_count=2, error_4xx_count=1,
        error_5xx_count=0, average_latency_ms=10)
    audit = AuditLog(actor_identifier='demo:test', action='demo-create', entity_type='demo-test',
                     entity_id=str(api.id), metadata_={'demonstration': True})
    session.add_all([aggregate, audit])
    session.flush()
    assert session.get(AuditLog, audit.id).metadata_ == {'demonstration': True}
    with pytest.raises(IntegrityError):
        with session.begin_nested():
            session.add(TrafficAggregate(api_service_id=api.id, window_start=now,
                window_end=now, request_count=1, error_4xx_count=2, error_5xx_count=0, average_latency_ms=1))
            session.flush()


def test_committed_data_survives_new_engine(engine):
    event_uuid = uuid4()
    with transaction(engine) as session:
        repo = Repository(session)
        api = service(repo, 'demo-persistence-' + uuid4().hex)
        repo.add_event(example(api.id, event_id=event_uuid))
    separate = make_engine()
    try:
        with separate.connect() as connection:
            assert connection.scalar(select(TrafficEvent.event_id).where(TrafficEvent.event_id == event_uuid)) == event_uuid
    finally:
        separate.dispose()


def test_transaction_rolls_back_with_safe_error(engine):
    name = 'demo-rollback-' + uuid4().hex
    with pytest.raises(PersistenceError):
        with transaction(engine) as session:
            repo = Repository(session)
            api = service(repo, name)
            session.add(TrafficEvent(**(example(api.id).model_dump() | {'status_code': 999})))
            session.flush()
    with engine.connect() as connection:
        assert connection.scalar(select(APIService.id).where(APIService.name == name)) is None


def test_migration_consistency(engine):
    command.check(Config('alembic.ini'))
