"""Disposable database migration/test runner and restart verification; no secret output."""
import argparse
import json
import os
import subprocess
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from alembic import command
from alembic.config import Config
from psycopg import sql
from sqlalchemy import inspect, select, text

from .config import Settings
from .models import TrafficEvent
from .repository import Repository
from .schemas import EventInput, ServiceInput
from .session import make_engine, transaction


def require_test_database(name):
    if not name.startswith('sentinelapi_test_') or not name.removeprefix('sentinelapi_test_').isalnum():
        raise ValueError('Only disposable sentinelapi_test_* databases are allowed')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['prepare', 'restart-check'])
    parser.add_argument('--report', type=Path, default=Path('/evidence/database-verification.json'))
    args = parser.parse_args()
    if args.action == 'restart-check':
        report = json.loads(args.report.read_text())
        if report.get('pytest_exit_code') != 0 or not report.get('migration_downgrade_upgrade'):
            raise ValueError('Prepare must pass before restart verification')
        require_test_database(report['test_database'])
        os.environ['POSTGRES_DB'] = report['test_database']
        engine = make_engine()
        try:
            with engine.connect() as connection:
                marker = connection.execute(select(TrafficEvent.event_id, TrafficEvent.source).where(
                    TrafficEvent.event_id == report['marker_event_id'])).one()
                assert marker.source == 'demo-test'
            report['survived_container_restart'] = True
            report['passed'] = True
            report['phase'] = 'complete'
            report['restart_checked_at_utc'] = datetime.now(timezone.utc).isoformat()
            args.report.write_text(json.dumps(report, indent=2) + '\n')
            print('PASS: fabricated event survived a new application process and PostgreSQL restart.')
        finally:
            engine.dispose()
        return 0

    settings = Settings.from_environment()
    name = 'sentinelapi_test_' + uuid4().hex
    require_test_database(name)
    args.report.write_text(json.dumps({'checked_at_utc': datetime.now(timezone.utc).isoformat(),
                                      'test_database': name, 'passed': False,
                                      'phase': 'preparing'}) + '\n')
    engine = make_engine(settings)
    try:
        with engine.connect().execution_options(isolation_level='AUTOCOMMIT') as connection:
            # psycopg Identifier quotes an internal generated identifier; never user SQL.
            raw = connection.connection.driver_connection
            raw.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(name)))
    finally:
        engine.dispose()
    os.environ['POSTGRES_DB'] = name
    config = Config('alembic.ini')
    command.upgrade(config, 'head')
    command.upgrade(config, 'head')
    command.check(config)
    # Destructive migration test is restricted to the database just created above.
    command.downgrade(config, 'base')
    engine = make_engine()
    try:
        assert set(inspect(engine).get_table_names()) <= {'alembic_version'}
    finally:
        engine.dispose()
    command.upgrade(config, 'head')
    test_paths = ['tests', 'collector/tests'] if Path('collector/tests').exists() else ['tests']
    result = subprocess.run(['python', '-m', 'pytest', '-q', '-p', 'no:cacheprovider',
                             '--junitxml=/tmp/sentinelapi-db-tests.xml', *test_paths], check=False)
    if result.returncode:
        args.report.write_text(json.dumps({'test_database': name, 'passed': False,
                                          'pytest_exit_code': result.returncode}) + '\n')
        print('FAIL: test database retained for investigation; no production database was downgraded.')
        return result.returncode
    engine = make_engine()
    marker = uuid4()
    try:
        with transaction(engine) as session:
            repo = Repository(session)
            api = repo.create_service(ServiceInput(name='demo-restart-marker', version='test-1', context='/demo-test'))
            repo.add_event(EventInput(api_service_id=api.id, event_id=marker, timestamp=datetime.now(timezone.utc),
                client_identifier='demo:restart-test', http_method='GET', endpoint='/demo-test',
                status_code=200, latency_ms='1.000', source='demo-test'))
        suite = ET.parse('/tmp/sentinelapi-db-tests.xml').getroot().find('testsuite')
        report = {'checked_at_utc': datetime.now(timezone.utc).isoformat(), 'test_database': name,
                  'passed': False, 'phase': 'awaiting-restart',
                  'pytest_summary': {key: suite.attrib[key] for key in ['tests', 'errors', 'failures', 'skipped', 'time']},
                  'marker_event_id': str(marker), 'fabricated_test_data': True,
                  'migration_upgrade_twice': True, 'migration_downgrade_upgrade': True,
                  'pytest_exit_code': result.returncode, 'survived_container_restart': False,
                  'tables': inspect(engine).get_table_names(),
                  'indexes': {table: [index['name'] for index in inspect(engine).get_indexes(table)]
                              for table in inspect(engine).get_table_names()}}
        args.report.write_text(json.dumps(report, indent=2) + '\n')
        print('PASS: migration cycle and tests; fabricated restart marker committed. Test database retained.')
    finally:
        engine.dispose()
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f'FAIL: database verification stopped ({type(error).__name__}); secrets and SQL details withheld.')
        raise SystemExit(1)
