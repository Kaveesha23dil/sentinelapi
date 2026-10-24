"""Offline startup/lifecycle and authenticated probe regressions; not live proof."""
import asyncio
import io
import json
from unittest.mock import Mock
from urllib.error import HTTPError, URLError

import pytest

from sentinelapi.detection import provision, worker
from sentinelapi.monitoring import healthcheck


class Response(io.BytesIO):
    def __init__(self, status, body):
        super().__init__(json.dumps(body).encode())
        self.status = status


@pytest.mark.parametrize('status,body,expected', [
    (200, {'database': 'available', 'collector': 'healthy'}, 'healthy'),
    (503, {'database': 'available', 'collector': 'stale-or-unavailable'}, 'collector-stale'),
    (503, {'detail': 'private server diagnostic'}, 'database-or-service-unavailable'),
    (401, {'detail': 'private server diagnostic'}, 'authentication-rejected'),
    (403, {}, 'authentication-rejected'),
    (404, {}, 'http-error'),
    (200, {}, 'database-or-service-unavailable'),
    (200, [], 'unexpected-response'),
])
def test_authenticated_health_probe(monkeypatch, capsys, status, body, expected):
    token = 'synthetic-healthcheck-token-' + 'x' * 40
    monkeypatch.setenv('MONITORING_API_TOKEN', token)

    def open_request(request, timeout):
        assert request.full_url == 'http://127.0.0.1:8001/api/v1/monitoring/health'
        assert request.get_header('Authorization') == 'Bearer ' + token
        assert timeout == 5
        if status >= 400:
            raise HTTPError(request.full_url, status, 'private reason', {}, Response(status, body))
        return Response(status, body)

    monkeypatch.setattr(healthcheck, 'urlopen', open_request)
    assert healthcheck.main() == (0 if expected == 'healthy' else 1)
    output = capsys.readouterr().out
    assert output.strip() == 'monitoring_health state=' + expected
    assert token not in output and 'private' not in output


def test_missing_health_token_does_not_send_request(monkeypatch):
    monkeypatch.delenv('MONITORING_API_TOKEN', raising=False)
    opener = Mock()
    monkeypatch.setattr(healthcheck, 'urlopen', opener)
    assert healthcheck.check_health() == 'authentication-not-configured'
    opener.assert_not_called()


def test_health_connection_failure_is_redacted(monkeypatch):
    monkeypatch.setenv('MONITORING_API_TOKEN', 'synthetic-' + 'x' * 40)
    monkeypatch.setattr(healthcheck, 'urlopen', Mock(side_effect=URLError('private error')))
    assert healthcheck.check_health() == 'connection-failed'


def test_health_invalid_json_is_not_healthy(monkeypatch):
    monkeypatch.setenv('MONITORING_API_TOKEN', 'synthetic-' + 'x' * 40)
    response = io.BytesIO(b'private invalid response')
    response.status = 200
    monkeypatch.setattr(healthcheck, 'urlopen', lambda *_args, **_kwargs: response)
    assert healthcheck.check_health() == 'unexpected-response'


def raw_connection(existing):
    raw = Mock()
    raw.execute.return_value.fetchone.return_value = existing
    return raw


def test_existing_role_passwords_are_not_rotated():
    raw = raw_connection((False, False, False, False, False, True))
    provision.provision(raw, {}, 'sentinelapi_test_runtime')
    statements = [str(call.args[0]) for call in raw.execute.call_args_list]
    assert not any('ALTER ROLE' in statement or 'CREATE ROLE' in statement for statement in statements)
    assert any('GRANT CONNECT' in statement for statement in statements)
    assert not any(' TO PUBLIC' in statement for statement in statements)


def test_new_roles_require_strong_secrets_before_any_mutation():
    raw = raw_connection(None)
    with pytest.raises(ValueError, match='strong private'):
        provision.provision(raw, {}, 'sentinelapi_test_runtime')
    assert len(raw.execute.call_args_list) == 1  # role lookup only


def test_explicit_rotation_and_new_role_creation():
    passwords = {role: 'synthetic-' + 'x' * 40 for role in provision.ROLES}
    for existing, operation in [(None, 'CREATE ROLE'),
                                ((False, False, False, False, False, True), 'ALTER ROLE')]:
        raw = raw_connection(existing)
        provision.provision(raw, passwords, 'sentinelapi_test_runtime', rotate_existing=True)
        statements = [str(call.args[0]) for call in raw.execute.call_args_list]
        assert sum(operation in statement for statement in statements) == 2


def test_privileged_role_is_refused_without_mutation():
    raw = raw_connection((True, False, False, False, False, True))
    with pytest.raises(ValueError, match='privileged'):
        provision.provision(raw, {}, 'sentinelapi_test_runtime')
    assert len(raw.execute.call_args_list) == 1


@pytest.mark.parametrize('fail_rule', [False, True])
def test_worker_finishes_cycle_and_disposes_on_stop(monkeypatch, caplog, fail_rule):
    from sentinelapi.ml import worker as ml_worker
    engine = Mock()
    monkeypatch.setattr(worker, 'make_engine', lambda: engine)

    async def scenario():
        stopping = asyncio.Event()

        def rules(actual_engine):
            assert actual_engine is engine
            if fail_rule:
                raise RuntimeError('synthetic failure')
            return {'state': 'processed', 'created': 0}

        def ml(actual_engine):
            assert actual_engine is engine
            stopping.set()
            return {'state': 'unconfigured', 'processed': 0}

        monkeypatch.setattr(worker, 'run_once', rules)
        monkeypatch.setattr(ml_worker, 'run_once', ml)
        await asyncio.wait_for(worker.serve(stopping), timeout=2)

    asyncio.run(scenario())
    engine.dispose.assert_called_once()
    assert 'synthetic failure' not in caplog.text
