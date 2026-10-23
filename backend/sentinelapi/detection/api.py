"""Sanitized alert management using deployment-scoped service roles."""
import hmac
import os
from datetime import datetime
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict, model_validator
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from sentinelapi.db.models import AlertEvidence, AuditLog, DetectionRule, SecurityAlert
from .rules import configuration

router = APIRouter(prefix='/api/v1/security')
bearer = HTTPBearer(auto_error=False)
Status = Literal['open', 'investigating', 'resolved', 'dismissed']
Severity = Literal['low', 'medium', 'high', 'critical']
TRANSITIONS = {'open': {'investigating', 'resolved', 'dismissed'},
               'investigating': {'resolved', 'dismissed'}, 'resolved': set(), 'dismissed': set()}


def session():
    from sentinelapi.monitoring.app import session as monitoring_session
    yield from monitoring_session()


def period(start, end):
    from sentinelapi.monitoring.app import period as monitoring_period
    return monitoring_period(start, end)


def principal(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)):
    tokens = {role: os.getenv(f'SECURITY_{role.upper()}_TOKEN', '') for role in ['reader', 'analyst', 'admin']}
    configured = {role: token for role, token in tokens.items()
                  if len(token) >= 32 and not token.startswith('REPLACE_WITH_')}
    if not configured or len(set(configured.values())) != len(configured):
        raise HTTPException(503, 'Security authentication not configured')
    if credentials:
        for role, token in configured.items():
            if hmac.compare_digest(credentials.credentials.encode(), token.encode()):
                return role
    raise HTTPException(401, 'Authentication required', headers={'WWW-Authenticate': 'Bearer'})


def require(role, allowed):
    if role not in allowed:
        raise HTTPException(403, 'Insufficient role')


class AlertPatch(BaseModel):
    model_config = ConfigDict(extra='forbid')
    status: Status


