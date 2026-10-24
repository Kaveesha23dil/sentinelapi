"""Owner-run additive grants for the combined read-only dashboard API.

Does not change passwords, role membership, existing grants or records.
"""
from sqlalchemy import text

from .session import make_engine


GRANTS = (
    'GRANT SELECT ON security_alerts, alert_evidence, detection_rules, ml_windows TO sentinelapi_monitor',
    'GRANT SELECT (id, timestamp, action, metadata, entity_type, entity_id) ON audit_logs TO sentinelapi_monitor',
)


def provision(connection):
    for statement in GRANTS:
        connection.execute(text(statement))


def main():
    engine = make_engine()
    try:
        with engine.begin() as connection:
            provision(connection)
        print('Dashboard reader grants applied; passwords and records preserved.')
        return 0
    except Exception:
        print('Dashboard reader provisioning failed; transaction rolled back; details withheld.')
        return 1
    finally:
        engine.dispose()


if __name__ == '__main__':
    raise SystemExit(main())
