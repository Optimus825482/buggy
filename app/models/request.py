"""
Buggy Call - Buggy Request Model
Represents guest requests for buggy pickup
"""
from app import db
from app.models import BaseModel, get_current_timestamp
from sqlalchemy import Column, Integer, String, Text, Enum, ForeignKey, DateTime
from sqlalchemy.orm import relationship
import enum


class RequestStatus(enum.Enum):
    """Request status enumeration"""
    PENDING = 'pending'
    ACCEPTED = 'accepted'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'


class BuggyRequest(db.Model, BaseModel):
    """Buggy request model"""
    
    __tablename__ = 'buggy_requests'
    
    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign Keys
    hotel_id = Column(Integer, ForeignKey('hotels.id', ondelete='CASCADE'), nullable=False, index=True)
    location_id = Column(Integer, ForeignKey('locations.id', ondelete='CASCADE'), nullable=False, index=True)
    buggy_id = Column(Integer, ForeignKey('buggies.id', ondelete='SET NULL'), index=True)
    accepted_by_id = Column(Integer, ForeignKey('system_users.id', ondelete='SET NULL'), index=True)
    
    # Request Information
    guest_name = Column(String(255))
    room_number = Column(String(50), index=True)
    has_room = Column(db.Boolean, default=True, nullable=False)  # Does guest have a room number?
    phone = Column(String(50))
    notes = Column(Text)
    guest_device_id = Column(Text)  # Push notification subscription info (JSON)
    status = Column(Enum(RequestStatus), default=RequestStatus.PENDING, nullable=False, index=True)
    cancelled_by = Column(String(50))  # 'driver', 'guest', 'admin'
    
    # Timestamps
    requested_at = Column(DateTime, default=get_current_timestamp, nullable=False, index=True)
    accepted_at = Column(DateTime)
    completed_at = Column(DateTime)
    cancelled_at = Column(DateTime)
    
    # Performance Metrics
    response_time = Column(Integer)  # Seconds from request to acceptance
    completion_time = Column(Integer)  # Seconds from acceptance to completion
    
    # Relationships
    hotel = relationship('Hotel', back_populates='requests')
    location = relationship('Location', back_populates='requests')
    buggy = relationship('Buggy', back_populates='requests')
    accepted_by_driver = relationship('SystemUser', back_populates='accepted_requests', foreign_keys=[accepted_by_id])
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'hotel_id': self.hotel_id,
            'location_id': self.location_id,
            'buggy_id': self.buggy_id,
            'accepted_by_id': self.accepted_by_id,
            'guest_name': self.guest_name,
            'room_number': self.room_number,
            'has_room': self.has_room,
            'phone': self.phone,
            'notes': self.notes,
            'guest_device_id': self.guest_device_id,
            'status': self.status.value if self.status else None,
            'cancelled_by': self.cancelled_by,
            'requested_at': self.requested_at.isoformat() if self.requested_at else None,
            'accepted_at': self.accepted_at.isoformat() if self.accepted_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'cancelled_at': self.cancelled_at.isoformat() if self.cancelled_at else None,
            'response_time': self.response_time,
            'completion_time': self.completion_time,
            'location': self.location.to_dict() if self.location else None,
            'buggy': self.buggy.to_dict() if self.buggy else None,
            'driver': self.accepted_by_driver.to_dict() if self.accepted_by_driver else None
        }
