"""
Buggy Call - Models Package
"""
from app import db
from datetime import datetime
import pytz
import os


def get_current_timestamp():
    """
    Get current UTC timestamp (timezone-aware, then converted to naive)
    
    IMPORTANT: All timestamps in the database are stored in UTC.
    Frontend should handle timezone conversion for display.
    
    Returns:
        datetime: Current UTC timestamp (naive datetime)
    """
    # Always use UTC for database storage (best practice for production)
    return datetime.now(pytz.UTC).replace(tzinfo=None)


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
