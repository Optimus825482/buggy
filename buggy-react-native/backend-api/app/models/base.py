"""
Base model ve mixin'ler
"""
from datetime import datetime
from typing import Any
from sqlalchemy import Column, Integer, DateTime, func
from sqlalchemy.ext.declarative import declarative_base, declared_attr

Base = declarative_base()


class TimestampMixin:
    """
    Tüm modellere otomatik created_at ve updated_at alanları ekler
    """
    
    @declared_attr
    def created_at(cls):
        """Kayıt oluşturulma zamanı"""
        return Column(
            DateTime,
            nullable=False,
            default=datetime.utcnow,
            server_default=func.now()
        )
    
    @declared_attr
    def updated_at(cls):
        """Kayıt güncellenme zamanı"""
        return Column(
            DateTime,
            nullable=False,
            default=datetime.utcnow,
            onupdate=datetime.utcnow,
            server_default=func.now()
        )


class BaseModel(Base, TimestampMixin):
    """
    Tüm modeller için base class
    - id: Primary key
    - created_at: Oluşturulma zamanı
    - updated_at: Güncellenme zamanı
    """
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    def to_dict(self) -> dict[str, Any]:
        """Model'i dictionary'ye çevir"""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }
    
    def __repr__(self) -> str:
        """String representation"""
        return f"<{self.__class__.__name__}(id={self.id})>"
