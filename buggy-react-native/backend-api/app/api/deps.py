"""
API Dependencies
Authentication ve authorization için dependency fonksiyonları
"""
from typing import Optional, List
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import logging

from app.database import get_db
from app.core.security import verify_token, extract_user_from_token
from app.models.user import SystemUser
from app.models.enums import UserRole

logger = logging.getLogger(__name__)

# HTTP Bearer token scheme
security = HTTPBearer()


# =============================================================================
# Authentication Dependencies
# =============================================================================

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> SystemUser:
    """
    JWT token'dan mevcut kullanıcıyı al
    
    Args:
        credentials: HTTP Authorization header'dan gelen token
        db: Database session
        
    Returns:
        SystemUser: Mevcut kullanıcı
        
    Raises:
        HTTPException: Token geçersiz veya kullanıcı bulunamadı
        
    Example:
        @app.get("/profile")
        async def get_profile(current_user: SystemUser = Depends(get_current_user)):
            return {"username": current_user.username}
    """
    # Token'ı al
    token = credentials.credentials
    
    # Token'ı doğrula ve kullanıcı bilgilerini çıkar
    try:
        user_info = extract_user_from_token(token)
        
        if not user_info:
            logger.warning("⚠️ Token'dan kullanıcı bilgisi çıkarılamadı")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Geçersiz kimlik doğrulama bilgileri",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user_id = user_info["user_id"]
        
    except Exception as e:
        logger.warning(f"⚠️ Token doğrulama hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Geçersiz veya süresi dolmuş token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Kullanıcıyı veritabanından al
    try:
        user = db.query(SystemUser).filter(
            SystemUser.id == user_id,
            SystemUser.is_active == True
        ).first()
        
        if not user:
            logger.warning(f"⚠️ Kullanıcı bulunamadı veya aktif değil: user_id={user_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Kullanıcı bulunamadı veya hesap aktif değil",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        logger.debug(f"✅ Kullanıcı doğrulandı: {user.username} (role={user.role})")
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Kullanıcı sorgulama hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Kimlik doğrulama sırasında bir hata oluştu"
        )


async def get_current_active_user(
    current_user: SystemUser = Depends(get_current_user)
) -> SystemUser:
    """
    Aktif kullanıcıyı al (is_active kontrolü)
    
    Args:
        current_user: Mevcut kullanıcı
        
    Returns:
        SystemUser: Aktif kullanıcı
        
    Raises:
        HTTPException: Kullanıcı aktif değil
    """
    if not current_user.is_active:
        logger.warning(f"⚠️ Aktif olmayan kullanıcı erişim denemesi: {current_user.username}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Hesabınız aktif değil"
        )
    
    return current_user


# =============================================================================
# Authorization Dependencies (Role-Based)
# =============================================================================

class RoleChecker:
    """
    Rol tabanlı yetkilendirme için dependency class
    
    Example:
        require_admin = RoleChecker([UserRole.ADMIN])
        
        @app.post("/locations")
        async def create_location(
            current_user: SystemUser = Depends(require_admin)
        ):
            # Sadece admin erişebilir
            pass
    """
    
    def __init__(self, allowed_roles: List[UserRole]):
        """
        Args:
            allowed_roles: İzin verilen roller listesi
        """
        self.allowed_roles = allowed_roles
    
    async def __call__(
        self,
        current_user: SystemUser = Depends(get_current_active_user)
    ) -> SystemUser:
        """
        Kullanıcının rolünü kontrol et
        
        Args:
            current_user: Mevcut kullanıcı
            
        Returns:
            SystemUser: Yetkili kullanıcı
            
        Raises:
            HTTPException: Kullanıcı yetkili değil
        """
        # Kullanıcının rolünü kontrol et
        user_role = UserRole(current_user.role)
        
        if user_role not in self.allowed_roles:
            logger.warning(
                f"⚠️ Yetkisiz erişim denemesi: user={current_user.username}, "
                f"role={user_role.value}, required={[r.value for r in self.allowed_roles]}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Bu işlem için {', '.join([r.value for r in self.allowed_roles])} yetkisi gereklidir"
            )
        
        logger.debug(f"✅ Yetki kontrolü başarılı: user={current_user.username}, role={user_role.value}")
        return current_user


# =============================================================================
# Pre-configured Role Dependencies
# =============================================================================

# Sadece admin erişebilir
require_admin = RoleChecker([UserRole.ADMIN])

# Sadece driver erişebilir
require_driver = RoleChecker([UserRole.DRIVER])

# Admin veya driver erişebilir
require_admin_or_driver = RoleChecker([UserRole.ADMIN, UserRole.DRIVER])


# =============================================================================
# Optional Authentication
# =============================================================================

async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: Session = Depends(get_db)
) -> Optional[SystemUser]:
    """
    Opsiyonel authentication (token yoksa None döner)
    Public endpoint'lerde kullanılır
    
    Args:
        credentials: HTTP Authorization header (opsiyonel)
        db: Database session
        
    Returns:
        Optional[SystemUser]: Kullanıcı (token varsa) veya None
        
    Example:
        @app.get("/locations")
        async def get_locations(
            current_user: Optional[SystemUser] = Depends(get_current_user_optional)
        ):
            # Token varsa kullanıcıya özel, yoksa genel liste döner
            if current_user:
                return get_user_locations(current_user.hotel_id)
            return get_public_locations()
    """
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        user_info = extract_user_from_token(token)
        
        if not user_info:
            return None
        
        user = db.query(SystemUser).filter(
            SystemUser.id == user_info["user_id"],
            SystemUser.is_active == True
        ).first()
        
        return user
        
    except Exception as e:
        logger.debug(f"Opsiyonel auth hatası (normal): {e}")
        return None


