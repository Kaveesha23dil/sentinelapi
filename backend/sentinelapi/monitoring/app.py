import hmac
import json
import os
import time
from datetime import datetime, timedelta, timezone
from contextlib import asynccontextmanager
from functools import lru_cache
from pathlib import Path
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import func, select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from sentinelapi.db.models import APIService, TrafficEvent
from sentinelapi.db.session import make_engine

@asynccontextmanager
async def lifespan(application):
    yield
    if engine.cache_info().currsize:
        engine().dispose()
        engine.cache_clear()


app = FastAPI(title='SentinelAPI monitoring', docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan)
bearer = HTTPBearer(auto_error=False)


def authorize(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)):
    expected = os.getenv('MONITORING_API_TOKEN', '')
    if len(expected) < 32 or expected.startswith('REPLACE_WITH_'):
        raise HTTPException(503, 'Monitoring authentication not configured')
    if not credentials or not hmac.compare_digest(credentials.credentials.encode(), expected.encode()):
        raise HTTPException(401, 'Authentication required', headers={'WWW-Authenticate': 'Bearer'})


@lru_cache
def engine():
    return make_engine()


def session():
    with Session(engine()) as value:
        yield value


@app.exception_handler(SQLAlchemyError)
def database_error(_, error):
    return JSONResponse(status_code=503, content={'detail': 'Monitoring database unavailable'})


@app.exception_handler(RequestValidationError)
def validation_error(_, error):
    return JSONResponse(status_code=422, content={'detail': 'Invalid query parameters'})


def period(start: datetime | None, end: datetime | None):
    end = end or datetime.now(timezone.utc)
    start = start or end - timedelta(hours=24)
    if start.tzinfo is None or end.tzinfo is None or not start < end or end-start > timedelta(days=31):
        raise HTTPException(422, 'Use an aware UTC time range of at most 31 days')
    return start.astimezone(timezone.utc), end.astimezone(timezone.utc)


def filters(start, end, api_id):
    clauses = [TrafficEvent.source == 'wso2-gateway', TrafficEvent.timestamp >= start, TrafficEvent.timestamp < end]
    if api_id:
        clauses.append(TrafficEvent.api_service_id == api_id)
    return clauses


def summary(db, start, end, api_id):
    clauses = filters(start, end, api_id)
    breakdown = dict(db.execute(select(TrafficEvent.status_code, func.count()).where(*clauses)
                                .group_by(TrafficEvent.status_code)).all())
    latency = db.scalar(select(func.avg(TrafficEvent.latency_ms)).where(*clauses))
    return {'start': start, 'end': end, 'request_count': sum(breakdown.values()),
            'error_4xx_count': sum(count for status, count in breakdown.items() if 400 <= status < 500),
            'error_5xx_count': sum(count for status, count in breakdown.items() if 500 <= status < 600),
            'average_latency_ms': float(latency) if latency is not None else None,
            'status_breakdown': breakdown}


@app.get('/api/v1/monitoring/overview', dependencies=[Depends(authorize)])
def overview(start: datetime | None = None, end: datetime | None = None,
             api_id: UUID | None = None, db: Session = Depends(session)):
    start, end = period(start, end)
    return summary(db, start, end, api_id)


@app.get('/api/v1/monitoring/events', dependencies=[Depends(authorize)])
def events(start: datetime | None = None, end: datetime | None = None, api_id: UUID | None = None,
           page: int = Query(1, ge=1, le=10000), page_size: int = Query(50, ge=1, le=100),
           db: Session = Depends(session)):
    start, end = period(start, end)
    clauses = filters(start, end, api_id)
    total = db.scalar(select(func.count()).select_from(TrafficEvent).where(*clauses))
    rows = db.scalars(select(TrafficEvent).where(*clauses)
        .order_by(TrafficEvent.timestamp.desc(), TrafficEvent.id.desc()).offset((page-1)*page_size).limit(page_size)).all()
    return {'page': page, 'page_size': page_size, 'total': total, 'events': [
        {key: getattr(row, key) for key in ['event_id', 'api_service_id', 'timestamp', 'http_method',
          'endpoint', 'status_code', 'latency_ms', 'client_identifier', 'source']} for row in rows]}


@app.get('/api/v1/monitoring/apis/{api_id}/stats', dependencies=[Depends(authorize)])
def stats(api_id: UUID, start: datetime | None = None, end: datetime | None = None,
          db: Session = Depends(session)):
    start, end = period(start, end)
    if db.get(APIService, api_id) is None:
        raise HTTPException(404, 'API service not found')
    return {'api_service_id': api_id, **summary(db, start, end, api_id)}


def collector_status():
    try:
        value = json.loads(Path('/collector-state/health.json').read_text())
        return value['ok'] and time.time() - value['checked_at'] < 60
    except (OSError, ValueError, KeyError):
        return False


@app.get('/api/v1/monitoring/health', dependencies=[Depends(authorize)])
def health(db: Session = Depends(session)):
    db.execute(text('SELECT 1'))
    fresh = collector_status()
    if not fresh:
        return JSONResponse(status_code=503, content={'database': 'available', 'collector': 'stale-or-unavailable'})
    return {'database': 'available', 'collector': 'healthy'}


from sentinelapi.detection.api import router as security_router
app.include_router(security_router)
