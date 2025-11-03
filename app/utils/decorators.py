"""
Buggy Call - Utility Decorators
"""
from functools import wraps
from flask import session, jsonify, request
from marshmallow import ValidationError


def require_role(*roles):
    """
    Decorator to require specific user roles
    
    Usage:
        @require_role('admin')
        def admin_only_function():
            ...
        
        @require_role('admin', 'driver')
        def admin_or_driver_function():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'role' not in session:
                return jsonify({'error': 'Unauthorized - Login required'}), 401
            
            user_role = session.get('role')
            if user_role not in roles:
                return jsonify({'error': 'Forbidden - Insufficient permissions'}), 403
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def require_login(f):
    """
    Decorator to require user login
    
    Usage:
        @require_login
        def protected_function():
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized - Login required'}), 401
        return f(*args, **kwargs)
    
    return decorated_function


def validate_schema(schema_class, location='json'):
    """
    Decorator to validate request data with Marshmallow schema
    
    Args:
        schema_class: Marshmallow schema class to use for validation
        location: Where to get data from ('json', 'form', 'args')
    
    Usage:
        @validate_schema(LocationCreateSchema)
        def create_location():
            data = request.validated_data
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get data based on location
            if location == 'json':
                data = request.get_json() or {}
            elif location == 'form':
                data = request.form.to_dict()
            elif location == 'args':
                data = request.args.to_dict()
            else:
                data = {}
            
            # Validate data
            schema = schema_class()
            try:
                validated_data = schema.load(data)
                # Attach validated data to request object
                request.validated_data = validated_data
            except ValidationError as err:
                return jsonify({
                    'error': 'Validation failed',
                    'errors': err.messages
                }), 400
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def handle_errors(f):
    """
    Decorator to handle common errors
    
    Usage:
        @handle_errors
        def some_function():
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValidationError as e:
            return jsonify({
                'error': 'Validation failed',
                'errors': e.messages
            }), 400
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except PermissionError as e:
            return jsonify({'error': str(e)}), 403
        except FileNotFoundError as e:
            return jsonify({'error': 'Resource not found'}), 404
        except Exception as e:
            # Log the error
            print(f"Unexpected error: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500
    
    return decorated_function
