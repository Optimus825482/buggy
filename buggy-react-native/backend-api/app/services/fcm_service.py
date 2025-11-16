"""
Firebase Cloud Messaging (FCM) Service
Push notification gönderme servisi
"""
from typing import List, Optional, Dict, Any
import logging
import json
from firebase_admin import messaging, credentials, initialize_app
import firebase_admin

from app.config import get_settings

logger = logging.getLogger(__name__)


class FCMService:
    """
    Firebase Cloud Messaging servisi
    Requirements: 7.2, 7.3, 7.4, 7.5, 7.6
    
    Singleton pattern ile tek instance kullanılır
    """
    
    _instance: Optional['FCMService'] = None
    _app: Optional[firebase_admin.App] = None
    _initialized: bool = False
    
    def __new__(cls):
        """Singleton pattern"""
        if cls._instance is None:
            cls._instance = super(FCMService, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize FCM service"""
        if not self._initialized:
            self._initialize_firebase()
            self._initialized = True
    
    def _initialize_firebase(self) -> None:
        """
        Firebase Admin SDK'yı başlat
        Requirements: 7.2
        
        Raises:
            Exception: Firebase başlatılamazsa
        """
        try:
            settings = get_settings()
            
            # Firebase credentials'ı al
            cred_dict = settings.get_firebase_credentials_dict()
            
            # Firebase Admin SDK'yı başlat
            cred = credentials.Certificate(cred_dict)
            self._app = initialize_app(cred, name='shuttle-call-fcm')
            
            logger.info("✅ Firebase Admin SDK başlatıldı")
            
        except Exception as e:
            logger.error(f"❌ Firebase başlatma hatası: {e}", exc_info=True)
            raise Exception(f"Firebase başlatılamadı: {e}")
    
    def validate_token(self, token: str) -> bool:
        """
        FCM token'ı doğrula
        Requirements: 7.2, 7.3
        
        Args:
            token: FCM token
            
        Returns:
            bool: Token geçerli mi?
        """
        try:
            if not token or len(token) < 10:
                return False
            
            # Token formatı kontrolü (basit)
            # Gerçek validasyon için FCM'e test mesajı gönderilebilir
            return True
            
        except Exception as e:
            logger.warning(f"⚠️ Token validasyon hatası: {e}")
            return False
    
    async def send_notification(
        self,
        token: str,
        title: str,
        body: str,
        data: Optional[Dict[str, str]] = None,
        sound: str = "default",
        badge: int = 1
    ) -> bool:
        """
        Tek bir cihaza FCM notification gönder
        Requirements: 7.2, 7.3
        
        Args:
            token: FCM token
            title: Notification başlığı
            body: Notification içeriği
            data: Ek data (opsiyonel)
            sound: Ses dosyası (default: "default")
            badge: Badge sayısı (iOS için)
            
        Returns:
            bool: Gönderim başarılı mı?
            
        Example:
            success = await fcm_service.send_notification(
                token="device_token",
                title="Yeni Shuttle Çağrısı",
                body="Oda 305 - Havuz Alanı",
                data={"request_id": "123", "type": "new_request"}
            )
        """
        try:
            # Token validasyonu
            if not self.validate_token(token):
                logger.warning(f"⚠️ Geçersiz FCM token")
                return False
            
            # Notification mesajı oluştur
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body
                ),
                data=data or {},
                token=token,
                android=messaging.AndroidConfig(
                    priority='high',
                    notification=messaging.AndroidNotification(
                        sound=sound,
                        channel_id='shuttle_requests',
                        priority='high',
                        default_vibrate_timings=True
                    )
                ),
                apns=messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(
                            sound=sound,
                            badge=badge,
                            content_available=True
                        )
                    )
                )
            )
            
            # Mesajı gönder
            response = messaging.send(message, app=self._app)
            
            logger.info(f"✅ FCM notification gönderildi: message_id={response}")
            return True
            
        except messaging.UnregisteredError:
            logger.warning(f"⚠️ FCM token geçersiz veya kayıtlı değil")
            return False
        except Exception as e:
            logger.error(f"❌ FCM gönderim hatası: {e}", exc_info=True)
            return False
    
    async def send_multicast(
        self,
        tokens: List[str],
        title: str,
        body: str,
        data: Optional[Dict[str, str]] = None,
        sound: str = "default"
    ) -> Dict[str, Any]:
        """
        Birden fazla cihaza FCM notification gönder
        Requirements: 7.2, 7.3
        
        Args:
            tokens: FCM token listesi (max 500)
            title: Notification başlığı
            body: Notification içeriği
            data: Ek data (opsiyonel)
            sound: Ses dosyası
            
        Returns:
            Dict: Gönderim sonucu (success_count, failure_count, responses)
            
        Example:
            result = await fcm_service.send_multicast(
                tokens=["token1", "token2", "token3"],
                title="Yeni Shuttle Çağrısı",
                body="Oda 305 - Havuz Alanı",
                data={"request_id": "123"}
            )
            print(f"Başarılı: {result['success_count']}")
        """
        try:
            # Token listesini filtrele (geçersiz olanları çıkar)
            valid_tokens = [t for t in tokens if self.validate_token(t)]
            
            if not valid_tokens:
                logger.warning("⚠️ Geçerli FCM token bulunamadı")
                return {
                    "success_count": 0,
                    "failure_count": len(tokens),
                    "responses": []
                }
            
            # Max 500 token limiti (FCM restriction)
            if len(valid_tokens) > 500:
                logger.warning(f"⚠️ Token sayısı 500'den fazla, ilk 500 alınıyor")
                valid_tokens = valid_tokens[:500]
            
            # Multicast mesajı oluştur
            message = messaging.MulticastMessage(
                notification=messaging.Notification(
                    title=title,
                    body=body
                ),
                data=data or {},
                tokens=valid_tokens,
                android=messaging.AndroidConfig(
                    priority='high',
                    notification=messaging.AndroidNotification(
                        sound=sound,
                        channel_id='shuttle_requests',
                        priority='high',
                        default_vibrate_timings=True
                    )
                ),
                apns=messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(
                            sound=sound,
                            badge=1,
                            content_available=True
                        )
                    )
                )
            )
            
            # Mesajları gönder
            response = messaging.send_multicast(message, app=self._app)
            
            logger.info(
                f"✅ FCM multicast gönderildi: "
                f"success={response.success_count}, "
                f"failure={response.failure_count}"
            )
            
            # Başarısız gönderimler için log
            if response.failure_count > 0:
                for idx, resp in enumerate(response.responses):
                    if not resp.success:
                        logger.warning(
                            f"⚠️ FCM gönderim başarısız: "
                            f"token_index={idx}, error={resp.exception}"
                        )
            
            return {
                "success_count": response.success_count,
                "failure_count": response.failure_count,
                "responses": [
                    {
                        "success": r.success,
                        "message_id": r.message_id if r.success else None,
                        "error": str(r.exception) if not r.success else None
                    }
                    for r in response.responses
                ]
            }
            
        except Exception as e:
            logger.error(f"❌ FCM multicast hatası: {e}", exc_info=True)
            return {
                "success_count": 0,
                "failure_count": len(tokens),
                "responses": [],
                "error": str(e)
            }


# Global FCM service instance
_fcm_service: Optional[FCMService] = None


def get_fcm_service() -> FCMService:
    """
    FCM service instance'ı döndür (singleton)
    
    Returns:
        FCMService: FCM service instance
        
    Example:
        from app.services.fcm_service import get_fcm_service
        
        fcm = get_fcm_service()
        await fcm.send_notification(token, "Başlık", "İçerik")
    """
    global _fcm_service
    
    if _fcm_service is None:
        _fcm_service = FCMService()
    
    return _fcm_service



# =============================================================================
# Notification Trigger Functions (Görev 9.2)
# =============================================================================

async def notify_new_request(
    request_id: int,
    hotel_id: int,
    location_name: str,
    room_number: str,
    guest_name: Optional[str] = None,
    driver_tokens: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Yeni request oluşturulduğunda sürücülere bildirim gönder
    Requirements: 7.4
    
    Args:
        request_id: Request ID
        hotel_id: Otel ID
        location_name: Lokasyon adı
        room_number: Oda numarası
        guest_name: Misafir adı (opsiyonel)
        driver_tokens: Sürücü FCM token listesi (opsiyonel, verilmezse DB'den alınır)
        
    Returns:
        Dict: Gönderim sonucu
        
    Example:
        result = await notify_new_request(
            request_id=123,
            hotel_id=1,
            location_name="Havuz Alanı",
            room_number="305",
            guest_name="Ahmet Yılmaz",
            driver_tokens=["token1", "token2"]
        )
    """
    try:
        fcm = get_fcm_service()
        
        # Driver token'ları verilmemişse DB'den al
        if driver_tokens is None:
            from sqlalchemy.orm import Session
            from app.database import SessionLocal
            from app.models.user import SystemUser
            from app.models.enums import UserRole
            
            db: Session = SessionLocal()
            try:
                # Aktif driver'ların FCM token'larını al
                drivers = db.query(SystemUser).filter(
                    SystemUser.hotel_id == hotel_id,
                    SystemUser.role == UserRole.DRIVER.value,
                    SystemUser.is_active == True,
                    SystemUser.fcm_token.isnot(None)
                ).all()
                
                driver_tokens = [d.fcm_token for d in drivers if d.fcm_token]
                
            finally:
                db.close()
        
        if not driver_tokens:
            logger.warning(f"⚠️ Bildirim gönderilemedi: Aktif driver bulunamadı (hotel_id={hotel_id})")
            return {"success_count": 0, "failure_count": 0}
        
        # Notification içeriği
        title = "🔔 Yeni Shuttle Çağrısı"
        body = f"Oda {room_number} - {location_name}"
        if guest_name:
            body = f"{guest_name} - {body}"
        
        data = {
            "type": "new_request",
            "request_id": str(request_id),
            "location_name": location_name,
            "room_number": room_number,
            "hotel_id": str(hotel_id)
        }
        
        # Multicast gönder
        result = await fcm.send_multicast(
            tokens=driver_tokens,
            title=title,
            body=body,
            data=data,
            sound="default"
        )
        
        logger.info(
            f"📢 Yeni request bildirimi gönderildi: "
            f"request_id={request_id}, "
            f"success={result['success_count']}, "
            f"failure={result['failure_count']}"
        )
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Yeni request bildirimi hatası: {e}", exc_info=True)
        return {"success_count": 0, "failure_count": 0, "error": str(e)}


async def notify_request_accepted(
    request_id: int,
    shuttle_code: str,
    driver_name: str,
    guest_fcm_token: Optional[str] = None
) -> bool:
    """
    Request kabul edildiğinde misafire bildirim gönder
    Requirements: 7.5
    
    Args:
        request_id: Request ID
        shuttle_code: Shuttle kodu
        driver_name: Sürücü adı
        guest_fcm_token: Misafir FCM token (opsiyonel, verilmezse DB'den alınır)
        
    Returns:
        bool: Gönderim başarılı mı?
        
    Example:
        success = await notify_request_accepted(
            request_id=123,
            shuttle_code="B01",
            driver_name="Mehmet Yılmaz",
            guest_fcm_token="guest_token"
        )
    """
    try:
        fcm = get_fcm_service()
        
        # Guest token verilmemişse DB'den al
        if guest_fcm_token is None:
            from sqlalchemy.orm import Session
            from app.database import SessionLocal
            from app.models.request import ShuttleRequest
            from datetime import datetime
            
            db: Session = SessionLocal()
            try:
                request = db.query(ShuttleRequest).filter(
                    ShuttleRequest.id == request_id
                ).first()
                
                if request and request.guest_fcm_token:
                    # Token süresi dolmamışsa kullan
                    if request.guest_fcm_token_expires_at and \
                       request.guest_fcm_token_expires_at > datetime.utcnow():
                        guest_fcm_token = request.guest_fcm_token
                
            finally:
                db.close()
        
        if not guest_fcm_token:
            logger.warning(f"⚠️ Bildirim gönderilemedi: Guest FCM token yok (request_id={request_id})")
            return False
        
        # Notification içeriği
        title = "✅ Shuttle Kabul Edildi"
        body = f"{shuttle_code} shuttle'ı size doğru geliyor"
        
        data = {
            "type": "request_accepted",
            "request_id": str(request_id),
            "shuttle_code": shuttle_code,
            "driver_name": driver_name
        }
        
        # Notification gönder
        success = await fcm.send_notification(
            token=guest_fcm_token,
            title=title,
            body=body,
            data=data,
            sound="default",
            badge=1
        )
        
        if success:
            logger.info(f"📢 Request kabul bildirimi gönderildi: request_id={request_id}")
        
        return success
        
    except Exception as e:
        logger.error(f"❌ Request kabul bildirimi hatası: {e}", exc_info=True)
        return False


async def notify_request_completed(
    request_id: int,
    guest_fcm_token: Optional[str] = None
) -> bool:
    """
    Request tamamlandığında misafire bildirim gönder
    Requirements: 7.6
    
    Args:
        request_id: Request ID
        guest_fcm_token: Misafir FCM token (opsiyonel, verilmezse DB'den alınır)
        
    Returns:
        bool: Gönderim başarılı mı?
        
    Example:
        success = await notify_request_completed(
            request_id=123,
            guest_fcm_token="guest_token"
        )
    """
    try:
        fcm = get_fcm_service()
        
        # Guest token verilmemişse DB'den al
        if guest_fcm_token is None:
            from sqlalchemy.orm import Session
            from app.database import SessionLocal
            from app.models.request import ShuttleRequest
            from datetime import datetime
            
            db: Session = SessionLocal()
            try:
                request = db.query(ShuttleRequest).filter(
                    ShuttleRequest.id == request_id
                ).first()
                
                if request and request.guest_fcm_token:
                    # Token süresi dolmamışsa kullan
                    if request.guest_fcm_token_expires_at and \
                       request.guest_fcm_token_expires_at > datetime.utcnow():
                        guest_fcm_token = request.guest_fcm_token
                
            finally:
                db.close()
        
        if not guest_fcm_token:
            logger.warning(f"⚠️ Bildirim gönderilemedi: Guest FCM token yok (request_id={request_id})")
            return False
        
        # Notification içeriği
        title = "🎉 Shuttle Ulaştı"
        body = "İyi yolculuklar!"
        
        data = {
            "type": "request_completed",
            "request_id": str(request_id)
        }
        
        # Notification gönder
        success = await fcm.send_notification(
            token=guest_fcm_token,
            title=title,
            body=body,
            data=data,
            sound="default",
            badge=1
        )
        
        if success:
            logger.info(f"📢 Request tamamlanma bildirimi gönderildi: request_id={request_id}")
        
        return success
        
    except Exception as e:
        logger.error(f"❌ Request tamamlanma bildirimi hatası: {e}", exc_info=True)
        return False
