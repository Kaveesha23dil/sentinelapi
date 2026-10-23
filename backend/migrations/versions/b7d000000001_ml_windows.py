"""Add ML scores; preserve all existing telemetry and alerts."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = 'b7d000000001'
down_revision = 'a6d1023f0001'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('ml_windows',
        sa.Column('id', sa.Uuid(), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('api_service_id', sa.Uuid(), sa.ForeignKey('api_services.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('window_id', sa.String(64), nullable=False),
        sa.Column('window_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('window_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('schema_version', sa.String(64), nullable=False),
        sa.Column('model_version', sa.String(64), nullable=False),
        sa.Column('decision_score', sa.Double(), nullable=False),
        sa.Column('anomaly', sa.Boolean(), nullable=False),
        sa.Column('features', JSONB(), nullable=False),
        sa.Column('provenance', sa.String(64), nullable=False),
        sa.Column('alert_id', sa.Uuid(), sa.ForeignKey('security_alerts.id', ondelete='RESTRICT')),
        sa.UniqueConstraint('window_id','model_version'),
        sa.CheckConstraint('window_end > window_start', name='window_order'))
    op.create_index('ix_ml_windows_api_start', 'ml_windows', ['api_service_id','window_start'])


def downgrade():
    if not (op.get_bind().engine.url.database or '').startswith('sentinelapi_test_'):
        raise RuntimeError('Downgrade restricted to disposable test databases')
    op.drop_table('ml_windows')
