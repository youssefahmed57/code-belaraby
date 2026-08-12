"""Phase 0 and Phase 1A Security Tables Migration

Revision ID: 002_security_tables
Revises: 001_initial_schema
Create Date: 2026-08-05 22:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '002_security_tables'
down_revision = '001_initial_schema'
branch_labels = None
depends_on = None

def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # 1. User table additions
    user_columns = [c['name'] for c in inspector.get_columns('users')]
    if 'failed_login_attempts' not in user_columns:
        op.add_column('users', sa.Column('failed_login_attempts', sa.Integer(), nullable=True, server_default='0'))
    if 'locked_until' not in user_columns:
        op.add_column('users', sa.Column('locked_until', sa.DateTime(), nullable=True))
    if 'xp_points' not in user_columns:
        op.add_column('users', sa.Column('xp_points', sa.Integer(), nullable=True, server_default='0'))
    if 'level' not in user_columns:
        op.add_column('users', sa.Column('level', sa.Integer(), nullable=True, server_default='1'))

    # 2. Course table additions
    course_columns = [c['name'] for c in inspector.get_columns('courses')]
    if 'unlock_mode' not in course_columns:
        op.add_column('courses', sa.Column('unlock_mode', sa.String(50), nullable=True, server_default='sequential'))

    # 3. Payment table additions
    payment_columns = [c['name'] for c in inspector.get_columns('payments')]
    if 'receipt_hash' not in payment_columns:
        op.add_column('payments', sa.Column('receipt_hash', sa.String(64), nullable=True))
        op.create_index('ix_payments_receipt_hash', 'payments', ['receipt_hash'])

def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    payment_columns = [c['name'] for c in inspector.get_columns('payments')]
    if 'receipt_hash' in payment_columns:
        op.drop_index('ix_payments_receipt_hash', table_name='payments')
        op.drop_column('payments', 'receipt_hash')

    course_columns = [c['name'] for c in inspector.get_columns('courses')]
    if 'unlock_mode' in course_columns:
        op.drop_column('courses', 'unlock_mode')

    user_columns = [c['name'] for c in inspector.get_columns('users')]
    if 'level' in user_columns:
        op.drop_column('users', 'level')
    if 'xp_points' in user_columns:
        op.drop_column('users', 'xp_points')
    if 'locked_until' in user_columns:
        op.drop_column('users', 'locked_until')
    if 'failed_login_attempts' in user_columns:
        op.drop_column('users', 'failed_login_attempts')
