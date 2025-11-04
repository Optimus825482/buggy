"""
Buggy Call - Session Cleanup Middleware
Handles cleanup when driver sessions expire
"""
from flask import session, g, request
from app import db
from app.models.user import SystemUser, UserRole
from app.models.buggy import Buggy, BuggyStatus
from app.models.buggy_driver import BuggyDriver
from datetime import datetime


def cleanup_expired_driver_sessions():
    """
    Check for expired driver sessions and cleanup buggy status
    This runs before each request to ensure buggies are properly cleaned up
    """
    # Only check if there's a user_id in session
    if 'user_id' not in session:
        return
    
    user_id = session.get('user_id')
    
    # Check if user exists and is a driver
    user = SystemUser.query.get(user_id)
    if not user or user.role != UserRole.DRIVER:
        return
    
    # CRITICAL: Ensure driver sessions are non-permanent
    # This forces session to expire when browser closes
    if session.permanent:
        print(f'[SESSION_CLEANUP] WARNING: Driver session was permanent, fixing...')
        session.permanent = False
    
    # Mark that we've checked this session
    g.session_checked = True


def cleanup_inactive_drivers():
    """
    Cleanup buggies for drivers who haven't been active
    This should be called periodically (e.g., via cron or background task)
    """
    from datetime import timedelta
    
    # Find all active driver associations
    active_associations = BuggyDriver.query.filter_by(is_active=True).all()
    
    for assoc in active_associations:
        # If driver hasn't been active in last 5 minutes, consider them disconnected
        if assoc.last_active_at:
            time_since_active = datetime.utcnow() - assoc.last_active_at
            if time_since_active > timedelta(minutes=5):
                print(f'[SESSION_CLEANUP] Driver {assoc.driver_id} inactive for {time_since_active}, cleaning up buggy {assoc.buggy_id}')
                
                # Deactivate driver
                assoc.is_active = False
                
                # Set buggy to offline and clear location
                buggy = Buggy.query.get(assoc.buggy_id)
                if buggy:
                    buggy.status = BuggyStatus.OFFLINE
                    buggy.current_location_id = None
                    
                    # Emit WebSocket event
                    try:
                        from app import socketio
                        socketio.emit('buggy_status_changed', {
                            'buggy_id': buggy.id,
                            'buggy_code': buggy.code,
                            'buggy_icon': buggy.icon,
                            'driver_id': None,
                            'driver_name': None,
                            'location_name': None,
                            'status': 'offline',
                            'reason': 'session_expired'
                        }, room=f'hotel_{buggy.hotel_id}_admin')
                    except Exception as e:
                        print(f'[SESSION_CLEANUP] Error emitting event: {e}')
    
    db.session.commit()
