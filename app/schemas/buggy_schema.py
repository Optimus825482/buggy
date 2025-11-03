"""
Buggy Call - Buggy Schema
"""
from marshmallow import Schema, fields, validate


class BuggySchema(Schema):
    """Buggy validation schema"""
    
    id = fields.Int(dump_only=True)
    hotel_id = fields.Int(required=True)
    driver_id = fields.Int(allow_none=True)
    name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    plate_number = fields.Str(allow_none=True, validate=validate.Length(max=50))
    model = fields.Str(allow_none=True, validate=validate.Length(max=100))
    capacity = fields.Int(missing=4, validate=validate.Range(min=1, max=20))
    status = fields.Str(validate=validate.OneOf(['available', 'busy', 'offline']))
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    
    # Nested fields
    driver = fields.Nested('SystemUserSchema', dump_only=True, exclude=('password_hash',))
    
    class Meta:
        ordered = True


class BuggyCreateSchema(Schema):
    """Schema for creating a new buggy"""
    
    hotel_id = fields.Int(required=True)
    driver_id = fields.Int(allow_none=True)
    name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    plate_number = fields.Str(allow_none=True, validate=validate.Length(max=50))
    model = fields.Str(allow_none=True, validate=validate.Length(max=100))
    capacity = fields.Int(missing=4, validate=validate.Range(min=1, max=20))
    status = fields.Str(missing='offline', validate=validate.OneOf(['available', 'busy', 'offline']))


class BuggyUpdateSchema(Schema):
    """Schema for updating buggy information"""
    
    driver_id = fields.Int(allow_none=True)
    name = fields.Str(validate=validate.Length(min=1, max=100))
    plate_number = fields.Str(allow_none=True, validate=validate.Length(max=50))
    model = fields.Str(allow_none=True, validate=validate.Length(max=100))
    capacity = fields.Int(validate=validate.Range(min=1, max=20))
    status = fields.Str(validate=validate.OneOf(['available', 'busy', 'offline']))


class BuggyStatusUpdateSchema(Schema):
    """Schema for updating buggy status"""
    
    status = fields.Str(required=True, validate=validate.OneOf(['available', 'busy', 'offline']))
    location_id = fields.Int(allow_none=True)
