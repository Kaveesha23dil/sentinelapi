"""Offline synthetic fixtures only; these tests do not prove WSO2 ingestion."""
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from sentinelapi.detection.rules import (DEFAULTS, Baseline, Observation, configuration,
                                         evaluate, fingerprint)

NOW = datetime(2026, 10, 23, 12, tzinfo=timezone.utc)
API = uuid4()


def rows(count, **changes):
    return [Observation(uuid4(), API, NOW-timedelta(seconds=1), 200,
                        'fixture-client', True, **changes) for _ in range(count)]


def check(kind, events, **kwargs):
    return evaluate(kind, configuration(kind, DEFAULTS[kind]), events, NOW, **kwargs)


@pytest.mark.parametrize('count, expected', [(0, False), (100, False), (101, True)])
def test_flood_threshold(count, expected):
    assert bool(check('request_flood', rows(count))) == expected


@pytest.mark.parametrize('total, errors, expected', [(19, 19, False), (20, 10, False), (20, 11, True), (20, 0, False)])
def test_error_rate(total, errors, expected):
    events = rows(total)
    events = [replace(row, status=500 if index < errors else 200) for index, row in enumerate(events)]
    assert bool(check('error_rate', events)) == expected


def test_half_open_window_and_timezone():
    events = rows(100)
    outside = replace(rows(1)[0], timestamp=NOW-timedelta(seconds=60))
    assert not check('request_flood', events+[outside])
    inside = replace(outside, timestamp=NOW-timedelta(seconds=60)+timedelta(microseconds=1))
    assert check('request_flood', events+[inside])
    assert check('request_flood', events+[replace(inside, timestamp=NOW)])
    assert not check('request_flood', events+[replace(inside, timestamp=NOW+timedelta(microseconds=1))])
    with pytest.raises(ValueError):
        replace(inside, timestamp=NOW.replace(tzinfo=None))


def test_verified_client_and_api_grouping():
    events = rows(60)+[replace(row, client='other') for row in rows(60)]
    assert not check('request_flood', events)
    assert not check('request_flood', rows(60)+[replace(row, api_id=uuid4()) for row in rows(60)])
    for changes in [{'client': None}, {'client_verified': False}]:
        assert not check('request_flood', [replace(row, **changes) for row in rows(101)])
    # API-level ratio remains usable without client identity.
    assert check('error_rate', [replace(row, status=404, client=None) for row in rows(20)])


def test_enumeration_requires_explicit_route_evidence():
    events = [replace(row, status=404) for row in rows(15)]
    assert not check('enumeration', events)
    assert not check('enumeration', [replace(row, unknown_route='/same') for row in events])
    assert check('enumeration', [replace(row, unknown_route=f'/fixture/{index}') for index, row in enumerate(events)])


def test_auth_requires_confirmed_failure():
    events = [replace(row, status=401) for row in rows(10)]
    assert not check('auth_failures', events)
    assert not check('auth_failures', [replace(row, confirmed_auth_failure=True) for row in events[:9]])
    assert check('auth_failures', [replace(row, confirmed_auth_failure=True) for row in events])


@pytest.mark.parametrize('average, windows, end, expected', [
    (10, 11, NOW-timedelta(hours=1), False), (0, 12, NOW-timedelta(hours=1), False),
    (10, 12, NOW, False), (10, 12, NOW-timedelta(hours=1), True),
    (11, 12, NOW-timedelta(hours=1), False)])
def test_baseline_readiness(average, windows, end, expected):
    baseline = {(API, 'fixture-client'): Baseline(average, windows, end)}
    assert bool(check('unusual_activity', rows(31), baselines=baseline)) == expected


def test_late_out_of_order_and_duplicates():
    events = rows(101)
    assert check('request_flood', events) == check('request_flood', list(reversed(events))+events)
    assert not check('unusual_activity', events)
    with pytest.raises(ValueError, match='Conflicting'):
        check('request_flood', events+[replace(events[0], status=500)])


def test_fingerprint_stable_and_versioned():
    finding = check('request_flood', rows(101))[0]
    rule_id = uuid4()
    value = fingerprint(rule_id, 1, finding, 60)
    assert value == fingerprint(rule_id, 1, replace(finding, measured=200), 60)
    assert value != fingerprint(rule_id, 2, finding, 60)
    assert value != fingerprint(rule_id, 1, replace(finding, target='other'), 60)
    assert value != fingerprint(rule_id, 1, replace(finding, end=NOW+timedelta(seconds=60)), 60)


@pytest.mark.parametrize('changes', [{'window_seconds': 0}, {'window_seconds': 301}, {'threshold': float('nan')},
    {'minimum_requests': 0}, {'extra': 'unsafe'}, {'version': 0}, {'threshold': 1.1}])
def test_configuration_validation(changes):
    with pytest.raises(ValueError):
        configuration('error_rate', DEFAULTS['error_rate'] | changes)


def test_evidence_bounded_and_deterministic():
    finding = check('request_flood', rows(200))[0]
    assert len(finding.event_ids) == 100 and finding.count == 200
    assert 'observed' in finding.explanation