# =============================================================================
# Hotel Context Dependency
# =============================================================================

async def get_user_hotel_id(
    current_user: SystemUser = Depends(get_current_active_user)
) -> int:
    """
    Kullanıcının otel ID'sini al
    
    Args:
        current_user: Mevcut kullanıcı
        
    Returns:
        int: Otel ID
        
    Example:
        @app.get("/requests")
        async def get_requests(
            hotel_id: int = Depends(get_user_hotel_id),
            db: Session = Depends(get_db)
        ):
            return db.query(Request).filter_by(hotel_id=hotel_id).all()
    """
    return current_user.hotel_id


# =============================================================================
# Custom Authorization Helpers
# =============================================================================

def check_resource_access(
    user: SystemUser,
    resource_hotel_id: int,
    resource_name: str = "kaynak"
) -> None:
    """
    Kullanıcının bir kaynağa erişim yetkisi var mı kontrol et
    
    Args:
        user: Mevcut kullanıcı
        resource_hotel_id: Kaynağın otel ID'si
        resource_name: Kaynak adı (hata mesajı için)
        
    Raises:
        HTTPException: Kullanıcı kaynağa erişemez
        
    Example:
        location = db.query(Location).get(location_id)
        check_resource_access(current_user, location.hotel_id, "lokasyon")
    """
    # Admin her şeye erişebilir (kendi otelinde)
    # Driver sadece kendi otelindeki kaynaklara erişebilir
    
    if user.hotel_id != resource_hotel_id:
        logger.warning(
            f"⚠️ Otel dışı erişim denemesi: user={user.username}, "
            f"user_hotel={user.hotel_id}, resource_hotel={resource_hotel_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Bu {resource_name} erişim yetkiniz yok"
        )


def check_driver_shuttle_access(
    user: SystemUser,
    shuttle_id: int,
    db: Session
) -> None:
    """
    Driver'ın bir shuttle'a erişim yetkisi var mı kontrol et
    
    Args:
        user: Mevcut kullanıcı (driver olmalı)
        shuttle_id: Shuttle ID
        db: Database session
        
    Raises:
        HTTPException: Driver bu shuttle'a atanmamış
    """
    from app.models.shuttle_driver import ShuttleDriver
    
    # Admin her shuttle'a erişebilir
    if user.is_admin():
        return
    
    # Driver sadece atandığı shuttle'lara erişebilir
    assignment = db.query(ShuttleDriver).filter(
        ShuttleDriver.driver_id == user.id,
        ShuttleDriver.shuttle_id == shuttle_id,
        ShuttleDriver.is_active == True
    ).first()
    
    if not assignment:
        logger.warning(
            f"⚠️ Atanmamış shuttle erişim denemesi: driver={user.username}, shuttle_id={shuttle_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu shuttle'a erişim yetkiniz yok"
        )
