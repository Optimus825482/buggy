"""
Database models package
"""
from app.models.base import Base, TimestampMixin, BaseModel
from app.models.enums import UserRole, ShuttleStatus, RequestStatus
from app.models.hotel import Hotel
from app.models.user import SystemUser
from app.models.location import Location
from app.models.shuttle import Shuttle
from app.models.shuttle_driver import ShuttleDriver
from app.models.request import ShuttleRequest
from app.models.audit import AuditTrail

__all__ = [
    "Base",
    "BaseModel",
    "TimestampMixin",
    "UserRole",
    "ShuttleStatus",
    "RequestStatus",
    "Hotel",
    "SystemUser",
    "Location",
    "Shuttle",
    "ShuttleDriver",
    "ShuttleRequest",
    "AuditTrail",
]
