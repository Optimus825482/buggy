"""
Buggy Call - Driver API Routes
Extracted from api_old.py for driver-specific endpoints
"""
from flask import Blueprint, jsonify, request, session, current_app
from app import db, csrf, socketio
from app.models.user import SystemUser, UserRole
from app.models.location import Location
from app.models.buggy import Buggy, BuggyStatus
from app.models.request import BuggyRequest, RequestStatus
from app.models.buggy_driver import BuggyDriver
from app.services import LocationService, BuggyService, FCMNotificationService
from app.utils import APIResponse, require_login, require_role
from app.utils.logger import log_driver_event, log_error
from app.utils.exceptions import BuggyCallException, ForbiddenException, BusinessLogicException
from datetime import datetime

api_driver_bp = Blueprint('api_driver', __name__)

# Exempt API endpoints from CSRF (using JWT/session instead)
csrf.exempt(api_driver_bp)


# ==================== Driver Initial Location ====================
@api_driver_bp.route('/api/driver/set-initial-location', methods=['POST'])
# Rate limiter removed
@require_login
def set_initial_location():
    """Set driver's initial location on first login"""
    try:
        user = SystemUser.query.get(session['user_id'])
        data = request.get_json()
        
        if not data or 'location_id' not in data:
            return jsonify({'error': 'location_id gereklidir'}), 400
        
        location_id = data['location_id']
        
        # Check if user is driver
        if user.role != UserRole.DRIVER:
            return jsonify({'error': 'Sadece sürücüler lokasyon ayarlayabilir'}), 403
        
        # Check if driver has buggy
        if not user.buggy:
            return jsonify({'error': 'Size atanmış buggy bulunamadı'}), 404
        
        # Validate location
        location = Location.query.get(location_id)
        if not location:
            return jsonify({'error': 'Lokasyon bulunamadı'}), 404
        
        if location.hotel_id != user.hotel_id:
            return jsonify({'error': 'Lokasyon farklı bir otele ait'}), 400
        
        # Set buggy location and status
        user.buggy.current_location_id = location_id
        user.buggy.status = BuggyStatus.AVAILABLE
        
        # Remove location setup flag
        session.pop('needs_location_setup', None)
        
        db.session.commit()
        
        # Log initial location setup
        from app.services.audit_service import AuditService
        AuditService.log_action(
            action='driver_initial_location_set',
            entity_type='buggy',
            entity_id=user.buggy.id,
            new_values={'location_id': location_id, 'location_name': location.name},
            user_id=user.id,
            hotel_id=user.hotel_id
        )
        
        # Emit WebSocket event to admin panel for real-time status update
        try:
            from app import socketio
            socketio.emit('buggy_status_changed', {
                'buggy_id': user.buggy.id,
                'buggy_code': user.buggy.code,
                'buggy_icon': user.buggy.icon,
                'driver_id': user.id,
                'driver_name': user.full_name if user.full_name else user.username,
                'location_id': location_id,
                'location_name': location.name,
                'status': 'available',
                'reason': 'initial_location_set'
            }, room=f'hotel_{user.hotel_id}_admin')
            print(f'[INITIAL_LOCATION] Emitted buggy_status_changed event to hotel_{user.hotel_id}_admin')
        except Exception as e:
            print(f'[INITIAL_LOCATION] Error emitting buggy_status_changed: {e}')
        
        # Emit buggy status update for real-time dashboard
        try:
            from app.services.buggy_service import BuggyService
            BuggyService.emit_buggy_status_update(user.buggy.id, user.hotel_id)
            print(f'[INITIAL_LOCATION] Emitted buggy status update')
        except Exception as e:
            print(f'[INITIAL_LOCATION] Error emitting buggy status: {e}')
        
        return jsonify({
            'success': True,
            'message': 'Lokasyon ayarlandı, sisteme hoş geldiniz!',
            'buggy': user.buggy.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ==================== Driver Location Management ====================
@api_driver_bp.route('/api/driver/set-location', methods=['POST'])
# Rate limiter removed
@require_login
def set_driver_location():
    """Set or update driver's current location"""
    try:
        user = SystemUser.query.get(session['user_id'])
        
        # User kontrolü
        if not user:
            return jsonify({'error': 'Kullanıcı bulunamadı'}), 404
        
        data = request.get_json()
        
        if not data or 'location_id' not in data:
            return jsonify({'error': 'location_id gereklidir'}), 400
        
        location_id = data['location_id']
        
        # Location ID validasyonu
        if not isinstance(location_id, int) or location_id <= 0:
            return jsonify({'error': 'Geçersiz location_id'}), 400
        
        # Check if user is driver
        if user.role != UserRole.DRIVER:
            return jsonify({'error': 'Sadece sürücüler lokasyon ayarlayabilir'}), 403
        
        # Check if driver has buggy
        if not user.buggy:
            return jsonify({'error': 'Size atanmış buggy bulunamadı. Lütfen yöneticinizle iletişime geçin.'}), 404
        
        # Validate location
        location = Location.query.get(location_id)
        if not location or not location.is_active:
            return jsonify({'error': 'Geçerli bir lokasyon bulunamadı'}), 404
        
        if location.hotel_id != user.hotel_id:
            return jsonify({'error': 'Lokasyon farklı bir otele ait'}), 400
        
        # Store old location for audit
        old_location_id = user.buggy.current_location_id
        old_location_name = user.buggy.current_location.name if user.buggy.current_location else None
        
        # Update buggy location and set to available
        user.buggy.current_location_id = location_id
        user.buggy.status = BuggyStatus.AVAILABLE
        
        db.session.commit()
        
        # Log location update
        from app.services.audit_service import AuditService
        AuditService.log_action(
            action='driver_location_updated',
            entity_type='buggy',
            entity_id=user.buggy.id,
            old_values={'location_id': old_location_id, 'location_name': old_location_name},
            new_values={'location_id': location_id, 'location_name': location.name},
            user_id=user.id,
            hotel_id=user.hotel_id
        )
        
        # Emit WebSocket events to admin
        from app.websocket import socketio
        
        # Emit location update event
        socketio.emit('driver_location_updated', {
            'buggy_id': user.buggy.id,
            'buggy_code': user.buggy.code,
            'driver_name': user.full_name,
            'location_id': location_id,
            'location_name': location.name,
            'status': user.buggy.status.value
        }, room=f'hotel_{user.hotel_id}_admin')
        
        # Emit buggy status changed event for full dashboard update
        socketio.emit('buggy_status_changed', {
            'buggy_id': user.buggy.id,
            'buggy_code': user.buggy.code,
            'buggy_icon': user.buggy.icon,
            'driver_id': user.id,
            'driver_name': user.full_name if user.full_name else user.username,
            'location_id': location_id,
            'location_name': location.name,
            'status': 'available',
            'reason': 'location_updated'
        }, room=f'hotel_{user.hotel_id}_admin')
        
        print(f'[LOCATION_UPDATE] Emitted events to hotel_{user.hotel_id}_admin')
        
        return jsonify({
            'success': True,
            'message': 'Konumunuz güncellendi',
            'buggy': user.buggy.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ==================== Driver Request Management ====================
@api_driver_bp.route('/api/driver/accept-request/<int:request_id>', methods=['POST'])
@require_login
def driver_accept_request(request_id):
    """Accept a PENDING buggy request"""
    try:
        user = SystemUser.query.get(session['user_id'])
        
        if not user:
            return jsonify({'error': 'Kullanıcı bulunamadı'}), 404
        
        if user.role != UserRole.DRIVER:
            return jsonify({'error': 'Sadece sürücüler talep kabul edebilir'}), 403
        
        if not user.buggy:
            return jsonify({'error': 'Size atanmış buggy bulunamadı. Lütfen yöneticinizle iletişime geçin.'}), 404

        # Use RequestService for validation + DB update + FCM (with row-level locking)
        from app.services.request_service import RequestService
        buggy_request = RequestService.accept_request(
            request_id=request_id,
            buggy_id=user.buggy.id,
            driver_id=user.id
        )

        # Emit WebSocket events
        from app.websocket import socketio
        
        # Notify guest
        socketio.emit('request_accepted', {
            'request_id': buggy_request.id,
            'buggy': user.buggy.to_dict(),
            'driver': user.to_dict()
        }, room=f'request_{buggy_request.id}')
        
        # Notify admin
        socketio.emit('request_status_changed', {
            'request_id': buggy_request.id,
            'status': 'accepted',
            'buggy_code': user.buggy.code
        }, room=f'hotel_{user.hotel_id}_admin')
        
        # Emit buggy status change
        socketio.emit('buggy_status_changed', {
            'buggy_id': user.buggy.id,
            'status': 'busy',
            'location_name': buggy_request.location.name if buggy_request.location else None
        }, room=f'hotel_{user.hotel_id}_admin')
        
        return jsonify({
            'success': True,
            'message': 'Talep kabul edildi',
            'request': {
                'id': buggy_request.id,
                'guest_name': buggy_request.guest_name,
                'room_number': buggy_request.room_number,
                'location': buggy_request.location.to_dict() if buggy_request.location else None,
                'status': buggy_request.status.value
            }
        }), 200
        
    except ForbiddenException as e:
        return jsonify({'error': e.message}), 403
    except BusinessLogicException as e:
        return jsonify({'error': e.message}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@api_driver_bp.route('/api/driver/complete-request/<int:request_id>', methods=['POST'])
@require_login
def driver_complete_request(request_id):
    """Mark an accepted request as completed"""
    try:
        user = SystemUser.query.get(session['user_id'])
        
        if not user:
            return jsonify({'error': 'Kullanıcı bulunamadı'}), 404
        
        if user.role != UserRole.DRIVER:
            return jsonify({'error': 'Sadece sürücüler talep tamamlayabilir'}), 403
        
        if not user.buggy:
            return jsonify({'error': 'Size atanmış buggy bulunamadı. Lütfen yöneticinizle iletişime geçin.'}), 404
        
        data = request.get_json() or {}
        completion_location_id = data.get('completion_location_id')
        
        # Use RequestService for validation + DB update + FCM
        from app.services.request_service import RequestService
        buggy_request = RequestService.complete_request(
            request_id=request_id,
            driver_id=user.id,
            current_location_id=completion_location_id
        )
        
        # Set completion_location_id on the request model
        if completion_location_id:
            buggy_request.completion_location_id = completion_location_id
            db.session.commit()
        
        # Emit WebSocket events
        from app.websocket import socketio
        socketio.emit('request_completed', {
            'request_id': buggy_request.id
        }, room=f'request_{buggy_request.id}')
        
        socketio.emit('request_status_changed', {
            'request_id': buggy_request.id,
            'status': 'completed'
        }, room=f'hotel_{user.hotel_id}_admin')
        
        # Buggy status değişikliğini bildir
        socketio.emit('buggy_status_changed', {
            'buggy_id': user.buggy.id,
            'status': 'available',
            'location_id': completion_location_id,
            'location_name': completion_location.name if completion_location_id and buggy_request.completion_location else None
        }, room=f'hotel_{user.hotel_id}_admin')
        
        return jsonify({
            'success': True,
            'message': 'Talep tamamlandı!',
            'request': {
                'id': buggy_request.id,
                'status': buggy_request.status.value,
                'completion_location_id': buggy_request.completion_location_id
            }
        }), 200
        
    except ForbiddenException as e:
        return jsonify({'error': e.message}), 403
    except BusinessLogicException as e:
        return jsonify({'error': e.message}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ==================== Driver Dashboard API ====================
@api_driver_bp.route('/api/driver/pending-requests', methods=['GET'])
# Rate limiter removed
@require_login
@require_role('driver')
def get_pending_requests():
    """Get all pending requests for driver's hotel"""
    try:
        user = SystemUser.query.get(session['user_id'])
        
        # Check if driver has assigned buggy
        if not user.buggy:
            return jsonify({'success': False, 'error': 'No buggy assigned'}), 400
        
        # Query PENDING requests for the hotel with location eager loading
        from sqlalchemy.orm import joinedload
        from app.models.request import RequestStatus
        
        pending_requests = BuggyRequest.query\
            .options(joinedload(BuggyRequest.location))\
            .filter_by(
                hotel_id=user.hotel_id,
                status=RequestStatus.PENDING
            )\
            .order_by(BuggyRequest.requested_at.desc())\
            .all()
        
        print(f'📋 Found {len(pending_requests)} pending requests for hotel {user.hotel_id}')
        
        # Serialize with location and guest info
        requests_data = [{
            'id': req.id,
            'guest_name': req.guest_name,
            'room_number': req.room_number,
            'phone_number': req.phone,
            'location': {
                'id': req.location.id,
                'name': req.location.name
            } if req.location else None,
            'requested_at': req.requested_at.isoformat() if req.requested_at else None,
            'notes': req.notes
        } for req in pending_requests]
        
        # Log fetch action for debugging
        try:
            from app.services.audit_service import AuditService
            AuditService.log_action(
                action='driver_fetched_pending_requests',
                entity_type='request',
                entity_id=None,
                new_values={'count': len(pending_requests)},
                user_id=user.id,
                hotel_id=user.hotel_id
            )
        except Exception as log_error:
            # Logging failure should not break the API
            print(f"Audit log failed: {log_error}")
        
        print(f'✅ Returning {len(requests_data)} pending requests to driver {user.username}')
        
        return jsonify({
            'success': True,
            'requests': requests_data,
            'total': len(requests_data)
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_driver_bp.route('/api/driver/active-request', methods=['GET'])
# Rate limiter removed
@require_login
@require_role('driver')
def get_active_request():
    """Get driver's currently active request"""
    try:
        user = SystemUser.query.get(session['user_id'])
        
        # Check if driver has assigned buggy
        if not user.buggy:
            return jsonify({'success': False, 'error': 'No buggy assigned'}), 400
        
        # Find accepted request assigned to this buggy
        from sqlalchemy.orm import joinedload
        from app.models.request import RequestStatus
        
        active_request = BuggyRequest.query\
            .options(joinedload(BuggyRequest.location))\
            .filter_by(
                buggy_id=user.buggy.id,
                status=RequestStatus.ACCEPTED
            )\
            .first()
        
        if not active_request:
            # Log fetch action
            try:
                from app.services.audit_service import AuditService
                AuditService.log_action(
                    action='driver_fetched_active_request',
                    entity_type='request',
                    entity_id=None,
                    new_values={'has_active': False},
                    user_id=user.id,
                    hotel_id=user.hotel_id
                )
            except Exception as log_error:
                print(f"Audit log failed: {log_error}")
            
            return jsonify({
                'success': True,
                'request': None
            }), 200
        
        # Serialize with full details
        request_data = {
            'id': active_request.id,
            'guest_name': active_request.guest_name,
            'room_number': active_request.room_number,
            'phone_number': active_request.phone,
            'location': {
                'id': active_request.location.id,
                'name': active_request.location.name
            } if active_request.location else None,
            'requested_at': active_request.requested_at.isoformat() if active_request.requested_at else None,
            'accepted_at': active_request.accepted_at.isoformat() if active_request.accepted_at else None,
            'notes': active_request.notes,
            'status': active_request.status.value
        }
        
        # Log fetch action
        try:
            from app.services.audit_service import AuditService
            AuditService.log_action(
                action='driver_fetched_active_request',
                entity_type='request',
                entity_id=active_request.id,
                new_values={'has_active': True, 'request_id': active_request.id},
                user_id=user.id,
                hotel_id=user.hotel_id
            )
        except Exception as log_error:
            print(f"Audit log failed: {log_error}")
        
        return jsonify({
            'success': True,
            'request': request_data
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_driver_bp.route('/api/driver/shuttle-info', methods=['GET'])
@api_driver_bp.route('/api/driver/buggy-info', methods=['GET'])  # Backward compatibility
@require_login
@require_role('driver')
def get_driver_shuttle_info():
    """Get driver's assigned shuttle information"""
    try:
        user = SystemUser.query.get(session['user_id'])
        
        # User kontrolü
        if not user:
            return jsonify({
                'success': False,
                'error': 'Kullanıcı bulunamadı'
            }), 404
        
        if not user.buggy:
            return jsonify({
                'success': False,
                'error': 'Size atanmış shuttle bulunamadı. Lütfen yöneticinizle iletişime geçin.'
            }), 404
        
        return jsonify({
            'success': True,
            'buggy': {  # Keep 'buggy' key for backward compatibility
                'id': user.buggy.id,
                'code': user.buggy.code,
                'model': user.buggy.model,
                'icon': user.buggy.icon,
                'status': user.buggy.status.value if hasattr(user.buggy.status, 'value') else str(user.buggy.status)
            }
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
