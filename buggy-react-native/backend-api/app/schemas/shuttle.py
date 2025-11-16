"""
Shuttle schemas
Shuttle CRUD işlemleri için Pydantic modelleri
"""
from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
from app.models.enums import ShuttleStatus


class ShuttleBase(BaseModel):
    """Shuttle base schema - ortak alanlar"""
    code: str = Field(..., min_length=1, max_length=50, description="Shuttle kodu (örn: B01)")
    model: Optional[str] = Field(None, max_length=100, description="Shuttle modeli")
    license_plate: Optional[str] = Field(None, max_length=50, description="Plaka numarası")
    icon: Optional[str] = Field(None, max_length=10, description="İkon emoji (örn: 🚗)")
    
    @validator('code')
    def validate_code(cls, v):
        """Kod validasyonu - büyük harf ve rakam"""
        if v:
            v = v.strip().upper()
            if not v:
                raise ValueError('Shuttle kodu boş olamaz')
        return v


class ShuttleCreate(ShuttleBase):
    """Shuttle oluşturma schema"""
    hotel_id: int = Field(..., gt=0, description="Otel ID")
    current_location_id: Optional[int] = Field(None, gt=0, description="Başlangıç lokasyon ID")
    status: ShuttleStatus = Field(
        default=ShuttleStatus.AVAILABLE,
        description="Başlangıç durumu"
    )


class ShuttleUpdate(BaseModel):
    """Shuttle güncelleme schema - tüm alanlar opsiyonel"""
    code: Optional[str] = Field(None, min_length=1, max_length=50)
    model: Optional[str] = Field(None, max_length=100)
    license_plate: Optional[str] = Field(None, max_length=50)
    icon: Optional[str] = Field(None, max_length=10)
    current_location_id: Optional[int] = Field(None, gt=0)
    
    @validator('code')
    def validate_code(cls, v):
        """Kod validasyonu"""
        if v:
            v = v.strip().upper()
            if not v:
                raise ValueError('Shuttle kodu boş olamaz')
        return v


class ShuttleStatusUpdate(BaseModel):
    """Shuttle durum güncelleme schema"""
    status: ShuttleStatus = Field(..., description="Yeni durum (available/busy/offline)")
    current_location_id: Optional[int] = Field(
        None,
        gt=0,
        description="Mevcut lokasyon ID (opsiyonel)"
    )


class ShuttleLocationUpdate(BaseModel):
    """Shuttle lokasyon güncelleme schema"""
    current_location_id: int = Field(..., gt=0, description="Yeni lokasyon ID")


class ShuttleResponse(ShuttleBase):
    """Shuttle response schema"""
    id: int
    hotel_id: int
    current_location_id: Optional[int] = None
    status: str
    created_at: datetime
    updated_at: datetime
    
    # İlişkili veriler (opsiyonel)
    current_location_name: Optional[str] = Field(None, description="Mevcut lokasyon adı")
    active_driver_count: Optional[int] = Field(None, description="Aktif sürücü sayısı")
    
    class Config:
        from_attributes = True  # Pydantic v2 için


class ShuttleDetailResponse(ShuttleResponse):
    """Shuttle detay response schema - ilişkili verilerle"""
    hotel_name: Optional[str] = None
    current_location_name: Optional[str] = None
    active_drivers: Optional[list[dict]] = Field(
        default_factory=list,
        description="Aktif sürücü listesi"
    )


class ShuttleListResponse(BaseModel):
    """Shuttle listesi response schema"""
    total: int = Field(..., description="Toplam shuttle sayısı")
    items: list[ShuttleResponse] = Field(..., description="Shuttle listesi")


class DriverAssignment(BaseModel):
    """Sürücü atama schema"""
    driver_id: int = Field(..., gt=0, description="Sürücü ID")
    is_primary: bool = Field(default=False, description="Ana sürücü mü?")
    is_active: bool = Field(default=True, description="Aktif mi?")


class DriverAssignmentResponse(BaseModel):
    """Sürücü atama response schema"""
    shuttle_id: int
    driver_id: int
    driver_name: str
    is_primary: bool
    is_active: bool
    assigned_at: datetime
    last_active_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
