"""
Buggy Call - Hotel Model
"""
from app import db
from app.models import BaseModel, get_current_timestamp
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.orm import relationship


class Hotel(db.Model, BaseModel):
    """Hotel model"""
    
    __tablename__ = 'hotels'
    
    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Hotel Information
    name = Column(String(255), nullable=False)
    code = Column(String(50), nullable=True, unique=True)  # Hotel code (e.g., 'TEST', 'HOTEL1')
    address = Column(Text, nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)
    logo = Column(String(500), nullable=True)
    timezone = Column(String(50), default='Europe/Istanbul')
    
    # Timestamps
    created_at = Column(DateTime, default=get_current_timestamp, nullable=False)
    updated_at = Column(DateTime, default=get_current_timestamp, onupdate=get_current_timestamp, nullable=False)
    
    # Relationships
    users = relationship('SystemUser', back_populates='hotel', cascade='all, delete-orphan')
    locations = relationship('Location', back_populates='hotel', cascade='all, delete-orphan')
    buggies = relationship('Buggy', back_populates='hotel', cascade='all, delete-orphan')
    requests = relationship('BuggyRequest', back_populates='hotel', cascade='all, delete-orphan')
    audit_logs = relationship('AuditTrail', back_populates='hotel', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Hotel {self.name}>'
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'address': self.address,
            'phone': self.phone,
            'email': self.email,
            'logo': self.logo,
            'timezone': self.timezone,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

