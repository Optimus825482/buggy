"""
Location model
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class Location(BaseModel):
    """
    Lokasyon modeli
    QR kod ile erişilebilen konumları tutar
    """
    __tablename__ = "locations"
    
    # İlişkiler
    hotel_id = Column(
        Integer,
        ForeignKey("hotels.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Otel ID"
    )
    
    # Temel bilgiler
    name = Column(String(255), nullable=False, comment="Lokasyon adı")
    description = Column(Text, comment="Açıklama")
    
    # QR kod
    qr_code_data = Column(
        String(500),
        unique=True,
        nullable=False,
        index=True,
        comment="QR kod verisi"
    )
    qr_code_image = Column(Text, comment="QR kod görseli (base64)")
    
    # Görsel
    location_image = Column(Text, comment="Lokasyon görseli")
    
    # Sıralama
    display_order = Column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
        index=True,
        comment="Görüntüleme sırası"
    )
    
    # Koordinatlar (opsiyonel)
    latitude = Column(Numeric(10, 8), comment="Enlem")
    longitude = Column(Numeric(11, 8), comment="Boylam")
    
    # Durum
    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
        index=True,
        comment="Aktif mi?"
    )
    
    # İlişkiler
    hotel = relationship("Hotel", back_populates="locations")
    requests = relationship(
        "ShuttleRequest",
        back_populates="location",
        foreign_keys="ShuttleRequest.location_id"
    )
    completion_requests = relationship(
        "ShuttleRequest",
        back_populates="completion_location",
        foreign_keys="ShuttleRequest.completion_location_id"
    )
    shuttles_at_location = relationship(
        "Shuttle",
        back_populates="current_location"
    )
    
    def __repr__(self) -> str:
        return f"<Location(id={self.id}, name='{self.name}', qr_code='{self.qr_code_data}')>"
