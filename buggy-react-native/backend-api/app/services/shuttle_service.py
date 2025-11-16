"""
Shuttle Service
Shuttle yönetimi için business logic
"""
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from typing import Optional, List
from fastapi import HTTPException, status
from datetime import datetime

from app.models.shuttle import Shuttle
from app.models.shuttle_driver import ShuttleDriver
from app.models.user import SystemUser
from app.models.enums import ShuttleStatus, UserRole
from app.schemas.shuttle import ShuttleCreate, ShuttleUpdate, ShuttleStatusUpdate


class ShuttleService:
    """Shuttle business logic"""
    
    @staticmethod
    def create_shuttle(db: Session, shuttle_data: ShuttleCreate) -> Shuttle:
        """
        Yeni shuttle oluştur
        
        Args:
            db: Database session
            shuttle_data: Shuttle oluşturma verisi
            
        Returns:
            Shuttle: Oluşturulan shuttle
            
        Raises:
            HTTPException: Hata durumunda
        """
        try:
            # Yeni shuttle oluştur
            shuttle = Shuttle(
                hotel_id=shuttle_data.hotel_id,
                code=shuttle_data.code.upper(),
                model=shuttle_data.model,
                license_plate=shuttle_data.license_plate,
                icon=shuttle_data.icon,
                current_location_id=shuttle_data.current_location_id,
                status=shuttle_data.status.value
            )
            
            db.add(shuttle)
            db.commit()
            db.refresh(shuttle)
            
            return shuttle
            
        except IntegrityError as e:
            db.rollback()
            if "code" in str(e):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Bu shuttle kodu zaten kullanılıyor"
                )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Shuttle oluşturulamadı"
            )
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Shuttle oluşturulurken hata: {str(e)}"
            )
    
    @staticmethod
    def update_shuttle(
        db: Session,
        shuttle_id: int,
        shuttle_data: ShuttleUpdate
    ) -> Shuttle:
        """
        Shuttle güncelle
        
        Args:
            db: Database session
            shuttle_id: Shuttle ID
            shuttle_data: Güncelleme verisi
            
        Returns:
            Shuttle: Güncellenmiş shuttle
            
        Raises:
            HTTPException: Shuttle bulunamazsa veya hata durumunda
        """
        try:
            # Shuttle'ı bul
            shuttle = db.query(Shuttle).filter(Shuttle.id == shuttle_id).first()
            if not shuttle:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Shuttle bulunamadı"
                )
            
            # Sadece gönderilen alanları güncelle
            update_data = shuttle_data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                # Code alanını uppercase yap
                if field == 'code' and value:
                    value = value.upper()
                setattr(shuttle, field, value)
            
            db.commit()
            db.refresh(shuttle)
            
            return shuttle
            
        except HTTPException:
            raise
        except IntegrityError as e:
            db.rollback()
            if "code" in str(e):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Bu shuttle kodu zaten kullanılıyor"
                )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Shuttle güncellenemedi"
            )
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Shuttle güncellenirken hata: {str(e)}"
            )
    
    @staticmethod
    def delete_shuttle(db: Session, shuttle_id: int) -> bool:
        """
        Shuttle sil
        
        Args:
            db: Database session
            shuttle_id: Shuttle ID
            
        Returns:
            bool: Başarılı ise True
            
        Raises:
            HTTPException: Shuttle bulunamazsa veya hata durumunda
        """
        try:
            shuttle = db.query(Shuttle).filter(Shuttle.id == shuttle_id).first()
            if not shuttle:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Shuttle bulunamadı"
                )
            
            # Aktif request'i varsa silinemez
            if shuttle.status == ShuttleStatus.BUSY.value:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Aktif görevde olan shuttle silinemez"
                )
            
            db.delete(shuttle)
            db.commit()
            
            return True
            
        except HTTPException:
            raise
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Bu shuttle kullanımda olduğu için silinemez"
            )
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Shuttle silinirken hata: {str(e)}"
            )
    
    @staticmethod
    def update_shuttle_status(
        db: Session,
        shuttle_id: int,
        status_data: ShuttleStatusUpdate
    ) -> Shuttle:
        """
        Shuttle durumunu güncelle
        
        Args:
            db: Database session
            shuttle_id: Shuttle ID
            status_data: Durum güncelleme verisi
            
        Returns:
            Shuttle: Güncellenmiş shuttle
            
        Raises:
            HTTPException: Shuttle bulunamazsa veya hata durumunda
        """
        try:
            shuttle = db.query(Shuttle).filter(Shuttle.id == shuttle_id).first()
            if not shuttle:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Shuttle bulunamadı"
                )
            
            # Durumu güncelle
            shuttle.status = status_data.status.value
            
            # Lokasyon varsa güncelle
            if status_data.current_location_id is not None:
                shuttle.current_location_id = status_data.current_location_id
            
            db.commit()
            db.refresh(shuttle)
            
            return shuttle
            
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Shuttle durumu güncellenirken hata: {str(e)}"
            )
    
    @staticmethod
    def update_shuttle_location(
        db: Session,
        shuttle_id: int,
        location_id: int
    ) -> Shuttle:
        """
        Shuttle lokasyonunu güncelle
        
        Args:
            db: Database session
            shuttle_id: Shuttle ID
            location_id: Yeni lokasyon ID
            
        Returns:
            Shuttle: Güncellenmiş shuttle
            
        Raises:
            HTTPException: Shuttle bulunamazsa veya hata durumunda
        """
        try:
            shuttle = db.query(Shuttle).filter(Shuttle.id == shuttle_id).first()
            if not shuttle:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Shuttle bulunamadı"
                )
            
            shuttle.current_location_id = location_id
            
            db.commit()
            db.refresh(shuttle)
            
            return shuttle
            
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Shuttle lokasyonu güncellenirken hata: {str(e)}"
            )
    
    @staticmethod
    def assign_driver_to_shuttle(
        db: Session,
        shuttle_id: int,
        driver_id: int,
        is_primary: bool = False,
        is_active: bool = True
    ) -> ShuttleDriver:
        """
        Shuttle'a sürücü ata
        
        Args:
            db: Database session
            shuttle_id: Shuttle ID
            driver_id: Sürücü ID
            is_primary: Birincil sürücü mü?
            is_active: Aktif mi?
            
        Returns:
            ShuttleDriver: Atama kaydı
            
        Raises:
            HTTPException: Hata durumunda
        """
        try:
            # Shuttle kontrolü
            shuttle = db.query(Shuttle).filter(Shuttle.id == shuttle_id).first()
            if not shuttle:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Shuttle bulunamadı"
                )
            
            # Sürücü kontrolü
            driver = db.query(SystemUser).filter(
                SystemUser.id == driver_id,
                SystemUser.role == UserRole.DRIVER.value
            ).first()
            if not driver:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Sürücü bulunamadı"
                )
            
            # Mevcut atama var mı kontrol et
            existing = db.query(ShuttleDriver).filter(
                ShuttleDriver.shuttle_id == shuttle_id,
                ShuttleDriver.driver_id == driver_id
            ).first()
            
            if existing:
                # Mevcut atamayı güncelle
                existing.is_primary = is_primary
                existing.is_active = is_active
                existing.last_active_at = datetime.utcnow() if is_active else existing.last_active_at
                db.commit()
                db.refresh(existing)
                return existing
            
            # Yeni atama oluştur
            assignment = ShuttleDriver(
                shuttle_id=shuttle_id,
                driver_id=driver_id,
                is_primary=is_primary,
                is_active=is_active,
                assigned_at=datetime.utcnow(),
                last_active_at=datetime.utcnow() if is_active else None
            )
            
            db.add(assignment)
            db.commit()
            db.refresh(assignment)
            
            return assignment
            
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Sürücü atanırken hata: {str(e)}"
            )
    
    @staticmethod
    def get_available_shuttles(
        db: Session,
        hotel_id: int
    ) -> List[Shuttle]:
        """
        Müsait shuttle'ları getir
        
        Args:
            db: Database session
            hotel_id: Otel ID
            
        Returns:
            List[Shuttle]: Müsait shuttle listesi
        """
        return db.query(Shuttle).filter(
            Shuttle.hotel_id == hotel_id,
            Shuttle.status == ShuttleStatus.AVAILABLE.value
        ).all()
    
    @staticmethod
    def get_shuttle_by_id(db: Session, shuttle_id: int) -> Optional[Shuttle]:
        """
        ID ile shuttle getir
        
        Args:
            db: Database session
            shuttle_id: Shuttle ID
            
        Returns:
            Optional[Shuttle]: Shuttle veya None
        """
        return db.query(Shuttle).filter(Shuttle.id == shuttle_id).first()
    
    @staticmethod
    def get_shuttle_by_code(db: Session, code: str) -> Optional[Shuttle]:
        """
        Kod ile shuttle getir
        
        Args:
            db: Database session
            code: Shuttle kodu
            
        Returns:
            Optional[Shuttle]: Shuttle veya None
        """
        return db.query(Shuttle).filter(Shuttle.code == code.upper()).first()
    
    @staticmethod
    def get_shuttles(
        db: Session,
        hotel_id: Optional[int] = None,
        status: Optional[ShuttleStatus] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Shuttle]:
        """
        Shuttle listesi getir
        
        Args:
            db: Database session
            hotel_id: Otel ID filtresi (opsiyonel)
            status: Durum filtresi (opsiyonel)
            skip: Kaç kayıt atlanacak
            limit: Maksimum kayıt sayısı
            
        Returns:
            List[Shuttle]: Shuttle listesi
        """
        query = db.query(Shuttle).options(
            joinedload(Shuttle.current_location),
            joinedload(Shuttle.driver_assignments)
        )
        
        # Filtreler
        if hotel_id is not None:
            query = query.filter(Shuttle.hotel_id == hotel_id)
        if status is not None:
            query = query.filter(Shuttle.status == status.value)
        
        # Sıralama ve pagination
        query = query.order_by(Shuttle.code)
        query = query.offset(skip).limit(limit)
        
        return query.all()
    
    @staticmethod
    def count_shuttles(
        db: Session,
        hotel_id: Optional[int] = None,
        status: Optional[ShuttleStatus] = None
    ) -> int:
        """
        Shuttle sayısını getir
        
        Args:
            db: Database session
            hotel_id: Otel ID filtresi (opsiyonel)
            status: Durum filtresi (opsiyonel)
            
        Returns:
            int: Shuttle sayısı
        """
        query = db.query(Shuttle)
        
        if hotel_id is not None:
            query = query.filter(Shuttle.hotel_id == hotel_id)
        if status is not None:
            query = query.filter(Shuttle.status == status.value)
        
        return query.count()
    
    @staticmethod
    def get_driver_assignments(
        db: Session,
        shuttle_id: int,
        active_only: bool = False
    ) -> List[ShuttleDriver]:
        """
        Shuttle'ın sürücü atamalarını getir
        
        Args:
            db: Database session
            shuttle_id: Shuttle ID
            active_only: Sadece aktif atamaları getir
            
        Returns:
            List[ShuttleDriver]: Atama listesi
        """
        query = db.query(ShuttleDriver).filter(
            ShuttleDriver.shuttle_id == shuttle_id
        ).options(
            joinedload(ShuttleDriver.driver)
        )
        
        if active_only:
            query = query.filter(ShuttleDriver.is_active == True)
        
        return query.all()
    
    @staticmethod
    def remove_driver_assignment(
        db: Session,
        shuttle_id: int,
        driver_id: int
    ) -> bool:
        """
        Sürücü atamasını kaldır
        
        Args:
            db: Database session
            shuttle_id: Shuttle ID
            driver_id: Sürücü ID
            
        Returns:
            bool: Başarılı ise True
            
        Raises:
            HTTPException: Atama bulunamazsa
        """
        try:
            assignment = db.query(ShuttleDriver).filter(
                ShuttleDriver.shuttle_id == shuttle_id,
                ShuttleDriver.driver_id == driver_id
            ).first()
            
            if not assignment:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Atama bulunamadı"
                )
            
            db.delete(assignment)
            db.commit()
            
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Atama kaldırılırken hata: {str(e)}"
            )
