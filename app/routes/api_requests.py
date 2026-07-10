"""
Buggy Call - Requests API Routes
Extracted from api.py for modularity
"""
from flask import Blueprint, jsonify, request, session, current_app
from app import db, csrf
from app.models.user import SystemUser
from app.models.location import Location
from app.models.buggy import Buggy, BuggyStatus
from app.models.request import BuggyRequest, RequestStatus
from app.utils import require_login, require_role
from app.utils.exceptions import BuggyCallException, ForbiddenException, BusinessLogicException
from app.utils.logger import logger, log_request_event, log_websocket_event, log_error
from app.utils.helpers import RequestContext

api_requests_bp = Blueprint('api_requests', __name__)

# CSRF exempt for API endpoints
csrf.exempt(api_requests_bp)


# ==================== Requests API ====================

@api_requests_bp.route('/api/requests', methods=['POST'])
def create_request():
    """Create new buggy request (Guest - no auth required)"""
    try:
        data = request.get_json()

        # Validate required fields
        location_id = data.get('location_id')
        if not location_id:
            log_error('CREATE_REQUEST', 'Location ID eksik', data)
            return jsonify({'error': 'Location ID gerekli'}), 400

        # Use RequestService for validation + creation + audit + FCM
        from app.services.request_service import RequestService
        from app.utils.exceptions import BusinessLogicException, ValidationException

        buggy_request = RequestService.create_request(
            location_id=location_id,
            room_number=data.get('room_number'),
            guest_name=data.get('guest_name'),
            phone=data.get('phone'),
            notes=data.get('notes'),
            has_room=data.get('has_room', True)
        )

        location = buggy_request.location

        # Log request creation (route-level logging)
        log_request_event('CREATED', {
            'request_id': buggy_request.id,
            'guest_name': buggy_request.guest_name,
            'location': location.name,
            'hotel_id': location.hotel_id,
            'room_number': buggy_request.room_number
        })

        # Emit WebSocket event for drivers and admins
        from app import socketio

        # Prepare event data safely
        try:
            location_dict = location.to_dict()
        except Exception:
            location_dict = {
                'id': location.id,
                'name': location.name,
                'hotel_id': location.hotel_id
            }

        event_data = {
            'request_id': buggy_request.id,
            'guest_name': buggy_request.guest_name,
            'location': location_dict,
            'room_number': buggy_request.room_number,
            'phone_number': buggy_request.phone,
            'notes': buggy_request.notes,
            'requested_at': buggy_request.requested_at.isoformat()
        }

        # Send via SSE
        try:
            from app.routes.sse import send_to_all_drivers
            sent_count = send_to_all_drivers(location.hotel_id, 'new_request', event_data)
            log_websocket_event('SSE_NEW_REQUEST', {'request_id': buggy_request.id, 'drivers_notified': sent_count})
        except Exception as sse_error:
            log_error('SSE_NOTIFICATION', str(sse_error), {'request_id': buggy_request.id})

        # Send via WebSocket to DRIVERS
        try:
            drivers_room = f'hotel_{location.hotel_id}_drivers'
            socketio.emit('new_request', event_data, room=drivers_room, namespace='/')
            log_websocket_event('WS_NEW_REQUEST_DRIVERS', {'request_id': buggy_request.id, 'room': drivers_room})
        except Exception as ws_error:
            log_error('WS_NOTIFICATION_DRIVERS', str(ws_error), {'request_id': buggy_request.id})

        # Send via WebSocket to admin
        try:
            admin_room = f'hotel_{location.hotel_id}_admin'
            socketio.emit('new_request', event_data, room=admin_room, namespace='/')
            log_websocket_event('WS_NEW_REQUEST_ADMIN', {'request_id': buggy_request.id, 'room': admin_room})
        except Exception as ws_error:
            log_error('WS_NOTIFICATION_ADMIN', str(ws_error), {'request_id': buggy_request.id})

        # Note: FCM notification is already sent by RequestService.create_request()

        # Prepare response data safely
        try:
            request_dict = buggy_request.to_dict(include_relations=False)
        except Exception:
            request_dict = {
                'id': buggy_request.id,
                'status': buggy_request.status.value if buggy_request.status else 'PENDING',
                'guest_name': buggy_request.guest_name,
                'location_id': buggy_request.location_id
            }

        return jsonify({
            'success': True,
            'message': 'Buggy cagriniz alindi',
            'request_id': buggy_request.id,
            'request': request_dict
        }), 201

    except BusinessLogicException as e:
        return jsonify({'error': e.message, 'message': e.message}), 400
    except ValidationException as e:
        return jsonify({'error': e.message}), 400
    except Exception as e:
        db.session.rollback()
        import traceback
        error_details = {
            'error_type': type(e).__name__,
            'error_message': str(e),
            'traceback': traceback.format_exc(),
            'request_data': data if 'data' in locals() else 'N/A'
        }
        log_error('CREATE_REQUEST_FAILED', str(e), error_details)
        return jsonify({
            'error': str(e),
            'error_type': type(e).__name__,
            'message': 'Request olusturulamadi. Lutfen tekrar deneyin.'
        }), 500


