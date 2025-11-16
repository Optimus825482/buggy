"""
Buggy Call - WebSocket Events
"""
from flask_socketio import emit, join_room, leave_room
from flask import request, session
from app import socketio, db
from app.models.user import SystemUser, UserRole
from app.models.session import Session as SessionModel
from app.models.buggy import BuggyStatus
from app.services.audit_service import AuditService
from datetime import datetime

# Store user_id mapping for WebSocket connections
# Key: request.sid, Value: user_id
ws_connections = {}


@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print(f'✅ Client connected: {request.sid}')
    
    # Session bilgisini logla (debug için)
    user_id = session.get('user_id')
    role = session.get('role')
    if user_id:
        print(f'   User: {user_id}, Role: {role}')
    
    emit('connected', {
        'message': 'Connected to Buggy Call server',
        'sid': request.sid
    })
    
    return True  # ✅ Bağlantıyı kabul et


@socketio.on('disconnect')
def handle_disconnect():
    """
    ✅ RACE CONDITION FIX: Critical DB updates sync, notifications async
    Handle client disconnection - Auto-terminate driver sessions
    """
    print(f'Client disconnected: {request.sid}')

    # Get user_id from global mapping (set in join_user)
    user_id = ws_connections.get(request.sid)

    # Fallback to Flask session
    if not user_id:
        user_id = session.get('ws_user_id') or session.get('user_id')

    if not user_id:
        print(f'No user_id found for SID: {request.sid}')
        return

    # ✅ Connection mapping'i hemen temizle
    if request.sid in ws_connections:
        del ws_connections[request.sid]
        print(f'Cleaned up connection mapping for SID: {request.sid}')

    # ✅ RACE CONDITION FIX: Database update SYNCHRONOUSLY to prevent race condition
    # Only audit/notifications go to background thread
    buggy_data = _update_driver_status_sync(user_id)

    # ✅ Background thread only for non-critical tasks (audit, notifications)
    if buggy_data:
        from threading import Thread
        Thread(target=_handle_driver_disconnect_async,
               args=(user_id, buggy_data),
               daemon=True).start()
        print(f'[DISCONNECT] Notifications queued in background for user {user_id}')
    else:
        print(f'[DISCONNECT] No active buggy for user {user_id}')


def _update_driver_status_sync(user_id):
    """
    ✅ RACE CONDITION FIX: Synchronous database update
    Immediately set buggy to OFFLINE when driver disconnects
    Returns buggy_data dict for async notification, or None if no active buggy
    """
    try:
        # Get user from database
        user = SystemUser.query.get(user_id)

        # Only process for drivers
        if not user or user.role != UserRole.DRIVER:
            print(f'[DISCONNECT_SYNC] User {user_id} is not a driver, skipping')
            return None

        print(f'[DISCONNECT_SYNC] Processing disconnect for driver: {user.username} (ID: {user_id})')

        # Find driver's active buggy using BuggyDriver table
        from app.models.buggy_driver import BuggyDriver
        from app.models.buggy import Buggy

        active_buggy_assoc = BuggyDriver.query.filter_by(
            driver_id=user_id,
            is_active=True
        ).first()

        if not active_buggy_assoc:
            print(f'[DISCONNECT_SYNC] Driver {user.username} has no active buggy assignment')
            return None

        buggy = Buggy.query.get(active_buggy_assoc.buggy_id)

        if not buggy:
            print(f'[DISCONNECT_SYNC] Buggy not found for driver {user.username}')
            return None

        # ✅ CRITICAL: Update database immediately to prevent race condition
        # Deactivate driver association
        active_buggy_assoc.is_active = False
        print(f'[DISCONNECT_SYNC] Deactivated driver association for buggy_id={buggy.id}')

        # Set buggy to OFFLINE and clear location
        buggy.status = BuggyStatus.OFFLINE
        buggy.current_location_id = None  # Clear location on disconnect

        # Commit changes IMMEDIATELY
        db.session.commit()

        print(f'[DISCONNECT_SYNC] ✅ Buggy {buggy.code} set to OFFLINE (database updated)')

        # Return data for async notification
        return {
            'buggy_id': buggy.id,
            'buggy_code': buggy.code,
            'buggy_icon': buggy.icon,
            'hotel_id': buggy.hotel_id,
            'driver_name': user.username
        }

    except Exception as e:
        print(f'[DISCONNECT_SYNC] Error updating driver status: {str(e)}')
        import traceback
        traceback.print_exc()
        try:
            db.session.rollback()
        except:
            pass
        return None


