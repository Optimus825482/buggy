"""
Buggy Call - Buggy Model
Represents golf carts/buggies
"""
from app import db
from app.models import BaseModel, get_current_timestamp
from sqlalchemy import Column, Integer, String, Enum, ForeignKey, DateTime
from sqlalchemy.orm import relationship
import enum


class BuggyStatus(enum.Enum):
    """Buggy status enumeration"""
    AVAILABLE = 'available'
    BUSY = 'busy'
    OFFLINE = 'offline'


class Buggy(db.Model, BaseModel):
    """Buggy model"""
    
    __tablename__ = 'buggies'
    
    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign Keys
    hotel_id = Column(Integer, ForeignKey('hotels.id', ondelete='CASCADE'), nullable=False, index=True)
    current_location_id = Column(Integer, ForeignKey('locations.id', ondelete='SET NULL'), index=True)
    # DEPRECATED: driver_id kept for backward compatibility during migration
    # Use buggy_drivers table and get_active_driver() method instead
    driver_id = Column(Integer, ForeignKey('system_users.id', ondelete='SET NULL'), index=True)
    
    # Buggy Information
    code = Column(String(50), nullable=False, unique=True, index=True)
    model = Column(String(100))
    license_plate = Column(String(50))
    icon = Column(String(10), nullable=True)  # Emoji/icon for visual identification
    status = Column(Enum(BuggyStatus), default=BuggyStatus.AVAILABLE, nullable=False, index=True)
    
    # Timestamps
    created_at = Column(DateTime, default=get_current_timestamp, nullable=False)
    updated_at = Column(DateTime, default=get_current_timestamp, onupdate=get_current_timestamp, nullable=False)
    
    # Relationships
    hotel = relationship('Hotel', back_populates='buggies')
    current_location = relationship('Location', foreign_keys=[current_location_id])
    requests = relationship('BuggyRequest', back_populates='buggy')
    
    # Many-to-many relationship with drivers
    driver_associations = relationship('BuggyDriver', foreign_keys='BuggyDriver.buggy_id', backref='buggy', cascade='all, delete-orphan')
    
    def get_active_driver(self):
        """Get currently active (logged in) driver ID - only if buggy is active"""
        driver_id, _ = self._get_driver_association(active_only=True)
        return driver_id
    
    def get_active_driver_name(self):
        """Get currently active (logged in) driver's name - only if buggy is active"""
        _, driver_name = self._get_driver_association(active_only=True)
        return driver_name
    
    def _get_driver_association(self, active_only=False):
        """
        Internal method to get driver association (cached in memory)
        Returns: (driver_id, driver_name) tuple or (None, None)
        """
        # Cache kontrolü - aynı instance için tekrar sorgu yapma
        cache_key = f'_driver_cache_{"active" if active_only else "assigned"}'
        if hasattr(self, cache_key):
            return getattr(self, cache_key)
        
        from app.models.buggy_driver import BuggyDriver
        from app.models.user import SystemUser
        
        if active_only:
            # Sadece aktif sürücü
            if self.status == BuggyStatus.OFFLINE:
                result = (None, None)
            else:
                assoc = BuggyDriver.query.filter_by(
                    buggy_id=self.id,
                    is_active=True
                ).first()
                if assoc:
                    driver = SystemUser.query.get(assoc.driver_id)
                    result = (assoc.driver_id, driver.full_name if driver and driver.full_name else driver.username if driver else None)
                else:
                    result = (None, None)
        else:
            # Primary veya herhangi bir atanmış sürücü
            primary_assoc = BuggyDriver.query.filter_by(
                buggy_id=self.id,
                is_primary=True
            ).first()
            
            if primary_assoc:
                driver = SystemUser.query.get(primary_assoc.driver_id)
                result = (primary_assoc.driver_id, driver.full_name if driver and driver.full_name else driver.username if driver else None)
            else:
                # Primary yoksa en son atanan
                any_assoc = BuggyDriver.query.filter_by(
                    buggy_id=self.id
                ).order_by(BuggyDriver.assigned_at.desc()).first()
                
                if any_assoc:
                    driver = SystemUser.query.get(any_assoc.driver_id)
                    result = (any_assoc.driver_id, driver.full_name if driver and driver.full_name else driver.username if driver else None)
                else:
                    result = (None, None)
        
        # Cache'e kaydet
        setattr(self, cache_key, result)
        return result
    
    def get_assigned_driver(self):
        """Get assigned driver (primary driver) regardless of active status"""
        driver_id, _ = self._get_driver_association(active_only=False)
        return driver_id
    
    def get_assigned_driver_name(self):
        """Get assigned driver's name (primary driver) regardless of active status"""
        _, driver_name = self._get_driver_association(active_only=False)
        return driver_name
    
    def to_dict(self):
        """Convert to dictionary"""
        # Tek seferde hem aktif hem atanmış sürücü bilgisini al (cache kullanarak)
        active_driver_id, active_driver_name = self._get_driver_association(active_only=True)
        assigned_driver_id, assigned_driver_name = self._get_driver_association(active_only=False)
        
        # Öncelik: Aktif sürücü varsa onu göster, yoksa atanmış sürücüyü göster
        display_driver_id = active_driver_id if active_driver_id else assigned_driver_id
        display_driver_name = active_driver_name if active_driver_name else assigned_driver_name
        
        return {
            'id': self.id,
            'hotel_id': self.hotel_id,
            'driver_id': display_driver_id,  # Aktif veya atanmış sürücü
            'current_location_id': self.current_location_id,
            'code': self.code,
            'model': self.model,
            'license_plate': self.license_plate,
            'icon': self.icon or '🚗',  # Buggy icon for visual identification (default: 🚗)
            'status': self.status.value if self.status else None,
            'driver_name': display_driver_name,  # Aktif veya atanmış sürücü adı
            'current_location': {
                'id': self.current_location.id,
                'name': self.current_location.name
            } if self.current_location else None,
            'current_location_name': self.current_location.name if self.current_location else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
