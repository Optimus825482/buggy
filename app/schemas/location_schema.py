"""
Buggy Call - Location Schema
"""
from marshmallow import Schema, fields, validate, validates, ValidationError
from decimal import Decimal


class LocationSchema(Schema):
    """Location validation schema"""
    
    id = fields.Int(dump_only=True)
    hotel_id = fields.Int(required=True)
    name = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    description = fields.Str(allow_none=True)
    qr_code_data = fields.Str(dump_only=True)
    qr_code_image = fields.Str(dump_only=True)
    display_order = fields.Int(missing=0)
    latitude = fields.Decimal(places=8, allow_none=True)
    longitude = fields.Decimal(places=8, allow_none=True)
    is_active = fields.Bool(missing=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    
    @validates('latitude')
    def validate_latitude(self, value):
        """Validate latitude range"""
        if value is not None:
            if value < Decimal('-90') or value > Decimal('90'):
                raise ValidationError('Latitude must be between -90 and 90')
    
    @validates('longitude')
    def validate_longitude(self, value):
        """Validate longitude range"""
        if value is not None:
            if value < Decimal('-180') or value > Decimal('180'):
                raise ValidationError('Longitude must be between -180 and 180')
    
    class Meta:
        ordered = True


class LocationCreateSchema(Schema):
    """Schema for creating a new location"""
    
    hotel_id = fields.Int(required=True)
    name = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    description = fields.Str(allow_none=True)
    display_order = fields.Int(missing=0)
    latitude = fields.Decimal(places=8, allow_none=True)
    longitude = fields.Decimal(places=8, allow_none=True)
    is_active = fields.Bool(missing=True)


class LocationUpdateSchema(Schema):
    """Schema for updating location information"""
    
    name = fields.Str(validate=validate.Length(min=1, max=255))
    description = fields.Str(allow_none=True)
    display_order = fields.Int()
    latitude = fields.Decimal(places=8, allow_none=True)
    longitude = fields.Decimal(places=8, allow_none=True)
    is_active = fields.Bool()
