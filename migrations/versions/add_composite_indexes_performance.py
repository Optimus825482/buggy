"""Add composite indexes for performance optimization

Revision ID: perf_composite_idx_001
Revises: 
Create Date: 2024-11-14 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'perf_composite_idx_001'
down_revision = None  # Update this with your latest migration
branch_labels = None
depends_on = None


def upgrade():
    """
    Add composite indexes for frequently queried combinations
    These indexes optimize common query patterns in the application
    """
    
    # Composite index for pending requests by hotel
    # Used in: get_PENDING_requests(hotel_id)
    op.create_index(
        'idx_requests_hotel_status_requested',
        'buggy_requests',
        ['hotel_id', 'status', 'requested_at'],
        unique=False
    )
    
    # Composite index for driver's active request
    # Used in: get_driver_active_request(driver_id)
    op.create_index(
        'idx_requests_driver_status',
        'buggy_requests',
        ['accepted_by_id', 'status'],
        unique=False
    )
    
    # Composite index for location-based queries
    # Used in: filtering requests by location and status
    op.create_index(
        'idx_requests_location_status',
        'buggy_requests',
        ['location_id', 'status'],
        unique=False
    )
    
    # Composite index for buggy-based queries
    # Used in: filtering requests by buggy and status
    op.create_index(
        'idx_requests_buggy_status',
        'buggy_requests',
        ['buggy_id', 'status'],
        unique=False
    )
    
    # Index for date range queries
    # Used in: get_requests with date filters
    op.create_index(
        'idx_requests_requested_at',
        'buggy_requests',
        ['requested_at'],
        unique=False
    )


def downgrade():
    """Remove composite indexes"""
    
    op.drop_index('idx_requests_requested_at', table_name='buggy_requests')
    op.drop_index('idx_requests_buggy_status', table_name='buggy_requests')
    op.drop_index('idx_requests_location_status', table_name='buggy_requests')
    op.drop_index('idx_requests_driver_status', table_name='buggy_requests')
    op.drop_index('idx_requests_hotel_status_requested', table_name='buggy_requests')
