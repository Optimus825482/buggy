"""
Buggy Call - Firebase Cloud Messaging (FCM) Notification Service
Gelişmiş push notification sistemi
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
    """Firebase Cloud Messaging servisi"""
    
    _initialized = False
    
    @staticmethod
    def initialize():
        """Firebase Admin SDK'yı başlat"""
        if FCMNotificationService._initialized:
            return
        
        try:
            # Eğer zaten başlatılmışsa tekrar başlatma
            firebase_admin.get_app()
            FCMNotificationService._initialized = True
            print("✅ Firebase Admin SDK zaten başlatılmış")
        except ValueError:
            # İlk kez başlatılıyor
            service_account_path = os.getenv('FIREBASE_SERVICE_ACCOUNT_PATH', 'firebase-service-account.json')
            
            if os.path.exists(service_account_path):
                cred = credentials.Certificate(service_account_path)
                firebase_admin.initialize_app(cred)
                FCMNotificationService._initialized = True
                print("✅ Firebase Admin SDK başlatıldı")
            else:
                print(f"⚠️ Firebase service account dosyası bulunamadı: {service_account_path}")
    
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
        Tek bir token'a bildirim gönder
        
        Args:
            token: FCM device token
            title: Bildirim başlığı
            body: Bildirim içeriği
            data: Ek veri (dict)
            priority: Öncelik (high/normal)
            sound: Ses dosyası
            badge: Badge sayısı
            image: Görsel URL
            click_action: Tıklama aksiyonu
        
        Returns:
            bool: Başarılı ise True
        """
        FCMNotificationService.initialize()
        
        if not FCMNotificationService._initialized:
            print("❌ Firebase başlatılamadı, bildirim gönderilemedi")
            return False
        
        try:
            # Notification payload
            notification = messaging.Notification(
                title=title,
                body=body,
                image=image
            )
            
            # Android config
            android_config = messaging.AndroidConfig(
                priority=priority,
                notification=messaging.AndroidNotification(
                    sound=sound,
                    click_action=click_action,
                    icon='/static/icons/Icon-192.png',
                    color='#4CAF50'
                )
            )
            
            # APNS (iOS) config
            apns_config = messaging.APNSConfig(
                payload=messaging.APNSPayload(
                    aps=messaging.Aps(
                        sound=sound,
                        badge=badge,
                        content_available=True
                    )
                )
            )
            
            # Web push config
            webpush_config = messaging.WebpushConfig(
                notification=messaging.WebpushNotification(
                    title=title,
                    body=body,
                    icon='/static/icons/Icon-192.png',
                    badge='/static/icons/Icon-96.png',
                    image=image,
                    vibrate=[200, 100, 200],
                    data=data or {}
                ),
                fcm_options=messaging.WebpushFCMOptions(
                    link=click_action
                )
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
            print(f"✅ FCM bildirimi gönderildi: {response}")
            
            # Log kaydet
            FCMNotificationService._log_notification(
                token=token,
                title=title,
                body=body,
                status='sent',
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
        Birden fazla token'a bildirim gönder (Multicast)
        
        Args:
            tokens: FCM token listesi
            title: Bildirim başlığı
            body: Bildirim içeriği
            data: Ek veri
            priority: Öncelik
            image: Görsel URL
        
        Returns:
            dict: {'success': başarılı_sayısı, 'failure': başarısız_sayısı}
        """
        FCMNotificationService.initialize()
        
        if not FCMNotificationService._initialized:
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
            
            # Android config
            android_config = messaging.AndroidConfig(
                priority=priority,
                notification=messaging.AndroidNotification(
                    sound='default',
                    icon='/static/icons/Icon-192.png',
                    color='#4CAF50'
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
            
            print(f"✅ Multicast: {response.success_count} başarılı, {response.failure_count} başarısız")
            
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
        Yeni talep bildirimi - Tüm müsait sürücülere gönder
        
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
        
        title = "🚗 Yeni Buggy Talebi!"
        body = f"📍 {request_obj.location.name}\n🏨 {room_info}{guest_info}"
        
        # Data payload
        data = {
            'type': 'new_request',
            'request_id': str(request_obj.id),
            'location_id': str(request_obj.location_id),
            'location_name': request_obj.location.name,
            'room_number': request_obj.room_number or '',
            'guest_name': request_obj.guest_name or '',
            'url': '/driver/dashboard'
        }
        
        # Görsel (harita varsa)
        image = None
        if hasattr(request_obj.location, 'latitude') and request_obj.location.latitude:
            image = f"/api/map/thumbnail?lat={request_obj.location.latitude}&lng={request_obj.location.longitude}"
        
        # Gönder
        result = FCMNotificationService.send_to_multiple(
            tokens=tokens,
            title=title,
            body=body,
            data=data,
            priority='high',
            image=image
        )
        
        # Audit log
        if result['success'] > 0:
            from app.services.audit_service import AuditService
            AuditService.log_action(
                action='fcm_notification_sent',
                entity_type='request',
                entity_id=request_obj.id,
                new_values={
                    'notification_type': 'new_request',
                    'recipient_count': result['success'],
                    'driver_ids': driver_ids
                },
                hotel_id=request_obj.hotel_id
            )
        
        return result['success']
    
    @staticmethod
    def notify_request_accepted(request_obj) -> bool:
        """
        Talep kabul edildi bildirimi - Misafire gönder
        
        Args:
            request_obj: BuggyRequest nesnesi
        
        Returns:
            bool: Başarılı ise True
        """
        # Misafir token'ı varsa gönder
        if not hasattr(request_obj, 'guest_fcm_token') or not request_obj.guest_fcm_token:
            print("⚠️ Misafir FCM token'ı yok")
            return False
        
        title = "✅ Buggy Kabul Edildi"
        body = f"Buggy'niz yola çıktı! Sürücü: {request_obj.buggy.code}"
        
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
            priority='high'
        )
    
    @staticmethod
    def notify_request_completed(request_obj) -> bool:
        """
        Talep tamamlandı bildirimi - Misafire gönder
        
        Args:
            request_obj: BuggyRequest nesnesi
        
        Returns:
            bool: Başarılı ise True
        """
        if not hasattr(request_obj, 'guest_fcm_token') or not request_obj.guest_fcm_token:
            return False
        
        title = "🎉 Buggy Geldi!"
        body = "Buggy'niz konumunuza ulaştı. İyi yolculuklar!"
        
        data = {
            'type': 'request_completed',
            'request_id': str(request_obj.id)
        }
        
        return FCMNotificationService.send_to_token(
            token=request_obj.guest_fcm_token,
            title=title,
            body=body,
            data=data,
            priority='high'
        )
    
    @staticmethod
    def _log_notification(token: str, title: str, body: str, status: str, response: str = None, error: str = None):
        """Bildirim logla"""
        try:
            # Token'dan user_id bul
            user = SystemUser.query.filter_by(fcm_token=token).first()
            
            if user:
                log = NotificationLog(
                    user_id=user.id,
                    notification_type='fcm',
                    priority='high',
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
        """Geçersiz token'ı temizle"""
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
