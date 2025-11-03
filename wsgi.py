"""
Buggy Call - WSGI Entry Point for Production
Handles Railway deployment - migrations run via start command
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

logger.info("✅ Application initialized successfully")
logger.info(f"Environment: {os.getenv('FLASK_ENV', 'development')}")
logger.info(f"Async mode: {app.config.get('SOCKETIO_ASYNC_MODE', 'threading')}")

if __name__ == "__main__":
    # This is for local testing only
    # Railway will use gunicorn with gevent worker
    socketio.run(app, host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
