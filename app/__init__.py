"""
Buggy Call - Flask Application Factory
"""
from flask import Flask, render_template, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_socketio import SocketIO
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect
from flask_caching import Cache
# Flask-Session removed - using Flask's built-in session
import os
import logging
from logging.handlers import RotatingFileHandler

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
socketio = SocketIO()
# Rate limiter completely removed for high-traffic hotel environments
csrf = CSRFProtect()
cache = Cache()


def connect_with_retry(app, max_retries=5, delay=2):
    """
    Connect to database with exponential backoff retry logic
    
    Args:
        app: Flask application instance
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        
    Returns:
        bool: True if connection successful
        
    Raises:
        Exception: If connection fails after all retries
    """
    import time
    from sqlalchemy import text
    
    for attempt in range(max_retries):
        try:
            with app.app_context():
                db.session.execute(text('SELECT 1'))
                app.logger.info("✅ Database connection successful")
                return True
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = delay * (2 ** attempt)
                app.logger.warning(
                    f"Database connection failed (attempt {attempt + 1}/{max_retries}), "
                    f"retrying in {wait_time}s... Error: {str(e)}"
                )
                time.sleep(wait_time)
            else:
                app.logger.error(
                    f"❌ Database connection failed after {max_retries} attempts: {str(e)}"
                )
                raise


