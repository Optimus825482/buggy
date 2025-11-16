"""
Security utilities
JWT token yönetimi ve password hashing
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError, DecodeError
from passlib.context import CryptContext
import logging

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Password hashing context (bcrypt)
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=settings.BCRYPT_ROUNDS
)


# =============================================================================
# JWT Token Utilities
# =============================================================================

def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    JWT access token oluştur
    
    Args:
        data: Token payload'ına eklenecek veriler (user_id, username, role, hotel_id)
        expires_delta: Token geçerlilik süresi (None ise default kullanılır)
        
    Returns:
        str: JWT access token
        
    Example:
        token = create_access_token(
            data={
                "sub": str(user.id),
                "username": user.username,
                "role": user.role,
                "hotel_id": user.hotel_id
            }
        )
    """
    try:
        to_encode = data.copy()
        
        # Expiration time
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
            )
        
        # Token payload
        to_encode.update({
            "exp": expire,
            "type": "access",
            "iat": datetime.utcnow()
        })
        
        # JWT encode
        encoded_jwt = jwt.encode(
            to_encode,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )
        
        logger.debug(f"✅ Access token oluşturuldu: user={data.get('username')}")
        return encoded_jwt
        
    except Exception as e:
        logger.error(f"❌ Access token oluşturma hatası: {e}")
        raise


def create_refresh_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    JWT refresh token oluştur
    
    Args:
        data: Token payload'ına eklenecek veriler (sadece user_id)
        expires_delta: Token geçerlilik süresi (None ise default kullanılır)
        
    Returns:
        str: JWT refresh token
        
    Example:
        token = create_refresh_token(
            data={"sub": str(user.id)}
        )
    """
    try:
        to_encode = data.copy()
        
        # Expiration time
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
            )
        
        # Token payload (minimal data for refresh token)
        to_encode.update({
            "exp": expire,
            "type": "refresh",
            "iat": datetime.utcnow()
        })
        
        # JWT encode
        encoded_jwt = jwt.encode(
            to_encode,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )
        
        logger.debug(f"✅ Refresh token oluşturuldu: user_id={data.get('sub')}")
        return encoded_jwt
        
    except Exception as e:
        logger.error(f"❌ Refresh token oluşturma hatası: {e}")
        raise


def verify_token(token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
    """
    JWT token'ı doğrula ve payload'ı döndür
    
    Args:
        token: JWT token string
        token_type: Token tipi ("access" veya "refresh")
        
    Returns:
        Optional[Dict]: Token payload (geçersizse None)
        
    Raises:
        JWTError: Token geçersiz veya süresi dolmuş
        
    Example:
        payload = verify_token(token, token_type="access")
        if payload:
            user_id = payload.get("sub")
            username = payload.get("username")
    """
    try:
        # JWT decode
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        # Token type kontrolü
        if payload.get("type") != token_type:
            logger.warning(f"⚠️ Token type uyuşmazlığı: beklenen={token_type}, gelen={payload.get('type')}")
            return None
        
        # Expiration kontrolü (jwt.decode otomatik yapar ama double-check)
        exp = payload.get("exp")
        if exp and datetime.fromtimestamp(exp) < datetime.utcnow():
            logger.warning("⚠️ Token süresi dolmuş")
            return None
        
        logger.debug(f"✅ Token doğrulandı: type={token_type}, user={payload.get('username', payload.get('sub'))}")
        return payload
        
    except ExpiredSignatureError:
        logger.warning("⚠️ Token süresi dolmuş (ExpiredSignatureError)")
        raise
    except DecodeError as e:
        logger.warning(f"⚠️ Token decode hatası: {e}")
        raise
    except InvalidTokenError as e:
        logger.warning(f"⚠️ Token doğrulama hatası: {e}")
        raise
    except Exception as e:
        logger.error(f"❌ Beklenmeyen token doğrulama hatası: {e}")
        raise


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """
    JWT token'ı decode et (doğrulama yapmadan)
    Debug ve test amaçlı kullanılır
    
    Args:
        token: JWT token string
        
    Returns:
        Optional[Dict]: Token payload (decode edilemezse None)
    """
    try:
        # Doğrulama yapmadan decode et
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            options={"verify_signature": False, "verify_exp": False}
        )
        return payload
    except Exception as e:
        logger.error(f"❌ Token decode hatası: {e}")
        return None


def extract_user_from_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Token'dan kullanıcı bilgilerini çıkar
    
    Args:
        token: JWT access token
        
    Returns:
        Optional[Dict]: Kullanıcı bilgileri (user_id, username, role, hotel_id)
        
    Example:
        user_info = extract_user_from_token(token)
        if user_info:
            user_id = user_info["user_id"]
            username = user_info["username"]
            role = user_info["role"]
            hotel_id = user_info["hotel_id"]
    """
    try:
        payload = verify_token(token, token_type="access")
        
        if not payload:
            return None
        
        # Kullanıcı bilgilerini çıkar
        user_info = {
            "user_id": int(payload.get("sub")),
            "username": payload.get("username"),
            "role": payload.get("role"),
            "hotel_id": payload.get("hotel_id")
        }
        
        # Zorunlu alanları kontrol et
        if not all([user_info["user_id"], user_info["username"], user_info["role"]]):
            logger.warning("⚠️ Token'da eksik kullanıcı bilgisi")
            return None
        
        return user_info
        
    except Exception as e:
        logger.error(f"❌ Token'dan kullanıcı bilgisi çıkarma hatası: {e}")
        return None


