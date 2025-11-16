"""
Enum tanımlamaları
"""
from enum import Enum


class UserRole(str, Enum):
    """Kullanıcı rolleri"""
    ADMIN = "admin"
    DRIVER = "driver"
    
    def __str__(self) -> str:
        return self.value


class ShuttleStatus(str, Enum):
    """Shuttle durumları"""
    AVAILABLE = "available"  # Müsait
    BUSY = "busy"           # Meşgul
    OFFLINE = "offline"     # Çevrimdışı
    
    def __str__(self) -> str:
        return self.value


class RequestStatus(str, Enum):
    """Request durumları"""
    PENDING = "PENDING"         # Bekliyor
    ACCEPTED = "ACCEPTED"       # Kabul edildi
    COMPLETED = "COMPLETED"     # Tamamlandı
    CANCELLED = "CANCELLED"     # İptal edildi
    UNANSWERED = "UNANSWERED"   # Cevapsız (timeout)
    
    def __str__(self) -> str:
        return self.value
