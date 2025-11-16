"""
WebSocket API Endpoint
Real-time updates için WebSocket bağlantısı
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, status
from typing import Optional
import logging
import json

from app.services.websocket_service import get_connection_manager
from app.core.security import extract_user_from_token

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None, description="JWT token (opsiyonel, guest için)"),
    room: Optional[str] = Query(None, description="Room adı (opsiyonel)")
):
    """
    WebSocket endpoint
    Requirements: 10.1, 10.2
    
    **Bağlantı Kurma:**
    - URL: ws://localhost:8000/api/v1/ws?token=JWT_TOKEN&room=hotel_1_drivers
    - Token: JWT authentication token (driver/admin için gerekli, guest için opsiyonel)
    - Room: Katılınacak room adı (opsiyonel, sonra join_room ile de yapılabilir)
    
    **Room Formatları:**
    - hotel_{hotel_id}_drivers: Driver'lar için
    - hotel_{hotel_id}_admin: Admin'ler için
    - request_{request_id}: Belirli bir request için (guest)
    
    **Mesaj Formatı (Client -> Server):**
    ```json
    {
        "type": "join_room",
        "room": "hotel_1_drivers"
    }
    ```
    
    **Mesaj Formatı (Server -> Client):**
    ```json
    {
        "type": "new_request",
        "data": {
            "request_id": 123,
            "location_name": "Havuz Alanı",
            "room_number": "305"
        },
        "timestamp": "2024-11-16T10:30:00Z"
    }
    ```
    
    **Event Tipleri:**
    - room_joined: Room'a katıldı
    - new_request: Yeni request oluşturuldu
    - request_accepted: Request kabul edildi
    - request_completed: Request tamamlandı
    - shuttle_status_changed: Shuttle durumu değişti
    - driver_logged_in: Driver giriş yaptı
    - driver_logged_out: Driver çıkış yaptı
    - error: Hata mesajı
    """
    manager = get_connection_manager()
    current_room: Optional[str] = None
    user_info: Optional[dict] = None
    
    try:
        # JWT token varsa doğrula ve kullanıcı bilgilerini al
        if token:
            try:
                user_data = extract_user_from_token(token)
                if user_data:
                    user_info = {
                        "user_id": user_data.get("user_id"),
                        "username": user_data.get("username"),
                        "role": user_data.get("role"),
                        "hotel_id": user_data.get("hotel_id")
                    }
                    logger.info(f"🔐 WebSocket auth başarılı: user={user_info['username']}")
                else:
                    logger.warning("⚠️ WebSocket auth başarısız: Token geçersiz")
            except Exception as e:
                logger.warning(f"⚠️ WebSocket auth hatası: {e}")
        
        # İlk room varsa bağlan
        if room:
            current_room = room
            await manager.connect(websocket, room, user_info)
        else:
            # Room yoksa default bağlantı kur
            await websocket.accept()
            await manager.send_personal_message(
                websocket,
                {
                    "type": "connected",
                    "message": "WebSocket bağlantısı kuruldu. join_room mesajı gönderin."
                }
            )
        
        # Mesaj dinleme döngüsü
        while True:
            try:
                # Client'tan mesaj al
                data = await websocket.receive_text()
                message = json.loads(data)
                
                message_type = message.get("type")
                
                # join_room mesajı
                if message_type == "join_room":
                    new_room = message.get("room")
                    
                    if not new_room:
                        await manager.send_personal_message(
                            websocket,
                            {
                                "type": "error",
                                "message": "Room adı gerekli"
                            }
                        )
                        continue
                    
                    # Eski room'dan çık
                    if current_room:
                        manager.disconnect(websocket, current_room)
                    
                    # Yeni room'a katıl
                    current_room = new_room
                    await manager.connect(websocket, new_room, user_info)
                
                # leave_room mesajı
                elif message_type == "leave_room":
                    if current_room:
                        manager.disconnect(websocket, current_room)
                        current_room = None
                        
                        await manager.send_personal_message(
                            websocket,
                            {
                                "type": "room_left",
                                "message": "Room'dan ayrıldınız"
                            }
                        )
                
                # ping mesajı (keep-alive)
                elif message_type == "ping":
                    await manager.send_personal_message(
                        websocket,
                        {
                            "type": "pong",
                            "timestamp": message.get("timestamp")
                        }
                    )
                
                # Bilinmeyen mesaj tipi
                else:
                    logger.warning(f"⚠️ Bilinmeyen mesaj tipi: {message_type}")
                    await manager.send_personal_message(
                        websocket,
                        {
                            "type": "error",
                            "message": f"Bilinmeyen mesaj tipi: {message_type}"
                        }
                    )
                
            except json.JSONDecodeError:
                logger.warning("⚠️ Geçersiz JSON mesajı alındı")
                await manager.send_personal_message(
                    websocket,
                    {
                        "type": "error",
                        "message": "Geçersiz JSON formatı"
                    }
                )
            except WebSocketDisconnect:
                raise
            except Exception as e:
                logger.error(f"❌ WebSocket mesaj işleme hatası: {e}", exc_info=True)
                await manager.send_personal_message(
                    websocket,
                    {
                        "type": "error",
                        "message": "Mesaj işlenirken hata oluştu"
                    }
                )
    
    except WebSocketDisconnect:
        logger.info("🔌 WebSocket bağlantısı kesildi (client)")
        if current_room:
            manager.disconnect(websocket, current_room)
    
    except Exception as e:
        logger.error(f"❌ WebSocket hatası: {e}", exc_info=True)
        if current_room:
            manager.disconnect(websocket, current_room)
        try:
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        except:
            pass
