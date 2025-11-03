"""
Buggy Call - Push Notification Service
"""
from pywebpush import webpush, WebPushException
import json
import os
from app import db
from app.models.user import SystemUser


class NotificationService:
    """Service for push notifications"""
    
    # VAPID keys (should be in environment variables)
    VAPID_PRIVATE_KEY = os.getenv('VAPID_PRIVATE_KEY')
    VAPID_PUBLIC_KEY = os.getenv('VAPID_PUBLIC_KEY')
    VAPID_CLAIMS = {
        "sub": "mailto:admin@buggycall.com"
    }
    
    @staticmethod
    def send_notification(subscription_info, title, body, data=None):
        """
        Send push notification
        
        Args:
            subscription_info: Web push subscription info
            title: Notification title
            body: Notification body
            data: Additional data
        
        Returns:
            Boolean indicating success
        """
        if not NotificationService.VAPID_PRIVATE_KEY:
            print("Warning: VAPID keys not configured")
            return False
        
        try:
            notification_data = {
                "title": title,
                "body": body,
                "icon": "/static/icons/Icon-192.png",
                "badge": "/static/icons/Icon-72.png",
                "data": data or {}
            }
            
            webpush(
                subscription_info=subscription_info,
                data=json.dumps(notification_data),
                vapid_private_key=NotificationService.VAPID_PRIVATE_KEY,
                vapid_claims=NotificationService.VAPID_CLAIMS
            )
            
            return True
            
        except WebPushException as e:
            print(f"Push notification error: {e}")
            return False
        except Exception as e:
            print(f"Notification error: {e}")
            return False
    
    @staticmethod
    def notify_new_request(request_obj):
        """Notify drivers about new request"""
        # Get available drivers in the hotel
        from app.models.buggy import Buggy
        from app.services.audit_service import AuditService
        
        buggies = Buggy.query.filter_by(
            hotel_id=request_obj.hotel_id,
            status='available'
        ).all()
        
        notification_count = 0
        for buggy in buggies:
            if buggy.driver_id:
                driver = SystemUser.query.get(buggy.driver_id)
                if driver and hasattr(driver, 'push_subscription'):
                    success = NotificationService.send_notification(
                        subscription_info=driver.push_subscription,
                        title="Yeni Buggy Talebi",
                        body=f"{request_obj.location.name} - Oda: {request_obj.room_number or 'Belirtilmedi'}",
                        data={
                            'type': 'new_request',
                            'request_id': request_obj.id
                        }
                    )
                    if success:
                        notification_count += 1
        
        # Log bulk notification if multiple drivers notified
        if notification_count > 1:
            AuditService.log_action(
                action='bulk_push_notification_sent',
                entity_type='notification',
                entity_id=request_obj.id,
                new_values={
                    'notification_type': 'new_request',
                    'recipient_count': notification_count,
                    'request_id': request_obj.id
                },
                hotel_id=request_obj.hotel_id
            )
    
    @staticmethod
    def notify_request_accepted(request_obj):
        """Notify guest that request was accepted"""
        # If we have guest device info, send notification
        if hasattr(request_obj, 'guest_device_id') and request_obj.guest_device_id:
            NotificationService.send_notification(
                subscription_info=request_obj.guest_device_id,
                title="Buggy Kabul Edildi",
                body=f"Buggy'niz yola çıktı. {request_obj.buggy.code}",
                data={
                    'type': 'request_accepted',
                    'request_id': request_obj.id
                }
            )
    
    @staticmethod
    def notify_request_completed(request_obj):
        """Notify guest that buggy has arrived"""
        if hasattr(request_obj, 'guest_device_id') and request_obj.guest_device_id:
            NotificationService.send_notification(
                subscription_info=request_obj.guest_device_id,
                title="Buggy Geldi!",
                body="Buggy'niz konumunuza ulaştı. İyi yolculuklar!",
                data={
                    'type': 'request_completed',
                    'request_id': request_obj.id
                }
            )
    
    @staticmethod
    def generate_vapid_keys():
        """Generate VAPID keys for push notifications"""
        from pywebpush import webpush
        from py_vapid import Vapid01
        
        vapid = Vapid01()
        vapid.generate_keys()
        
        return {
            'public_key': vapid.public_key.export_public(),
            'private_key': vapid.private_key.export()
        }
