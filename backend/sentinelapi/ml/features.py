"""Versioned, identity-free features from sanitized completed gateway events."""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from collections import defaultdict

SCHEMA = 'api-60s-v1'
FEATURES = ('request_count', 'error_4xx_ratio', 'error_5xx_ratio',
            'unique_endpoints', 'get_ratio', 'post_ratio', 'status_code_diversity')
MIN_REQUESTS = 5
LATENESS_SECONDS = 120


def utc(value):
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError('Aware timestamp required')
    return value.astimezone(timezone.utc)


def floor_minute(value):
    return utc(value).replace(second=0, microsecond=0)


@dataclass(frozen=True)
class Event:
    event_id: str
    api_id: str
    timestamp: datetime
    status: int | None
    method: str | None
    endpoint: str | None


@dataclass(frozen=True)
class Window:
    api_id: str
    start: datetime
    end: datetime
    values: tuple
    event_ids: tuple
    eligible: bool
    reason: str | None

    @property
    def identifier(self):
        return sha256(f'{SCHEMA}|{self.api_id}|{self.start.isoformat()}'.encode()).hexdigest()

    @property
    def summary(self):
        return dict(zip(FEATURES, self.values, strict=True))


def aggregate(events, *, complete_through, coverage_start):
    """Return nonempty [start,end) UTC windows; exclude partial coverage edges.

    Caller supplies a finalized event-time watermark (now minus lateness for live
    use). Conflicting UUID duplicates fail closed. Missing categorical fields make
    the entire window ineligible, avoiding fabricated zeroes/imputation bias.
    Latency and client identity are intentionally outside schema v1.
    """
    complete_through, coverage_start = utc(complete_through), utc(coverage_start)
    unique, groups = {}, defaultdict(list)
    for event in events:
        utc(event.timestamp)
        if event.event_id in unique and unique[event.event_id] != event:
            raise ValueError('Conflicting duplicate event')
        unique[event.event_id] = event
    for event in unique.values():
        start = floor_minute(event.timestamp)
        if start >= coverage_start and start + timedelta(seconds=60) <= complete_through:
            groups[(event.api_id, start)].append(event)
    result = []
    for (api, start), rows in sorted(groups.items()):
        rows.sort(key=lambda e: e.event_id)
        n = len(rows)
        missing = any(e.status is None or not 100 <= e.status <= 599 or
                      e.method not in {'GET','POST','PUT','PATCH','DELETE','HEAD','OPTIONS','TRACE','CONNECT'}
                      or not e.endpoint for e in rows)
        reason = 'missing-fields' if missing else 'low-volume' if n < MIN_REQUESTS else None
        values = (n, sum(400 <= (e.status or 0) < 500 for e in rows)/n,
                  sum(500 <= (e.status or 0) < 600 for e in rows)/n,
                  len({e.endpoint for e in rows if e.endpoint}),
                  sum(e.method == 'GET' for e in rows)/n,
                  sum(e.method == 'POST' for e in rows)/n,
                  len({e.status for e in rows if e.status is not None}))
        result.append(Window(api, start, start+timedelta(seconds=60), values,
                             tuple(e.event_id for e in rows), reason is None, reason))
    return result
