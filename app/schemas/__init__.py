"""
Buggy Call - Schemas Package
"""
from app.schemas.hotel_schema import HotelSchema, HotelCreateSchema, HotelUpdateSchema
from app.schemas.user_schema import (
    SystemUserSchema, UserCreateSchema, UserUpdateSchema,
    UserLoginSchema, PasswordChangeSchema
)
from app.schemas.location_schema import LocationSchema, LocationCreateSchema, LocationUpdateSchema
from app.schemas.buggy_schema import BuggySchema, BuggyCreateSchema, BuggyUpdateSchema, BuggyStatusUpdateSchema
from app.schemas.request_schema import (
    BuggyRequestSchema, BuggyRequestCreateSchema, BuggyRequestAcceptSchema,
    BuggyRequestCompleteSchema, BuggyRequestCancelSchema, BuggyRequestFilterSchema
)

__all__ = [
    'HotelSchema', 'HotelCreateSchema', 'HotelUpdateSchema',
    'SystemUserSchema', 'UserCreateSchema', 'UserUpdateSchema',
    'UserLoginSchema', 'PasswordChangeSchema',
    'LocationSchema', 'LocationCreateSchema', 'LocationUpdateSchema',
    'BuggySchema', 'BuggyCreateSchema', 'BuggyUpdateSchema', 'BuggyStatusUpdateSchema',
    'BuggyRequestSchema', 'BuggyRequestCreateSchema', 'BuggyRequestAcceptSchema',
    'BuggyRequestCompleteSchema', 'BuggyRequestCancelSchema', 'BuggyRequestFilterSchema'
]
