"""Pure sliding-window strategies. Optional evidence is trusted adapter input only."""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from math import isfinite
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

Kind = Literal['request_flood', 'error_rate', 'enumeration', 'auth_failures', 'unusual_activity']
DEFAULTS = {
    'request_flood': dict(window_seconds=60, threshold=100),
    'error_rate': dict(window_seconds=300, threshold=0.5, minimum_requests=20),
    'enumeration': dict(window_seconds=120, threshold=15),
    'auth_failures': dict(window_seconds=120, threshold=10),
    'unusual_activity': dict(window_seconds=300, threshold=3),
}


class RuleConfig(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    version: int = Field(default=1, ge=1)
    window_seconds: int = Field(ge=1, le=300)
    threshold: float = Field(gt=0, le=100000, allow_inf_nan=False)
    minimum_requests: int = Field(default=1, ge=1, le=100000)
    baseline_windows: int = Field(default=12, ge=12, le=288)


def configuration(kind: Kind, value: dict) -> RuleConfig:
    if kind not in DEFAULTS:
        raise ValueError('Unsupported rule type')
    result = RuleConfig.model_validate(value)
    if kind == 'error_rate' and result.threshold > 1:
        raise ValueError('Error ratio must be at most one')
    return result


@dataclass(frozen=True)
class Observation:
    event_id: UUID
    api_id: UUID
    timestamp: datetime
    status: int
    client: str | None = None
    client_verified: bool = False
    unknown_route: str | None = None
    confirmed_auth_failure: bool = False

    def __post_init__(self):
        if self.timestamp.tzinfo is None or self.timestamp.utcoffset() is None:
            raise ValueError('Aware event timestamp required')
        if not 100 <= self.status <= 599:
            raise ValueError('Invalid HTTP status')


@dataclass(frozen=True)
class Baseline:
    average: float
    complete_windows: int
    end: datetime

    def __post_init__(self):
        if self.end.tzinfo is None or not isfinite(self.average) or self.average < 0 or self.complete_windows < 0:
            raise ValueError('Invalid baseline')


@dataclass(frozen=True)
class Finding:
    api_id: UUID
    target: str
    start: datetime
    end: datetime
    measured: float
    threshold: float
    count: int
    event_ids: tuple[UUID, ...]
    explanation: str


def evaluate(kind: Kind, config: RuleConfig, events: list[Observation], end: datetime,
             baselines: dict | None = None) -> list[Finding]:
    """Evaluate (end-window, end], deduplicating event UUIDs before grouping.

    Error ratio groups by API because BASIC provides no verified client. Other
    rules require adapter-verified identity; arbitrary 401/404 are insufficient.
    """
    if end.tzinfo is None or end.utcoffset() is None:
        raise ValueError('Aware window required')
    if kind not in DEFAULTS:
        raise ValueError('Unsupported rule type')
    end = end.astimezone(timezone.utc)
    start = end - timedelta(seconds=config.window_seconds)
    unique = {}
    for event in events:
        previous = unique.get(event.event_id)
        if previous is not None and previous != event:
            raise ValueError('Conflicting duplicate event')
        unique[event.event_id] = event
    groups = {}
    for event in unique.values():
        if not start < event.timestamp <= end:
            continue
        if kind != 'error_rate' and (not event.client or not event.client_verified):
            continue
        target = 'api' if kind == 'error_rate' else event.client
        groups.setdefault((event.api_id, target), []).append(event)
    findings = []
    for (api_id, target), rows in sorted(groups.items(), key=lambda item: str(item[0])):
        threshold = config.threshold
        evidence = rows
        if kind == 'request_flood':
            measured = len(rows)
            triggered = measured > threshold
        elif kind == 'error_rate':
            evidence = [row for row in rows if row.status >= 400]
            measured = len(evidence) / len(rows)
            triggered = len(rows) >= config.minimum_requests and measured > threshold
        elif kind == 'enumeration':
            evidence = [row for row in rows if row.unknown_route is not None]
            measured = len({row.unknown_route for row in evidence})
            triggered = measured >= threshold
        elif kind == 'auth_failures':
            evidence = [row for row in rows if row.confirmed_auth_failure]
            measured = len(evidence)
            triggered = measured >= threshold
        elif kind == 'unusual_activity':
            baseline = (baselines or {}).get((api_id, target))
            if (baseline is None or baseline.complete_windows < config.baseline_windows
                    or baseline.average <= 0 or baseline.end > start):
                continue
            measured = len(rows) / baseline.average
            triggered = measured > threshold
        else:
            raise ValueError('Unsupported rule type')
        if triggered:
            findings.append(Finding(api_id, target, start, end, measured, threshold, len(rows),
                tuple(row.event_id for row in sorted(evidence, key=lambda row: str(row.event_id))[:100]),
                f'{kind}: observed {measured:.6g}; threshold {threshold:g}; '
                f'{len(rows)} observed requests in {config.window_seconds}s. This is a signal, not attribution.'))
    return findings


def fingerprint(rule_id, version: int, finding: Finding, seconds: int) -> str:
    """One incident per rule/version/API/target/UTC epoch bucket.

    Neighboring buckets can produce distinct alerts for a sustained incident.
    """
    bucket = int(finding.end.timestamp()) // seconds
    return sha256(f'{rule_id}|{version}|{finding.api_id}|{finding.target}|{bucket}'.encode()).hexdigest()