@api_requests_bp.route('/api/requests', methods=['GET'])
@require_login
def get_requests():
    """Get all requests (Admin/Driver)"""
    try:
        from sqlalchemy.orm import joinedload

        user = SystemUser.query.get(session['user_id'])

        # Get query parameters
        status_str = request.args.get('status')
        buggy_id = request.args.get('buggy_id')

        # Build query with eager loading (N+1 problemi cozumu)
        query = BuggyRequest.query.filter_by(hotel_id=user.hotel_id)\
            .options(
                joinedload(BuggyRequest.location),
                joinedload(BuggyRequest.completion_location),
                joinedload(BuggyRequest.buggy).joinedload(Buggy.current_location),
                joinedload(BuggyRequest.buggy).joinedload(Buggy.driver_associations),
                joinedload(BuggyRequest.accepted_by_driver)
            )

        # Handle status filter - convert string to enum
        if status_str:
            try:
                status_enum = RequestStatus(status_str.upper())
                query = query.filter_by(status=status_enum)
            except ValueError:
                pass

        if buggy_id:
            query = query.filter_by(buggy_id=buggy_id)

        # Get requests
        requests = query.order_by(BuggyRequest.requested_at.desc()).all()

        result = []
        for req in requests:
            try:
                req_dict = req.to_dict(include_relations=False)

                # Add location info safely
                try:
                    if req.location:
                        req_dict['location'] = req.location.to_dict()
                except Exception:
                    req_dict['location'] = None

                # Add completion location info safely
                try:
                    if req.completion_location:
                        req_dict['completion_location'] = req.completion_location.to_dict()
                except Exception:
                    req_dict['completion_location'] = None

                # Add buggy info safely
                try:
                    if req.buggy:
                        req_dict['buggy'] = req.buggy.to_dict()
                except Exception:
                    req_dict['buggy'] = None

                # Add driver info safely
                try:
                    if req.accepted_by_driver:
                        req_dict['driver'] = {
                            'id': req.accepted_by_driver.id,
                            'username': req.accepted_by_driver.username,
                            'full_name': req.accepted_by_driver.full_name
                        }
                    elif req.buggy and req.buggy.driver:
                        req_dict['driver'] = {
                            'id': req.buggy.driver.id,
                            'username': req.buggy.driver.username,
                            'full_name': req.buggy.driver.full_name
                        }
                except Exception:
                    req_dict['driver'] = None

                # Add performance metrics with _seconds suffix for frontend compatibility
                req_dict['response_time_seconds'] = req.response_time

                # Completion time - Dinamik hesaplama (requested_at -> completed_at)
                completion_time_seconds = None
                if req.completed_at and req.requested_at:
                    delta = req.completed_at - req.requested_at
                    completion_time_seconds = int(delta.total_seconds())
                elif req.completion_time:
                    completion_time_seconds = req.completion_time

                req_dict['completion_time_seconds'] = completion_time_seconds

                result.append(req_dict)
            except Exception as req_error:
                log_error('GET_REQUESTS_ITEM', str(req_error), {'request_id': req.id})
                continue

        return jsonify({
            'success': True,
            'requests': result
        }), 200
    except Exception as e:
        current_app.logger.error(f'Error in get_requests: {str(e)}')
        return jsonify({'error': str(e)}), 500


