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
        from app.models.buggy_driver import BuggyDriver
        
        # Only return driver if buggy is AVAILABLE or BUSY (not OFFLINE)
        if self.status == BuggyStatus.OFFLINE:
            return None
        
        # Get active (logged in) driver
        active_assoc = BuggyDriver.query.filter_by(
            buggy_id=self.id,
            is_active=True
        ).first()
        
        # Double check: if association exists but buggy is offline, return None
        if active_assoc and self.status == BuggyStatus.OFFLINE:
            return None
            
        return active_assoc.driver_id if active_assoc else None
    
    def get_active_driver_name(self):
        """Get currently active (logged in) driver's name - only if buggy is active"""
        from app.models.buggy_driver import BuggyDriver
        from app.models.user import SystemUser
        
        # Only show driver if buggy is AVAILABLE or BUSY (not OFFLINE)
        if self.status == BuggyStatus.OFFLINE:
            return None
        
        # Get active (logged in) driver
        active_assoc = BuggyDriver.query.filter_by(
            buggy_id=self.id,
            is_active=True
        ).first()
        if active_assoc:
            driver = SystemUser.query.get(active_assoc.driver_id)
            if driver:
                return driver.full_name if driver.full_name else driver.username
        
        return None
    
    def get_assigned_driver(self):
        """Get assigned driver (primary driver) regardless of active status"""
        from app.models.buggy_driver import BuggyDriver
        
        print(f'[GET_ASSIGNED_DRIVER] Checking buggy_id={self.id}')
        
        # Önce primary driver'ı ara
        primary_assoc = BuggyDriver.query.filter_by(
            buggy_id=self.id,
            is_primary=True
        ).first()
        
        if primary_assoc:
            print(f'[GET_ASSIGNED_DRIVER] Found primary driver: {primary_assoc.driver_id}')
            return primary_assoc.driver_id
        
        # Primary yoksa, herhangi bir atamayı al (en son atanan)
        any_assoc = BuggyDriver.query.filter_by(
            buggy_id=self.id
        ).order_by(BuggyDriver.assigned_at.desc()).first()
        
        if any_assoc:
            print(f'[GET_ASSIGNED_DRIVER] Found any driver: {any_assoc.driver_id}')
            return any_assoc.driver_id
        
        print(f'[GET_ASSIGNED_DRIVER] No driver found for buggy_id={self.id}')
        return None
    
    def get_assigned_driver_name(self):
        """Get assigned driver's name (primary driver) regardless of active status"""
        from app.models.buggy_driver import BuggyDriver
        from app.models.user import SystemUser
        
        # Önce primary driver'ı ara
        primary_assoc = BuggyDriver.query.filter_by(
            buggy_id=self.id,
            is_primary=True
        ).first()
        
        if primary_assoc:
            driver = SystemUser.query.get(primary_assoc.driver_id)
            if driver:
                return driver.full_name if driver.full_name else driver.username
        
        # Primary yoksa, herhangi bir atamayı al (en son atanan)
        any_assoc = BuggyDriver.query.filter_by(
            buggy_id=self.id
        ).order_by(BuggyDriver.assigned_at.desc()).first()
        
        if any_assoc:
            driver = SystemUser.query.get(any_assoc.driver_id)
            if driver:
                return driver.full_name if driver.full_name else driver.username
        
        return None
    
    def to_dict(self):
        """Convert to dictionary"""
        # Aktif sürücü (online olan)
        active_driver_id = self.get_active_driver()
        active_driver_name = self.get_active_driver_name()
        
        # Atanmış sürücü (offline olsa bile)
        assigned_driver_id = self.get_assigned_driver()
        assigned_driver_name = self.get_assigned_driver_name()
        
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
