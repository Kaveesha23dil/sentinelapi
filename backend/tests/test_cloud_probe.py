from fastapi.testclient import TestClient

from sentinelapi.monitoring.app import app


def test_liveness_does_not_require_database_or_token(monkeypatch):
    monkeypatch.delenv('POSTGRES_PASSWORD', raising=False)
    monkeypatch.delenv('MONITORING_API_TOKEN', raising=False)
    with TestClient(app) as client:
        response = client.get('/healthz')
    assert response.status_code == 200
    assert response.json() == {'status': 'ok'}


def test_monitoring_still_requires_authentication(monkeypatch):
    monkeypatch.delenv('MONITORING_API_TOKEN', raising=False)
    with TestClient(app) as client:
        response = client.get('/api/v1/monitoring/session')
    assert response.status_code == 503
