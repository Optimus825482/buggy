"""
Buggy Call - Models Package
"""
from app import db
from datetime import datetime
import pytz


def get_current_timestamp():
    """Get current timestamp in UTC"""
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
