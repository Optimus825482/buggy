"""
Location Endpoints
Lokasyon yönetimi için API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
import logging

from app.database import get_db
from app.api.deps import (
    get_current_active_user,
    require_admin,
    get_user_hotel_id,
    check_resource_access
)
from app.models.user import SystemUser
from app.models.location import Location
from app.schemas.location import (
    LocationCreate,
    LocationUpdate,
    LocationResponse,
    QRCodeResponse,
    LocationListResponse
)
from app.services.location_service import LocationService

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# Public Endpoints (QR kod okuma için)
# =============================================================================

@router.get(
    "/qr/{qr_code}",
    response_model=LocationResponse,
    summary="QR kod ile lokasyon getir",
    description="QR kod okuyarak lokasyon bilgilerini getirir (public endpoint)"
)
async def get_location_by_qr_code(
    qr_code: str,
    db: Session = Depends(get_db)
):
    """
    QR kod ile lokasyon getir
    
    - **qr_code**: QR kod verisi (örn: LOC_ABC123)
    
    Returns:
        LocationResponse: Lokasyon bilgileri
    """
    try:
        logger.info(f"📱 QR kod taraması: {qr_code}")
        location = LocationService.get_location_by_qr_code(db, qr_code)
        logger.info(f"✅ Lokasyon bulundu: {location.name}")
        return location
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ QR kod okuma hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="QR kod okunamadı"
        )


# =============================================================================
# Authenticated Endpoints
# =============================================================================

@router.get(
    "",
    response_model=LocationListResponse,
    summary="Lokasyon listesi",
    description="Kullanıcının oteline ait lokasyonları listeler"
)
async def get_locations(
    is_active: Optional[bool] = Query(None, description="Aktif durum filtresi"),
    skip: int = Query(0, ge=0, description="Kaç kayıt atlanacak"),
    limit: int = Query(100, ge=1, le=1000, description="Maksimum kayıt sayısı"),
    hotel_id: int = Depends(get_user_hotel_id),
    db: Session = Depends(get_db),
    current_user: SystemUser = Depends(get_current_active_user)
):
    """
    Lokasyon listesi getir
    
    - Kullanıcının oteline ait lokasyonları getirir
    - Aktif/pasif filtreleme yapılabilir
    - Pagination destekler
    
    Returns:
        LocationListResponse: Lokasyon listesi ve toplam sayı
    """
    try:
        logger.info(
            f"📋 Lokasyon listesi istendi: user={current_user.username}, "
            f"hotel_id={hotel_id}, is_active={is_active}"
        )
        
        # Lokasyonları getir
        locations = LocationService.get_locations(
            db=db,
            hotel_id=hotel_id,
            is_active=is_active,
            skip=skip,
            limit=limit
        )
        
        # Toplam sayıyı getir
        total = LocationService.count_locations(
            db=db,
            hotel_id=hotel_id,
            is_active=is_active
        )
        
        logger.info(f"✅ {len(locations)} lokasyon bulundu (toplam: {total})")
        
        return LocationListResponse(
            total=total,
            items=locations
        )
        
    except Exception as e:
        logger.error(f"❌ Lokasyon listesi hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Lokasyonlar getirilemedi"
        )


@router.get(
    "/{location_id}",
    response_model=LocationResponse,
    summary="Lokasyon detayı",
    description="ID ile lokasyon detaylarını getirir"
)
async def get_location(
    location_id: int,
    db: Session = Depends(get_db),
    current_user: SystemUser = Depends(get_current_active_user)
):
    """
    Lokasyon detayı getir
    
    - **location_id**: Lokasyon ID
    
    Returns:
        LocationResponse: Lokasyon detayları
    """
    try:
        logger.info(f"🔍 Lokasyon detayı istendi: id={location_id}, user={current_user.username}")
        
        location = LocationService.get_location_by_id(db, location_id)
        
        if not location:
            logger.warning(f"⚠️ Lokasyon bulunamadı: id={location_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lokasyon bulunamadı"
            )
        
        # Kullanıcının bu lokasyona erişim yetkisi var mı kontrol et
        check_resource_access(current_user, location.hotel_id, "lokasyon")
        
        logger.info(f"✅ Lokasyon bulundu: {location.name}")
        return location
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Lokasyon detay hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Lokasyon getirilemedi"
        )


# =============================================================================
# Admin Only Endpoints
# =============================================================================

@router.post(
    "",
    response_model=LocationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Lokasyon oluştur",
    description="Yeni lokasyon oluşturur (sadece admin)"
)
async def create_location(
    location_data: LocationCreate,
    db: Session = Depends(get_db),
    current_user: SystemUser = Depends(require_admin)
):
    """
    Yeni lokasyon oluştur
    
    - Sadece admin kullanıcılar erişebilir
    - QR kod verisi boş bırakılırsa otomatik oluşturulur
    
    Returns:
        LocationResponse: Oluşturulan lokasyon
    """
    try:
        logger.info(
            f"➕ Yeni lokasyon oluşturuluyor: name={location_data.name}, "
            f"hotel_id={location_data.hotel_id}, user={current_user.username}"
        )
        
        # Kullanıcının bu otele lokasyon ekleme yetkisi var mı kontrol et
        check_resource_access(current_user, location_data.hotel_id, "otel")
        
        # Lokasyon oluştur
        location = LocationService.create_location(db, location_data)
        
        logger.info(f"✅ Lokasyon oluşturuldu: id={location.id}, name={location.name}")
        return location
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Lokasyon oluşturma hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Lokasyon oluşturulamadı"
        )


@router.put(
    "/{location_id}",
    response_model=LocationResponse,
    summary="Lokasyon güncelle",
    description="Mevcut lokasyonu günceller (sadece admin)"
)
async def update_location(
    location_id: int,
    location_data: LocationUpdate,
    db: Session = Depends(get_db),
    current_user: SystemUser = Depends(require_admin)
):
    """
    Lokasyon güncelle
    
    - Sadece admin kullanıcılar erişebilir
    - Sadece gönderilen alanlar güncellenir
    
    Returns:
        LocationResponse: Güncellenmiş lokasyon
    """
    try:
        logger.info(
            f"✏️ Lokasyon güncelleniyor: id={location_id}, user={current_user.username}"
        )
        
        # Lokasyonu kontrol et
        existing_location = LocationService.get_location_by_id(db, location_id)
        if not existing_location:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lokasyon bulunamadı"
            )
        
        # Kullanıcının bu lokasyonu güncelleme yetkisi var mı kontrol et
        check_resource_access(current_user, existing_location.hotel_id, "lokasyon")
        
        # Lokasyonu güncelle
        location = LocationService.update_location(db, location_id, location_data)
        
        logger.info(f"✅ Lokasyon güncellendi: id={location.id}, name={location.name}")
        return location
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Lokasyon güncelleme hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Lokasyon güncellenemedi"
        )


@router.delete(
    "/{location_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Lokasyon sil",
    description="Lokasyonu siler (sadece admin)"
)
async def delete_location(
    location_id: int,
    db: Session = Depends(get_db),
    current_user: SystemUser = Depends(require_admin)
):
    """
    Lokasyon sil
    
    - Sadece admin kullanıcılar erişebilir
    - Kullanımda olan lokasyonlar silinemez
    
    Returns:
        204 No Content
    """
    try:
        logger.info(f"🗑️ Lokasyon siliniyor: id={location_id}, user={current_user.username}")
        
        # Lokasyonu kontrol et
        location = LocationService.get_location_by_id(db, location_id)
        if not location:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lokasyon bulunamadı"
            )
        
        # Kullanıcının bu lokasyonu silme yetkisi var mı kontrol et
        check_resource_access(current_user, location.hotel_id, "lokasyon")
        
        # Lokasyonu sil
        LocationService.delete_location(db, location_id)
        
        logger.info(f"✅ Lokasyon silindi: id={location_id}")
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Lokasyon silme hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Lokasyon silinemedi"
        )


@router.post(
    "/{location_id}/qr",
    response_model=QRCodeResponse,
    summary="QR kod oluştur",
    description="Lokasyon için QR kod görseli oluşturur (sadece admin)"
)
async def generate_qr_code(
    location_id: int,
    db: Session = Depends(get_db),
    current_user: SystemUser = Depends(require_admin)
):
    """
    QR kod oluştur
    
    - Sadece admin kullanıcılar erişebilir
    - Lokasyon için QR kod görseli oluşturur ve kaydeder
    - Base64 encoded PNG formatında döner
    
    Returns:
        QRCodeResponse: QR kod verisi ve görseli
    """
    try:
        logger.info(
            f"🔲 QR kod oluşturuluyor: location_id={location_id}, user={current_user.username}"
        )
        
        # Lokasyonu kontrol et
        location = LocationService.get_location_by_id(db, location_id)
        if not location:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lokasyon bulunamadı"
            )
        
        # Kullanıcının bu lokasyon için QR kod oluşturma yetkisi var mı kontrol et
        check_resource_access(current_user, location.hotel_id, "lokasyon")
        
        # QR kod oluştur ve kaydet
        updated_location = LocationService.generate_and_save_qr_code(db, location_id)
        
        logger.info(f"✅ QR kod oluşturuldu: location_id={location_id}")
        
        return QRCodeResponse(
            qr_code_data=updated_location.qr_code_data,
            qr_code_image=updated_location.qr_code_image
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ QR kod oluşturma hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="QR kod oluşturulamadı"
        )
