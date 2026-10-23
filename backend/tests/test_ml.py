"""Unit tests use explicitly synthetic data; no live/DB proof implied."""
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock
import pytest
from fastapi.testclient import TestClient
from sentinelapi.ml.worker import run_once, configured_model, persist
from sentinelapi.monitoring.app import app

from test_ml_model import trained

START = datetime(2026,1,1,tzinfo=timezone.utc)


def test_unconfigured_never_touches_database(monkeypatch):
    monkeypatch.delenv('ML_MODEL_DIR',raising=False)
    engine=Mock()
    assert run_once(engine)['state']=='unconfigured'
    engine.assert_not_called()
    with pytest.raises(ValueError): configured_model()


def test_duplicate_score_no_alert(trained):
    _,heldout,_,meta=trained
    db=Mock(); db.scalar.return_value=None
    w=replace(heldout[0],api_id='00000000-0000-0000-0000-000000000001')
    assert persist(db,w,{'decision_score':-.2,'anomaly':True},meta,START) is False
    db.add.assert_not_called()


def test_worker_finalization_and_failure_watermark(monkeypatch):
    from contextlib import contextmanager
    from types import SimpleNamespace
    from datetime import timedelta
    import sentinelapi.ml.worker as worker
    monkeypatch.setenv('ML_MODEL_DIR','fixture-not-loaded')
    checkpoint=SimpleNamespace(watermark=START)
    db=Mock()
    db.scalar.return_value=True
    db.get.return_value=checkpoint
    db.scalars.return_value.all.return_value=[]
    @contextmanager
    def transaction(_):
        yield db
    monkeypatch.setattr(worker,'transaction',transaction)
    monkeypatch.setattr(worker,'configured_model',lambda: (None,{'version':'fixture',
        'api_id':'00000000-0000-0000-0000-000000000001'}))
    assert worker.run_once(None,START+timedelta(seconds=179))['state']=='caught-up'
    assert checkpoint.watermark==START
    assert worker.run_once(None,START+timedelta(seconds=180))['state']=='processed'
    assert checkpoint.watermark==START+timedelta(minutes=1)
    # Overflow must not advance the watermark, including empty/normal histories.
    db.scalars.return_value.all.return_value=[None]*10001
    with pytest.raises(ValueError,match='capacity'):
        worker.run_once(None,START+timedelta(minutes=5))
    assert checkpoint.watermark==START+timedelta(minutes=1)


def test_experimental_model_requires_explicit_enable(monkeypatch):
    import sentinelapi.ml.model as model
    monkeypatch.setenv('ML_MODEL_DIR','fixture-not-loaded')
    monkeypatch.setenv('ML_APPROVED_SHA256','fixture-digest')
    monkeypatch.delenv('ML_ALLOW_EXPERIMENTAL',raising=False)
    monkeypatch.setattr(model,'load',lambda *_:(None,{'production_ready':False}))
    with pytest.raises(ValueError,match='Experimental'): configured_model()
    monkeypatch.setenv('ML_ALLOW_EXPERIMENTAL','true')
    assert configured_model()[1]['production_ready'] is False


@pytest.mark.parametrize('route',['model','health','evaluation','anomalies'])
def test_routes_require_authentication(monkeypatch,route):
    monkeypatch.setenv('SECURITY_READER_TOKEN','fixture-reader-'+'x'*40)
    with TestClient(app) as client:
        assert client.get('/api/v1/ml/'+route).status_code==401


def test_authenticated_unavailable_safe(monkeypatch):
    monkeypatch.setenv('SECURITY_READER_TOKEN','fixture-reader-'+'x'*40)
    monkeypatch.delenv('ML_MODEL_DIR',raising=False)
    monkeypatch.delenv('ML_EVALUATION_FILE',raising=False)
    headers={'Authorization':'Bearer fixture-reader-'+'x'*40}
    with TestClient(app) as client:
        assert client.get('/api/v1/ml/model',headers=headers).json()['state']=='unavailable'
        assert client.get('/api/v1/ml/health',headers=headers).status_code==503
        assert client.get('/api/v1/ml/evaluation',headers=headers).status_code==503
        assert client.get('/api/v1/ml/anomalies?page_size=101',headers=headers).status_code==422


def test_ml_additive_migration():
    from importlib.util import spec_from_file_location, module_from_spec
    from io import StringIO
    from alembic.migration import MigrationContext
    from alembic.operations import Operations
    from sentinelapi.db.models import Base
    path=Path(__file__).parents[1]/'migrations/versions/b7d000000001_ml_windows.py'
    spec=spec_from_file_location('ml_migration',path); mod=module_from_spec(spec); spec.loader.exec_module(mod)
    output=StringIO()
    context=MigrationContext.configure(dialect_name='postgresql',opts={'as_sql':True,'output_buffer':output,'target_metadata':Base.metadata})
    with Operations.context(context): mod.upgrade()
    sql=output.getvalue()
    assert 'CREATE TABLE ml_windows' in sql and 'DROP ' not in sql and 'DELETE FROM ' not in sql
    assert 'UNIQUE (window_id, model_version)' in sql
