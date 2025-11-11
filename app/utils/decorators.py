"""
Buggy Call - Custom Decorators
Performans optimize edilmiş decorator'lar
"""
from functools import wraps
from flask import session, redirect, url_for, flash, request, jsonify
from marshmallow import ValidationError
from app import cache
from app.models.user import SystemUser, UserRole


def get_current_user_cached():
    """
    Cache'lenmiş user bilgisi al
    
    Returns:
        SystemUser veya None
    """
    user_id = session.get('user_id')
    if not user_id:
        return None
    
    # Cache'den kontrol et (60 saniye)
    cache_key = f'user_{user_id}'
    user = cache.get(cache_key)
    
    if not user:
        # Cache'de yoksa DB'den çek
        user = SystemUser.query.get(user_id)
        if user:
            # Cache'e kaydet
            cache.set(cache_key, user, timeout=60)
    
    return user


def invalidate_user_cache(user_id):
    """
    User cache'ini temizle (user güncellendiğinde kullan)
    
    Args:
        user_id: User ID
    """
    cache_key = f'user_{user_id}'
    cache.delete(cache_key)


def login_required(fn):
    """Giriş yapmış kullanıcı gerektirir"""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json:
                return jsonify({'error': 'Giriş yapmanız gerekiyor'}), 401
            flash('Lütfen giriş yapın', 'warning')
            return redirect(url_for('auth.login'))
        
        user = get_current_user_cached()
        if not user:
            session.clear()
            if request.is_json:
                return jsonify({'error': 'Kullanıcı bulunamadı'}), 401
            flash('Kullanıcı bulunamadı', 'danger')
            return redirect(url_for('auth.login'))
        
        return fn(*args, **kwargs)
    return wrapper


def admin_required(fn):
    """Admin rolü gerektirir"""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json:
                return jsonify({'error': 'Giriş yapmanız gerekiyor'}), 401
            flash('Lütfen giriş yapın', 'warning')
            return redirect(url_for('auth.login'))
        
        user = get_current_user_cached()  # ✅ Cache'den al
        if not user:
            session.clear()
            if request.is_json:
                return jsonify({'error': 'Kullanıcı bulunamadı'}), 401
            flash('Kullanıcı bulunamadı', 'danger')
            return redirect(url_for('auth.login'))
        
        if user.role != UserRole.ADMIN:
            if request.is_json:
                return jsonify({'error': 'Bu işlem için yetkiniz yok'}), 403
            flash('Bu sayfaya erişim yetkiniz yok', 'danger')
            return redirect(url_for('auth.login'))
        
        return fn(*args, **kwargs)
    return wrapper


def driver_required(fn):
    """Driver rolü gerektirir"""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json:
                return jsonify({'error': 'Giriş yapmanız gerekiyor'}), 401
            flash('Lütfen giriş yapın', 'warning')
            return redirect(url_for('auth.login'))
        
        user = get_current_user_cached()  # ✅ Cache'den al
        if not user:
            session.clear()
            if request.is_json:
                return jsonify({'error': 'Kullanıcı bulunamadı'}), 401
            flash('Kullanıcı bulunamadı', 'danger')
            return redirect(url_for('auth.login'))
        
        if user.role != UserRole.DRIVER:
            if request.is_json:
                return jsonify({'error': 'Bu işlem için yetkiniz yok'}), 403
            flash('Bu sayfaya erişim yetkiniz yok', 'danger')
            return redirect(url_for('auth.login'))
        
        return fn(*args, **kwargs)
    return wrapper


# ============================================================================
# ESKİ DECORATOR'LAR (Geriye Uyumluluk İçin)
# ============================================================================

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
