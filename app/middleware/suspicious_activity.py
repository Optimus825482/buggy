"""
Suspicious Activity Detection Middleware
Detects and logs suspicious user behavior
"""
from flask import request, session
from datetime import datetime, timedelta
from collections import defaultdict
import threading

# Thread-safe storage for tracking activity
activity_tracker = defaultdict(lambda: {'count': 0, 'last_reset': datetime.utcnow()})
activity_lock = threading.Lock()

# Thresholds for suspicious activity
THRESHOLDS = {
    'failed_login_attempts': 5,  # 5 failed logins in time window
    'rapid_requests': 100,  # 100 requests in time window
    'time_window_minutes': 5,  # Time window for tracking
    'bulk_operations': 50,  # 50+ items in single operation
}

# ✅ PERFORMANS: Sadece kritik endpoint'lerde monitoring yap
MONITORED_ENDPOINTS = {
    'auth.login',
    'auth.change_password',
    'api.create_request',
    'api.delete_request',
    'admin.delete_user',
    'admin.delete_buggy',
    'admin.delete_location',
    'system_admin.reset_database',
    'system_reset.reset_system'
}


def detect_suspicious_activity(app):
    """Register suspicious activity detection middleware"""
    
    @app.before_request
    def check_suspicious_activity():
        """
        ✅ PERFORMANS OPTİMİZE: Sadece kritik endpoint'lerde kontrol et
        Check for suspicious activity patterns
        """
        # Skip for static files and health checks
        if request.endpoint in ['static', 'health_check', None] or \
           request.path.startswith('/static/'):
            return None
        
        # ✅ Sadece kritik endpoint'lerde monitoring yap
        if request.endpoint not in MONITORED_ENDPOINTS:
            return None
        
        user_id = session.get('user_id')
        ip_address = request.remote_addr
        
        # Track by user_id if logged in, otherwise by IP
        tracker_key = f"user_{user_id}" if user_id else f"ip_{ip_address}"
        
        with activity_lock:
            tracker = activity_tracker[tracker_key]
            now = datetime.utcnow()
            
            # Reset counter if time window has passed
            if (now - tracker['last_reset']).total_seconds() > THRESHOLDS['time_window_minutes'] * 60:
                tracker['count'] = 0
                tracker['last_reset'] = now
            
            # Increment request count
            tracker['count'] += 1
            
            # Check for rapid requests (potential DDoS or scraping)
            if tracker['count'] > THRESHOLDS['rapid_requests']:
                log_suspicious_activity(
                    action='rapid_requests_detected',
                    details=f"{tracker['count']} requests in {THRESHOLDS['time_window_minutes']} minutes",
                    user_id=user_id,
                    ip_address=ip_address
                )
        
        return None
    
    @app.after_request
    def check_bulk_operations(response):
        """Check for suspicious bulk operations"""
        # Only check POST/PUT/DELETE requests
        if request.method not in ['POST', 'PUT', 'DELETE']:
            return response
        
        # Check if request contains bulk data
        if request.is_json:
            data = request.get_json(silent=True)
            if data and isinstance(data, dict):
                # Check for arrays that might indicate bulk operations
                for key, value in data.items():
                    if isinstance(value, list) and len(value) > THRESHOLDS['bulk_operations']:
                        log_suspicious_activity(
                            action='suspicious_bulk_operation',
                            details=f"Bulk operation with {len(value)} items on {request.endpoint}",
                            user_id=session.get('user_id'),
                            ip_address=request.remote_addr
                        )
                        break
        
        return response


def log_suspicious_activity(action, details, user_id=None, ip_address=None):
    """Log suspicious activity to audit trail"""
    try:
        from app.services.audit_service import AuditService
        from app.models.user import SystemUser
        
        hotel_id = None
        if user_id:
            user = SystemUser.query.get(user_id)
            if user:
                hotel_id = user.hotel_id
        
        AuditService.log_action(
            action=action,
            entity_type='security',
            entity_id=None,
            new_values={'details': details, 'ip_address': ip_address},
            user_id=user_id,
            hotel_id=hotel_id
        )
    except Exception as e:
        # Don't fail the request if logging fails
        print(f"Failed to log suspicious activity: {str(e)}")


def track_failed_login(username, ip_address):
    """Track failed login attempts"""
    tracker_key = f"login_{username}_{ip_address}"
    
    with activity_lock:
        tracker = activity_tracker[tracker_key]
        now = datetime.utcnow()
        
        # Reset counter if time window has passed
        if (now - tracker['last_reset']).total_seconds() > THRESHOLDS['time_window_minutes'] * 60:
            tracker['count'] = 0
            tracker['last_reset'] = now
        
        # Increment failed login count
        tracker['count'] += 1
        
        # Check for brute force attack
        if tracker['count'] >= THRESHOLDS['failed_login_attempts']:
            log_suspicious_activity(
                action='brute_force_attempt',
                details=f"{tracker['count']} failed login attempts for user '{username}'",
                user_id=None,
                ip_address=ip_address
            )
            return True  # Suspicious activity detected
    
    return False


def check_unauthorized_access(user_id, required_role, endpoint):
    """Log unauthorized access attempts"""
    log_suspicious_activity(
        action='unauthorized_access_attempt',
        details=f"User attempted to access {endpoint} without {required_role} role",
        user_id=user_id,
        ip_address=request.remote_addr if request else None
    )
