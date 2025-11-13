"""
Buggy Call - Models Package
"""
from app import db
from datetime import datetime
import pytz
import os


def get_current_timestamp():
    """
    Get current timestamp in configured timezone
    Reads APP_TIMEZONE from environment (default: Europe/Istanbul)
    """
    try:
        timezone_str = os.getenv('APP_TIMEZONE', 'Europe/Istanbul')
        timezone = pytz.timezone(timezone_str)
        return datetime.now(timezone)
    except Exception as e:
        # Fallback to UTC if timezone is invalid
        import logging
        logging.warning(f"Invalid timezone '{timezone_str}', falling back to UTC: {str(e)}")
        return datetime.now(pytz.UTC)


# Base model class
class BaseModel:
    """Base model with common fields"""
    
    def to_dict(self):
        """Convert model to dictionary"""
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                value = value.isoformat()
            result[column.name] = value
        return result
    
    def update(self, **kwargs):
        """Update model attributes"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        return self
