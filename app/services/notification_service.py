"""
Buggy Call - Push Notification Service
Enhanced with priority levels, rich media, and comprehensive logging
"""
from pywebpush import webpush, WebPushException
import json
import os
from datetime import datetime, timedelta
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
    def send_notification(subscription_info, title, body, data=None, sound=None, vibrate=None):
        """
        Send push notification
        
        Args:
            subscription_info: Web push subscription info
            title: Notification title
            body: Notification body
            data: Additional data
            sound: Sound file path (optional)
            vibrate: Vibration pattern (optional, e.g., [200, 100, 200])
        
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
            
            # Ses ekle (varsa)
            if sound:
                notification_data["sound"] = sound
            
            # Titreşim ekle (varsa)
            if vibrate:
                notification_data["vibrate"] = vibrate
            
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
        """
        Notify drivers about new request - LEGACY METHOD
        Redirects to enhanced v2 method
        """
        return NotificationService.notify_new_request_v2(request_obj)
    
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

    
    @staticmethod
    def send_notification_v2(
        subscription_info,
        title,
        body,
        notification_type='general',
        priority='normal',
        data=None,
        image=None,
        actions=None
    ):
        """
        Enhanced notification sending with priority and rich media
        
        Args:
            subscription_info: Web push subscription info
            title: Notification title
            body: Notification body
            notification_type: Type (new_request, status_update, etc.)
            priority: Priority level (high, normal, low)
            data: Additional data
            image: Image URL for rich notification
            actions: Custom action buttons
        
        Returns:
            Boolean indicating success
        """
        if not NotificationService.VAPID_PRIVATE_KEY:
            print("Warning: VAPID keys not configured")
            return False
        
        # Build notification payload
        notification_data = {
            "title": title,
            "body": body,
            "icon": "/static/icons/Icon-192.png",
            "badge": "/static/icons/Icon-96.png",
            "type": notification_type,
            "priority": priority,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data or {}
        }
        
        # Add rich media
        if image:
            notification_data["image"] = image
        
        # Add custom actions
        if actions:
            notification_data["actions"] = actions
        
        # Priority-based configuration
        if priority == 'high':
            notification_data["sound"] = "/static/sounds/urgent.mp3"
            notification_data["vibrate"] = [200, 100, 200, 100, 200, 100, 200]
            notification_data["requireInteraction"] = True
        elif priority == 'normal':
            notification_data["sound"] = "/static/sounds/notification.mp3"
            notification_data["vibrate"] = [200, 100, 200]
        else:  # low
            notification_data["sound"] = "/static/sounds/subtle.mp3"
            notification_data["vibrate"] = [100]
        
        try:
            # Send via Web Push
            response = webpush(
                subscription_info=subscription_info,
                data=json.dumps(notification_data),
                vapid_private_key=NotificationService.VAPID_PRIVATE_KEY,
                vapid_claims=NotificationService.VAPID_CLAIMS,
                ttl=86400  # 24 hours TTL
            )
            
            # Log delivery attempt
            NotificationService._log_delivery(
                subscription_info,
                notification_data,
                'sent',
                response.status_code if hasattr(response, 'status_code') else 200
            )
            
            return True
            
        except WebPushException as e:
            # Handle specific errors
            if hasattr(e, 'response') and e.response and e.response.status_code == 410:
                # Subscription expired - remove it
                NotificationService._remove_expired_subscription(subscription_info)
            
            NotificationService._log_delivery(
                subscription_info,
                notification_data,
                'failed',
                str(e)
            )
            
            return False
        except Exception as e:
            print(f"Notification error: {e}")
            NotificationService._log_delivery(
                subscription_info,
                notification_data,
                'failed',
                str(e)
            )
            return False
    
    @staticmethod
    def _log_delivery(subscription_info, notification_data, status, response_info):
        """Log notification delivery attempt"""
        try:
            from app.models.notification_log import NotificationLog
            
            # Extract user_id from subscription or data
            user_id = None
            if isinstance(subscription_info, dict) and 'user_id' in subscription_info:
                user_id = subscription_info['user_id']
            elif 'data' in notification_data and 'user_id' in notification_data['data']:
                user_id = notification_data['data']['user_id']
            
            if not user_id:
                # Try to find user by subscription
                user = SystemUser.query.filter(
                    SystemUser.push_subscription.isnot(None)
                ).first()
                if user:
                    user_id = user.id
            
            if user_id:
                log = NotificationLog(
                    user_id=user_id,
                    notification_type=notification_data.get('type', 'general'),
                    priority=notification_data.get('priority', 'normal'),
                    title=notification_data.get('title', ''),
                    body=notification_data.get('body', ''),
                    status=status,
                    error_message=str(response_info) if status == 'failed' else None,
                    sent_at=datetime.utcnow()
                )
                db.session.add(log)
                db.session.commit()
        except Exception as e:
            print(f"Error logging notification delivery: {e}")
            db.session.rollback()
    
    @staticmethod
    def _remove_expired_subscription(subscription_info):
        """Remove expired push subscription"""
        try:
            # Find user with this subscription and clear it
            users = SystemUser.query.filter(
                SystemUser.push_subscription.isnot(None)
            ).all()
            
            for user in users:
                if user.push_subscription == subscription_info:
                    user.push_subscription = None
                    user.push_subscription_date = None
                    db.session.commit()
                    print(f"Removed expired subscription for user {user.id}")
                    break
        except Exception as e:
            print(f"Error removing expired subscription: {e}")
            db.session.rollback()
    
    @staticmethod
    def notify_new_request_v2(request_obj):
        """Enhanced new request notification with rich media"""
        from app.models.buggy import Buggy
        from app.services.audit_service import AuditService
        
        buggies = Buggy.query.filter_by(
            hotel_id=request_obj.hotel_id,
            status='available'
        ).all()
        
        # Build notification content
        room_info = f"Oda {request_obj.room_number}" if request_obj.room_number else "Misafir"
        guest_info = f" - {request_obj.guest_name}" if request_obj.guest_name else ""
        
        # Generate map image (if location has coordinates)
        map_image = None
        if hasattr(request_obj.location, 'latitude') and hasattr(request_obj.location, 'longitude'):
            if request_obj.location.latitude and request_obj.location.longitude:
                map_image = f"/api/map/thumbnail?lat={request_obj.location.latitude}&lng={request_obj.location.longitude}"
        
        notification_count = 0
        for buggy in buggies:
            if buggy.driver_id:
                driver = SystemUser.query.get(buggy.driver_id)
                if driver and driver.push_subscription:
                    success = NotificationService.send_notification_v2(
                        subscription_info=driver.push_subscription,
                        title="🚗 Yeni Buggy Talebi!",
                        body=f"📍 {request_obj.location.name}\n🏨 {room_info}{guest_info}",
                        notification_type='new_request',
                        priority='high',
                        data={
                            'request_id': request_obj.id,
                            'location_id': request_obj.location_id,
                            'url': '/driver/dashboard',
                            'user_id': driver.id
                        },
                        image=map_image,
                        actions=[
                            {'action': 'accept', 'title': '✅ Kabul Et'},
                            {'action': 'details', 'title': '📋 Detaylar'}
                        ]
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
        
        return notification_count
    
    @staticmethod
    def retry_failed_notifications():
        """Retry failed notifications with exponential backoff"""
        from app.models.notification_log import NotificationLog
        
        # Get failed notifications from last 24 hours
        failed = NotificationLog.query.filter(
            NotificationLog.status == 'failed',
            NotificationLog.sent_at >= datetime.utcnow() - timedelta(hours=24),
            NotificationLog.retry_count < 3
        ).all()
        
        for log in failed:
            # Calculate backoff delay
            delay = min(300, 30 * (2 ** log.retry_count))  # Max 5 minutes
            
            if (datetime.utcnow() - log.sent_at).total_seconds() >= delay:
                # Retry sending
                user = SystemUser.query.get(log.user_id)
                if user and user.push_subscription:
                    success = NotificationService.send_notification_v2(
                        subscription_info=user.push_subscription,
                        title=log.title,
                        body=log.body,
                        notification_type=log.notification_type,
                        priority=log.priority,
                        data={'user_id': user.id}
                    )
                    
                    if success:
                        log.status = 'sent'
                        log.retry_count += 1
                    else:
                        log.retry_count += 1
                        if log.retry_count >= 3:
                            log.status = 'permanently_failed'
                    
                    db.session.commit()