class RulePatch(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    enabled: bool | None = None
    configuration: dict | None = None

    @model_validator(mode='after')
    def nonempty(self):
        if not self.model_fields_set or any(getattr(self, field) is None for field in self.model_fields_set):
            raise ValueError('Provide enabled or configuration')
        return self


def alert_view(row):
    # Older demo alerts are preserved and explicitly distinguished.
    return {key: getattr(row, key) for key in ['id', 'api_service_id', 'rule_id', 'rule_version',
        'severity', 'status', 'risk_score', 'first_detected_at', 'last_detected_at',
        'window_start', 'window_end', 'measured_value', 'threshold']} | {
        'explanation': row.description if row.incident_fingerprint else 'Legacy demonstration alert',
        'risk_score_basis': 'Fixed medium-severity policy score; not a probability' if row.incident_fingerprint else 'legacy',
        'origin': 'detector' if row.incident_fingerprint else 'legacy'}


def rule_view(row):
    try:
        config = configuration(row.rule_type, row.configuration).model_dump()
    except ValueError:
        config = None
    return {'id': row.id, 'name': row.name if row.rule_type in
            ['error_rate', 'request_flood', 'enumeration', 'auth_failures', 'unusual_activity'] else 'legacy',
            'rule_type': row.rule_type if config else 'unsupported', 'configuration': config,
            'enabled': row.enabled, 'live_supported': row.rule_type == 'error_rate' and config is not None}


def audit(db, role, action, entity, entity_id, changes):
    db.add(AuditLog(actor_identifier='security:'+role, action=action, entity_type=entity,
                    entity_id=str(entity_id), metadata_=changes))


def clauses(start, end, severity, status, api_id, rule_id):
    start, end = period(start, end)
    result = [SecurityAlert.last_detected_at >= start, SecurityAlert.last_detected_at < end]
    for field, value in [(SecurityAlert.severity, severity), (SecurityAlert.status, status),
                         (SecurityAlert.api_service_id, api_id), (SecurityAlert.rule_id, rule_id)]:
        if value is not None:
            result.append(field == value)
    return result


@router.get('/alerts')
def alerts(start: datetime | None = None, end: datetime | None = None, severity: Severity | None = None,
           status: Status | None = None, api_id: UUID | None = None, rule_id: UUID | None = None,
           page: int = Query(1, ge=1, le=10000), page_size: int = Query(50, ge=1, le=100),
           role=Depends(principal), db: Session = Depends(session)):
    filters = clauses(start, end, severity, status, api_id, rule_id)
    total = db.scalar(select(func.count()).select_from(SecurityAlert).where(*filters))
    rows = db.scalars(select(SecurityAlert).where(*filters).order_by(
        SecurityAlert.last_detected_at.desc(), SecurityAlert.id).offset((page-1)*page_size).limit(page_size))
    return {'page': page, 'page_size': page_size, 'total': total, 'alerts': [alert_view(row) for row in rows]}


@router.get('/alerts/{alert_id}')
def detail(alert_id: UUID, role=Depends(principal), db: Session = Depends(session)):
    row = db.get(SecurityAlert, alert_id)
    if row is None:
        raise HTTPException(404, 'Alert not found')
    evidence = db.scalars(select(AlertEvidence).where(AlertEvidence.alert_id == alert_id)
                          .order_by(AlertEvidence.id).limit(100))
    # Never expose arbitrary legacy JSON, raw routes, request data or headers.
    return alert_view(row) | {'evidence': [{'id': item.id, 'event_id': item.event_id,
        'request_count': item.details.get('request_count') if
        isinstance(item.details.get('request_count'), int) else None} for item in evidence]}


@router.patch('/alerts/{alert_id}')
def update_alert(alert_id: UUID, patch: AlertPatch, role=Depends(principal), db: Session = Depends(session)):
    require(role, {'analyst', 'admin'})
    row = db.scalar(select(SecurityAlert).where(SecurityAlert.id == alert_id).with_for_update())
    if row is None:
        raise HTTPException(404, 'Alert not found')
    if patch.status != row.status:
        if patch.status not in TRANSITIONS[row.status]:
            raise HTTPException(409, 'Unsupported status transition')
        audit(db, role, 'alert.status', 'security_alert', row.id, {'from': row.status, 'to': patch.status})
        row.status = patch.status
        db.commit()
    return alert_view(row)


@router.get('/rules')
def rules(page: int = Query(1, ge=1, le=10000), page_size: int = Query(50, ge=1, le=100),
          role=Depends(principal), db: Session = Depends(session)):
    rows = db.scalars(select(DetectionRule).order_by(DetectionRule.name).offset((page-1)*page_size).limit(page_size))
    return {'page': page, 'page_size': page_size,
            'total': db.scalar(select(func.count()).select_from(DetectionRule)), 'rules': [rule_view(row) for row in rows]}


@router.patch('/rules/{rule_id}')
def update_rule(rule_id: UUID, patch: RulePatch, role=Depends(principal), db: Session = Depends(session)):
    require(role, {'admin'})
    row = db.scalar(select(DetectionRule).where(DetectionRule.id == rule_id).with_for_update())
    if row is None:
        raise HTTPException(404, 'Rule not found')
    try:
        old = configuration(row.rule_type, row.configuration)
        updated = configuration(row.rule_type, patch.configuration if patch.configuration is not None else row.configuration)
    except ValueError:
        raise HTTPException(422, 'Invalid rule configuration') from None
    if patch.enabled is True and row.rule_type != 'error_rate':
        raise HTTPException(409, 'Required trusted telemetry adapter unavailable')
    updated.version = old.version+1
    row.configuration = updated.model_dump()
    if patch.enabled is not None:
        row.enabled = patch.enabled
    audit(db, role, 'rule.update', 'detection_rule', row.id,
          {'before': old.model_dump(), 'after': updated.model_dump(), 'enabled': row.enabled})
    db.commit()
    return rule_view(row)


@router.get('/summary')
def summary(start: datetime | None = None, end: datetime | None = None, severity: Severity | None = None,
            status: Status | None = None, api_id: UUID | None = None, rule_id: UUID | None = None,
            role=Depends(principal), db: Session = Depends(session)):
    rows = db.execute(select(SecurityAlert.status, SecurityAlert.severity, func.count()).where(
        *clauses(start, end, severity, status, api_id, rule_id)).group_by(SecurityAlert.status, SecurityAlert.severity))
    return {'groups': [{'status': state, 'severity': level, 'count': count} for state, level, count in rows]}