def create_app(config_name=None):
    """Application factory pattern"""
    
    # Create Flask app
    # Use root templates folder (not app/templates)
    import os
    template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')
    static_dir = os.path.join(os.path.dirname(__file__), 'static')
    
    app = Flask(__name__, 
                template_folder=template_dir,
                static_folder=static_dir)
    
    # Load configuration
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    from app.config import get_config
    app.config.from_object(get_config(config_name))
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    
    # Rate limiter completely removed
    
    # Initialize CSRF protection
    # Note: API blueprints (api_bp, auth_bp, health_bp) are explicitly exempted
    # because they use JSON and JWT/session authentication
    csrf.init_app(app)
    
    # Configure CSRF to work with JSON requests
    app.config['WTF_CSRF_CHECK_DEFAULT'] = True
    app.config['WTF_CSRF_METHODS'] = ['POST', 'PUT', 'PATCH', 'DELETE']
    app.config['WTF_CSRF_HEADERS'] = ['X-CSRFToken', 'X-CSRF-Token']
    
    # Initialize cache
    cache.init_app(app, config={
        'CACHE_TYPE': 'redis' if app.config.get('REDIS_URL') else 'simple',
        'CACHE_REDIS_URL': app.config.get('REDIS_URL'),
        'CACHE_DEFAULT_TIMEOUT': 300
    })
    
    # Session - Flask's built-in session kullanılıyor
    # sess.init_app(app)  # Flask-Session kaldırıldı
    
    # Import all models to ensure proper initialization
    with app.app_context():
        from app.models.hotel import Hotel
        from app.models.user import SystemUser
        from app.models.location import Location
        from app.models.buggy import Buggy
        from app.models.buggy_driver import BuggyDriver  # New association table
        from app.models.request import BuggyRequest
        from app.models.audit import AuditTrail
        from app.models.session import Session
        from app.models.notification_log import NotificationLog  # Notification tracking
    
    # Initialize CORS
    CORS(app, 
         origins=app.config['CORS_ORIGINS'],
         supports_credentials=True)
    
    # Initialize SocketIO (skip during migrations)
    if not os.getenv('SKIP_SOCKETIO'):
        # Use threading mode in testing to prevent blocking
        socketio.init_app(app,
                         cors_allowed_origins=app.config['SOCKETIO_CORS_ALLOWED_ORIGINS'],
                         async_mode='threading' if app.config['TESTING'] else app.config['SOCKETIO_ASYNC_MODE'],
                         message_queue=app.config['SOCKETIO_MESSAGE_QUEUE'])
    
    # Setup logging
    setup_logging(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Register error handlers
    register_error_handlers(app)

    # Register suspicious activity detection (disabled in testing)
    if not app.config['TESTING']:
        from app.middleware.suspicious_activity import detect_suspicious_activity
        detect_suspicious_activity(app)
    
    # Apply security headers
    apply_security_headers(app)
    
    # Register context processors
    register_context_processors(app)
    
    # Create upload folders
    create_upload_folders(app)
    
    # Register shell context
    register_shell_context(app)
    
    # Initialize background jobs (skip during migrations and testing)
    if not os.getenv('SKIP_BACKGROUND_JOBS') and not app.config['TESTING']:
        try:
            from app.services.background_jobs import BackgroundJobsService
            BackgroundJobsService.init_scheduler(app)
            app.logger.info("✅ Background jobs initialized")
        except Exception as e:
            app.logger.error(f"❌ Failed to initialize background jobs: {e}")
    
    return app


def setup_logging(app):
    """Setup comprehensive logging configuration"""
    
    # Set log level
    log_level = getattr(logging, app.config.get('LOG_LEVEL', 'INFO'))
    app.logger.setLevel(log_level)
    
    # Structured logging format
    log_format = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s: %(message)s [in %(pathname)s:%(lineno)d]',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    if not app.debug and not app.testing:
        # Create logs directory if it doesn't exist
        try:
            if not os.path.exists('logs'):
                os.makedirs('logs', mode=0o755, exist_ok=True)
        except Exception as e:
            # If we can't create logs dir, just use console
            app.logger.warning(f"Could not create logs directory: {e}")
        
        # Setup file handler
        try:
            file_handler = RotatingFileHandler(
                app.config['LOG_FILE'],
                maxBytes=app.config['LOG_MAX_BYTES'],
                backupCount=app.config['LOG_BACKUP_COUNT']
            )
            file_handler.setFormatter(log_format)
            file_handler.setLevel(log_level)
            app.logger.addHandler(file_handler)
        except Exception as e:
            app.logger.warning(f"Could not setup file logging: {e}")
    
    # Always add console handler for Railway logs
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_format)
    console_handler.setLevel(log_level)
    app.logger.addHandler(console_handler)
    
    # Log startup info
    app.logger.info('='*60)
    app.logger.info(f'Buggy Call starting - Environment: {app.config.get("FLASK_ENV")}')
    app.logger.info(f'Debug mode: {app.config.get("DEBUG")}')
    app.logger.info(f'Database: {app.config.get("SQLALCHEMY_DATABASE_URI", "").split("@")[-1] if "@" in app.config.get("SQLALCHEMY_DATABASE_URI", "") else "Not configured"}')
    app.logger.info('='*60)
    
    # Add request logging middleware
    @app.before_request
    def log_request():
        """Log all HTTP requests"""
        from flask import request
        if not request.path.startswith('/static'):
            app.logger.debug(f'{request.method} {request.path} - {request.remote_addr}')
    
    @app.after_request
    def log_response(response):
        """Log HTTP responses"""
        from flask import request
        if not request.path.startswith('/static'):
            app.logger.debug(f'{request.method} {request.path} - {response.status_code}')
        return response


