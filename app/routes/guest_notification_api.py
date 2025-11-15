"""
Guest Notification API Routes
FCM token kaydetme ve bildirim gönderme
Powered by Erkan ERDEM
"""
from flask import Blueprint, jsonify, request, current_app
from app import db, csrf
from app.models.request import BuggyRequest
from app.constants import (
    GUEST_TOKEN_TTL_SECONDS,
    REQUEST_STATUS_MESSAGES,
    ERROR_MESSAGES,
    SUCCESS_MESSAGES,
    HttpStatus
)
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

guest_notification_api_bp = Blueprint('guest_notification_api', __name__)

# CSRF exempt for API endpoints
csrf.exempt(guest_notification_api_bp)


def cleanup_expired_guest_tokens():
    """
    ✅ DATABASE VERSION: Expired guest FCM token'larını temizle
    TTL'i dolmuş token'ları database'den sil
    """
    try:
        current_time = datetime.utcnow().replace(tzinfo=None)

        # Find and clear expired tokens in database
        expired_requests = BuggyRequest.query.filter(
            BuggyRequest.guest_fcm_token.isnot(None),
            BuggyRequest.guest_fcm_token_expires_at < current_time
        ).all()

        count = 0
        for req in expired_requests:
            req.guest_fcm_token = None
            req.guest_fcm_token_expires_at = None
            count += 1
            logger.info(f'🗑️ Expired guest FCM token removed: Request {req.id}')

        if count > 0:
            db.session.commit()
            logger.info(f'🧹 Cleaned up {count} expired guest FCM tokens from database')

    except Exception as e:
        db.session.rollback()
        logger.error(f'❌ Error cleaning up expired tokens: {str(e)}')


def get_guest_token(request_id: int) -> str:
    """
    ✅ DATABASE VERSION: Guest FCM token'ını al (TTL kontrolü ile)

    Args:
        request_id: Request ID

    Returns:
        str: FCM token veya None
    """
    try:
        buggy_request = BuggyRequest.query.get(request_id)

        if not buggy_request or not buggy_request.guest_fcm_token:
            return None

        # Check if expired
        current_time = datetime.utcnow().replace(tzinfo=None)
        if buggy_request.guest_fcm_token_expires_at and buggy_request.guest_fcm_token_expires_at < current_time:
            logger.warning(f'⚠️ Guest FCM token expired for request {request_id}')
            # Clear expired token
            buggy_request.guest_fcm_token = None
            buggy_request.guest_fcm_token_expires_at = None
            db.session.commit()
            return None

        return buggy_request.guest_fcm_token

    except Exception as e:
        logger.error(f'❌ Error getting guest token: {str(e)}')
        return None


