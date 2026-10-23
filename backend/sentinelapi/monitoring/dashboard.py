"""Read-only dashboard queries over actual gateway telemetry; no demo fallback."""
from datetime import datetime
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from sentinelapi.db.models import APIService, TrafficEvent
from .app import authorize, session, period, filters

router = APIRouter(prefix='/api/v1/monitoring', dependencies=[Depends(authorize)])


@router.get('/session')
def current_session():
    return {'role': 'monitor', 'capabilities': ['monitoring:read']}


@router.get('/services')
def services(start: datetime | None = None, end: datetime | None = None,
             page: int = Query(1, ge=1, le=10000), page_size: int = Query(50, ge=1, le=100),
             db: Session = Depends(session)):
    start, end = period(start, end)
    counts = select(TrafficEvent.api_service_id, func.count().label('requests'),
        func.min(TrafficEvent.timestamp).label('first_event'),
        func.max(TrafficEvent.timestamp).label('last_event')).where(*filters(start, end, None))
    counts = counts.group_by(TrafficEvent.api_service_id).subquery()
    rows = db.execute(select(APIService, counts.c.requests, counts.c.first_event, counts.c.last_event)
        .outerjoin(counts, APIService.id == counts.c.api_service_id)
        .order_by(APIService.name, APIService.id).offset((page-1)*page_size).limit(page_size))
    return {'page': page, 'page_size': page_size,
        'total': db.scalar(select(func.count()).select_from(APIService)), 'services': [
            {'id': row.id, 'name': row.name, 'version': row.version, 'context': row.context,
             'request_count': count or 0, 'first_event': first, 'last_event': last,
             'health': None, 'coverage': 'observed-events-only'} for row, count, first, last in rows]}


@router.get('/timeseries')
def timeseries(start: datetime | None = None, end: datetime | None = None,
               api_id: UUID | None = None, db: Session = Depends(session)):
    start, end = period(start, end)
    # At most 745 hourly or 1441 minute bins including partial boundaries.
    bucket = func.date_trunc('minute' if (end-start).total_seconds() <= 86400 else 'hour', TrafficEvent.timestamp)
    rows = db.execute(select(bucket, func.count()).where(*filters(start, end, api_id))
        .group_by(bucket).order_by(bucket))
    return {'start': start, 'end': end, 'bucket_seconds': 60 if (end-start).total_seconds() <= 86400 else 3600,
            'points': [{'timestamp': stamp, 'requests': count} for stamp, count in rows],
            'coverage': 'observed-events-only'}


@router.get('/endpoints')
def endpoints(start: datetime | None = None, end: datetime | None = None,
              api_id: UUID | None = None, limit: int = Query(5, ge=1, le=20),
              db: Session = Depends(session)):
    start, end = period(start, end)
    rows = db.execute(select(TrafficEvent.endpoint, TrafficEvent.http_method, func.count().label('requests'))
        .where(*filters(start, end, api_id)).group_by(TrafficEvent.endpoint, TrafficEvent.http_method)
        .order_by(func.count().desc(), TrafficEvent.endpoint, TrafficEvent.http_method).limit(limit))
    return {'endpoints': [{'endpoint': endpoint, 'http_method': method, 'request_count': count}
                          for endpoint, method, count in rows]}
