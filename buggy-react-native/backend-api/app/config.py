"""
Uygulama yapılandırma ayarları
Pydantic Settings ile environment variables yönetimi
"""
from pydantic_settings import BaseSettings
from pydantic import Field, validator
from typing import Optional
import os


class Settings(BaseSettings):
    """
    Uygulama ayarları
    Environment variables'dan otomatik yüklenir
    """
    
    # Uygulama Ayarları
    APP_NAME: str = "Shuttle Call API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False, description="Debug modu")
    ENVIRONMENT: str = Field(default="development", description="Ortam: development, staging, production")
    
    # Server Ayarları
    HOST: str = Field(default="0.0.0.0", description="Server host")
    PORT: int = Field(default=8000, description="Server port")
    
    # Database Ayarları
    DATABASE_URL: str = Field(
        ...,  # Required field
        description="PostgreSQL bağlantı URL'i (postgresql://user:pass@host:port/dbname)"
    )
    DB_POOL_SIZE: int = Field(default=20, description="Connection pool boyutu")
    DB_MAX_OVERFLOW: int = Field(default=40, description="Maksimum overflow connection")
    
    # JWT Ayarları
    JWT_SECRET_KEY: str = Field(
        ...,  # Required field
        description="JWT token için secret key (güçlü bir key kullan!)"
    )
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT algoritması")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60, description="Access token süresi (dakika)")
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=30, description="Refresh token süresi (gün)")
    
    # Firebase Cloud Messaging (FCM) Ayarları
    FIREBASE_SERVICE_ACCOUNT_BASE64: str = Field(
        ...,  # Required field
        description="Firebase service account JSON (base64 encoded)"
    )
    
    # CORS Ayarları
    CORS_ORIGINS: list[str] = Field(
        default=[
            "http://localhost:19006",
            "http://localhost:8081",
            "exp://localhost:19000",
        ],
        description="İzin verilen origin'ler"
    )
    
    # Security Ayarları
    BCRYPT_ROUNDS: int = Field(default=12, description="Bcrypt salt rounds")
    RATE_LIMIT_PER_MINUTE: int = Field(default=100, description="Dakika başına maksimum istek")
    
    # Logging Ayarları
    LOG_LEVEL: str = Field(default="INFO", description="Log seviyesi")
    
    @validator("DATABASE_URL")
    def validate_database_url(cls, v):
        """Database URL formatını kontrol et"""
        if not v.startswith("postgresql://") and not v.startswith("postgresql+psycopg2://"):
            raise ValueError("DATABASE_URL postgresql:// ile başlamalı")
        return v
    
    @validator("JWT_SECRET_KEY")
    def validate_jwt_secret(cls, v):
        """JWT secret key güvenliğini kontrol et"""
        if len(v) < 32:
            raise ValueError("JWT_SECRET_KEY en az 32 karakter olmalı")
        return v
    
    @validator("FIREBASE_SERVICE_ACCOUNT_BASE64")
    def validate_firebase_base64(cls, v):
        """Firebase credentials base64 formatını kontrol et"""
        import base64
        try:
            # Base64 decode test
            decoded = base64.b64decode(v)
            # JSON parse test
            import json
            json.loads(decoded)
            return v
        except Exception as e:
            raise ValueError(f"FIREBASE_SERVICE_ACCOUNT_BASE64 geçersiz format: {e}")
    
    @validator("ENVIRONMENT")
    def validate_environment(cls, v):
        """Environment değerini kontrol et"""
        allowed = ["development", "staging", "production"]
        if v not in allowed:
            raise ValueError(f"ENVIRONMENT {allowed} değerlerinden biri olmalı")
        return v
    
    @property
    def is_production(self) -> bool:
        """Production ortamında mı?"""
        return self.ENVIRONMENT == "production"
    
    @property
    def is_development(self) -> bool:
        """Development ortamında mı?"""
        return self.ENVIRONMENT == "development"
    
    def get_firebase_credentials_dict(self) -> dict:
        """
        Firebase credentials'ı base64'ten decode edip dict olarak döndür
        
        Returns:
            dict: Firebase service account credentials
        """
        import base64
        import json
        
        try:
            decoded = base64.b64decode(self.FIREBASE_SERVICE_ACCOUNT_BASE64)
            return json.loads(decoded)
        except Exception as e:
            raise ValueError(f"Firebase credentials decode hatası: {e}")
    
    class Config:
        """Pydantic config"""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Settings instance'ı döndür (singleton pattern)
    
    Returns:
        Settings: Uygulama ayarları
        
    Example:
        from app.config import get_settings
        
        settings = get_settings()
        print(settings.DATABASE_URL)
    """
    global settings
    
    if settings is None:
        try:
            settings = Settings()
        except Exception as e:
            raise RuntimeError(f"Ayarlar yüklenemedi: {e}")
    
    return settings


def reload_settings():
    """
    Settings'i yeniden yükle
    Test veya runtime config değişikliği için kullanılır
    """
    global settings
    settings = None
    return get_settings()
