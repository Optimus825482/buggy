"""
Buggy Call - Users & Buggy Location API Routes
Extracted from api_old.py for modularity
"""
from flask import Blueprint, jsonify, request, session, current_app
from app import db, socketio
from app.models.user import SystemUser, UserRole
from app.models.hotel import Hotel
from app.models.location import Location
from app.models.buggy import Buggy, BuggyStatus
from app.models.buggy_driver import BuggyDriver
from app.services import AuthService
from app.utils import APIResponse, require_login, require_role, validate_schema
from app.utils.decorators import get_current_user_cached, invalidate_user_cache
from app.utils.exceptions import BuggyCallException
from app.schemas import UserCreateSchema
from datetime import datetime

api_users_bp = Blueprint('api_users', __name__)


# ==================== Users API ====================
@api_users_bp.route('/api/users/<int:user_id>/reset-password', methods=['POST'])
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


@api_users_bp.route('/api/users', methods=['POST'])
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

        full_name = f"{data.get('first_name', '')} {data.get('last_name', '')}".strip() or data['username']

        # Use AuthService for creation + audit logging
        from app.services.auth_service import AuthService
        from app.utils.exceptions import ValidationException, ResourceNotFoundException

        new_user = AuthService.create_user(
            hotel_id=user.hotel_id,
            username=data['username'],
            password=data['password'],
            role=data['role'],
            full_name=full_name,
            email=data.get('email'),
            phone=data.get('phone')
        )

        return jsonify({
            'success': True,
            'message': 'Kullanıcı başarıyla oluşturuldu',
            'user': {
                'id': new_user.id,
                'username': new_user.username,
                'role': new_user.role.value,
                'full_name': new_user.full_name,
                'email': new_user.email,
                'phone': new_user.phone,
                'hotel_id': new_user.hotel_id
            }
        }), 201

    except ValidationException as e:
        return jsonify({'error': e.message}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ==================== User Management API (CRUD) ====================
@api_users_bp.route('/api/users/<int:user_id>', methods=['GET'])
@require_login
def get_user(user_id):
    """
    Kullanıcı bilgilerini getir (Admin veya kendi bilgisi)
    """
    try:
        current_user = SystemUser.query.get(session['user_id'])

        # Admin değilse sadece kendi bilgisini görebilir
        if current_user.role != UserRole.ADMIN and current_user.id != user_id:
            return jsonify({'success': False, 'error': 'Bu işlem için yetkiniz yok'}), 403

        # Kullanıcıyı getir
        user = SystemUser.query.filter_by(id=user_id, hotel_id=current_user.hotel_id).first()
        if not user:
            return jsonify({'success': False, 'error': 'Kullanıcı bulunamadı'}), 404

        # Ad ve soyadı ayır
        full_name_parts = user.full_name.split(' ', 1) if user.full_name else ['', '']
        first_name = full_name_parts[0] if len(full_name_parts) > 0 else ''
        last_name = full_name_parts[1] if len(full_name_parts) > 1 else ''

        return jsonify({
            'success': True,
            'user': {
                'id': user.id,
                'username': user.username,
                'role': user.role.value,
                'full_name': user.full_name,
                'first_name': first_name,
                'last_name': last_name,
                'email': user.email,
                'phone': user.phone,
                'is_active': user.is_active,
                'created_at': user.created_at.isoformat() if user.created_at else None
            }
        }), 200

    except Exception as e:
        current_app.logger.error(f'Error getting user {user_id}: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500


@api_users_bp.route('/api/users/<int:user_id>', methods=['PUT'])
@require_login
def update_user(user_id):
    """
    Kullanıcı bilgilerini güncelle (Admin veya kendi bilgisi)
    """
    try:
        current_user = SystemUser.query.get(session['user_id'])

        # Admin değilse sadece kendi bilgisini güncelleyebilir
        if current_user.role != UserRole.ADMIN and current_user.id != user_id:
            return jsonify({'success': False, 'error': 'Bu işlem için yetkiniz yok'}), 403

        # Kullanıcıyı getir
        user = SystemUser.query.filter_by(id=user_id, hotel_id=current_user.hotel_id).first()
        if not user:
            return jsonify({'success': False, 'error': 'Kullanıcı bulunamadı'}), 404

        data = request.get_json()

        # Güncellenebilir alanlar
        if 'first_name' in data or 'last_name' in data:
            first_name = data.get('first_name', '').strip()
            last_name = data.get('last_name', '').strip()
            user.full_name = f"{first_name} {last_name}".strip()

        if 'email' in data:
            user.email = data['email'].strip() if data['email'] else None

        if 'phone' in data:
            user.phone = data['phone'].strip() if data['phone'] else None

        # Şifre güncelleme (opsiyonel)
        if 'password' in data and data['password']:
            if len(data['password']) < 6:
                return jsonify({'success': False, 'error': 'Şifre en az 6 karakter olmalıdır'}), 400
            user.set_password(data['password'])

        # Admin sadece role ve is_active güncelleyebilir
        if current_user.role == UserRole.ADMIN:
            if 'is_active' in data:
                user.is_active = bool(data['is_active'])

            if 'role' in data and data['role'] in ['admin', 'driver']:
                user.role = UserRole.ADMIN if data['role'] == 'admin' else UserRole.DRIVER

        db.session.commit()

        # Audit log
        from app.services.audit_service import AuditService
        AuditService.log_action(
            action='user_updated',
            entity_type='user',
            entity_id=user_id,
            new_values={'updated_by': current_user.id},
            user_id=current_user.id,
            hotel_id=current_user.hotel_id
        )

        return jsonify({
            'success': True,
            'message': 'Kullanıcı bilgileri başarıyla güncellendi',
            'user': {
                'id': user.id,
                'username': user.username,
                'full_name': user.full_name,
                'email': user.email,
                'phone': user.phone,
                'is_active': user.is_active
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error updating user {user_id}: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500


@api_users_bp.route('/api/users/<int:user_id>', methods=['DELETE'])
@require_login
def delete_user(user_id):
    """
    Kullanıcıyı sil (Sadece Admin)
    """
    try:
        current_user = SystemUser.query.get(session['user_id'])

        # Sadece admin silebilir
        if current_user.role != UserRole.ADMIN:
            return jsonify({'success': False, 'error': 'Bu işlem için yetkiniz yok'}), 403

        # Kendini silemez
        if current_user.id == user_id:
            return jsonify({'success': False, 'error': 'Kendi hesabınızı silemezsiniz'}), 400

        # Kullanıcıyı getir
        user = SystemUser.query.filter_by(id=user_id, hotel_id=current_user.hotel_id).first()
        if not user:
            return jsonify({'success': False, 'error': 'Kullanıcı bulunamadı'}), 404

        # Eğer sürücü ise, buggy atamalarını kaldır
        if user.role == UserRole.DRIVER:
            # Tüm buggy atamalarını sil
            BuggyDriver.query.filter_by(driver_id=user_id).delete()

            # Eğer aktif oturumu varsa, buggy'leri offline yap
            assigned_buggies = Buggy.query.filter_by(driver_id=user_id).all()
            for buggy in assigned_buggies:
                buggy.driver_id = None
                buggy.status = BuggyStatus.OFFLINE
                buggy.current_location_id = None

        # Kullanıcıyı sil
        username = user.username
        full_name = user.full_name
        db.session.delete(user)
        db.session.commit()

        # Audit log
        from app.services.audit_service import AuditService
        AuditService.log_action(
            action='user_deleted',
            entity_type='user',
            entity_id=user_id,
            old_values={'username': username, 'full_name': full_name},
            user_id=current_user.id,
            hotel_id=current_user.hotel_id
        )

        # WebSocket ile bildir
        socketio.emit('user_deleted', {
            'user_id': user_id,
            'username': username
        }, room=f'hotel_{current_user.hotel_id}_admin')

        return jsonify({
            'success': True,
            'message': f'Kullanıcı "{full_name or username}" başarıyla silindi'
        }), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error deleting user {user_id}: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== Buggy Location Tracking ====================
@api_users_bp.route('/api/buggies/locations', methods=['GET'])
@require_login
@require_role('admin')
def get_buggies_locations():
    """Get all buggies with their current locations (Admin only)"""
    try:
        from app.utils.helpers import RequestContext
        from sqlalchemy.orm import joinedload

        hotel_id = RequestContext.get_current_hotel_id()

        # Eager loading ile tüm ilişkileri tek sorguda çek (N+1 problemi çözümü)
        buggies = Buggy.query.filter_by(hotel_id=hotel_id)\
            .options(
                joinedload(Buggy.current_location),
                joinedload(Buggy.driver_associations)
            ).all()

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


@api_users_bp.route('/api/buggies/<int:buggy_id>/location', methods=['PUT'])
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
        if user.role == UserRole.DRIVER and buggy.driver_id != user.id:
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
        socketio.emit('buggy_location_changed', {
            'buggy_id': buggy_id,
            'location_id': location_id,
            'location_name': location.name,
            'buggy_code': buggy.code
        }, room=f'hotel_{buggy.hotel_id}_admin')

        return jsonify({
            'success': True,
            'message': 'Lokasyon güncellendi',
            'buggy': buggy.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
