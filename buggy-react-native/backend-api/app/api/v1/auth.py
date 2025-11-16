"""
Authentication Endpoints
Login, logout, token refresh ve şifre değiştirme
"""
from datetime import datetime
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging

from app.database import get_db
from app.models.user import SystemUser
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    TokenResponse,
    RefreshTokenRequest,
    ChangePasswordRequest,
    UserResponse,
    MessageResponse
)
from app.core.security import (
    verify_password,
    hash_password,
    create_token_pair,
    verify_token,
    validate_password_strength
)
from app.api.deps import get_current_active_user

logger = logging.getLogger(__name__)

# Router oluştur
router = APIRouter()


# =============================================================================
# Login Endpoint
# =============================================================================

@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="Kullanıcı girişi",
    description="Kullanıcı adı ve şifre ile giriş yap, JWT token al",
    responses={
        200: {
            "description": "Giriş başarılı",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
                        "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
                        "token_type": "bearer",
                        "user": {
                            "id": 1,
                            "username": "admin1",
                            "full_name": "Admin User",
                            "role": "admin",
                            "hotel_id": 1
                        }
                    }
                }
            }
        },
        401: {"description": "Kullanıcı adı veya şifre hatalı"},
        403: {"description": "Hesap aktif değil"}
    }
)
async def login(
    credentials: LoginRequest,
    db: Session = Depends(get_db)
) -> LoginResponse:
    """
    Kullanıcı girişi
    
    - **username**: Kullanıcı adı
    - **password**: Şifre
    
    Returns:
        LoginResponse: Access token, refresh token ve kullanıcı bilgileri
    """
    try:
        # Kullanıcıyı bul
        user = db.query(SystemUser).filter(
            SystemUser.username == credentials.username.lower()
        ).first()
        
        # Kullanıcı bulunamadı veya şifre yanlış
        if not user or not verify_password(credentials.password, user.password_hash):
            logger.warning(f"⚠️ Başarısız giriş denemesi: username={credentials.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Kullanıcı adı veya şifre hatalı",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Hesap aktif mi kontrol et
        if not user.is_active:
            logger.warning(f"⚠️ Aktif olmayan hesap giriş denemesi: username={user.username}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Hesabınız aktif değil. Lütfen yöneticinizle iletişime geçin"
            )
        
        # Token çifti oluştur
        token_data = {
            "sub": str(user.id),
            "username": user.username,
            "role": user.role,
            "hotel_id": user.hotel_id
        }
        tokens = create_token_pair(token_data)
        
        # Son giriş zamanını güncelle
        user.last_login = datetime.utcnow()
        db.commit()
        
        logger.info(f"✅ Başarılı giriş: username={user.username}, role={user.role}")
        
        # Response oluştur
        return LoginResponse(
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            token_type=tokens["token_type"],
            user=UserResponse.from_orm(user)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Login hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Giriş işlemi sırasında bir hata oluştu"
        )


# =============================================================================
# Token Refresh Endpoint
# =============================================================================

@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Token yenileme",
    description="Refresh token ile yeni access token al",
    responses={
        200: {
            "description": "Token yenileme başarılı",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
                        "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
                        "token_type": "bearer"
                    }
                }
            }
        },
        401: {"description": "Refresh token geçersiz veya süresi dolmuş"},
        404: {"description": "Kullanıcı bulunamadı"}
    }
)
async def refresh_token(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db)
) -> TokenResponse:
    """
    Token yenileme
    
    - **refresh_token**: JWT refresh token
    
    Returns:
        TokenResponse: Yeni access token ve refresh token
    """
    try:
        # Refresh token'ı doğrula
        payload = verify_token(request.refresh_token, token_type="refresh")
        
        if not payload:
            logger.warning("⚠️ Geçersiz refresh token")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Geçersiz veya süresi dolmuş refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Kullanıcı ID'sini al
        user_id = int(payload.get("sub"))
        
        # Kullanıcıyı bul
        user = db.query(SystemUser).filter(
            SystemUser.id == user_id,
            SystemUser.is_active == True
        ).first()
        
        if not user:
            logger.warning(f"⚠️ Token yenileme için kullanıcı bulunamadı: user_id={user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Kullanıcı bulunamadı veya hesap aktif değil"
            )
        
        # Yeni token çifti oluştur
        token_data = {
            "sub": str(user.id),
            "username": user.username,
            "role": user.role,
            "hotel_id": user.hotel_id
        }
        tokens = create_token_pair(token_data)
        
        logger.info(f"✅ Token yenilendi: username={user.username}")
        
        return TokenResponse(
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            token_type=tokens["token_type"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Token yenileme hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token yenileme sırasında bir hata oluştu"
        )


# =============================================================================
# Logout Endpoint
# =============================================================================

@router.post(
    "/logout",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Çıkış yap",
    description="Kullanıcı çıkışı (client-side token silme)",
    responses={
        200: {
            "description": "Çıkış başarılı",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Başarıyla çıkış yapıldı"
                    }
                }
            }
        },
        401: {"description": "Kimlik doğrulama gerekli"}
    }
)
async def logout(
    current_user: SystemUser = Depends(get_current_active_user)
) -> MessageResponse:
    """
    Çıkış yap
    
    Not: JWT token'lar stateless olduğu için server-side invalidation yapılmaz.
    Client, token'ları local storage'dan silmelidir.
    
    Returns:
        MessageResponse: Başarı mesajı
    """
    try:
        logger.info(f"✅ Çıkış yapıldı: username={current_user.username}")
        
        return MessageResponse(
            message="Başarıyla çıkış yapıldı"
        )
        
    except Exception as e:
        logger.error(f"❌ Logout hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Çıkış işlemi sırasında bir hata oluştu"
        )


