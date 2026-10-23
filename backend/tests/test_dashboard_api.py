"""HTTP/SQL-contract tests with mocked DB; not genuine PostgreSQL integration."""
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4
import pytest
from fastapi.testclient import TestClient
from sentinelapi.monitoring.app import app, session
from sentinelapi.detection.api import session as security_session


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv('MONITORING_API_TOKEN', 'fixture-monitor-'+'x'*40)
    for role in ['reader','analyst','admin']:
        monkeypatch.setenv('SECURITY_'+role.upper()+'_TOKEN','fixture-'+role+'-'+'x'*40)
    db=Mock()
    app.dependency_overrides[session]=lambda:db
    app.dependency_overrides[security_session]=lambda:db
    with TestClient(app) as client:
        yield client,db
    app.dependency_overrides.clear()


def header(role='monitor'):
    return {'Authorization':'Bearer fixture-'+role+'-'+'x'*40}


@pytest.mark.parametrize('route',['session','services','timeseries','endpoints'])
def test_dashboard_routes_require_monitor_auth(client,route):
    http,db=client
    assert http.get('/api/v1/monitoring/'+route).status_code==401
    db.execute.assert_not_called()


@pytest.mark.parametrize('role,expected',[('reader',['security:read']),('analyst',['security:read','alerts:update']),('admin',['security:read','alerts:update','rules:update'])])
def test_server_capabilities(client,role,expected):
    http,db=client
    assert http.get('/api/v1/security/session',headers=header(role)).json()=={'role':role,'capabilities':expected}
    db.execute.assert_not_called()


def test_monitor_session(client):
    http,_=client
    assert http.get('/api/v1/monitoring/session',headers=header()).json()=={'role':'monitor','capabilities':['monitoring:read']}


@pytest.mark.parametrize('params',[{'http_method':'INVALID'},{'status_code':600},{'page_size':101},{'start':'private-filter-value'}])
def test_traffic_filter_validation(client,params):
    http,_=client
    r=http.get('/api/v1/monitoring/events',params=params,headers=header())
    assert r.status_code==422 and 'private-filter-value' not in r.text


def test_method_and_status_are_server_side_filters(client):
    http,db=client;db.scalar.return_value=0;db.scalars.return_value.all.return_value=[]
    r=http.get('/api/v1/monitoring/events',params={'http_method':'POST','status_code':404},headers=header())
    assert r.status_code==200 and r.json()['events']==[]
    query=db.scalars.call_args.args[0]
    assert {'POST',404} <= set(query.compile().params.values())


def test_service_contract_and_timeseries_no_invented_empty_buckets(client):
    http,db=client;now=datetime(2026,10,23,tzinfo=timezone.utc)
    service=SimpleNamespace(id=uuid4(),name='Fixture API',version='test',context='/fixture')
    db.scalar.return_value=1;db.execute.return_value=[(service,7,now,now)]
    r=http.get('/api/v1/monitoring/services',headers=header())
    assert r.status_code==200 and r.json()['services'][0]['health'] is None
    db.execute.return_value=[(now,7)]
    r=http.get('/api/v1/monitoring/timeseries',headers=header())
    assert r.status_code==200 and len(r.json()['points'])==1 and r.json()['coverage']=='observed-events-only'


@pytest.mark.parametrize('suffix',['events','history'])
def test_incident_extensions_auth_and_missing_record(client,suffix):
    http,db=client;db.get.return_value=None
    path=f'/api/v1/security/alerts/{uuid4()}/{suffix}'
    assert http.get(path).status_code==401
    assert http.get(path,headers=header('reader')).status_code==404
