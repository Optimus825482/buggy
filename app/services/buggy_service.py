"""
Buggy Call - Buggy Service
"""
from app import db, socketio
from app.models.buggy import Buggy, BuggyStatus
from app.models.user import SystemUser, UserRole
from app.models.hotel import Hotel
from app.services.audit_service import AuditService
from app.utils.exceptions import ResourceNotFoundException, ValidationException, BusinessLogicException
from app.utils.helpers import Pagination
from datetime import datetime


class BuggyService:
    """Service for buggy management"""
    
    @staticmethod
    def get_all_buggies(hotel_id, status=None, page=1, per_page=50):
        """
        Get all buggies for a hotel
        
        Args:
            hotel_id: Hotel ID
            status: Filter by status (optional)
            page: Page number
            per_page: Items per page
        
        Returns:
            Paginated buggies
        """
        query = Buggy.query.filter_by(hotel_id=hotel_id)
        
        if status:
            query = query.filter_by(status=BuggyStatus[status.upper()])
        
        query = query.order_by(Buggy.name)
        
        return Pagination.paginate(query, page, per_page)
    
    @staticmethod
    def get_buggy(buggy_id):
        """
        Get buggy by ID
        
        Args:
            buggy_id: Buggy ID
        
        Returns:
            Buggy object
        
        Raises:
            ResourceNotFoundException: If buggy not found
        """
        buggy = Buggy.query.get(buggy_id)
        if not buggy:
            raise ResourceNotFoundException('Buggy', buggy_id)
        return buggy
    
    @staticmethod
    def get_available_buggies(hotel_id):
        """
        Get available buggies for a hotel
        
        Args:
            hotel_id: Hotel ID
        
        Returns:
            List of available buggies
        """
        return Buggy.query.filter_by(
            hotel_id=hotel_id,
            status=BuggyStatus.AVAILABLE
        ).all()
    
    @staticmethod
    def create_buggy(hotel_id, name, plate_number=None, model=None, 
                    capacity=4, driver_id=None):
        """
        Create new buggy
        
        Args:
            hotel_id: Hotel ID
            name: Buggy name/code
            plate_number: License plate (optional)
            model: Buggy model (optional)
            capacity: Passenger capacity
            driver_id: Assigned driver ID (optional)
        
        Returns:
            Created buggy
        
        Raises:
            ResourceNotFoundException: If hotel or driver not found
            ValidationException: If name already exists or driver already assigned
        """
        # Check if hotel exists
        hotel = Hotel.query.get(hotel_id)
        if not hotel:
            raise ResourceNotFoundException('Hotel', hotel_id)
        
        # Check if buggy name already exists for this hotel
        existing = Buggy.query.filter_by(
            hotel_id=hotel_id,
            name=name
        ).first()
        if existing:
            raise ValidationException(f'Buggy adı "{name}" bu otel için zaten kullanılıyor')
        
        # Check if driver exists and is a driver role
        if driver_id:
            driver = SystemUser.query.get(driver_id)
            if not driver:
                raise ResourceNotFoundException('Driver', driver_id)
            if driver.role != UserRole.DRIVER:
                raise ValidationException('Seçilen kullanıcı sürücü rolünde değil')
            if driver.hotel_id != hotel_id:
                raise ValidationException('Sürücü farklı bir otele ait')
            
            # Check if driver already assigned to another buggy
            existing_buggy = Buggy.query.filter_by(driver_id=driver_id).first()
            if existing_buggy:
                raise ValidationException(
                    f'Bu sürücü zaten "{existing_buggy.name}" buggy\'sine atanmış'
                )
        
        # Create buggy
        buggy = Buggy(
            hotel_id=hotel_id,
            name=name,
            plate_number=plate_number,
            model=model,
            capacity=capacity,
            driver_id=driver_id,
            status=BuggyStatus.OFFLINE
        )
        
        db.session.add(buggy)
        db.session.commit()
        
        # Log creation
        AuditService.log_create(
            entity_type='buggy',
            entity_id=buggy.id,
            new_values=buggy.to_dict(),
            hotel_id=hotel_id
        )
        
        return buggy
    
    @staticmethod
    def update_buggy(buggy_id, **kwargs):
        """
        Update buggy
        
        Args:
            buggy_id: Buggy ID
            **kwargs: Fields to update
        
        Returns:
            Updated buggy
        
        Raises:
            ResourceNotFoundException: If buggy not found
            ValidationException: If validation fails
        """
        buggy = Buggy.query.get(buggy_id)
        if not buggy:
            raise ResourceNotFoundException('Buggy', buggy_id)
        
        # Store old values for audit
        old_values = buggy.to_dict()
        
        # Check if name is being changed and already exists
        if 'name' in kwargs and kwargs['name'] != buggy.name:
            existing = Buggy.query.filter_by(
                hotel_id=buggy.hotel_id,
                name=kwargs['name']
            ).first()
            if existing:
                raise ValidationException(f'Buggy adı "{kwargs["name"]}" zaten kullanılıyor')
        
        # Check driver assignment
        if 'driver_id' in kwargs and kwargs['driver_id'] != buggy.driver_id:
            if kwargs['driver_id']:
                driver = SystemUser.query.get(kwargs['driver_id'])
                if not driver:
                    raise ResourceNotFoundException('Driver', kwargs['driver_id'])
                if driver.role != UserRole.DRIVER:
                    raise ValidationException('Seçilen kullanıcı sürücü rolünde değil')
                
                # Check if driver already assigned
                existing_buggy = Buggy.query.filter_by(
                    driver_id=kwargs['driver_id']
                ).first()
                if existing_buggy and existing_buggy.id != buggy_id:
                    raise ValidationException(
                        f'Bu sürücü zaten "{existing_buggy.name}" buggy\'sine atanmış'
                    )
        
        # Update allowed fields
        allowed_fields = ['name', 'plate_number', 'model', 'capacity', 
                         'driver_id', 'status']
        for field in allowed_fields:
            if field in kwargs:
                if field == 'status' and isinstance(kwargs[field], str):
                    setattr(buggy, field, BuggyStatus[kwargs[field].upper()])
                else:
                    setattr(buggy, field, kwargs[field])
        
        db.session.commit()
        
        # Log update
        AuditService.log_update(
            entity_type='buggy',
            entity_id=buggy.id,
            old_values=old_values,
            new_values=buggy.to_dict(),
            hotel_id=buggy.hotel_id
        )
        
        return buggy
    
    @staticmethod
    def update_status(buggy_id, status, location_id=None):
        """
        Update buggy status
        
        Args:
            buggy_id: Buggy ID
            status: New status
            location_id: Current location ID (optional)
        
        Returns:
            Updated buggy
        
        Raises:
            ResourceNotFoundException: If buggy not found
            BusinessLogicException: If status transition is invalid
        """
        buggy = Buggy.query.get(buggy_id)
        if not buggy:
            raise ResourceNotFoundException('Buggy', buggy_id)
        
        old_status = buggy.status
        new_status = BuggyStatus[status.upper()] if isinstance(status, str) else status
        
        # Validate status transition
        if old_status == BuggyStatus.BUSY and new_status == BuggyStatus.AVAILABLE:
            # Check if buggy has active requests
            from app.models.request import BuggyRequest, RequestStatus
            active_request = BuggyRequest.query.filter_by(
                buggy_id=buggy_id,
                status=RequestStatus.ACCEPTED
            ).first()
            if active_request:
                raise BusinessLogicException(
                    'Buggy\'nin aktif talebi var. Önce talebi tamamlayın.'
                )
        
        # Update status
        buggy.status = new_status
        db.session.commit()
        
        # Log status change
        AuditService.log_action(
            action='status_changed',
            entity_type='buggy',
            entity_id=buggy.id,
            old_values={'status': old_status.value},
            new_values={'status': new_status.value, 'location_id': location_id},
            hotel_id=buggy.hotel_id
        )
        
        return buggy
    
    @staticmethod
    def delete_buggy(buggy_id):
        """
        Delete buggy
        
        Args:
            buggy_id: Buggy ID
        
        Raises:
            ResourceNotFoundException: If buggy not found
            ValidationException: If buggy has active requests
        """
        buggy = Buggy.query.get(buggy_id)
        if not buggy:
            raise ResourceNotFoundException('Buggy', buggy_id)
        
        # Check if buggy has active requests
        from app.models.request import BuggyRequest, RequestStatus
        active_requests = BuggyRequest.query.filter_by(
            buggy_id=buggy_id
        ).filter(
            BuggyRequest.status.in_([RequestStatus.PENDING, RequestStatus.ACCEPTED])
        ).count()
        
        if active_requests > 0:
            raise ValidationException(
                f'Bu buggy\'nin {active_requests} aktif talebi var. '
                'Önce talepleri tamamlayın veya iptal edin.'
            )
        
        # Store values for audit
        old_values = buggy.to_dict()
        hotel_id = buggy.hotel_id
        
        # Delete buggy
        db.session.delete(buggy)
        db.session.commit()
        
        # Log deletion
        AuditService.log_delete(
            entity_type='buggy',
            entity_id=buggy_id,
            old_values=old_values,
            hotel_id=hotel_id
        )
    
    @staticmethod
    def get_buggy_by_driver(driver_id):
        """
        Get buggy assigned to a driver
        
        Args:
            driver_id: Driver ID
        
        Returns:
            Buggy object or None
        """
        return Buggy.query.filter_by(driver_id=driver_id).first()

    @staticmethod
    def update_location(buggy_id, location_id):
        """
        Update buggy's current location
        
        Args:
            buggy_id: Buggy ID
            location_id: Location ID
        
        Returns:
            Updated buggy
        
        Raises:
            ResourceNotFoundException: If buggy or location not found
            ValidationException: If location belongs to different hotel
        """
        buggy = Buggy.query.get(buggy_id)
        if not buggy:
            raise ResourceNotFoundException('Buggy', buggy_id)
        
        from app.models.location import Location
        location = Location.query.get(location_id)
        if not location:
            raise ResourceNotFoundException('Location', location_id)
        
        if location.hotel_id != buggy.hotel_id:
            raise ValidationException('Lokasyon farklı bir otele ait')
        
        # Store old location for audit
        old_location_id = buggy.current_location_id
        old_location_name = buggy.current_location.name if buggy.current_location else None
        
        # Update location and set to available
        buggy.current_location_id = location_id
        buggy.status = BuggyStatus.AVAILABLE
        
        db.session.commit()
        
        # Log location update
        AuditService.log_action(
            action='location_updated',
            entity_type='buggy',
            entity_id=buggy.id,
            old_values={'location_id': old_location_id, 'location_name': old_location_name},
            new_values={'location_id': location_id, 'location_name': location.name},
            hotel_id=buggy.hotel_id
        )
        
        return buggy
    
    @staticmethod
    def get_available_buggies_by_location(hotel_id, location_id=None):
        """
        Get available buggies, optionally filtered by location
        
        Args:
            hotel_id: Hotel ID
            location_id: Location ID (optional)
        
        Returns:
            List of available buggies with location info
        """
        query = Buggy.query.filter_by(
            hotel_id=hotel_id,
            status=BuggyStatus.AVAILABLE
        )
        
        if location_id:
            query = query.filter_by(current_location_id=location_id)
        
        buggies = query.all()
        
        # Return with location info
        return [{
            **buggy.to_dict(),
            'current_location': {
                'id': buggy.current_location.id,
                'name': buggy.current_location.name
            } if buggy.current_location else None
        } for buggy in buggies]
    
    @staticmethod
    def emit_buggy_status_update(buggy_id, hotel_id):
        """
        Emit buggy status update to all admin clients via WebSocket
        
        Args:
            buggy_id: Buggy ID
            hotel_id: Hotel ID for room targeting
        
        Returns:
            None
        
        Note:
            This function emits real-time updates to admin dashboard
            Status determination:
            - offline: No active session
            - available: Active session but no active request
            - busy: Active session with active request
        """
        try:
            from app.models.buggy_driver import BuggyDriver
            
            # Get buggy
            buggy = Buggy.query.get(buggy_id)
            if not buggy:
                # Log warning but don't raise - non-blocking
                print(f'Warning: Buggy {buggy_id} not found for status update')
                return
            
            # Get active session info
            active_session = BuggyDriver.query.filter_by(
                buggy_id=buggy_id,
                is_active=True
            ).first()
            
            driver_name = None
            if active_session:
                driver = SystemUser.query.get(active_session.driver_id)
                driver_name = driver.full_name if driver and driver.full_name else (driver.username if driver else None)
            
            # Determine status
            status = 'offline'
            if active_session:
                # Check if buggy has active request
                from app.models.request import BuggyRequest, RequestStatus
                active_request = BuggyRequest.query.filter_by(
                    buggy_id=buggy_id,
                    status=RequestStatus.ACCEPTED
                ).first()
                
                status = 'busy' if active_request else 'available'
            
            # Get location name if location exists
            location_name = None
            if buggy.current_location_id:
                location = Location.query.get(buggy.current_location_id)
                location_name = location.name if location else None
            
            # Prepare payload
            payload = {
                'buggy_id': buggy.id,
                'buggy_code': buggy.code,
                'buggy_icon': buggy.icon,
                'status': status,
                'driver_name': driver_name,
                'location_id': buggy.current_location_id,
                'location_name': location_name,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Emit to admin room
            room = f'hotel_{hotel_id}_admin'
            socketio.emit('buggy_status_update', payload, room=room)
            
            print(f'✅ Buggy status update emitted: Buggy {buggy.code} -> {status} (room: {room})')
            
        except Exception as e:
            # Log error but don't raise - this should be non-blocking
            print(f'❌ Error emitting buggy status update: {str(e)}')
            import traceback
            traceback.print_exc()