def register_blueprints(app):
    """Register Flask blueprints"""
    from app.routes.auth import auth_bp
    from app.routes.admin import admin_bp
    from app.routes.driver import driver_bp
    from app.routes.guest import guest_bp
    from app.routes.api import api_bp
    from app.routes.reports import reports_bp
    from app.routes.health import health_bp
    from app.routes.audit import audit_bp
    from app.routes.setup import setup_bp
    from app.routes.system_reset import system_reset_bp
    from app.routes.system_admin import system_admin_bp
    from app.routes.test import test_bp
    from app.routes.admin_notification_api import admin_notification_api
    from app.routes.map_api import map_api
    from app.routes.sse import sse_bp
    from app.routes.guest_notification_api import guest_notification_api_bp
    from app.routes.fcm_api import fcm_api

    app.register_blueprint(setup_bp)  # No prefix, setup routes at root level
    app.register_blueprint(system_reset_bp)  # No prefix, system reset at root level
    app.register_blueprint(system_admin_bp)  # No prefix, system admin at root level
    
    # Exempt setup, system reset, system admin, and map API from CSRF
    csrf.exempt(setup_bp)
    csrf.exempt(system_reset_bp)
    csrf.exempt(system_admin_bp)
    csrf.exempt(map_api)  # Map API uses GET requests for thumbnails
    csrf.exempt(guest_notification_api_bp)  # Guest notification API
    csrf.exempt(fcm_api)  # FCM API uses JWT authentication
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(driver_bp, url_prefix='/driver')
    app.register_blueprint(guest_bp, url_prefix='/guest')
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(reports_bp, url_prefix='/api/reports')
    app.register_blueprint(audit_bp, url_prefix='/api')
    app.register_blueprint(admin_notification_api)  # Admin notification monitoring
    app.register_blueprint(map_api)  # Map thumbnail generation
    app.register_blueprint(guest_notification_api_bp, url_prefix='/api')  # Guest notification API
    app.register_blueprint(fcm_api)  # FCM Token Management API
    app.register_blueprint(health_bp)  # No prefix for health endpoints
    app.register_blueprint(sse_bp, url_prefix='/sse')  # SSE for real-time notifications
    
    # Test routes (sadece development'ta)
    if app.config.get('DEBUG'):
        app.register_blueprint(test_bp)
        csrf.exempt(test_bp)
    
    # Register home route
    @app.route('/')
    def index():
        from flask import redirect, url_for, session
        # Redirect to appropriate dashboard based on user role
        if 'user_id' in session:
            if session.get('role') == 'admin':
                return redirect(url_for('admin.dashboard'))
            elif session.get('role') == 'driver':
                return redirect(url_for('driver.dashboard'))
        # Default to login page
        return redirect(url_for('auth.login'))
    
    # Favicon route (for browsers that request /favicon.ico)
    @app.route('/favicon.ico')
    def favicon():
        from flask import send_from_directory
        import os
        return send_from_directory(
            os.path.join(app.root_path, 'static'),
            'favicon.ico',
            mimetype='image/vnd.microsoft.icon'
        )
    
    # Register service worker routes
    @app.route('/sw.js')
    def service_worker():
        from flask import send_from_directory
        return send_from_directory(app.static_folder, 'sw.js', mimetype='application/javascript')
    
    @app.route('/firebase-messaging-sw.js')
    def firebase_service_worker():
        from flask import send_from_directory
        return send_from_directory(app.static_folder, 'firebase-messaging-sw.js', mimetype='application/javascript')

    # Register offline page route
    @app.route('/offline.html')
    def offline():
        from flask import render_template
        return render_template('offline.html')
    
    # Register WebSocket events
    from app.websocket import events


