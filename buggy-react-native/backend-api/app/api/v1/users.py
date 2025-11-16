"""
User API Endpoints
Kullanıcı yönetimi ve FCM token işlemleri
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from app.database import get_db
from app.api.deps import (
    get_current_active_user,
    get_user_hotel_id,
    require_admin
)
from app.models.user import SystemUser
from app.schemas.user import (
    FCMTokenUpdate,
    FCMTokenResponse,
    UserCreate,
    UserUpdate
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["users"])


# =============================================================================
# FCM Token Endpoints (Görev 9.3)
# =============================================================================

@router.put(
    "/{user_id}/fcm-token",
    response_model=FCMTokenResponse,
    summary="Driver FCM token güncelle",
    description="""
    Driver'ın FCM token'ını günceller.
    
    **Requirements:** 7.1, 7.2
    
    **Authentication:** Driver (kendi token'ını) veya Admin
    
    **İşlem:**
    - FCM token'ı veritabanına kaydeder
    - Token kayıt tarihini günceller
    - Push notification almak için gereklidir
    """
)
async def update_fcm_token(
    user_id: int,
    token_data: FCMTokenUpdate,
    db: Session = Depends(get_db),
    current_user: SystemUser = Depends(get_current_active_user)
) -> FCMTokenResponse:
    """
    FCM token güncelle
    
    Args:
        user_id: Kullanıcı ID
        token_data: FCM token verisi
        db: Database session
        current_user: Mevcut kullanıcı
        
    Returns:
        FCMTokenResponse: Güncelleme sonucu
        
    Raises:
        HTTPException: Kullanıcı bulunamazsa veya yetki yoksa
    """
    try:
        # Yetki kontrolü: Kullanıcı sadece kendi token'ını güncelleyebilir (admin hariç)
        if current_user.id != user_id and not current_user.is_admin():
            logger.warning(
                f"⚠️ Yetkisiz FCM token güncelleme denemesi: "
                f"user={current_user.username}, target_user_id={user_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sadece kendi FCM token'ınızı güncelleyebilirsiniz"
            )
        
        # Kullanıcıyı bul
        user = db.query(SystemUser).filter(
            SystemUser.id == user_id,
            SystemUser.hotel_id == current_user.hotel_id
        ).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Kullanıcı bulunamadı"
            )
        
        # FCM token'ı güncelle
        user.fcm_token = token_data.fcm_token
        user.fcm_token_date = datetime.utcnow()
        
        db.commit()
        db.refresh(user)
        
        logger.info(f"✅ FCM token güncellendi: user={user.username}")
        
        return FCMTokenResponse(
            success=True,
            message="FCM token başarıyla güncellendi",
            fcm_token=user.fcm_token,
            updated_at=user.fcm_token_date
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ FCM token güncelleme hatası: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="FCM token güncellenirken bir hata oluştu"
        )


@router.delete(
    "/{user_id}/fcm-token",
    response_model=FCMTokenResponse,
    summary="Driver FCM token sil",
    description="""
    Driver'ın FCM token'ını siler (logout için).
    
    **Requirements:** 7.1, 7.2
    
    **Authentication:** Driver (kendi token'ını) veya Admin
    
    **İşlem:**
    - FCM token'ı veritabanından siler
    - Artık push notification almaz
    """
)
async def delete_fcm_token(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: SystemUser = Depends(get_current_active_user)
) -> FCMTokenResponse:
    """
    FCM token sil
    
    Args:
        user_id: Kullanıcı ID
        db: Database session
        current_user: Mevcut kullanıcı
        
    Returns:
        FCMTokenResponse: Silme sonucu
        
    Raises:
        HTTPException: Kullanıcı bulunamazsa veya yetki yoksa
    """
    try:
        # Yetki kontrolü: Kullanıcı sadece kendi token'ını silebilir (admin hariç)
        if current_user.id != user_id and not current_user.is_admin():
            logger.warning(
                f"⚠️ Yetkisiz FCM token silme denemesi: "
                f"user={current_user.username}, target_user_id={user_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sadece kendi FCM token'ınızı silebilirsiniz"
            )
        
        # Kullanıcıyı bul
        user = db.query(SystemUser).filter(
            SystemUser.id == user_id,
            SystemUser.hotel_id == current_user.hotel_id
        ).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Kullanıcı bulunamadı"
            )
        
        # FCM token'ı sil
        user.fcm_token = None
        user.fcm_token_date = None
        
        db.commit()
        
        logger.info(f"✅ FCM token silindi: user={user.username}")
        
        return FCMTokenResponse(
            success=True,
            message="FCM token başarıyla silindi",
            fcm_token=None,
            updated_at=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ FCM token silme hatası: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="FCM token silinirken bir hata oluştu"
        )


# =============================================================================
# User Management Endpoints (Görev 11.3'te implement edilecek)
# =============================================================================

@router.get(
    "",
    summary="Kullanıcıları listele",
    description="""
    Oteldeki tüm kullanıcıları listeler.
    
    **Requirements:** 9.4
    
    **Authentication:** Admin
    
    **Query Parameters:**
    - role: Rol filtresi (admin, driver)
    - is_active: Aktiflik filtresi (true, false)
    - skip: Pagination offset (default: 0)
    - limit: Pagination limit (default: 100)
    """
)
async def list_users(
    role: Optional[str] = None,
    is_active: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    hotel_id: int = Depends(get_user_hotel_id),
    current_user: SystemUser = Depends(require_admin)
):
    """
    Kullanıcıları listele
    
    Args:
        role: Rol filtresi (opsiyonel)
        is_active: Aktiflik filtresi (opsiyonel)
        skip: Pagination offset
        limit: Pagination limit
        db: Database session
        hotel_id: Otel ID
        current_user: Mevcut kullanıcı (admin)
        
    Returns:
        List[UserDetailResponse]: Kullanıcı listesi
    """
    try:
        from app.services.user_service import UserService
        
        logger.debug(
            f"📋 Kullanıcılar listeleniyor: hotel_id={hotel_id}, "
            f"role={role}, is_active={is_active}"
        )
        
        users = UserService.get_users(
            db=db,
            hotel_id=hotel_id,
            role=role,
            is_active=is_active,
            skip=skip,
            limit=limit
        )
        
        logger.debug(f"✅ {len(users)} kullanıcı bulundu")
        
        return users
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Kullanıcı listeleme hatası: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Kullanıcılar listelenirken bir hata oluştu"
        )


@router.get(
    "/{user_id}",
    summary="Kullanıcı detayını getir",
    description="""
    Kullanıcı detaylarını getirir.
    
    **Requirements:** 9.4
    
    **Authentication:** Admin
    """
)
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    hotel_id: int = Depends(get_user_hotel_id),
    current_user: SystemUser = Depends(require_admin)
):
    """
    Kullanıcı detayını getir
    
    Args:
        user_id: Kullanıcı ID
        db: Database session
        hotel_id: Otel ID
        current_user: Mevcut kullanıcı (admin)
        
    Returns:
        UserDetailResponse: Kullanıcı detayı
    """
    try:
        from app.services.user_service import UserService
        
        logger.debug(f"🔍 Kullanıcı getiriliyor: user_id={user_id}")
        
        user = UserService.get_user_by_id(
            db=db,
            user_id=user_id,
            hotel_id=hotel_id
        )
        
        logger.debug(f"✅ Kullanıcı bulundu: username={user.username}")
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Kullanıcı getirme hatası: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Kullanıcı getirilirken bir hata oluştu"
        )


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Yeni kullanıcı oluştur",
    description="""
    Yeni kullanıcı (driver veya admin) oluşturur.
    
    **Requirements:** 9.4
    
    **Authentication:** Admin
    
    **Validasyonlar:**
    - Username benzersiz olmalı
    - Şifre en az 8 karakter olmalı
    - Rol admin veya driver olmalı
    """
)
async def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: SystemUser = Depends(require_admin)
):
    """
    Yeni kullanıcı oluştur
    
    Args:
        user_data: Kullanıcı oluşturma verisi
        db: Database session
        current_user: Mevcut kullanıcı (admin)
        
    Returns:
        UserDetailResponse: Oluşturulan kullanıcı
    """
    try:
        from app.services.user_service import UserService
        
        logger.info(f"👤 Yeni kullanıcı oluşturuluyor: username={user_data.username}")
        
        new_user = UserService.create_user(
            db=db,
            user_data=user_data
        )
        
        logger.info(f"✅ Kullanıcı oluşturuldu: username={new_user.username}")
        
        return new_user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Kullanıcı oluşturma hatası: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Kullanıcı oluşturulurken bir hata oluştu"
        )


@router.put(
    "/{user_id}",
    summary="Kullanıcı güncelle",
    description="""
    Kullanıcı bilgilerini günceller.
    
    **Requirements:** 9.4
    
    **Authentication:** Admin
    
    **Güncellenebilir Alanlar:**
    - full_name
    - email
    - phone
    - is_active
    """
)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    hotel_id: int = Depends(get_user_hotel_id),
    current_user: SystemUser = Depends(require_admin)
):
    """
    Kullanıcı güncelle
    
    Args:
        user_id: Kullanıcı ID
        user_data: Güncelleme verisi
        db: Database session
        hotel_id: Otel ID
        current_user: Mevcut kullanıcı (admin)
        
    Returns:
        UserDetailResponse: Güncellenmiş kullanıcı
    """
    try:
        from app.services.user_service import UserService
        
        logger.info(f"✏️ Kullanıcı güncelleniyor: user_id={user_id}")
        
        updated_user = UserService.update_user(
            db=db,
            user_id=user_id,
            hotel_id=hotel_id,
            user_data=user_data
        )
        
        logger.info(f"✅ Kullanıcı güncellendi: username={updated_user.username}")
        
        return updated_user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Kullanıcı güncelleme hatası: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Kullanıcı güncellenirken bir hata oluştu"
        )


@router.delete(
    "/{user_id}",
    summary="Kullanıcı sil",
    description="""
    Kullanıcıyı siler (soft delete - is_active=False).
    
    **Requirements:** 9.4
    
    **Authentication:** Admin
    
    **Not:** Bu işlem soft delete'dir. Kullanıcı veritabanından silinmez,
    sadece is_active=False olarak işaretlenir ve FCM token'ı temizlenir.
    """
)
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    hotel_id: int = Depends(get_user_hotel_id),
    current_user: SystemUser = Depends(require_admin)
):
    """
    Kullanıcı sil (soft delete)
    
    Args:
        user_id: Kullanıcı ID
        db: Database session
        hotel_id: Otel ID
        current_user: Mevcut kullanıcı (admin)
        
    Returns:
        UserDetailResponse: Silinen kullanıcı
    """
    try:
        from app.services.user_service import UserService
        
        logger.info(f"🗑️ Kullanıcı siliniyor: user_id={user_id}")
        
        deleted_user = UserService.delete_user(
            db=db,
            user_id=user_id,
            hotel_id=hotel_id
        )
        
        logger.info(f"✅ Kullanıcı silindi: username={deleted_user.username}")
        
        return deleted_user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Kullanıcı silme hatası: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Kullanıcı silinirken bir hata oluştu"
        )
