import pytest
from pydantic import ValidationError

from sentinelapi.db.config import Settings


def test_cloud_tls_configuration(monkeypatch):
    monkeypatch.setenv('POSTGRES_PASSWORD', 'synthetic-test-only')
    monkeypatch.setenv('POSTGRES_SSLMODE', 'verify-full')
    monkeypatch.setenv('POSTGRES_SSLROOTCERT', '/certificates/postgres-ca.pem')
    settings = Settings.from_environment()
    assert settings.url().query == {
        'sslmode': 'verify-full', 'sslrootcert': '/certificates/postgres-ca.pem'}


def test_local_database_defaults_preserved():
    assert not Settings(database='test', username='test', password='synthetic').url().query


def test_invalid_tls_mode_rejected():
    with pytest.raises(ValidationError):
        Settings(database='test', username='test', password='synthetic', sslmode='invalid')
