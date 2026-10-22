"""Inspect dedicated roles using their real credentials; emit boolean grants only."""
import json
import os
from pathlib import Path
from pydantic import SecretStr
from sqlalchemy import text
from .config import Settings
from .session import make_engine


def main():
    report = {}
    settings = Settings.from_environment()
    for name, variable in [('sentinelapi_collector', 'COLLECTOR_DB_PASSWORD'),
                           ('sentinelapi_monitor', 'MONITORING_DB_PASSWORD')]:
        engine = make_engine(settings.model_copy(update={'username': name, 'password': SecretStr(os.environ[variable])}))
        try:
            with engine.connect() as connection:
                grants = {permission: connection.scalar(text(
                    "SELECT has_table_privilege(current_user, 'traffic_events', :permission)"),
                    {'permission': permission}) for permission in ['SELECT', 'INSERT', 'UPDATE', 'DELETE']}
                elevated = connection.execute(text('SELECT rolsuper, rolcreatedb, rolcreaterole FROM pg_roles WHERE rolname=current_user')).one()
                assert grants['SELECT'] and not grants['UPDATE'] and not grants['DELETE'] and not any(elevated)
                assert grants['INSERT'] == (name == 'sentinelapi_collector')
                report[name] = {'traffic_events_grants': grants, 'elevated_role': any(elevated),
                                'default_transaction_read_only': connection.scalar(text('SHOW default_transaction_read_only'))}
        finally:
            engine.dispose()
    Path('/evidence/runtime-privileges.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        print('FAIL: runtime privilege verification; details redacted.')
        raise SystemExit(1)
