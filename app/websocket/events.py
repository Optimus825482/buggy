"""
Buggy Call - WebSocket Events
"""
from flask_socketio import emit, join_room, leave_room
from flask import request
from app import socketio


@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print(f'Client connected: {request.sid}')
    emit('connected', {
        'message': 'Connected to Buggy Call server',
        'sid': request.sid
    })


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print(f'Client disconnected: {request.sid}')


@socketio.on('join_hotel')
def handle_join_hotel(data):
    """Join hotel room for real-time updates"""
    hotel_id = data.get('hotel_id')
    role = data.get('role', 'guest')  # admin, driver, guest
    
    if hotel_id:
        # Join hotel room
        room = f'hotel_{hotel_id}'
        join_room(room)
        
        # Join role-specific room
        if role in ['driver', 'admin']:
            role_room = f'hotel_{hotel_id}_{role}s'
            join_room(role_room)
            print(f'Client joined: {room} and {role_room}')
        else:
            print(f'Client joined: {room}')
        
        emit('joined_hotel', {
            'hotel_id': hotel_id,
            'role': role,
            'room': room
        })


@socketio.on('join_request')
def handle_join_request(data):
    """Join request room for status tracking (Guest)"""
    request_id = data.get('request_id')
    if request_id:
        room = f'request_{request_id}'
        join_room(room)
        print(f'Client joined request room: {room}')
        emit('joined_request', {'request_id': request_id})


@socketio.on('driver_status')
def handle_driver_status(data):
    """Update driver/buggy status"""
    buggy_id = data.get('buggy_id')
    status = data.get('status')  # available, busy, offline
    hotel_id = data.get('hotel_id')
    location_id = data.get('location_id')
    
    if buggy_id and status and hotel_id:
        # Broadcast to hotel room
        emit('buggy_status_changed', {
            'buggy_id': buggy_id,
            'status': status,
            'location_id': location_id
        }, room=f'hotel_{hotel_id}')
        
        print(f'Buggy {buggy_id} status changed to {status}')


@socketio.on('driver_location')
def handle_driver_location(data):
    """Update driver location"""
    buggy_id = data.get('buggy_id')
    location_id = data.get('location_id')
    hotel_id = data.get('hotel_id')
    
    if buggy_id and location_id and hotel_id:
        # Broadcast to hotel admins
        emit('driver_location_update', {
            'buggy_id': buggy_id,
            'location_id': location_id
        }, room=f'hotel_{hotel_id}_admins')
        
        print(f'Buggy {buggy_id} location updated to {location_id}')


@socketio.on('request_notification')
def handle_request_notification(data):
    """Send request notification to drivers"""
    hotel_id = data.get('hotel_id')
    request_data = data.get('request')
    
    if hotel_id and request_data:
        emit('new_request', request_data, room=f'hotel_{hotel_id}_drivers')
        print(f'New request notification sent to hotel {hotel_id} drivers')


@socketio.on('ping')
def handle_ping():
    """Handle ping for connection keep-alive"""
    emit('pong', {
        'timestamp': 'now',
        'sid': request.sid
    })


@socketio.on('join_user')
def handle_join_user(data):
    """Join user-specific room for session management"""
    user_id = data.get('user_id')
    if user_id:
        room = f'user_{user_id}'
        join_room(room)
        print(f'User {user_id} joined personal room')
        emit('joined_user_room', {'user_id': user_id})


@socketio.on('request_accepted_event')
def handle_request_accepted_event(data):
    """Broadcast request acceptance to guest and admins"""
    request_id = data.get('request_id')
    hotel_id = data.get('hotel_id')
    buggy_data = data.get('buggy')
    driver_data = data.get('driver')
    
    if request_id and hotel_id:
        # Notify guest
        emit('request_accepted', {
            'request_id': request_id,
            'buggy': buggy_data,
            'driver': driver_data
        }, room=f'request_{request_id}')
        
        # Notify admins
        emit('request_status_changed', {
            'request_id': request_id,
            'status': 'accepted',
            'buggy': buggy_data,
            'driver': driver_data
        }, room=f'hotel_{hotel_id}_admins')
        
        print(f'Request {request_id} accepted by driver')


@socketio.on('request_completed_event')
def handle_request_completed_event(data):
    """Broadcast request completion to guest and admins"""
    request_id = data.get('request_id')
    hotel_id = data.get('hotel_id')
    
    if request_id and hotel_id:
        # Notify guest
        emit('request_completed', {
            'request_id': request_id,
            'message': 'Buggy\'niz geldi!'
        }, room=f'request_{request_id}')
        
        # Notify admins
        emit('request_status_changed', {
            'request_id': request_id,
            'status': 'completed'
        }, room=f'hotel_{hotel_id}_admins')
        
        print(f'Request {request_id} completed')


@socketio.on('driver_location_updated_event')
def handle_driver_location_updated_event(data):
    """Broadcast driver location update to admins"""
    buggy_id = data.get('buggy_id')
    buggy_code = data.get('buggy_code')
    driver_name = data.get('driver_name')
    location_id = data.get('location_id')
    location_name = data.get('location_name')
    hotel_id = data.get('hotel_id')
    status = data.get('status')
    
    if hotel_id:
        emit('driver_location_updated', {
            'buggy_id': buggy_id,
            'buggy_code': buggy_code,
            'driver_name': driver_name,
            'location_id': location_id,
            'location_name': location_name,
            'status': status
        }, room=f'hotel_{hotel_id}_admins')
        
        print(f'Driver location updated: Buggy {buggy_code} at {location_name}')


@socketio.on('force_logout_event')
def handle_force_logout_event(data):
    """Force logout a user (session terminated)"""
    user_id = data.get('user_id')
    reason = data.get('reason', 'Session terminated')
    message = data.get('message', 'Oturumunuz sonlandırıldı')
    
    if user_id:
        emit('force_logout', {
            'reason': reason,
            'message': message
        }, room=f'user_{user_id}')
        
        print(f'Force logout sent to user {user_id}: {reason}')
