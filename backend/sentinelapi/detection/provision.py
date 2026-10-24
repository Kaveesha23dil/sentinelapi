"""Owner-run scoped grants; existing passwords change only with explicit opt-in."""
import argparse
import os

from psycopg import sql

from sentinelapi.db.session import make_engine

ROLES = {'sentinelapi_detector': 'DETECTOR_DB_PASSWORD',
         'sentinelapi_security': 'SECURITY_DB_PASSWORD'}
GRANTS = (
    'GRANT SELECT ON traffic_events, api_services, detection_rules, security_alerts, alert_evidence, detection_checkpoints TO sentinelapi_detector',
    'GRANT INSERT ON detection_rules, security_alerts, alert_evidence, detection_checkpoints TO sentinelapi_detector',
    'GRANT UPDATE ON detection_checkpoints TO sentinelapi_detector',
    'GRANT SELECT, INSERT ON ml_windows TO sentinelapi_detector',
    'GRANT UPDATE (alert_id) ON ml_windows TO sentinelapi_detector',
    'GRANT SELECT ON security_alerts, alert_evidence, detection_rules, ml_windows TO sentinelapi_security',
    'GRANT UPDATE (status) ON security_alerts TO sentinelapi_security',
    'GRANT UPDATE (configuration, enabled, updated_at) ON detection_rules TO sentinelapi_security',
    'GRANT INSERT ON audit_logs TO sentinelapi_security',
    'GRANT SELECT (event_id, timestamp, http_method, endpoint, status_code) ON traffic_events TO sentinelapi_security',
    'GRANT SELECT (id, timestamp, action, metadata, entity_type, entity_id) ON audit_logs TO sentinelapi_security',
)


def provision(raw, passwords, database, *, rotate_existing=False):
    existing = {}
    # Validate the complete request before changing any role. The caller owns
    # one transaction for all role/grant operations.
    for role in ROLES:
        row = raw.execute(
            'SELECT rolsuper, rolcreatedb, rolcreaterole, rolreplication, rolbypassrls, rolcanlogin '
            'FROM pg_roles WHERE rolname=%s', (role,)).fetchone()
        if row and (any(row[:5]) or not row[5]):
            raise ValueError('Refusing an existing privileged or non-login runtime role')
        existing[role] = row is not None
        if row is None or rotate_existing:
            value = passwords.get(role, '')
            if len(value) < 32 or value.startswith('REPLACE_WITH_'):
                raise ValueError('Configure strong private runtime role passwords')
    for role in ROLES:
        if not existing[role]:
            raw.execute(sql.SQL('CREATE ROLE {} LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE '
                                'NOREPLICATION NOBYPASSRLS PASSWORD {}').format(
                                    sql.Identifier(role), sql.Literal(passwords[role])))
        elif rotate_existing:
            raw.execute(sql.SQL('ALTER ROLE {} PASSWORD {}').format(
                sql.Identifier(role), sql.Literal(passwords[role])))
        raw.execute(sql.SQL('GRANT CONNECT ON DATABASE {} TO {}').format(
            sql.Identifier(database), sql.Identifier(role)))
        raw.execute(sql.SQL('GRANT USAGE ON SCHEMA public TO {}').format(sql.Identifier(role)))
    for statement in GRANTS:
        raw.execute(statement)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rotate-existing-passwords', action='store_true',
                        help='Explicitly rotate BOTH runtime role passwords; update dependents together')
    args = parser.parse_args()
    engine = make_engine()
    try:
        with engine.begin() as connection:
            provision(connection.connection.driver_connection,
                      {role: os.getenv(variable, '') for role, variable in ROLES.items()},
                      engine.url.database, rotate_existing=args.rotate_existing_passwords)
        print('Scoped runtime grants applied; existing passwords preserved.' if not args.rotate_existing_passwords
              else 'Scoped runtime grants applied; explicitly requested password rotation completed.')
    except Exception:
        # Driver/SQL exceptions can include credential-bearing statements.
        print('Runtime provisioning failed; transaction rolled back. Verify owner access, schema and private credentials.')
        return 1
    finally:
        engine.dispose()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
