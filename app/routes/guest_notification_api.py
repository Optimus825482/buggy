"""
Guest Notification API Routes
FCM token kaydetme ve bildirim gönderme
Powered by Erkan ERDEM
"""
from flask import Blueprint, jsonify, request, current_app
from app import db, csrf
from app.models.request import BuggyRequest
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

guest_notification_api_bp = Blueprint('guest_notification_api', __name__)

# CSRF exempt for API endpoints
csrf.exempt(guest_notification_api_bp)

# In-memory storage for guest FCM tokens (request_id -> token mapping)
# Production'da Redis veya database kullanılmalı
GUEST_FCM_TOKENS = {}

# Token TTL configuration (1 hour)
GUEST_TOKEN_TTL_SECONDS = 3600


def cleanup_expired_guest_tokens():
    """
    Expired guest FCM token'larını temizle
    TTL'i dolmuş token'ları sil
    """
    try:
        current_time = datetime.utcnow().replace(tzinfo=None).timestamp()
        expired_tokens = []
        
        for request_id, token_data in list(GUEST_FCM_TOKENS.items()):
            if token_data.get('expires_at', 0) < current_time:
                expired_tokens.append(request_id)
        
        # Remove expired tokens
        for request_id in expired_tokens:
            del GUEST_FCM_TOKENS[request_id]
            logger.info(f'🗑️ Expired guest FCM token removed: Request {request_id}')
        
        if expired_tokens:
            logger.info(f'🧹 Cleaned up {len(expired_tokens)} expired guest FCM tokens')
            
    except Exception as e:
        logger.error(f'❌ Error cleaning up expired tokens: {str(e)}')


def get_guest_token(request_id: int) -> str:
    """
    Guest FCM token'ını al (TTL kontrolü ile)
    
    Args:
        request_id: Request ID
    
    Returns:
        str: FCM token veya None
    """
    token_data = GUEST_FCM_TOKENS.get(request_id)
    
    if not token_data:
        return None
    
    # Check if expired
    current_time = datetime.utcnow().replace(tzinfo=None).timestamp()
    if token_data.get('expires_at', 0) < current_time:
        logger.warning(f'⚠️ Guest FCM token expired for request {request_id}')
        del GUEST_FCM_TOKENS[request_id]
        return None
    
    return token_data.get('token')


@guest_notification_api_bp.route('/guest/register-fcm-token', methods=['POST'])
def register_guest_fcm_token():
    """
    Guest kullanıcısının FCM token'ını kaydet
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'Veri gönderilmedi'
            }), 400
        
        token = data.get('token')
        request_id = data.get('request_id')
        
        if not token:
            return jsonify({
                'success': False,
                'message': 'FCM token gerekli'
            }), 400
        
        if not request_id:
            return jsonify({
                'success': False,
                'message': 'Request ID gerekli'
            }), 400
        
        # Token'ı kaydet (request_id ile ilişkilendir) with TTL
        current_utc = datetime.utcnow().replace(tzinfo=None)
        GUEST_FCM_TOKENS[request_id] = {
            'token': token,
            'registered_at': current_utc,
            'expires_at': current_utc.timestamp() + GUEST_TOKEN_TTL_SECONDS
        }
        
        logger.info(f'✅ Guest FCM token registered for request {request_id} (TTL: {GUEST_TOKEN_TTL_SECONDS}s)')
        
        # Cleanup expired tokens
        cleanup_expired_guest_tokens()
        
        return jsonify({
            'success': True,
            'message': 'FCM token başarıyla kaydedildi'
        }), 200
        
    except Exception as e:
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
        
        # FCM token'ı al
        token_data = GUEST_FCM_TOKENS.get(request_id)
        if not token_data:
            logger.warning(f'⚠️ No FCM token found for request {request_id}')
            return jsonify({
                'success': False,
                'message': 'FCM token bulunamadı'
            }), 404
        
        fcm_token = token_data['token']
        
        # Bildirim içeriğini hazırla
        data = request.get_json() or {}
        notification_type = data.get('type', 'status_update')
        
        # Status'a göre mesaj oluştur
        status_messages = {
            'accepted': {
                'title': '🎉 Shuttle Kabul Edildi!',
                'body': f'Shuttle size doğru geliyor. Buggy: {buggy_request.buggy.code if buggy_request.buggy else "N/A"}'
            },
            'in_progress': {
                'title': '🚗 Shuttle Yolda!',
                'body': 'Sürücü konumunuza yaklaşıyor'
            },
            'completed': {
                'title': '✅ Shuttle Ulaştı!',
                'body': 'İyi günler dileriz'
            },
            'cancelled': {
                'title': '❌ Talep İptal Edildi',
                'body': 'Shuttle talebiniz iptal edildi'
            }
        }
        
        status = buggy_request.status.value if hasattr(buggy_request.status, 'value') else str(buggy_request.status)
        message_data = status_messages.get(status, {
            'title': 'Shuttle Call',
            'body': 'Talep durumunuz güncellendi'
        })
        
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


def send_fcm_http_notification(token, message_data, status):
    """
    Firebase Admin SDK kullanarak bildirim gönder
    Returns: (success: bool, message: str)
    """
    try:
        import firebase_admin
        from firebase_admin import messaging, credentials
        
        # Firebase Admin SDK'yı başlat (eğer başlatılmamışsa)
        if not firebase_admin._apps:
            cred_path = current_app.config.get('FIREBASE_SERVICE_ACCOUNT_PATH', 'firebase-service-account.json')
            try:
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
                logger.info('✅ Firebase Admin SDK initialized')
            except Exception as init_error:
                logger.error(f'❌ Firebase Admin SDK init error: {str(init_error)}')
                return False, f'Firebase başlatılamadı: {str(init_error)}'
        
        # FCM mesajı oluştur
        message = messaging.Message(
            notification=messaging.Notification(
                title=message_data['title'],
                body=message_data['body']
            ),
            data={
                'type': 'status_update',
                'status': status,
                'priority': 'high' if status == 'accepted' else 'normal'
            },
            token=token,
            webpush=messaging.WebpushConfig(
                notification=messaging.WebpushNotification(
                    title=message_data['title'],
                    body=message_data['body'],
                    icon='/static/icons/Icon-192.png',
                    badge='/static/icons/Icon-96.png',
                    vibrate=[200, 100, 200, 100, 200],
                    require_interaction=(status == 'accepted')
                )
                # fcm_options kaldırıldı - HTTP URL hatası önlendi
            )
        )
        
        # Bildirimi gönder
        response = messaging.send(message)
        logger.info(f'✅ FCM notification sent successfully: {response}')
        return True, 'Bildirim başarıyla gönderildi'
        
    except Exception as e:
        logger.error(f'❌ FCM send error: {str(e)}')
        import traceback
        logger.error(traceback.format_exc())
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
    Kayıtlı FCM token'ları göster (debug için)
    """
    try:
        tokens_info = {}
        for req_id, token_data in GUEST_FCM_TOKENS.items():
            tokens_info[req_id] = {
                'token_preview': token_data['token'][:20] + '...',
                'registered_at': token_data['registered_at']
            }
        
        return jsonify({
            'success': True,
            'total_tokens': len(GUEST_FCM_TOKENS),
            'tokens': tokens_info
        }), 200
        
    except Exception as e:
        logger.error(f'❌ Debug tokens error: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'Token listesi alınamadı: {str(e)}'
        }), 500
