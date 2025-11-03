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
    Comprehensive health check endpoint for Railway monitoring
    
    Returns system health status including:
    - Overall status
    - Database connection and table count
    - Redis connection (if configured)
    - Application status
    - Python version
    - Timestamp
    """
    from flask import current_app
    from sqlalchemy import inspect, text
    
    health_status = {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'environment': current_app.config.get('FLASK_ENV', 'unknown'),
        'python_version': sys.version.split()[0],
        'checks': {}
    }
    
    # Check database connection
    try:
        db.session.execute(text('SELECT 1'))
        
        # Get table count
        inspector = inspect(db.engine)
        table_count = len(inspector.get_table_names())
        
        # Check critical tables
        critical_tables = ['hotel', 'system_user', 'location', 'buggy']
        existing_tables = inspector.get_table_names()
        missing_tables = [t for t in critical_tables if t not in existing_tables]
        
        health_status['checks']['database'] = {
            'status': 'healthy',
            'message': 'Database connection successful',
            'table_count': table_count,
            'critical_tables_ok': len(missing_tables) == 0
        }
        
        if missing_tables:
            health_status['checks']['database']['missing_tables'] = missing_tables
            health_status['checks']['database']['status'] = 'degraded'
            
    except Exception as e:
        health_status['status'] = 'unhealthy'
        health_status['checks']['database'] = {
            'status': 'unhealthy',
            'message': f'Database connection failed: {str(e)}'
        }
    
    # Check Redis connection (if configured)
    try:
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
        # Redis failure is not critical
        health_status['checks']['redis'] = {
            'status': 'unhealthy',
            'message': f'Redis connection failed: {str(e)}'
        }
    
    # Application status check
    try:
        health_status['checks']['application'] = {
            'status': 'healthy',
            'message': 'Application running',
            'debug_mode': current_app.config.get('DEBUG', False)
        }
    except Exception as e:
        health_status['status'] = 'unhealthy'
        health_status['checks']['application'] = {
            'status': 'unhealthy',
            'message': f'Application check failed: {str(e)}'
        }
    
    # Determine HTTP status code
    # 200 = healthy, 503 = unhealthy
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
