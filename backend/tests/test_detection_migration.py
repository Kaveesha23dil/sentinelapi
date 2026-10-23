"""DDL generation checks only; actual PostgreSQL application remains required."""
from importlib.util import module_from_spec, spec_from_file_location
from io import StringIO
from pathlib import Path

from alembic.migration import MigrationContext
from alembic.operations import Operations

from sentinelapi.db.models import Base


def test_additive_migration_ddl_matches_metadata():
    path = Path(__file__).parents[1]/'migrations/versions/a6d1023f0001_detection_engine.py'
    spec = spec_from_file_location('detection_migration', path)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    output = StringIO()
    context = MigrationContext.configure(dialect_name='postgresql', opts={
        'as_sql': True, 'output_buffer': output, 'target_metadata': Base.metadata})
    with Operations.context(context):
        module.upgrade()
    sql = output.getvalue()
    assert 'DROP ' not in sql and 'DELETE ' not in sql and 'UPDATE ' not in sql
    assert 'CREATE TABLE detection_checkpoints' in sql
    for name in ['incident_fingerprint', 'rule_version', 'window_start', 'window_end', 'measured_value', 'threshold']:
        assert f'ADD COLUMN {name}' in sql
    assert 'ck_security_alerts_window_order' in sql
    assert 'ck_security_alerts_rule_version_positive' in sql
    assert 'uq_security_alerts_incident_fingerprint' in sql
