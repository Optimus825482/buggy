"""
Buggy Call - Session Model
Tracks user sessions for security
"""
from app import db
from app.models import BaseModel, get_current_timestamp
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship


class Session(db.Model, BaseModel):
    """Session model"""
    
    __tablename__ = 'sessions'
    
    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign Keys
    user_id = Column(Integer, ForeignKey('system_users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Session Information
    session_token = Column(String(500), nullable=False, unique=True, index=True)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    is_active = Column(db.Boolean, default=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False, index=True)
    
    # Timestamps
    created_at = Column(DateTime, default=get_current_timestamp, nullable=False)
    last_activity = Column(DateTime, default=get_current_timestamp, onupdate=get_current_timestamp)
    revoked_at = Column(DateTime)
    
    # Relationships
    user = relationship('SystemUser')
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'session_token': self.session_token,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'is_active': self.is_active,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_activity': self.last_activity.isoformat() if self.last_activity else None,
            'revoked_at': self.revoked_at.isoformat() if self.revoked_at else None
        }
