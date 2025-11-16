"""
User Pydantic schemas
Kullanıcı işlemleri için schema'lar
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, validator


# =============================================================================
# FCM Token Schemas (Görev 9.3)
# =============================================================================

class FCMTokenUpdate(BaseModel):
    """
    Driver FCM token güncelleme
    Requirements: 7.1, 7.2
    """
    fcm_token: str = Field(..., description="Firebase Cloud Messaging token", min_length=10)
    
    class Config:
        json_schema_extra = {
            "example": {
                "fcm_token": "dGhpcyBpcyBhIGZha2UgdG9rZW4gZm9yIGV4YW1wbGU="
            }
        }


class FCMTokenResponse(BaseModel):
    """
    FCM token güncelleme response
    """
    success: bool
    message: str
    fcm_token: Optional[str] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "FCM token güncellendi",
                "fcm_token": "dGhpcyBpcyBhIGZha2UgdG9rZW4=",
                "updated_at": "2024-11-16T10:30:00Z"
            }
        }


# =============================================================================
# User Management Schemas (Görev 11.1 için hazırlık)
# =============================================================================

class UserBase(BaseModel):
    """Base user schema"""
    username: str = Field(..., min_length=3, max_length=50)
    full_name: str = Field(..., min_length=1, max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    role: str = Field(..., description="admin veya driver")
    
    @validator('role')
    def validate_role(cls, v):
        """Rol kontrolü"""
        if v not in ['admin', 'driver']:
            raise ValueError('Rol admin veya driver olmalı')
        return v


class UserCreate(UserBase):
    """
    Yeni kullanıcı oluşturma
    Requirements: 9.4
    """
    password: str = Field(..., min_length=8, description="Şifre (min 8 karakter)")
    hotel_id: int = Field(..., gt=0, description="Otel ID")
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "driver1",
                "full_name": "Mehmet Yılmaz",
                "email": "mehmet@example.com",
                "phone": "+905551234567",
                "role": "driver",
                "password": "SecurePass123",
                "hotel_id": 1
            }
        }


class UserUpdate(BaseModel):
    """
    Kullanıcı güncelleme
    Requirements: 9.4
    """
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "full_name": "Mehmet Yılmaz",
                "email": "mehmet.new@example.com",
                "phone": "+905559876543",
                "is_active": True
            }
        }


class UserResponse(BaseModel):
    """
    Kullanıcı response
    Requirements: 9.4
    """
    id: int
    hotel_id: int
    username: str
    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    role: str
    is_active: bool
    must_change_password: bool
    fcm_token: Optional[str] = None
    fcm_token_date: Optional[datetime] = None
    created_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "hotel_id": 1,
                "username": "driver1",
                "full_name": "Mehmet Yılmaz",
                "email": "mehmet@example.com",
                "phone": "+905551234567",
                "role": "driver",
                "is_active": True,
                "must_change_password": False,
                "fcm_token": "dGhpcyBpcyBhIGZha2UgdG9rZW4=",
                "fcm_token_date": "2024-11-16T10:30:00Z",
                "created_at": "2024-11-16T10:00:00Z",
                "last_login": "2024-11-16T10:30:00Z"
            }
        }


class UserListResponse(BaseModel):
    """
    Kullanıcı listesi response
    """
    total: int
    items: list[UserResponse]
    
    class Config:
        json_schema_extra = {
            "example": {
                "total": 10,
                "items": []
            }
        }
