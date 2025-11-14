"""merge multiple heads

Revision ID: 4dbc5ff1187a
Revises: 003, 74c532f38763, perf_composite_idx_001
Create Date: 2025-11-14 23:37:45.438753

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4dbc5ff1187a'
down_revision = ('003', '74c532f38763', 'perf_composite_idx_001')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
