"""
Buggy Call - User Schema
"""
from marshmallow import Schema, fields, validate, validates, ValidationError, validates_schema
import re


class SystemUserSchema(Schema):
    """System user validation schema"""
    
    id = fields.Int(dump_only=True)
    hotel_id = fields.Int(required=True)
    username = fields.Str(required=True, validate=validate.Length(min=3, max=50))
    role = fields.Str(required=True, validate=validate.OneOf(['admin', 'driver']))
    full_name = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    email = fields.Email(allow_none=True)
    phone = fields.Str(allow_none=True, validate=validate.Length(max=50))
    is_active = fields.Bool(missing=True)
    created_at = fields.DateTime(dump_only=True)
    last_login = fields.DateTime(dump_only=True)
    
    class Meta:
        ordered = True


class UserCreateSchema(Schema):
    """Schema for creating a new user"""
    
    hotel_id = fields.Int(required=True)
    username = fields.Str(required=True, validate=validate.Length(min=3, max=50))
    password = fields.Str(required=True, validate=validate.Length(min=8))
    password_confirm = fields.Str(required=True)
    role = fields.Str(required=True, validate=validate.OneOf(['admin', 'driver']))
    full_name = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    email = fields.Email(allow_none=True)
    phone = fields.Str(allow_none=True, validate=validate.Length(max=50))
    
    @validates('password')
    def validate_password(self, value):
        """Validate password complexity"""
        if len(value) < 8:
            raise ValidationError('Şifre en az 8 karakter olmalıdır')
        if not re.search(r'[A-Z]', value):
            raise ValidationError('Şifre en az 1 büyük harf içermelidir')
        if not re.search(r'[a-z]', value):
            raise ValidationError('Şifre en az 1 küçük harf içermelidir')
        if not re.search(r'\d', value):
            raise ValidationError('Şifre en az 1 rakam içermelidir')
    
    @validates_schema
    def validate_passwords_match(self, data, **kwargs):
        """Validate that passwords match"""
        if data.get('password') != data.get('password_confirm'):
            raise ValidationError('Şifreler eşleşmiyor', 'password_confirm')


class UserUpdateSchema(Schema):
    """Schema for updating user information"""
    
    full_name = fields.Str(validate=validate.Length(min=1, max=255))
    email = fields.Email(allow_none=True)
    phone = fields.Str(allow_none=True, validate=validate.Length(max=50))
    is_active = fields.Bool()


class UserLoginSchema(Schema):
    """Schema for user login"""
    
    username = fields.Str(required=True, validate=validate.Length(min=3, max=50))
    password = fields.Str(required=True, validate=validate.Length(min=1))


class PasswordChangeSchema(Schema):
    """Schema for changing password"""
    
    current_password = fields.Str(required=True)
    new_password = fields.Str(required=True, validate=validate.Length(min=8))
    new_password_confirm = fields.Str(required=True)
    
    @validates('new_password')
    def validate_password(self, value):
        """Validate password complexity"""
        if len(value) < 8:
            raise ValidationError('Şifre en az 8 karakter olmalıdır')
        if not re.search(r'[A-Z]', value):
            raise ValidationError('Şifre en az 1 büyük harf içermelidir')
        if not re.search(r'[a-z]', value):
            raise ValidationError('Şifre en az 1 küçük harf içermelidir')
        if not re.search(r'\d', value):
            raise ValidationError('Şifre en az 1 rakam içermelidir')
    
    @validates_schema
    def validate_passwords_match(self, data, **kwargs):
        """Validate that passwords match"""
        if data.get('new_password') != data.get('new_password_confirm'):
            raise ValidationError('Şifreler eşleşmiyor', 'new_password_confirm')
