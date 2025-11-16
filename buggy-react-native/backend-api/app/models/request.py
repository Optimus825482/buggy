"""
ShuttleRequest model
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
from app.models.enums import RequestStatus


class ShuttleRequest(BaseModel):
    """
    Shuttle çağrı talebi modeli
    Misafirlerin shuttle çağrılarını tutar
    """
    __tablename__ = "shuttle_requests"
    
    # İlişkiler
    hotel_id = Column(
        Integer,
        ForeignKey("hotels.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Otel ID"
    )
    location_id = Column(
        Integer,
        ForeignKey("locations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Çağrı yapılan lokasyon ID"
    )
    completion_location_id = Column(
        Integer,
        ForeignKey("locations.id", ondelete="SET NULL"),
        nullable=True,
        comment="Tamamlama lokasyonu ID"
    )
    shuttle_id = Column(
        Integer,
        ForeignKey("shuttles.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Atanan shuttle ID"
    )
    accepted_by_id = Column(
        Integer,
        ForeignKey("system_users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Kabul eden sürücü ID"
    )
    
    # Misafir bilgileri
    guest_name = Column(String(255), comment="Misafir adı")
    room_number = Column(String(50), index=True, comment="Oda numarası")
    has_room = Column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
        comment="Oda var mı?"
    )
    phone = Column(String(50), comment="Telefon")
    notes = Column(Text, comment="Notlar")
    
    # Guest FCM token (1 saat geçerli)
    guest_fcm_token = Column(String(500), comment="Misafir FCM token")
    guest_fcm_token_expires_at = Column(DateTime, comment="Token son kullanma tarihi")
    
    # Durum
    status = Column(
        String(20),
        nullable=False,
        default=RequestStatus.PENDING.value,
        server_default=RequestStatus.PENDING.value,
        index=True,
        comment="Talep durumu"
    )
    cancelled_by = Column(String(50), comment="İptal eden (admin/driver/guest)")
    
    # Zaman bilgileri
    requested_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        server_default="now()",
        index=True,
        comment="Talep zamanı"
    )
    accepted_at = Column(DateTime, comment="Kabul zamanı")
    completed_at = Column(DateTime, comment="Tamamlanma zamanı")
    cancelled_at = Column(DateTime, comment="İptal zamanı")
    timeout_at = Column(DateTime, comment="Timeout zamanı")
    
    # Performans metrikleri
    response_time = Column(Integer, comment="Yanıt süresi (saniye)")
    completion_time = Column(Integer, comment="Tamamlanma süresi (saniye)")
    
    # İlişkiler
    hotel = relationship("Hotel", back_populates="requests")
    location = relationship(
        "Location",
        back_populates="requests",
        foreign_keys=[location_id]
    )
    completion_location = relationship(
        "Location",
        back_populates="completion_requests",
        foreign_keys=[completion_location_id]
    )
    shuttle = relationship("Shuttle", back_populates="requests")
    accepted_by = relationship(
        "SystemUser",
        back_populates="accepted_requests",
        foreign_keys=[accepted_by_id]
    )
    
    def __repr__(self) -> str:
        return f"<ShuttleRequest(id={self.id}, status='{self.status}', room='{self.room_number}')>"
    
    def is_pending(self) -> bool:
        """Bekliyor mu kontrol et"""
        return self.status == RequestStatus.PENDING.value
    
    def is_accepted(self) -> bool:
        """Kabul edildi mi kontrol et"""
        return self.status == RequestStatus.ACCEPTED.value
    
    def is_completed(self) -> bool:
        """Tamamlandı mı kontrol et"""
        return self.status == RequestStatus.COMPLETED.value
