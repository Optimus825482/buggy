"""
Buggy Call - WebSocket Events
Enhanced with guest connection tracking and real-time status updates
Performance optimized with throttling and queue management
"""
from flask_socketio import emit, join_room, leave_room
from flask import session
from app import socketio
import logging
import time
from collections import deque, defaultdict
from threading import Lock

logger = logging.getLogger(__name__)

# Track connected guests per hotel (hotel_id -> count)
CONNECTED_GUESTS = {}

# Performance Optimization: Throttling & Queue Management
# Max 10 events per second per room
THROTTLE_LIMIT = 10
THROTTLE_WINDOW = 1.0  # seconds

# Event queues and throttle tracking
event_queues = defaultdict(deque)
throttle_counters = defaultdict(lambda: {'count': 0, 'window_start': time.time()})
queue_lock = Lock()


@socketio.on('connect')
def handle_connect():
    """
    Handle client connection with error handling
    """
    try:
        from flask import session
        user_id = session.get('user_id', 'unknown')
        role = session.get('role', 'unknown')
        
        logger.info(f"🔌 Client connected: User {user_id}, Role {role}")
        emit('connected', {
            'message': 'Connected to Buggy Call server',
            'timestamp': time.time()
        })
        
        # Log connection
        from app.utils.logger import WebSocketLogger
        if user_id != 'unknown':
            WebSocketLogger.log_connection(user_id, role)
    
    except Exception as e:
        logger.error(f"❌ Error in handle_connect: {str(e)}")
        from app.utils.logger import log_error
        log_error('WS_CONNECT', str(e), {'exception_type': type(e).__name__})


@socketio.on('disconnect')
def handle_disconnect():
    """
    Handle client disconnection with cleanup
    """
    try:
        from flask import session
        user_id = session.get('user_id', 'unknown')
        
        logger.info(f"🔌 Client disconnected: User {user_id}")
        
        # Log disconnection
        from app.utils.logger import WebSocketLogger
        if user_id != 'unknown':
            WebSocketLogger.log_disconnection(user_id, reason='client_disconnect')
    
    except Exception as e:
        logger.error(f"❌ Error in handle_disconnect: {str(e)}")
        from app.utils.logger import log_error
        log_error('WS_DISCONNECT', str(e), {'exception_type': type(e).__name__})


@socketio.on('join_room')
def handle_join_room(data):
    """Handle joining a room"""
    room = data.get('room')
    if room:
        join_room(room)
        emit('joined_room', {'room': room}, room=room)
        print(f'Client joined room: {room}')


@socketio.on('leave_room')
def handle_leave_room(data):
    """Handle leaving a room"""
    room = data.get('room')
    if room:
        leave_room(room)
        emit('left_room', {'room': room}, room=room)
        print(f'Client left room: {room}')


@socketio.on('ping')
def handle_ping():
    """Handle ping"""
    emit('pong', {'timestamp': 'now'})


def throttled_emit(event_name, data, room=None, broadcast=False):
    """
    Throttled emit with queue management
    Max 10 events per second per room
    
    Args:
        event_name: Event name
        data: Event data
        room: Room name (optional)
        broadcast: Broadcast to all (default: False)
    """
    room_key = room or 'global'
    
    with queue_lock:
        current_time = time.time()
        throttle_data = throttle_counters[room_key]
        
        # Reset counter if window expired
        if current_time - throttle_data['window_start'] >= THROTTLE_WINDOW:
            throttle_data['count'] = 0
            throttle_data['window_start'] = current_time
        
        # Check if under throttle limit
        if throttle_data['count'] < THROTTLE_LIMIT:
            # Send immediately
            throttle_data['count'] += 1
            emit(event_name, data, room=room, broadcast=broadcast)
            logger.debug(f"📤 Emitted {event_name} to {room_key} (count: {throttle_data['count']})")
        else:
            # Queue for later
            event_queues[room_key].append({
                'event': event_name,
                'data': data,
                'room': room,
                'broadcast': broadcast,
                'queued_at': current_time
            })
            logger.warning(f"⏳ Queued {event_name} for {room_key} (throttle limit reached)")


