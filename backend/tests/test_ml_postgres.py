"""Real PostgreSQL ML persistence checks: synthetic fixtures, never live proof.

Use only the existing guarded sentinelapi_test_* database runner after migration.
"""
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from sqlalchemy import select, func
from test_postgres import engine, session
from sentinelapi.db.models import APIService, TrafficEvent, MLWindow, AlertEvidence, SecurityAlert
from sentinelapi.ml.features import Event, aggregate, SCHEMA
from sentinelapi.ml.worker import persist


def test_ml_alert_atomic_evidence_and_idempotence(session):
    now = datetime(2026,1,1,tzinfo=timezone.utc)
    api=APIService(name='ml-synthetic-'+uuid4().hex,version='test',context='/fixture')
    session.add(api); session.flush()
    events=[]
    for i in range(5):
        event_id=uuid4()
        session.add(TrafficEvent(api_service_id=api.id,event_id=event_id,timestamp=now,
            http_method='GET',endpoint='/fixture',status_code=500,source='synthetic-test'))
        events.append(Event(str(event_id),str(api.id),now,500,'GET','/fixture'))
    session.flush()
    w=aggregate(events,coverage_start=now,complete_through=now+timedelta(minutes=1))[0]
    result={'decision_score':-.123456789,'anomaly':True}
    meta={'version':'iforest-test','provenance':'synthetic-controlled'}
    assert persist(session,w,result,meta,now+timedelta(minutes=3))
    assert not persist(session,w,result,meta,now+timedelta(minutes=3))
    session.flush()
    row=session.scalar(select(MLWindow).where(MLWindow.window_id==w.identifier))
    assert row.schema_version==SCHEMA and row.decision_score==result['decision_score']
    alert=session.get(SecurityAlert,row.alert_id)
    assert 'does not establish malicious intent' in alert.description
    assert session.scalar(select(func.count()).select_from(AlertEvidence).where(AlertEvidence.alert_id==alert.id))==6
    evidence=session.scalar(select(AlertEvidence).where(AlertEvidence.alert_id==alert.id,AlertEvidence.evidence_type=='ml_window'))
    assert evidence.details['decision_score']==result['decision_score']


def test_normal_window_persists_without_alert(session):
    now=datetime(2026,1,1,tzinfo=timezone.utc)
    api=APIService(name='ml-normal-'+uuid4().hex,version='test',context='/fixture')
    session.add(api);session.flush()
    events=[Event(str(uuid4()),str(api.id),now,200,'GET','/fixture') for _ in range(5)]
    w=aggregate(events,coverage_start=now,complete_through=now+timedelta(minutes=1))[0]
    assert persist(session,w,{'decision_score':.2,'anomaly':False},
        {'version':'iforest-test','provenance':'synthetic-controlled'},now)
    session.flush()
    row=session.scalar(select(MLWindow).where(MLWindow.window_id==w.identifier))
    assert row.alert_id is None and not row.anomaly
