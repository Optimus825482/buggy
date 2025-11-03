"""
Buggy Call - Buggy Request Schema
"""
from marshmallow import Schema, fields, validate, validates_schema, ValidationError


class BuggyRequestSchema(Schema):
    """Buggy request validation schema"""
    
    id = fields.Int(dump_only=True)
    hotel_id = fields.Int(required=True)
    location_id = fields.Int(required=True)
    buggy_id = fields.Int(allow_none=True)
    accepted_by_id = fields.Int(allow_none=True)
    guest_name = fields.Str(allow_none=True, validate=validate.Length(max=255))
    room_number = fields.Str(allow_none=True, validate=validate.Length(max=50))
    phone = fields.Str(allow_none=True, validate=validate.Length(max=50))
    has_room = fields.Bool(missing=True)
    guest_device_id = fields.Str(allow_none=True, validate=validate.Length(max=255))
    notes = fields.Str(allow_none=True)
    status = fields.Str(validate=validate.OneOf(['pending', 'accepted', 'completed', 'cancelled']))
    requested_at = fields.DateTime(dump_only=True)
    accepted_at = fields.DateTime(dump_only=True)
    completed_at = fields.DateTime(dump_only=True)
    cancelled_at = fields.DateTime(dump_only=True)
    response_time = fields.Int(dump_only=True)
    completion_time = fields.Int(dump_only=True)
    
    # Nested fields
    location = fields.Nested('LocationSchema', dump_only=True)
    buggy = fields.Nested('BuggySchema', dump_only=True)
    driver = fields.Nested('SystemUserSchema', dump_only=True, exclude=('password_hash',))
    
    class Meta:
        ordered = True


class BuggyRequestCreateSchema(Schema):
    """Schema for creating a new buggy request"""
    
    location_id = fields.Int(required=True)
    guest_name = fields.Str(allow_none=True, validate=validate.Length(max=255))
    room_number = fields.Str(allow_none=True, validate=validate.Length(max=50))
    phone = fields.Str(allow_none=True, validate=validate.Length(max=50))
    has_room = fields.Bool(missing=True)
    notes = fields.Str(allow_none=True)
    
    @validates_schema
    def validate_room_info(self, data, **kwargs):
        """Validate that room number is provided if has_room is True"""
        if data.get('has_room', True) and not data.get('room_number'):
            raise ValidationError('Oda numarası gereklidir', 'room_number')


class BuggyRequestAcceptSchema(Schema):
    """Schema for accepting a buggy request"""
    
    buggy_id = fields.Int(required=True)


class BuggyRequestCompleteSchema(Schema):
    """Schema for completing a buggy request"""
    
    notes = fields.Str(allow_none=True)


class BuggyRequestCancelSchema(Schema):
    """Schema for cancelling a buggy request"""
    
    reason = fields.Str(required=True, validate=validate.Length(min=1, max=500))
    cancelled_by = fields.Int(allow_none=True)


class BuggyRequestFilterSchema(Schema):
    """Schema for filtering buggy requests"""
    
    status = fields.Str(allow_none=True, validate=validate.OneOf(['pending', 'accepted', 'completed', 'cancelled']))
    location_id = fields.Int(allow_none=True)
    buggy_id = fields.Int(allow_none=True)
    date_from = fields.DateTime(allow_none=True)
    date_to = fields.DateTime(allow_none=True)
    page = fields.Int(missing=1, validate=validate.Range(min=1))
    per_page = fields.Int(missing=20, validate=validate.Range(min=1, max=100))
