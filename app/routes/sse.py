"""
SSE (Server-Sent Events) for Real-time Notifications
Simple and reliable push notifications to drivers
"""
from flask import Blueprint, Response, stream_with_context, request, session
from app.models.user import SystemUser, UserRole
from app.utils.decorators import require_login, require_role
from app import csrf
import json
import time
import queue
from datetime import datetime

sse_bp = Blueprint('sse', __name__)

# CSRF exempt for SSE endpoints
csrf.exempt(sse_bp)

# Store active SSE connections per driver
# Key: user_id, Value: queue
active_connections = {}


def get_driver_queue(user_id):
    """Get or create queue for driver"""
    if user_id not in active_connections:
        active_connections[user_id] = queue.Queue()
    return active_connections[user_id]


def send_to_driver(user_id, event_type, data):
    """Send event to specific driver"""
    if user_id in active_connections:
        try:
            active_connections[user_id].put({
                'event': event_type,
                'data': data,
                'timestamp': datetime.utcnow().isoformat()
            })
            print(f'✅ SSE: Sent {event_type} to driver {user_id}')
            return True
        except Exception as e:
            print(f'❌ SSE: Error sending to driver {user_id}: {e}')
            return False
    return False


def send_to_all_drivers(hotel_id, event_type, data):
    """Send event to all drivers in hotel"""
    from app.models.buggy_driver import BuggyDriver
    
    # Get all active drivers in hotel
    active_drivers = BuggyDriver.query.filter_by(
        is_active=True
    ).join(SystemUser).filter(
        SystemUser.hotel_id == hotel_id,
        SystemUser.role == UserRole.DRIVER
    ).all()
    
    sent_count = 0
    for driver_assoc in active_drivers:
        if send_to_driver(driver_assoc.driver_id, event_type, data):
            sent_count += 1
    
    print(f'✅ SSE: Sent {event_type} to {sent_count} drivers in hotel {hotel_id}')
    return sent_count


@sse_bp.route('/stream')
@require_login
@require_role('driver')
def stream():
    """SSE stream endpoint for drivers"""
    user_id = session.get('user_id')
    print(f'✅ [SSE] Driver {user_id} connected to stream')
    
    def event_stream():
        """Generate SSE events"""
        q = get_driver_queue(user_id)
        print(f'✅ [SSE] Queue created for driver {user_id}')
        
        # Send initial connection message
        yield f"data: {json.dumps({'event': 'connected', 'message': 'SSE connected'})}\n\n"
        
        # Keep connection alive and send events
        while True:
            try:
                # Wait for event with timeout (for keep-alive)
                try:
                    event = q.get(timeout=30)  # 30 second timeout
                    yield f"event: {event['event']}\n"
                    yield f"data: {json.dumps(event['data'])}\n\n"
                except queue.Empty:
                    # Send keep-alive ping
                    yield f"data: {json.dumps({'event': 'ping', 'timestamp': datetime.utcnow().isoformat()})}\n\n"
            except GeneratorExit:
                # Client disconnected
                print(f'SSE: Driver {user_id} disconnected')
                if user_id in active_connections:
                    del active_connections[user_id]
                break
            except Exception as e:
                print(f'SSE: Error for driver {user_id}: {e}')
                break
    
    return Response(
        stream_with_context(event_stream()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Connection': 'keep-alive'
        }
    )


@sse_bp.route('/test-notification', methods=['POST'])
@require_login
def test_notification():
    """Test endpoint to send notification to a driver"""
    data = request.get_json()
    user_id = data.get('user_id')
    
    if not user_id:
        return {'error': 'user_id required'}, 400
    
    success = send_to_driver(user_id, 'test', {
        'message': 'Test notification',
        'timestamp': datetime.utcnow().isoformat()
    })
    
    return {
        'success': success,
        'message': 'Notification sent' if success else 'Driver not connected'
    }
