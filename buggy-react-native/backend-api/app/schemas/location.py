"""
Location schemas
Lokasyon CRUD işlemleri için Pydantic modelleri
"""
from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
from decimal import Decimal


class LocationBase(BaseModel):
    """Location base schema - ortak alanlar"""
    name: str = Field(..., min_length=1, max_length=255, description="Lokasyon adı")
    description: Optional[str] = Field(None, description="Lokasyon açıklaması")
    display_order: int = Field(default=0, ge=0, description="Görüntüleme sırası")
    latitude: Optional[Decimal] = Field(None, description="Enlem koordinatı")
    longitude: Optional[Decimal] = Field(None, description="Boylam koordinatı")
    is_active: bool = Field(default=True, description="Aktif durumu")
    
    @validator('latitude')
    def validate_latitude(cls, v):
        """Enlem validasyonu (-90 ile 90 arası)"""
        if v is not None and (v < -90 or v > 90):
            raise ValueError('Enlem -90 ile 90 arasında olmalıdır')
        return v
    
    @validator('longitude')
    def validate_longitude(cls, v):
        """Boylam validasyonu (-180 ile 180 arası)"""
        if v is not None and (v < -180 or v > 180):
            raise ValueError('Boylam -180 ile 180 arasında olmalıdır')
        return v


class LocationCreate(LocationBase):
    """Location oluşturma schema"""
    hotel_id: int = Field(..., gt=0, description="Otel ID")
    qr_code_data: Optional[str] = Field(
        None,
        max_length=500,
        description="QR kod verisi (boş bırakılırsa otomatik oluşturulur)"
    )
    location_image: Optional[str] = Field(None, description="Lokasyon görseli (base64)")


class LocationUpdate(BaseModel):
    """Location güncelleme schema - tüm alanlar opsiyonel"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    display_order: Optional[int] = Field(None, ge=0)
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    is_active: Optional[bool] = None
    location_image: Optional[str] = None
    
    @validator('latitude')
    def validate_latitude(cls, v):
        """Enlem validasyonu"""
        if v is not None and (v < -90 or v > 90):
            raise ValueError('Enlem -90 ile 90 arasında olmalıdır')
        return v
    
    @validator('longitude')
    def validate_longitude(cls, v):
        """Boylam validasyonu"""
        if v is not None and (v < -180 or v > 180):
            raise ValueError('Boylam -180 ile 180 arasında olmalıdır')
        return v


class LocationResponse(LocationBase):
    """Location response schema"""
    id: int
    hotel_id: int
    qr_code_data: str
    qr_code_image: Optional[str] = None
    location_image: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True  # Pydantic v2 için (eskiden orm_mode)


class QRCodeResponse(BaseModel):
    """QR kod response schema"""
    qr_code_data: str = Field(..., description="QR kod verisi")
    qr_code_image: str = Field(..., description="QR kod görseli (base64 PNG)")
    
    class Config:
        from_attributes = True


class LocationListResponse(BaseModel):
    """Location listesi response schema"""
    total: int = Field(..., description="Toplam lokasyon sayısı")
    items: list[LocationResponse] = Field(..., description="Lokasyon listesi")
