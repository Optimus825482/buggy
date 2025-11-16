"""
Shuttle Endpoints
Shuttle yönetimi için API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
import logging

from app.database import get_db
from app.api.deps import (
    get_current_active_user,
    require_admin,
    require_driver,
    get_user_hotel_id,
    check_resource_access
)
from app.models.user import SystemUser
from app.models.shuttle import Shuttle
from app.models.enums import ShuttleStatus
from app.schemas.shuttle import (
    ShuttleCreate,
    ShuttleUpdate,
    ShuttleStatusUpdate,
    ShuttleLocationUpdate,
    ShuttleResponse,
    ShuttleDetailResponse,
    ShuttleListResponse,
    DriverAssignment,
    DriverAssignmentResponse
)
from app.services.shuttle_service import ShuttleService

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# Authenticated Endpoints (Tüm kullanıcılar)
# =============================================================================

@router.get(
    "",
    response_model=ShuttleListResponse,
    summary="Shuttle listesi",
    description="Kullanıcının oteline ait shuttle'ları listeler"
)
async def get_shuttles(
    status_filter: Optional[ShuttleStatus] = Query(None, alias="status", description="Durum filtresi"),
    skip: int = Query(0, ge=0, description="Kaç kayıt atlanacak"),
    limit: int = Query(100, ge=1, le=1000, description="Maksimum kayıt sayısı"),
    hotel_id: int = Depends(get_user_hotel_id),
    db: Session = Depends(get_db),
    current_user: SystemUser = Depends(get_current_active_user)
):
    """
    Shuttle listesi getir
    
    - Kullanıcının oteline ait shuttle'ları getirir
    - Durum filtreleme yapılabilir (available/busy/offline)
    - Pagination destekler
    
    Returns:
        ShuttleListResponse: Shuttle listesi ve toplam sayı
    """
    try:
        logger.info(
            f"📋 Shuttle listesi istendi: user={current_user.username}, "
            f"hotel_id={hotel_id}, status={status_filter}"
        )
        
        # Shuttle'ları getir
        shuttles = ShuttleService.get_shuttles(
            db=db,
            hotel_id=hotel_id,
            status=status_filter,
            skip=skip,
            limit=limit
        )
        
        # Toplam sayıyı getir
        total = ShuttleService.count_shuttles(
            db=db,
            hotel_id=hotel_id,
            status=status_filter
        )
        
        # Response'a ekstra bilgiler ekle
        shuttle_responses = []
        for shuttle in shuttles:
            shuttle_dict = {
                "id": shuttle.id,
                "hotel_id": shuttle.hotel_id,
                "code": shuttle.code,
                "model": shuttle.model,
                "license_plate": shuttle.license_plate,
                "icon": shuttle.icon,
                "current_location_id": shuttle.current_location_id,
                "status": shuttle.status,
                "created_at": shuttle.created_at,
                "updated_at": shuttle.updated_at,
                "current_location_name": shuttle.current_location.name if shuttle.current_location else None,
                "active_driver_count": sum(1 for a in shuttle.driver_assignments if a.is_active)
            }
            shuttle_responses.append(ShuttleResponse(**shuttle_dict))
        
        logger.info(f"✅ {len(shuttles)} shuttle bulundu (toplam: {total})")
        
        return ShuttleListResponse(
            total=total,
            items=shuttle_responses
        )
        
    except Exception as e:
        logger.error(f"❌ Shuttle listesi hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Shuttle'lar getirilemedi"
        )


@router.get(
    "/{shuttle_id}",
    response_model=ShuttleDetailResponse,
    summary="Shuttle detayı",
    description="ID ile shuttle detaylarını getirir"
)
async def get_shuttle(
    shuttle_id: int,
    db: Session = Depends(get_db),
    current_user: SystemUser = Depends(get_current_active_user)
):
    """
    Shuttle detayı getir
    
    - **shuttle_id**: Shuttle ID
    
    Returns:
        ShuttleDetailResponse: Shuttle detayları ve ilişkili veriler
    """
    try:
        logger.info(f"🔍 Shuttle detayı istendi: id={shuttle_id}, user={current_user.username}")
        
        shuttle = ShuttleService.get_shuttle_by_id(db, shuttle_id)
        
        if not shuttle:
            logger.warning(f"⚠️ Shuttle bulunamadı: id={shuttle_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Shuttle bulunamadı"
            )
        
        # Kullanıcının bu shuttle'a erişim yetkisi var mı kontrol et
        check_resource_access(current_user, shuttle.hotel_id, "shuttle")
        
        # Aktif sürücüleri getir
        assignments = ShuttleService.get_driver_assignments(db, shuttle_id, active_only=True)
        active_drivers = [
            {
                "driver_id": a.driver_id,
                "driver_name": a.driver.full_name,
                "is_primary": a.is_primary
            }
            for a in assignments
        ]
        
        # Response oluştur
        shuttle_dict = {
            "id": shuttle.id,
            "hotel_id": shuttle.hotel_id,
            "code": shuttle.code,
            "model": shuttle.model,
            "license_plate": shuttle.license_plate,
            "icon": shuttle.icon,
            "current_location_id": shuttle.current_location_id,
            "status": shuttle.status,
            "created_at": shuttle.created_at,
            "updated_at": shuttle.updated_at,
            "hotel_name": shuttle.hotel.name if shuttle.hotel else None,
            "current_location_name": shuttle.current_location.name if shuttle.current_location else None,
            "active_drivers": active_drivers
        }
        
        logger.info(f"✅ Shuttle bulundu: {shuttle.code}")
        return ShuttleDetailResponse(**shuttle_dict)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Shuttle detay hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Shuttle getirilemedi"
        )


# =============================================================================
# Driver Endpoints
# =============================================================================

@router.put(
    "/{shuttle_id}/status",
    response_model=ShuttleResponse,
    summary="Shuttle durumunu güncelle",
    description="Shuttle durumunu günceller (driver)"
)
async def update_shuttle_status(
    shuttle_id: int,
    status_data: ShuttleStatusUpdate,
    db: Session = Depends(get_db),
    current_user: SystemUser = Depends(require_driver)
):
    """
    Shuttle durumunu güncelle
    
    - Sürücüler kendi shuttle'larının durumunu güncelleyebilir
    - Durum: available, busy, offline
    - Opsiyonel olarak lokasyon da güncellenebilir
    
    Returns:
        ShuttleResponse: Güncellenmiş shuttle
    """
    try:
        logger.info(
            f"🔄 Shuttle durumu güncelleniyor: id={shuttle_id}, "
            f"status={status_data.status}, user={current_user.username}"
        )
        
        # Shuttle'ı kontrol et
        shuttle = ShuttleService.get_shuttle_by_id(db, shuttle_id)
        if not shuttle:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Shuttle bulunamadı"
            )
        
        # Kullanıcının bu shuttle'a erişim yetkisi var mı kontrol et
        check_resource_access(current_user, shuttle.hotel_id, "shuttle")
        
        # Sürücünün bu shuttle'a atanmış olup olmadığını kontrol et
        assignments = ShuttleService.get_driver_assignments(db, shuttle_id, active_only=True)
        is_assigned = any(a.driver_id == current_user.id for a in assignments)
        
        if not is_assigned:
            logger.warning(
                f"⚠️ Sürücü bu shuttle'a atanmamış: driver={current_user.username}, "
                f"shuttle={shuttle.code}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bu shuttle'a atanmamışsınız"
            )
        
        # Durumu güncelle
        updated_shuttle = ShuttleService.update_shuttle_status(db, shuttle_id, status_data)
        
        logger.info(
            f"✅ Shuttle durumu güncellendi: id={shuttle_id}, "
            f"status={updated_shuttle.status}"
        )
        
        return ShuttleResponse(
            id=updated_shuttle.id,
            hotel_id=updated_shuttle.hotel_id,
            code=updated_shuttle.code,
            model=updated_shuttle.model,
            license_plate=updated_shuttle.license_plate,
            icon=updated_shuttle.icon,
            current_location_id=updated_shuttle.current_location_id,
            status=updated_shuttle.status,
            created_at=updated_shuttle.created_at,
            updated_at=updated_shuttle.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Shuttle durum güncelleme hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Shuttle durumu güncellenemedi"
        )


@router.put(
    "/{shuttle_id}/location",
    response_model=ShuttleResponse,
    summary="Shuttle lokasyonunu güncelle",
    description="Shuttle'ın mevcut lokasyonunu günceller (driver)"
)
async def update_shuttle_location(
    shuttle_id: int,
    location_data: ShuttleLocationUpdate,
    db: Session = Depends(get_db),
    current_user: SystemUser = Depends(require_driver)
):
    """
    Shuttle lokasyonunu güncelle
    
    - Sürücüler kendi shuttle'larının lokasyonunu güncelleyebilir
    
    Returns:
        ShuttleResponse: Güncellenmiş shuttle
    """
    try:
        logger.info(
            f"📍 Shuttle lokasyonu güncelleniyor: id={shuttle_id}, "
            f"location_id={location_data.current_location_id}, user={current_user.username}"
        )
        
        # Shuttle'ı kontrol et
        shuttle = ShuttleService.get_shuttle_by_id(db, shuttle_id)
        if not shuttle:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Shuttle bulunamadı"
            )
        
        # Kullanıcının bu shuttle'a erişim yetkisi var mı kontrol et
        check_resource_access(current_user, shuttle.hotel_id, "shuttle")
        
        # Sürücünün bu shuttle'a atanmış olup olmadığını kontrol et
        assignments = ShuttleService.get_driver_assignments(db, shuttle_id, active_only=True)
        is_assigned = any(a.driver_id == current_user.id for a in assignments)
        
        if not is_assigned:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bu shuttle'a atanmamışsınız"
            )
        
        # Lokasyonu güncelle
        updated_shuttle = ShuttleService.update_shuttle_location(
            db, shuttle_id, location_data.current_location_id
        )
        
        logger.info(
            f"✅ Shuttle lokasyonu güncellendi: id={shuttle_id}, "
            f"location_id={updated_shuttle.current_location_id}"
        )
        
        return ShuttleResponse(
            id=updated_shuttle.id,
            hotel_id=updated_shuttle.hotel_id,
            code=updated_shuttle.code,
            model=updated_shuttle.model,
            license_plate=updated_shuttle.license_plate,
            icon=updated_shuttle.icon,
            current_location_id=updated_shuttle.current_location_id,
            status=updated_shuttle.status,
            created_at=updated_shuttle.created_at,
            updated_at=updated_shuttle.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Shuttle lokasyon güncelleme hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Shuttle lokasyonu güncellenemedi"
        )


# =============================================================================
# Admin Only Endpoints
# =============================================================================

@router.post(
    "",
    response_model=ShuttleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Shuttle oluştur",
    description="Yeni shuttle oluşturur (sadece admin)"
)
async def create_shuttle(
    shuttle_data: ShuttleCreate,
    db: Session = Depends(get_db),
    current_user: SystemUser = Depends(require_admin)
):
    """
    Yeni shuttle oluştur
    
    - Sadece admin kullanıcılar erişebilir
    - Shuttle kodu otomatik olarak büyük harfe çevrilir
    
    Returns:
        ShuttleResponse: Oluşturulan shuttle
    """
    try:
        logger.info(
            f"➕ Yeni shuttle oluşturuluyor: code={shuttle_data.code}, "
            f"hotel_id={shuttle_data.hotel_id}, user={current_user.username}"
        )
        
        # Kullanıcının bu otele shuttle ekleme yetkisi var mı kontrol et
        check_resource_access(current_user, shuttle_data.hotel_id, "otel")
        
        # Shuttle oluştur
        shuttle = ShuttleService.create_shuttle(db, shuttle_data)
        
        logger.info(f"✅ Shuttle oluşturuldu: id={shuttle.id}, code={shuttle.code}")
        
        return ShuttleResponse(
            id=shuttle.id,
            hotel_id=shuttle.hotel_id,
            code=shuttle.code,
            model=shuttle.model,
            license_plate=shuttle.license_plate,
            icon=shuttle.icon,
            current_location_id=shuttle.current_location_id,
            status=shuttle.status,
            created_at=shuttle.created_at,
            updated_at=shuttle.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Shuttle oluşturma hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Shuttle oluşturulamadı"
        )


@router.put(
    "/{shuttle_id}",
    response_model=ShuttleResponse,
    summary="Shuttle güncelle",
    description="Mevcut shuttle'ı günceller (sadece admin)"
)
async def update_shuttle(
    shuttle_id: int,
    shuttle_data: ShuttleUpdate,
    db: Session = Depends(get_db),
    current_user: SystemUser = Depends(require_admin)
):
    """
    Shuttle güncelle
    
    - Sadece admin kullanıcılar erişebilir
    - Sadece gönderilen alanlar güncellenir
    
    Returns:
        ShuttleResponse: Güncellenmiş shuttle
    """
    try:
        logger.info(
            f"✏️ Shuttle güncelleniyor: id={shuttle_id}, user={current_user.username}"
        )
        
        # Shuttle'ı kontrol et
        existing_shuttle = ShuttleService.get_shuttle_by_id(db, shuttle_id)
        if not existing_shuttle:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Shuttle bulunamadı"
            )
        
        # Kullanıcının bu shuttle'ı güncelleme yetkisi var mı kontrol et
        check_resource_access(current_user, existing_shuttle.hotel_id, "shuttle")
        
        # Shuttle'ı güncelle
        shuttle = ShuttleService.update_shuttle(db, shuttle_id, shuttle_data)
        
        logger.info(f"✅ Shuttle güncellendi: id={shuttle.id}, code={shuttle.code}")
        
        return ShuttleResponse(
            id=shuttle.id,
            hotel_id=shuttle.hotel_id,
            code=shuttle.code,
            model=shuttle.model,
            license_plate=shuttle.license_plate,
            icon=shuttle.icon,
            current_location_id=shuttle.current_location_id,
            status=shuttle.status,
            created_at=shuttle.created_at,
            updated_at=shuttle.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Shuttle güncelleme hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Shuttle güncellenemedi"
        )


@router.delete(
    "/{shuttle_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Shuttle sil",
    description="Shuttle'ı siler (sadece admin)"
)
async def delete_shuttle(
    shuttle_id: int,
    db: Session = Depends(get_db),
    current_user: SystemUser = Depends(require_admin)
):
    """
    Shuttle sil
    
    - Sadece admin kullanıcılar erişebilir
    - Aktif görevde olan shuttle'lar silinemez
    
    Returns:
        204 No Content
    """
    try:
        logger.info(f"🗑️ Shuttle siliniyor: id={shuttle_id}, user={current_user.username}")
        
        # Shuttle'ı kontrol et
        shuttle = ShuttleService.get_shuttle_by_id(db, shuttle_id)
        if not shuttle:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Shuttle bulunamadı"
            )
        
        # Kullanıcının bu shuttle'ı silme yetkisi var mı kontrol et
        check_resource_access(current_user, shuttle.hotel_id, "shuttle")
        
        # Shuttle'ı sil
        ShuttleService.delete_shuttle(db, shuttle_id)
        
        logger.info(f"✅ Shuttle silindi: id={shuttle_id}")
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Shuttle silme hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Shuttle silinemedi"
        )


@router.post(
    "/{shuttle_id}/drivers",
    response_model=DriverAssignmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Sürücü ata",
    description="Shuttle'a sürücü atar (sadece admin)"
)
async def assign_driver(
    shuttle_id: int,
    assignment_data: DriverAssignment,
    db: Session = Depends(get_db),
    current_user: SystemUser = Depends(require_admin)
):
    """
    Shuttle'a sürücü ata
    
    - Sadece admin kullanıcılar erişebilir
    - Aynı sürücü birden fazla kez atanamaz
    
    Returns:
        DriverAssignmentResponse: Atama bilgileri
    """
    try:
        logger.info(
            f"👤 Sürücü atanıyor: shuttle_id={shuttle_id}, "
            f"driver_id={assignment_data.driver_id}, user={current_user.username}"
        )
        
        # Shuttle'ı kontrol et
        shuttle = ShuttleService.get_shuttle_by_id(db, shuttle_id)
        if not shuttle:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Shuttle bulunamadı"
            )
        
        # Kullanıcının bu shuttle'a sürücü atama yetkisi var mı kontrol et
        check_resource_access(current_user, shuttle.hotel_id, "shuttle")
        
        # Sürücüyü ata
        assignment = ShuttleService.assign_driver_to_shuttle(
            db=db,
            shuttle_id=shuttle_id,
            driver_id=assignment_data.driver_id,
            is_primary=assignment_data.is_primary,
            is_active=assignment_data.is_active
        )
        
        logger.info(
            f"✅ Sürücü atandı: shuttle_id={shuttle_id}, "
            f"driver_id={assignment_data.driver_id}"
        )
        
        return DriverAssignmentResponse(
            shuttle_id=assignment.shuttle_id,
            driver_id=assignment.driver_id,
            driver_name=assignment.driver.full_name,
            is_primary=assignment.is_primary,
            is_active=assignment.is_active,
            assigned_at=assignment.assigned_at,
            last_active_at=assignment.last_active_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Sürücü atama hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Sürücü atanamadı"
        )


@router.get(
    "/{shuttle_id}/drivers",
    response_model=list[DriverAssignmentResponse],
    summary="Sürücü atamalarını listele",
    description="Shuttle'ın sürücü atamalarını listeler (sadece admin)"
)
async def get_driver_assignments(
    shuttle_id: int,
    active_only: bool = Query(False, description="Sadece aktif atamaları getir"),
    db: Session = Depends(get_db),
    current_user: SystemUser = Depends(require_admin)
):
    """
    Shuttle'ın sürücü atamalarını listele
    
    - Sadece admin kullanıcılar erişebilir
    
    Returns:
        List[DriverAssignmentResponse]: Atama listesi
    """
    try:
        logger.info(
            f"📋 Sürücü atamaları istendi: shuttle_id={shuttle_id}, "
            f"active_only={active_only}, user={current_user.username}"
        )
        
        # Shuttle'ı kontrol et
        shuttle = ShuttleService.get_shuttle_by_id(db, shuttle_id)
        if not shuttle:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Shuttle bulunamadı"
            )
        
        # Kullanıcının bu shuttle'ın atamalarını görme yetkisi var mı kontrol et
        check_resource_access(current_user, shuttle.hotel_id, "shuttle")
        
        # Atamaları getir
        assignments = ShuttleService.get_driver_assignments(db, shuttle_id, active_only)
        
        logger.info(f"✅ {len(assignments)} atama bulundu")
        
        return [
            DriverAssignmentResponse(
                shuttle_id=a.shuttle_id,
                driver_id=a.driver_id,
                driver_name=a.driver.full_name,
                is_primary=a.is_primary,
                is_active=a.is_active,
                assigned_at=a.assigned_at,
                last_active_at=a.last_active_at
            )
            for a in assignments
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Atama listesi hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Atamalar getirilemedi"
        )


@router.delete(
    "/{shuttle_id}/drivers/{driver_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Sürücü atamasını kaldır",
    description="Shuttle'dan sürücü atamasını kaldırır (sadece admin)"
)
async def remove_driver_assignment(
    shuttle_id: int,
    driver_id: int,
    db: Session = Depends(get_db),
    current_user: SystemUser = Depends(require_admin)
):
    """
    Sürücü atamasını kaldır
    
    - Sadece admin kullanıcılar erişebilir
    
    Returns:
        204 No Content
    """
    try:
        logger.info(
            f"🗑️ Sürücü ataması kaldırılıyor: shuttle_id={shuttle_id}, "
            f"driver_id={driver_id}, user={current_user.username}"
        )
        
        # Shuttle'ı kontrol et
        shuttle = ShuttleService.get_shuttle_by_id(db, shuttle_id)
        if not shuttle:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Shuttle bulunamadı"
            )
        
        # Kullanıcının bu atamayı kaldırma yetkisi var mı kontrol et
        check_resource_access(current_user, shuttle.hotel_id, "shuttle")
        
        # Atamayı kaldır
        ShuttleService.remove_driver_assignment(db, shuttle_id, driver_id)
        
        logger.info(f"✅ Sürücü ataması kaldırıldı: shuttle_id={shuttle_id}, driver_id={driver_id}")
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Atama kaldırma hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Atama kaldırılamadı"
        )
