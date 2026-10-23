"""Add nullable alert incident metadata and a transactional detector watermark.

Existing demonstration alerts remain unchanged. No data backfill or deletion.
"""
from alembic import op
import sqlalchemy as sa

revision = 'a6d1023f0001'
down_revision = '71a9c2e16b05'
branch_labels = None
depends_on = None


def upgrade():
    for column in [sa.Column('incident_fingerprint', sa.String(64)),
                   sa.Column('rule_version', sa.Integer()),
                   sa.Column('window_start', sa.DateTime(timezone=True)),
                   sa.Column('window_end', sa.DateTime(timezone=True)),
                   sa.Column('measured_value', sa.Numeric(20, 6)),
                   sa.Column('threshold', sa.Numeric(20, 6))]:
        op.add_column('security_alerts', column)
    op.create_unique_constraint('uq_security_alerts_incident_fingerprint', 'security_alerts', ['incident_fingerprint'])
    op.create_check_constraint('window_order', 'security_alerts', 'window_end > window_start')
    op.create_check_constraint('rule_version_positive', 'security_alerts', 'rule_version > 0')
    op.create_table('detection_checkpoints',
        sa.Column('name', sa.String(64), primary_key=True),
        sa.Column('watermark', sa.DateTime(timezone=True), nullable=False))


def downgrade():
    if not (op.get_bind().engine.url.database or '').startswith('sentinelapi_test_'):
        raise RuntimeError('Downgrade restricted to disposable test databases')
    op.drop_table('detection_checkpoints')
    op.drop_constraint('ck_security_alerts_rule_version_positive', 'security_alerts', type_='check')
    op.drop_constraint('ck_security_alerts_window_order', 'security_alerts', type_='check')
    op.drop_constraint('uq_security_alerts_incident_fingerprint', 'security_alerts', type_='unique')
    for name in ['threshold', 'measured_value', 'window_end', 'window_start', 'rule_version', 'incident_fingerprint']:
        op.drop_column('security_alerts', name)
