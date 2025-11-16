"""
AuditTrail model
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, BigInteger
from sqlalchemy.orm import relationship
from app.models.base import Base


class AuditTrail(Base):
    """
    Audit trail modeli
    Sistem üzerindeki tüm önemli işlemleri loglar
    """
    __tablename__ = "audit_trail"
    
    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    
    # İlişkiler
    hotel_id = Column(
        Integer,
        ForeignKey("hotels.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Otel ID"
    )
    user_id = Column(
        Integer,
        ForeignKey("system_users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="İşlemi yapan kullanıcı ID"
    )
    
    # İşlem bilgileri
    action = Column(
        String(100),
        nullable=False,
        index=True,
        comment="İşlem tipi (create/update/delete/login/logout)"
    )
    entity_type = Column(
        String(50),
        nullable=False,
        comment="Etkilenen entity tipi (user/location/shuttle/request)"
    )
    entity_id = Column(Integer, comment="Etkilenen entity ID")
    
    # Değişiklik detayları
    old_values = Column(Text, comment="Eski değerler (JSON)")
    new_values = Column(Text, comment="Yeni değerler (JSON)")
    
    # İstek bilgileri
    ip_address = Column(String(45), comment="IP adresi")
    user_agent = Column(Text, comment="User agent")
    
    # Zaman
    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        server_default="now()",
        index=True,
        comment="İşlem zamanı"
    )
    
    # İlişkiler
    hotel = relationship("Hotel", back_populates="audit_logs")
    user = relationship("SystemUser", back_populates="audit_logs")
    
    def __repr__(self) -> str:
        return f"<AuditTrail(id={self.id}, action='{self.action}', entity='{self.entity_type}')>"
