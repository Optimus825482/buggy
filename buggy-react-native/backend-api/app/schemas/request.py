"""
Request Pydantic schemas
Guest ve Driver request işlemleri için schema'lar
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, validator
from app.models.enums import RequestStatus


# ============================================================================
# Guest Request Schemas (Görev 7.1)
# ============================================================================

class RequestCreate(BaseModel):
    """
    Guest tarafından yeni request oluşturma
    Requirements: 6.1
    """
    location_id: int = Field(..., description="Çağrı yapılan lokasyon ID", gt=0)
    room_number: Optional[str] = Field(None, description="Oda numarası", max_length=50)
    guest_name: Optional[str] = Field(None, description="Misafir adı", max_length=255)
    phone: Optional[str] = Field(None, description="Telefon numarası", max_length=50)
    notes: Optional[str] = Field(None, description="Ek notlar")
    has_room: bool = Field(True, description="Oda var mı?")
    
    @validator('room_number')
    def validate_room_number(cls, v, values):
        """Oda varsa oda numarası zorunlu"""
        if values.get('has_room', True) and not v:
            raise ValueError('Oda numarası gereklidir')
        return v
    
    @validator('phone')
    def validate_phone(cls, v):
        """Telefon numarası formatı kontrolü (opsiyonel)"""
        if v and len(v) < 10:
            raise ValueError('Geçerli bir telefon numarası giriniz')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "location_id": 1,
                "room_number": "305",
                "guest_name": "Ahmet Yılmaz",
                "phone": "+905551234567",
                "notes": "Acil",
                "has_room": True
            }
        }


class RequestResponse(BaseModel):
    """
    Request detay response
    Requirements: 6.1, 6.5
    """
    id: int
    hotel_id: int
    location_id: int
    completion_location_id: Optional[int] = None
    shuttle_id: Optional[int] = None
    accepted_by_id: Optional[int] = None
    
    # Misafir bilgileri
    guest_name: Optional[str] = None
    room_number: Optional[str] = None
    has_room: bool
    phone: Optional[str] = None
    notes: Optional[str] = None
    
    # Durum
    status: str
    cancelled_by: Optional[str] = None
    
    # Zaman bilgileri
    requested_at: datetime
    accepted_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    timeout_at: Optional[datetime] = None
    
    # Performans metrikleri
    response_time: Optional[int] = None
    completion_time: Optional[int] = None
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "hotel_id": 1,
                "location_id": 1,
                "completion_location_id": None,
                "shuttle_id": None,
                "accepted_by_id": None,
                "guest_name": "Ahmet Yılmaz",
                "room_number": "305",
                "has_room": True,
                "phone": "+905551234567",
                "notes": "Acil",
                "status": "PENDING",
                "cancelled_by": None,
                "requested_at": "2024-11-16T10:30:00Z",
                "accepted_at": None,
                "completed_at": None,
                "cancelled_at": None,
                "timeout_at": None,
                "response_time": None,
                "completion_time": None,
                "created_at": "2024-11-16T10:30:00Z",
                "updated_at": "2024-11-16T10:30:00Z"
            }
        }


class GuestFCMTokenUpdate(BaseModel):
    """
    Guest FCM token güncelleme
    Requirements: 6.5
    """
    fcm_token: str = Field(..., description="Firebase Cloud Messaging token", min_length=10)
    
    class Config:
        json_schema_extra = {
            "example": {
                "fcm_token": "dGhpcyBpcyBhIGZha2UgdG9rZW4gZm9yIGV4YW1wbGU="
            }
        }


# ============================================================================
# Driver Request Schemas (Görev 8.1 için hazırlık)
# ============================================================================

class RequestAccept(BaseModel):
    """
    Driver tarafından request kabul etme
    Requirements: 8.2, 8.3
    """
    shuttle_id: int = Field(..., description="Shuttle ID", gt=0)
    
    class Config:
        json_schema_extra = {
            "example": {
                "shuttle_id": 1
            }
        }


class RequestComplete(BaseModel):
    """
    Driver tarafından request tamamlama
    Requirements: 8.5, 8.6
    """
    completion_location_id: int = Field(..., description="Tamamlama lokasyonu ID", gt=0)
    
    class Config:
        json_schema_extra = {
            "example": {
                "completion_location_id": 2
            }
        }


class RequestStatusUpdate(BaseModel):
    """
    Request durum güncelleme (Admin için)
    """
    status: RequestStatus = Field(..., description="Yeni durum")
    cancelled_by: Optional[str] = Field(None, description="İptal eden")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "CANCELLED",
                "cancelled_by": "admin"
            }
        }


# ============================================================================
# List ve Filter Schemas
# ============================================================================

class RequestListResponse(BaseModel):
    """
    Request listesi response
    """
    total: int
    items: list[RequestResponse]
    
    class Config:
        json_schema_extra = {
            "example": {
                "total": 10,
                "items": []
            }
        }