# =============================================================================
# Change Password Endpoint
# =============================================================================

@router.post(
    "/change-password",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Şifre değiştir",
    description="Mevcut kullanıcının şifresini değiştir",
    responses={
        200: {
            "description": "Şifre değiştirildi",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Şifreniz başarıyla değiştirildi"
                    }
                }
            }
        },
        400: {"description": "Şifre güvenlik kurallarına uymuyor"},
        401: {"description": "Mevcut şifre yanlış"}
    }
)
async def change_password(
    request: ChangePasswordRequest,
    current_user: SystemUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> MessageResponse:
    """
    Şifre değiştir
    
    - **current_password**: Mevcut şifre
    - **new_password**: Yeni şifre (en az 8 karakter, harf ve rakam içermeli)
    - **confirm_password**: Yeni şifre tekrar
    
    Returns:
        MessageResponse: Başarı mesajı
    """
    try:
        # Mevcut şifreyi doğrula
        if not verify_password(request.current_password, current_user.password_hash):
            logger.warning(f"⚠️ Yanlış mevcut şifre: username={current_user.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Mevcut şifre yanlış"
            )
        
        # Yeni şifre güvenlik kontrolü (ekstra kontrol)
        is_valid, error_message = validate_password_strength(request.new_password)
        if not is_valid:
            logger.warning(f"⚠️ Zayıf şifre denemesi: username={current_user.username}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_message
            )
        
        # Yeni şifre mevcut şifre ile aynı olmamalı
        if verify_password(request.new_password, current_user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Yeni şifre mevcut şifre ile aynı olamaz"
            )
        
        # Şifreyi hashle ve güncelle
        current_user.password_hash = hash_password(request.new_password)
        current_user.must_change_password = False  # Şifre değiştirildi flag'ini kaldır
        current_user.updated_at = datetime.utcnow()
        
        db.commit()
        
        logger.info(f"✅ Şifre değiştirildi: username={current_user.username}")
        
        return MessageResponse(
            message="Şifreniz başarıyla değiştirildi"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Şifre değiştirme hatası: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Şifre değiştirme sırasında bir hata oluştu"
        )


# =============================================================================
# Current User Info Endpoint
# =============================================================================

@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Mevcut kullanıcı bilgileri",
    description="Giriş yapmış kullanıcının bilgilerini getir",
    responses={
        200: {
            "description": "Kullanıcı bilgileri",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "username": "admin1",
                        "full_name": "Admin User",
                        "email": "admin@hotel.com",
                        "role": "admin",
                        "hotel_id": 1,
                        "is_active": True
                    }
                }
            }
        },
        401: {"description": "Kimlik doğrulama gerekli"}
    }
)
async def get_current_user_info(
    current_user: SystemUser = Depends(get_current_active_user)
) -> UserResponse:
    """
    Mevcut kullanıcı bilgileri
    
    Returns:
        UserResponse: Kullanıcı bilgileri
    """
    try:
        logger.debug(f"📋 Kullanıcı bilgileri istendi: username={current_user.username}")
        
        return UserResponse.from_orm(current_user)
        
    except Exception as e:
        logger.error(f"❌ Kullanıcı bilgisi alma hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Kullanıcı bilgileri alınırken bir hata oluştu"
        )
