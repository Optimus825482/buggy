"""
Buggy Call - WSGI Entry Point for Production
Handles Railway deployment - migrations run via start command
"""
import os
import logging
import sys

# Configure logging for startup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

logger.info("="*60)
logger.info("🚀 Buggy Call - Starting Application")
logger.info("="*60)

try:
    from app import create_app, socketio
    
    # Create app with production config
    logger.info("⏳ Creating Flask application...")
    app = create_app('production')
    
    # Initialize production configuration
    from app.config import ProductionConfig
    logger.info("⏳ Initializing production configuration...")
    ProductionConfig.init_app(app)
    
    logger.info("✅ Application initialized successfully")
    logger.info(f"   Environment: {os.getenv('FLASK_ENV', 'production')}")
    logger.info(f"   Async mode: {app.config.get('SOCKETIO_ASYNC_MODE', 'gevent')}")
    logger.info(f"   Port: {os.getenv('PORT', '5000')}")
    logger.info("="*60)
    
except Exception as e:
    logger.error("="*60)
    logger.error("❌ FATAL: Application initialization failed")
    logger.error(f"   Error: {str(e)}")
    logger.error("="*60)
    import traceback
    traceback.print_exc()
    sys.exit(1)

if __name__ == "__main__":
    # This is for local testing only
    # Railway will use gunicorn with gevent worker
    logger.info("Running in local mode with SocketIO...")
    socketio.run(app, host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
