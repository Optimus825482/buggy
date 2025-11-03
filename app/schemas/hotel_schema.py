"""
Buggy Call - Hotel Schema
"""
from marshmallow import Schema, fields, validate, validates, ValidationError


class HotelSchema(Schema):
    """Hotel validation schema"""
    
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    code = fields.Str(validate=validate.Length(min=2, max=50))
    address = fields.Str(allow_none=True)
    phone = fields.Str(allow_none=True, validate=validate.Length(max=50))
    email = fields.Email(allow_none=True)
    logo = fields.Str(allow_none=True, validate=validate.Length(max=500))
    timezone = fields.Str(validate=validate.Length(max=50))
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    
    class Meta:
        ordered = True


class HotelCreateSchema(Schema):
    """Schema for creating a new hotel"""
    
    name = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    code = fields.Str(required=True, validate=validate.Length(min=2, max=50))
    address = fields.Str(allow_none=True)
    phone = fields.Str(allow_none=True, validate=validate.Length(max=50))
    email = fields.Email(allow_none=True)
    timezone = fields.Str(missing='Europe/Istanbul', validate=validate.Length(max=50))


class HotelUpdateSchema(Schema):
    """Schema for updating hotel information"""
    
    name = fields.Str(validate=validate.Length(min=1, max=255))
    address = fields.Str(allow_none=True)
    phone = fields.Str(allow_none=True, validate=validate.Length(max=50))
    email = fields.Email(allow_none=True)
    logo = fields.Str(allow_none=True, validate=validate.Length(max=500))
    timezone = fields.Str(validate=validate.Length(max=50))
