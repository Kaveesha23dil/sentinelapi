# Synthetic feature checks; no live data.
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import pytest
from sentinelapi.ml.features import Event, FEATURES, SCHEMA, aggregate
START = datetime(2026,1,1,tzinfo=timezone.utc)

def events(count=5, **changes):
    return [replace(Event(str(i),'fixture', START+timedelta(seconds=i),200,'GET','/safe'),**changes)
            for i in range(count)]


def windows(rows, **changes):
    return aggregate(rows,**(dict(coverage_start=START,complete_through=START+timedelta(minutes=1))|changes))


def test_boundaries_duplicates_order_utc():
    rows=events()+events(5,timestamp=START+timedelta(minutes=1))
    # Same IDs with different timestamps are conflicting, never silently dropped.
    with pytest.raises(ValueError): windows(rows)
    first=events()
    result=windows(list(reversed(first))+first+[replace(first[0],event_id='edge',timestamp=START+timedelta(minutes=1))])
    assert len(result)==1 and result[0].summary['request_count']==5
    assert result[0].summary==dict(zip(FEATURES,(5,0,0,1,1,0,1)))
    offset=timezone(timedelta(hours=5,minutes=30))
    assert windows([replace(e,timestamp=e.timestamp.astimezone(offset)) for e in first])==result


@pytest.mark.parametrize('field,value',[('status',None),('method',None),('endpoint',None),('status',700),('method','BAD')])
def test_missing_fields(field,value):
    w=windows(events(**{field:value}))[0]
    assert not w.eligible and w.reason=='missing-fields'


def test_low_volume_partial_and_unsupported_latency():
    assert not windows(events(4))[0].eligible
    assert windows(events(),complete_through=START+timedelta(seconds=59))==[]
    assert windows(events(),coverage_start=START+timedelta(seconds=1))==[]
    assert 'avg_latency_ms' not in FEATURES and len(FEATURES)==7 and SCHEMA=='api-60s-v1'
    with pytest.raises(ValueError): windows(events(timestamp=datetime(2026,1,1)))
