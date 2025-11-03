"""
Buggy Call - System User Model
Represents admin users and drivers
"""
from app import db
from app.models import BaseModel, get_current_timestamp
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Enum, DateTime, Text
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash
import enum

# Import will be done lazily to avoid circular imports


class UserRole(enum.Enum):
    """User role enumeration"""
    ADMIN = 'admin'
    DRIVER = 'driver'


class SystemUser(db.Model, BaseModel):
    """System user model (admin and drivers)"""
    
    __tablename__ = 'system_users'
    
    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign Keys
    hotel_id = Column(Integer, ForeignKey('hotels.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # User Information
    username = Column(String(50), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255))
    phone = Column(String(50))
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    must_change_password = Column(Boolean, default=False, nullable=False)  # Force password change on next login
    push_subscription = Column(Text)  # JSON string for push notification subscription
    
    # Timestamps
    created_at = Column(DateTime, default=get_current_timestamp, nullable=False)
    last_login = Column(DateTime)
    
    # Relationships
    hotel = relationship('Hotel', back_populates='users')
    accepted_requests = relationship('BuggyRequest', back_populates='accepted_by_driver', foreign_keys='BuggyRequest.accepted_by_id')
    
    # Many-to-many relationship with buggies
    buggy_associations = relationship('BuggyDriver', foreign_keys='BuggyDriver.driver_id', backref='driver', cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'hotel_id': self.hotel_id,
            'username': self.username,
            'role': self.role.value if self.role else None,
            'full_name': self.full_name,
            'email': self.email,
            'phone': self.phone,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
