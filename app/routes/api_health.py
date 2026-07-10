"""
Buggy Call - Health & Info API Routes
Backward-compatible endpoints formerly in api.py
"""
from flask import Blueprint, jsonify
from app import db
from datetime import datetime

api_health_bp = Blueprint('api_health', __name__)


@api_health_bp.route('/api/health')
def api_health():
    """Basic health check (backward compat: was in old api_bp)"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'message': 'Buggy Call API is running'
    }), 200


@api_health_bp.route('/api/health/ready')
def api_health_ready():
    """Readiness check with DB validation (backward compat)"""
    try:
        db.session.execute('SELECT 1')
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        critical_tables = ['hotel', 'system_user', 'location', 'buggy', 'buggy_request']
        critical_tables_ok = all(table in tables for table in critical_tables)
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'checks': {
                'database': {
                    'status': 'healthy',
                    'table_count': len(tables),
                    'critical_tables_ok': critical_tables_ok
                },
                'application': {'status': 'healthy'}
            }
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(e),
            'checks': {'database': {'status': 'unhealthy', 'error': str(e)}}
        }), 503


@api_health_bp.route('/api/version')
def api_version():
    """API version (backward compat)"""
    return jsonify({
        'version': '1.0.0',
        'name': 'Buggy Call API',
        'author': 'Erkan ERDEM'
    }), 200
