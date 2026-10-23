"""Read-only historical export and explicitly synthetic controlled scenarios."""
from collections import Counter
from datetime import datetime, timedelta, timezone
import numpy as np
from sqlalchemy import select
from .features import Event, aggregate
from .features import utc


def historical(db, start, end, api_id=None, limit=100000):
    from sentinelapi.db.models import TrafficEvent
    start,end=utc(start),utc(end)
    if start>=end:
        raise ValueError('Start must precede end')
    query = select(TrafficEvent).where(TrafficEvent.source == 'wso2-gateway',
        TrafficEvent.timestamp >= start, TrafficEvent.timestamp < end)
    if api_id:
        query = query.where(TrafficEvent.api_service_id == api_id)
    rows = db.scalars(query.order_by(TrafficEvent.timestamp, TrafficEvent.event_id).limit(limit+1)).all()
    if len(rows) > limit:
        raise ValueError('Historical capacity exceeded; narrow UTC interval')
    windows = aggregate([Event(str(r.event_id), str(r.api_service_id), r.timestamp,
        r.status_code, r.http_method, r.endpoint) for r in rows],
        coverage_start=start, complete_through=end)
    # No raw endpoints, client identities or event payloads leave this adapter.
    profile = dict(provenance='wso2-gateway', events=len(rows),
        source_filter_is_not_cryptographic_provenance=True,
        start=start.isoformat(), end=end.isoformat(), windows=len(windows),
        eligible_windows=sum(w.eligible for w in windows),
        observed_start=min((r.timestamp for r in rows), default=None).isoformat() if rows else None,
        observed_end=max((r.timestamp for r in rows), default=None).isoformat() if rows else None,
        api_count=len({r.api_service_id for r in rows}),
        latency_present=sum(r.latency_ms is not None for r in rows),
        client_present=sum(r.client_identifier is not None for r in rows),
        status_distribution=dict(Counter(str(r.status_code) for r in rows)))
    return windows, profile


def synthetic(seed=42, minutes=540, include_events=False):
    """Controlled simulation, not a sample of production or evidence of attacks.

    Train period is normal by generator design. Held-out period includes normal
    variation, benign bursts, moderate/severe error and volume scenarios. Labels
    describe injected scenarios, not inferred intent. Labels never enter features.
    """
    rng = np.random.default_rng(seed)
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    events, labels, scenarios = [], [], []
    for minute in range(minutes):
        scenario = 'normal'
        if minute >= 360:
            scenario = ('normal', 'benign-burst', 'error-moderate', 'error-severe',
                        'volume-moderate', 'volume-severe')[((minute-360)//5) % 6]
        n = int(rng.integers(18, 55))
        if scenario in {'benign-burst', 'volume-moderate'}:
            n = int(rng.integers(55, 95))
        if scenario == 'volume-severe':
            n = int(rng.integers(120, 220))
        error = {'error-moderate': .22, 'error-severe': .8}.get(scenario, .03)
        for j in range(n):
            status = int(rng.choice([200, 404, 500], p=[1-error, error*.6, error*.4]))
            events.append(Event(f'synthetic-{minute}-{j}', 'synthetic-demo-api',
                start+timedelta(minutes=minute, seconds=float(rng.uniform(0, 60))), status,
                str(rng.choice(['GET', 'POST'], p=[.8, .2])),
                '/synthetic/'+str(rng.integers(0, 4))))
        labels.append(int(scenario.startswith(('error-', 'volume-'))))
        scenarios.append(scenario)
    windows = aggregate(events, coverage_start=start, complete_through=start+timedelta(minutes=minutes))
    result = (windows, np.asarray(labels), scenarios)
    return (*result, events) if include_events else result


def chronological_split(windows, split_at):
    ordered = sorted(windows, key=lambda w: (w.start, w.api_id))
    train = [w for w in ordered if w.end <= split_at and w.eligible]
    evaluation = [w for w in ordered if w.start >= split_at and w.eligible]
    if not train or not evaluation or max(w.end for w in train) > min(w.start for w in evaluation):
        raise ValueError('Insufficient chronological coverage')
    return train, evaluation
