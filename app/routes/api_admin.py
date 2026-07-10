"""
Buggy Call - Admin API Routes
Extracted from api_old.py
"""
from flask import Blueprint, jsonify, request, session, current_app
from app import db, csrf, socketio
from app.models.user import SystemUser, UserRole
from app.models.location import Location
from app.models.buggy import Buggy, BuggyStatus
from app.models.buggy_driver import BuggyDriver
from app.models.session import Session as SessionModel
from app.models.request import BuggyRequest
from app.models.notification_log import NotificationLog
from app.services import BuggyService, AuditService
from app.utils import APIResponse, require_login, require_role, validate_schema, handle_errors
from app.utils.logger import logger, log_driver_event, log_api_call, log_error
from app.models import get_current_timestamp
from datetime import datetime
import json

api_admin_bp = Blueprint('api_admin', __name__)

csrf.exempt(api_admin_bp)


# ==================== Admin Session Management ====================

@api_admin_bp.route('/api/admin/close-driver-session/<int:driver_id>', methods=['POST'])
@require_login
@require_role('admin')
def admin_close_driver_session(driver_id):
    """Admin closes driver session and sets buggy offline"""
    try:
        driver = SystemUser.query.get(driver_id)
        if not driver:
            return jsonify({'error': 'Sürücü bulunamadı'}), 404

        if driver.role != UserRole.DRIVER:
            return jsonify({'error': 'Kullanıcı sürücü değil'}), 400

        # Close all active BuggyDriver associations and set buggies offline
        active_buggy_drivers = BuggyDriver.query.filter_by(
            driver_id=driver_id,
            is_active=True
        ).all()

        buggy_ids = []
        for assoc in active_buggy_drivers:
            assoc.is_active = False
            assoc.last_active_at = get_current_timestamp()

            buggy = assoc.buggy
            if buggy:
                buggy.status = BuggyStatus.OFFLINE
                buggy.current_location_id = None
                buggy_ids.append({
                    'id': buggy.id,
                    'code': buggy.code,
                    'icon': buggy.icon
                })

        # Close all active sessions for this driver
        active_sessions = SessionModel.query.filter_by(
            user_id=driver_id,
            is_active=True
        ).all()

        for sess in active_sessions:
            sess.is_active = False
            sess.revoked_at = get_current_timestamp()

        db.session.commit()

        # Log admin action
        AuditService.log_action(
            action='admin_closed_driver_session',
            entity_type='session',
            entity_id=driver_id,
            new_values={'driver_name': driver.full_name, 'reason': 'admin_action'},
            user_id=session.get('user_id'),
            hotel_id=driver.hotel_id
        )

        # Emit WebSocket event to force driver logout
        socketio.emit('force_logout', {
            'reason': 'admin_terminated',
            'message': 'Oturumunuz yönetici tarafından kapatıldı. Lütfen tekrar giriş yapın.'
        }, room=f'user_{driver_id}')

        # Emit buggy status changed events to admin panel
        for buggy_info in buggy_ids:
            socketio.emit('buggy_status_changed', {
                'buggy_id': buggy_info['id'],
                'buggy_code': buggy_info['code'],
                'buggy_icon': buggy_info['icon'],
                'driver_id': None,
                'driver_name': None,
                'location_name': None,
                'status': 'offline',
                'reason': 'admin_closed_session'
            }, room=f'hotel_{driver.hotel_id}_admin')

        return jsonify({
            'success': True,
            'message': f'{driver.full_name} oturumu kapatıldı'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ==================== Admin Session Listing ====================

@api_admin_bp.route('/api/admin/sessions', methods=['GET'])
@require_login
def get_admin_sessions():
    """Get all active sessions (admin only)"""
    try:
        user = SystemUser.query.get(session['user_id'])

        if user.role != UserRole.ADMIN:
            return jsonify({'error': 'Sadece adminler oturumları görüntüleyebilir'}), 403

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


# ==================== Admin Session Termination ====================

@api_admin_bp.route('/api/admin/sessions/<int:session_id>/terminate', methods=['POST'])
@require_login
def terminate_admin_session(session_id):
    """Terminate a user session (admin only)"""
    try:
        user = SystemUser.query.get(session['user_id'])

        if user.role != UserRole.ADMIN:
            return jsonify({'error': 'Sadece adminler oturum sonlandırabilir'}), 403

        user_session = SessionModel.query.filter_by(
            id=session_id,
            hotel_id=user.hotel_id
        ).first()

        if not user_session:
            return jsonify({'error': 'Oturum bulunamadı'}), 404

        if not user_session.is_active:
            return jsonify({'error': 'Oturum zaten sonlandırılmış'}), 400

        user_session.is_active = False
        user_session.revoked_at = get_current_timestamp()

        # If driver, set buggy offline
        session_user = SystemUser.query.get(user_session.user_id)
        if session_user and session_user.role == UserRole.DRIVER and session_user.buggy:
            session_user.buggy.status = BuggyStatus.OFFLINE

        db.session.commit()

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


# ==================== Admin Driver Management ====================

@api_admin_bp.route('/api/admin/assign-driver-to-buggy', methods=['POST'])
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

        if not data or 'buggy_id' not in data or 'driver_id' not in data:
            return jsonify({'success': False, 'error': 'buggy_id ve driver_id gereklidir'}), 400

        buggy_id = data['buggy_id']
        driver_id = data['driver_id']

        buggy = Buggy.query.filter_by(id=buggy_id, hotel_id=admin.hotel_id).first()
        if not buggy:
            return jsonify({'success': False, 'error': 'Buggy bulunamadı'}), 404

        driver = SystemUser.query.filter_by(
            id=driver_id,
            hotel_id=admin.hotel_id,
            role=UserRole.DRIVER
        ).first()
        if not driver:
            return jsonify({'success': False, 'error': 'Sürücü bulunamadı'}), 404

        old_driver_id = buggy.get_active_driver()
        old_driver_name = buggy.get_active_driver_name()

        existing = BuggyDriver.query.filter_by(buggy_id=buggy_id, driver_id=driver_id).first()
        if not existing:
            association = BuggyDriver(
                buggy_id=buggy_id,
                driver_id=driver_id,
                is_active=False,
                is_primary=True,
                assigned_at=get_current_timestamp()
            )
            db.session.add(association)

        db.session.commit()

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


@api_admin_bp.route('/api/admin/transfer-driver', methods=['POST'])
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

        required_fields = ['driver_id', 'source_buggy_id', 'target_buggy_id']
        for field in required_fields:
            if not data or field not in data:
                return jsonify({'success': False, 'error': f'{field} gereklidir'}), 400

        driver_id = data['driver_id']
        source_buggy_id = data['source_buggy_id']
        target_buggy_id = data['target_buggy_id']

        if source_buggy_id == target_buggy_id:
            return jsonify({'success': False, 'error': 'Kaynak ve hedef buggy aynı olamaz'}), 400

        driver = SystemUser.query.filter_by(
            id=driver_id,
            hotel_id=admin.hotel_id,
            role=UserRole.DRIVER
        ).first()
        if not driver:
            return jsonify({'success': False, 'error': 'Sürücü bulunamadı'}), 404

        source_buggy = Buggy.query.filter_by(id=source_buggy_id, hotel_id=admin.hotel_id).first()
        if not source_buggy:
            return jsonify({'success': False, 'error': 'Kaynak buggy bulunamadı'}), 404

        target_buggy = Buggy.query.filter_by(id=target_buggy_id, hotel_id=admin.hotel_id).first()
        if not target_buggy:
            return jsonify({'success': False, 'error': 'Hedef buggy bulunamadı'}), 404

        source_association = BuggyDriver.query.filter_by(
            buggy_id=source_buggy_id,
            driver_id=driver_id
        ).first()

        if not source_association:
            return jsonify({'success': False, 'error': 'Sürücü kaynak buggy\'ye atanmamış'}), 400

        active_session = SessionModel.query.filter_by(
            user_id=driver_id,
            is_active=True
        ).first()

        session_was_active = active_session is not None

        if active_session:
            active_session.is_active = False
            active_session.revoked_at = get_current_timestamp()

            source_association.is_active = False

            source_buggy.status = BuggyStatus.OFFLINE
            target_buggy.status = BuggyStatus.OFFLINE
        else:
            source_association.is_active = False

        target_association = BuggyDriver.query.filter_by(
            buggy_id=target_buggy_id,
            driver_id=driver_id
        ).first()

        if target_association:
            target_association.is_active = False
            target_association.assigned_at = get_current_timestamp()
        else:
            target_association = BuggyDriver(
                buggy_id=target_buggy_id,
                driver_id=driver_id,
                is_active=False,
                is_primary=True,
                assigned_at=get_current_timestamp()
            )
            db.session.add(target_association)

        db.session.commit()

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

        socketio.emit('driver_transferred', {
            'driver_id': driver_id,
            'driver_name': driver.full_name,
            'source_buggy_id': source_buggy_id,
            'source_buggy_code': source_buggy.code,
            'target_buggy_id': target_buggy_id,
            'target_buggy_code': target_buggy.code,
            'session_terminated': session_was_active
        }, room=f'hotel_{admin.hotel_id}_admin')

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


# ==================== Legacy Push / Notification Endpoints ====================

@api_admin_bp.route('/api/push/vapid-public-key', methods=['GET'])
def get_vapid_public_key():
    """
    LEGACY: Get VAPID public key for push notifications
    NOT USED - FCM kullaniliyor
    """
    return jsonify({
        'error': 'Legacy endpoint - FCM kullaniliyor',
        'message': 'Bu endpoint artik kullanilmiyor. FCM sistemi aktif.'
    }), 410


@api_admin_bp.route('/api/notification-permission', methods=['POST'])
@require_login
def handle_notification_permission():
    """
    Update notification permission status in session
    Only accessible by drivers and admins
    """
    try:
        user_id = session.get('user_id')
        if not user_id:
            current_app.logger.warning('[NotificationPermission] Unauthorized access attempt - no user_id in session')
            return jsonify({
                'success': False,
                'error': 'Oturum bulunamadi'
            }), 401

        user = SystemUser.query.get(user_id)
        if not user:
            current_app.logger.warning(f'[NotificationPermission] User not found: {user_id}')
            return jsonify({
                'success': False,
                'error': 'Kullanici bulunamadi'
            }), 404

        user_role = session.get('role')
        if user_role not in ['driver', 'admin']:
            current_app.logger.warning(
                f'[NotificationPermission] Unauthorized role access attempt - '
                f'user_id: {user_id}, role: {user_role}'
            )
            return jsonify({
                'success': False,
                'error': 'Bu islem icin yetkiniz yok'
            }), 403

        data = request.get_json()
        if not data:
            current_app.logger.warning(f'[NotificationPermission] Empty request body - user_id: {user_id}')
            return jsonify({
                'success': False,
                'error': 'Gecersiz istek'
            }), 400

        status = data.get('status')
        valid_statuses = ['default', 'granted', 'denied']

        if not status:
            current_app.logger.warning(f'[NotificationPermission] Missing status - user_id: {user_id}')
            return jsonify({
                'success': False,
                'error': 'Bildirim izni durumu gerekli'
            }), 400

        if status not in valid_statuses:
            current_app.logger.warning(
                f'[NotificationPermission] Invalid status value - '
                f'user_id: {user_id}, status: {status}'
            )
            return jsonify({
                'success': False,
                'error': f'Gecersiz durum degeri. Izin verilen degerler: {", ".join(valid_statuses)}'
            }), 400

        try:
            session['notification_permission_asked'] = True
            session['notification_permission_status'] = status
            session.modified = True

            current_app.logger.info(
                f'[NotificationPermission] Permission updated - '
                f'user_id: {user_id}, role: {user_role}, status: {status}'
            )

            return jsonify({
                'success': True,
                'message': 'Bildirim izni durumu guncellendi',
                'data': {
                    'notification_permission_asked': True,
                    'notification_permission_status': status
                }
            }), 200

        except Exception as session_error:
            current_app.logger.error(
                f'[NotificationPermission] Session update failed - '
                f'user_id: {user_id}, error: {str(session_error)}'
            )
            return jsonify({
                'success': False,
                'error': 'Oturum guncellenirken hata olustu'
            }), 500

    except Exception as e:
        current_app.logger.error(
            f'[NotificationPermission] Unexpected error - '
            f'user_id: {session.get("user_id")}, error: {str(e)}'
        )
        return jsonify({
            'success': False,
            'error': 'Bildirim izni guncellenirken beklenmeyen bir hata olustu'
        }), 500


@api_admin_bp.route('/api/push/test', methods=['POST'])
@require_login
def test_push_notification():
    """Test push notification - LEGACY"""
    return jsonify({'error': 'Legacy endpoint - FCM kullaniliyor'}), 410


# ==================== Guest Push Notifications ====================

@api_admin_bp.route('/api/guest/subscribe-push', methods=['POST'])
@csrf.exempt
def guest_subscribe_push():
    """
    Guest icin push notification subscription kaydet

    Request Body:
        {
            "request_id": 123,
            "subscription": {
                "endpoint": "...",
                "keys": {...}
            }
        }
    """
    try:
        data = request.get_json()

        if not data or 'request_id' not in data or 'subscription' not in data:
            return jsonify({'error': 'request_id ve subscription gereklidir'}), 400

        request_id = data['request_id']
        subscription = data['subscription']

        buggy_request = BuggyRequest.query.get(request_id)
        if not buggy_request:
            return jsonify({'error': 'Talep bulunamadi'}), 404

        buggy_request.guest_push_subscription = json.dumps(subscription)
        db.session.commit()

        current_app.logger.info(f'Guest push subscription kaydedildi: request_id={request_id}')

        return jsonify({
            'success': True,
            'message': 'Push subscription kaydedildi'
        }), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Guest push subscription hatasi: {str(e)}')
        return jsonify({'error': str(e)}), 500
