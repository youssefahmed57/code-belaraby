"""Initial Schema Migration

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-08-01 20:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from app.core.database import Base

# revision identifiers, used by Alembic.
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Use SQLAlchemy metadata create_all for initial revision compatibility
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)

def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
