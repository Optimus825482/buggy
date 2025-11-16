"""
Shuttle model
"""
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
from app.models.enums import ShuttleStatus


class Shuttle(BaseModel):
    """
    Shuttle modeli
    Otel içi ulaşım araçlarını tutar
    """
    __tablename__ = "shuttles"
    
    # İlişkiler
    hotel_id = Column(
        Integer,
        ForeignKey("hotels.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Otel ID"
    )
    current_location_id = Column(
        Integer,
        ForeignKey("locations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Mevcut lokasyon ID"
    )
    
    # Temel bilgiler
    code = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        comment="Shuttle kodu (örn: B01)"
    )
    model = Column(String(100), comment="Model")
    license_plate = Column(String(50), comment="Plaka")
    icon = Column(String(10), comment="İkon emoji")
    
    # Durum
    status = Column(
        String(20),
        nullable=False,
        default=ShuttleStatus.AVAILABLE.value,
        server_default=ShuttleStatus.AVAILABLE.value,
        index=True,
        comment="Shuttle durumu (available/busy/offline)"
    )
    
    # İlişkiler
    hotel = relationship("Hotel", back_populates="shuttles")
    current_location = relationship("Location", back_populates="shuttles_at_location")
    driver_assignments = relationship(
        "ShuttleDriver",
        back_populates="shuttle",
        cascade="all, delete-orphan"
    )
    requests = relationship("ShuttleRequest", back_populates="shuttle")
    
    def __repr__(self) -> str:
        return f"<Shuttle(id={self.id}, code='{self.code}', status='{self.status}')>"
    
    def is_available(self) -> bool:
        """Müsait mi kontrol et"""
        return self.status == ShuttleStatus.AVAILABLE.value
    
    def is_busy(self) -> bool:
        """Meşgul mu kontrol et"""
        return self.status == ShuttleStatus.BUSY.value
