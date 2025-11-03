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
import os
import logging
from logging.handlers import RotatingFileHandler

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
socketio = SocketIO()
limiter = Limiter(key_func=get_remote_address)
csrf = CSRFProtect()
cache = Cache()


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
    
    # Initialize rate limiter
    limiter.init_app(app)
    
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
    
    # Initialize CORS
    CORS(app, 
         origins=app.config['CORS_ORIGINS'],
         supports_credentials=True)
    
    # Initialize SocketIO
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
    
    # Register context processors
    register_context_processors(app)
    
    # Create upload folders
    create_upload_folders(app)
    
    # Register shell context
    register_shell_context(app)
    
    return app


def setup_logging(app):
    """Setup logging configuration"""
    if not app.debug and not app.testing:
        # Create logs directory if it doesn't exist
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        # Setup file handler
        file_handler = RotatingFileHandler(
            app.config['LOG_FILE'],
            maxBytes=app.config['LOG_MAX_BYTES'],
            backupCount=app.config['LOG_BACKUP_COUNT']
        )
        
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        
        file_handler.setLevel(getattr(logging, app.config['LOG_LEVEL']))
        app.logger.addHandler(file_handler)
        app.logger.setLevel(getattr(logging, app.config['LOG_LEVEL']))
        app.logger.info('Buggy Call startup')


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

    app.register_blueprint(setup_bp)  # No prefix, setup routes at root level
    app.register_blueprint(system_reset_bp)  # No prefix, system reset at root level
    
    # Exempt setup and system reset from CSRF (they use JSON without CSRF tokens)
    csrf.exempt(setup_bp)
    csrf.exempt(system_reset_bp)
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(driver_bp, url_prefix='/driver')
    app.register_blueprint(guest_bp, url_prefix='/guest')
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(reports_bp, url_prefix='/api/reports')
    app.register_blueprint(audit_bp, url_prefix='/api')
    app.register_blueprint(health_bp)  # No prefix for health endpoints
    
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
    
    # Register service worker route
    @app.route('/sw.js')
    def service_worker():
        from flask import send_from_directory
        return send_from_directory(app.static_folder, 'sw.js', mimetype='application/javascript')

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
        if app.config['DEBUG']:
            return jsonify({'error': 'Not found'}), 404
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        app.logger.error(f'Internal error: {str(error)}')
        if app.config['DEBUG']:
            return jsonify({'error': 'Internal server error', 'details': str(error)}), 500
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(403)
    def forbidden_error(error):
        return jsonify({'error': 'Forbidden'}), 403
    
    @app.errorhandler(401)
    def unauthorized_error(error):
        return jsonify({'error': 'Unauthorized'}), 401
    
    @app.errorhandler(429)
    def ratelimit_handler(error):
        """Handle rate limit exceeded"""
        return jsonify({
            'error': 'Rate limit exceeded',
            'message': 'Too many requests. Please try again later.'
        }), 429


def register_context_processors(app):
    """Register template context processors"""
    
    @app.context_processor
    def inject_config():
        return {
            'app_name': app.config['APP_NAME'],
            'theme_colors': app.config['THEME_COLORS']
        }


def create_upload_folders(app):
    """Create upload folders if they don't exist"""
    folders = [
        app.config['UPLOAD_FOLDER'],
        app.config['QR_CODE_FOLDER']
    ]
    
    for folder in folders:
        if not os.path.exists(folder):
            os.makedirs(folder)


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
