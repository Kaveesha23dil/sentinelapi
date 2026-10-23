"""Owner-run provisioning for NEW scoped detector/security roles; no grants to PUBLIC.

Never prints SQL, passwords or connection strings. Existing role passwords are
rotated only through an explicit invocation of this command.
"""
import os

from psycopg import sql
from sentinelapi.db.session import make_engine


def main():
    values = {}
    for role, variable in [('sentinelapi_detector', 'DETECTOR_DB_PASSWORD'),
                           ('sentinelapi_security', 'SECURITY_DB_PASSWORD')]:
        value = os.getenv(variable, '')
        if len(value) < 32 or value.startswith('REPLACE_WITH_'):
            raise ValueError('Set private runtime role passwords of at least 32 characters')
        values[role] = value
    engine = make_engine()
    try:
        with engine.begin() as connection:
            raw = connection.connection.driver_connection
            for role, password in values.items():
                if not raw.execute('SELECT 1 FROM pg_roles WHERE rolname=%s', (role,)).fetchone():
                    raw.execute(sql.SQL('CREATE ROLE {} LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION').format(sql.Identifier(role)))
                raw.execute(sql.SQL('ALTER ROLE {} PASSWORD {}').format(sql.Identifier(role), sql.Literal(password)))
                raw.execute(sql.SQL('GRANT USAGE ON SCHEMA public TO {}').format(sql.Identifier(role)))
            raw.execute('GRANT SELECT ON traffic_events, api_services, detection_rules, security_alerts, alert_evidence, detection_checkpoints TO sentinelapi_detector')
            raw.execute('GRANT INSERT ON detection_rules, security_alerts, alert_evidence, detection_checkpoints TO sentinelapi_detector')
            raw.execute('GRANT UPDATE ON detection_checkpoints TO sentinelapi_detector')
            raw.execute('GRANT SELECT ON security_alerts, alert_evidence, detection_rules TO sentinelapi_security')
            raw.execute('GRANT UPDATE (status) ON security_alerts TO sentinelapi_security')
            raw.execute('GRANT UPDATE (configuration, enabled, updated_at) ON detection_rules TO sentinelapi_security')
            raw.execute('GRANT INSERT ON audit_logs TO sentinelapi_security')
            raw.execute('GRANT SELECT, INSERT ON ml_windows TO sentinelapi_detector')
            raw.execute('GRANT UPDATE (alert_id) ON ml_windows TO sentinelapi_detector')
            raw.execute('GRANT SELECT ON ml_windows TO sentinelapi_security')
        print('Scoped runtime roles provisioned; no existing alerts or telemetry modified.')
    finally:
        engine.dispose()


if __name__ == '__main__':
    main()
