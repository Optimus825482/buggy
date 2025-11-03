"""
Buggy Call - Audit Trail Model
Tracks all important system events
"""
from app import db
from app.models import BaseModel, get_current_timestamp
from sqlalchemy import Column, Integer, String, Text, ForeignKey, BigInteger, DateTime
from sqlalchemy.orm import relationship


class AuditTrail(db.Model, BaseModel):
    """
    Audit trail model - IMMUTABLE
    
    Security: Audit logs cannot be modified or deleted to maintain integrity
    """
    
    __tablename__ = 'audit_trail'
    __table_args__ = {'info': {'immutable': True}}
    
    # Primary Key
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    
    # Foreign Keys
    hotel_id = Column(Integer, ForeignKey('hotels.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('system_users.id', ondelete='SET NULL'), index=True)
    
    # Audit Information
    action = Column(String(100), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False, index=True)
    entity_id = Column(Integer, index=True)
    old_values = Column(Text)
    new_values = Column(Text)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    
    # Timestamp
    created_at = Column(DateTime, default=get_current_timestamp, nullable=False, index=True)
    
    # Relationships
    hotel = relationship('Hotel', back_populates='audit_logs')
    user = relationship('SystemUser')
    
    def __setattr__(self, key, value):
        """Prevent modification of audit logs after creation"""
        # Allow setting attributes during initialization
        if not hasattr(self, 'id') or self.id is None:
            super().__setattr__(key, value)
        else:
            # Prevent modification after creation
            raise AttributeError(f"Audit logs are immutable. Cannot modify '{key}'")
    
    def __delattr__(self, key):
        """Prevent deletion of audit log attributes"""
        raise AttributeError("Audit logs are immutable. Cannot delete attributes")
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'hotel_id': self.hotel_id,
            'user_id': self.user_id,
            'action': self.action,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'old_values': self.old_values,
            'new_values': self.new_values,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
