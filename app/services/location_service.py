"""
Buggy Call - Location Service
"""
from app import db
from app.models.location import Location
from app.models.hotel import Hotel
from app.services.audit_service import AuditService
from app.services.qr_service import QRCodeService
from app.utils.exceptions import ResourceNotFoundException, ValidationException
from app.utils.helpers import Pagination, generate_unique_code


class LocationService:
    """Service for location management"""
    
    @staticmethod
    def get_all_locations(hotel_id, include_inactive=False, page=1, per_page=50):
        """
        Get all locations for a hotel
        
        Args:
            hotel_id: Hotel ID
            include_inactive: Include inactive locations
            page: Page number
            per_page: Items per page
        
        Returns:
            Paginated locations
        """
        query = Location.query.filter_by(hotel_id=hotel_id)
        
        if not include_inactive:
            query = query.filter_by(is_active=True)
        
        query = query.order_by(Location.display_order, Location.name)
        
        return Pagination.paginate(query, page, per_page)
    
    @staticmethod
    def get_location(location_id):
        """
        Get location by ID
        
        Args:
            location_id: Location ID
        
        Returns:
            Location object
        
        Raises:
            ResourceNotFoundException: If location not found
        """
        location = Location.query.get(location_id)
        if not location:
            raise ResourceNotFoundException('Location', location_id)
        return location
    
    @staticmethod
    def get_location_by_qr_code(qr_code_data):
        """
        Get location by QR code data
        
        Args:
            qr_code_data: QR code data
        
        Returns:
            Location object
        
        Raises:
            ResourceNotFoundException: If location not found
        """
        location = Location.query.filter_by(qr_code_data=qr_code_data).first()
        if not location:
            raise ResourceNotFoundException('Location')
        return location
    
    @staticmethod
    def create_location(hotel_id, name, description=None, latitude=None, 
                       longitude=None, display_order=0, is_active=True):
        """
        Create new location
        
        Args:
            hotel_id: Hotel ID
            name: Location name
            description: Description (optional)
            latitude: Latitude (optional)
            longitude: Longitude (optional)
            display_order: Display order
            is_active: Active status
        
        Returns:
            Created location
        
        Raises:
            ResourceNotFoundException: If hotel not found
            ValidationException: If location name already exists
        """
        # Check if hotel exists
        hotel = Hotel.query.get(hotel_id)
        if not hotel:
            raise ResourceNotFoundException('Hotel', hotel_id)
        
        # Check if location name already exists for this hotel
        existing = Location.query.filter_by(
            hotel_id=hotel_id,
            name=name
        ).first()
        if existing:
            raise ValidationException(f'Lokasyon adı "{name}" bu otel için zaten kullanılıyor')
        
        # Generate unique QR code data
        qr_code_data = generate_unique_code(prefix='LOC_', length=12)
        
        # Ensure QR code is unique
        while Location.query.filter_by(qr_code_data=qr_code_data).first():
            qr_code_data = generate_unique_code(prefix='LOC_', length=12)
        
        # Create location
        location = Location(
            hotel_id=hotel_id,
            name=name,
            description=description,
            qr_code_data=qr_code_data,
            latitude=latitude,
            longitude=longitude,
            display_order=display_order,
            is_active=is_active
        )
        
        db.session.add(location)
        db.session.flush()  # Get ID before generating QR code
        
        # Generate QR code image
        qr_image_path = QRCodeService.generate_qr_code(
            location.id,
            qr_code_data,
            location.name
        )
        location.qr_code_image = qr_image_path
        
        db.session.commit()
        
        # Log creation
        AuditService.log_create(
            entity_type='location',
            entity_id=location.id,
            new_values=location.to_dict(),
            hotel_id=hotel_id
        )
        
        return location
    
    @staticmethod
    def update_location(location_id, **kwargs):
        """
        Update location
        
        Args:
            location_id: Location ID
            **kwargs: Fields to update
        
        Returns:
            Updated location
        
        Raises:
            ResourceNotFoundException: If location not found
            ValidationException: If name already exists
        """
        location = Location.query.get(location_id)
        if not location:
            raise ResourceNotFoundException('Location', location_id)
        
        # Store old values for audit
        old_values = location.to_dict()
        
        # Check if name is being changed and already exists
        if 'name' in kwargs and kwargs['name'] != location.name:
            existing = Location.query.filter_by(
                hotel_id=location.hotel_id,
                name=kwargs['name']
            ).first()
            if existing:
                raise ValidationException(f'Lokasyon adı "{kwargs["name"]}" zaten kullanılıyor')
        
        # Update allowed fields
        allowed_fields = ['name', 'description', 'latitude', 'longitude', 
                         'display_order', 'is_active']
        for field in allowed_fields:
            if field in kwargs:
                setattr(location, field, kwargs[field])
        
        db.session.commit()
        
        # Log update
        AuditService.log_update(
            entity_type='location',
            entity_id=location.id,
            old_values=old_values,
            new_values=location.to_dict(),
            hotel_id=location.hotel_id
        )
        
        return location
    
    @staticmethod
    def delete_location(location_id):
        """
        Delete location with enhanced active buggy validation
        
        Args:
            location_id: Location ID
        
        Raises:
            ResourceNotFoundException: If location not found
            ValidationException: If location has active requests or active buggies
        """
        location = Location.query.get(location_id)
        if not location:
            raise ResourceNotFoundException('Location', location_id)
        
        # Check if location has active requests
        from app.models.request import BuggyRequest, RequestStatus
        active_requests = BuggyRequest.query.filter_by(
            location_id=location_id,
            status=RequestStatus.PENDING
        ).count()
        
        if active_requests > 0:
            raise ValidationException(
                f'Bu lokasyonda {active_requests} aktif talep var. '
                'Önce talepleri tamamlayın veya iptal edin.'
            )
        
        # Check for buggies with active driver sessions
        from app.models.buggy import Buggy
        from app.models.buggy_driver import BuggyDriver
        
        # Get all buggies at this location
        buggies_at_location = Buggy.query.filter_by(
            current_location_id=location_id
        ).all()
        
        # Categorize buggies as active or inactive
        active_buggies = []
        inactive_buggies = []
        
        for buggy in buggies_at_location:
            # Check if buggy has an active driver session
            has_active_session = BuggyDriver.query.filter_by(
                buggy_id=buggy.id,
                is_active=True
            ).first() is not None
            
            if has_active_session:
                active_buggies.append(buggy)
            else:
                inactive_buggies.append(buggy)
        
        # Block deletion if any buggy has an active driver session
        if active_buggies:
            raise ValidationException(
                f'Bu lokasyonda {len(active_buggies)} aktif buggy bulunuyor. '
                'Sürücüler oturumu kapatana veya farklı lokasyon seçene kadar bu lokasyon silinemez.'
            )
        
        # Set current_location_id to NULL for all inactive buggies
        for buggy in inactive_buggies:
            buggy.current_location_id = None
        
        # Store values for audit
        old_values = location.to_dict()
        hotel_id = location.hotel_id
        affected_buggy_ids = [b.id for b in inactive_buggies]
        
        # Delete QR code file
        QRCodeService.delete_qr_code(location.id)
        
        # Delete location
        db.session.delete(location)
        db.session.commit()
        
        # Enhanced audit logging with affected buggies
        audit_new_values = {
            'affected_buggies_count': len(inactive_buggies),
            'affected_buggy_ids': affected_buggy_ids
        } if inactive_buggies else None
        
        AuditService.log_delete(
            entity_type='location',
            entity_id=location_id,
            old_values=old_values,
            hotel_id=hotel_id
        )
        
        # Log additional information about affected buggies if any
        if inactive_buggies:
            AuditService.log_action(
                action='location_deleted_with_buggies',
                entity_type='location',
                entity_id=location_id,
                new_values=audit_new_values,
                hotel_id=hotel_id
            )
    
    @staticmethod
    def regenerate_qr_code(location_id):
        """
        Regenerate QR code for location
        
        Args:
            location_id: Location ID
        
        Returns:
            Updated location
        
        Raises:
            ResourceNotFoundException: If location not found
        """
        location = Location.query.get(location_id)
        if not location:
            raise ResourceNotFoundException('Location', location_id)
        
        # Delete old QR code
        QRCodeService.delete_qr_code(location.id)
        
        # Generate new QR code
        qr_image_path = QRCodeService.generate_qr_code(
            location.id,
            location.qr_code_data,
            location.name
        )
        
        old_path = location.qr_code_image
        location.qr_code_image = qr_image_path
        db.session.commit()
        
        # Log regeneration
        AuditService.log_action(
            action='qr_code_regenerated',
            entity_type='location',
            entity_id=location.id,
            old_values={'qr_code_image': old_path},
            new_values={'qr_code_image': qr_image_path},
            hotel_id=location.hotel_id
        )
        
        return location
