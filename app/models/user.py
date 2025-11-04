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
    must_change_password = Column(Boolean, default=False, nullable=False)
    push_subscription = Column(Text)
    push_subscription_date = Column(DateTime)
    notification_preferences = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=get_current_timestamp, nullable=False)
    last_login = Column(DateTime)
    
    # Relationships
    hotel = relationship('Hotel', back_populates='users')
    accepted_requests = relationship('BuggyRequest', back_populates='accepted_by_driver', foreign_keys='BuggyRequest.accepted_by_id')
    
    # Many-to-many relationship with buggies
    buggy_associations = relationship('BuggyDriver', foreign_keys='BuggyDriver.driver_id', backref='driver', cascade='all, delete-orphan')
    
    @property
    def buggy(self):
        """Get the buggy assigned to this driver (if any)"""
        if self.role != UserRole.DRIVER:
            return None
        
        from app.models.buggy_driver import BuggyDriver
        from app.models.buggy import Buggy
        
        # Get active buggy association
        active_assoc = BuggyDriver.query.filter_by(
            driver_id=self.id,
            is_primary=True
        ).first()
        
        if active_assoc:
            return Buggy.query.get(active_assoc.buggy_id)
        
        return None
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password"""
        return check_password_hash(self.password_hash, password)
    
    def get_notification_preferences(self):
        """Get notification preferences as dict"""
        import json
        if self.notification_preferences:
            try:
                return json.loads(self.notification_preferences)
            except:
                pass
        # Default preferences
        return {
            'enabled': True,
            'sound': True,
            'vibration': True,
            'priority_only': False,
            'quiet_hours': {
                'enabled': False,
                'start': '22:00',
                'end': '08:00'
            }
        }
    
    def set_notification_preferences(self, preferences):
        """Set notification preferences from dict"""
        import json
        self.notification_preferences = json.dumps(preferences)
    
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
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'push_subscription_date': self.push_subscription_date.isoformat() if self.push_subscription_date else None,
            'notification_preferences': self.get_notification_preferences()
        }
