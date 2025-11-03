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
    SOCKETIO_ASYNC_MODE = 'threading'  # Use threading mode (works without eventlet)
    
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
    SESSION_PERMANENT = True
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    SESSION_COOKIE_SECURE = not DEBUG
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
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
    """Production configuration"""
    DEBUG = False
    TESTING = False
    
    # Override with production-specific settings
    SQLALCHEMY_ECHO = False
    SESSION_COOKIE_SECURE = True
    
    # Stricter rate limits for production
    RATELIMIT_DEFAULT = "50 per hour"


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