@api_requests_bp.route('/api/requests/<int:request_id>', methods=['GET'])
def get_request(request_id):
    """Get single request (Guest - no auth required)"""
    try:
        buggy_request = BuggyRequest.query.get(request_id)

        if not buggy_request:
            return jsonify({'error': 'Talep bulunamadi'}), 404

        # Safe to_dict call
        try:
            req_dict = buggy_request.to_dict(include_relations=False)
        except Exception as dict_error:
            log_error('GET_REQUEST_TO_DICT', str(dict_error), {'request_id': request_id})
            req_dict = {
                'id': buggy_request.id,
                'status': buggy_request.status.value if buggy_request.status else 'PENDING'
            }

        # Add location info safely
        try:
            if buggy_request.location:
                req_dict['location'] = buggy_request.location.to_dict()
        except Exception:
            req_dict['location'] = None

        # Add buggy info safely
        try:
            if buggy_request.buggy:
                req_dict['buggy'] = {
                    'id': buggy_request.buggy.id,
                    'code': buggy_request.buggy.code,
                    'icon': buggy_request.buggy.icon
                }
        except Exception:
            req_dict['buggy'] = None

        return jsonify({
            'success': True,
            'request': req_dict
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_requests_bp.route('/api/requests/<int:request_id>/accept', methods=['PUT', 'POST'])
@require_login
def accept_request(request_id):
    """Accept request (Driver)"""
    try:
        user = SystemUser.query.get(session['user_id'])

        # Get driver's buggy via association
        buggy = user.buggy
        if not buggy:
            log_error('ACCEPT_REQUEST', 'Buggy bulunamadi', {'user_id': user.id, 'request_id': request_id})
            return jsonify({'error': 'Bu kullaniciya atanmis buggy bulunamadi'}), 404

        # Use RequestService for validation + DB update + FCM
        from app.services.request_service import RequestService
        buggy_request = RequestService.accept_request(
            request_id=request_id,
            buggy_id=buggy.id,
            driver_id=user.id
        )

        # Emit WebSocket event for guest
        from app import socketio
        socketio.emit('request_accepted', {
            'request_id': buggy_request.id,
            'buggy': buggy.to_dict(),
            'accepted_at': buggy_request.accepted_at.isoformat()
        }, room=f'request_{request_id}')

        # Emit to other drivers that this request is taken (via SSE)
        from app.routes.sse import send_to_all_drivers
        send_to_all_drivers(buggy_request.hotel_id, 'request_taken', {
            'request_id': buggy_request.id
        })

        # Emit via WebSocket for backward compatibility
        socketio.emit('request_taken', {
            'request_id': buggy_request.id
        }, room=f'hotel_{buggy_request.hotel_id}_drivers')

        # Emit buggy status update for real-time dashboard
        try:
            from app.services.buggy_service import BuggyService
            BuggyService.emit_buggy_status_update(buggy.id, buggy_request.hotel_id)
        except Exception:
            pass

        return jsonify({
            'success': True,
            'message': 'Talep kabul edildi',
            'request': buggy_request.to_dict()
        }), 200

    except ForbiddenException as e:
        return jsonify({'error': e.message}), 403
    except BusinessLogicException as e:
        return jsonify({'error': e.message}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@api_requests_bp.route('/api/requests/<int:request_id>/complete', methods=['PUT', 'POST'])
@require_login
@require_role('driver')
def complete_request(request_id):
    """Complete a buggy request and update buggy location"""
    try:
        user = SystemUser.query.get(session['user_id'])

        # Check if driver has assigned buggy
        if not user.buggy:
            return jsonify({'success': False, 'error': 'No buggy assigned'}), 400

        data = request.get_json() or {}
        current_location_id = data.get('current_location_id')
        notes = data.get('notes', '')

        # Validate current_location_id is provided
        if not current_location_id:
            return jsonify({'success': False, 'error': 'Current location is required'}), 400

        # Validate notes length
        if notes and len(notes) > 500:
            return jsonify({'success': False, 'error': 'Notes must be 500 characters or less'}), 400

        # Verify location exists and belongs to hotel
        location = Location.query.get(current_location_id)
        if not location:
            return jsonify({'success': False, 'error': 'Invalid location'}), 400

        if location.hotel_id != user.hotel_id:
            return jsonify({'success': False, 'error': 'Invalid location'}), 400

        # Get the request
        buggy_request = BuggyRequest.query.get(request_id)
        if not buggy_request:
            return jsonify({'success': False, 'error': 'Request not found'}), 404

        # Verify request is assigned to driver's buggy
        if buggy_request.buggy_id != user.buggy.id:
            return jsonify({'success': False, 'error': 'Request not assigned to your buggy'}), 403

        # Verify request status is ACCEPTED
        if buggy_request.status != RequestStatus.ACCEPTED:
            return jsonify({'success': False, 'error': 'Request is not in accepted status'}), 400

        # Use RequestService for completion (handles transaction, audit, websocket)
        from app.services.request_service import RequestService

        try:
            buggy_request = RequestService.complete_request(
                request_id=request_id,
                driver_id=user.id,
                current_location_id=current_location_id,
                notes=notes
            )

            # Return success response with buggy status and location
            return jsonify({
                'success': True,
                'message': 'Request completed successfully',
                'request': {
                    'id': buggy_request.id,
                    'status': buggy_request.status.value,
                    'completed_at': buggy_request.completed_at.isoformat() if buggy_request.completed_at else None
                },
                'buggy': {
                    'id': user.buggy.id,
                    'status': user.buggy.status.value,
                    'current_location': {
                        'id': location.id,
                        'name': location.name
                    }
                }
            }), 200

        except BuggyCallException as e:
            return jsonify({'success': False, 'error': str(e)}), e.status_code

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Completion failed'}), 500


@api_requests_bp.route('/api/requests/<int:request_id>/cancel', methods=['PUT', 'POST'])
@require_login
def cancel_request(request_id):
    """Cancel request (Admin/System only - Guests cannot cancel)"""
    try:
        # Sadece admin ve sistem kullanicilari iptal edebilir
        current_user = RequestContext.get_current_user()
        if not current_user or current_user.role != UserRole.ADMIN:
            return jsonify({
                'error': 'Yetkisiz islem. Misafirler talep iptal edemez.',
                'message': 'Talebiniz 1 saat icinde yanitlanmazsa otomatik olarak isaretlenecektir.'
            }), 403

        buggy_request = BuggyRequest.query.get(request_id)
        if not buggy_request:
            return jsonify({'error': 'Talep bulunamadi'}), 404

        if buggy_request.status == RequestStatus.COMPLETED:
            return jsonify({'error': 'Tamamlanmis talep iptal edilemez'}), 400

        if buggy_request.status == RequestStatus.CANCELLED:
            return jsonify({'error': 'Bu talep zaten iptal edilmis'}), 400

        # Update request
        from app.models import get_current_timestamp
        old_status = buggy_request.status
        buggy_request.status = RequestStatus.CANCELLED
        buggy_request.cancelled_at = get_current_timestamp()
        buggy_request.cancelled_by = current_user.id

        # If was accepted, free up the buggy
        if old_status == RequestStatus.ACCEPTED and buggy_request.buggy:
            buggy_request.buggy.status = BuggyStatus.AVAILABLE

        db.session.commit()

        # Emit WebSocket event
        from app import socketio
        socketio.emit('request_cancelled', {
            'request_id': buggy_request.id
        }, room=f'request_{request_id}')

        if old_status == RequestStatus.ACCEPTED:
            socketio.emit('request_cancelled', {
                'request_id': buggy_request.id
            }, room=f'hotel_{buggy_request.hotel_id}_drivers')

        return jsonify({
            'success': True,
            'message': 'Talep iptal edildi'
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
