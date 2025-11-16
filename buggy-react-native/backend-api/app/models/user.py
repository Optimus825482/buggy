"""
SystemUser model
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
from app.models.enums import UserRole


class SystemUser(BaseModel):
    """
    Sistem kullanıcısı modeli (Admin ve Driver)
    Guest kullanıcılar bu tabloda tutulmaz
    """
    __tablename__ = "system_users"
    
    # İlişkiler
    hotel_id = Column(
        Integer,
        ForeignKey("hotels.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Otel ID"
    )
    
    # Kimlik bilgileri
    username = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        comment="Kullanıcı adı"
    )
    password_hash = Column(String(255), nullable=False, comment="Şifre hash")
    
    # Rol
    role = Column(
        String(20),
        nullable=False,
        index=True,
        comment="Kullanıcı rolü (admin/driver)"
    )
    
    # Kişisel bilgiler
    full_name = Column(String(255), nullable=False, comment="Ad Soyad")
    email = Column(String(255), comment="E-posta")
    phone = Column(String(50), comment="Telefon")
    
    # Durum
    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
        index=True,
        comment="Aktif mi?"
    )
    must_change_password = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
        comment="Şifre değiştirmeli mi?"
    )
    
    # FCM Token (Push notification için)
    fcm_token = Column(String(255), index=True, comment="FCM token")
    fcm_token_date = Column(DateTime, comment="FCM token kayıt tarihi")
    
    # Notification tercihleri
    notification_preferences = Column(Text, comment="Bildirim tercihleri (JSON)")
    
    # Son giriş
    last_login = Column(DateTime, comment="Son giriş zamanı")
    
    # İlişkiler
    hotel = relationship("Hotel", back_populates="users")
    shuttle_assignments = relationship(
        "ShuttleDriver",
        back_populates="driver",
        cascade="all, delete-orphan"
    )
    accepted_requests = relationship(
        "ShuttleRequest",
        back_populates="accepted_by",
        foreign_keys="ShuttleRequest.accepted_by_id"
    )
    audit_logs = relationship("AuditTrail", back_populates="user")
    
    def __repr__(self) -> str:
        return f"<SystemUser(id={self.id}, username='{self.username}', role='{self.role}')>"
    
    def is_admin(self) -> bool:
        """Admin mi kontrol et"""
        return self.role == UserRole.ADMIN.value
    
    def is_driver(self) -> bool:
        """Driver mi kontrol et"""
        return self.role == UserRole.DRIVER.value
