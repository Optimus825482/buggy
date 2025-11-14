"""
Buggy Call - Firebase Cloud Messaging (FCM) Notification Service
Priority-based & Rich Media Support - Production Ready
Enhanced with comprehensive error handling, retry logic, and detailed logging
"""
import firebase_admin
from firebase_admin import credentials, messaging
import os
import json
import time
import traceback
from datetime import datetime, timedelta
from app import db
from app.models.user import SystemUser
from app.models.notification_log import NotificationLog
from app.utils.logger import logger, log_fcm_event, log_error
from typing import List, Dict, Optional, Tuple


class FCMNotificationService:
    """Firebase Cloud Messaging servisi - Production Ready"""
    
    _initialized = False
    
    # Retry configuration
    MAX_RETRIES = 3
    RETRY_DELAY_BASE = 1  # seconds
    RETRY_BACKOFF_MULTIPLIER = 2  # exponential backoff
    
    @staticmethod
    def _retry_with_exponential_backoff(func, *args, **kwargs) -> Tuple[bool, Optional[str], int]:
        """
        Retry a function with exponential backoff
        
        Args:
            func: Function to retry
            *args: Function arguments
            **kwargs: Function keyword arguments
        
        Returns:
            Tuple[bool, Optional[str], int]: (success, error_message, attempts)
        """
        last_error = None
        
        for attempt in range(FCMNotificationService.MAX_RETRIES):
            try:
                result = func(*args, **kwargs)
                if result:
                    if attempt > 0:
                        logger.info(f"✅ Retry başarılı (attempt {attempt + 1}/{FCMNotificationService.MAX_RETRIES})")
                    return True, None, attempt + 1
                else:
                    last_error = "Function returned False"
                    
            except messaging.UnregisteredError as e:
                # Don't retry for invalid tokens
                logger.warning(f"⚠️ Invalid token, no retry: {str(e)}")
                return False, f"Invalid token: {str(e)}", attempt + 1
                
            except messaging.SenderIdMismatchError as e:
                # Don't retry for sender ID mismatch
                logger.warning(f"⚠️ Sender ID mismatch, no retry: {str(e)}")
                return False, f"Sender ID mismatch: {str(e)}", attempt + 1
                
            except Exception as e:
                last_error = str(e)
                logger.warning(f"⚠️ Attempt {attempt + 1}/{FCMNotificationService.MAX_RETRIES} failed: {last_error}")
            
            # Exponential backoff (don't sleep on last attempt)
            if attempt < FCMNotificationService.MAX_RETRIES - 1:
                delay = FCMNotificationService.RETRY_DELAY_BASE * (FCMNotificationService.RETRY_BACKOFF_MULTIPLIER ** attempt)
                logger.info(f"⏳ Waiting {delay}s before retry...")
                time.sleep(delay)
        
        logger.error(f"❌ All {FCMNotificationService.MAX_RETRIES} attempts failed")
        return False, last_error, FCMNotificationService.MAX_RETRIES
    
    @staticmethod
    def initialize() -> bool:
        """
        Firebase Admin SDK'yı başlat - Enhanced error handling
        
        Returns:
            bool: Başarılı ise True, aksi halde False
        """
        if FCMNotificationService._initialized:
            logger.info("✅ Firebase Admin SDK zaten başlatılmış")
            return True
        
        try:
            # Check if already initialized
            firebase_admin.get_app()
            FCMNotificationService._initialized = True
            logger.info("✅ Firebase Admin SDK zaten başlatılmış")
            return True
            
        except ValueError:
            # Not initialized, proceed with initialization
            try:
                service_account_path = os.getenv(
                    'FIREBASE_SERVICE_ACCOUNT_PATH', 
                    'firebase-service-account.json'
                )
                
                # Validate service account file exists
                if not os.path.exists(service_account_path):
                    error_msg = f'Service account dosyası bulunamadı: {service_account_path}'
                    logger.error(f"❌ FCM_INIT: {error_msg}")
                    log_error('FCM_INIT', error_msg, {
                        'path': service_account_path,
                        'cwd': os.getcwd()
                    })
                    return False
                
                # Validate service account file is readable
                try:
                    with open(service_account_path, 'r') as f:
                        json.load(f)
                except json.JSONDecodeError as e:
                    error_msg = f'Service account dosyası geçersiz JSON: {str(e)}'
                    logger.error(f"❌ FCM_INIT: {error_msg}")
                    log_error('FCM_INIT', error_msg, {'path': service_account_path})
                    return False
                except Exception as e:
                    error_msg = f'Service account dosyası okunamadı: {str(e)}'
                    logger.error(f"❌ FCM_INIT: {error_msg}")
                    log_error('FCM_INIT', error_msg, {'path': service_account_path})
                    return False
                
                # Initialize Firebase Admin SDK
                cred = credentials.Certificate(service_account_path)
                firebase_admin.initialize_app(cred)
                FCMNotificationService._initialized = True
                
                logger.info("✅ Firebase Admin SDK başarıyla başlatıldı")
                log_fcm_event('SDK_INITIALIZED', {
                    'service_account': service_account_path,
                    'timestamp': datetime.utcnow().isoformat()
                })
                return True
                
            except Exception as e:
                error_msg = f'Firebase Admin SDK başlatma hatası: {str(e)}'
                logger.error(f"❌ FCM_INIT: {error_msg}")
                logger.error(f"❌ Traceback: {traceback.format_exc()}")
                log_error('FCM_INIT', error_msg, {
                    'exception_type': type(e).__name__,
                    'traceback': traceback.format_exc()
                })
                return False
        
        except Exception as e:
            # Unexpected error
            error_msg = f'Beklenmeyen FCM başlatma hatası: {str(e)}'
            logger.error(f"❌ FCM_INIT: {error_msg}")
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            log_error('FCM_INIT', error_msg, {
                'exception_type': type(e).__name__,
                'traceback': traceback.format_exc()
            })
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
        click_action: Optional[str] = None,
        retry: bool = True
    ) -> bool:
        """
        Tek bir token'a bildirim gönder - Priority-based with retry logic
        
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
            retry: Retry on failure (default: True)
        
        Returns:
            bool: Başarılı ise True
        """
        # Initialize Firebase
        if not FCMNotificationService.initialize():
            error_msg = "Firebase başlatılamadı, bildirim gönderilemedi"
            logger.error(f"❌ {error_msg}")
            FCMNotificationService._log_notification(
                token=token,
                title=title,
                body=body,
                status='failed',
                priority=priority,
                error=error_msg
            )
            return False
        
        # Define send function for retry
        def _send():
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
                
                # Vibration patterns based on priority
                vibration_patterns = {
                    'high': [200, 100, 200, 100, 200, 100, 200],  # Urgent: 4 vibrations
                    'normal': [200, 100, 200],  # Normal: 2 vibrations
                    'low': [100]  # Low: 1 short vibration
                }
                vibrate = vibration_patterns.get(priority, vibration_patterns['normal'])
                
                webpush_config = messaging.WebpushConfig(
                    notification=messaging.WebpushNotification(
                        title=title,
                        body=body,
                        icon='/static/icons/Icon-192.png',
                        badge='/static/icons/Icon-96.png',
                        image=image,
                        vibrate=vibrate,
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
                logger.info(f"✅ FCM bildirimi gönderildi (Priority: {priority}): {response}")
                
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
                
            except messaging.UnregisteredError as e:
                logger.warning(f"❌ Token geçersiz veya kayıtsız: {token[:20]}...")
                FCMNotificationService._remove_invalid_token(token)
                FCMNotificationService._log_notification(
                    token=token,
                    title=title,
                    body=body,
                    status='failed',
                    priority=priority,
                    error=f"Invalid token: {str(e)}"
                )
                raise  # Re-raise to be caught by retry logic
                
            except Exception as e:
                logger.error(f"❌ FCM bildirim hatası: {str(e)}")
                logger.error(f"❌ Traceback: {traceback.format_exc()}")
                FCMNotificationService._log_notification(
                    token=token,
                    title=title,
                    body=body,
                    status='failed',
                    priority=priority,
                    error=str(e)
                )
                raise  # Re-raise to be caught by retry logic
        
        # Execute with retry if enabled
        if retry:
            success, error_msg, attempts = FCMNotificationService._retry_with_exponential_backoff(_send)
            if success:
                logger.info(f"✅ FCM notification sent successfully (attempts: {attempts})")
                return True
            else:
                logger.error(f"❌ FCM notification failed after {attempts} attempts: {error_msg}")
                return False
        else:
            # No retry, execute once
            try:
                return _send()
            except Exception as e:
                logger.error(f"❌ FCM notification failed (no retry): {str(e)}")
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
            
            # ✅ Yeni API kullan: send_each_for_multicast (batch endpoint hatası çözümü)
            try:
                response = messaging.send_each_for_multicast(message)
            except AttributeError:
                # Eski SDK versiyonu için fallback
                response = messaging.send_multicast(message)
            
            print(f"✅ FCM notifications sent: {response.success_count} success, {response.failure_count} failed")
            
            # Başarısız token'ları temizle ve hata detaylarını logla
            if response.failure_count > 0:
                print(f"❌ FCM Failures detected:")
                for idx, resp in enumerate(response.responses):
                    if not resp.success:
                        token = tokens[idx]
                        error_code = resp.exception.code if hasattr(resp.exception, 'code') else 'UNKNOWN'
                        error_msg = str(resp.exception) if resp.exception else 'No error message'
                        print(f"   Token {idx+1}: {token[:20]}... - Error: {error_code} - {error_msg}")
                        FCMNotificationService._remove_invalid_token(token)
            
            return {
                'success': response.success_count,
                'failure': response.failure_count
            }
            
        except Exception as e:
            print(f"❌ FCM error: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'success': 0, 'failure': len(tokens)}

    @staticmethod
    def notify_new_request(request_obj) -> int:
        """
        ⚡ KRITIK SISTEM: Yeni talep bildirimi - HIGH PRIORITY + Rich Media
        Tüm müsait sürücülere GARANTILI gönder

        Args:
            request_obj: BuggyRequest nesnesi

        Returns:
            int: Bildirim gönderilen sürücü sayısı
        """
        from app.models.buggy import Buggy, BuggyStatus

        logger.info('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
        logger.info(f'🔔 [FCM] NEW REQUEST NOTIFICATION START')
        logger.info(f'📋 Request ID: {request_obj.id}')
        logger.info(f'🏨 Hotel ID: {request_obj.hotel_id}')
        logger.info(f'📍 Location: {request_obj.location.name}')
        logger.info('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')

        # Tüm buggy'leri detaylı logla
        all_buggies = Buggy.query.filter_by(hotel_id=request_obj.hotel_id).all()
        logger.info(f"🚗 Hotel {request_obj.hotel_id} - Toplam buggy sayısı: {len(all_buggies)}")
        for b in all_buggies:
            logger.info(f"  - Buggy {b.code}: Status={b.status.value}, Driver ID={b.driver_id}")

        # Müsait buggy'leri bul
        available_buggies = Buggy.query.filter_by(
            hotel_id=request_obj.hotel_id,
            status=BuggyStatus.AVAILABLE
        ).all()

        logger.info(f"✅ Müsait buggy sayısı: {len(available_buggies)}")

        # Sürücü token'larını topla
        tokens = []
        driver_ids = []
        driver_details = []

        for buggy in available_buggies:
            # Yeni sistem: BuggyDriver association table kullan
            from app.models.buggy_driver import BuggyDriver
            active_assignments = BuggyDriver.query.filter_by(
                buggy_id=buggy.id,
                is_active=True
            ).all()

            logger.info(f"  🔍 Buggy {buggy.code}: {len(active_assignments)} aktif atama")

            for assignment in active_assignments:
                driver = SystemUser.query.get(assignment.driver_id)
                if driver:
                    has_token = bool(driver.fcm_token)
                    token_preview = driver.fcm_token[:20] + '...' if driver.fcm_token else 'None'

                    logger.info(f"    👤 Driver: {driver.full_name} (ID: {driver.id})")
                    logger.info(f"       FCM Token: {'✅ ' + token_preview if has_token else '❌ None'}")

                    if driver.fcm_token and driver.id not in driver_ids:
                        tokens.append(driver.fcm_token)
                        driver_ids.append(driver.id)
                        driver_details.append({
                            'id': driver.id,
                            'name': driver.full_name,
                            'buggy': buggy.code
                        })
                        logger.info(f"       ✅ Token added to send list")
                    elif driver.fcm_token:
                        logger.warning(f"       ⚠️ Driver already in list (duplicate prevented)")
                    else:
                        logger.error(f"       ❌ NO FCM TOKEN - Driver cannot receive notifications!")

        logger.info('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
        logger.info(f"📊 SUMMARY:")
        logger.info(f"   Total Available Buggies: {len(available_buggies)}")
        logger.info(f"   Drivers with FCM Tokens: {len(tokens)}")
        logger.info(f"   Ready to Send: {len(tokens)} notifications")
        logger.info('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')

        if not tokens:
            error_msg = 'KRITIK: Bildirim gönderilecek sürücü bulunamadı!'
            logger.error(f"❌ {error_msg}")
            logger.error(f"   Hotel ID: {request_obj.hotel_id}")
            logger.error(f"   Request ID: {request_obj.id}")
            logger.error(f"   Available Buggies: {len(available_buggies)}")
            logger.error(f"   Drivers Found: {len(driver_ids)}")
            logger.error('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')

            log_error('FCM_NO_DRIVERS', error_msg, {
                'hotel_id': request_obj.hotel_id,
                'request_id': request_obj.id,
                'available_buggies': len(available_buggies),
                'all_buggies': len(all_buggies),
                'drivers_checked': len(driver_ids)
            })
            return 0
        
        # Bildirim içeriği - ENHANCED
        room_info = f"Oda {request_obj.room_number}" if request_obj.room_number else "Misafir"
        guest_info = f" - {request_obj.guest_name}" if request_obj.guest_name else ""

        title = "🚗 YENİ SHUTTLE TALEBİ!"
        body = f"📍 {request_obj.location.name}\n🏨 {room_info}{guest_info}"

        logger.info(f"📝 Notification content:")
        logger.info(f"   Title: {title}")
        logger.info(f"   Body: {body}")

        # Data payload - Action buttons için
        data = {
            'type': 'new_request',
            'request_id': str(request_obj.id),
            'location_id': str(request_obj.location_id),
            'location_name': request_obj.location.name,
            'room_number': request_obj.room_number or '',
            'guest_name': request_obj.guest_name or '',
            'url': '/driver/dashboard',
            'priority': 'high',
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
                    logger.info(f"🗺️ Map image URL generated")
        except Exception as e:
            logger.warning(f"⚠️ Harita thumbnail oluşturulamadı: {str(e)}")

        # HIGH PRIORITY ile gönder
        logger.info(f"📤 Sending notifications to {len(tokens)} drivers...")
        logger.info(f"   Priority: HIGH")
        logger.info(f"   Drivers: {', '.join([d['name'] for d in driver_details])}")

        result = FCMNotificationService.send_to_multiple(
            tokens=tokens,
            title=title,
            body=body,
            data=data,
            priority='high',  # Yeni talep = HIGH priority
            image=image
        )

        logger.info('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
        logger.info(f"📊 NOTIFICATION RESULT:")
        logger.info(f"   ✅ Success: {result['success']}")
        logger.info(f"   ❌ Failed: {result['failure']}")
        logger.info('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')

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
                        'failed_count': result['failure'],
                        'driver_ids': driver_ids,
                        'driver_details': driver_details
                    },
                    hotel_id=request_obj.hotel_id
                )
                logger.info(f"✅ Audit log saved")
            except Exception as e:
                logger.error(f"❌ Audit log hatası: {str(e)}")

        logger.info(f"🎉 [FCM] NEW REQUEST NOTIFICATION COMPLETE")
        logger.info(f"   Notified {result['success']} drivers successfully")
        logger.info('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')

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
                    sent_at=datetime.utcnow().replace(tzinfo=None)  # UTC naive
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
    def validate_token(token: str) -> bool:
        """
        FCM token formatını doğrula
        
        Args:
            token: FCM device token
        
        Returns:
            bool: Geçerli ise True
        """
        if not token or not isinstance(token, str):
            return False
        
        # Token minimum uzunluk kontrolü (FCM tokens genellikle 152+ karakter)
        if len(token) < 100:
            logger.warning(f"⚠️ Token çok kısa: {len(token)} karakter")
            return False
        
        # Token maksimum uzunluk kontrolü
        if len(token) > 500:
            logger.warning(f"⚠️ Token çok uzun: {len(token)} karakter")
            return False
        
        # Token sadece geçerli karakterler içermeli (alphanumeric, -, _, :)
        import re
        if not re.match(r'^[A-Za-z0-9_:-]+$', token):
            logger.warning(f"⚠️ Token geçersiz karakterler içeriyor")
            return False
        
        return True
    
    @staticmethod
    def register_token(user_id: int, token: str) -> bool:
        """
        Kullanıcı için FCM token kaydet - Enhanced with validation
        
        Args:
            user_id: Kullanıcı ID
            token: FCM device token
        
        Returns:
            bool: Başarılı ise True
        """
        try:
            # Validate token format
            if not FCMNotificationService.validate_token(token):
                logger.error(f"❌ Geçersiz token formatı: User {user_id}")
                return False
            
            user = SystemUser.query.get(user_id)
            if not user:
                logger.error(f"❌ Kullanıcı bulunamadı: User {user_id}")
                return False
            
            # Check if token already exists for another user
            existing_user = SystemUser.query.filter_by(fcm_token=token).first()
            if existing_user and existing_user.id != user_id:
                logger.warning(f"⚠️ Token başka bir kullanıcıda kayıtlı: User {existing_user.id}, yeni User {user_id}")
                # Remove from old user
                existing_user.fcm_token = None
                existing_user.fcm_token_date = None
            
            # Register token
            user.fcm_token = token
            user.fcm_token_date = datetime.utcnow().replace(tzinfo=None)  # UTC naive
            db.session.commit()
            
            logger.info(f"✅ FCM token kaydedildi: User {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Token kayıt hatası: {str(e)}")
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
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
            user.fcm_token_date = datetime.utcnow().replace(tzinfo=None)  # UTC naive
            db.session.commit()
            
            print(f"🔄 FCM token yenilendi: User {user_id}")
            return True
            
        except Exception as e:
            print(f"❌ Token yenileme hatası: {str(e)}")
            db.session.rollback()
            return False