def process_event_queues():
    """
    Process queued events (called periodically)
    Should be called from a background task
    """
    with queue_lock:
        current_time = time.time()
        
        for room_key, queue in list(event_queues.items()):
            if not queue:
                continue
            
            throttle_data = throttle_counters[room_key]
            
            # Reset counter if window expired
            if current_time - throttle_data['window_start'] >= THROTTLE_WINDOW:
                throttle_data['count'] = 0
                throttle_data['window_start'] = current_time
            
            # Process queued events
            processed = 0
            while queue and throttle_data['count'] < THROTTLE_LIMIT:
                event_data = queue.popleft()
                
                # Check if event is too old (> 5 seconds)
                if current_time - event_data['queued_at'] > 5.0:
                    logger.warning(f"⚠️ Dropped stale event {event_data['event']} for {room_key}")
                    continue
                
                # Emit event
                emit(
                    event_data['event'],
                    event_data['data'],
                    room=event_data['room'],
                    broadcast=event_data['broadcast']
                )
                
                throttle_data['count'] += 1
                processed += 1
            
            if processed > 0:
                logger.info(f"✅ Processed {processed} queued events for {room_key}")


def get_throttle_stats():
    """
    Get throttling statistics for monitoring
    
    Returns:
        dict: Throttle stats per room
    """
    with queue_lock:
        stats = {}
        for room_key in set(list(throttle_counters.keys()) + list(event_queues.keys())):
            stats[room_key] = {
                'current_count': throttle_counters[room_key]['count'],
                'queued_events': len(event_queues[room_key]),
                'window_start': throttle_counters[room_key]['window_start']
            }
        return stats


