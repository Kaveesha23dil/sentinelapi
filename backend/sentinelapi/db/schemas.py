"""Explicit safe DTOs. Reject unknown fields rather than silently retaining bodies."""
from datetime import datetime, timezone
from decimal import Decimal
from typing import Annotated, Literal
from uuid import UUID

from pydantic import (AwareDatetime, BaseModel, ConfigDict, Field,
                      StringConstraints, field_validator, model_validator)

SafeLabel = Annotated[str, StringConstraints(pattern=r'^[A-Za-z0-9_.:-]{1,128}$')]
Pseudonym = Annotated[str, StringConstraints(pattern=r'^(demo:[a-z0-9_-]{1,64}|hmac:[a-f0-9]{64})$')]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)


class ServiceInput(StrictModel):
    name: SafeLabel
    version: Annotated[str, StringConstraints(pattern=r'^[A-Za-z0-9_.-]{1,64}$')]
    context: Annotated[str, StringConstraints(pattern=r'^/[A-Za-z0-9_/{}/.-]*$', max_length=256)]
    gateway_api_id: SafeLabel | None = None


class EventInput(StrictModel):
    api_service_id: UUID
    event_id: UUID
    timestamp: AwareDatetime
    client_identifier: Pseudonym | None = None
    http_method: Literal['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD', 'OPTIONS', 'TRACE', 'CONNECT']
    # A normalized route template, with no query string, fragment or request body.
    endpoint: Annotated[str, StringConstraints(pattern=r'^/[A-Za-z0-9_/{}/.-]*$', max_length=512)]
    status_code: int = Field(ge=100, le=599)
    latency_ms: Decimal | None = Field(default=None, ge=0, le=99999999999, max_digits=14, decimal_places=3, allow_inf_nan=False)
    source: Literal['demo-test', 'wso2-gateway']

    @field_validator('timestamp')
    @classmethod
    def utc(cls, value: datetime):
        return value.astimezone(timezone.utc)


class EvidenceDetails(StrictModel):
    demonstration: Literal[True]
    reason_code: Literal['demo-threshold', 'demo-example']
    observed_count: int = Field(ge=0)


class AlertInput(StrictModel):
    api_service_id: UUID
    rule_id: UUID | None = None
    severity: Literal['low', 'medium', 'high', 'critical']
    status: Literal['open', 'investigating', 'resolved', 'dismissed'] = 'open'
    risk_score: Decimal = Field(ge=0, le=100, max_digits=5, decimal_places=2, allow_inf_nan=False)
    # Initial foundation accepts controlled examples only. Real telemetry DTOs
    # and redaction policies must be designed before ingestion is enabled.
    title: Literal['Demonstration security alert'] = 'Demonstration security alert'
    description: Literal['Fabricated test data; not WSO2 telemetry.'] = 'Fabricated test data; not WSO2 telemetry.'
    first_detected_at: AwareDatetime
    last_detected_at: AwareDatetime

    @model_validator(mode='after')
    def ordered(self):
        if self.last_detected_at < self.first_detected_at:
            raise ValueError('Detection timestamps must be ordered')
        return self