def _handle_driver_disconnect_async(user_id, buggy_data):
    """
    ✅ RACE CONDITION FIX: Background notification and audit only
    Database already updated synchronously in _update_driver_status_sync
    This function only handles non-critical tasks: audit logs and WebSocket notifications
    """
    try:
        from app import create_app
        app = create_app()

        with app.app_context():
            # Log audit trail
            AuditService.log_action(
                action='driver_disconnected',
                entity_type='buggy',
                entity_id=buggy_data['buggy_id'],
                user_id=user_id,
                hotel_id=buggy_data['hotel_id'],
                new_values={
                    'reason': 'connection_lost',
                    'buggy_code': buggy_data['buggy_code'],
                    'driver_name': buggy_data['driver_name'],
                    'status': 'offline'
                }
            )

            # Emit WebSocket event to admin panel
            from app import socketio
            room_name = f'hotel_{buggy_data["hotel_id"]}_admin'
            event_data = {
                'buggy_id': buggy_data['buggy_id'],
                'buggy_code': buggy_data['buggy_code'],
                'buggy_icon': buggy_data['buggy_icon'],
                'driver_id': None,
                'driver_name': None,
                'location_name': None,
                'status': 'offline',
                'reason': 'connection_lost'
            }

            print(f'[DISCONNECT_ASYNC] Emitting buggy_status_changed to room: {room_name}')
            socketio.emit('buggy_status_changed', event_data, room=room_name, namespace='/')

            print(f'[DISCONNECT_ASYNC] ✅ Notifications sent for Buggy {buggy_data["buggy_code"]}')

    except Exception as e:
        print(f'[DISCONNECT_ASYNC] Error sending notifications for user {user_id}: {str(e)}')
        import traceback
        traceback.print_exc()


@socketio.on('join_hotel')
def handle_join_hotel(data):
    """Join hotel room for real-time updates"""
    hotel_id = data.get('hotel_id')
    role = data.get('role', 'guest')  # admin, driver, guest

    if hotel_id:
        # Join hotel room
        room = f'hotel_{hotel_id}'
        join_room(room)

        # Join role-specific room (use singular form for consistency)
        if role == 'admin':
            role_room = f'hotel_{hotel_id}_admin'
            join_room(role_room)
            print(f'✅ [WEBSOCKET] Client joined: {room} and {role_room}')
            logger.info(f'✅ [WEBSOCKET] Admin joined: {room} and {role_room}')
        elif role == 'driver':
            role_room = f'hotel_{hotel_id}_drivers'
            join_room(role_room)
            print(f'✅ [WEBSOCKET] Driver joined room: {role_room}')
            logger.info(f'✅ [WEBSOCKET] Driver joined room: {role_room}')
        else:
            print(f'✅ [WEBSOCKET] Client joined: {room}')
            logger.info(f'✅ [WEBSOCKET] Guest joined: {room}')

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
        }, room=f'hotel_{hotel_id}_admin')
        
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
        # Store user_id in global mapping for disconnect handler
        ws_connections[request.sid] = user_id
        
        # Also store in Flask session as backup
        session['ws_user_id'] = user_id
        
        room = f'user_{user_id}'
        join_room(room)
        print(f'User {user_id} joined personal room (SID: {request.sid})')
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
        }, room=f'hotel_{hotel_id}_admin')
        
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
        }, room=f'hotel_{hotel_id}_admin')
        
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
        }, room=f'hotel_{hotel_id}_admin')
        
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
