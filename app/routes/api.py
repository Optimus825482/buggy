"""
Buggy Call - API Routes
Powered by Erkan ERDEM
Updated with Service Layer & Security
"""
from flask import Blueprint, jsonify, request, session
from app import db, limiter, csrf
from app.models.user import SystemUser, UserRole
from app.models.location import Location
from app.models.buggy import Buggy, BuggyStatus
from app.models.request import BuggyRequest, RequestStatus
from app.services import LocationService, BuggyService, RequestService, AuthService
from app.utils import APIResponse, require_login, require_role, validate_schema
from app.utils.exceptions import BuggyCallException
from app.schemas import (
    LocationCreateSchema, LocationUpdateSchema,
    BuggyCreateSchema, BuggyUpdateSchema,
    BuggyRequestCreateSchema, BuggyRequestAcceptSchema,
    UserCreateSchema
)
from datetime import datetime
import qrcode
import io
import base64

api_bp = Blueprint('api', __name__)

# Exempt API endpoints from CSRF (using JWT/session instead)
csrf.exempt(api_bp)


# ==================== Health & Info ====================
@api_bp.route('/health')
def health():
    """Basic health check endpoint - always returns 200"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'message': 'Buggy Call API is running'
    }), 200


@api_bp.route('/health/ready')
def health_ready():
    """Detailed readiness check with database validation"""
    try:
        from sqlalchemy import inspect
        
        # Test database connection
        db.session.execute('SELECT 1')
        
        # Get table information
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        
        # Check critical tables
        critical_tables = ['hotel', 'system_user', 'location', 'buggy', 'buggy_request']
        critical_tables_ok = all(table in tables for table in critical_tables)
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'checks': {
                'database': {
                    'status': 'healthy',
                    'table_count': len(tables),
                    'critical_tables_ok': critical_tables_ok
                },
                'application': {
                    'status': 'healthy'
                }
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(e),
            'checks': {
                'database': {
                    'status': 'unhealthy',
                    'error': str(e)
                }
            }
        }), 503


@api_bp.route('/version')
def version():
    """API version"""
    return jsonify({
        'version': '1.0.0',
        'name': 'Buggy Call API',
        'author': 'Erkan ERDEM'
    }), 200


# ==================== Locations API ====================
@api_bp.route('/locations', methods=['GET'])
@limiter.limit("30 per minute")
def get_locations():
    """Get all locations (Public - no auth required for guests)"""
    try:
        # Get hotel_id from query params or session
        hotel_id = request.args.get('hotel_id', type=int)
        if not hotel_id and 'user_id' in session:
            from app.utils.helpers import RequestContext
            hotel_id = RequestContext.get_current_hotel_id()
        hotel_id = hotel_id or 1  # Default to hotel_id=1
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        result = LocationService.get_all_locations(
            hotel_id=hotel_id,
            include_inactive=False,
            page=page,
            per_page=per_page
        )
        
        # Return with both 'items' and 'locations' for backward compatibility
        response_data = result.copy()
        response_data['locations'] = result['items']
        
        return APIResponse.success(response_data)
    except BuggyCallException as e:
        return jsonify(e.to_dict()), e.status_code
    except Exception as e:
        return APIResponse.error(str(e), 500)


@api_bp.route('/locations/<int:location_id>', methods=['GET'])
@limiter.limit("30 per minute")
def get_location(location_id):
    """Get single location (Public - no auth required for guests)"""
    try:
        location = LocationService.get_location(location_id)
        return APIResponse.success({'location': location.to_dict()})
    except BuggyCallException as e:
        return jsonify(e.to_dict()), e.status_code
    except Exception as e:
        return APIResponse.error(str(e), 500)


@api_bp.route('/locations', methods=['POST'])
@require_login
def create_location():
    """Create new location"""
    try:
        from app.config import Config
        
        user = SystemUser.query.get(session['user_id'])
        data = request.get_json()
        
        # Validate required fields
        if not data.get('name'):
            return jsonify({'error': 'Lokasyon adı gerekli'}), 400
        
        # Auto-assign display_order if not provided or is 0
        if 'display_order' not in data or data['display_order'] is None or data['display_order'] == 0:
            max_order = db.session.query(db.func.max(Location.display_order)).filter_by(hotel_id=user.hotel_id).scalar() or 0
            data['display_order'] = max_order + 1
        
        # Create location first to get the ID
        location = Location(
            hotel_id=user.hotel_id,
            name=data['name'],
            description=data.get('description', ''),
            qr_code_data='',  # Temporary, will be updated after we have the ID
            latitude=data.get('latitude'),
            longitude=data.get('longitude'),
            is_active=True,
            display_order=data['display_order']
        )
        
        db.session.add(location)
        db.session.flush()  # Get the location ID without committing
        
        # Generate QR code data as URL with location ID
        # Priority: 1) Railway URL env var, 2) Config BASE_URL, 3) Request host
        import os
        
        railway_domain = os.getenv('RAILWAY_PUBLIC_DOMAIN')
        railway_static_url = os.getenv('RAILWAY_STATIC_URL')
        
        if railway_domain:
            base_url = f"https://{railway_domain}"
        elif railway_static_url:
            base_url = railway_static_url.rstrip('/')
        elif current_app.config.get('BASE_URL') and current_app.config.get('BASE_URL') != 'http://localhost:5000':
            base_url = current_app.config.get('BASE_URL')
        else:
            base_url = request.host_url.rstrip('/')
        
        qr_code_data = f"{base_url}/guest/call?location={location.id}"
        location.qr_code_data = qr_code_data
        
        # Generate QR code image
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_code_data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_base64 = base64.b64encode(buffer.getvalue()).decode()
        location.qr_code_image = f"data:image/png;base64,{img_base64}"
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Lokasyon başarıyla oluşturuldu',
            'location': location.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@api_bp.route('/locations/<int:location_id>', methods=['PUT'])
@require_login
def update_location(location_id):
    """Update location"""
    try:
        user = SystemUser.query.get(session['user_id'])
        location = Location.query.filter_by(id=location_id, hotel_id=user.hotel_id).first()
        
        if not location:
            return jsonify({'error': 'Lokasyon bulunamadı'}), 404
        
        data = request.get_json()
        
        # Update fields
        if 'name' in data:
            location.name = data['name']
        if 'description' in data:
            location.description = data['description']
        if 'latitude' in data:
            location.latitude = data['latitude']
        if 'longitude' in data:
            location.longitude = data['longitude']
        if 'is_active' in data:
            location.is_active = data['is_active']
        if 'display_order' in data:
            location.display_order = data['display_order']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Lokasyon başarıyla güncellendi',
            'location': location.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@api_bp.route('/locations/<int:location_id>', methods=['DELETE'])
@require_login
def delete_location(location_id):
    """Delete location"""
    try:
        user = SystemUser.query.get(session['user_id'])
        location = Location.query.filter_by(id=location_id, hotel_id=user.hotel_id).first()

        if not location:
            return jsonify({'error': 'Lokasyon bulunamadı'}), 404

        # Check if location has active requests
        active_requests = BuggyRequest.query.filter_by(
            location_id=location_id
        ).filter(
            BuggyRequest.status.in_([RequestStatus.PENDING, RequestStatus.ACCEPTED])
        ).count()
        
        if active_requests > 0:
            return jsonify({
                'error': f'Bu lokasyonda {active_requests} aktif talep var. Önce talepleri tamamlayın veya iptal edin.'
            }), 400

        # Check if any buggy is currently at this location
        buggies_at_location = Buggy.query.filter_by(current_location_id=location_id).count()
        if buggies_at_location > 0:
            return jsonify({
                'error': f'Bu lokasyonda {buggies_at_location} buggy bulunuyor. Önce buggy\'leri başka lokasyona taşıyın.'
            }), 400

        db.session.delete(location)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Lokasyon başarıyla silindi'
        }), 200
    except Exception as e:
        db.session.rollback()
        import traceback
        print(f"Error deleting location {location_id}: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': f'Lokasyon silinirken hata oluştu: {str(e)}'}), 500


@api_bp.route('/locations/<int:location_id>/qr-code', methods=['GET'])
def download_qr_code(location_id):
    """Download QR code image as PNG"""
    try:
        from flask import send_file

        location = Location.query.get(location_id)
        if not location:
            return jsonify({'error': 'Lokasyon bulunamadı'}), 404

        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5, error_correction=qrcode.constants.ERROR_CORRECT_H)
        qr.add_data(location.qr_code_data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        # Save to BytesIO
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)

        return send_file(
            buffer,
            mimetype='image/png',
            as_attachment=True,
            download_name=f'QR_{location.name.replace(" ", "_")}_{location.qr_code_data}.png'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== Buggies API ====================
@api_bp.route('/buggies', methods=['GET'])
@require_login
def get_buggies():
    """Get all buggies"""
    try:
        user = SystemUser.query.get(session['user_id'])
        buggies = Buggy.query.filter_by(hotel_id=user.hotel_id).all()
        
        result = []
        for buggy in buggies:
            buggy_dict = buggy.to_dict()
            # to_dict() already includes driver_name and driver_id from get_active_driver methods
            # Just add current_location_name for backward compatibility
            if buggy.current_location_id:
                location = Location.query.get(buggy.current_location_id)
                buggy_dict['current_location_name'] = location.name if location else None
            else:
                buggy_dict['current_location_name'] = None
            
            result.append(buggy_dict)
        
        return jsonify({
            'success': True,
            'buggies': result
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/buggies', methods=['POST'])
@require_login
def create_buggy():
    """Create new buggy (driver assignment is optional)"""
    try:
        from app.models.user import UserRole
        from app.models.buggy_driver import BuggyDriver
        
        user = SystemUser.query.get(session['user_id'])
        data = request.get_json()
        
        if not data.get('code'):
            return jsonify({'error': 'Buggy kodu gerekli'}), 400
        
        buggy_code = data['code']
        driver_id = data.get('driver_id')  # Optional
        
        # Check if buggy code already exists
        existing_buggy = Buggy.query.filter_by(hotel_id=user.hotel_id, code=buggy_code).first()
        if existing_buggy:
            return jsonify({'error': 'Bu buggy kodu zaten kullanılıyor'}), 400
        
        # Create buggy without driver
        buggy = Buggy(
            hotel_id=user.hotel_id,
            code=buggy_code,
            license_plate=data.get('license_plate'),
            status=BuggyStatus.OFFLINE,
            driver_id=None  # Will be managed through buggy_drivers table
        )
        
        db.session.add(buggy)
        db.session.flush()  # Get buggy ID
        
        # If driver_id provided, create association
        driver_info = None
        if driver_id:
            # Verify driver exists
            driver = SystemUser.query.filter_by(
                id=driver_id,
                hotel_id=user.hotel_id,
                role=UserRole.DRIVER
            ).first()
            
            if driver:
                # Create buggy-driver association
                association = BuggyDriver(
                    buggy_id=buggy.id,
                    driver_id=driver_id,
                    is_active=False,  # Will be activated when driver logs in
                    is_primary=True,
                    assigned_at=datetime.utcnow()
                )
                db.session.add(association)
                
                driver_info = {
                    'id': driver.id,
                    'username': driver.username,
                    'full_name': driver.full_name
                }
        
        db.session.commit()
        
        response = {
            'success': True,
            'message': 'Buggy başarıyla oluşturuldu',
            'buggy': buggy.to_dict()
        }
        
        if driver_info:
            response['driver'] = driver_info
            response['message'] = 'Buggy ve sürücü ataması başarıyla oluşturuldu'
        
        return jsonify(response), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@api_bp.route('/buggies/<int:buggy_id>', methods=['GET'])
@require_login
def get_buggy(buggy_id):
    """Get single buggy"""
    try:
        user = SystemUser.query.get(session['user_id'])
        buggy = Buggy.query.filter_by(id=buggy_id, hotel_id=user.hotel_id).first()
        
        if not buggy:
            return jsonify({'error': 'Buggy bulunamadı'}), 404
        
        buggy_dict = buggy.to_dict()
        # Add driver name
        if buggy.driver:
            # Use full_name if available, otherwise use username
            buggy_dict['driver_name'] = buggy.driver.full_name if buggy.driver.full_name else buggy.driver.username
        else:
            buggy_dict['driver_name'] = None
        
        return jsonify({
            'success': True,
            'buggy': buggy_dict
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/buggies/<int:buggy_id>', methods=['PUT'])
@require_login
def update_buggy(buggy_id):
    """Update buggy"""
    try:
        user = SystemUser.query.get(session['user_id'])
        buggy = Buggy.query.filter_by(id=buggy_id, hotel_id=user.hotel_id).first()
        
        if not buggy:
            return jsonify({'error': 'Buggy bulunamadı'}), 404
        
        data = request.get_json()
        
        if 'code' in data:
            buggy.code = data['code']
        if 'model' in data:
            buggy.model = data['model']
        if 'license_plate' in data:
            buggy.license_plate = data['license_plate']
        if 'status' in data:
            buggy.status = BuggyStatus(data['status'])
        # Note: driver_id is now managed through buggy_drivers table, not directly on buggy
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Buggy başarıyla güncellendi',
            'buggy': buggy.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@api_bp.route('/buggies/<int:buggy_id>', methods=['DELETE'])
@require_login
def delete_buggy(buggy_id):
    """Delete buggy"""
    try:
        user = SystemUser.query.get(session['user_id'])
        buggy = Buggy.query.filter_by(id=buggy_id, hotel_id=user.hotel_id).first()
        
        if not buggy:
            return jsonify({'error': 'Buggy bulunamadı'}), 404
        
        db.session.delete(buggy)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Buggy başarıyla silindi'
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ==================== Drivers API ====================
@api_bp.route('/drivers', methods=['GET'])
@require_login
def get_drivers():
    """Get all drivers"""
    try:
        user = SystemUser.query.get(session['user_id'])
        from app.models.user import UserRole
        drivers = SystemUser.query.filter_by(hotel_id=user.hotel_id, role=UserRole.DRIVER, is_active=True).all()
        
        return jsonify({
            'success': True,
            'drivers': [{
                'id': d.id, 
                'username': d.username, 
                'full_name': d.full_name if d.full_name else d.username
            } for d in drivers]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== Requests API ====================
@api_bp.route('/requests', methods=['POST'])
def create_request():
    """Create new buggy request (Guest - no auth required)"""
    try:
        data = request.get_json()
        
        # Validate required fields
        location_id = data.get('location_id')
        if not location_id:
            return jsonify({'error': 'Location ID gerekli'}), 400
        
        # Get location to verify and get hotel_id
        location = Location.query.get(location_id)
        if not location:
            return jsonify({'error': 'Geçersiz lokasyon'}), 404
        
        # Create request
        buggy_request = BuggyRequest(
            hotel_id=location.hotel_id,
            location_id=location_id,
            guest_name=data.get('guest_name'),
            room_number=data.get('room_number'),
            phone=data.get('phone'),
            notes=data.get('notes'),
            guest_device_id=request.remote_addr,  # Use IP as guest identifier
            status='pending',
            requested_at=datetime.utcnow()
        )
        
        db.session.add(buggy_request)
        db.session.commit()
        
        # Emit WebSocket event for drivers and admins
        from app import socketio
        event_data = {
            'request_id': buggy_request.id,
            'guest_name': buggy_request.guest_name,
            'location': location.to_dict(),
            'room_number': buggy_request.room_number,
            'phone_number': buggy_request.phone,
            'notes': buggy_request.notes,
            'requested_at': buggy_request.requested_at.isoformat()
        }
        
        # Send to drivers
        socketio.emit('new_request', event_data, room=f'hotel_{location.hotel_id}_drivers')
        
        # Send to admins
        socketio.emit('new_request', event_data, room='admin')
        
        return jsonify({
            'success': True,
            'message': 'Buggy çağrınız alındı',
            'request_id': buggy_request.id,
            'request': buggy_request.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@api_bp.route('/requests', methods=['GET'])
@require_login
def get_requests():
    """Get all requests (Admin/Driver)"""
    try:
        user = SystemUser.query.get(session['user_id'])
        
        # Get query parameters
        status = request.args.get('status')
        buggy_id = request.args.get('buggy_id')
        
        # Build query
        query = BuggyRequest.query.filter_by(hotel_id=user.hotel_id)
        
        if status:
            query = query.filter_by(status=status)
        
        if buggy_id:
            query = query.filter_by(buggy_id=buggy_id)
        
        # Get requests
        requests = query.order_by(BuggyRequest.requested_at.desc()).all()
        
        result = []
        for req in requests:
            req_dict = req.to_dict()
            # Add location info
            if req.location:
                req_dict['location'] = req.location.to_dict()
            # Add buggy info
            if req.buggy:
                req_dict['buggy'] = req.buggy.to_dict()
            result.append(req_dict)
        
        return jsonify({
            'success': True,
            'requests': result
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/requests/<int:request_id>', methods=['GET'])
def get_request(request_id):
    """Get single request (Guest - no auth required)"""
    try:
        buggy_request = BuggyRequest.query.get(request_id)
        
        if not buggy_request:
            return jsonify({'error': 'Talep bulunamadı'}), 404
        
        req_dict = buggy_request.to_dict()
        # Add location info
        if buggy_request.location:
            req_dict['location'] = buggy_request.location.to_dict()
        # Add buggy info
        if buggy_request.buggy:
            req_dict['buggy'] = {
                'name': buggy_request.buggy.name,
                'plate_number': buggy_request.buggy.plate_number
            }
        
        return jsonify({
            'success': True,
            'request': req_dict
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/requests/<int:request_id>/accept', methods=['PUT', 'POST'])
@require_login
def accept_request(request_id):
    """Accept request (Driver)"""
    try:
        user = SystemUser.query.get(session['user_id'])
        
        # Get driver's buggy
        buggy = Buggy.query.filter_by(driver_id=user.id).first()
        if not buggy:
            return jsonify({'error': 'Bu kullanıcıya atanmış buggy bulunamadı'}), 404
        
        # Get request
        buggy_request = BuggyRequest.query.get(request_id)
        if not buggy_request:
            return jsonify({'error': 'Talep bulunamadı'}), 404
        
        if buggy_request.status != 'pending':
            return jsonify({'error': 'Bu talep zaten işleme alınmış'}), 400
        
        # Update request
        buggy_request.status = 'accepted'
        buggy_request.buggy_id = buggy.id
        buggy_request.accepted_at = datetime.utcnow()
        
        if buggy_request.requested_at:
            delta = buggy_request.accepted_at - buggy_request.requested_at
            buggy_request.response_time_seconds = int(delta.total_seconds())
        
        # Update buggy status
        buggy.status = BuggyStatus.BUSY
        
        db.session.commit()
        
        # Emit WebSocket event for guest
        from app import socketio
        socketio.emit('request_accepted', {
            'request_id': buggy_request.id,
            'buggy': buggy.to_dict(),
            'accepted_at': buggy_request.accepted_at.isoformat()
        }, room=f'request_{request_id}')
        
        # Emit to other drivers that this request is taken
        socketio.emit('request_taken', {
            'request_id': buggy_request.id
        }, room=f'hotel_{buggy_request.hotel_id}_drivers')
        
        return jsonify({
            'success': True,
            'message': 'Talep kabul edildi',
            'request': buggy_request.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@api_bp.route('/requests/<int:request_id>/complete', methods=['PUT', 'POST'])
@limiter.limit("30 per minute")
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
        from app.utils.exceptions import BuggyCallException
        
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


@api_bp.route('/requests/<int:request_id>/cancel', methods=['PUT', 'POST'])
def cancel_request(request_id):
    """Cancel request (Guest or Admin)"""
    try:
        buggy_request = BuggyRequest.query.get(request_id)
        if not buggy_request:
            return jsonify({'error': 'Talep bulunamadı'}), 404
        
        if buggy_request.status == 'completed':
            return jsonify({'error': 'Tamamlanmış talep iptal edilemez'}), 400
        
        if buggy_request.status == 'cancelled':
            return jsonify({'error': 'Bu talep zaten iptal edilmiş'}), 400
        
        # Update request
        old_status = buggy_request.status
        buggy_request.status = 'cancelled'
        buggy_request.cancelled_at = datetime.utcnow()
        
        # If was accepted, free up the buggy
        if old_status == 'accepted' and buggy_request.buggy:
            buggy_request.buggy.status = BuggyStatus.AVAILABLE
        
        db.session.commit()
        
        # Emit WebSocket event
        from app import socketio
        socketio.emit('request_cancelled', {
            'request_id': buggy_request.id
        }, room=f'request_{request_id}')
        
        if old_status == 'accepted':
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


# ==================== Users API ====================
@api_bp.route('/users/<int:user_id>/reset-password', methods=['POST'])
@require_login
def reset_user_password(user_id):
    """Reset user password to temporary password (Admin only)"""
    try:
        # Check if user is admin
        admin = SystemUser.query.get(session['user_id'])
        if not admin or admin.role != UserRole.ADMIN:
            return jsonify({'error': 'Bu işlem için yetkiniz yok'}), 403
        
        # Get target user
        target_user = SystemUser.query.filter_by(id=user_id, hotel_id=admin.hotel_id).first()
        if not target_user:
            return jsonify({'error': 'Kullanıcı bulunamadı'}), 404
        
        # Generate temporary password: username + "123*"
        temp_password = f"{target_user.username}123*"
        
        # Reset password
        target_user.set_password(temp_password)
        target_user.must_change_password = True
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Şifre sıfırlandı',
            'username': target_user.username,
            'temp_password': temp_password
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@api_bp.route('/users', methods=['POST'])
@require_login
def create_user():
    """Create new user (Admin only)"""
    try:
        # Check if user is admin
        user = SystemUser.query.get(session['user_id'])
        if not user or user.role != UserRole.ADMIN:
            return jsonify({'error': 'Bu işlem için yetkiniz yok'}), 403
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['username', 'password', 'role']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'{field} alanı zorunludur'}), 400
        
        # Validate role
        valid_roles = ['admin', 'driver']
        if data['role'] not in valid_roles:
            return jsonify({'error': 'Geçersiz rol'}), 400
        
        # Convert string role to Enum
        role_enum = UserRole.ADMIN if data['role'] == 'admin' else UserRole.DRIVER
        
        # Check if username already exists
        existing_user = SystemUser.query.filter_by(username=data['username']).first()
        if existing_user:
            return jsonify({'error': 'Bu kullanıcı adı zaten kullanılıyor'}), 400
        
        # Create new user
        new_user = SystemUser(
            username=data['username'],
            role=role_enum,
            hotel_id=user.hotel_id,  # Same hotel as admin
            full_name=f"{data.get('first_name', '')} {data.get('last_name', '')}".strip() or data['username'],
            email=data.get('email'),
            phone=data.get('phone'),
            is_active=True
        )
        new_user.set_password(data['password'])
        
        db.session.add(new_user)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Kullanıcı başarıyla oluşturuldu',
            'user': {
                'id': new_user.id,
                'username': new_user.username,
                'role': new_user.role.value,
                'full_name': new_user.full_name,
                'email': new_user.email,
                'phone': new_user.phone
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ==================== Push Notifications ====================
@api_bp.route('/push/vapid-public-key', methods=['GET'])
def get_vapid_public_key():
    """Get VAPID public key for push notifications"""
    from app.services.notification_service import NotificationService
    
    public_key = NotificationService.VAPID_PUBLIC_KEY
    if not public_key:
        return jsonify({'error': 'VAPID keys not configured'}), 500
    
    return jsonify({'public_key': public_key})


@api_bp.route('/push/subscribe', methods=['POST'])
@require_login
@limiter.limit("10 per minute")
def subscribe_push():
    """Subscribe to push notifications"""
    try:
        data = request.get_json()
        
        if not data or 'subscription' not in data:
            return jsonify({'error': 'Subscription bilgisi gerekli'}), 400
        
        # Get current user
        user = SystemUser.query.get(session['user_id'])
        if not user:
            return jsonify({'error': 'Kullanıcı bulunamadı'}), 404
        
        # Store subscription info (you may want to add a push_subscription field to SystemUser model)
        # For now, we'll store it in a JSON field or separate table
        import json
        user.push_subscription = json.dumps(data['subscription'])
        db.session.commit()
        
        # Log push subscription
        from app.services.audit_service import AuditService
        AuditService.log_action(
            action='push_notification_subscribed',
            entity_type='notification',
            entity_id=user.id,
            new_values={'user_id': user.id},
            user_id=user.id,
            hotel_id=user.hotel_id
        )
        
        return jsonify({
            'success': True,
            'message': 'Push bildirimleri aktif edildi'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@api_bp.route('/push/unsubscribe', methods=['POST'])
@require_login
def unsubscribe_push():
    """Unsubscribe from push notifications"""
    try:
        user = SystemUser.query.get(session['user_id'])
        if not user:
            return jsonify({'error': 'Kullanıcı bulunamadı'}), 404
        
        user.push_subscription = None
        db.session.commit()
        
        # Log push unsubscription
        from app.services.audit_service import AuditService
        AuditService.log_action(
            action='push_notification_unsubscribed',
            entity_type='notification',
            entity_id=user.id,
            new_values={'user_id': user.id},
            user_id=user.id,
            hotel_id=user.hotel_id
        )
        
        return jsonify({
            'success': True,
            'message': 'Push bildirimleri kapatıldı'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@api_bp.route('/push/test', methods=['POST'])
@require_login
@limiter.limit("5 per minute")
def test_push_notification():
    """Test push notification"""
    try:
        from app.services.notification_service import NotificationService
        
        user = SystemUser.query.get(session['user_id'])
        if not user or not hasattr(user, 'push_subscription') or not user.push_subscription:
            return jsonify({'error': 'Push bildirimleri aktif değil'}), 400
        
        import json
        subscription_info = json.loads(user.push_subscription)
        
        success = NotificationService.send_notification(
            subscription_info=subscription_info,
            title="Test Bildirimi",
            body="Push bildirimleri başarıyla çalışıyor!",
            data={'type': 'test'}
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Test bildirimi gönderildi'
            })
        else:
            return jsonify({'error': 'Bildirim gönderilemedi'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500



# ==================== Buggy Location Tracking ====================
@api_bp.route('/buggies/locations', methods=['GET'])
@limiter.limit("30 per minute")
@require_login
@require_role('admin')
def get_buggy_locations():
    """Get all buggies with their current locations (Admin only)"""
    try:
        from app.utils.helpers import RequestContext
        hotel_id = RequestContext.get_current_hotel_id()
        
        # Get all buggies with their locations
        buggies = Buggy.query.filter_by(hotel_id=hotel_id).all()
        
        result = []
        for buggy in buggies:
            buggy_data = buggy.to_dict()
            result.append(buggy_data)
        
        return jsonify({
            'success': True,
            'buggies': result,
            'total': len(result)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/buggies/<int:buggy_id>/location', methods=['PUT'])
@limiter.limit("20 per minute")
@require_login
def update_buggy_location(buggy_id):
    """Update buggy's current location (Driver or Admin)"""
    try:
        user = SystemUser.query.get(session['user_id'])
        data = request.get_json()
        
        if not data or 'location_id' not in data:
            return jsonify({'error': 'location_id gereklidir'}), 400
        
        location_id = data['location_id']
        
        # Get buggy
        buggy = Buggy.query.get(buggy_id)
        if not buggy:
            return jsonify({'error': 'Buggy bulunamadı'}), 404
        
        # Check authorization
        if user.role == 'driver' and buggy.driver_id != user.id:
            return jsonify({'error': 'Bu buggy size atanmamış'}), 403
        
        # Validate location
        location = Location.query.get(location_id)
        if not location:
            return jsonify({'error': 'Lokasyon bulunamadı'}), 404
        
        if location.hotel_id != buggy.hotel_id:
            return jsonify({'error': 'Lokasyon farklı bir otele ait'}), 400
        
        # Update location
        old_location_id = buggy.current_location_id
        buggy.current_location_id = location_id
        db.session.commit()
        
        # Log location change
        from app.services.audit_service import AuditService
        AuditService.log_action(
            action='buggy_location_changed',
            entity_type='buggy',
            entity_id=buggy_id,
            old_values={'location_id': old_location_id},
            new_values={'location_id': location_id},
            user_id=user.id,
            hotel_id=buggy.hotel_id
        )
        
        # Emit WebSocket event for real-time tracking
        from app import socketio
        socketio.emit('buggy_location_changed', {
            'buggy_id': buggy_id,
            'location_id': location_id,
            'location_name': location.name,
            'buggy_code': buggy.code
        }, room=f'hotel_{buggy.hotel_id}_admins')
        
        return jsonify({
            'success': True,
            'message': 'Lokasyon güncellendi',
            'buggy': buggy.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500



# ==================== Driver Initial Location Setup ====================
@api_bp.route('/driver/set-initial-location', methods=['POST'])
@limiter.limit("10 per minute")
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
        
        return jsonify({
            'success': True,
            'message': 'Lokasyon ayarlandı, sisteme hoş geldiniz!',
            'buggy': user.buggy.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500



# ==================== Admin Session Management ====================
@api_bp.route('/admin/close-driver-session/<int:driver_id>', methods=['POST'])
@limiter.limit("20 per minute")
@require_login
@require_role('admin')
def close_driver_session(driver_id):
    """Admin closes driver session and sets buggy offline"""
    try:
        # Get driver
        driver = SystemUser.query.get(driver_id)
        if not driver:
            return jsonify({'error': 'Sürücü bulunamadı'}), 404
        
        if driver.role != UserRole.DRIVER:
            return jsonify({'error': 'Kullanıcı sürücü değil'}), 400
        
        # Set buggy to offline if exists
        if driver.buggy:
            driver.buggy.status = BuggyStatus.OFFLINE
        
        # Close all active sessions for this driver
        from app.models.session import Session as SessionModel
        active_sessions = SessionModel.query.filter_by(
            user_id=driver_id,
            is_active=True
        ).all()
        
        for sess in active_sessions:
            sess.is_active = False
            sess.revoked_at = datetime.utcnow()
        
        db.session.commit()
        
        # Log admin action
        from app.services.audit_service import AuditService
        AuditService.log_action(
            action='admin_closed_driver_session',
            entity_type='session',
            entity_id=driver_id,
            new_values={'driver_name': driver.full_name, 'reason': 'admin_action'},
            user_id=session.get('user_id'),
            hotel_id=driver.hotel_id
        )
        
        # Emit WebSocket event to force driver logout
        from app import socketio
        socketio.emit('force_logout', {
            'user_id': driver_id,
            'reason': 'Oturumunuz yönetici tarafından kapatıldı',
            'message': 'Oturumunuz yönetici tarafından kapatıldı. Lütfen tekrar giriş yapın.'
        }, room=f'user_{driver_id}')
        
        return jsonify({
            'success': True,
            'message': f'{driver.full_name} oturumu kapatıldı'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ==================== Driver Location Management ====================
@api_bp.route('/driver/set-location', methods=['POST'])
@limiter.limit("20 per minute")
@require_login
def set_driver_location():
    """Set or update driver's current location"""
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
        
        # Emit WebSocket event to admin
        from app.websocket import socketio
        socketio.emit('driver_location_updated', {
            'buggy_id': user.buggy.id,
            'buggy_code': user.buggy.code,
            'driver_name': user.full_name,
            'location_id': location_id,
            'location_name': location.name,
            'status': user.buggy.status.value
        }, room=f'hotel_{user.hotel_id}_admin')
        
        return jsonify({
            'success': True,
            'message': 'Konumunuz güncellendi',
            'buggy': user.buggy.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ==================== Driver Request Management ====================
@api_bp.route('/driver/accept-request/<int:request_id>', methods=['POST'])
@limiter.limit("30 per minute")
@require_login
def driver_accept_request(request_id):
    """Accept a pending buggy request"""
    try:
        user = SystemUser.query.get(session['user_id'])
        
        # Check if user is driver
        if user.role != UserRole.DRIVER:
            return jsonify({'error': 'Sadece sürücüler talep kabul edebilir'}), 403
        
        # Check if driver has buggy
        if not user.buggy:
            return jsonify({'error': 'Size atanmış buggy bulunamadı'}), 404
        
        # Check if buggy is available
        if user.buggy.status != BuggyStatus.AVAILABLE:
            return jsonify({'error': 'Buggy müsait değil'}), 400
        
        # Get request with row-level lock to prevent race conditions
        buggy_request = db.session.query(BuggyRequest).filter_by(
            id=request_id,
            hotel_id=user.hotel_id,
            status=RequestStatus.PENDING
        ).with_for_update().first()
        
        if not buggy_request:
            return jsonify({'error': 'Talep bulunamadı veya artık müsait değil'}), 404
        
        # Update request
        buggy_request.status = RequestStatus.ACCEPTED
        buggy_request.buggy_id = user.buggy.id
        buggy_request.accepted_by_id = user.id
        buggy_request.accepted_at = datetime.utcnow()
        
        # Update buggy status
        user.buggy.status = BuggyStatus.BUSY
        
        db.session.commit()
        
        # Log acceptance
        from app.services.audit_service import AuditService
        AuditService.log_action(
            action='request_accepted',
            entity_type='request',
            entity_id=buggy_request.id,
            new_values={
                'buggy_id': user.buggy.id,
                'driver_id': user.id,
                'driver_name': user.full_name
            },
            user_id=user.id,
            hotel_id=user.hotel_id
        )
        
        # Send notification to guest if subscribed
        if buggy_request.guest_device_id:
            from app.services.notification_service import NotificationService
            import json
            try:
                subscription = json.loads(buggy_request.guest_device_id)
                NotificationService.send_notification(
                    subscription_info=subscription,
                    title="Buggy Kabul Edildi",
                    body=f"Buggy'niz yola çıktı. {user.buggy.code}",
                    data={'type': 'request_accepted', 'request_id': buggy_request.id}
                )
            except:
                pass  # Notification failure shouldn't break the flow
        
        # Emit WebSocket events
        from app.websocket import socketio
        socketio.emit('request_accepted', {
            'request_id': buggy_request.id,
            'buggy': user.buggy.to_dict(),
            'driver': user.to_dict()
        }, room=f'request_{buggy_request.id}')
        
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
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@api_bp.route('/driver/complete-request/<int:request_id>', methods=['POST'])
@limiter.limit("30 per minute")
@require_login
def driver_complete_request(request_id):
    """Mark an accepted request as completed"""
    try:
        user = SystemUser.query.get(session['user_id'])
        
        # Check if user is driver
        if user.role != UserRole.DRIVER:
            return jsonify({'error': 'Sadece sürücüler talep tamamlayabilir'}), 403
        
        # Check if driver has buggy
        if not user.buggy:
            return jsonify({'error': 'Size atanmış buggy bulunamadı'}), 404
        
        # Get request
        buggy_request = BuggyRequest.query.filter_by(
            id=request_id,
            buggy_id=user.buggy.id,
            accepted_by_id=user.id,
            status=RequestStatus.ACCEPTED
        ).first()
        
        if not buggy_request:
            return jsonify({'error': 'Talep bulunamadı veya size ait değil'}), 404
        
        # Update request
        buggy_request.status = RequestStatus.COMPLETED
        buggy_request.completed_at = datetime.utcnow()
        
        # Keep buggy busy until driver sets new location
        # (Location modal will be shown on frontend)
        
        db.session.commit()
        
        # Log completion
        from app.services.audit_service import AuditService
        AuditService.log_action(
            action='request_completed',
            entity_type='request',
            entity_id=buggy_request.id,
            new_values={'completed_at': buggy_request.completed_at.isoformat()},
            user_id=user.id,
            hotel_id=user.hotel_id
        )
        
        # Send notification to guest if subscribed
        if buggy_request.guest_device_id:
            from app.services.notification_service import NotificationService
            import json
            try:
                subscription = json.loads(buggy_request.guest_device_id)
                NotificationService.send_notification(
                    subscription_info=subscription,
                    title="Buggy Geldi!",
                    body="Buggy'niz konumunuza ulaştı. İyi yolculuklar!",
                    data={'type': 'request_completed', 'request_id': buggy_request.id}
                )
            except:
                pass
        
        # Emit WebSocket events
        from app.websocket import socketio
        socketio.emit('request_completed', {
            'request_id': buggy_request.id
        }, room=f'request_{buggy_request.id}')
        
        socketio.emit('request_status_changed', {
            'request_id': buggy_request.id,
            'status': 'completed'
        }, room=f'hotel_{user.hotel_id}_admin')
        
        return jsonify({
            'success': True,
            'message': 'Talep tamamlandı! Lütfen yeni konumunuzu seçin.',
            'show_location_modal': True
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ==================== Admin Session Management ====================
@api_bp.route('/admin/sessions', methods=['GET'])
@limiter.limit("30 per minute")
@require_login
def get_active_sessions():
    """Get all active sessions (admin only)"""
    try:
        user = SystemUser.query.get(session['user_id'])
        
        if user.role != UserRole.ADMIN:
            return jsonify({'error': 'Sadece adminler oturumları görüntüleyebilir'}), 403
        
        from app.models.session import Session as SessionModel
        
        # Get active sessions for this hotel
        sessions = SessionModel.query.filter_by(
            hotel_id=user.hotel_id,
            is_active=True
        ).order_by(SessionModel.created_at.desc()).all()
        
        return jsonify({
            'success': True,
            'sessions': [s.to_dict() for s in sessions]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/admin/sessions/<int:session_id>/terminate', methods=['POST'])
@limiter.limit("20 per minute")
@require_login
def terminate_session(session_id):
    """Terminate a user session (admin only)"""
    try:
        user = SystemUser.query.get(session['user_id'])
        
        if user.role != UserRole.ADMIN:
            return jsonify({'error': 'Sadece adminler oturum sonlandırabilir'}), 403
        
        from app.models.session import Session as SessionModel
        
        # Get session
        user_session = SessionModel.query.filter_by(
            id=session_id,
            hotel_id=user.hotel_id
        ).first()
        
        if not user_session:
            return jsonify({'error': 'Oturum bulunamadı'}), 404
        
        if not user_session.is_active:
            return jsonify({'error': 'Oturum zaten sonlandırılmış'}), 400
        
        # Terminate session
        user_session.is_active = False
        user_session.revoked_at = datetime.utcnow()
        
        # If driver, set buggy offline
        session_user = SystemUser.query.get(user_session.user_id)
        if session_user and session_user.role == UserRole.DRIVER and session_user.buggy:
            session_user.buggy.status = BuggyStatus.OFFLINE
        
        db.session.commit()
        
        # Log termination
        from app.services.audit_service import AuditService
        AuditService.log_action(
            action='session_terminated_by_admin',
            entity_type='session',
            entity_id=user_session.id,
            new_values={
                'terminated_user_id': user_session.user_id,
                'terminated_by_admin_id': user.id
            },
            user_id=user.id,
            hotel_id=user.hotel_id
        )
        
        # Emit WebSocket event to force logout
        from app.websocket import socketio
        socketio.emit('force_logout', {
            'reason': 'Session terminated by administrator',
            'message': 'Oturumunuz yönetici tarafından sonlandırıldı'
        }, room=f'user_{user_session.user_id}')
        
        return jsonify({
            'success': True,
            'message': 'Oturum başarıyla sonlandırıldı'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ==================== Driver Dashboard API ====================
@api_bp.route('/driver/pending-requests', methods=['GET'])
@limiter.limit("30 per minute")
@require_login
@require_role('driver')
def get_pending_requests():
    """Get all pending requests for driver's hotel"""
    try:
        user = SystemUser.query.get(session['user_id'])
        
        # Check if driver has assigned buggy
        if not user.buggy:
            return jsonify({'success': False, 'error': 'No buggy assigned'}), 400
        
        # Query pending requests for the hotel with location eager loading
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
        
        return jsonify({
            'success': True,
            'requests': requests_data,
            'total': len(requests_data)
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/driver/active-request', methods=['GET'])
@limiter.limit("30 per minute")
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


# ==================== Admin Driver Management ====================
@api_bp.route('/admin/assign-driver-to-buggy', methods=['POST'])
@limiter.limit("20 per minute")
@require_login
@require_role('admin')
def assign_driver_to_buggy():
    """
    Assign a driver to a buggy (Admin only)
    
    Request Body:
    {
        "buggy_id": 1,
        "driver_id": 5
    }
    
    Response:
    {
        "success": true,
        "message": "Sürücü başarıyla atandı",
        "buggy": {...}
    }
    """
    try:
        admin = SystemUser.query.get(session['user_id'])
        data = request.get_json()
        
        # Validate required fields
        if not data or 'buggy_id' not in data or 'driver_id' not in data:
            return jsonify({'success': False, 'error': 'buggy_id ve driver_id gereklidir'}), 400
        
        buggy_id = data['buggy_id']
        driver_id = data['driver_id']
        
        # Get buggy
        buggy = Buggy.query.filter_by(id=buggy_id, hotel_id=admin.hotel_id).first()
        if not buggy:
            return jsonify({'success': False, 'error': 'Buggy bulunamadı'}), 404
        
        # Get driver
        driver = SystemUser.query.filter_by(
            id=driver_id,
            hotel_id=admin.hotel_id,
            role=UserRole.DRIVER
        ).first()
        if not driver:
            return jsonify({'success': False, 'error': 'Sürücü bulunamadı'}), 404
        
        # Store old driver for audit
        old_driver_id = buggy.get_active_driver()
        old_driver_name = buggy.get_active_driver_name()
        
        # Assign driver to buggy using association table
        from app.models.buggy_driver import BuggyDriver
        
        # Check if driver is already assigned to this buggy
        existing = BuggyDriver.query.filter_by(buggy_id=buggy_id, driver_id=driver_id).first()
        if not existing:
            # Create new association
            association = BuggyDriver(
                buggy_id=buggy_id,
                driver_id=driver_id,
                is_active=False,  # Will be set to True when driver logs in
                is_primary=True,  # Mark as primary driver
                assigned_at=datetime.utcnow()
            )
            db.session.add(association)
        
        db.session.commit()
        
        # Log driver assignment
        from app.services.audit_service import AuditService
        AuditService.log_action(
            action='driver_assigned_to_buggy',
            entity_type='buggy',
            entity_id=buggy_id,
            old_values={
                'driver_id': old_driver_id,
                'driver_name': old_driver_name
            },
            new_values={
                'driver_id': driver_id,
                'driver_name': driver.full_name,
                'buggy_code': buggy.code,
                'admin_name': admin.full_name
            },
            user_id=admin.id,
            hotel_id=admin.hotel_id
        )
        
        # Emit WebSocket event for real-time updates
        from app import socketio
        socketio.emit('driver_assigned', {
            'buggy_id': buggy_id,
            'buggy_code': buggy.code,
            'driver_id': driver_id,
            'driver_name': driver.full_name
        }, room=f'hotel_{admin.hotel_id}_admin')
        
        return jsonify({
            'success': True,
            'message': f'{driver.full_name} başarıyla {buggy.code} buggy\'sine atandı',
            'buggy': buggy.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/admin/transfer-driver', methods=['POST'])
@limiter.limit("20 per minute")
@require_login
@require_role('admin')
def transfer_driver():
    """
    Transfer a driver from one buggy to another (Admin only)
    
    Request Body:
    {
        "driver_id": 5,
        "source_buggy_id": 1,
        "target_buggy_id": 2
    }
    
    Response:
    {
        "success": true,
        "message": "Sürücü başarıyla transfer edildi",
        "source_buggy": {...},
        "target_buggy": {...}
    }
    """
    try:
        admin = SystemUser.query.get(session['user_id'])
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['driver_id', 'source_buggy_id', 'target_buggy_id']
        for field in required_fields:
            if not data or field not in data:
                return jsonify({'success': False, 'error': f'{field} gereklidir'}), 400
        
        driver_id = data['driver_id']
        source_buggy_id = data['source_buggy_id']
        target_buggy_id = data['target_buggy_id']
        
        # Validate source and target are different
        if source_buggy_id == target_buggy_id:
            return jsonify({'success': False, 'error': 'Kaynak ve hedef buggy aynı olamaz'}), 400
        
        # Get driver
        driver = SystemUser.query.filter_by(
            id=driver_id,
            hotel_id=admin.hotel_id,
            role=UserRole.DRIVER
        ).first()
        if not driver:
            return jsonify({'success': False, 'error': 'Sürücü bulunamadı'}), 404
        
        # Get source buggy
        source_buggy = Buggy.query.filter_by(id=source_buggy_id, hotel_id=admin.hotel_id).first()
        if not source_buggy:
            return jsonify({'success': False, 'error': 'Kaynak buggy bulunamadı'}), 404
        
        # Get target buggy
        target_buggy = Buggy.query.filter_by(id=target_buggy_id, hotel_id=admin.hotel_id).first()
        if not target_buggy:
            return jsonify({'success': False, 'error': 'Hedef buggy bulunamadı'}), 404
        
        # Verify driver is assigned to source buggy using buggy_drivers table
        from app.models.buggy_driver import BuggyDriver
        source_association = BuggyDriver.query.filter_by(
            buggy_id=source_buggy_id,
            driver_id=driver_id
        ).first()
        
        if not source_association:
            return jsonify({'success': False, 'error': 'Sürücü kaynak buggy\'ye atanmamış'}), 400
        
        # Check if driver has active session
        from app.models.session import Session as SessionModel
        active_session = SessionModel.query.filter_by(
            user_id=driver_id,
            is_active=True
        ).first()
        
        session_was_active = active_session is not None
        
        # If active session exists, terminate it
        if active_session:
            active_session.is_active = False
            active_session.revoked_at = datetime.utcnow()
            
            # Deactivate driver association from source buggy
            source_association.is_active = False
            
            # Set both buggies to OFFLINE
            source_buggy.status = BuggyStatus.OFFLINE
            target_buggy.status = BuggyStatus.OFFLINE
        else:
            # Just deactivate the association without changing buggy status
            source_association.is_active = False
        
        # Create or activate driver association with target buggy
        target_association = BuggyDriver.query.filter_by(
            buggy_id=target_buggy_id,
            driver_id=driver_id
        ).first()
        
        if target_association:
            # Reactivate existing association
            target_association.is_active = False  # Will be activated when driver logs in
            target_association.assigned_at = datetime.utcnow()
        else:
            # Create new association
            target_association = BuggyDriver(
                buggy_id=target_buggy_id,
                driver_id=driver_id,
                is_active=False,  # Will be activated when driver logs in
                is_primary=True,
                assigned_at=datetime.utcnow()
            )
            db.session.add(target_association)
        
        db.session.commit()
        
        # Log driver transfer
        from app.services.audit_service import AuditService
        AuditService.log_action(
            action='driver_transferred',
            entity_type='buggy',
            entity_id=target_buggy_id,
            old_values={
                'source_buggy_id': source_buggy_id,
                'source_buggy_code': source_buggy.code
            },
            new_values={
                'target_buggy_id': target_buggy_id,
                'target_buggy_code': target_buggy.code,
                'driver_id': driver_id,
                'driver_name': driver.full_name,
                'admin_name': admin.full_name,
                'session_terminated': session_was_active
            },
            user_id=admin.id,
            hotel_id=admin.hotel_id
        )
        
        # Emit WebSocket event for real-time updates
        from app import socketio
        socketio.emit('driver_transferred', {
            'driver_id': driver_id,
            'driver_name': driver.full_name,
            'source_buggy_id': source_buggy_id,
            'source_buggy_code': source_buggy.code,
            'target_buggy_id': target_buggy_id,
            'target_buggy_code': target_buggy.code,
            'session_terminated': session_was_active
        }, room=f'hotel_{admin.hotel_id}_admin')
        
        # If session was terminated, notify driver
        if session_was_active:
            socketio.emit('force_logout', {
                'reason': 'Driver transferred to another buggy',
                'message': f'Başka bir buggy\'ye transfer edildiniz: {target_buggy.code}'
            }, room=f'user_{driver_id}')
        
        return jsonify({
            'success': True,
            'message': f'{driver.full_name} başarıyla {source_buggy.code}\'dan {target_buggy.code}\'a transfer edildi',
            'source_buggy': source_buggy.to_dict(),
            'target_buggy': target_buggy.to_dict(),
            'session_terminated': session_was_active
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
