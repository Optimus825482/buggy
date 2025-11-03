"""
Buggy Call - Audit Trail Service
"""
from app import db
from app.models.audit import AuditTrail
from flask import request, session
import json
from datetime import datetime
from functools import wraps


class AuditService:
    """Service for audit trail logging"""
    
    @staticmethod
    def log_action(action, entity_type, entity_id=None, old_values=None, new_values=None, 
                   user_id=None, hotel_id=None):
        """
        Log an action to the audit trail
        
        Args:
            action: Action type (e.g., 'create', 'update', 'delete', 'login', 'logout')
            entity_type: Type of entity (e.g., 'location', 'buggy', 'request', 'user')
            entity_id: ID of the entity
            old_values: Dictionary of old values (for updates)
            new_values: Dictionary of new values (for creates/updates)
            user_id: ID of the user performing the action
            hotel_id: ID of the hotel
        """
        try:
            # Get user_id from session if not provided
            if user_id is None:
                user_id = session.get('user_id')
            
            # Get hotel_id from session if not provided
            if hotel_id is None:
                # Try to get from user's hotel
                from app.models.user import SystemUser
                if user_id:
                    user = SystemUser.query.get(user_id)
                    if user:
                        hotel_id = user.hotel_id
            
            # Create audit trail entry
            audit = AuditTrail(
                hotel_id=hotel_id,
                user_id=user_id,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                old_values=json.dumps(old_values) if old_values else None,
                new_values=json.dumps(new_values) if new_values else None,
                ip_address=request.remote_addr if request else None,
                user_agent=request.user_agent.string if request and request.user_agent else None
            )
            
            db.session.add(audit)
            db.session.commit()
            
            return audit
            
        except Exception as e:
            # Log error but don't fail the main operation
            print(f"Audit logging error: {str(e)}")
            db.session.rollback()
            return None
    
    @staticmethod
    def log_create(entity_type, entity_id, new_values, user_id=None, hotel_id=None):
        """Log a create action"""
        return AuditService.log_action(
            action='create',
            entity_type=entity_type,
            entity_id=entity_id,
            new_values=new_values,
            user_id=user_id,
            hotel_id=hotel_id
        )
    
    @staticmethod
    def log_update(entity_type, entity_id, old_values, new_values, user_id=None, hotel_id=None):
        """Log an update action"""
        return AuditService.log_action(
            action='update',
            entity_type=entity_type,
            entity_id=entity_id,
            old_values=old_values,
            new_values=new_values,
            user_id=user_id,
            hotel_id=hotel_id
        )
    
    @staticmethod
    def log_delete(entity_type, entity_id, old_values, user_id=None, hotel_id=None):
        """Log a delete action"""
        return AuditService.log_action(
            action='delete',
            entity_type=entity_type,
            entity_id=entity_id,
            old_values=old_values,
            user_id=user_id,
            hotel_id=hotel_id
        )
    
    @staticmethod
    def log_login(user_id, hotel_id, success=True):
        """Log a login attempt"""
        return AuditService.log_action(
            action='login_success' if success else 'login_failed',
            entity_type='user',
            entity_id=user_id,
            user_id=user_id,
            hotel_id=hotel_id
        )
    
    @staticmethod
    def log_logout(user_id, hotel_id):
        """Log a logout"""
        return AuditService.log_action(
            action='logout',
            entity_type='user',
            entity_id=user_id,
            user_id=user_id,
            hotel_id=hotel_id
        )
    
    @staticmethod
    def get_audit_trail(hotel_id, filters=None, page=1, per_page=50):
        """
        Get audit trail with filters
        
        Args:
            hotel_id: Hotel ID to filter by
            filters: Dictionary of filters (user_id, action, entity_type, date_from, date_to)
            page: Page number
            per_page: Items per page
        
        Returns:
            Dictionary with items, total, page, pages
        """
        query = AuditTrail.query.filter_by(hotel_id=hotel_id)
        
        if filters:
            if filters.get('user_id'):
                query = query.filter_by(user_id=filters['user_id'])
            
            if filters.get('action'):
                query = query.filter_by(action=filters['action'])
            
            if filters.get('entity_type'):
                query = query.filter_by(entity_type=filters['entity_type'])
            
            if filters.get('date_from'):
                query = query.filter(AuditTrail.created_at >= filters['date_from'])
            
            if filters.get('date_to'):
                query = query.filter(AuditTrail.created_at <= filters['date_to'])
        
        # Order by most recent first
        query = query.order_by(AuditTrail.created_at.desc())
        
        # Paginate
        total = query.count()
        items = query.limit(per_page).offset((page - 1) * per_page).all()
        
        return {
            'items': [item.to_dict() for item in items],
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': (total + per_page - 1) // per_page
        }


def audit_log(entity_type, action='update'):
    """
    Decorator for automatic audit logging
    
    Usage:
        @audit_log('location', 'create')
        def create_location(data):
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Execute the function
            result = f(*args, **kwargs)
            
            # Try to log the action
            try:
                entity_id = None
                new_values = None
                
                # Try to extract entity_id and values from result
                if isinstance(result, dict):
                    entity_id = result.get('id')
                    new_values = result
                elif hasattr(result, 'id'):
                    entity_id = result.id
                    if hasattr(result, 'to_dict'):
                        new_values = result.to_dict()
                
                AuditService.log_action(
                    action=action,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    new_values=new_values
                )
            except Exception as e:
                # Don't fail if audit logging fails
                print(f"Audit logging decorator error: {str(e)}")
            
            return result
        
        return decorated_function
    return decorator
