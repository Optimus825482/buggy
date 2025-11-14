"""
Buggy Call - FCM Token Management API
Session-based authentication
"""
from flask import Blueprint, request, jsonify, session
from app.services.fcm_notification_service import FCMNotificationService
from app.models.user import SystemUser
from app import db
import logging

logger = logging.getLogger(__name__)

fcm_api = Blueprint('fcm_api', __name__, url_prefix='/api/fcm')


@fcm_api.route('/register-token', methods=['POST'])
def register_token():
    """
    FCM token kaydet
    
    Request Body:
        {
            "token": "fcm_device_token"
        }
    
    Returns:
        Success message
    """
    try:
        data = request.get_json()
        token = data.get('token')
        
        if not token:
            return jsonify({'success': False, 'message': 'Token gereklidir'}), 400
        
        # Kullanıcı ID'sini session'dan al
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'success': False, 'message': 'Oturum bulunamadı'}), 401
        
        # Token'ı kaydet
        success = FCMNotificationService.register_token(user_id, token)
        
        if success:
            logger.info(f"✅ FCM token kaydedildi: User {user_id}")
            return jsonify({
                'success': True,
                'message': 'FCM token başarıyla kaydedildi',
                'user_id': user_id
            }), 200
        else:
            logger.error(f"❌ FCM token kaydedilemedi: User {user_id}")
            return jsonify({'success': False, 'message': 'Token kaydedilemedi'}), 500
            
    except Exception as e:
        logger.error(f"❌ FCM token kayıt hatası: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@fcm_api.route('/refresh-token', methods=['POST'])
def refresh_token():
    """
    FCM token'ı yenile
    
    Request Body:
        {
            "old_token": "old_fcm_token",
            "new_token": "new_fcm_token"
        }
    
    Returns:
        Success message
    """
    try:
        data = request.get_json()
        old_token = data.get('old_token')
        new_token = data.get('new_token')
        
        if not old_token or not new_token:
            return jsonify({'success': False, 'message': 'Eski ve yeni token gereklidir'}), 400
        
        # Kullanıcı ID'sini session'dan al
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'success': False, 'message': 'Oturum bulunamadı'}), 401
        
        # Token'ı yenile
        success = FCMNotificationService.refresh_token(user_id, old_token, new_token)
        
        if success:
            logger.info(f"🔄 FCM token yenilendi: User {user_id}")
            return jsonify({
                'success': True,
                'message': 'FCM token başarıyla yenilendi',
                'user_id': user_id
            }), 200
        else:
            logger.error(f"❌ FCM token yenilenemedi: User {user_id}")
            return jsonify({'success': False, 'message': 'Token yenilenemedi'}), 500
            
    except Exception as e:
        logger.error(f"❌ FCM token yenileme hatası: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@fcm_api.route('/test-notification', methods=['POST'])
def test_notification():
    """
    Test notification gönder
    
    Request Body:
        {
            "title": "Test Başlık",
            "body": "Test Mesaj"
        }
    
    Returns:
        Delivery status
    """
    try:
        data = request.get_json()
        title = data.get('title', '🔔 Test Bildirimi')
        body = data.get('body', 'Bu bir test bildirimidir.')
        
        # Kullanıcı ID'sini session'dan al
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'success': False, 'message': 'Oturum bulunamadı'}), 401
        
        # Kullanıcının token'ını al
        user = SystemUser.query.get(user_id)
        if not user or not user.fcm_token:
            return jsonify({'success': False, 'message': 'FCM token bulunamadı'}), 404
        
        # Test bildirimi gönder
        success = FCMNotificationService.send_to_token(
            token=user.fcm_token,
            title=title,
            body=body,
            data={'type': 'test', 'timestamp': str(db.func.now())},
            priority='high'
        )
        
        if success:
            logger.info(f"✅ Test bildirimi gönderildi: User {user_id}")
            return jsonify({
                'success': True,
                'message': 'Test bildirimi başarıyla gönderildi',
                'user_id': user_id,
                'status': 'sent'
            }), 200
        else:
            logger.error(f"❌ Test bildirimi gönderilemedi: User {user_id}")
            return jsonify({
                'success': False,
                'message': 'Test bildirimi gönderilemedi',
                'status': 'failed'
            }), 500
            
    except Exception as e:
        logger.error(f"❌ Test bildirimi hatası: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500
