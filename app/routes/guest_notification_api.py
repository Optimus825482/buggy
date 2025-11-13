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
        
        # Token'ı kaydet (request_id ile ilişkilendir)
        GUEST_FCM_TOKENS[request_id] = {
            'token': token,
            'registered_at': datetime.utcnow().isoformat()
        }
        
        logger.info(f'✅ Guest FCM token registered for request {request_id}')
        
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
            return send_fcm_http_notification(fcm_token, message_data, status)
        
    except Exception as e:
        logger.error(f'❌ Error sending guest notification: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'Bildirim gönderilemedi: {str(e)}'
        }), 500


def send_fcm_http_notification(token, message_data, status):
    """
    FCM HTTP v1 API kullanarak bildirim gönder (fallback)
    """
    try:
        import requests
        
        # FCM server key gerekli
        server_key = current_app.config.get('FCM_SERVER_KEY')
        if not server_key:
            logger.error('❌ FCM_SERVER_KEY not configured')
            return jsonify({
                'success': False,
                'message': 'FCM yapılandırması eksik'
            }), 500
        
        # FCM HTTP v1 endpoint
        url = 'https://fcm.googleapis.com/fcm/send'
        
        headers = {
            'Authorization': f'key={server_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'to': token,
            'notification': {
                'title': message_data['title'],
                'body': message_data['body'],
                'icon': '/static/icons/Icon-192.png',
                'badge': '/static/icons/Icon-96.png',
                'vibrate': [200, 100, 200, 100, 200],
                'requireInteraction': (status == 'accepted')
            },
            'data': {
                'type': 'status_update',
                'status': status,
                'priority': 'high' if status == 'accepted' else 'normal'
            },
            'priority': 'high'
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        if response.status_code == 200:
            logger.info(f'✅ FCM HTTP notification sent successfully')
            return jsonify({
                'success': True,
                'message': 'Bildirim başarıyla gönderildi (HTTP)'
            }), 200
        else:
            logger.error(f'❌ FCM HTTP error: {response.status_code} - {response.text}')
            return jsonify({
                'success': False,
                'message': f'FCM HTTP hatası: {response.status_code}'
            }), 500
            
    except Exception as e:
        logger.error(f'❌ FCM HTTP send error: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'HTTP bildirim gönderilemedi: {str(e)}'
        }), 500


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
