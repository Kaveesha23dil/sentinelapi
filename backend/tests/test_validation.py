from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from sentinelapi.db.config import Settings
from sentinelapi.db.models import AuditLog, Base
from sentinelapi.db.schemas import AlertInput, EventInput, EvidenceDetails


def event(**changes):
    values = dict(api_service_id=uuid4(), event_id=uuid4(), timestamp=datetime.now(timezone.utc),
                  client_identifier='demo:test-client', http_method='GET', endpoint='/api/v1/orders',
                  status_code=200, latency_ms='12.500', source='demo-test')
    return EventInput(**(values | changes))


@pytest.mark.parametrize('change', [
    {'timestamp': datetime(2026, 1, 1)}, {'status_code': 600}, {'latency_ms': '-1'},
    {'latency_ms': 'NaN'}, {'endpoint': '/orders?token=synthetic'},
    {'client_identifier': '192.0.2.1'}, {'Authorization': 'synthetic'},
    {'http_method': 'INVALID'}, {'source': 'unknown'}])
def test_reject_unsafe_or_invalid_event(change):
    with pytest.raises(ValidationError):
        event(**change)


def test_safe_event_and_utc():
    assert event().timestamp.utcoffset().total_seconds() == 0


def test_json_evidence_rejects_arbitrary_payload():
    with pytest.raises(ValidationError):
        EvidenceDetails(demonstration=True, reason_code='demo-example', observed_count=1,
                        password='synthetic')


def test_alert_time_order():
    with pytest.raises(ValidationError):
        AlertInput(api_service_id=uuid4(), severity='high', risk_score=90,
                   first_detected_at='2026-10-22T01:00:00Z', last_detected_at='2026-10-21T01:00:00Z')


def test_metadata_name_and_all_tables():
    assert len(Base.metadata.tables) == 8
    assert 'metadata' in AuditLog.__table__.c
    assert AuditLog.metadata is Base.metadata


def test_missing_runtime_secret_rejected(monkeypatch):
    monkeypatch.delenv('POSTGRES_PASSWORD', raising=False)
    with pytest.raises(ValueError, match='runtime environment'):
        Settings.from_environment()


def test_url_escapes_secret_without_printing_it():
    settings = Settings(database='example', username='example', password='synthetic@:/%')
    assert settings.url().password == 'synthetic@:/%'
    assert 'synthetic@' not in str(settings.url())
