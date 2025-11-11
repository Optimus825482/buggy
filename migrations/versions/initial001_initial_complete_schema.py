"""initial_complete_schema

Revision ID: initial001
Revises: 
Create Date: 2025-11-04 20:52:18.815214

Complete database schema for Buggy Call system
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'initial001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create hotels table
    op.create_table('hotels',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )
    op.create_index(op.f('ix_hotels_is_active'), 'hotels', ['is_active'], unique=False)

    # Create system_users table
    op.create_table('system_users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('hotel_id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=100), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('role', sa.Enum('admin', 'driver', name='userrole'), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['hotel_id'], ['hotels.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )
    op.create_index(op.f('ix_system_users_hotel_id'), 'system_users', ['hotel_id'], unique=False)
    op.create_index(op.f('ix_system_users_is_active'), 'system_users', ['is_active'], unique=False)
    op.create_index(op.f('ix_system_users_role'), 'system_users', ['role'], unique=False)
    op.create_index(op.f('ix_system_users_username'), 'system_users', ['username'], unique=True)

    # Create locations table
    op.create_table('locations',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('hotel_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('qr_code_data', sa.String(length=500), nullable=False),
        sa.Column('qr_code_image', sa.Text(), nullable=True),
        sa.Column('location_image', sa.Text(), nullable=True),
        sa.Column('display_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('latitude', sa.DECIMAL(precision=10, scale=8), nullable=True),
        sa.Column('longitude', sa.DECIMAL(precision=11, scale=8), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['hotel_id'], ['hotels.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )
    op.create_index(op.f('ix_locations_display_order'), 'locations', ['display_order'], unique=False)
    op.create_index(op.f('ix_locations_hotel_id'), 'locations', ['hotel_id'], unique=False)
    op.create_index(op.f('ix_locations_is_active'), 'locations', ['is_active'], unique=False)
    op.create_index(op.f('ix_locations_qr_code_data'), 'locations', ['qr_code_data'], unique=True)

    # Create buggies table
    op.create_table('buggies',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('hotel_id', sa.Integer(), nullable=False),
        sa.Column('buggy_number', sa.String(length=50), nullable=False),
        sa.Column('plate_number', sa.String(length=50), nullable=True),
        sa.Column('status', sa.Enum('available', 'busy', 'maintenance', 'offline', name='buggystatus'), nullable=False, server_default='available'),
        sa.Column('current_location_id', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['current_location_id'], ['locations.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['hotel_id'], ['hotels.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )
    op.create_index(op.f('ix_buggies_hotel_id'), 'buggies', ['hotel_id'], unique=False)
    op.create_index(op.f('ix_buggies_is_active'), 'buggies', ['is_active'], unique=False)
    op.create_index(op.f('ix_buggies_status'), 'buggies', ['status'], unique=False)

    # Create buggy_drivers table
    op.create_table('buggy_drivers',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('buggy_id', sa.Integer(), nullable=False),
        sa.Column('driver_id', sa.Integer(), nullable=False),
        sa.Column('assigned_at', sa.DateTime(), nullable=False),
        sa.Column('unassigned_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.ForeignKeyConstraint(['buggy_id'], ['buggies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['driver_id'], ['system_users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )
    op.create_index(op.f('ix_buggy_drivers_buggy_id'), 'buggy_drivers', ['buggy_id'], unique=False)
    op.create_index(op.f('ix_buggy_drivers_driver_id'), 'buggy_drivers', ['driver_id'], unique=False)
    op.create_index(op.f('ix_buggy_drivers_is_active'), 'buggy_drivers', ['is_active'], unique=False)

    # Create buggy_requests table
    op.create_table('buggy_requests',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('hotel_id', sa.Integer(), nullable=False),
        sa.Column('location_id', sa.Integer(), nullable=False),
        sa.Column('buggy_id', sa.Integer(), nullable=True),
        sa.Column('driver_id', sa.Integer(), nullable=True),
        sa.Column('guest_name', sa.String(length=255), nullable=True),
        sa.Column('guest_room', sa.String(length=50), nullable=True),
        sa.Column('guest_phone', sa.String(length=50), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('PENDING', 'accepted', 'completed', 'cancelled', name='requeststatus'), nullable=False, server_default='PENDING'),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('requested_at', sa.DateTime(), nullable=False),
        sa.Column('accepted_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('cancelled_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['buggy_id'], ['buggies.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['driver_id'], ['system_users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['hotel_id'], ['hotels.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['location_id'], ['locations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )
    op.create_index(op.f('ix_buggy_requests_hotel_id'), 'buggy_requests', ['hotel_id'], unique=False)
    op.create_index(op.f('ix_buggy_requests_location_id'), 'buggy_requests', ['location_id'], unique=False)
    op.create_index(op.f('ix_buggy_requests_status'), 'buggy_requests', ['status'], unique=False)

    # Create sessions table
    op.create_table('sessions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('session_token', sa.String(length=255), nullable=False),
        sa.Column('ip_address', sa.String(length=50), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['system_users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )
    op.create_index(op.f('ix_sessions_session_token'), 'sessions', ['session_token'], unique=True)
    op.create_index(op.f('ix_sessions_user_id'), 'sessions', ['user_id'], unique=False)

    # Create audit_trail table
    op.create_table('audit_trail',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('hotel_id', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('entity_type', sa.String(length=100), nullable=True),
        sa.Column('entity_id', sa.Integer(), nullable=True),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['hotel_id'], ['hotels.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['system_users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )
    op.create_index(op.f('ix_audit_trail_action'), 'audit_trail', ['action'], unique=False)
    op.create_index(op.f('ix_audit_trail_created_at'), 'audit_trail', ['created_at'], unique=False)
    op.create_index(op.f('ix_audit_trail_hotel_id'), 'audit_trail', ['hotel_id'], unique=False)

    # Create notification_logs table
    op.create_table('notification_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('hotel_id', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('request_id', sa.Integer(), nullable=True),
        sa.Column('notification_type', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='sent'),
        sa.Column('sent_at', sa.DateTime(), nullable=False),
        sa.Column('read_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['hotel_id'], ['hotels.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['request_id'], ['buggy_requests.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['system_users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )
    op.create_index(op.f('ix_notification_logs_hotel_id'), 'notification_logs', ['hotel_id'], unique=False)
    op.create_index(op.f('ix_notification_logs_sent_at'), 'notification_logs', ['sent_at'], unique=False)
    op.create_index(op.f('ix_notification_logs_user_id'), 'notification_logs', ['user_id'], unique=False)


def downgrade():
    op.drop_table('notification_logs')
    op.drop_table('audit_trail')
    op.drop_table('sessions')
    op.drop_table('buggy_requests')
    op.drop_table('buggy_drivers')
    op.drop_table('buggies')
    op.drop_table('locations')
    op.drop_table('system_users')
    op.drop_table('hotels')
