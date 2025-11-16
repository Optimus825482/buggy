"""
Authentication Schemas
Login, token ve kullanıcı bilgileri için Pydantic modelleri
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, validator


# =============================================================================
# Login Schemas
# =============================================================================

class LoginRequest(BaseModel):
    """
    Login isteği için schema
    
    Example:
        {
            "username": "admin1",
            "password": "SecurePass123"
        }
    """
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="Kullanıcı adı",
        example="admin1"
    )
    password: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="Şifre",
        example="SecurePass123"
    )
    
    @validator('username')
    def username_must_be_alphanumeric(cls, v):
        """Kullanıcı adı alfanumerik olmalı"""
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Kullanıcı adı sadece harf, rakam, _ ve - içerebilir')
        return v.lower()  # Küçük harfe çevir
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "admin1",
                "password": "SecurePass123"
            }
        }


class TokenResponse(BaseModel):
    """
    Token response schema
    
    Example:
        {
            "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
            "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
            "token_type": "bearer"
        }
    """
    access_token: str = Field(
        ...,
        description="JWT access token (1 saat geçerli)",
        example="eyJ0eXAiOiJKV1QiLCJhbGc..."
    )
    refresh_token: str = Field(
        ...,
        description="JWT refresh token (30 gün geçerli)",
        example="eyJ0eXAiOiJKV1QiLCJhbGc..."
    )
    token_type: str = Field(
        default="bearer",
        description="Token tipi",
        example="bearer"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
                "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
                "token_type": "bearer"
            }
        }


class UserResponse(BaseModel):
    """
    Kullanıcı bilgileri response schema
    
    Example:
        {
            "id": 1,
            "username": "admin1",
            "full_name": "Admin User",
            "email": "admin@hotel.com",
            "phone": "+90 555 123 4567",
            "role": "admin",
            "hotel_id": 1,
            "is_active": true,
            "must_change_password": false,
            "last_login": "2024-01-15T10:30:00",
            "created_at": "2024-01-01T00:00:00"
        }
    """
    id: int = Field(..., description="Kullanıcı ID", example=1)
    username: str = Field(..., description="Kullanıcı adı", example="admin1")
    full_name: str = Field(..., description="Ad Soyad", example="Admin User")
    email: Optional[str] = Field(None, description="E-posta", example="admin@hotel.com")
    phone: Optional[str] = Field(None, description="Telefon", example="+90 555 123 4567")
    role: str = Field(..., description="Kullanıcı rolü", example="admin")
    hotel_id: int = Field(..., description="Otel ID", example=1)
    is_active: bool = Field(..., description="Aktif mi?", example=True)
    must_change_password: bool = Field(
        ...,
        description="Şifre değiştirmeli mi?",
        example=False
    )
    last_login: Optional[datetime] = Field(
        None,
        description="Son giriş zamanı",
        example="2024-01-15T10:30:00"
    )
    created_at: datetime = Field(
        ...,
        description="Oluşturulma zamanı",
        example="2024-01-01T00:00:00"
    )
    
    class Config:
        from_attributes = True  # SQLAlchemy modellerinden otomatik dönüşüm
        json_schema_extra = {
            "example": {
                "id": 1,
                "username": "admin1",
                "full_name": "Admin User",
                "email": "admin@hotel.com",
                "phone": "+90 555 123 4567",
                "role": "admin",
                "hotel_id": 1,
                "is_active": True,
                "must_change_password": False,
                "last_login": "2024-01-15T10:30:00",
                "created_at": "2024-01-01T00:00:00"
            }
        }


class LoginResponse(BaseModel):
    """
    Login response schema (token + user bilgileri)
    
    Example:
        {
            "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
            "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
            "token_type": "bearer",
            "user": {
                "id": 1,
                "username": "admin1",
                "full_name": "Admin User",
                "role": "admin",
                "hotel_id": 1
            }
        }
    """
    access_token: str = Field(
        ...,
        description="JWT access token",
        example="eyJ0eXAiOiJKV1QiLCJhbGc..."
    )
    refresh_token: str = Field(
        ...,
        description="JWT refresh token",
        example="eyJ0eXAiOiJKV1QiLCJhbGc..."
    )
    token_type: str = Field(
        default="bearer",
        description="Token tipi",
        example="bearer"
    )
    user: UserResponse = Field(
        ...,
        description="Kullanıcı bilgileri"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
                "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
                "token_type": "bearer",
                "user": {
                    "id": 1,
                    "username": "admin1",
                    "full_name": "Admin User",
                    "email": "admin@hotel.com",
                    "role": "admin",
                    "hotel_id": 1,
                    "is_active": True,
                    "must_change_password": False
                }
            }
        }


# =============================================================================
# Token Refresh Schemas
# =============================================================================

class RefreshTokenRequest(BaseModel):
    """
    Token yenileme isteği schema
    
    Example:
        {
            "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
        }
    """
    refresh_token: str = Field(
        ...,
        description="JWT refresh token",
        example="eyJ0eXAiOiJKV1QiLCJhbGc..."
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
            }
        }


# =============================================================================
# Password Change Schemas
# =============================================================================

class ChangePasswordRequest(BaseModel):
    """
    Şifre değiştirme isteği schema
    
    Example:
        {
            "current_password": "OldPass123",
            "new_password": "NewSecurePass456",
            "confirm_password": "NewSecurePass456"
        }
    """
    current_password: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="Mevcut şifre",
        example="OldPass123"
    )
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Yeni şifre (en az 8 karakter)",
        example="NewSecurePass456"
    )
    confirm_password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Yeni şifre tekrar",
        example="NewSecurePass456"
    )
    
    @validator('new_password')
    def validate_password_strength(cls, v):
        """Şifre güvenlik kontrolü"""
        if len(v) < 8:
            raise ValueError('Şifre en az 8 karakter olmalıdır')
        
        if not any(c.isalpha() for c in v):
            raise ValueError('Şifre en az bir harf içermelidir')
        
        if not any(c.isdigit() for c in v):
            raise ValueError('Şifre en az bir rakam içermelidir')
        
        return v
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        """Şifrelerin eşleşmesi kontrolü"""
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Şifreler eşleşmiyor')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "current_password": "OldPass123",
                "new_password": "NewSecurePass456",
                "confirm_password": "NewSecurePass456"
            }
        }


# =============================================================================
# Common Response Schemas
# =============================================================================

class MessageResponse(BaseModel):
    """
    Basit mesaj response schema
    
    Example:
        {
            "message": "İşlem başarılı"
        }
    """
    message: str = Field(
        ...,
        description="İşlem sonucu mesajı",
        example="İşlem başarılı"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "İşlem başarılı"
            }
        }


class ErrorResponse(BaseModel):
    """
    Hata response schema
    
    Example:
        {
            "detail": "Kullanıcı adı veya şifre hatalı"
        }
    """
    detail: str = Field(
        ...,
        description="Hata mesajı",
        example="Kullanıcı adı veya şifre hatalı"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "detail": "Kullanıcı adı veya şifre hatalı"
            }
        }
