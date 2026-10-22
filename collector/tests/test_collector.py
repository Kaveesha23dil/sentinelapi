"""Synthetic unit fixtures model the inspected live format; never live evidence."""
import json
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy.exc import OperationalError

from traffic_collector.checkpoint import Checkpoints
from traffic_collector.config import Config
from traffic_collector.normalizer import normalize
from traffic_collector.parser import parse
from traffic_collector.reader import chunks
from traffic_collector.sanitizer import endpoint
from traffic_collector.transport import publish
from traffic_collector.writer import persist

CONFIG = Config('f0d23a14-460c-4441-9c76-0f39bfd2efb3', 'DemoCommerceAPI', '/democommerceapi', '1.0.0')


def line(flow='RESPONSE_OUT', **changes):
    data = {'flow': flow, 'verb': 'GET', 'apiTo': '/democommerceapi/1.0.0/api/v1/orders/123?token=synthetic',
            'correlationId': 'be73ac04-fae9-4f03-9534-9e1c55ee82d6', 'statusCode': 200} | changes
    return '[2026-10-22 09:55:28,629]  INFO {API_LOG} DemoCommerceAPI - ' + json.dumps(data)


def test_actual_format_sanitization_and_missing_measurements():
    flow = parse(line(sourceIP='192.0.2.1', headers=['Authorization=synthetic'], payload='synthetic'), CONFIG)
    event = normalize(flow, CONFIG, uuid4())
    assert event.endpoint == '/api/v1/orders/{order_id}'
    assert event.latency_ms is None and event.client_identifier is None
    assert 'synthetic' not in json.dumps(flow)
    assert '192.0.2.1' not in json.dumps(flow)


@pytest.mark.parametrize('raw', ['', '{broken', line()[:-2], 'x'*17000,
    line(statusCode=999), line(statusCode=True), line(statusCode=None), line(correlationId='bad'),
    line(verb='UNKNOWN'), line(flow='UNKNOWN'), line(apiTo='/unrelated/orders')])
def test_malformed_and_unknown_fields(raw):
    assert parse(raw, CONFIG) is None


def test_only_one_logical_completed_request():
    service = uuid4()
    flows = [parse(line(flow), CONFIG) for flow in ['REQUEST_IN', 'REQUEST_OUT', 'RESPONSE_IN', 'RESPONSE_OUT']]
    events = [event for flow in flows if (event := normalize(flow, CONFIG, service))]
    assert len(events) == 1
    assert normalize(flows[-1], CONFIG, service).event_id == events[0].event_id


def test_reused_correlation_at_different_completion_time_is_distinct():
    flow = parse(line(), CONFIG)
    service = uuid4()
    assert normalize(flow, CONFIG, service).event_id != normalize(flow | {'timestamp': '2026-10-22T10:00:00+00:00'}, CONFIG, service).event_id


def test_routes_do_not_keep_unknown_identifiers():
    assert endpoint('/democommerceapi/1.0.0/user/private-name?secret=synthetic', CONFIG.context, CONFIG.version) == '/{unmapped}'


def test_checkpoint_recovery_and_transport_gc(tmp_path):
    spool, state = tmp_path/'spool', tmp_path/'state'
    spool.mkdir()
    state.mkdir()
    publish({'flows': [parse(line(), CONFIG)]}, spool, state)
    checks = Checkpoints(state)
    filename, flows = next(chunks(spool, checks.completed))
    checks.commit(filename)
    assert list(chunks(spool, Checkpoints(state).completed)) == []
    publish({'flows': [parse(line(), CONFIG)]}, spool, state)
    assert not list(spool.glob('*.ndjson'))


def test_truncated_spool_line_does_not_crash_reader(tmp_path):
    (tmp_path/('a'*64+'.ndjson')).write_text('{broken\n' + json.dumps(parse(line(), CONFIG)) + '\n')
    assert len(next(chunks(tmp_path, []))[1]) == 1


def test_untrusted_extra_transport_data_rejected(tmp_path):
    with pytest.raises(ValueError, match='Unexpected'):
        publish({'flows': [parse(line(), CONFIG) | {'Authorization': 'synthetic'}]}, tmp_path, tmp_path)


def test_database_retry_is_bounded(monkeypatch):
    import traffic_collector.writer as writer
    calls = []
    def fail(*args, **kwargs):
        calls.append(1)
        raise OperationalError('safe-test', None, RuntimeError('unavailable'))
    monkeypatch.setattr(writer, 'Session', fail)
    delays = []
    with pytest.raises(RuntimeError, match='checkpoint retained'):
        persist(None, [], CONFIG, pause=delays.append)
    assert len(calls) == 4 and delays == [1, 2, 4]


def test_checkpoint_does_not_advance_on_write_failure(monkeypatch, tmp_path):
    import traffic_collector.main as main
    class Engine:
        def connect(self):
            return self
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def execute(self, *args):
            pass
    spool, state = tmp_path/'spool', tmp_path/'state'
    spool.mkdir()
    state.mkdir()
    config = Config(CONFIG.api_id, CONFIG.api_name, CONFIG.context, CONFIG.version, spool=spool, state=state)
    publish({'flows': [parse(line(), CONFIG)]}, spool, state)
    monkeypatch.setattr(main, 'persist', lambda *args: (_ for _ in ()).throw(RuntimeError('unavailable')))
    with pytest.raises(RuntimeError):
        main.cycle(Engine(), config, Checkpoints(state))
    assert Checkpoints(state).completed == []
