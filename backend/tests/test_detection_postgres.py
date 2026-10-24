"""Real PostgreSQL tests, restricted to the existing disposable-test runner.

All traffic here is explicitly synthetic, including rows using the gateway source
to exercise the production adapter. None of these results count as live proof.
"""
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from test_postgres import engine
from sentinelapi.db.models import (APIService, AlertEvidence, AuditLog, DetectionCheckpoint,
                                   DetectionRule, SecurityAlert, TrafficEvent)
from sentinelapi.detection.api import session as api_session
from sentinelapi.detection.worker import run_once, seed_rules, WindowCapacityError
from sentinelapi.detection.rules import DEFAULTS, configuration
from sentinelapi.monitoring.app import app

NOW = datetime(2026, 10, 23, 12, tzinfo=timezone.utc)


@pytest.fixture
def isolated(engine):
    # Use real independent transactions so worker rollback/restart behavior is
    # exercised. The imported engine fixture refuses non-test database names.
    with Session(engine, expire_on_commit=False) as db:
        db.execute(delete(DetectionCheckpoint).where(DetectionCheckpoint.name == 'live-v1'))
        seed_rules(db)
        definitions = db.scalars(select(DetectionRule).where(DetectionRule.name.in_(DEFAULTS))).all()
        saved = [(row.id, row.configuration, row.enabled) for row in definitions]
        for row in definitions:
            row.configuration = configuration(row.rule_type, DEFAULTS[row.rule_type]).model_dump()
            row.enabled = row.rule_type == 'error_rate'
        api = APIService(name='fixture-detector-'+uuid4().hex, version='test', context='/fixture')
        db.add(api)
        db.add(DetectionCheckpoint(name='live-v1', watermark=NOW-timedelta(seconds=60)))
        db.flush()
        api_id = api.id
        db.commit()
        try:
            yield engine, db, api_id
        finally:
            db.rollback()
            alert_ids = select(SecurityAlert.id).where(SecurityAlert.api_service_id == api_id)
            db.execute(delete(AlertEvidence).where(AlertEvidence.alert_id.in_(alert_ids)))
            db.execute(delete(SecurityAlert).where(SecurityAlert.api_service_id == api_id))
            db.execute(delete(TrafficEvent).where(TrafficEvent.api_service_id == api_id))
            db.execute(delete(APIService).where(APIService.id == api_id))
            db.execute(delete(DetectionCheckpoint).where(DetectionCheckpoint.name == 'live-v1'))
            for rule_id, config, enabled in saved:
                row = db.get(DetectionRule, rule_id)
                row.configuration, row.enabled = config, enabled
            db.commit()


def populate(db, api_id, statuses, timestamp=NOW-timedelta(seconds=30)):
    ids = []
    for status in statuses:
        event_id = uuid4()
        ids.append(event_id)
        db.add(TrafficEvent(api_service_id=api_id, event_id=event_id, timestamp=timestamp,
            http_method='GET', endpoint='/fixture', status_code=status, source='wso2-gateway'))
    db.commit()
    return ids


def test_worker_recovery_dedup_evidence_late_events(isolated):
    connection, db, api_id = isolated
    ids = populate(db, api_id, [500]*11+[200]*9)
    first = run_once(connection, NOW+timedelta(seconds=120))
    assert first['created'] == 1
    second = run_once(connection, NOW+timedelta(seconds=180))
    assert second['created'] == 0
    alerts = db.scalars(select(SecurityAlert).where(SecurityAlert.api_service_id == api_id)).all()
    assert len(alerts) == 1 and alerts[0].rule_version == 1
    evidence = db.scalars(select(AlertEvidence).where(AlertEvidence.alert_id == alerts[0].id)).all()
    assert {row.event_id for row in evidence} == set(ids[:11])
    # Simulates late arrival while the worker is restarted with the persisted watermark.
    populate(db, api_id, [500], NOW-timedelta(seconds=20))
    assert run_once(connection, NOW+timedelta(seconds=240))['created'] == 0
    db.expire_all()
    assert db.get(DetectionCheckpoint, 'live-v1').watermark == NOW+timedelta(seconds=120)


def test_disabled_rule_and_normal_traffic(isolated):
    connection, db, api_id = isolated
    populate(db, api_id, [200]*20)
    assert run_once(connection, NOW+timedelta(seconds=120))['created'] == 0
    rule = db.scalar(select(DetectionRule).where(DetectionRule.rule_type == 'error_rate'))
    rule.enabled = False
    populate(db, api_id, [500]*30)
    assert run_once(connection, NOW+timedelta(seconds=180))['created'] == 0


