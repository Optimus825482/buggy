"""
Buggy Call - WSGI Entry Point for Production
Handles Railway deployment with automatic database initialization
"""
import os
import logging
from app import create_app, socketio

# Configure logging for startup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

# Create app with production config
app = create_app('production')

# Initialize production configuration
from app.config import ProductionConfig
ProductionConfig.init_app(app)

# Initialize database on startup (Railway deployment)
if os.getenv('RAILWAY_ENVIRONMENT'):
    logger.info("Railway environment detected, initializing database...")
    try:
        from scripts.railway_init import initialize_railway_database
        with app.app_context():
            initialize_railway_database(app)
    except Exception as e:
        logger.error(f"Failed to initialize Railway database: {e}")
        # Don't raise - let health check handle it
        pass
else:
    logger.info("Non-Railway environment, skipping automatic initialization")

if __name__ == "__main__":
    # This is for local testing only
    # Railway will use gunicorn
    socketio.run(app, host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
