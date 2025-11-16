"""
Buggy Call - Models Package
"""
from app import db
from datetime import datetime
import pytz
import os


def get_current_timestamp():
    """
    Get current Cyprus timezone timestamp (timezone-naive for DB storage)
    
    IMPORTANT: All timestamps in the database are stored in Cyprus local time.
    This matches the hotel's operational timezone (Europe/Nicosia - GMT+2/+3).
    
    Returns:
        datetime: Current Cyprus timestamp (naive datetime)
    """
    # ✅ Use Cyprus timezone for database storage (matches hotel operations)
    cyprus_tz = pytz.timezone('Europe/Nicosia')
    cyprus_time = datetime.now(cyprus_tz)
    return cyprus_time.replace(tzinfo=None)


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