# =============================================================================
# Password Hashing Utilities
# =============================================================================

def hash_password(password: str) -> str:
    """
    Şifreyi bcrypt ile hashle
    
    Args:
        password: Plain text şifre
        
    Returns:
        str: Hashlenmiş şifre
        
    Example:
        hashed = hash_password("mypassword123")
        # Veritabanına hashed değeri kaydet
    """
    try:
        hashed = pwd_context.hash(password)
        logger.debug("✅ Şifre hashlendi")
        return hashed
    except Exception as e:
        logger.error(f"❌ Şifre hashleme hatası: {e}")
        raise


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Plain text şifreyi hashlenmiş şifre ile karşılaştır
    
    Args:
        plain_password: Kullanıcının girdiği şifre
        hashed_password: Veritabanındaki hashlenmiş şifre
        
    Returns:
        bool: Şifreler eşleşiyor mu?
        
    Example:
        if verify_password(input_password, user.password_hash):
            # Şifre doğru
            login_user(user)
    """
    try:
        is_valid = pwd_context.verify(plain_password, hashed_password)
        
        if is_valid:
            logger.debug("✅ Şifre doğrulandı")
        else:
            logger.debug("⚠️ Şifre yanlış")
        
        return is_valid
        
    except Exception as e:
        logger.error(f"❌ Şifre doğrulama hatası: {e}")
        return False


def validate_password_strength(password: str) -> tuple[bool, Optional[str]]:
    """
    Şifre güvenliğini kontrol et (opsiyonel)
    
    Args:
        password: Kontrol edilecek şifre
        
    Returns:
        tuple: (geçerli_mi, hata_mesajı)
        
    Example:
        is_valid, error = validate_password_strength("weak")
        if not is_valid:
            raise ValueError(error)
    """
    # Minimum uzunluk
    if len(password) < 8:
        return False, "Şifre en az 8 karakter olmalıdır"
    
    # Maksimum uzunluk
    if len(password) > 128:
        return False, "Şifre en fazla 128 karakter olabilir"
    
    # En az bir harf içermeli
    if not any(c.isalpha() for c in password):
        return False, "Şifre en az bir harf içermelidir"
    
    # En az bir rakam içermeli
    if not any(c.isdigit() for c in password):
        return False, "Şifre en az bir rakam içermelidir"
    
    # Yaygın şifreler kontrolü (opsiyonel)
    common_passwords = ["password", "12345678", "qwerty", "abc123"]
    if password.lower() in common_passwords:
        return False, "Bu şifre çok yaygın, daha güçlü bir şifre seçin"
    
    return True, None


# =============================================================================
# Token Helper Functions
# =============================================================================

def create_token_pair(user_data: Dict[str, Any]) -> Dict[str, str]:
    """
    Access ve refresh token çifti oluştur
    
    Args:
        user_data: Kullanıcı bilgileri (user_id, username, role, hotel_id)
        
    Returns:
        Dict: {"access_token": "...", "refresh_token": "...", "token_type": "bearer"}
        
    Example:
        tokens = create_token_pair({
            "sub": str(user.id),
            "username": user.username,
            "role": user.role,
            "hotel_id": user.hotel_id
        })
    """
    try:
        # Access token (tüm bilgiler)
        access_token = create_access_token(data=user_data)
        
        # Refresh token (sadece user_id)
        refresh_token = create_refresh_token(
            data={"sub": user_data.get("sub")}
        )
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
        
    except Exception as e:
        logger.error(f"❌ Token çifti oluşturma hatası: {e}")
        raise


def get_token_expiry_info(token: str) -> Optional[Dict[str, Any]]:
    """
    Token'ın süre bilgilerini döndür
    
    Args:
        token: JWT token
        
    Returns:
        Optional[Dict]: {"expires_at": datetime, "expires_in_seconds": int, "is_expired": bool}
    """
    try:
        payload = decode_token(token)
        if not payload:
            return None
        
        exp_timestamp = payload.get("exp")
        if not exp_timestamp:
            return None
        
        expires_at = datetime.fromtimestamp(exp_timestamp)
        now = datetime.utcnow()
        expires_in_seconds = int((expires_at - now).total_seconds())
        is_expired = expires_in_seconds <= 0
        
        return {
            "expires_at": expires_at,
            "expires_in_seconds": max(0, expires_in_seconds),
            "is_expired": is_expired
        }
        
    except Exception as e:
        logger.error(f"❌ Token süre bilgisi alma hatası: {e}")
        return None
