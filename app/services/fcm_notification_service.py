"""
Buggy Call - Firebase Cloud Messaging (FCM) Notification Service
Priority-based & Rich Media Support - Optimize edilmiş
"""
import firebase_admin
from firebase_admin import credentials, messaging
import os
import json
from datetime import datetime, timedelta
from app import db
from app.models.user import SystemUser
from app.models.notification_log import NotificationLog
from typing import List, Dict, Optional


class FCMNotificationService:
    """Firebase Cloud Messaging servisi - Optimize edilmiş"""
    
    _initialized = False
    
    @staticmethod
    def initialize():
        """Firebase Admin SDK'yı başlat - Error handling ile"""
        if FCMNotificationService._initialized:
            return True
        
        try:
            firebase_admin.get_app()
            FCMNotificationService._initialized = True
            print("✅ Firebase Admin SDK zaten başlatılmış")
            return True
        except ValueError:
            try:
                service_account_path = os.getenv('FIREBASE_SERVICE_ACCOUNT_PATH', 'firebase-service-account.json')
                
                if not os.path.exists(service_account_path):
                    print(f"❌ Firebase service account dosyası bulunamadı: {service_account_path}")
                    return False
                
                cred = credentials.Certificate(service_account_path)
                firebase_admin.initialize_app(cred)
                FCMNotificationService._initialized = True
                print("✅ Firebase Admin SDK başlatıldı")
                return True
                
            except Exception as e:
                print(f"❌ Firebase Admin SDK başlatma hatası: {str(e)}")
                return False

    @staticmethod
    def send_to_token(
        token: str,
        title: str,
        body: str,
        data: Optional[Dict] = None,
        priority: str = 'high',
        sound: str = 'default',
        badge: Optional[int] = None,
        image: Optional[str] = None,
        click_action: Optional[str] = None
    ) -> bool:
        """
        Tek bir token'a bildirim gönder - Priority-based
        
        Args:
            token: FCM device token
            title: Bildirim başlığı
            body: Bildirim içeriği
            data: Ek veri (dict)
            priority: Öncelik (high/normal/low)
            sound: Ses dosyası
            badge: Badge sayısı
            image: Görsel URL (Rich media)
            click_action: Tıklama aksiyonu
        
        Returns:
            bool: Başarılı ise True
        """
        if not FCMNotificationService.initialize():
            print("❌ Firebase başlatılamadı, bildirim gönderilemedi")
            return False
        
        try:
            # Notification payload
            notification = messaging.Notification(
                title=title,
                body=body,
                image=image
            )
            
            # Android config - Priority-based
            android_priority = 'high' if priority == 'high' else 'normal'
            android_config = messaging.AndroidConfig(
                priority=android_priority,
                notification=messaging.AndroidNotification(
                    sound=sound if priority == 'high' else None,
                    click_action=click_action,
                    icon='/static/icons/Icon-192.png',
                    color='#4CAF50',
                    channel_id='buggy_notifications'
                )
            )
            
            # APNS (iOS) config - Priority-based
            apns_priority = '10' if priority == 'high' else '5'
            apns_config = messaging.APNSConfig(
                headers={'apns-priority': apns_priority},
                payload=messaging.APNSPayload(
                    aps=messaging.Aps(
                        sound=sound if priority == 'high' else None,
                        badge=badge,
                        content_available=True
                    )
                )
            )
            
            # Web push config - Rich media support
            # fcm_options sadece HTTPS URL'ler için kullanılabilir
            webpush_fcm_options = None
            if click_action and click_action.startswith('https://'):
                webpush_fcm_options = messaging.WebpushFCMOptions(link=click_action)
            
            webpush_config = messaging.WebpushConfig(
                notification=messaging.WebpushNotification(
                    title=title,
                    body=body,
                    icon='/static/icons/Icon-192.png',
                    badge='/static/icons/Icon-96.png',
                    image=image,
                    vibrate=[200, 100, 200] if priority == 'high' else None,
                    data=data or {},
                    require_interaction=priority == 'high'
                ),
                fcm_options=webpush_fcm_options
            )
            
            # Message oluştur
            message = messaging.Message(
                token=token,
                notification=notification,
                data=data or {},
                android=android_config,
                apns=apns_config,
                webpush=webpush_config
            )
            
            # Gönder
            response = messaging.send(message)
            print(f"✅ FCM bildirimi gönderildi (Priority: {priority}): {response}")
            
            # Log kaydet
            FCMNotificationService._log_notification(
                token=token,
                title=title,
                body=body,
                status='sent',
                priority=priority,
                response=response
            )
            
            return True
            
        except messaging.UnregisteredError:
            print(f"❌ Token geçersiz veya kayıtsız: {token[:20]}...")
            FCMNotificationService._remove_invalid_token(token)
            return False
            
        except Exception as e:
            print(f"❌ FCM bildirim hatası: {str(e)}")
            FCMNotificationService._log_notification(
                token=token,
                title=title,
                body=body,
                status='failed',
                priority=priority,
                error=str(e)
            )
            return False
    
    @staticmethod
    def send_to_multiple(
        tokens: List[str],
        title: str,
        body: str,
        data: Optional[Dict] = None,
        priority: str = 'high',
        image: Optional[str] = None
    ) -> Dict[str, int]:
        """
        Birden fazla token'a bildirim gönder (Multicast) - Priority-based
        
        Args:
            tokens: FCM token listesi
            title: Bildirim başlığı
            body: Bildirim içeriği
            data: Ek veri
            priority: Öncelik (high/normal/low)
            image: Görsel URL (Rich media)
        
        Returns:
            dict: {'success': başarılı_sayısı, 'failure': başarısız_sayısı}
        """
        if not FCMNotificationService.initialize():
            print("❌ Firebase başlatılamadı")
            return {'success': 0, 'failure': len(tokens)}
        
        if not tokens:
            return {'success': 0, 'failure': 0}
        
        try:
            # Notification
            notification = messaging.Notification(
                title=title,
                body=body,
                image=image
            )
            
            # Android config - Priority-based
            android_priority = 'high' if priority == 'high' else 'normal'
            android_config = messaging.AndroidConfig(
                priority=android_priority,
                notification=messaging.AndroidNotification(
                    sound='default' if priority == 'high' else None,
                    icon='/static/icons/Icon-192.png',
                    color='#4CAF50',
                    channel_id='buggy_notifications'
                )
            )
            
            # Multicast message
            message = messaging.MulticastMessage(
                tokens=tokens,
                notification=notification,
                data=data or {},
                android=android_config
            )
            
            # Gönder
            response = messaging.send_multicast(message)
            
            print(f"✅ Multicast (Priority: {priority}): {response.success_count} başarılı, {response.failure_count} başarısız")
            
            # Başarısız token'ları temizle
            if response.failure_count > 0:
                failed_tokens = [
                    tokens[idx] for idx, resp in enumerate(response.responses)
                    if not resp.success
                ]
                for token in failed_tokens:
                    FCMNotificationService._remove_invalid_token(token)
            
            return {
                'success': response.success_count,
                'failure': response.failure_count
            }
            
        except Exception as e:
            print(f"❌ Multicast hatası: {str(e)}")
            return {'success': 0, 'failure': len(tokens)}

    @staticmethod
    def notify_new_request(request_obj) -> int:
        """
        Yeni talep bildirimi - HIGH PRIORITY + Rich Media
        Tüm müsait sürücülere gönder
        
        Args:
            request_obj: BuggyRequest nesnesi
        
        Returns:
            int: Bildirim gönderilen sürücü sayısı
        """
        from app.models.buggy import Buggy, BuggyStatus
        
        # Müsait buggy'leri bul
        available_buggies = Buggy.query.filter_by(
            hotel_id=request_obj.hotel_id,
            status=BuggyStatus.AVAILABLE
        ).all()
        
        # Sürücü token'larını topla
        tokens = []
        driver_ids = []
        
        for buggy in available_buggies:
            if buggy.driver_id:
                driver = SystemUser.query.get(buggy.driver_id)
                if driver and driver.fcm_token:
                    tokens.append(driver.fcm_token)
                    driver_ids.append(driver.id)
        
        if not tokens:
            print("⚠️ Bildirim gönderilecek sürücü bulunamadı")
            return 0
        
        # Bildirim içeriği
        room_info = f"Oda {request_obj.room_number}" if request_obj.room_number else "Misafir"
        guest_info = f" - {request_obj.guest_name}" if request_obj.guest_name else ""
        
        title = "🚗 Yeni Shuttle Talebi!"
        body = f"📍 {request_obj.location.name}\n🏨 {room_info}{guest_info}"
        
        # Data payload - Action buttons için
        data = {
            'type': 'new_request',
            'request_id': str(request_obj.id),
            'location_id': str(request_obj.location_id),
            'location_name': request_obj.location.name,
            'room_number': request_obj.room_number or '',
            'guest_name': request_obj.guest_name or '',
            'url': '/driver/dashboard',
            'actions': json.dumps([
                {'action': 'accept', 'title': 'Kabul Et'},
                {'action': 'details', 'title': 'Detaylar'}
            ])
        }
        
        # Rich media - Harita thumbnail
        image = None
        try:
            if hasattr(request_obj.location, 'latitude') and request_obj.location.latitude:
                lat = request_obj.location.latitude
                lng = request_obj.location.longitude
                google_maps_key = os.getenv('GOOGLE_MAPS_API_KEY', '')
                if google_maps_key:
                    image = f"https://maps.googleapis.com/maps/api/staticmap?center={lat},{lng}&zoom=15&size=400x200&markers=color:red%7C{lat},{lng}&key={google_maps_key}"
        except Exception as e:
            print(f"⚠️ Harita thumbnail oluşturulamadı: {str(e)}")
        
        # HIGH PRIORITY ile gönder
        result = FCMNotificationService.send_to_multiple(
            tokens=tokens,
            title=title,
            body=body,
            data=data,
            priority='high',  # Yeni talep = HIGH priority
            image=image
        )
        
        # Audit log
        if result['success'] > 0:
            try:
                from app.services.audit_service import AuditService
                AuditService.log_action(
                    action='fcm_notification_sent',
                    entity_type='request',
                    entity_id=request_obj.id,
                    new_values={
                        'notification_type': 'new_request',
                        'priority': 'high',
                        'recipient_count': result['success'],
                        'driver_ids': driver_ids
                    },
                    hotel_id=request_obj.hotel_id
                )
            except Exception as e:
                print(f"⚠️ Audit log hatası: {str(e)}")
        
        return result['success']
    
    @staticmethod
    def notify_request_accepted(request_obj) -> bool:
        """
        Talep kabul edildi bildirimi - NORMAL PRIORITY
        Misafire gönder
        
        Args:
            request_obj: BuggyRequest nesnesi
        
        Returns:
            bool: Başarılı ise True
        """
        if not hasattr(request_obj, 'guest_fcm_token') or not request_obj.guest_fcm_token:
            print("⚠️ Misafir FCM token'ı yok")
            return False
        
        title = "✅ Shuttle Kabul Edildi"
        body = f"Shuttle'ınız yola çıktı! Sürücü: {request_obj.buggy.code}"
        
        data = {
            'type': 'request_accepted',
            'request_id': str(request_obj.id),
            'buggy_code': request_obj.buggy.code,
            'driver_name': request_obj.accepted_by.username if request_obj.accepted_by else ''
        }
        
        return FCMNotificationService.send_to_token(
            token=request_obj.guest_fcm_token,
            title=title,
            body=body,
            data=data,
            priority='normal'  # Kabul = NORMAL priority
        )
    
    @staticmethod
    def notify_request_completed(request_obj) -> bool:
        """
        Talep tamamlandı bildirimi - LOW PRIORITY
        Misafire gönder
        
        Args:
            request_obj: BuggyRequest nesnesi
        
        Returns:
            bool: Başarılı ise True
        """
        if not hasattr(request_obj, 'guest_fcm_token') or not request_obj.guest_fcm_token:
            return False
        
        title = "🎉 Shuttle Geldi!"
        body = "Shuttle'ınız konumunuza ulaştı. İyi yolculuklar!"
        
        data = {
            'type': 'request_completed',
            'request_id': str(request_obj.id)
        }
        
        return FCMNotificationService.send_to_token(
            token=request_obj.guest_fcm_token,
            title=title,
            body=body,
            data=data,
            priority='low'  # Tamamlandı = LOW priority
        )

    @staticmethod
    def _log_notification(token: str, title: str, body: str, status: str, priority: str = 'normal', response: str = None, error: str = None):
        """Bildirim logla - Priority tracking ile"""
        try:
            user = SystemUser.query.filter_by(fcm_token=token).first()
            
            if user:
                log = NotificationLog(
                    user_id=user.id,
                    notification_type='fcm',
                    priority=priority,
                    title=title,
                    body=body,
                    status=status,
                    error_message=error,
                    sent_at=datetime.utcnow()
                )
                db.session.add(log)
                db.session.commit()
        except Exception as e:
            print(f"⚠️ Log kaydedilemedi: {str(e)}")
            db.session.rollback()
    
    @staticmethod
    def _remove_invalid_token(token: str):
        """Geçersiz token'ı temizle - Automatic cleanup"""
        try:
            user = SystemUser.query.filter_by(fcm_token=token).first()
            if user:
                user.fcm_token = None
                user.fcm_token_date = None
                db.session.commit()
                print(f"🗑️ Geçersiz token temizlendi: User {user.id}")
        except Exception as e:
            print(f"⚠️ Token temizlenemedi: {str(e)}")
            db.session.rollback()
    
    @staticmethod
    def register_token(user_id: int, token: str) -> bool:
        """
        Kullanıcı için FCM token kaydet
        
        Args:
            user_id: Kullanıcı ID
            token: FCM device token
        
        Returns:
            bool: Başarılı ise True
        """
        try:
            user = SystemUser.query.get(user_id)
            if not user:
                return False
            
            user.fcm_token = token
            user.fcm_token_date = datetime.utcnow()
            db.session.commit()
            
            print(f"✅ FCM token kaydedildi: User {user_id}")
            return True
            
        except Exception as e:
            print(f"❌ Token kayıt hatası: {str(e)}")
            db.session.rollback()
            return False
    
    @staticmethod
    def refresh_token(user_id: int, old_token: str, new_token: str) -> bool:
        """
        FCM token'ı yenile - Automatic token refresh
        
        Args:
            user_id: Kullanıcı ID
            old_token: Eski token
            new_token: Yeni token
        
        Returns:
            bool: Başarılı ise True
        """
        try:
            user = SystemUser.query.get(user_id)
            if not user:
                return False
            
            # Eski token kontrolü
            if user.fcm_token != old_token:
                print(f"⚠️ Token uyuşmazlığı: User {user_id}")
            
            # Yeni token kaydet
            user.fcm_token = new_token
            user.fcm_token_date = datetime.utcnow()
            db.session.commit()
            
            print(f"🔄 FCM token yenilendi: User {user_id}")
            return True
            
        except Exception as e:
            print(f"❌ Token yenileme hatası: {str(e)}")
            db.session.rollback()
            return False
