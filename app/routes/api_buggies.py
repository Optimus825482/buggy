"""
Buggy Call - Buggy & Driver API Routes
"""
from flask import Blueprint, jsonify, request, session, current_app
from app import db, socketio
from app.models.user import SystemUser, UserRole
from app.models.buggy import Buggy, BuggyStatus
from app.models.buggy_driver import BuggyDriver
from app.models.location import Location
from app.models import get_current_timestamp
from app.utils import APIResponse, require_login
from app.utils.buggy_icons import assign_buggy_icon
from datetime import datetime

api_buggies_bp = Blueprint('api_buggies', __name__)


# ==================== Buggies API ====================
@api_buggies_bp.route('/api/buggies', methods=['GET'])
@require_login
def get_buggies():
    """Get all buggies"""
    try:
        from sqlalchemy.orm import joinedload

        user = SystemUser.query.get(session['user_id'])

        # Eager loading ile tüm ilişkileri tek sorguda çek (N+1 problemi çözümü)
        buggies = Buggy.query.filter_by(hotel_id=user.hotel_id)\
            .options(
                joinedload(Buggy.current_location),
                joinedload(Buggy.driver_associations)
            ).all()

        result = []
        for buggy in buggies:
            buggy_dict = buggy.to_dict()
            result.append(buggy_dict)

        return jsonify({
            'success': True,
            'buggies': result
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_buggies_bp.route('/api/buggies', methods=['POST'])
@require_login
def create_buggy():
    """Create new buggy (driver assignment is optional)"""
    try:
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

        # Use provided icon or assign unique icon for this buggy
        buggy_icon = data.get('icon') or assign_buggy_icon(user.hotel_id)

        # Create buggy without driver
        buggy = Buggy(
            hotel_id=user.hotel_id,
            code=buggy_code,
            license_plate=data.get('license_plate'),
            icon=buggy_icon,  # Assign icon
            status=BuggyStatus.OFFLINE,
            driver_id=None  # Will be managed through buggy_drivers table
        )

        db.session.add(buggy)
        db.session.flush()  # Get buggy ID

        # If driver_id provided, create association
        driver_info = None
        if driver_id:
            print(f'🔍 Looking for driver with ID: {driver_id}, hotel_id: {user.hotel_id}')

            # Verify driver exists
            driver = SystemUser.query.filter_by(
                id=driver_id,
                hotel_id=user.hotel_id,
                role=UserRole.DRIVER
            ).first()

            if driver:
                print(f'✅ Driver found: {driver.username} ({driver.full_name})')

                # Create buggy-driver association
                association = BuggyDriver(
                    buggy_id=buggy.id,
                    driver_id=driver_id,
                    is_active=False,  # Will be activated when driver logs in
                    is_primary=True,
                    assigned_at=get_current_timestamp()
                )
                db.session.add(association)
                print(f'✅ BuggyDriver association created: buggy_id={buggy.id}, driver_id={driver_id}')

                driver_info = {
                    'id': driver.id,
                    'username': driver.username,
                    'full_name': driver.full_name
                }
            else:
                print(f'❌ Driver not found with ID: {driver_id}')

        db.session.commit()
        print(f'✅ Buggy created successfully: {buggy.code} (ID: {buggy.id})')

        response = {
            'success': True,
            'message': 'Buggy başarıyla oluşturuldu',
            'buggy': buggy.to_dict()
        }

        if driver_info:
            response['driver'] = driver_info
            response['message'] = 'Buggy ve sürücü ataması başarıyla oluşturuldu'
            print(f'✅ Response includes driver info: {driver_info}')

        return jsonify(response), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@api_buggies_bp.route('/api/buggies/<int:buggy_id>', methods=['GET'])
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


@api_buggies_bp.route('/api/buggies/<int:buggy_id>', methods=['PUT'])
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
        if 'icon' in data:
            buggy.icon = data['icon']
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


@api_buggies_bp.route('/api/buggies/<int:buggy_id>', methods=['DELETE'])
@require_login
def delete_buggy(buggy_id):
    """Delete buggy (fails if buggy has active requests)"""
    try:
        user = SystemUser.query.get(session['user_id'])
        buggy = Buggy.query.filter_by(id=buggy_id, hotel_id=user.hotel_id).first()

        if not buggy:
            return jsonify({'error': 'Buggy bulunamadı'}), 404

        # Check for active requests (prevent data integrity issues)
        active_request = BuggyRequest.query.filter(
            BuggyRequest.buggy_id == buggy_id,
            BuggyRequest.status.in_([RequestStatus.PENDING, RequestStatus.ACCEPTED])
        ).first()
        if active_request:
            return jsonify({'error': 'Bu buggy\'nin aktif talepleri bulunuyor. Önce talepleri tamamlayın.'}), 400

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
@api_buggies_bp.route('/api/drivers', methods=['GET'])
@require_login
def get_drivers():
    """Get all drivers"""
    try:
        user = SystemUser.query.get(session['user_id'])
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


@api_buggies_bp.route('/api/drivers/active', methods=['GET'])
def get_active_drivers():
    """Get active drivers with their buggies (No auth required for guest debugging)"""
    try:
        hotel_id = request.args.get('hotel_id', 1, type=int)
        notify_param = request.args.get('notify', 'false')
        notify = notify_param.lower() == 'true' if notify_param else False

        # DEBUG: Tüm buggy'leri kontrol et
        all_buggies = Buggy.query.filter_by(hotel_id=hotel_id).all()
        print(f'\n🔍 [DEBUG] Hotel {hotel_id} - Total Buggies: {len(all_buggies)}')
        for b in all_buggies:
            print(f'   Buggy {b.code}: status={b.status.value}, location={b.current_location_id}')

        # N+1 FIX: Single query to get all active assignments
        active_assignments = BuggyDriver.query.join(
            Buggy, BuggyDriver.buggy_id == Buggy.id
        ).filter(
            Buggy.hotel_id == hotel_id,
            Buggy.status == BuggyStatus.AVAILABLE,
            BuggyDriver.is_active == True
        ).all()

        print(f'🟢 [DEBUG] Available Buggies with Active Assignments: {len(active_assignments)}')

        active_drivers = []

        for assignment in active_assignments:
            buggy = assignment.buggy
            driver = assignment.driver

            if buggy and driver:
                print(f'   ✅ Buggy {buggy.code}, Driver: {driver.full_name or driver.username}, FCM: {bool(driver.fcm_token)}')
                active_drivers.append({
                    'driver_id': driver.id,
                    'driver_name': driver.full_name or driver.username,
                    'buggy_id': buggy.id,
                    'buggy_code': buggy.code,
                    'buggy_icon': buggy.icon,
                    'buggy_status': buggy.status.value,
                    'has_fcm_token': bool(driver.fcm_token),
                    'last_active': assignment.last_active_at.isoformat() if assignment.last_active_at else None
                })

        print(f'👥 [DEBUG] Total Active Drivers: {len(active_drivers)}\n')

        # Eğer notify=true ise, sürücülere WebSocket ile bildirim gönder
        if notify and len(active_drivers) > 0:
            # Location bilgisini al (varsa)
            location_id = request.args.get('location_id', type=int)
            location_name = 'Bilinmeyen Lokasyon'
            if location_id:
                location = Location.query.get(location_id)
                if location:
                    location_name = location.name

            # WebSocket event data - hotel_id ve guest_count eklendi
            event_data = {
                'type': 'guest_connected',
                'message': '🚨 Yeni Misafir Bağlandı!',
                'hotel_id': hotel_id,
                'location_id': location_id,
                'location_name': location_name,
                'guest_count': len(active_drivers),  # Aktif sürücü sayısı
                'timestamp': datetime.utcnow().isoformat()
            }

            # Hotel drivers room'a gönder
            drivers_room = f'hotel_{hotel_id}_drivers'
            socketio.emit('guest_connected', event_data, room=drivers_room, namespace='/')
            print(f'🚨 WebSocket: Guest connected notification sent to {drivers_room}')
            print(f'   Event Data: {event_data}')

        return jsonify({
            'success': True,
            'hotel_id': hotel_id,
            'active_drivers_count': len(active_drivers),
            'active_drivers': active_drivers,
            'notification_sent': notify and len(active_drivers) > 0
        }), 200
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f'❌ [ERROR] get_active_drivers failed: {str(e)}')
        print(error_details)
        return jsonify({
            'success': False,
            'error': str(e),
            'details': error_details if current_app.debug else None
        }), 500
