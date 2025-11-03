"""
Buggy Call - Location Model
Represents guest pickup locations with QR codes
"""
from app import db
from app.models import BaseModel, get_current_timestamp
from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, DECIMAL, DateTime
from sqlalchemy.orm import relationship


class Location(db.Model, BaseModel):
    """Location model"""
    
    __tablename__ = 'locations'
    
    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign Keys
    hotel_id = Column(Integer, ForeignKey('hotels.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Location Information
    name = Column(String(255), nullable=False)
    description = Column(Text)
    qr_code_data = Column(String(500), nullable=False, unique=True, index=True)
    qr_code_image = Column(Text)  # Base64 encoded image or file path
    display_order = Column(Integer, default=0, nullable=False, index=True)  # For sorting locations
    latitude = Column(DECIMAL(10, 8))
    longitude = Column(DECIMAL(11, 8))
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    
    # Timestamps
    created_at = Column(DateTime, default=get_current_timestamp, nullable=False)
    updated_at = Column(DateTime, default=get_current_timestamp, onupdate=get_current_timestamp, nullable=False)
    
    # Relationships
    hotel = relationship('Hotel', back_populates='locations')
    requests = relationship('BuggyRequest', back_populates='location')
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'hotel_id': self.hotel_id,
            'name': self.name,
            'description': self.description,
            'qr_code_data': self.qr_code_data,
            'qr_code_image': self.qr_code_image,
            'display_order': self.display_order,
            'latitude': float(self.latitude) if self.latitude else None,
            'longitude': float(self.longitude) if self.longitude else None,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
