"""
Buggy Call - Notification Log Model
Tracks notification delivery status and metrics
"""
from app import db
from app.models import BaseModel, get_current_timestamp
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime


class NotificationLog(db.Model, BaseModel):
    """Log for notification delivery tracking"""
    
    __tablename__ = 'notification_logs'
    
    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign Keys
    user_id = Column(Integer, ForeignKey('system_users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Notification Information
    notification_type = Column(String(50), nullable=False, index=True)
    priority = Column(String(20), default='normal', index=True)
    title = Column(String(200), nullable=False)
    body = Column(Text)
    
    # Delivery Status
    status = Column(String(20), nullable=False, index=True)  # sent, delivered, failed, clicked
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    
    # Timestamps
    sent_at = Column(DateTime, default=get_current_timestamp, nullable=False, index=True)
    delivered_at = Column(DateTime)
    clicked_at = Column(DateTime)
    
    # Relationships
    user = relationship('SystemUser', backref='notification_logs')
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_notification_status_sent_at', 'status', 'sent_at'),
        Index('idx_notification_type_priority', 'notification_type', 'priority'),
    )
    
    def __repr__(self):
        return f'<NotificationLog {self.id}: {self.notification_type} to {self.user_id} - {self.status}>'
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'notification_type': self.notification_type,
            'priority': self.priority,
            'title': self.title,
            'body': self.body,
            'status': self.status,
            'error_message': self.error_message,
            'retry_count': self.retry_count,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'delivered_at': self.delivered_at.isoformat() if self.delivered_at else None,
            'clicked_at': self.clicked_at.isoformat() if self.clicked_at else None
        }
