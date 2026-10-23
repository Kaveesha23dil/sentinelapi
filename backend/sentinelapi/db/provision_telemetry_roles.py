"""Provision only dedicated local telemetry roles; never echo credential SQL."""
import os
from psycopg import sql
from .session import make_engine


def main():
    engine = make_engine()
    try:
        with engine.begin() as connection:
            raw = connection.connection.driver_connection
            database = engine.url.database
            for name, variable, tables in [
                ('sentinelapi_collector', 'COLLECTOR_DB_PASSWORD', ['api_services', 'traffic_events']),
                ('sentinelapi_monitor', 'MONITORING_DB_PASSWORD', ['api_services', 'traffic_events']),
            ]:
                secret = os.environ[variable]
                if len(secret) < 32 or secret.startswith('REPLACE_WITH_'):
                    raise ValueError('Configure a strong runtime database secret')
                existing = raw.execute('SELECT rolsuper, rolcreatedb, rolcreaterole FROM pg_roles WHERE rolname=%s', (name,)).fetchone()
                if existing and any(existing):
                    raise ValueError('Refusing to modify an existing privileged role')
                if existing:
                    raw.execute(sql.SQL('ALTER ROLE {} PASSWORD {}').format(sql.Identifier(name), sql.Literal(secret)))
                else:
                    raw.execute(sql.SQL('CREATE ROLE {} LOGIN PASSWORD {}').format(sql.Identifier(name), sql.Literal(secret)))
                raw.execute(sql.SQL('GRANT CONNECT ON DATABASE {} TO {}').format(sql.Identifier(database), sql.Identifier(name)))
                raw.execute(sql.SQL('GRANT USAGE ON SCHEMA public TO {}').format(sql.Identifier(name)))
                for table in tables:
                    privileges = sql.SQL('SELECT, INSERT') if name == 'sentinelapi_collector' else sql.SQL('SELECT')
                    raw.execute(sql.SQL('GRANT {} ON TABLE {} TO {}').format(privileges, sql.Identifier(table), sql.Identifier(name)))
                if name == 'sentinelapi_monitor':
                    raw.execute(sql.SQL('ALTER ROLE {} SET default_transaction_read_only = on').format(sql.Identifier(name)))
        print('Dedicated collector and read-only monitoring roles provisioned; secrets withheld.')
    finally:
        engine.dispose()


if __name__ == '__main__':
    try:
        main()
    except Exception:
        print('Role provisioning failed; details redacted. Verify owner access and runtime secrets.')
        raise SystemExit(1)
