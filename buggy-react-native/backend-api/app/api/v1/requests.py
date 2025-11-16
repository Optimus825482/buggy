"""
Request API Endpoints
Guest ve Driver request işlemleri
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging

from app.database import get_db
from app.api.deps import (
    get_current_user_optional,
    get_current_active_user,
    get_user_hotel_id
)
from app.models.user import SystemUser
from app.schemas.request import (
    RequestCreate,
    RequestResponse,
    GuestFCMTokenUpdate,
    RequestAccept,
    RequestComplete
)
from app.services.request_service import RequestService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/requests", tags=["requests"])


# =============================================================================
# Guest Request Endpoints (Görev 7.3)
# =============================================================================

@router.post(
    "",
    response_model=RequestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Yeni shuttle request oluştur",
    description="""
    Guest tarafından yeni shuttle çağrısı oluşturur.
    
    **Requirements:** 6.1, 6.2, 6.3
    
    **İşlem Adımları:**
    1. Lokasyonu doğrula
    2. Müsait shuttle kontrolü yap
    3. Request oluştur
    4. Sürücülere FCM notification gönder (TODO: Görev 9.2)
    5. WebSocket event emit et (TODO: Görev 10.3)
    
    **Not:** Bu endpoint authentication gerektirmez (guest kullanımı için).
    Ancak hotel_id query parameter olarak gönderilmelidir.
    """
)
async def create_request(
    request_data: RequestCreate,
    hotel_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[SystemUser] = Depends(get_current_user_optional)
) -> RequestResponse:
    """
    Yeni shuttle request oluştur
    
    Args:
        request_data: Request oluşturma verisi
        hotel_id: Otel ID (query parameter)
        db: Database session
        current_user: Mevcut kullanıcı (opsiyonel, guest için None)
        
    Returns:
        RequestResponse: Oluşturulan request
        
    Raises:
        HTTPException: Lokasyon bulunamazsa veya hata oluşursa
    """
    try:
        logger.info(
            f"📞 Yeni request oluşturuluyor: hotel_id={hotel_id}, "
            f"location_id={request_data.location_id}, room={request_data.room_number}"
        )
        
        # Request oluştur
        new_request = RequestService.create_request(
            db=db,
            hotel_id=hotel_id,
            request_data=request_data
        )
        
        logger.info(f"✅ Request oluşturuldu: request_id={new_request.id}")
        
        return new_request
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Request oluşturma hatası: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Request oluşturulurken bir hata oluştu"
        )


@router.get(
    "/{request_id}",
    response_model=RequestResponse,
    summary="Request detayını getir",
    description="""
    Request ID ile request detaylarını getirir.
    
    **Requirements:** 6.5
    
    **Not:** Bu endpoint authentication gerektirmez (guest kullanımı için).
    Ancak hotel_id query parameter olarak gönderilmelidir.
    """
)
async def get_request(
    request_id: int,
    hotel_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[SystemUser] = Depends(get_current_user_optional)
) -> RequestResponse:
    """
    Request detayını getir
    
    Args:
        request_id: Request ID
        hotel_id: Otel ID (query parameter)
        db: Database session
        current_user: Mevcut kullanıcı (opsiyonel)
        
    Returns:
        RequestResponse: Request detayı
        
    Raises:
        HTTPException: Request bulunamazsa
    """
    try:
        logger.debug(f"🔍 Request getiriliyor: request_id={request_id}, hotel_id={hotel_id}")
        
        # Request'i getir
        request = RequestService.get_request_by_id(
            db=db,
            request_id=request_id,
            hotel_id=hotel_id
        )
        
        logger.debug(f"✅ Request bulundu: request_id={request_id}, status={request.status}")
        
        return request
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Request getirme hatası: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Request getirilirken bir hata oluştu"
        )


@router.put(
    "/{request_id}/fcm-token",
    response_model=RequestResponse,
    summary="Guest FCM token güncelle",
    description="""
    Guest'in FCM token'ını request'e kaydeder (1 saat TTL).
    
    **Requirements:** 6.4, 6.5
    
    Bu token, request kabul edildiğinde veya tamamlandığında
    guest'e push notification göndermek için kullanılır.
    
    **Not:** Bu endpoint authentication gerektirmez (guest kullanımı için).
    """
)
async def update_guest_fcm_token(
    request_id: int,
    hotel_id: int,
    token_data: GuestFCMTokenUpdate,
    db: Session = Depends(get_db),
    current_user: Optional[SystemUser] = Depends(get_current_user_optional)
) -> RequestResponse:
    """
    Guest FCM token güncelle
    
    Args:
        request_id: Request ID
        hotel_id: Otel ID (query parameter)
        token_data: FCM token verisi
        db: Database session
        current_user: Mevcut kullanıcı (opsiyonel)
        
    Returns:
        RequestResponse: Güncellenmiş request
        
    Raises:
        HTTPException: Request bulunamazsa
    """
    try:
        logger.info(f"🔔 FCM token kaydediliyor: request_id={request_id}")
        
        # FCM token'ı kaydet
        updated_request = RequestService.store_guest_fcm_token(
            db=db,
            request_id=request_id,
            hotel_id=hotel_id,
            token_data=token_data
        )
        
        logger.info(f"✅ FCM token kaydedildi: request_id={request_id}")
        
        return updated_request
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ FCM token kaydetme hatası: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="FCM token kaydedilirken bir hata oluştu"
        )


# =============================================================================
# Driver Request Endpoints (Görev 8.2'de implement edilecek)
# =============================================================================

@router.get(
    "/pending",
    response_model=list[RequestResponse],
    summary="Bekleyen requestleri listele",
    description="""
    Driver için bekleyen (PENDING) requestleri listeler.
    
    **Requirements:** 8.1
    
    **Authentication:** Driver veya Admin
    
    **İşlem:**
    - Otelin tüm PENDING durumundaki requestleri getirir
    - Talep zamanına göre sıralanır (en eski önce)
    """
)
async def get_pending_requests(
    db: Session = Depends(get_db),
    hotel_id: int = Depends(get_user_hotel_id),
    current_user: SystemUser = Depends(get_current_active_user)
) -> list[RequestResponse]:
    """
    Bekleyen requestleri listele
    
    Args:
        db: Database session
        hotel_id: Otel ID (user'dan alınır)
        current_user: Mevcut kullanıcı (driver veya admin)
        
    Returns:
        list[RequestResponse]: Bekleyen request listesi
    """
    try:
        logger.debug(f"📋 Bekleyen requestler getiriliyor: hotel_id={hotel_id}, user={current_user.username}")
        
        # Bekleyen requestleri getir
        pending_requests = RequestService.get_pending_requests(
            db=db,
            hotel_id=hotel_id
        )
        
        logger.debug(f"✅ {len(pending_requests)} bekleyen request bulundu")
        
        return pending_requests
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Bekleyen requestler getirme hatası: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Bekleyen requestler getirilirken bir hata oluştu"
        )


@router.get(
    "/active",
    response_model=Optional[RequestResponse],
    summary="Aktif request'i getir",
    description="""
    Driver'ın aktif (ACCEPTED) request'ini getirir.
    
    **Requirements:** 8.1
    
    **Authentication:** Driver
    
    **İşlem:**
    - Driver'ın ACCEPTED durumundaki request'ini getirir
    - Bir driver aynı anda sadece 1 aktif request'e sahip olabilir
    - Aktif request yoksa None döner
    """
)
async def get_active_request(
    db: Session = Depends(get_db),
    hotel_id: int = Depends(get_user_hotel_id),
    current_user: SystemUser = Depends(get_current_active_user)
) -> Optional[RequestResponse]:
    """
    Aktif request'i getir
    
    Args:
        db: Database session
        hotel_id: Otel ID (user'dan alınır)
        current_user: Mevcut kullanıcı (driver)
        
    Returns:
        Optional[RequestResponse]: Aktif request (varsa)
    """
    try:
        logger.debug(f"🔍 Aktif request getiriliyor: driver={current_user.username}")
        
        # Aktif request'i getir
        active_request = RequestService.get_driver_active_request(
            db=db,
            driver_id=current_user.id,
            hotel_id=hotel_id
        )
        
        if active_request:
            logger.debug(f"✅ Aktif request bulundu: request_id={active_request.id}")
        else:
            logger.debug("ℹ️ Aktif request yok")
        
        return active_request
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Aktif request getirme hatası: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Aktif request getirilirken bir hata oluştu"
        )


@router.put(
    "/{request_id}/accept",
    response_model=RequestResponse,
    summary="Request'i kabul et",
    description="""
    Driver tarafından request kabul edilir.
    
    **Requirements:** 8.2, 8.3
    
    **Authentication:** Driver
    
    **İşlem Adımları:**
    1. Request'i ACCEPTED durumuna güncelle
    2. Shuttle'ı BUSY durumuna güncelle
    3. Response time hesapla
    4. Guest'e FCM notification gönder (TODO: Görev 9.2)
    5. WebSocket event emit et (TODO: Görev 10.3)
    
    **Validasyonlar:**
    - Request PENDING durumunda olmalı
    - Shuttle müsait (AVAILABLE) olmalı
    - Driver'ın başka aktif request'i olmamalı
    """
)
async def accept_request(
    request_id: int,
    accept_data: RequestAccept,
    db: Session = Depends(get_db),
    hotel_id: int = Depends(get_user_hotel_id),
    current_user: SystemUser = Depends(get_current_active_user)
) -> RequestResponse:
    """
    Request'i kabul et
    
    Args:
        request_id: Request ID
        accept_data: Kabul verisi (shuttle_id)
        db: Database session
        hotel_id: Otel ID (user'dan alınır)
        current_user: Mevcut kullanıcı (driver)
        
    Returns:
        RequestResponse: Kabul edilmiş request
    """
    try:
        logger.info(
            f"✅ Request kabul ediliyor: request_id={request_id}, "
            f"shuttle_id={accept_data.shuttle_id}, driver={current_user.username}"
        )
        
        # Request'i kabul et
        accepted_request = RequestService.accept_request(
            db=db,
            request_id=request_id,
            shuttle_id=accept_data.shuttle_id,
            driver_id=current_user.id,
            hotel_id=hotel_id
        )
        
        logger.info(
            f"✅ Request kabul edildi: request_id={request_id}, "
            f"response_time={accepted_request.response_time}s"
        )
        
        return accepted_request
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Request kabul etme hatası: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Request kabul edilirken bir hata oluştu"
        )


@router.put(
    "/{request_id}/complete",
    response_model=RequestResponse,
    summary="Request'i tamamla",
    description="""
    Driver tarafından request tamamlanır.
    
    **Requirements:** 8.5, 8.6
    
    **Authentication:** Driver
    
    **İşlem Adımları:**
    1. Request'i COMPLETED durumuna güncelle
    2. Shuttle'ı AVAILABLE durumuna güncelle
    3. Shuttle'ın lokasyonunu güncelle
    4. Completion time hesapla
    5. Guest'e FCM notification gönder (TODO: Görev 9.2)
    6. WebSocket event emit et (TODO: Görev 10.3)
    
    **Validasyonlar:**
    - Request ACCEPTED durumunda olmalı
    - Completion location geçerli ve aktif olmalı
    """
)
async def complete_request(
    request_id: int,
    complete_data: RequestComplete,
    db: Session = Depends(get_db),
    hotel_id: int = Depends(get_user_hotel_id),
    current_user: SystemUser = Depends(get_current_active_user)
) -> RequestResponse:
    """
    Request'i tamamla
    
    Args:
        request_id: Request ID
        complete_data: Tamamlama verisi (completion_location_id)
        db: Database session
        hotel_id: Otel ID (user'dan alınır)
        current_user: Mevcut kullanıcı (driver)
        
    Returns:
        RequestResponse: Tamamlanmış request
    """
    try:
        logger.info(
            f"🏁 Request tamamlanıyor: request_id={request_id}, "
            f"completion_location_id={complete_data.completion_location_id}, "
            f"driver={current_user.username}"
        )
        
        # Request'i tamamla
        completed_request = RequestService.complete_request(
            db=db,
            request_id=request_id,
            completion_location_id=complete_data.completion_location_id,
            hotel_id=hotel_id
        )
        
        logger.info(
            f"✅ Request tamamlandı: request_id={request_id}, "
            f"completion_time={completed_request.completion_time}s"
        )
        
        return completed_request
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Request tamamlama hatası: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Request tamamlanırken bir hata oluştu"
        )
