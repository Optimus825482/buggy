"""
Script to fix active BuggyDriver sessions
This closes all active driver sessions for a specific buggy
"""
from app import create_app, db
from app.models.buggy_driver import BuggyDriver
from datetime import datetime

def close_buggy_driver_sessions(buggy_id):
    """Close all active driver sessions for a buggy"""
    app = create_app()
    with app.app_context():
        # Find all active sessions for this buggy
        active_sessions = BuggyDriver.query.filter_by(
            buggy_id=buggy_id,
            is_active=True
        ).all()
        
        if not active_sessions:
            print(f"No active sessions found for buggy {buggy_id}")
            return
        
        print(f"Found {len(active_sessions)} active session(s) for buggy {buggy_id}")
        
        for session in active_sessions:
            print(f"  - Closing session ID {session.id} (driver_id: {session.driver_id})")
            session.is_active = False
            session.last_active_at = datetime.utcnow()
        
        db.session.commit()
        print(f"Successfully closed all active sessions for buggy {buggy_id}")

if __name__ == '__main__':
    # Fix buggy 1
    close_buggy_driver_sessions(1)