@guest_notification_api_bp.route('/guest/register-fcm-token', methods=['POST'])
def register_guest_fcm_token():
    """
    ✅ DATABASE VERSION: Guest kullanıcısının FCM token'ını kaydet
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'message': ERROR_MESSAGES['MISSING_FIELD'].format(field='Data')
            }), HttpStatus.BAD_REQUEST

        token = data.get('token')
        request_id = data.get('request_id')

        if not token:
            return jsonify({
                'success': False,
                'message': ERROR_MESSAGES['MISSING_FIELD'].format(field='FCM token')
            }), HttpStatus.BAD_REQUEST

        if not request_id:
            return jsonify({
                'success': False,
                'message': ERROR_MESSAGES['MISSING_FIELD'].format(field='Request ID')
            }), HttpStatus.BAD_REQUEST

        # Find the request
        buggy_request = BuggyRequest.query.get(request_id)
        if not buggy_request:
            return jsonify({
                'success': False,
                'message': ERROR_MESSAGES['NOT_FOUND'].format(entity='Request')
            }), HttpStatus.NOT_FOUND

        # ✅ Store token in database with TTL
        current_utc = datetime.utcnow().replace(tzinfo=None)
        buggy_request.guest_fcm_token = token
        buggy_request.guest_fcm_token_expires_at = current_utc + timedelta(seconds=GUEST_TOKEN_TTL_SECONDS)

        db.session.commit()

        logger.info(f'✅ Guest FCM token saved to database for request {request_id} (TTL: {GUEST_TOKEN_TTL_SECONDS}s)')

        # Cleanup expired tokens
        cleanup_expired_guest_tokens()

        return jsonify({
            'success': True,
            'message': SUCCESS_MESSAGES['TOKEN_REGISTERED']
        }), HttpStatus.OK

    except Exception as e:
        db.session.rollback()
        logger.error(f'❌ Error registering guest FCM token: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'Token kaydedilemedi: {str(e)}'
        }), 500


@guest_notification_api_bp.route('/guest/send-notification/<int:request_id>', methods=['POST'])
def send_guest_notification(request_id):
    """
    Guest kullanıcısına bildirim gönder
    Bu endpoint backend tarafından (request status değişikliklerinde) çağrılır
    """
    try:
        # Request'i kontrol et
        buggy_request = BuggyRequest.query.get(request_id)
        if not buggy_request:
            return jsonify({
                'success': False,
                'message': 'Request bulunamadı'
            }), 404

        # ✅ DATABASE VERSION: FCM token'ı al
        fcm_token = get_guest_token(request_id)
        if not fcm_token:
            logger.warning(f'⚠️ No FCM token found for request {request_id}')
            return jsonify({
                'success': False,
                'message': 'FCM token bulunamadı'
            }), 404
        
        # Bildirim içeriğini hazırla
        data = request.get_json() or {}
        notification_type = data.get('type', 'status_update')
        
        # ✅ CODE REFACTORING: Use centralized status messages
        status = buggy_request.status.value if hasattr(buggy_request.status, 'value') else str(buggy_request.status)
        status_lower = status.lower() if status else 'pending'

        # Get message template from constants
        message_template = REQUEST_STATUS_MESSAGES.get(status_lower, {
            'title': 'Shuttle Call',
            'body': 'Talep durumunuz güncellendi'
        })

        # Format message with actual data
        buggy_code = buggy_request.buggy.code if buggy_request.buggy else "N/A"
        message_data = {
            'title': message_template['title'],
            'body': message_template['body'].format(buggy_code=buggy_code) if '{buggy_code}' in message_template['body'] else message_template['body']
        }
        
        # FCM bildirimi gönder
        try:
            import firebase_admin
            from firebase_admin import messaging, credentials
            
            # Firebase Admin SDK'yı başlat (eğer başlatılmamışsa)
            if not firebase_admin._apps:
                # Firebase service account key dosyası gerekli
                # Production'da environment variable'dan alınmalı
                cred_path = current_app.config.get('FIREBASE_CREDENTIALS_PATH')
                if cred_path:
                    cred = credentials.Certificate(cred_path)
                    firebase_admin.initialize_app(cred)
                else:
                    logger.warning('⚠️ Firebase credentials not configured')
                    # Fallback: Web Push API kullan (FCM HTTP v1)
                    return send_fcm_http_notification(fcm_token, message_data, status)
            
            # FCM mesajı oluştur
            message = messaging.Message(
                notification=messaging.Notification(
                    title=message_data['title'],
                    body=message_data['body'],
                    image='/static/icons/Icon-192.png'
                ),
                data={
                    'type': notification_type,
                    'request_id': str(request_id),
                    'status': status,
                    'priority': 'high' if status == 'accepted' else 'normal'
                },
                token=fcm_token,
                android=messaging.AndroidConfig(
                    priority='high',
                    notification=messaging.AndroidNotification(
                        sound='default',
                        channel_id='shuttle_updates'
                    )
                ),
                apns=messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(
                            sound='default',
                            badge=1
                        )
                    )
                ),
                webpush=messaging.WebpushConfig(
                    notification=messaging.WebpushNotification(
                        icon='/static/icons/Icon-192.png',
                        badge='/static/icons/Icon-96.png',
                        vibrate=[200, 100, 200, 100, 200],
                        require_interaction=(status == 'accepted')
                    )
                )
            )
            
            # Bildirimi gönder
            response = messaging.send(message)
            logger.info(f'✅ FCM notification sent successfully: {response}')
            
            return jsonify({
                'success': True,
                'message': 'Bildirim başarıyla gönderildi',
                'response': response
            }), 200
            
        except Exception as fcm_error:
            logger.error(f'❌ FCM send error: {str(fcm_error)}')
            # Fallback: HTTP API kullan
            success, message = send_fcm_http_notification(fcm_token, message_data, status)
            if success:
                return jsonify({'success': True, 'message': message}), 200
            else:
                return jsonify({'success': False, 'message': message}), 500
        
    except Exception as e:
        logger.error(f'❌ Error sending guest notification: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'Bildirim gönderilemedi: {str(e)}'
        }), 500


def send_fcm_http_notification(token, message_data, status, request_id=None):
    """
    ✅ FIXED: FCMNotificationService kullanarak bildirim gönder
    Returns: (success: bool, message: str)
    """
    try:
        from app.services.fcm_notification_service import FCMNotificationService

        logger.info('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
        logger.info(f'📤 [GUEST_FCM] Sending notification to guest')
        logger.info(f'   Type: {status}')
        logger.info(f'   Title: {message_data["title"]}')
        logger.info(f'   Request ID: {request_id}')
        logger.info(f'   Token: {token[:20]}...')
        logger.info('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')

        # FCM Service kullan (env variable desteği ile)
        success = FCMNotificationService.send_to_token(
            token=token,
            title=message_data['title'],
            body=message_data['body'],
            data={
                'type': 'status_update',
                'status': status,
                'request_id': str(request_id) if request_id else '',
                'priority': 'high' if status == 'accepted' else 'normal',
                'click_action': f'/guest/status/{request_id}' if request_id else '/'
            },
            priority='high' if status == 'accepted' else 'normal',
            sound='default',
            retry=True,
            click_action=f'/guest/status/{request_id}' if request_id else '/'
        )

        if success:
            logger.info('✅ [GUEST_FCM] Notification sent successfully!')
            logger.info('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
            return True, 'Bildirim başarıyla gönderildi'
        else:
            logger.error('❌ [GUEST_FCM] Notification failed!')
            logger.error('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
            return False, 'Bildirim gönderilemedi'

    except Exception as e:
        logger.error(f'❌ [GUEST_FCM] Error: {str(e)}')
        import traceback
        logger.error(traceback.format_exc())
        logger.error('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
        return False, f'Bildirim gönderilemedi: {str(e)}'


@guest_notification_api_bp.route('/guest/test-notification', methods=['POST'])
def test_guest_notification():
    """
    Test bildirimi gönder
    """
    try:
        data = request.get_json()
        request_id = data.get('request_id')
        
        if not request_id:
            return jsonify({
                'success': False,
                'message': 'Request ID gerekli'
            }), 400
        
        # Test bildirimi gönder
        return send_guest_notification(request_id)
        
    except Exception as e:
        logger.error(f'❌ Test notification error: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'Test bildirimi gönderilemedi: {str(e)}'
        }), 500


@guest_notification_api_bp.route('/guest/debug-tokens', methods=['GET'])
def debug_tokens():
    """
    ✅ DATABASE VERSION: Kayıtlı FCM token'ları göster (debug için)
    """
    try:
        # Query all requests with active FCM tokens
        current_time = datetime.utcnow().replace(tzinfo=None)
        active_tokens = BuggyRequest.query.filter(
            BuggyRequest.guest_fcm_token.isnot(None),
            BuggyRequest.guest_fcm_token_expires_at > current_time
        ).all()

        tokens_info = {}
        for req in active_tokens:
            tokens_info[req.id] = {
                'token_preview': req.guest_fcm_token[:20] + '...' if req.guest_fcm_token else 'N/A',
                'expires_at': req.guest_fcm_token_expires_at.isoformat() if req.guest_fcm_token_expires_at else None,
                'status': req.status.value if req.status else None,
                'guest_name': req.guest_name
            }

        return jsonify({
            'success': True,
            'total_tokens': len(active_tokens),
            'tokens': tokens_info
        }), 200

    except Exception as e:
        logger.error(f'❌ Debug tokens error: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'Token listesi alınamadı: {str(e)}'
        }), 500
