"""add_push_notification_fields

Revision ID: 002
Revises: initial001
Create Date: 2025-11-04 17:30:00.000000

Add push notification and password change fields to system_users
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002'
down_revision = 'initial001'
branch_labels = None
depends_on = None


def upgrade():
    """Add missing columns to system_users table"""
    # Add must_change_password column
    op.add_column('system_users', 
        sa.Column('must_change_password', sa.Boolean(), nullable=False, server_default='0')
    )
    
    # Add push_subscription column (TEXT for JSON data)
    op.add_column('system_users', 
        sa.Column('push_subscription', sa.Text(), nullable=True)
    )
    
    # Add push_subscription_date column
    op.add_column('system_users', 
        sa.Column('push_subscription_date', sa.DateTime(), nullable=True)
    )
    
    # Add notification_preferences column (TEXT for JSON data)
    op.add_column('system_users', 
        sa.Column('notification_preferences', sa.Text(), nullable=True)
    )


def downgrade():
    """Remove added columns"""
    op.drop_column('system_users', 'notification_preferences')
    op.drop_column('system_users', 'push_subscription_date')
    op.drop_column('system_users', 'push_subscription')
    op.drop_column('system_users', 'must_change_password')
