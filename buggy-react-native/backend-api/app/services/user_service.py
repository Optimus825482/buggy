"""
User Service Layer
Kullanıcı yönetimi için business logic
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
from fastapi import HTTPException, status
import logging

from app.models.user import SystemUser
from app.models.shuttle_driver import ShuttleDriver
from app.models.enums import UserRole
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import hash_password

logger = logging.getLogger(__name__)


class UserService:
    """
    User işlemleri için servis katmanı
    Requirements: 9.4
    """
    
    @staticmethod
    def create_user(
        db: Session,
        user_data: UserCreate
    ) -> SystemUser:
        """
        Yeni kullanıcı oluştur
        Requirements: 9.4
        
        Args:
            db: Database session
            user_data: Kullanıcı oluşturma verisi
            
        Returns:
            SystemUser: Oluşturulan kullanıcı
            
        Raises:
            HTTPException: Username zaten varsa
        """
        try:
            # Username kontrolü
            existing_user = db.query(SystemUser).filter(
                SystemUser.username == user_data.username
            ).first()
            
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"'{user_data.username}' kullanıcı adı zaten kullanılıyor"
                )
            
            # Şifreyi hashle
            password_hash = hash_password(user_data.password)
            
            # Kullanıcı oluştur
            new_user = SystemUser(
                hotel_id=user_data.hotel_id,
                username=user_data.username,
                password_hash=password_hash,
                full_name=user_data.full_name,
                email=user_data.email,
                phone=user_data.phone,
                role=user_data.role,
                is_active=True,
                must_change_password=False
            )
            
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            
            logger.info(f"✅ Kullanıcı oluşturuldu: username={new_user.username}, role={new_user.role}")
            
            return new_user
            
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Kullanıcı oluşturma hatası: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Kullanıcı oluşturulurken hata: {str(e)}"
            )
    
    @staticmethod
    def update_user(
        db: Session,
        user_id: int,
        hotel_id: int,
        user_data: UserUpdate
    ) -> SystemUser:
        """
        Kullanıcı bilgilerini güncelle
        Requirements: 9.4
        
        Args:
            db: Database session
            user_id: Kullanıcı ID
            hotel_id: Otel ID
            user_data: Güncelleme verisi
            
        Returns:
            SystemUser: Güncellenmiş kullanıcı
            
        Raises:
            HTTPException: Kullanıcı bulunamazsa
        """
        try:
            # Kullanıcıyı bul
            user = db.query(SystemUser).filter(
                and_(
                    SystemUser.id == user_id,
                    SystemUser.hotel_id == hotel_id
                )
            ).first()
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Kullanıcı bulunamadı"
                )
            
            # Güncelleme verilerini uygula
            if user_data.full_name is not None:
                user.full_name = user_data.full_name
            
            if user_data.email is not None:
                user.email = user_data.email
            
            if user_data.phone is not None:
                user.phone = user_data.phone
            
            if user_data.is_active is not None:
                user.is_active = user_data.is_active
            
            db.commit()
            db.refresh(user)
            
            logger.info(f"✅ Kullanıcı güncellendi: username={user.username}")
            
            return user
            
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Kullanıcı güncelleme hatası: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Kullanıcı güncellenirken hata: {str(e)}"
            )
    
    @staticmethod
    def delete_user(
        db: Session,
        user_id: int,
        hotel_id: int
    ) -> SystemUser:
        """
        Kullanıcıyı sil (soft delete - is_active=False)
        Requirements: 9.4
        
        Args:
            db: Database session
            user_id: Kullanıcı ID
            hotel_id: Otel ID
            
        Returns:
            SystemUser: Silinen kullanıcı
            
        Raises:
            HTTPException: Kullanıcı bulunamazsa
        """
        try:
            # Kullanıcıyı bul
            user = db.query(SystemUser).filter(
                and_(
                    SystemUser.id == user_id,
                    SystemUser.hotel_id == hotel_id
                )
            ).first()
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Kullanıcı bulunamadı"
                )
            
            # Soft delete
            user.is_active = False
            
            # FCM token'ı temizle
            user.fcm_token = None
            user.fcm_token_date = None
            
            db.commit()
            db.refresh(user)
            
            logger.info(f"✅ Kullanıcı silindi (soft delete): username={user.username}")
            
            return user
            
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Kullanıcı silme hatası: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Kullanıcı silinirken hata: {str(e)}"
            )
    
    @staticmethod
    def get_user_by_id(
        db: Session,
        user_id: int,
        hotel_id: int
    ) -> SystemUser:
        """
        Kullanıcıyı ID ile getir
        Requirements: 9.4
        
        Args:
            db: Database session
            user_id: Kullanıcı ID
            hotel_id: Otel ID
            
        Returns:
            SystemUser: Kullanıcı
            
        Raises:
            HTTPException: Kullanıcı bulunamazsa
        """
        user = db.query(SystemUser).filter(
            and_(
                SystemUser.id == user_id,
                SystemUser.hotel_id == hotel_id
            )
        ).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Kullanıcı bulunamadı"
            )
        
        return user
    
    @staticmethod
    def get_users(
        db: Session,
        hotel_id: int,
        role: Optional[str] = None,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[SystemUser]:
        """
        Kullanıcıları listele
        Requirements: 9.4
        
        Args:
            db: Database session
            hotel_id: Otel ID
            role: Rol filtresi (opsiyonel)
            is_active: Aktiflik filtresi (opsiyonel)
            skip: Pagination offset
            limit: Pagination limit
            
        Returns:
            List[SystemUser]: Kullanıcı listesi
        """
        query = db.query(SystemUser).filter(
            SystemUser.hotel_id == hotel_id
        )
        
        # Filtreleri uygula
        if role:
            query = query.filter(SystemUser.role == role)
        
        if is_active is not None:
            query = query.filter(SystemUser.is_active == is_active)
        
        # Sıralama ve pagination
        users = query.order_by(SystemUser.created_at.desc()).offset(skip).limit(limit).all()
        
        return users
    
    @staticmethod
    def assign_driver_to_shuttle(
        db: Session,
        driver_id: int,
        shuttle_id: int,
        hotel_id: int,
        is_primary: bool = False
    ) -> ShuttleDriver:
        """
        Driver'ı shuttle'a ata
        Requirements: 9.4
        
        Args:
            db: Database session
            driver_id: Driver ID
            shuttle_id: Shuttle ID
            hotel_id: Otel ID
            is_primary: Birincil sürücü mü?
            
        Returns:
            ShuttleDriver: Atama kaydı
            
        Raises:
            HTTPException: Driver veya shuttle bulunamazsa
        """
        try:
            # Driver kontrolü
            driver = db.query(SystemUser).filter(
                and_(
                    SystemUser.id == driver_id,
                    SystemUser.hotel_id == hotel_id,
                    SystemUser.role == UserRole.DRIVER.value
                )
            ).first()
            
            if not driver:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Driver bulunamadı"
                )
            
            # Shuttle kontrolü
            from app.models.shuttle import Shuttle
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
            
            # Mevcut atama var mı kontrol et
            existing_assignment = db.query(ShuttleDriver).filter(
                and_(
                    ShuttleDriver.driver_id == driver_id,
                    ShuttleDriver.shuttle_id == shuttle_id
                )
            ).first()
            
            if existing_assignment:
                # Mevcut atamayı güncelle
                existing_assignment.is_active = True
                existing_assignment.is_primary = is_primary
                db.commit()
                db.refresh(existing_assignment)
                
                logger.info(
                    f"✅ Driver ataması güncellendi: driver={driver.username}, "
                    f"shuttle={shuttle.code}"
                )
                
                return existing_assignment
            
            # Yeni atama oluştur
            assignment = ShuttleDriver(
                driver_id=driver_id,
                shuttle_id=shuttle_id,
                is_primary=is_primary,
                is_active=True
            )
            
            db.add(assignment)
            db.commit()
            db.refresh(assignment)
            
            logger.info(
                f"✅ Driver shuttle'a atandı: driver={driver.username}, "
                f"shuttle={shuttle.code}"
            )
            
            return assignment
            
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Driver atama hatası: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Driver atanırken hata: {str(e)}"
            )
