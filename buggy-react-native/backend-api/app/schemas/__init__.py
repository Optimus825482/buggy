"""
Pydantic Schemas
Request ve response modelleri
"""
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    TokenResponse,
    RefreshTokenRequest,
    ChangePasswordRequest,
    UserResponse
)
from app.schemas.location import (
    LocationCreate,
    LocationUpdate,
    LocationResponse,
    QRCodeResponse,
    LocationListResponse
)
from app.schemas.request import (
    RequestCreate,
    RequestResponse,
    GuestFCMTokenUpdate,
    RequestAccept,
    RequestComplete,
    RequestStatusUpdate,
    RequestListResponse
)
from app.schemas.user import (
    FCMTokenUpdate,
    FCMTokenResponse,
    UserCreate,
    UserUpdate,
    UserResponse as UserDetailResponse,
    UserListResponse
)

__all__ = [
    # Auth schemas
    "LoginRequest",
    "LoginResponse",
    "TokenResponse",
    "RefreshTokenRequest",
    "ChangePasswordRequest",
    "UserResponse",
    # Location schemas
    "LocationCreate",
    "LocationUpdate",
    "LocationResponse",
    "QRCodeResponse",
    "LocationListResponse",
    # Request schemas
    "RequestCreate",
    "RequestResponse",
    "GuestFCMTokenUpdate",
    "RequestAccept",
    "RequestComplete",
    "RequestStatusUpdate",
    "RequestListResponse",
    # User schemas
    "FCMTokenUpdate",
    "FCMTokenResponse",
    "UserCreate",
    "UserUpdate",
    "UserDetailResponse",
    "UserListResponse"
]