@socketio.on('guest_connected')
def handle_guest_connected(data):
    """
    Handle guest connection event
    Notifies all drivers in the hotel that a guest is viewing the request page
    
    Args:
        data: {
            'hotel_id': int,
            'location_id': int (optional),
            'location_name': str (optional)
        }
    """
    try:
        hotel_id = data.get('hotel_id')
        location_id = data.get('location_id')
        location_name = data.get('location_name', 'Bilinmeyen Lokasyon')
        
        if not hotel_id:
            logger.warning("⚠️ guest_connected: hotel_id missing")
            return
        
        # Increment guest count for this hotel
        if hotel_id not in CONNECTED_GUESTS:
            CONNECTED_GUESTS[hotel_id] = 0
        CONNECTED_GUESTS[hotel_id] += 1
        
        guest_count = CONNECTED_GUESTS[hotel_id]
        
        logger.info(f"👤 Guest connected to hotel {hotel_id} (total: {guest_count})")

        # Prepare event data
        event_data = {
            'hotel_id': hotel_id,
            'location_id': location_id,
            'location_name': location_name,
            'guest_count': guest_count,
            'timestamp': socketio.server.get_current_time() if hasattr(socketio.server, 'get_current_time') else None
        }

        drivers_room = f'hotel_{hotel_id}_drivers'

        # Log detailed information
        logger.info('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
        logger.info(f'📡 [GUEST_CONNECTED] Broadcasting to drivers:')
        logger.info(f'   Room: {drivers_room}')
        logger.info(f'   Hotel ID: {hotel_id}')
        logger.info(f'   Location: {location_name}')
        logger.info(f'   Guest Count: {guest_count}')
        logger.info('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')

        # Broadcast to all drivers in this hotel (throttled)
        throttled_emit('guest_connected', event_data, room=drivers_room, broadcast=True)

        logger.info(f"✅ [GUEST_CONNECTED] Event emitted to {drivers_room}")
        
    except Exception as e:
        logger.error(f"❌ Error in handle_guest_connected: {str(e)}")


@socketio.on('guest_disconnected')
def handle_guest_disconnected(data):
    """
    Handle guest disconnection event
    Updates the guest count for drivers
    
    Args:
        data: {
            'hotel_id': int
        }
    """
    try:
        hotel_id = data.get('hotel_id')
        
        if not hotel_id:
            logger.warning("⚠️ guest_disconnected: hotel_id missing")
            return
        
        # Decrement guest count
        if hotel_id in CONNECTED_GUESTS and CONNECTED_GUESTS[hotel_id] > 0:
            CONNECTED_GUESTS[hotel_id] -= 1
            guest_count = CONNECTED_GUESTS[hotel_id]
            
            logger.info(f"👤 Guest disconnected from hotel {hotel_id} (remaining: {guest_count})")
            
            # Broadcast updated count to drivers
            emit('guest_disconnected', {
                'hotel_id': hotel_id,
                'guest_count': guest_count
            }, room=f'hotel_{hotel_id}_drivers', broadcast=True)
            
    except Exception as e:
        logger.error(f"❌ Error in handle_guest_disconnected: {str(e)}")


@socketio.on('request_accepted')
def handle_request_accepted(data):
    """
    Handle request accepted event
    Notifies guest and updates driver dashboards
    
    Args:
        data: {
            'request_id': int,
            'buggy_code': str,
            'driver_name': str,
            'hotel_id': int
        }
    """
    try:
        request_id = data.get('request_id')
        buggy_code = data.get('buggy_code')
        driver_name = data.get('driver_name')
        hotel_id = data.get('hotel_id')
        
        logger.info(f"✅ Request {request_id} accepted by {driver_name} (Buggy: {buggy_code})")
        
        # Notify guest
        emit('request_accepted', {
            'request_id': request_id,
            'buggy_code': buggy_code,
            'driver_name': driver_name,
            'status': 'accepted'
        }, room=f'request_{request_id}', broadcast=True)
        
        # Notify all drivers (remove from pending list)
        emit('request_taken', {
            'request_id': request_id,
            'buggy_code': buggy_code
        }, room=f'hotel_{hotel_id}_drivers', broadcast=True)
        
        # Notify admin dashboard
        emit('request_status_changed', {
            'request_id': request_id,
            'status': 'accepted',
            'buggy_code': buggy_code,
            'driver_name': driver_name
        }, room=f'hotel_{hotel_id}_admin', broadcast=True)
        
        logger.info(f"📡 Broadcast request_accepted for request {request_id}")
        
    except Exception as e:
        logger.error(f"❌ Error in handle_request_accepted: {str(e)}")


@socketio.on('request_completed')
def handle_request_completed(data):
    """
    Handle request completed event
    Notifies guest and updates dashboards
    
    Args:
        data: {
            'request_id': int,
            'hotel_id': int,
            'buggy_id': int,
            'location_id': int (optional)
        }
    """
    try:
        request_id = data.get('request_id')
        hotel_id = data.get('hotel_id')
        buggy_id = data.get('buggy_id')
        location_id = data.get('location_id')
        
        logger.info(f"🎉 Request {request_id} completed")
        
        # Notify guest
        emit('request_completed', {
            'request_id': request_id,
            'status': 'completed'
        }, room=f'request_{request_id}', broadcast=True)
        
        # Notify admin dashboard
        emit('request_status_changed', {
            'request_id': request_id,
            'status': 'completed'
        }, room=f'hotel_{hotel_id}_admin', broadcast=True)
        
        # Notify buggy status change (if buggy_id provided)
        if buggy_id:
            emit('buggy_status_changed', {
                'buggy_id': buggy_id,
                'status': 'available',
                'location_id': location_id
            }, room=f'hotel_{hotel_id}_admin', broadcast=True)
        
        logger.info(f"📡 Broadcast request_completed for request {request_id}")
        
    except Exception as e:
        logger.error(f"❌ Error in handle_request_completed: {str(e)}")


@socketio.on('buggy_status_changed')
def handle_buggy_status_changed(data):
    """
    Handle buggy status change event
    Updates admin dashboard in real-time
    
    Args:
        data: {
            'buggy_id': int,
            'status': str ('available', 'busy', 'offline'),
            'hotel_id': int,
            'location_id': int (optional),
            'driver_id': int (optional)
        }
    """
    try:
        buggy_id = data.get('buggy_id')
        status = data.get('status')
        hotel_id = data.get('hotel_id')
        location_id = data.get('location_id')
        driver_id = data.get('driver_id')
        
        logger.info(f"🚗 Buggy {buggy_id} status changed to {status}")
        
        # Broadcast to admin dashboard
        emit('buggy_status_changed', {
            'buggy_id': buggy_id,
            'status': status,
            'location_id': location_id,
            'driver_id': driver_id
        }, room=f'hotel_{hotel_id}_admin', broadcast=True)
        
        logger.info(f"📡 Broadcast buggy_status_changed for buggy {buggy_id}")
        
    except Exception as e:
        logger.error(f"❌ Error in handle_buggy_status_changed: {str(e)}")
