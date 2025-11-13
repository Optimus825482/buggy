"""
Buggy Call - Web Push Notification Service
Powered by Erkan ERDEM
"""
from flask import current_app
from pywebpush import webpush, WebPushException
import json


class WebPushService:
    """Web Push Notification servisi"""
    
    @staticmethod
    def send_notification(subscription_info, title, body, data=None):
        """
        Web push notification gönder
        
        Args:
            subscription_info (dict): Push subscription bilgisi
            title (str): Bildirim başlığı
            body (str): Bildirim içeriği
            data (dict): Ek veri
            
        Returns:
            bool: Başarılı ise True
        """
        try:
            # VAPID keys
            vapid_private_key = current_app.config.get('VAPID_PRIVATE_KEY')
            vapid_claims = {
                "sub": f"mailto:{current_app.config.get('VAPID_CLAIM_EMAIL', 'admin@buggycall.com')}"
            }
            
            # Notification payload
            notification_data = {
                "title": title,
                "body": body,
                "icon": "/static/icons/icon-192x192.png",
                "badge": "/static/icons/badge-72x72.png",
                "data": data or {}
            }
            
            # Send push notification
            response = webpush(
                subscription_info=subscription_info,
                data=json.dumps(notification_data),
                vapid_private_key=vapid_private_key,
                vapid_claims=vapid_claims
            )
            
            current_app.logger.info(f'Web push notification gönderildi: {title}')
            return True
            
        except WebPushException as e:
            current_app.logger.error(f'Web push hatası: {str(e)}')
            
            # Subscription geçersizse (410 Gone)
            if e.response and e.response.status_code == 410:
                current_app.logger.warning('Push subscription geçersiz (410 Gone)')
            
            return False
            
        except Exception as e:
            current_app.logger.error(f'Web push genel hatası: {str(e)}')
            return False
    
    @staticmethod
    def send_shuttle_on_way_notification(request_id, location_name, driver_name=None):
        """
        Guest'e "Shuttle yola çıktı" bildirimi gönder
        
        Args:
            request_id (int): Request ID
            location_name (str): Lokasyon adı
            driver_name (str): Sürücü adı (opsiyonel)
            
        Returns:
            bool: Başarılı ise True
        """
        try:
            from app.models.request import BuggyRequest
            
            # Request'i bul
            buggy_request = BuggyRequest.query.get(request_id)
            if not buggy_request or not buggy_request.guest_push_subscription:
                return False
            
            # Subscription'ı parse et
            subscription = json.loads(buggy_request.guest_push_subscription)
            
            # Bildirim içeriği
            title = "🚗 Shuttle Yola Çıktı!"
            body = f"{location_name} konumuna shuttle yola çıktı."
            
            if driver_name:
                body += f" Sürücü: {driver_name}"
            
            data = {
                "request_id": request_id,
                "type": "shuttle_on_way",
                "url": f"/guest/status/{request_id}"
            }
            
            return WebPushService.send_notification(subscription, title, body, data)
            
        except Exception as e:
            current_app.logger.error(f'Shuttle on way notification hatası: {str(e)}')
            return False
    
    @staticmethod
    def send_shuttle_arrived_notification(request_id, location_name):
        """
        Guest'e "Shuttle geldi" bildirimi gönder
        
        Args:
            request_id (int): Request ID
            location_name (str): Lokasyon adı
            
        Returns:
            bool: Başarılı ise True
        """
        try:
            from app.models.request import BuggyRequest
            
            # Request'i bul
            buggy_request = BuggyRequest.query.get(request_id)
            if not buggy_request or not buggy_request.guest_push_subscription:
                return False
            
            # Subscription'ı parse et
            subscription = json.loads(buggy_request.guest_push_subscription)
            
            # Bildirim içeriği
            title = "✅ Shuttle Geldi!"
            body = f"{location_name} konumunda shuttle sizi bekliyor."
            
            data = {
                "request_id": request_id,
                "type": "shuttle_arrived",
                "url": f"/guest/status/{request_id}"
            }
            
            return WebPushService.send_notification(subscription, title, body, data)
            
        except Exception as e:
            current_app.logger.error(f'Shuttle arrived notification hatası: {str(e)}')
            return False
