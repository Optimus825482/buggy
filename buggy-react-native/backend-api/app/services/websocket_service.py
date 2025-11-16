"""
WebSocket Service
Real-time updates için WebSocket yönetimi
"""
from typing import Dict, Set, Optional, Any
from fastapi import WebSocket, WebSocketDisconnect
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    WebSocket bağlantı yöneticisi
    Requirements: 10.1, 10.2
    
    Room-based broadcasting sistemi ile çalışır:
    - hotel_{id}_drivers: Driver'lar için room
    - hotel_{id}_admin: Admin'ler için room
    - request_{id}: Belirli bir request için room (guest)
    """
    
    def __init__(self):
        """Initialize connection manager"""
        # Room bazlı aktif bağlantılar: {room_name: {websocket1, websocket2, ...}}
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        
        # WebSocket -> user bilgisi mapping: {websocket: {"user_id": 1, "username": "driver1", "role": "driver"}}
        self.connection_info: Dict[WebSocket, Dict[str, Any]] = {}
        
        logger.info("✅ WebSocket ConnectionManager başlatıldı")
    
    async def connect(self, websocket: WebSocket, room: str, user_info: Optional[Dict[str, Any]] = None) -> None:
        """
        WebSocket bağlantısı kur ve room'a ekle
        Requirements: 10.1, 10.2
        
        Args:
            websocket: WebSocket bağlantısı
            room: Room adı (örn: "hotel_1_drivers")
            user_info: Kullanıcı bilgileri (opsiyonel)
            
        Example:
            await manager.connect(
                websocket,
                "hotel_1_drivers",
                {"user_id": 5, "username": "driver1", "role": "driver"}
            )
        """
        try:
            # WebSocket bağlantısını kabul et
            await websocket.accept()
            
            # Room yoksa oluştur
            if room not in self.active_connections:
                self.active_connections[room] = set()
            
            # WebSocket'i room'a ekle
            self.active_connections[room].add(websocket)
            
            # Kullanıcı bilgilerini sakla
            if user_info:
                self.connection_info[websocket] = user_info
            
            logger.info(
                f"✅ WebSocket bağlantısı kuruldu: room={room}, "
                f"user={user_info.get('username') if user_info else 'guest'}, "
                f"total_in_room={len(self.active_connections[room])}"
            )
            
            # Room'a katıldı mesajı gönder
            await self.send_personal_message(
                websocket,
                {
                    "type": "room_joined",
                    "room": room,
                    "timestamp": datetime.utcnow().isoformat(),
                    "message": f"{room} room'una katıldınız"
                }
            )
            
        except Exception as e:
            logger.error(f"❌ WebSocket bağlantı hatası: {e}", exc_info=True)
            raise
    
    def disconnect(self, websocket: WebSocket, room: str) -> None:
        """
        WebSocket bağlantısını kapat ve room'dan çıkar
        Requirements: 10.1, 10.2
        
        Args:
            websocket: WebSocket bağlantısı
            room: Room adı
        """
        try:
            # Room'dan çıkar
            if room in self.active_connections:
                self.active_connections[room].discard(websocket)
                
                # Room boşsa sil
                if not self.active_connections[room]:
                    del self.active_connections[room]
            
            # Kullanıcı bilgilerini sil
            user_info = self.connection_info.pop(websocket, None)
            
            logger.info(
                f"🔌 WebSocket bağlantısı kapatıldı: room={room}, "
                f"user={user_info.get('username') if user_info else 'guest'}"
            )
            
        except Exception as e:
            logger.error(f"❌ WebSocket disconnect hatası: {e}", exc_info=True)
    
    async def send_personal_message(self, websocket: WebSocket, message: Dict[str, Any]) -> bool:
        """
        Belirli bir WebSocket'e mesaj gönder
        Requirements: 10.1
        
        Args:
            websocket: WebSocket bağlantısı
            message: Gönderilecek mesaj (dict)
            
        Returns:
            bool: Gönderim başarılı mı?
        """
        try:
            await websocket.send_json(message)
            return True
        except Exception as e:
            logger.warning(f"⚠️ WebSocket mesaj gönderme hatası: {e}")
            return False
    
    async def broadcast_to_room(self, room: str, message: Dict[str, Any]) -> int:
        """
        Room'daki tüm bağlantılara mesaj gönder (broadcast)
        Requirements: 10.1, 10.2
        
        Args:
            room: Room adı
            message: Gönderilecek mesaj (dict)
            
        Returns:
            int: Başarılı gönderim sayısı
            
        Example:
            count = await manager.broadcast_to_room(
                "hotel_1_drivers",
                {
                    "type": "new_request",
                    "data": {"request_id": 123, "location": "Havuz"}
                }
            )
        """
        if room not in self.active_connections:
            logger.debug(f"ℹ️ Room bulunamadı: {room}")
            return 0
        
        success_count = 0
        failed_connections = []
        
        # Room'daki tüm bağlantılara gönder
        for connection in self.active_connections[room].copy():
            try:
                await connection.send_json(message)
                success_count += 1
            except Exception as e:
                logger.warning(f"⚠️ Broadcast hatası: {e}")
                failed_connections.append(connection)
        
        # Başarısız bağlantıları temizle
        for connection in failed_connections:
            self.active_connections[room].discard(connection)
            self.connection_info.pop(connection, None)
        
        logger.debug(
            f"📢 Broadcast gönderildi: room={room}, "
            f"success={success_count}, failed={len(failed_connections)}"
        )
        
        return success_count
    
    async def broadcast_to_multiple_rooms(
        self,
        rooms: list[str],
        message: Dict[str, Any]
    ) -> Dict[str, int]:
        """
        Birden fazla room'a mesaj gönder
        Requirements: 10.1, 10.2
        
        Args:
            rooms: Room adları listesi
            message: Gönderilecek mesaj
            
        Returns:
            Dict[str, int]: Her room için başarılı gönderim sayısı
            
        Example:
            results = await manager.broadcast_to_multiple_rooms(
                ["hotel_1_drivers", "hotel_1_admin"],
                {"type": "shuttle_status_changed", "data": {...}}
            )
        """
        results = {}
        
        for room in rooms:
            count = await self.broadcast_to_room(room, message)
            results[room] = count
        
        return results
    
    def get_room_connections_count(self, room: str) -> int:
        """
        Room'daki aktif bağlantı sayısını döndür
        
        Args:
            room: Room adı
            
        Returns:
            int: Bağlantı sayısı
        """
        if room not in self.active_connections:
            return 0
        return len(self.active_connections[room])
    
    def get_all_rooms(self) -> list[str]:
        """
        Tüm aktif room'ları döndür
        
        Returns:
            list[str]: Room adları listesi
        """
        return list(self.active_connections.keys())
    
    def get_connection_info(self, websocket: WebSocket) -> Optional[Dict[str, Any]]:
        """
        WebSocket'in kullanıcı bilgilerini döndür
        
        Args:
            websocket: WebSocket bağlantısı
            
        Returns:
            Optional[Dict]: Kullanıcı bilgileri (varsa)
        """
        return self.connection_info.get(websocket)


# Global ConnectionManager instance
_connection_manager: Optional[ConnectionManager] = None


def get_connection_manager() -> ConnectionManager:
    """
    ConnectionManager instance'ı döndür (singleton)
    
    Returns:
        ConnectionManager: WebSocket connection manager
        
    Example:
        from app.services.websocket_service import get_connection_manager
        
        manager = get_connection_manager()
        await manager.broadcast_to_room("hotel_1_drivers", message)
    """
    global _connection_manager
    
    if _connection_manager is None:
        _connection_manager = ConnectionManager()
    
    return _connection_manager



# =============================================================================
# WebSocket Event Emitters (Görev 10.3)
# =============================================================================

async def emit_new_request(
    hotel_id: int,
    request_id: int,
    location_name: str,
    room_number: str,
    guest_name: Optional[str] = None
) -> int:
    """
    Yeni request oluşturulduğunda driver ve admin'lere bildir
    Requirements: 10.3, 10.4
    
    Args:
        hotel_id: Otel ID
        request_id: Request ID
        location_name: Lokasyon adı
        room_number: Oda numarası
        guest_name: Misafir adı (opsiyonel)
        
    Returns:
        int: Toplam gönderim sayısı
        
    Example:
        count = await emit_new_request(
            hotel_id=1,
            request_id=123,
            location_name="Havuz Alanı",
            room_number="305",
            guest_name="Ahmet Yılmaz"
        )
    """
    try:
        manager = get_connection_manager()
        
        # Event mesajı
        message = {
            "type": "new_request",
            "data": {
                "request_id": request_id,
                "location_name": location_name,
                "room_number": room_number,
                "guest_name": guest_name,
                "hotel_id": hotel_id
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Driver ve admin room'larına gönder
        rooms = [
            f"hotel_{hotel_id}_drivers",
            f"hotel_{hotel_id}_admin"
        ]
        
        results = await manager.broadcast_to_multiple_rooms(rooms, message)
        total_count = sum(results.values())
        
        logger.info(
            f"📢 WebSocket: new_request event gönderildi: "
            f"request_id={request_id}, total_sent={total_count}"
        )
        
        return total_count
        
    except Exception as e:
        logger.error(f"❌ WebSocket emit_new_request hatası: {e}", exc_info=True)
        return 0


async def emit_request_accepted(
    hotel_id: int,
    request_id: int,
    shuttle_code: str,
    driver_name: str
) -> int:
    """
    Request kabul edildiğinde guest ve admin'e bildir
    Requirements: 10.3, 10.4
    
    Args:
        hotel_id: Otel ID
        request_id: Request ID
        shuttle_code: Shuttle kodu
        driver_name: Sürücü adı
        
    Returns:
        int: Toplam gönderim sayısı
    """
    try:
        manager = get_connection_manager()
        
        # Event mesajı
        message = {
            "type": "request_accepted",
            "data": {
                "request_id": request_id,
                "shuttle_code": shuttle_code,
                "driver_name": driver_name,
                "hotel_id": hotel_id
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Guest ve admin room'larına gönder
        rooms = [
            f"request_{request_id}",  # Guest için
            f"hotel_{hotel_id}_admin"  # Admin için
        ]
        
        results = await manager.broadcast_to_multiple_rooms(rooms, message)
        total_count = sum(results.values())
        
        logger.info(
            f"📢 WebSocket: request_accepted event gönderildi: "
            f"request_id={request_id}, total_sent={total_count}"
        )
        
        return total_count
        
    except Exception as e:
        logger.error(f"❌ WebSocket emit_request_accepted hatası: {e}", exc_info=True)
        return 0


async def emit_request_completed(
    hotel_id: int,
    request_id: int
) -> int:
    """
    Request tamamlandığında guest, driver ve admin'e bildir
    Requirements: 10.3, 10.4
    
    Args:
        hotel_id: Otel ID
        request_id: Request ID
        
    Returns:
        int: Toplam gönderim sayısı
    """
    try:
        manager = get_connection_manager()
        
        # Event mesajı
        message = {
            "type": "request_completed",
            "data": {
                "request_id": request_id,
                "hotel_id": hotel_id
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Guest, driver ve admin room'larına gönder
        rooms = [
            f"request_{request_id}",  # Guest için
            f"hotel_{hotel_id}_drivers",  # Driver'lar için
            f"hotel_{hotel_id}_admin"  # Admin için
        ]
        
        results = await manager.broadcast_to_multiple_rooms(rooms, message)
        total_count = sum(results.values())
        
        logger.info(
            f"📢 WebSocket: request_completed event gönderildi: "
            f"request_id={request_id}, total_sent={total_count}"
        )
        
        return total_count
        
    except Exception as e:
        logger.error(f"❌ WebSocket emit_request_completed hatası: {e}", exc_info=True)
        return 0


async def emit_shuttle_status_changed(
    hotel_id: int,
    shuttle_id: int,
    shuttle_code: str,
    status: str,
    location_id: Optional[int] = None
) -> int:
    """
    Shuttle durumu değiştiğinde admin'e bildir
    Requirements: 10.3, 10.4
    
    Args:
        hotel_id: Otel ID
        shuttle_id: Shuttle ID
        shuttle_code: Shuttle kodu
        status: Yeni durum (available, busy, offline)
        location_id: Lokasyon ID (opsiyonel)
        
    Returns:
        int: Toplam gönderim sayısı
    """
    try:
        manager = get_connection_manager()
        
        # Event mesajı
        message = {
            "type": "shuttle_status_changed",
            "data": {
                "shuttle_id": shuttle_id,
                "shuttle_code": shuttle_code,
                "status": status,
                "location_id": location_id,
                "hotel_id": hotel_id
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Admin room'una gönder
        room = f"hotel_{hotel_id}_admin"
        count = await manager.broadcast_to_room(room, message)
        
        logger.info(
            f"📢 WebSocket: shuttle_status_changed event gönderildi: "
            f"shuttle_id={shuttle_id}, status={status}, sent={count}"
        )
        
        return count
        
    except Exception as e:
        logger.error(f"❌ WebSocket emit_shuttle_status_changed hatası: {e}", exc_info=True)
        return 0


async def emit_driver_logged_in(
    hotel_id: int,
    driver_id: int,
    driver_name: str,
    shuttle_id: Optional[int] = None
) -> int:
    """
    Driver giriş yaptığında admin'e bildir
    Requirements: 10.3, 10.4
    
    Args:
        hotel_id: Otel ID
        driver_id: Driver ID
        driver_name: Driver adı
        shuttle_id: Shuttle ID (opsiyonel)
        
    Returns:
        int: Toplam gönderim sayısı
    """
    try:
        manager = get_connection_manager()
        
        # Event mesajı
        message = {
            "type": "driver_logged_in",
            "data": {
                "driver_id": driver_id,
                "driver_name": driver_name,
                "shuttle_id": shuttle_id,
                "hotel_id": hotel_id
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Admin room'una gönder
        room = f"hotel_{hotel_id}_admin"
        count = await manager.broadcast_to_room(room, message)
        
        logger.info(
            f"📢 WebSocket: driver_logged_in event gönderildi: "
            f"driver_id={driver_id}, sent={count}"
        )
        
        return count
        
    except Exception as e:
        logger.error(f"❌ WebSocket emit_driver_logged_in hatası: {e}", exc_info=True)
        return 0


async def emit_driver_logged_out(
    hotel_id: int,
    driver_id: int,
    driver_name: str
) -> int:
    """
    Driver çıkış yaptığında admin'e bildir
    Requirements: 10.3, 10.4
    
    Args:
        hotel_id: Otel ID
        driver_id: Driver ID
        driver_name: Driver adı
        
    Returns:
        int: Toplam gönderim sayısı
    """
    try:
        manager = get_connection_manager()
        
        # Event mesajı
        message = {
            "type": "driver_logged_out",
            "data": {
                "driver_id": driver_id,
                "driver_name": driver_name,
                "hotel_id": hotel_id
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Admin room'una gönder
        room = f"hotel_{hotel_id}_admin"
        count = await manager.broadcast_to_room(room, message)
        
        logger.info(
            f"📢 WebSocket: driver_logged_out event gönderildi: "
            f"driver_id={driver_id}, sent={count}"
        )
        
        return count
        
    except Exception as e:
        logger.error(f"❌ WebSocket emit_driver_logged_out hatası: {e}", exc_info=True)
        return 0
