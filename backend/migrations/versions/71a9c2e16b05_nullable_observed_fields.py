"""Represent unavailable gateway measurements as NULL, preserving existing rows."""
from alembic import op
import sqlalchemy as sa

revision = '71a9c2e16b05'
down_revision = '4061c4c0ee19'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('traffic_events', 'client_identifier', existing_type=sa.String(128), nullable=True)
    op.alter_column('traffic_events', 'latency_ms', existing_type=sa.Numeric(14, 3), nullable=True)


def downgrade():
    if not (op.get_bind().engine.url.database or '').startswith('sentinelapi_test_'):
        raise RuntimeError('Downgrade restricted to disposable test databases')
    # Never replace missing measurements with fabricated zeros. Refuse if NULLs exist.
    if op.get_bind().execute(sa.text('SELECT EXISTS (SELECT 1 FROM traffic_events WHERE client_identifier IS NULL OR latency_ms IS NULL)')).scalar():
        raise RuntimeError('Cannot restore NOT NULL while unobserved measurements exist')
    op.alter_column('traffic_events', 'client_identifier', existing_type=sa.String(128), nullable=False)
    op.alter_column('traffic_events', 'latency_ms', existing_type=sa.Numeric(14, 3), nullable=False)
