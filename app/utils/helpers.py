"""
Buggy Call - Helper Functions
"""
from flask import session, jsonify
from app.models.user import SystemUser
from app.models.hotel import Hotel


class RequestContext:
    """Helper class for request context"""
    
    @staticmethod
    def get_current_user():
        """Get current logged-in user"""
        user_id = session.get('user_id')
        if user_id:
            return SystemUser.query.get(user_id)
        return None
    
    @staticmethod
    def get_current_user_id():
        """Get current user ID"""
        return session.get('user_id')
    
    @staticmethod
    def get_current_hotel():
        """Get current user's hotel"""
        user = RequestContext.get_current_user()
        if user:
            return user.hotel
        return None
    
    @staticmethod
    def get_current_hotel_id():
        """Get current user's hotel ID"""
        user = RequestContext.get_current_user()
        if user:
            return user.hotel_id
        return None
    
    @staticmethod
    def get_current_role():
        """Get current user's role"""
        return session.get('role')
    
    @staticmethod
    def is_admin():
        """Check if current user is admin"""
        return session.get('role') == 'admin'
    
    @staticmethod
    def is_driver():
        """Check if current user is driver"""
        return session.get('role') == 'driver'


class APIResponse:
    """Helper class for standardized API responses"""
    
    @staticmethod
    def success(data=None, message=None, status=200):
        """Return success response"""
        response = {'success': True}
        if message:
            response['message'] = message
        if data is not None:
            response['data'] = data
        return jsonify(response), status
    
    @staticmethod
    def error(message, status=400, errors=None):
        """Return error response"""
        response = {
            'success': False,
            'error': message
        }
        if errors:
            response['errors'] = errors
        return jsonify(response), status
    
    @staticmethod
    def created(data, message='Resource created successfully'):
        """Return created response"""
        return APIResponse.success(data=data, message=message, status=201)
    
    @staticmethod
    def not_found(message='Resource not found'):
        """Return not found response"""
        return APIResponse.error(message=message, status=404)
    
    @staticmethod
    def unauthorized(message='Unauthorized'):
        """Return unauthorized response"""
        return APIResponse.error(message=message, status=401)
    
    @staticmethod
    def forbidden(message='Forbidden'):
        """Return forbidden response"""
        return APIResponse.error(message=message, status=403)
    
    @staticmethod
    def validation_error(errors):
        """Return validation error response"""
        return APIResponse.error(
            message='Validation failed',
            status=400,
            errors=errors
        )


class Pagination:
    """Helper class for pagination"""
    
    @staticmethod
    def paginate(query, page=1, per_page=20, max_per_page=100):
        """
        Paginate a SQLAlchemy query
        
        Args:
            query: SQLAlchemy query object
            page: Page number (1-indexed)
            per_page: Items per page
            max_per_page: Maximum items per page
        
        Returns:
            Dictionary with items, total, page, per_page, pages
        """
        # Validate and limit per_page
        per_page = min(per_page, max_per_page)
        
        # Get total count
        total = query.count()
        
        # Get items for current page
        items = query.limit(per_page).offset((page - 1) * per_page).all()
        
        # Calculate total pages
        pages = (total + per_page - 1) // per_page if total > 0 else 1
        
        return {
            'items': [item.to_dict() if hasattr(item, 'to_dict') else item for item in items],
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': pages,
            'has_prev': page > 1,
            'has_next': page < pages
        }


def generate_unique_code(prefix='', length=8):
    """Generate a unique code"""
    import uuid
    code = uuid.uuid4().hex[:length].upper()
    return f"{prefix}{code}" if prefix else code
