"""Combined deployment regressions; no live credentials or database writes."""
from pathlib import Path
from unittest.mock import Mock

from fastapi.testclient import TestClient
from sentinelapi.db.provision_dashboard_reader import provision
from sentinelapi.monitoring.app import app


ROOT = Path(__file__).resolve().parents[2]


def test_combined_compose_requires_reader_and_preserves_database_role():
    compose = (ROOT / 'compose.yaml').read_text()
    monitoring = compose.split('  monitoring:', 1)[1].split('  postgres:', 1)[0]
    assert 'SECURITY_READER_TOKEN: ${SECURITY_READER_TOKEN:?' in monitoring
    assert 'MONITORING_API_TOKEN: ${MONITORING_API_TOKEN:?' in monitoring
    assert 'POSTGRES_USER: sentinelapi_monitor' in monitoring
    assert 'SECURITY_ADMIN_TOKEN:' not in monitoring
    assert 'SECURITY_ANALYST_TOKEN:' not in monitoring


def test_dashboard_grants_are_additive_and_read_only():
    connection = Mock()
    provision(connection)
    statements = [str(call.args[0]) for call in connection.execute.call_args_list]
    assert len(statements) == 2
    assert all(statement.startswith('GRANT SELECT') for statement in statements)
    assert all(statement.endswith('TO sentinelapi_monitor') for statement in statements)


def test_reader_only_deployment_and_role_isolation(monkeypatch):
    monkeypatch.setenv('SECURITY_READER_TOKEN', 'synthetic-reader-' + 'x' * 40)
    monkeypatch.setenv('MONITORING_API_TOKEN', 'synthetic-monitor-' + 'x' * 40)
    monkeypatch.delenv('SECURITY_ADMIN_TOKEN', raising=False)
    monkeypatch.delenv('SECURITY_ANALYST_TOKEN', raising=False)
    with TestClient(app) as client:
        path = '/api/v1/security/session'
        assert client.get(path).status_code == 401
        assert client.get(path, headers={'Authorization': 'Bearer invalid'}).status_code == 401
        assert client.get(path, headers={'Authorization': 'Bearer synthetic-monitor-' + 'x' * 40}).status_code == 401
        response = client.get(path, headers={'Authorization': 'Bearer synthetic-reader-' + 'x' * 40})
        assert response.json() == {'role': 'reader', 'capabilities': ['security:read']}
