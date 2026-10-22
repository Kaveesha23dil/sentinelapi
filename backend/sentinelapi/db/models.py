"""Relational storage contracts. JSON values must pass the validation boundary."""
from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (Boolean, CheckConstraint, DateTime, ForeignKey, Index,
                        Integer, MetaData, Numeric, String, Text, UniqueConstraint, func)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention={
        'ix': 'ix_%(table_name)s_%(column_0_name)s',
        'uq': 'uq_%(table_name)s_%(column_0_name)s',
        'ck': 'ck_%(table_name)s_%(constraint_name)s',
        'fk': 'fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s',
        'pk': 'pk_%(table_name)s'})


class Identity:
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)


class Created:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class APIService(Identity, Created, Base):
    __tablename__ = 'api_services'
    name: Mapped[str] = mapped_column(String(128))
    version: Mapped[str] = mapped_column(String(64))
    context: Mapped[str] = mapped_column(String(256))
    gateway_api_id: Mapped[str | None] = mapped_column(String(128), unique=True)
    __table_args__ = (UniqueConstraint('name', 'version'),
                      CheckConstraint("length(name) > 0 AND length(version) > 0", name='identity_nonempty'))


class TrafficEvent(Identity, Created, Base):
    __tablename__ = 'traffic_events'
    api_service_id: Mapped[UUID] = mapped_column(ForeignKey('api_services.id', ondelete='RESTRICT'))
    event_id: Mapped[UUID] = mapped_column(unique=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    client_identifier: Mapped[str | None] = mapped_column(String(128))
    http_method: Mapped[str] = mapped_column(String(8))
    endpoint: Mapped[str] = mapped_column(String(512))
    status_code: Mapped[int] = mapped_column(Integer)
    latency_ms: Mapped[Decimal | None] = mapped_column(Numeric(14, 3))
    source: Mapped[str] = mapped_column(String(64))
    __table_args__ = (
        CheckConstraint('status_code BETWEEN 100 AND 599', name='status_range'),
        CheckConstraint("latency_ms >= 0 AND latency_ms < 'Infinity'::numeric", name='latency_nonnegative'),
        CheckConstraint("http_method IN ('GET','POST','PUT','PATCH','DELETE','HEAD','OPTIONS','TRACE','CONNECT')", name='method'),
        Index('ix_traffic_events_api_timestamp', 'api_service_id', 'timestamp'),
        Index('ix_traffic_events_timestamp', 'timestamp'),
        Index('ix_traffic_events_status_timestamp', 'status_code', 'timestamp'))


class TrafficAggregate(Identity, Base):
    __tablename__ = 'traffic_aggregates'
    api_service_id: Mapped[UUID] = mapped_column(ForeignKey('api_services.id', ondelete='RESTRICT'))
    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    window_end: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    request_count: Mapped[int] = mapped_column(Integer)
    error_4xx_count: Mapped[int] = mapped_column(Integer)
    error_5xx_count: Mapped[int] = mapped_column(Integer)
    average_latency_ms: Mapped[Decimal] = mapped_column(Numeric(14, 3))
    __table_args__ = (
        UniqueConstraint('api_service_id', 'window_start', 'window_end'),
        CheckConstraint('window_end > window_start', name='window_order'),
        CheckConstraint('request_count >= 0 AND error_4xx_count >= 0 AND error_5xx_count >= 0 AND error_4xx_count + error_5xx_count <= request_count', name='counts'),
        CheckConstraint("average_latency_ms >= 0 AND average_latency_ms < 'Infinity'::numeric", name='latency_nonnegative'))


class DetectionRule(Identity, Created, Base):
    __tablename__ = 'detection_rules'
    name: Mapped[str] = mapped_column(String(128), unique=True)
    rule_type: Mapped[str] = mapped_column(String(64))
    configuration: Mapped[dict] = mapped_column(JSONB)
    enabled: Mapped[bool] = mapped_column(Boolean, server_default='true')
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    __table_args__ = (CheckConstraint("jsonb_typeof(configuration) = 'object'", name='configuration_object'),)


class SecurityAlert(Identity, Base):
    __tablename__ = 'security_alerts'
    api_service_id: Mapped[UUID] = mapped_column(ForeignKey('api_services.id', ondelete='RESTRICT'))
    rule_id: Mapped[UUID | None] = mapped_column(ForeignKey('detection_rules.id', ondelete='SET NULL'))
    severity: Mapped[str] = mapped_column(String(16))
    status: Mapped[str] = mapped_column(String(16))
    risk_score: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    title: Mapped[str] = mapped_column(String(256))
    description: Mapped[str] = mapped_column(Text)
    first_detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    evidence: Mapped[list['AlertEvidence']] = relationship(back_populates='alert', passive_deletes=True)
    __table_args__ = (
        CheckConstraint("severity IN ('low','medium','high','critical')", name='severity'),
        CheckConstraint("status IN ('open','investigating','resolved','dismissed')", name='status'),
        CheckConstraint('risk_score BETWEEN 0 AND 100', name='risk_range'),
        CheckConstraint('last_detected_at >= first_detected_at', name='detection_order'),
        Index('ix_security_alerts_api_detected', 'api_service_id', 'last_detected_at'),
        Index('ix_security_alerts_status_severity', 'status', 'severity'),
        Index('ix_security_alerts_rule_id', 'rule_id'))


class AlertEvidence(Identity, Base):
    __tablename__ = 'alert_evidence'
    alert_id: Mapped[UUID] = mapped_column(ForeignKey('security_alerts.id', ondelete='CASCADE'), index=True)
    # References the public deduplication event UUID, not the internal row ID.
    event_id: Mapped[UUID | None] = mapped_column(ForeignKey('traffic_events.event_id', ondelete='SET NULL'), index=True)
    evidence_type: Mapped[str] = mapped_column(String(64))
    details: Mapped[dict] = mapped_column(JSONB)
    alert: Mapped[SecurityAlert] = relationship(back_populates='evidence')
    __table_args__ = (CheckConstraint("jsonb_typeof(details) = 'object'", name='details_object'),)


class AuditLog(Identity, Base):
    __tablename__ = 'audit_logs'
    actor_identifier: Mapped[str] = mapped_column(String(128))
    action: Mapped[str] = mapped_column(String(64))
    entity_type: Mapped[str] = mapped_column(String(64))
    entity_id: Mapped[str] = mapped_column(String(128))
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    # SQLAlchemy reserves Base.metadata; keep database name and Python name distinct.
    metadata_: Mapped[dict] = mapped_column('metadata', JSONB)
    __table_args__ = (CheckConstraint("jsonb_typeof(metadata) = 'object'", name='metadata_object'),
                      Index('ix_audit_logs_entity', 'entity_type', 'entity_id'))
