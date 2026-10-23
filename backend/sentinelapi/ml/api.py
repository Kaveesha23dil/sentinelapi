"""Read-only ML monitoring, sharing Step 6 service-role authentication."""
import json
import os
import platform
from importlib.metadata import version
from datetime import datetime
from pathlib import Path
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from sentinelapi.detection.api import principal, session, period
from sentinelapi.db.models import MLWindow

router = APIRouter(prefix='/api/v1/ml', dependencies=[Depends(principal)])


def readiness():
    try:
        # Health validates metadata/hash without deserializing a model in HTTP.
        import hashlib
        from .features import FEATURES, SCHEMA
        directory = Path(os.environ['ML_MODEL_DIR'])
        metadata = json.loads((directory/'metadata.json').read_text(encoding='utf-8'))
        digest = hashlib.sha256((directory/'model.joblib').read_bytes()).hexdigest()
        if digest != os.environ['ML_APPROVED_SHA256'] or digest != metadata['artifact_sha256']:
            raise ValueError()
        if metadata['schema'] != SCHEMA or metadata['features'] != list(FEATURES):
            raise ValueError()
        if metadata['python'] != platform.python_version() or any(metadata[key] != version(package)
            for key,package in [('sklearn','scikit-learn'),('numpy','numpy'),('joblib','joblib')]):
            raise ValueError()
        return dict(state='experimental' if not metadata['production_ready'] else 'ready',
            model_version=metadata['version'], provenance=metadata['provenance'],
            production_ready=metadata['production_ready'], features=metadata['features'],
            schema=metadata['schema'], trained_at=metadata['trained_at'],
            score_calibration=None, worker_status='not-checked-by-artifact-health',
            deployment_enabled=metadata['production_ready'] or os.getenv('ML_ALLOW_EXPERIMENTAL')=='true')
    except (OSError, ValueError, KeyError, TypeError):
        return {'state':'unavailable','production_ready':False}


@router.get('/model')
def model():
    return readiness()


@router.get('/health')
def health():
    result = readiness()
    return JSONResponse(status_code=503 if result['state']=='unavailable' else 200, content=result)


@router.get('/evaluation')
def evaluation():
    try:
        value = json.loads(Path(os.environ['ML_EVALUATION_FILE']).read_text(encoding='utf-8'))
        return {k:value[k] for k in ['provenance','production_ready','model_version',
            'evaluation_date','evaluation_windows','ml','rules','detection_latency_seconds']}
    except (OSError,ValueError,KeyError,TypeError):
        return JSONResponse(status_code=503,content={'detail':'Evaluation unavailable'})


@router.get('/anomalies')
def anomalies(start: datetime | None=None, end: datetime | None=None, api_id: UUID | None=None,
              model_version: str | None=Query(None,max_length=64),
              page: int=Query(1,ge=1,le=10000),page_size: int=Query(50,ge=1,le=100),
              db: Session=Depends(session)):
    start,end = period(start,end)
    filters=[MLWindow.anomaly.is_(True),MLWindow.window_start>=start,MLWindow.window_start<end]
    if api_id:
        filters.append(MLWindow.api_service_id==api_id)
    if model_version:
        filters.append(MLWindow.model_version==model_version)
    rows=db.scalars(select(MLWindow).where(*filters).order_by(MLWindow.window_start.desc(),MLWindow.id)
        .offset((page-1)*page_size).limit(page_size))
    return dict(page=page,page_size=page_size,
        total=db.scalar(select(func.count()).select_from(MLWindow).where(*filters)),
        anomalies=[{k:getattr(r,k) for k in ['window_id','window_start','window_end',
            'api_service_id','model_version','schema_version','decision_score','features','provenance','alert_id']} for r in rows])
