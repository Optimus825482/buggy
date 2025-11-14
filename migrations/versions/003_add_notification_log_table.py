"""Add notification_logs table for delivery tracking

Revision ID: 003
Revises: 002
Create Date: 2024-11-14 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade():
    """Create notification_logs table"""
    op.create_table(
        'notification_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('notification_type', sa.String(length=50), nullable=False),
        sa.Column('priority', sa.String(length=20), nullable=True),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('body', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=True),
        sa.Column('sent_at', sa.DateTime(), nullable=False),
        sa.Column('delivered_at', sa.DateTime(), nullable=True),
        sa.Column('clicked_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['system_users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for performance
    op.create_index('idx_notification_user_id', 'notification_logs', ['user_id'])
    op.create_index('idx_notification_type', 'notification_logs', ['notification_type'])
    op.create_index('idx_notification_priority', 'notification_logs', ['priority'])
    op.create_index('idx_notification_status', 'notification_logs', ['status'])
    op.create_index('idx_notification_sent_at', 'notification_logs', ['sent_at'])
    op.create_index('idx_notification_status_sent_at', 'notification_logs', ['status', 'sent_at'])
    op.create_index('idx_notification_type_priority', 'notification_logs', ['notification_type', 'priority'])


def downgrade():
    """Drop notification_logs table"""
    op.drop_index('idx_notification_type_priority', table_name='notification_logs')
    op.drop_index('idx_notification_status_sent_at', table_name='notification_logs')
    op.drop_index('idx_notification_sent_at', table_name='notification_logs')
    op.drop_index('idx_notification_status', table_name='notification_logs')
    op.drop_index('idx_notification_priority', table_name='notification_logs')
    op.drop_index('idx_notification_type', table_name='notification_logs')
    op.drop_index('idx_notification_user_id', table_name='notification_logs')
    op.drop_table('notification_logs')
