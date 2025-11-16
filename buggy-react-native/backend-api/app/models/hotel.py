"""
Hotel model
"""
from sqlalchemy import Column, String, Text
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class Hotel(BaseModel):
    """
    Hotel modeli
    Otel bilgilerini tutar
    """
    __tablename__ = "hotels"
    
    # Temel bilgiler
    name = Column(String(255), nullable=False, comment="Otel adı")
    code = Column(String(50), unique=True, index=True, comment="Otel kodu")
    
    # İletişim bilgileri
    address = Column(Text, comment="Adres")
    phone = Column(String(50), comment="Telefon")
    email = Column(String(255), comment="E-posta")
    
    # Görsel
    logo = Column(String(500), comment="Logo URL")
    
    # Timezone
    timezone = Column(
        String(50),
        nullable=False,
        default="Europe/Istanbul",
        server_default="Europe/Istanbul",
        comment="Otel timezone"
    )
    
    # İlişkiler
    users = relationship("SystemUser", back_populates="hotel", cascade="all, delete-orphan")
    locations = relationship("Location", back_populates="hotel", cascade="all, delete-orphan")
    shuttles = relationship("Shuttle", back_populates="hotel", cascade="all, delete-orphan")
    requests = relationship("ShuttleRequest", back_populates="hotel", cascade="all, delete-orphan")
    audit_logs = relationship("AuditTrail", back_populates="hotel", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Hotel(id={self.id}, name='{self.name}', code='{self.code}')>"
