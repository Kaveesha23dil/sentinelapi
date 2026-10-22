"""Read credentials at runtime; never copy a credential-bearing URL into config."""
from alembic import context

from sentinelapi.db.models import Base
from sentinelapi.db.session import make_engine

if context.is_offline_mode():
    raise RuntimeError('Offline migration disabled: use an explicit runtime database')

engine = make_engine()
try:
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=Base.metadata,
                          compare_type=True, compare_server_default=True)
        with context.begin_transaction():
            context.run_migrations()
finally:
    engine.dispose()
