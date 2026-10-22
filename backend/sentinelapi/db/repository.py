"""Transactions belong to callers. No commits, raw SQL interpolation or secret logs."""
from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from .models import APIService, AlertEvidence, SecurityAlert, TrafficEvent
from .schemas import AlertInput, EventInput, EvidenceDetails, ServiceInput


class DuplicateEventConflict(ValueError):
    """The UUID was already used for different data."""


class Repository:
    def __init__(self, session):
        self.session = session

    def create_service(self, data: ServiceInput):
        row = APIService(**data.model_dump())
        self.session.add(row)
        self.session.flush()
        return row

    def add_event(self, data: EventInput):
        values = data.model_dump()
        statement = insert(TrafficEvent).values(**values).on_conflict_do_nothing(
            index_elements=['event_id']).returning(TrafficEvent.id)
        created_id = self.session.scalar(statement)
        row = self.session.scalar(select(TrafficEvent).where(TrafficEvent.event_id == data.event_id))
        if created_id is None and any(getattr(row, key) != value for key, value in values.items()):
            raise DuplicateEventConflict('Event UUID already belongs to a different record')
        return row, created_id is not None

    def events(self, *, api_service_id: UUID, start: datetime, end: datetime, limit=100):
        if start.tzinfo is None or end.tzinfo is None or end <= start or not 1 <= limit <= 1000:
            raise ValueError('Use an aware ordered time range and limit 1..1000')
        return list(self.session.scalars(select(TrafficEvent).where(
            TrafficEvent.api_service_id == api_service_id,
            TrafficEvent.timestamp >= start, TrafficEvent.timestamp < end,
        ).order_by(TrafficEvent.timestamp, TrafficEvent.id).limit(limit)))

    def create_alert(self, data: AlertInput, details: EvidenceDetails, event_id=None):
        if event_id is not None:
            event = self.session.scalar(select(TrafficEvent).where(TrafficEvent.event_id == event_id))
            if event is None or event.api_service_id != data.api_service_id:
                raise ValueError('Evidence must reference an event for the alert API')
        alert = SecurityAlert(**data.model_dump())
        alert.evidence.append(AlertEvidence(event_id=event_id, evidence_type='demo-test',
                                            details=details.model_dump()))
        self.session.add(alert)
        self.session.flush()
        return alert
