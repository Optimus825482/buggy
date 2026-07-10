"""
Buggy Call - WebSocket Events
Enhanced with guest connection tracking and real-time status updates
Performance optimized with throttling and queue management

NOT: Event handler'lar events.py'dedir.
    Kritik is mantigi (race condition fix, DB update, request/buggy event'leri) events.py'de.
    Bu dosya sadece join/leave/guest event'leri ve throttling icerir.
"""
from flask_socketio import emit, join_room, leave_room
from flask import session, request
from app import socketio
import logging
import time
from collections import deque, defaultdict
from threading import Lock

logger = logging.getLogger(__name__)

# Track connected guests per hotel (hotel_id -> count)
CONNECTED_GUESTS = {}
GUEST_LOCK = Lock()

# Performance Optimization: Throttling & Queue Management
# Max 10 events per second per room
THROTTLE_LIMIT = 10
THROTTLE_WINDOW = 1.0  # seconds

# Event queues and throttle tracking
event_queues = defaultdict(deque)
throttle_counters = defaultdict(lambda: {'count': 0, 'window_start': time.time()})
queue_lock = Lock()


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


@socketio.on('join_hotel')
def handle_join_hotel(data):
    """
    Handle joining hotel room (for drivers and admins)
    """
    try:
        logger.info('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
        logger.info(f'📥 [WEBSOCKET] join_hotel event received!')
        logger.info(f'   Data: {data}')
        logger.info(f'   SID: {request.sid}')
        logger.info('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
        
        hotel_id = data.get('hotel_id')
        role = data.get('role', 'unknown')
        
        logger.info(f'   Hotel ID: {hotel_id}')
        logger.info(f'   Role: {role}')
        
        if not hotel_id:
            logger.warning("⚠️ join_hotel: hotel_id missing")
            return
        
        # Determine room based on role
        if role == 'driver':
            room = f'hotel_{hotel_id}_drivers'
        elif role == 'admin':
            room = f'hotel_{hotel_id}_admin'
        else:
            room = f'hotel_{hotel_id}'
        
        # Join the room
        join_room(room)
        
        logger.info(f"✅ Client joined room: {room} (Role: {role})")
        logger.info(f"📤 Emitting joined_hotel confirmation...")
        
        # Emit confirmation back to client
        emit('joined_hotel', {
            'hotel_id': hotel_id,
            'role': role,
            'room': room,
            'message': f'Successfully joined {room}'
        })
        
        logger.info(f"✅ joined_hotel event emitted successfully!")
        logger.info('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
        
    except Exception as e:
        logger.error(f"❌ Error in handle_join_hotel: {str(e)}")
        logger.error(f"   Exception type: {type(e).__name__}")
        logger.error(f"   Exception details: {str(e)}")


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
        with GUEST_LOCK:
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
        with GUEST_LOCK:
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


