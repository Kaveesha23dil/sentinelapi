"""HTTP auth/validation unit tests; persistence is covered in PostgreSQL tests."""
from unittest.mock import Mock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from sentinelapi.monitoring.app import app
from sentinelapi.detection.api import session, TRANSITIONS


@pytest.fixture
def client(monkeypatch):
    for role in ['reader', 'analyst', 'admin']:
        monkeypatch.setenv('SECURITY_'+role.upper()+'_TOKEN', 'fixture-'+role+'-'+'x'*40)
    db = Mock()
    app.dependency_overrides[session] = lambda: db
    with TestClient(app) as client:
        yield client, db
    app.dependency_overrides.clear()


def headers(role):
    return {'Authorization': 'Bearer fixture-'+role+'-'+'x'*40}


@pytest.mark.parametrize('path', ['/alerts', '/alerts/'+str(uuid4()), '/rules', '/summary'])
def test_authentication(client, path):
    client, db = client
    assert client.get('/api/v1/security'+path).status_code == 401
    db.assert_not_called()


@pytest.mark.parametrize('role, resource, patch', [
    ('reader', 'alerts', {'status': 'resolved'}), ('reader', 'rules', {'enabled': False}),
    ('analyst', 'rules', {'enabled': False})])
def test_authorization(client, role, resource, patch):
    client, db = client
    assert client.patch(f'/api/v1/security/{resource}/{uuid4()}', json=patch, headers=headers(role)).status_code == 403
    db.scalar.assert_not_called()


@pytest.mark.parametrize('params', [{'page': 0}, {'page_size': 101}, {'severity': 'secret'},
    {'status': 'invalid'}, {'start': 'private-data'}, {'start': '2026-10-23T00:00:00'}])
def test_filter_validation(client, params):
    client, _ = client
    response = client.get('/api/v1/security/alerts', params=params, headers=headers('reader'))
    assert response.status_code == 422 and 'private-data' not in response.text


@pytest.mark.parametrize('patch', [{}, {'enabled': None}, {'enabled': 'true'}, {'unknown': 'unsafe'}])
def test_patch_validation(client, patch):
    client, _ = client
    assert client.patch('/api/v1/security/rules/'+str(uuid4()), json=patch, headers=headers('admin')).status_code == 422


def test_terminal_statuses():
    assert TRANSITIONS['resolved'] == TRANSITIONS['dismissed'] == set()
    assert 'resolved' in TRANSITIONS['investigating']


def test_conflicting_role_tokens_fail_closed(client, monkeypatch):
    client, _ = client
    monkeypatch.setenv('SECURITY_ADMIN_TOKEN', 'fixture-reader-'+'x'*40)
    assert client.get('/api/v1/security/rules', headers=headers('reader')).status_code == 503