def register_error_handlers(app):
    """Register error handlers"""
    from app.utils.exceptions import BuggyCallException
    
    @app.errorhandler(BuggyCallException)
    def handle_buggy_call_exception(error):
        """Handle custom exceptions"""
        return jsonify(error.to_dict()), error.status_code
    
    @app.errorhandler(404)
    def not_found_error(error):
        """Handle not found errors"""
        from flask import request
        app.logger.warning(f'404 Not Found: {request.method} {request.path}')
        
        if app.config['DEBUG']:
            return jsonify({'error': 'Not found', 'path': request.path}), 404
        
        try:
            return render_template('errors/404.html'), 404
        except:
            return jsonify({'error': 'Not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle internal server errors with logging"""
        db.session.rollback()
        
        # Log error with full stack trace
        import traceback
        app.logger.error('='*60)
        app.logger.error('Internal Server Error')
        app.logger.error(f'Error: {str(error)}')
        app.logger.error('Stack trace:')
        app.logger.error(traceback.format_exc())
        app.logger.error('='*60)
        
        if app.config['DEBUG']:
            return jsonify({
                'error': 'Internal server error',
                'details': str(error),
                'traceback': traceback.format_exc()
            }), 500
        
        # Production: Don't expose error details
        try:
            return render_template('errors/500.html'), 500
        except:
            # Fallback if template rendering fails
            return jsonify({
                'error': 'Internal server error',
                'message': 'An unexpected error occurred. Please try again later.'
            }), 500
    
    @app.errorhandler(403)
    def forbidden_error(error):
        return jsonify({'error': 'Forbidden'}), 403
    
    @app.errorhandler(401)
    def unauthorized_error(error):
        return jsonify({'error': 'Unauthorized'}), 401
    
    # Rate limiter disabled - no 429 handler needed
    # @app.errorhandler(429)
    # def ratelimit_handler(error):
    #     """Handle rate limit exceeded"""
    #     from flask import request
    #     app.logger.warning(
    #         f'Rate limit exceeded: {request.remote_addr} - '
    #         f'{request.method} {request.path}'
    #     )
    #     
    #     return jsonify({
    #         'error': 'Rate limit exceeded',
    #         'message': 'Too many requests. Please try again later.',
    #         'retry_after': '60 seconds'
    #     }), 429
    
    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        """Catch-all handler for unexpected errors"""
        import traceback
        
        # Log the error
        app.logger.error('='*60)
        app.logger.error('Unexpected Error')
        app.logger.error(f'Error type: {type(error).__name__}')
        app.logger.error(f'Error: {str(error)}')
        app.logger.error('Stack trace:')
        app.logger.error(traceback.format_exc())
        app.logger.error('='*60)
        
        # Rollback database session
        try:
            db.session.rollback()
        except:
            pass
        
        if app.config['DEBUG']:
            return jsonify({
                'error': 'Unexpected error',
                'type': type(error).__name__,
                'details': str(error),
                'traceback': traceback.format_exc()
            }), 500
        
        # Production: Generic error message
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred. Please try again later.'
        }), 500


def apply_security_headers(app):
    """Apply security headers to all responses"""
    
    @app.after_request
    def set_security_headers(response):
        """Set security headers on all responses"""
        
        # Get security headers from config
        security_headers = app.config.get('SECURITY_HEADERS', {})
        
        for header, value in security_headers.items():
            response.headers[header] = value
        
        # Force HTTPS in production
        if not app.config.get('DEBUG') and not app.config.get('TESTING'):
            # Enforce HTTPS
            if app.config.get('SESSION_COOKIE_SECURE'):
                response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        return response


def register_context_processors(app):
    """Register template context processors"""
    
    @app.context_processor
    def inject_config():
        return {
            'app_name': app.config['APP_NAME'],
            'theme_colors': app.config['THEME_COLORS']
        }


def create_upload_folders(app):
    """
    Create upload folders if they don't exist
    Handles errors gracefully for production environments
    """
    folders = [
        app.config['UPLOAD_FOLDER'],
        app.config['QR_CODE_FOLDER']
    ]
    
    for folder in folders:
        try:
            if not os.path.exists(folder):
                os.makedirs(folder, mode=0o755, exist_ok=True)
                app.logger.info(f"✅ Created upload folder: {folder}")
            else:
                app.logger.debug(f"Upload folder exists: {folder}")
        except Exception as e:
            app.logger.error(f"❌ Failed to create upload folder {folder}: {e}")
            # Don't raise - app can still function without uploads
            pass


def register_shell_context(app):
    """Register shell context objects"""
    
    @app.shell_context_processor
    def make_shell_context():
        from app.models.hotel import Hotel
        from app.models.user import SystemUser
        from app.models.location import Location
        from app.models.buggy import Buggy
        from app.models.request import BuggyRequest
        from app.models.audit import AuditTrail
        from app.models.session import Session
        
        return {
            'db': db,
            'Hotel': Hotel,
            'SystemUser': SystemUser,
            'Location': Location,
            'Buggy': Buggy,
            'BuggyRequest': BuggyRequest,
            'AuditTrail': AuditTrail,
            'Session': Session
        }
