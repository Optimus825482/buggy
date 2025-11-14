"""
Performance Monitoring API
Provides endpoints for monitoring system performance
"""
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app.utils.performance_monitor import PerformanceMonitor
from app.websocket import get_throttle_stats
from functools import wraps
import logging

logger = logging.getLogger(__name__)

performance_bp = Blueprint('performance', __name__, url_prefix='/api/performance')


def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            return jsonify({
                'success': False,
                'error': 'Admin access required'
            }), 403
        return f(*args, **kwargs)
    return decorated_function


@performance_bp.route('/metrics', methods=['GET'])
@admin_required
def get_metrics():
    """
    Get performance metrics
    
    Returns:
        JSON response with metrics
    """
    try:
        operation = request.args.get('operation')
        metrics = PerformanceMonitor.get_metrics(operation)
        
        return jsonify({
            'success': True,
            'metrics': metrics
        })
    except Exception as e:
        logger.error(f"Error getting metrics: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@performance_bp.route('/metrics/reset', methods=['POST'])
@admin_required
def reset_metrics():
    """
    Reset performance metrics
    
    Returns:
        JSON response
    """
    try:
        operation = request.json.get('operation') if request.json else None
        PerformanceMonitor.reset_metrics(operation)
        
        return jsonify({
            'success': True,
            'message': 'Metrics reset successfully'
        })
    except Exception as e:
        logger.error(f"Error resetting metrics: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@performance_bp.route('/websocket/stats', methods=['GET'])
@admin_required
def get_websocket_stats():
    """
    Get WebSocket throttling statistics
    
    Returns:
        JSON response with WebSocket stats
    """
    try:
        stats = get_throttle_stats()
        
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        logger.error(f"Error getting WebSocket stats: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@performance_bp.route('/health', methods=['GET'])
@admin_required
def health_check():
    """
    System health check
    
    Returns:
        JSON response with health status
    """
    try:
        from app import db
        from app.models.request import BuggyRequest, RequestStatus
        from app.models.buggy import Buggy, BuggyStatus
        import time
        
        health = {
            'status': 'healthy',
            'checks': {}
        }
        
        # Database check
        try:
            start = time.time()
            db.session.execute('SELECT 1')
            db_time = time.time() - start
            health['checks']['database'] = {
                'status': 'ok',
                'response_time': f"{db_time:.3f}s"
            }
        except Exception as e:
            health['status'] = 'unhealthy'
            health['checks']['database'] = {
                'status': 'error',
                'error': str(e)
            }
        
        # Pending requests check
        try:
            pending_count = BuggyRequest.query.filter_by(
                status=RequestStatus.PENDING
            ).count()
            health['checks']['pending_requests'] = {
                'status': 'ok',
                'count': pending_count
            }
            
            if pending_count > 50:
                health['checks']['pending_requests']['warning'] = 'High pending request count'
        except Exception as e:
            health['checks']['pending_requests'] = {
                'status': 'error',
                'error': str(e)
            }
        
        # Available buggies check
        try:
            available_count = Buggy.query.filter_by(
                status=BuggyStatus.AVAILABLE
            ).count()
            health['checks']['available_buggies'] = {
                'status': 'ok',
                'count': available_count
            }
            
            if available_count == 0:
                health['checks']['available_buggies']['warning'] = 'No available buggies'
        except Exception as e:
            health['checks']['available_buggies'] = {
                'status': 'error',
                'error': str(e)
            }
        
        # Performance metrics check
        try:
            metrics = PerformanceMonitor.get_metrics()
            slow_operations = []
            
            for operation, metric in metrics.items():
                if metric.get('avg_time', 0) > 1.0:
                    slow_operations.append({
                        'operation': operation,
                        'avg_time': f"{metric['avg_time']:.3f}s"
                    })
            
            health['checks']['performance'] = {
                'status': 'ok',
                'tracked_operations': len(metrics)
            }
            
            if slow_operations:
                health['checks']['performance']['slow_operations'] = slow_operations
        except Exception as e:
            health['checks']['performance'] = {
                'status': 'error',
                'error': str(e)
            }
        
        return jsonify({
            'success': True,
            'health': health
        })
    except Exception as e:
        logger.error(f"Error in health check: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
