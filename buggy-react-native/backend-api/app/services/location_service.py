"""
Location Service
Lokasyon yönetimi için business logic
"""
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Optional, List
from fastapi import HTTPException, status
import qrcode
import io
import base64
import uuid

from app.models.location import Location
from app.schemas.location import LocationCreate, LocationUpdate


class LocationService:
    """Location business logic"""
    
    @staticmethod
    def create_location(db: Session, location_data: LocationCreate) -> Location:
        """
        Yeni lokasyon oluştur
        
        Args:
            db: Database session
            location_data: Lokasyon oluşturma verisi
            
        Returns:
            Location: Oluşturulan lokasyon
            
        Raises:
            HTTPException: Hata durumunda
        """
        try:
            # QR kod verisi yoksa otomatik oluştur
            if not location_data.qr_code_data:
                qr_code_data = f"LOC_{uuid.uuid4().hex[:8].upper()}"
            else:
                qr_code_data = location_data.qr_code_data
            
            # Yeni lokasyon oluştur
            location = Location(
                hotel_id=location_data.hotel_id,
                name=location_data.name,
                description=location_data.description,
                qr_code_data=qr_code_data,
                display_order=location_data.display_order,
                latitude=location_data.latitude,
                longitude=location_data.longitude,
                is_active=location_data.is_active,
                location_image=location_data.location_image
            )
            
            db.add(location)
            db.commit()
            db.refresh(location)
            
            return location
            
        except IntegrityError as e:
            db.rollback()
            if "qr_code_data" in str(e):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Bu QR kod zaten kullanılıyor"
                )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Lokasyon oluşturulamadı"
            )
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Lokasyon oluşturulurken hata: {str(e)}"
            )
    
    @staticmethod
    def update_location(
        db: Session,
        location_id: int,
        location_data: LocationUpdate
    ) -> Location:
        """
        Lokasyon güncelle
        
        Args:
            db: Database session
            location_id: Lokasyon ID
            location_data: Güncelleme verisi
            
        Returns:
            Location: Güncellenmiş lokasyon
            
        Raises:
            HTTPException: Lokasyon bulunamazsa veya hata durumunda
        """
        try:
            # Lokasyonu bul
            location = db.query(Location).filter(Location.id == location_id).first()
            if not location:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Lokasyon bulunamadı"
                )
            
            # Sadece gönderilen alanları güncelle
            update_data = location_data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(location, field, value)
            
            db.commit()
            db.refresh(location)
            
            return location
            
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Lokasyon güncellenirken hata: {str(e)}"
            )
    
    @staticmethod
    def delete_location(db: Session, location_id: int) -> bool:
        """
        Lokasyon sil
        
        Args:
            db: Database session
            location_id: Lokasyon ID
            
        Returns:
            bool: Başarılı ise True
            
        Raises:
            HTTPException: Lokasyon bulunamazsa veya hata durumunda
        """
        try:
            location = db.query(Location).filter(Location.id == location_id).first()
            if not location:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Lokasyon bulunamadı"
                )
            
            db.delete(location)
            db.commit()
            
            return True
            
        except HTTPException:
            raise
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Bu lokasyon kullanımda olduğu için silinemez"
            )
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Lokasyon silinirken hata: {str(e)}"
            )
    
    @staticmethod
    def get_location_by_id(db: Session, location_id: int) -> Optional[Location]:
        """
        ID ile lokasyon getir
        
        Args:
            db: Database session
            location_id: Lokasyon ID
            
        Returns:
            Optional[Location]: Lokasyon veya None
        """
        return db.query(Location).filter(Location.id == location_id).first()
    
    @staticmethod
    def get_location_by_qr_code(db: Session, qr_code: str) -> Optional[Location]:
        """
        QR kod ile lokasyon getir
        
        Args:
            db: Database session
            qr_code: QR kod verisi
            
        Returns:
            Optional[Location]: Lokasyon veya None
            
        Raises:
            HTTPException: Lokasyon bulunamazsa veya aktif değilse
        """
        location = db.query(Location).filter(
            Location.qr_code_data == qr_code
        ).first()
        
        if not location:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Geçersiz QR kod"
            )
        
        if not location.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bu lokasyon aktif değil"
            )
        
        return location
    
    @staticmethod
    def get_locations(
        db: Session,
        hotel_id: Optional[int] = None,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Location]:
        """
        Lokasyon listesi getir
        
        Args:
            db: Database session
            hotel_id: Otel ID filtresi (opsiyonel)
            is_active: Aktif durum filtresi (opsiyonel)
            skip: Kaç kayıt atlanacak
            limit: Maksimum kayıt sayısı
            
        Returns:
            List[Location]: Lokasyon listesi
        """
        query = db.query(Location)
        
        # Filtreler
        if hotel_id is not None:
            query = query.filter(Location.hotel_id == hotel_id)
        if is_active is not None:
            query = query.filter(Location.is_active == is_active)
        
        # Sıralama ve pagination
        query = query.order_by(Location.display_order, Location.name)
        query = query.offset(skip).limit(limit)
        
        return query.all()
    
    @staticmethod
    def count_locations(
        db: Session,
        hotel_id: Optional[int] = None,
        is_active: Optional[bool] = None
    ) -> int:
        """
        Lokasyon sayısını getir
        
        Args:
            db: Database session
            hotel_id: Otel ID filtresi (opsiyonel)
            is_active: Aktif durum filtresi (opsiyonel)
            
        Returns:
            int: Lokasyon sayısı
        """
        query = db.query(Location)
        
        if hotel_id is not None:
            query = query.filter(Location.hotel_id == hotel_id)
        if is_active is not None:
            query = query.filter(Location.is_active == is_active)
        
        return query.count()
    
    @staticmethod
    def generate_qr_code(qr_code_data: str) -> str:
        """
        QR kod görseli oluştur
        
        Args:
            qr_code_data: QR kod verisi
            
        Returns:
            str: Base64 encoded PNG görsel
        """
        try:
            # QR kod oluştur
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(qr_code_data)
            qr.make(fit=True)
            
            # PNG görsel oluştur
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Base64'e çevir
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            img_str = base64.b64encode(buffer.getvalue()).decode()
            
            return f"data:image/png;base64,{img_str}"
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"QR kod oluşturulamadı: {str(e)}"
            )
    
    @staticmethod
    def generate_and_save_qr_code(db: Session, location_id: int) -> Location:
        """
        Lokasyon için QR kod oluştur ve kaydet
        
        Args:
            db: Database session
            location_id: Lokasyon ID
            
        Returns:
            Location: QR kodu güncellenmiş lokasyon
            
        Raises:
            HTTPException: Lokasyon bulunamazsa veya hata durumunda
        """
        try:
            location = db.query(Location).filter(Location.id == location_id).first()
            if not location:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Lokasyon bulunamadı"
                )
            
            # QR kod görseli oluştur
            qr_code_image = LocationService.generate_qr_code(location.qr_code_data)
            
            # Lokasyona kaydet
            location.qr_code_image = qr_code_image
            db.commit()
            db.refresh(location)
            
            return location
            
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"QR kod kaydedilemedi: {str(e)}"
            )
