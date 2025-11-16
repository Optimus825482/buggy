"""
Request Service Layer
Guest ve Driver request işlemleri için business logic
"""
from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_
from fastapi import HTTPException, status

from app.models.request import ShuttleRequest
from app.models.location import Location
from app.models.shuttle import Shuttle
from app.models.enums import RequestStatus, ShuttleStatus
from app.schemas.request import RequestCreate, GuestFCMTokenUpdate


class RequestService:
    """
    Request işlemleri için servis katmanı
    Requirements: 6.1, 6.2, 6.3, 6.4, 6.5
    """
    
    # ========================================================================
    # Guest Operations (Görev 7.2)
    # ========================================================================
    
    @staticmethod
    def create_request(
        db: Session,
        hotel_id: int,
        request_data: RequestCreate
    ) -> ShuttleRequest:
        """
        Yeni shuttle request oluştur
        Requirements: 6.1, 6.2, 6.3
        
        Args:
            db: Database session
            hotel_id: Otel ID
            request_data: Request oluşturma verisi
            
        Returns:
            ShuttleRequest: Oluşturulan request
            
        Raises:
            HTTPException: Lokasyon bulunamazsa veya aktif değilse
        """
        try:
            # 1. Lokasyonu doğrula
            location = RequestService.validate_location(
                db, 
                request_data.location_id, 
                hotel_id
            )
            
            # 2. Müsait shuttle kontrolü
            available_shuttles = RequestService.check_available_shuttles(
                db, 
                hotel_id
            )
            
            if not available_shuttles:
                # Müsait shuttle yoksa da request oluştur ama uyarı ver
                # (Tasarım gereği request her zaman oluşturulmalı)
                pass
            
            # 3. Request oluştur
            new_request = ShuttleRequest(
                hotel_id=hotel_id,
                location_id=request_data.location_id,
                guest_name=request_data.guest_name,
                room_number=request_data.room_number,
                has_room=request_data.has_room,
                phone=request_data.phone,
                notes=request_data.notes,
                status=RequestStatus.PENDING.value,
                requested_at=datetime.utcnow()
            )
            
            db.add(new_request)
            db.commit()
            db.refresh(new_request)
            
            # 4. FCM notification gönder (Görev 9.2)
            try:
                from app.services.fcm_service import notify_new_request
                import asyncio
                
                # Async notification gönder (background task olarak)
                asyncio.create_task(
                    notify_new_request(
                        request_id=new_request.id,
                        hotel_id=hotel_id,
                        location_name=location.name,
                        room_number=request_data.room_number or "N/A",
                        guest_name=request_data.guest_name
                    )
                )
            except Exception as e:
                logger.warning(f"⚠️ FCM notification gönderilemedi: {e}")
            
            # 5. WebSocket event emit et (Görev 10.3)
            try:
                from app.services.websocket_service import emit_new_request
                import asyncio
                
                # Async WebSocket event gönder (background task olarak)
                asyncio.create_task(
                    emit_new_request(
                        hotel_id=hotel_id,
                        request_id=new_request.id,
                        location_name=location.name,
                        room_number=request_data.room_number or "N/A",
                        guest_name=request_data.guest_name
                    )
                )
            except Exception as e:
                logger.warning(f"⚠️ WebSocket event gönderilemedi: {e}")
            
            return new_request
            
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Request oluşturulurken hata: {str(e)}"
            )
    
    @staticmethod
    def validate_location(
        db: Session,
        location_id: int,
        hotel_id: int
    ) -> Location:
        """
        Lokasyonu doğrula
        Requirements: 6.2
        
        Args:
            db: Database session
            location_id: Lokasyon ID
            hotel_id: Otel ID
            
        Returns:
            Location: Doğrulanmış lokasyon
            
        Raises:
            HTTPException: Lokasyon bulunamazsa veya aktif değilse
        """
        location = db.query(Location).filter(
            and_(
                Location.id == location_id,
                Location.hotel_id == hotel_id
            )
        ).first()
        
        if not location:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lokasyon bulunamadı"
            )
        
        if not location.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bu lokasyon aktif değil"
            )
        
        return location
    
    @staticmethod
    def check_available_shuttles(
        db: Session,
        hotel_id: int
    ) -> List[Shuttle]:
        """
        Müsait shuttle'ları kontrol et
        Requirements: 6.3
        
        Args:
            db: Database session
            hotel_id: Otel ID
            
        Returns:
            List[Shuttle]: Müsait shuttle listesi
        """
        available_shuttles = db.query(Shuttle).filter(
            and_(
                Shuttle.hotel_id == hotel_id,
                Shuttle.status == ShuttleStatus.AVAILABLE.value
            )
        ).all()
        
        return available_shuttles
    
    @staticmethod
    def store_guest_fcm_token(
        db: Session,
        request_id: int,
        hotel_id: int,
        token_data: GuestFCMTokenUpdate
    ) -> ShuttleRequest:
        """
        Guest FCM token'ı sakla (1 saat TTL)
        Requirements: 6.4, 6.5
        
        Args:
            db: Database session
            request_id: Request ID
            hotel_id: Otel ID
            token_data: FCM token verisi
            
        Returns:
            ShuttleRequest: Güncellenmiş request
            
        Raises:
            HTTPException: Request bulunamazsa
        """
        try:
            # Request'i bul
            request = db.query(ShuttleRequest).filter(
                and_(
                    ShuttleRequest.id == request_id,
                    ShuttleRequest.hotel_id == hotel_id
                )
            ).first()
            
            if not request:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Request bulunamadı"
                )
            
            # FCM token'ı kaydet (1 saat geçerli)
            request.guest_fcm_token = token_data.fcm_token
            request.guest_fcm_token_expires_at = datetime.utcnow() + timedelta(hours=1)
            
            db.commit()
            db.refresh(request)
            
            return request
            
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"FCM token kaydedilirken hata: {str(e)}"
            )
    
    @staticmethod
    def get_request_by_id(
        db: Session,
        request_id: int,
        hotel_id: Optional[int] = None
    ) -> ShuttleRequest:
        """
        Request'i ID ile getir
        Requirements: 6.5
        
        Args:
            db: Database session
            request_id: Request ID
            hotel_id: Otel ID (opsiyonel, güvenlik için)
            
        Returns:
            ShuttleRequest: Request
            
        Raises:
            HTTPException: Request bulunamazsa
        """
        query = db.query(ShuttleRequest).options(
            joinedload(ShuttleRequest.location),
            joinedload(ShuttleRequest.shuttle),
            joinedload(ShuttleRequest.accepted_by)
        )
        
        if hotel_id:
            query = query.filter(
                and_(
                    ShuttleRequest.id == request_id,
                    ShuttleRequest.hotel_id == hotel_id
                )
            )
        else:
            query = query.filter(ShuttleRequest.id == request_id)
        
        request = query.first()
        
        if not request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Request bulunamadı"
            )
        
        return request
    
    # ========================================================================
    # Driver Operations (Görev 8.1)
    # ========================================================================
    
    @staticmethod
    def get_pending_requests(
        db: Session,
        hotel_id: int
    ) -> List[ShuttleRequest]:
        """
        Bekleyen requestleri getir
        Requirements: 8.1
        
        Args:
            db: Database session
            hotel_id: Otel ID
            
        Returns:
            List[ShuttleRequest]: Bekleyen request listesi
        """
        try:
            pending_requests = db.query(ShuttleRequest).options(
                joinedload(ShuttleRequest.location),
                joinedload(ShuttleRequest.shuttle),
                joinedload(ShuttleRequest.accepted_by)
            ).filter(
                and_(
                    ShuttleRequest.hotel_id == hotel_id,
                    ShuttleRequest.status == RequestStatus.PENDING.value
                )
            ).order_by(ShuttleRequest.requested_at.asc()).all()
            
            return pending_requests
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Bekleyen requestler getirilirken hata: {str(e)}"
            )
    
    @staticmethod
    def accept_request(
        db: Session,
        request_id: int,
        shuttle_id: int,
        driver_id: int,
        hotel_id: int
    ) -> ShuttleRequest:
        """
        Request'i kabul et
        Requirements: 8.2, 8.3
        
        Args:
            db: Database session
            request_id: Request ID
            shuttle_id: Shuttle ID
            driver_id: Driver ID
            hotel_id: Otel ID
            
        Returns:
            ShuttleRequest: Kabul edilmiş request
            
        Raises:
            HTTPException: Request bulunamazsa, zaten kabul edildiyse veya shuttle müsait değilse
        """
        try:
            # 1. Request'i bul
            request = db.query(ShuttleRequest).filter(
                and_(
                    ShuttleRequest.id == request_id,
                    ShuttleRequest.hotel_id == hotel_id
                )
            ).first()
            
            if not request:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Request bulunamadı"
                )
            
            # 2. Request durumunu kontrol et
            if request.status != RequestStatus.PENDING.value:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Bu request zaten {request.status} durumunda"
                )
            
            # 3. Shuttle'ı bul ve kontrol et
            shuttle = db.query(Shuttle).filter(
                and_(
                    Shuttle.id == shuttle_id,
                    Shuttle.hotel_id == hotel_id
                )
            ).first()
            
            if not shuttle:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Shuttle bulunamadı"
                )
            
            if shuttle.status != ShuttleStatus.AVAILABLE.value:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Shuttle müsait değil (durum: {shuttle.status})"
                )
            
            # 4. Driver'ın başka aktif request'i var mı kontrol et
            active_request = RequestService.get_driver_active_request(
                db=db,
                driver_id=driver_id,
                hotel_id=hotel_id
            )
            
            if active_request:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Zaten aktif bir request'iniz var"
                )
            
            # 5. Request'i kabul et
            accepted_at = datetime.utcnow()
            request.status = RequestStatus.ACCEPTED.value
            request.shuttle_id = shuttle_id
            request.accepted_by_id = driver_id
            request.accepted_at = accepted_at
            
            # 6. Response time hesapla
            request.response_time = RequestService.calculate_response_time(
                request.requested_at,
                accepted_at
            )
            
            # 7. Shuttle durumunu güncelle
            shuttle.status = ShuttleStatus.BUSY.value
            
            db.commit()
            db.refresh(request)
            
            # 8. Guest'e FCM notification gönder (Görev 9.2)
            try:
                from app.services.fcm_service import notify_request_accepted
                import asyncio
                
                # Async notification gönder (background task olarak)
                asyncio.create_task(
                    notify_request_accepted(
                        request_id=request.id,
                        shuttle_code=shuttle.code,
                        driver_name=request.accepted_by.full_name if request.accepted_by else "Sürücü",
                        guest_fcm_token=request.guest_fcm_token
                    )
                )
            except Exception as e:
                logger.warning(f"⚠️ FCM notification gönderilemedi: {e}")
            
            # 9. WebSocket event emit et (Görev 10.3)
            try:
                from app.services.websocket_service import emit_request_accepted
                import asyncio
                
                # Async WebSocket event gönder (background task olarak)
                asyncio.create_task(
                    emit_request_accepted(
                        hotel_id=hotel_id,
                        request_id=request.id,
                        shuttle_code=shuttle.code,
                        driver_name=request.accepted_by.full_name if request.accepted_by else "Sürücü"
                    )
                )
            except Exception as e:
                logger.warning(f"⚠️ WebSocket event gönderilemedi: {e}")
            
            return request
            
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Request kabul edilirken hata: {str(e)}"
            )
    
    @staticmethod
    def complete_request(
        db: Session,
        request_id: int,
        completion_location_id: int,
        hotel_id: int
    ) -> ShuttleRequest:
        """
        Request'i tamamla
        Requirements: 8.5, 8.6
        
        Args:
            db: Database session
            request_id: Request ID
            completion_location_id: Tamamlama lokasyonu ID
            hotel_id: Otel ID
            
        Returns:
            ShuttleRequest: Tamamlanmış request
            
        Raises:
            HTTPException: Request bulunamazsa veya kabul edilmemişse
        """
        try:
            # 1. Request'i bul
            request = db.query(ShuttleRequest).filter(
                and_(
                    ShuttleRequest.id == request_id,
                    ShuttleRequest.hotel_id == hotel_id
                )
            ).first()
            
            if not request:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Request bulunamadı"
                )
            
            # 2. Request durumunu kontrol et
            if request.status != RequestStatus.ACCEPTED.value:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Bu request kabul edilmemiş (durum: {request.status})"
                )
            
            # 3. Completion location'ı doğrula
            completion_location = RequestService.validate_location(
                db=db,
                location_id=completion_location_id,
                hotel_id=hotel_id
            )
            
            # 4. Request'i tamamla
            completed_at = datetime.utcnow()
            request.status = RequestStatus.COMPLETED.value
            request.completion_location_id = completion_location_id
            request.completed_at = completed_at
            
            # 5. Completion time hesapla
            if request.accepted_at:
                request.completion_time = RequestService.calculate_completion_time(
                    request.accepted_at,
                    completed_at
                )
            
            # 6. Shuttle durumunu güncelle
            if request.shuttle:
                request.shuttle.status = ShuttleStatus.AVAILABLE.value
                request.shuttle.current_location_id = completion_location_id
            
            db.commit()
            db.refresh(request)
            
            # 7. Guest'e FCM notification gönder (Görev 9.2)
            try:
                from app.services.fcm_service import notify_request_completed
                import asyncio
                
                # Async notification gönder (background task olarak)
                asyncio.create_task(
                    notify_request_completed(
                        request_id=request.id,
                        guest_fcm_token=request.guest_fcm_token
                    )
                )
            except Exception as e:
                logger.warning(f"⚠️ FCM notification gönderilemedi: {e}")
            
            # 8. WebSocket event emit et (Görev 10.3)
            try:
                from app.services.websocket_service import emit_request_completed
                import asyncio
                
                # Async WebSocket event gönder (background task olarak)
                asyncio.create_task(
                    emit_request_completed(
                        hotel_id=hotel_id,
                        request_id=request.id
                    )
                )
            except Exception as e:
                logger.warning(f"⚠️ WebSocket event gönderilemedi: {e}")
            
            return request
            
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Request tamamlanırken hata: {str(e)}"
            )
    
    @staticmethod
    def get_driver_active_request(
        db: Session,
        driver_id: int,
        hotel_id: int
    ) -> Optional[ShuttleRequest]:
        """
        Driver'ın aktif request'ini getir
        Requirements: 8.1
        
        Args:
            db: Database session
            driver_id: Driver ID
            hotel_id: Otel ID
            
        Returns:
            Optional[ShuttleRequest]: Aktif request (varsa)
        """
        try:
            active_request = db.query(ShuttleRequest).options(
                joinedload(ShuttleRequest.location),
                joinedload(ShuttleRequest.shuttle),
                joinedload(ShuttleRequest.accepted_by)
            ).filter(
                and_(
                    ShuttleRequest.hotel_id == hotel_id,
                    ShuttleRequest.accepted_by_id == driver_id,
                    ShuttleRequest.status == RequestStatus.ACCEPTED.value
                )
            ).first()
            
            return active_request
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Aktif request getirilirken hata: {str(e)}"
            )
    
    @staticmethod
    def calculate_response_time(
        requested_at: datetime,
        accepted_at: datetime
    ) -> int:
        """
        Yanıt süresini hesapla (saniye)
        Requirements: 8.6
        
        Args:
            requested_at: Talep zamanı
            accepted_at: Kabul zamanı
            
        Returns:
            int: Yanıt süresi (saniye)
        """
        delta = accepted_at - requested_at
        return int(delta.total_seconds())
    
    @staticmethod
    def calculate_completion_time(
        accepted_at: datetime,
        completed_at: datetime
    ) -> int:
        """
        Tamamlanma süresini hesapla (saniye)
        Requirements: 8.6
        
        Args:
            accepted_at: Kabul zamanı
            completed_at: Tamamlanma zamanı
            
        Returns:
            int: Tamamlanma süresi (saniye)
        """
        delta = completed_at - accepted_at
        return int(delta.total_seconds())
