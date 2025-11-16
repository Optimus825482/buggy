"""
ShuttleDriver association table
"""
from datetime import datetime
from sqlalchemy import Column, Integer, Boolean, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from app.models.base import Base


class ShuttleDriver(Base):
    """
    Shuttle-Driver ilişki tablosu
    Hangi sürücünün hangi shuttle'a atandığını tutar
    """
    __tablename__ = "shuttle_drivers"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # İlişkiler
    shuttle_id = Column(
        Integer,
        ForeignKey("shuttles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Shuttle ID"
    )
    driver_id = Column(
        Integer,
        ForeignKey("system_users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Sürücü ID"
    )
    
    # Durum
    is_primary = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
        comment="Birincil sürücü mü?"
    )
    is_active = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
        index=True,
        comment="Aktif mi?"
    )
    
    # Zaman bilgileri
    assigned_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        server_default="now()",
        comment="Atanma zamanı"
    )
    last_active_at = Column(DateTime, comment="Son aktif olma zamanı")
    
    # İlişkiler
    shuttle = relationship("Shuttle", back_populates="driver_assignments")
    driver = relationship("SystemUser", back_populates="shuttle_assignments")
    
    # Unique constraint: Bir shuttle'a aynı driver birden fazla kez atanamaz
    __table_args__ = (
        UniqueConstraint('shuttle_id', 'driver_id', name='uq_shuttle_driver'),
    )
    
    def __repr__(self) -> str:
        return f"<ShuttleDriver(shuttle_id={self.shuttle_id}, driver_id={self.driver_id}, active={self.is_active})>"
