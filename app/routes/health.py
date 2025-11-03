"""
Buggy Call - Health Check Routes
"""
from flask import Blueprint, jsonify
from app import db
from datetime import datetime
import sys

health_bp = Blueprint('health', __name__)


@health_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint for monitoring
    
    Returns system health status including:
    - Overall status
    - Database connection
    - Redis connection (if configured)
    - Python version
    - Timestamp
    """
    health_status = {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'python_version': sys.version,
        'checks': {}
    }
    
    # Check database connection
    try:
        from sqlalchemy import text
        db.session.execute(text('SELECT 1'))
        health_status['checks']['database'] = {
            'status': 'healthy',
            'message': 'Database connection successful'
        }
    except Exception as e:
        health_status['status'] = 'unhealthy'
        health_status['checks']['database'] = {
            'status': 'unhealthy',
            'message': f'Database connection failed: {str(e)}'
        }
    
    # Check Redis connection (if configured)
    try:
        from flask import current_app
        redis_url = current_app.config.get('REDIS_URL')
        
        if redis_url:
            import redis
            r = redis.from_url(redis_url)
            r.ping()
            health_status['checks']['redis'] = {
                'status': 'healthy',
                'message': 'Redis connection successful'
            }
        else:
            health_status['checks']['redis'] = {
                'status': 'not_configured',
                'message': 'Redis not configured (using memory cache)'
            }
    except ImportError:
        health_status['checks']['redis'] = {
            'status': 'not_available',
            'message': 'Redis library not installed'
        }
    except Exception as e:
        health_status['checks']['redis'] = {
            'status': 'unhealthy',
            'message': f'Redis connection failed: {str(e)}'
        }
    
    # Determine HTTP status code
    status_code = 200 if health_status['status'] == 'healthy' else 503
    
    return jsonify(health_status), status_code


@health_bp.route('/ping', methods=['GET'])
def ping():
    """Simple ping endpoint"""
    return jsonify({
        'status': 'ok',
        'message': 'pong',
        'timestamp': datetime.utcnow().isoformat()
    }), 200


@health_bp.route('/version', methods=['GET'])
def version():
    """Get application version info"""
    return jsonify({
        'app_name': 'Buggy Call',
        'version': '1.0.0',
        'python_version': sys.version,
        'timestamp': datetime.utcnow().isoformat()
    }), 200
