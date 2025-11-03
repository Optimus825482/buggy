"""
Buggy Call - WebSocket Events
"""
from flask_socketio import emit, join_room, leave_room
from app import socketio


@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print('Client connected')
    emit('connected', {'message': 'Connected to Buggy Call server'})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print('Client disconnected')


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
