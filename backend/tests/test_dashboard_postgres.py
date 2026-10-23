"""Actual SQL dashboard checks using synthetic events in guarded test databases."""
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4
import pytest
from fastapi.testclient import TestClient
from test_postgres import engine, session
from sentinelapi.db.models import APIService,TrafficEvent,SecurityAlert,AlertEvidence,AuditLog
from sentinelapi.monitoring.app import app,session as monitor_session
from sentinelapi.detection.api import session as security_session


@pytest.fixture
def populated(session,monkeypatch):
    monkeypatch.setenv('MONITORING_API_TOKEN','fixture-monitor-'+'x'*40)
    monkeypatch.setenv('SECURITY_READER_TOKEN','fixture-reader-'+'x'*40)
    now=datetime(2026,10,23,8,tzinfo=timezone.utc)
    api=APIService(name='dashboard-fixture-'+uuid4().hex,version='test',context='/fixture')
    session.add(api);session.flush()
    events=[]
    for i,(method,status) in enumerate([('GET',200),('POST',404),('POST',500)]):
        event=TrafficEvent(event_id=uuid4(),api_service_id=api.id,timestamp=now+timedelta(seconds=i),
            http_method=method,endpoint='/fixture',status_code=status,source='wso2-gateway')
        session.add(event);events.append(event)
    session.flush()
    app.dependency_overrides[monitor_session]=lambda:session
    app.dependency_overrides[security_session]=lambda:session
    with TestClient(app) as client:
        yield SimpleNamespace(client=client,api=api,events=events,now=now,db=session,
            params={'start':now.isoformat(),'end':(now+timedelta(minutes=2)).isoformat(),'api_id':str(api.id)},
            headers={'Authorization':'Bearer fixture-monitor-'+'x'*40})
    app.dependency_overrides.clear()


def test_real_sql_filters_and_counts(populated):
    p=populated
    r=p.client.get('/api/v1/monitoring/events',params=p.params|{'http_method':'POST','status_code':404},headers=p.headers)
    assert r.status_code==200 and r.json()['total']==1
    assert r.json()['events'][0]['event_id']==str(p.events[1].event_id)


def test_real_sql_series_endpoints_inventory(populated):
    p=populated
    series=p.client.get('/api/v1/monitoring/timeseries',params=p.params,headers=p.headers).json()
    assert series['points']==[{'timestamp':p.now.isoformat(),'requests':3}]
    routes=p.client.get('/api/v1/monitoring/endpoints',params=p.params,headers=p.headers).json()
    assert sum(e['request_count'] for e in routes['endpoints'])==3
    services=p.client.get('/api/v1/monitoring/services',params={k:v for k,v in p.params.items() if k!='api_id'}|{'page_size':100},headers=p.headers).json()
    service=next(s for s in services['services'] if s['id']==str(p.api.id))
    assert service['request_count']==3 and service['health'] is None


def test_real_sql_incident_evidence_and_sanitized_history(populated):
    p=populated
    alert=SecurityAlert(api_service_id=p.api.id,severity='medium',status='investigating',risk_score=50,
        title='Synthetic dashboard fixture',description='Not live evidence',first_detected_at=p.now,last_detected_at=p.now)
    p.db.add(alert);p.db.flush()
    p.db.add(AlertEvidence(alert_id=alert.id,event_id=p.events[0].event_id,evidence_type='fixture',details={}))
    p.db.add(AuditLog(actor_identifier='fixture-private-identity',action='alert.status',entity_type='security_alert',
        entity_id=str(alert.id),metadata_={'from':'open','to':'investigating','private':'not-returned'}))
    p.db.flush()
    headers={'Authorization':'Bearer fixture-reader-'+'x'*40}
    events=p.client.get(f'/api/v1/security/alerts/{alert.id}/events',headers=headers).json()
    assert len(events['events'])==1 and 'client_identifier' not in events['events'][0]
    history=p.client.get(f'/api/v1/security/alerts/{alert.id}/history',headers=headers)
    assert history.status_code==200 and history.json()['history'][0]['to']=='investigating'
    assert 'private' not in history.text
