"""
Buggy Call - Buggy Driver Association Model
Many-to-many relationship between buggies and drivers
"""
from app import db
from app.models import BaseModel, get_current_timestamp
from sqlalchemy import Column, Integer, ForeignKey, DateTime, Boolean


class BuggyDriver(db.Model, BaseModel):
    """Association table for buggy-driver many-to-many relationship"""
    
    __tablename__ = 'buggy_drivers'
    
    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign Keys
    buggy_id = Column(Integer, ForeignKey('buggies.id', ondelete='CASCADE'), nullable=False, index=True)
    driver_id = Column(Integer, ForeignKey('system_users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Status
    is_active = Column(Boolean, default=False, nullable=False, index=True)  # Currently logged in
    is_primary = Column(Boolean, default=False, nullable=False)  # Primary driver for this buggy
    
    # Timestamps
    assigned_at = Column(DateTime, default=get_current_timestamp, nullable=False)
    last_active_at = Column(DateTime)
    
    # Unique constraint: one driver can be assigned to one buggy at a time
    __table_args__ = (
        db.UniqueConstraint('buggy_id', 'driver_id', name='uq_buggy_driver'),
    )
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'buggy_id': self.buggy_id,
            'driver_id': self.driver_id,
            'is_active': self.is_active,
            'is_primary': self.is_primary,
            'assigned_at': self.assigned_at.isoformat() if self.assigned_at else None,
            'last_active_at': self.last_active_at.isoformat() if self.last_active_at else None
        }
