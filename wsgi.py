"""
Shuttle Call - WSGI Entry Point for Production
Handles Coolify deployment with Firebase credentials
"""
import os
import logging
import sys
import json

# Configure logging for startup
logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s [%(levelname)s] %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

logger.info("="*60)
logger.info("🚀 Shuttle Call - Starting Application")
logger.info("="*60)

# Firebase Service Account JSON'u environment'tan yükle
if os.getenv('FIREBASE_SERVICE_ACCOUNT_JSON'):
    try:
        logger.info("⏳ Loading Firebase credentials from environment...")
        service_account = json.loads(os.getenv('FIREBASE_SERVICE_ACCOUNT_JSON'))
        
        # JSON dosyasını oluştur
        with open('firebase-service-account.json', 'w') as f:
            json.dump(service_account, f, indent=2)
        
        logger.info("✅ Firebase credentials loaded successfully")
    except Exception as e:
        logger.error(f"❌ Failed to load Firebase credentials: {str(e)}")
else:
    logger.warning("⚠️ FIREBASE_SERVICE_ACCOUNT_JSON not found in environment")

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
    sys.exit(1)

if __name__ == "__main__":
    # This is for local testing only
    # Railway will use gunicorn with gevent worker
    logger.info("Running in local mode with SocketIO...")
    socketio.run(app, host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