def test_overflow_rolls_back_checkpoint(isolated, monkeypatch):
    connection, db, api_id = isolated
    populate(db, api_id, [500]*21)
    monkeypatch.setattr('sentinelapi.detection.worker.MAX_EVENTS', 20)
    before = db.get(DetectionCheckpoint, 'live-v1').watermark
    with pytest.raises(WindowCapacityError):
        run_once(connection, NOW+timedelta(seconds=120))
    db.expire_all()
    assert db.get(DetectionCheckpoint, 'live-v1').watermark == before
    assert db.scalar(select(func.count()).select_from(SecurityAlert).where(SecurityAlert.api_service_id == api_id)) == 0


def test_api_lifecycle_filtering_and_audit(isolated, monkeypatch):
    connection, db, api_id = isolated
    populate(db, api_id, [500]*20)
    run_once(connection, NOW+timedelta(seconds=120))
    alert = db.scalar(select(SecurityAlert).where(SecurityAlert.api_service_id == api_id))
    for role in ['reader', 'analyst', 'admin']:
        monkeypatch.setenv('SECURITY_'+role.upper()+'_TOKEN', 'fixture-'+role+'-'+'x'*40)
    app.dependency_overrides[api_session] = lambda: db
    try:
        with TestClient(app) as client:
            reader = {'Authorization': 'Bearer fixture-reader-'+'x'*40}
            analyst = {'Authorization': 'Bearer fixture-analyst-'+'x'*40}
            admin = {'Authorization': 'Bearer fixture-admin-'+'x'*40}
            base = '/api/v1/security'
            params = {'api_id': str(api_id), 'start': NOW.isoformat(),
                      'end': (NOW+timedelta(hours=1)).isoformat(), 'severity': 'medium'}
            assert client.get(base+'/alerts', params=params, headers=reader).json()['total'] == 1
            assert client.get(base+'/alerts', params=params | {'status': 'resolved'}, headers=reader).json()['total'] == 0
            detail = client.get(base+'/alerts/'+str(alert.id), headers=reader).json()
            assert len(detail['evidence']) == 20
            assert client.patch(base+'/alerts/'+str(alert.id), json={'status': 'investigating'}, headers=analyst).status_code == 200
            assert client.patch(base+'/alerts/'+str(alert.id), json={'status': 'resolved'}, headers=analyst).status_code == 200
            assert client.patch(base+'/alerts/'+str(alert.id), json={'status': 'open'}, headers=analyst).status_code == 409
            rule = db.scalar(select(DetectionRule).where(DetectionRule.rule_type == 'error_rate'))
            updated = client.patch(base+'/rules/'+str(rule.id), json={'enabled': False}, headers=admin)
            assert updated.status_code == 200 and updated.json()['configuration']['version'] == 2
            unsupported = db.scalar(select(DetectionRule).where(DetectionRule.rule_type == 'auth_failures'))
            assert client.patch(base+'/rules/'+str(unsupported.id), json={'enabled': True}, headers=admin).status_code == 409
            assert db.scalar(select(func.count()).select_from(AuditLog).where(AuditLog.entity_id == str(alert.id))) == 2
    finally:
        app.dependency_overrides.clear()


def test_incident_unique_constraint(isolated):
    connection, db, api_id = isolated
    populate(db, api_id, [500]*20)
    run_once(connection, NOW+timedelta(seconds=120))
    alert = db.scalar(select(SecurityAlert).where(SecurityAlert.api_service_id == api_id))
    with pytest.raises(IntegrityError):
        with db.begin_nested():
            db.add(SecurityAlert(api_service_id=api_id, rule_id=alert.rule_id, severity='medium',
                status='open', risk_score=50, title='fixture', description='fixture',
                first_detected_at=NOW, last_detected_at=NOW,
                incident_fingerprint=alert.incident_fingerprint))
            db.flush()


def test_seed_rules_preserves_reviewed_configuration(isolated):
    _, db, _ = isolated
    definitions = db.scalars(select(DetectionRule).where(DetectionRule.name.in_(DEFAULTS))).all()
    assert len(definitions) == 5
    assert {row.name for row in definitions if row.enabled} == {'error_rate'}
    rule = next(row for row in definitions if row.rule_type == 'error_rate')
    reviewed = dict(rule.configuration, threshold=0.75, version=2)
    rule.configuration, rule.enabled = reviewed, False
    db.commit()
    seed_rules(db)
    db.commit()
    db.expire_all()
    assert rule.configuration == reviewed and rule.enabled is False
    assert len(db.scalars(select(DetectionRule).where(DetectionRule.name.in_(DEFAULTS))).all()) == 5
