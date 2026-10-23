"""Monitoring and collector DB tests execute only in the dedicated test database."""
from datetime import datetime, timedelta, timezone
import os
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from sentinelapi.db.models import APIService, TrafficEvent
from sentinelapi.db.session import make_engine
from sentinelapi.monitoring.app import app, session as get_session
from traffic_collector.config import Config
from traffic_collector.parser import parse
from traffic_collector.writer import persist


@pytest.fixture
def db_engine():
    if not os.getenv('POSTGRES_DB', '').startswith('sentinelapi_test_'):
        pytest.fail('Refusing tests outside disposable test database')
    engine = make_engine()
    yield engine
    engine.dispose()


@pytest.fixture
def client(db_engine, monkeypatch):
    token = 'synthetic-monitoring-test-value-00000000'
    monkeypatch.setenv('MONITORING_API_TOKEN', token)
    with db_engine.connect() as connection:
        outer = connection.begin()
        with Session(connection, join_transaction_mode='create_savepoint') as db:
            app.dependency_overrides[get_session] = lambda: db
            with TestClient(app) as client:
                yield client, db, token
            app.dependency_overrides.clear()
        outer.rollback()


def test_monitoring_authentication(client):
    client, _, _ = client
    for path in ['overview', 'events', 'health', f'apis/{uuid4()}/stats']:
        assert client.get('/api/v1/monitoring/'+path).status_code == 401
    assert client.get('/api/v1/monitoring/events', headers={'Authorization': 'Bearer invalid'}).status_code == 401


def test_monitoring_pagination_filters_breakdown(client):
    client, db, token = client
    api = APIService(name='synthetic-monitor-'+uuid4().hex, version='test', context='/synthetic')
    other = APIService(name='synthetic-other-'+uuid4().hex, version='test', context='/synthetic')
    db.add_all([api, other])
    db.flush()
    now = datetime.now(timezone.utc)
    for index, (service_id, status, timestamp) in enumerate([
        (api.id, 200, now), (api.id, 404, now+timedelta(seconds=1)),
        (other.id, 500, now), (api.id, 200, now-timedelta(days=2))]):
        db.add(TrafficEvent(api_service_id=service_id, event_id=uuid4(), timestamp=timestamp,
            http_method='GET', endpoint='/health', status_code=status, source='wso2-gateway'))
    db.flush()
    headers = {'Authorization': 'Bearer '+token}
    params = {'api_id': str(api.id), 'start': (now-timedelta(seconds=1)).isoformat(),
              'end': (now+timedelta(minutes=1)).isoformat(), 'page_size': 1}
    first = client.get('/api/v1/monitoring/events', params=params, headers=headers).json()
    second = client.get('/api/v1/monitoring/events', params=params | {'page': 2}, headers=headers).json()
    assert first['total'] == 2 and len(first['events']) == 1
    assert first['events'][0]['event_id'] != second['events'][0]['event_id']
    summary = client.get('/api/v1/monitoring/overview', params=params, headers=headers).json()
    assert summary['request_count'] == 2 and summary['status_breakdown'] == {'200': 1, '404': 1}
    assert summary['average_latency_ms'] is None
    stats = client.get(f'/api/v1/monitoring/apis/{api.id}/stats', params=params, headers=headers)
    assert stats.status_code == 200 and stats.json()['request_count'] == 2


@pytest.mark.parametrize('params', [{'page': 0}, {'page_size': 101}, {'api_id': 'bad'},
    {'start': '2026-10-22T00:00:00'}, {'start': 'private-value'},
    {'start': '2020-01-01T00:00:00Z', 'end': '2026-01-01T00:00:00Z'}])
def test_monitoring_validation_does_not_echo_inputs(client, params):
    client, _, token = client
    response = client.get('/api/v1/monitoring/events', params=params, headers={'Authorization': 'Bearer '+token})
    assert response.status_code == 422
    assert 'private-value' not in response.text


def test_collector_real_database_deduplication(db_engine):
    config = Config(str(uuid4()), 'synthetic-collector-'+uuid4().hex, '/democommerceapi', '1.0.0')
    data = {'flow': 'RESPONSE_OUT', 'verb': 'GET', 'correlationId': str(uuid4()),
            'apiTo': '/democommerceapi/1.0.0/health', 'statusCode': 200}
    import json
    flow = parse('[2026-10-22 09:55:28,629]  INFO {API_LOG} '+config.api_name+' - '+json.dumps(data), config)
    assert persist(db_engine, [flow, flow], config) == 1
    assert persist(db_engine, [flow], config) == 0
    with Session(db_engine) as db:
        api = db.scalar(select(APIService).where(APIService.gateway_api_id == config.api_id))
        rows = db.scalars(select(TrafficEvent).where(TrafficEvent.api_service_id == api.id)).all()
        assert len(rows) == 1 and rows[0].latency_ms is None


def test_monitoring_stale_collector_is_not_healthy(client, monkeypatch):
    import sentinelapi.monitoring.app as module
    testclient, _, token = client
    monkeypatch.setattr(module, 'collector_status', lambda: False)
    response = testclient.get('/api/v1/monitoring/health', headers={'Authorization': 'Bearer '+token})
    assert response.status_code == 503 and response.json()['collector'] == 'stale-or-unavailable'


def test_monitoring_database_failure_is_safe(client):
    from sqlalchemy.exc import OperationalError
    testclient, _, token = client
    class FailedDatabase:
        def execute(self, *args):
            raise OperationalError('synthetic-private-query', {}, RuntimeError('synthetic-private-detail'))
    app.dependency_overrides[get_session] = lambda: FailedDatabase()
    response = testclient.get('/api/v1/monitoring/health', headers={'Authorization': 'Bearer '+token})
    assert response.status_code == 503
    assert 'synthetic-private' not in response.text
