"""
Buggy Call - Configuration Module
Manages all application configuration settings
"""
import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Base configuration class"""
    
    # Flask Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    TESTING = False
    
    # Application Settings
    APP_NAME = os.getenv('APP_NAME', 'Buggy Call')
    APP_TIMEZONE = os.getenv('APP_TIMEZONE', 'Europe/Istanbul')
    BASE_URL = os.getenv('BASE_URL', 'http://localhost:5000')
    
    # Database Configuration - MySQL Only
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = int(os.getenv('DB_PORT', 3306))
    DB_NAME = os.getenv('DB_NAME', 'buggycall')
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = DEBUG
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
        'max_overflow': 20
    }
    
    # JWT Configuration
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(seconds=int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 3600)))
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(seconds=int(os.getenv('JWT_REFRESH_TOKEN_EXPIRES', 2592000)))
    JWT_TOKEN_LOCATION = ['headers']
    JWT_HEADER_NAME = 'Authorization'
    JWT_HEADER_TYPE = 'Bearer'
    
    # CORS Configuration
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:5000').split(',')
    CORS_SUPPORTS_CREDENTIALS = True
    
    # SocketIO Configuration (works without Redis)
    SOCKETIO_MESSAGE_QUEUE = os.getenv('SOCKETIO_MESSAGE_QUEUE', None)  # None = single instance mode
    SOCKETIO_CORS_ALLOWED_ORIGINS = CORS_ORIGINS
    # Auto-detect best async mode: threading for local dev, gevent for production
    SOCKETIO_ASYNC_MODE = os.getenv('SOCKETIO_ASYNC_MODE', 'threading')
    
    # Upload Configuration
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'app', 'static', 'uploads')
    QR_CODE_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'app', 'static', 'qr_codes')
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'svg'}
    
    # QR Code Configuration
    QR_CODE_ERROR_CORRECTION = 'H'  # High error correction
    QR_CODE_BOX_SIZE = 10
    QR_CODE_BORDER = 4
    QR_CODE_FORMAT = 'PNG'
    
    # Push Notification Configuration (VAPID)
    VAPID_PUBLIC_KEY = os.getenv('VAPID_PUBLIC_KEY', '')
    VAPID_PRIVATE_KEY = os.getenv('VAPID_PRIVATE_KEY', '')
    VAPID_CLAIMS_EMAIL = os.getenv('VAPID_CLAIMS_EMAIL', 'mailto:admin@buggycall.com')
    
    # Email Configuration (Optional)
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', '')
    
    # Redis Configuration (Optional for caching - uses memory if not available)
    REDIS_URL = os.getenv('REDIS_URL', None)  # None = use simple cache
    
    # Rate Limiting (uses memory if Redis not available)
    RATELIMIT_STORAGE_URL = os.getenv('RATELIMIT_STORAGE_URL', 'memory://')
    RATELIMIT_ENABLED = True
    RATELIMIT_DEFAULT = "100 per hour"
    
    # Session Configuration
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = False  # Default: session expires on browser close
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)  # Only for admin sessions
    SESSION_COOKIE_SECURE = not DEBUG
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_NAME = 'buggycall_session'  # Custom cookie name
    SESSION_REFRESH_EACH_REQUEST = True  # Refresh session on each request
    
    # Security Headers
    SECURITY_HEADERS = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'SAMEORIGIN',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains'
    }
    
    # Pagination
    ITEMS_PER_PAGE = 20
    MAX_ITEMS_PER_PAGE = 100
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/buggycall.log')
    LOG_MAX_BYTES = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 5
    
    # Theme Colors (from logo)
    THEME_COLORS = {
        'primary': '#1BA5A8',      # Turquoise
        'accent': '#F28C38',       # Orange
        'dark': '#2C3E50',         # Dark Gray
        'light': '#ECF0F1',        # Light Gray
        'white': '#FFFFFF',        # White
        'success': '#27AE60',      # Green
        'danger': '#E74C3C',       # Red
        'warning': '#F39C12',      # Yellow
        'info': '#3498DB'          # Blue
    }


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Production configuration with Railway support"""
    DEBUG = False
    TESTING = False
    
    # Override with production-specific settings
    SQLALCHEMY_ECHO = False
    SESSION_COOKIE_SECURE = True
    
    # Stricter rate limits for production
    RATELIMIT_DEFAULT = "50 per hour"
    
    # Production-specific SQLAlchemy settings
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
        'max_overflow': 5,
        'pool_timeout': 30
    }
    
    # Use gevent for production WebSocket support (works with Python 3.11+)
    SOCKETIO_ASYNC_MODE = 'gevent'
    
    @classmethod
    def init_app(cls, app):
        """Initialize production configuration with Railway support"""
        Config.init_app(app) if hasattr(Config, 'init_app') else None
        
        # Parse Railway MySQL URL if provided
        mysql_url = os.getenv('MYSQL_PUBLIC_URL')
        if mysql_url:
            from urllib.parse import urlparse
            
            try:
                parsed = urlparse(mysql_url)
                
                # Validate parsed components
                if not parsed.hostname:
                    raise ValueError("MySQL hostname is missing from MYSQL_PUBLIC_URL")
                if not parsed.username:
                    raise ValueError("MySQL username is missing from MYSQL_PUBLIC_URL")
                if not parsed.password:
                    raise ValueError("MySQL password is missing from MYSQL_PUBLIC_URL")
                
                # Update database configuration
                app.config['DB_HOST'] = parsed.hostname
                app.config['DB_PORT'] = parsed.port or 3306
                app.config['DB_NAME'] = parsed.path.lstrip('/') or 'railway'
                app.config['DB_USER'] = parsed.username
                app.config['DB_PASSWORD'] = parsed.password
                
                # Rebuild SQLAlchemy URI with PyMySQL driver
                app.config['SQLALCHEMY_DATABASE_URI'] = (
                    f"mysql+pymysql://{parsed.username}:{parsed.password}"
                    f"@{parsed.hostname}:{parsed.port or 3306}"
                    f"/{parsed.path.lstrip('/') or 'railway'}?charset=utf8mb4"
                )
                
                app.logger.info(f"✅ Railway MySQL configured: {parsed.hostname}:{parsed.port or 3306}")
                app.logger.info(f"   Database: {parsed.path.lstrip('/') or 'railway'}")
            except ValueError as e:
                app.logger.error(f"❌ Invalid MYSQL_PUBLIC_URL: {e}")
                app.logger.error(f"   Expected format: mysql://user:pass@host:port/database")
                app.logger.error(f"   Check Railway MySQL service variables")
                raise
            except Exception as e:
                app.logger.error(f"❌ Failed to parse MYSQL_PUBLIC_URL: {e}")
                app.logger.error(f"   URL format may be incorrect")
                raise


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True

    # Use in-memory SQLite for fast testing (no external dependencies)
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

    # SQLite doesn't need connection pooling
    SQLALCHEMY_ENGINE_OPTIONS = {}

    # Disable CSRF for testing
    WTF_CSRF_ENABLED = False

    # Disable rate limiting for testing
    RATELIMIT_ENABLED = False

    # Faster password hashing for tests
    BCRYPT_LOG_ROUNDS = 4

    # Disable SQL echo for cleaner test output
    SQLALCHEMY_ECHO = False


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config(env=None):
    """Get configuration based on environment"""
    if env is None:
        env = os.getenv('FLASK_ENV', 'development')
    return config.get(env, config['default'])
