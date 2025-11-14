"""
Buggy Call - Request Service
"""
from app import db, socketio
from app.models.request import BuggyRequest, RequestStatus
from app.models.buggy import Buggy, BuggyStatus
from app.models.location import Location
from app.models.hotel import Hotel
from app.services.audit_service import AuditService
from app.utils.exceptions import (
    ResourceNotFoundException, ValidationException, 
    BusinessLogicException, ForbiddenException
)
from app.utils.helpers import Pagination
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class RequestService:
    """Service for buggy request management"""
    
    @staticmethod
    def create_request(location_id, room_number=None, guest_name=None, 
                      phone=None, has_room=True, notes=None, guest_device_id=None):
        """
        Create new buggy request (Guest)
        
        Args:
            location_id: Location ID
            room_number: Room number (optional if has_room=False)
            guest_name: Guest name (optional)
            phone: Phone number (optional)
            has_room: Whether guest has a room
            notes: Additional notes (optional)
            guest_device_id: Device ID for tracking (optional)
        
        Returns:
            Created request
        
        Raises:
            ResourceNotFoundException: If location not found
            ValidationException: If validation fails
            BusinessLogicException: If no buggies available
        """
        # Check if location exists and is active
        location = Location.query.get(location_id)
        if not location:
            raise ResourceNotFoundException('Location', location_id)
        
        if not location.is_active:
            raise ValidationException('Bu lokasyon şu anda aktif değil')
        
        # Validate room number if has_room is True
        if has_room and not room_number:
            raise ValidationException('Oda numarası gereklidir')
        
        # Check if there are any available buggies
        available_buggies = Buggy.query.filter_by(
            hotel_id=location.hotel_id,
            status=BuggyStatus.AVAILABLE
        ).count()
        
        if available_buggies == 0:
            raise BusinessLogicException(
                'Şu anda müsait buggy bulunmamaktadır. Lütfen daha sonra tekrar deneyin.'
            )
        
        # Create request
        request_obj = BuggyRequest(
            hotel_id=location.hotel_id,
            location_id=location_id,
            room_number=room_number,
            guest_name=guest_name,
            phone=phone,
            has_room=has_room,
            notes=notes,
            guest_device_id=guest_device_id,
            status=RequestStatus.PENDING
        )
        
        db.session.add(request_obj)
        db.session.commit()
        
        # Log creation
        AuditService.log_create(
            entity_type='request',
            entity_id=request_obj.id,
            new_values=request_obj.to_dict(),
            hotel_id=location.hotel_id
        )
        
        # Notify drivers via FCM (push notification) - Socket.IO kaldırıldı
        try:
            from app.services.fcm_notification_service import FCMNotificationService
            import logging
            logger = logging.getLogger(__name__)
            
            logger.info(f"🔔 FCM bildirimi gönderiliyor - Request ID: {request_obj.id}")
            notified_count = FCMNotificationService.notify_new_request(request_obj)
            
            if notified_count > 0:
                logger.info(f"✅ FCM: {notified_count} sürücüye bildirim gönderildi")
                print(f"✅ FCM: {notified_count} sürücüye bildirim gönderildi")
            else:
                logger.warning(f"⚠️ FCM: Hiçbir sürücüye bildirim gönderilemedi")
                print(f"⚠️ FCM: Hiçbir sürücüye bildirim gönderilemedi")
        except Exception as e:
            import traceback
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"❌ FCM bildirim hatası: {str(e)}")
            logger.error(traceback.format_exc())
            print(f"❌ FCM bildirim hatası: {str(e)}")
            print(traceback.format_exc())
        
        return request_obj
    
    @staticmethod
    def accept_request(request_id, buggy_id, driver_id):
        """
        Accept a request (Driver)
        
        Args:
            request_id: Request ID
            buggy_id: Buggy ID
            driver_id: Driver ID
        
        Returns:
            Updated request
        
        Raises:
            ResourceNotFoundException: If request or buggy not found
            BusinessLogicException: If request already accepted or buggy busy
            ForbiddenException: If driver not authorized
        """
        # Get request
        request_obj = BuggyRequest.query.get(request_id)
        if not request_obj:
            raise ResourceNotFoundException('Request', request_id)
        
        # Check if request is still PENDING
        if request_obj.status != RequestStatus.PENDING:
            raise BusinessLogicException('Bu talep zaten işleme alınmış')
        
        # Get buggy
        buggy = Buggy.query.get(buggy_id)
        if not buggy:
            raise ResourceNotFoundException('Buggy', buggy_id)
        
        # Check if driver is assigned to this buggy
        if buggy.driver_id != driver_id:
            raise ForbiddenException('Bu buggy size atanmamış')
        
        # Check if buggy is available
        if buggy.status != BuggyStatus.AVAILABLE:
            raise BusinessLogicException('Bu buggy şu anda müsait değil')
        
        # Check if buggy belongs to same hotel
        if buggy.hotel_id != request_obj.hotel_id:
            raise ValidationException('Buggy farklı bir otele ait')
        
        # Store old values for audit
        old_values = request_obj.to_dict()
        
        # Update request
        request_obj.buggy_id = buggy_id
        request_obj.accepted_by_id = driver_id
        request_obj.accepted_at = datetime.utcnow()
        request_obj.status = RequestStatus.ACCEPTED
        
        # Calculate response time
        if request_obj.requested_at:
            delta = request_obj.accepted_at - request_obj.requested_at
            request_obj.response_time = int(delta.total_seconds())
        
        # Update buggy status
        buggy.status = BuggyStatus.BUSY
        
        db.session.commit()
        
        # Log acceptance
        AuditService.log_update(
            entity_type='request',
            entity_id=request_obj.id,
            old_values=old_values,
            new_values=request_obj.to_dict(),
            user_id=driver_id,
            hotel_id=request_obj.hotel_id
        )
        
        # Guest'e FCM bildirimi gönder - Socket.IO kaldırıldı
        try:
            from app.routes.guest_notification_api import GUEST_FCM_TOKENS, send_fcm_http_notification
            
            token_data = GUEST_FCM_TOKENS.get(request_id)
            if token_data:
                message_data = {
                    'title': '🎉 Shuttle Kabul Edildi!',
                    'body': f'Shuttle size doğru geliyor. Buggy: {buggy.code}'
                }
                
                # Direkt FCM gönder
                send_fcm_http_notification(token_data['token'], message_data, 'accepted')
                logger.info(f"✅ Guest FCM bildirimi gönderildi - Request ID: {request_id}")
            else:
                logger.info(f"ℹ️ Guest FCM token bulunamadı - Request ID: {request_id}")
                
        except Exception as e:
            logger.error(f"❌ Guest FCM bildirim hatası: {str(e)}")
        
        return request_obj
    
    @staticmethod
    def complete_request(request_id, driver_id, current_location_id=None, notes=None):
        """
        Complete a request (Driver)
        
        Args:
            request_id: Request ID
            driver_id: Driver ID
            current_location_id: Current location of buggy after completion (optional)
            notes: Completion notes (optional)
        
        Returns:
            Updated request
        
        Raises:
            ResourceNotFoundException: If request not found
            BusinessLogicException: If request not accepted
            ForbiddenException: If driver not authorized
            ValidationException: If location invalid
        """
        # Get request
        request_obj = BuggyRequest.query.get(request_id)
        if not request_obj:
            raise ResourceNotFoundException('Request', request_id)
        
        # Check if request is accepted
        if request_obj.status != RequestStatus.ACCEPTED:
            raise BusinessLogicException('Bu talep kabul edilmemiş')
        
        # Check if driver is the one who accepted
        if request_obj.accepted_by_id != driver_id:
            raise ForbiddenException('Bu talebi siz kabul etmediniz')
        
        # Store old values for audit
        old_values = request_obj.to_dict()
        
        # Update request
        request_obj.completed_at = datetime.utcnow()
        request_obj.status = RequestStatus.COMPLETED
        if notes:
            request_obj.notes = (request_obj.notes or '') + '\n' + notes
        
        # Calculate completion time
        if request_obj.accepted_at:
            delta = request_obj.completed_at - request_obj.accepted_at
            request_obj.completion_time = int(delta.total_seconds())
        
        # Update buggy status to available
        if request_obj.buggy:
            request_obj.buggy.status = BuggyStatus.AVAILABLE
            
            # Update buggy's current location if provided
            if current_location_id:
                # Validate location exists and belongs to same hotel
                location = Location.query.get(current_location_id)
                if not location:
                    raise ResourceNotFoundException('Location', current_location_id)
                
                if location.hotel_id != request_obj.hotel_id:
                    raise ValidationException('Lokasyon farklı bir otele ait')
                
                request_obj.buggy.current_location_id = current_location_id
        
        db.session.commit()
        
        # Log completion
        AuditService.log_update(
            entity_type='request',
            entity_id=request_obj.id,
            old_values=old_values,
            new_values=request_obj.to_dict(),
            user_id=driver_id,
            hotel_id=request_obj.hotel_id
        )
        
        # Guest'e FCM bildirimi gönder - Socket.IO kaldırıldı
        try:
            from app.routes.guest_notification_api import GUEST_FCM_TOKENS, send_fcm_http_notification
            
            token_data = GUEST_FCM_TOKENS.get(request_id)
            if token_data:
                message_data = {
                    'title': '✅ Shuttle Ulaştı!',
                    'body': 'Shuttle\'ınız hedefe ulaştı. İyi yolculuklar!'
                }
                
                # Direkt FCM gönder
                send_fcm_http_notification(token_data['token'], message_data, 'completed')
                logger.info(f"✅ Guest tamamlanma FCM bildirimi gönderildi - Request ID: {request_id}")
            else:
                logger.info(f"ℹ️ Guest FCM token bulunamadı - Request ID: {request_id}")
                
        except Exception as e:
            logger.error(f"❌ Guest tamamlanma FCM bildirim hatası: {str(e)}")
        
        # Buggy status güncellendi - Socket.IO kaldırıldı
        
        return request_obj
    
    @staticmethod
    def cancel_request(request_id, reason, cancelled_by_id=None):
        """
        Cancel a request
        
        Args:
            request_id: Request ID
            reason: Cancellation reason
            cancelled_by_id: User ID who cancelled (optional)
        
        Returns:
            Updated request
        
        Raises:
            ResourceNotFoundException: If request not found
            BusinessLogicException: If request already completed
        """
        # Get request
        request_obj = BuggyRequest.query.get(request_id)
        if not request_obj:
            raise ResourceNotFoundException('Request', request_id)
        
        # Check if request can be cancelled
        if request_obj.status == RequestStatus.COMPLETED:
            raise BusinessLogicException('Tamamlanmış talep iptal edilemez')
        
        if request_obj.status == RequestStatus.CANCELLED:
            raise BusinessLogicException('Bu talep zaten iptal edilmiş')
        
        # Store old values for audit
        old_values = request_obj.to_dict()
        
        # Update request
        request_obj.cancelled_at = datetime.utcnow()
        request_obj.status = RequestStatus.CANCELLED
        request_obj.cancelled_by = cancelled_by_id
        request_obj.notes = (request_obj.notes or '') + f'\nİptal nedeni: {reason}'
        
        # If buggy was assigned, make it available again
        if request_obj.buggy and request_obj.buggy.status == BuggyStatus.BUSY:
            request_obj.buggy.status = BuggyStatus.AVAILABLE
        
        db.session.commit()
        
        # Log cancellation
        AuditService.log_update(
            entity_type='request',
            entity_id=request_obj.id,
            old_values=old_values,
            new_values=request_obj.to_dict(),
            user_id=cancelled_by_id,
            hotel_id=request_obj.hotel_id
        )
        
        # Notify relevant parties
        socketio.emit('request_cancelled', {
            'request': request_obj.to_dict(),
            'reason': reason
        }, room=f'request_{request_id}')
        
        socketio.emit('request_status_changed', {
            'request': request_obj.to_dict()
        }, room=f'hotel_{request_obj.hotel_id}_admin')
        
        return request_obj
    
    @staticmethod
    def get_requests(hotel_id, status=None, location_id=None, buggy_id=None,
                    date_from=None, date_to=None, page=1, per_page=50):
        """
        Get requests with filters
        
        Args:
            hotel_id: Hotel ID
            status: Filter by status (optional)
            location_id: Filter by location (optional)
            buggy_id: Filter by buggy (optional)
            date_from: Filter from date (optional)
            date_to: Filter to date (optional)
            page: Page number
            per_page: Items per page
        
        Returns:
            Paginated requests
        """
        query = BuggyRequest.query.filter_by(hotel_id=hotel_id)
        
        if status:
            query = query.filter_by(status=RequestStatus[status.upper()])
        
        if location_id:
            query = query.filter_by(location_id=location_id)
        
        if buggy_id:
            query = query.filter_by(buggy_id=buggy_id)
        
        if date_from:
            query = query.filter(BuggyRequest.requested_at >= date_from)
        
        if date_to:
            query = query.filter(BuggyRequest.requested_at <= date_to)
        
        query = query.order_by(BuggyRequest.requested_at.desc())
        
        return Pagination.paginate(query, page, per_page)
    
    @staticmethod
    def get_request(request_id):
        """
        Get request by ID
        
        Args:
            request_id: Request ID
        
        Returns:
            Request object
        
        Raises:
            ResourceNotFoundException: If request not found
        """
        request_obj = BuggyRequest.query.get(request_id)
        if not request_obj:
            raise ResourceNotFoundException('Request', request_id)
        return request_obj
    
    @staticmethod
    def get_PENDING_requests(hotel_id):
        """
        Get all PENDING requests for a hotel
        
        Args:
            hotel_id: Hotel ID
        
        Returns:
            List of PENDING requests
        """
        return BuggyRequest.query.filter_by(
            hotel_id=hotel_id,
            status=RequestStatus.PENDING
        ).order_by(BuggyRequest.requested_at).all()
    
    @staticmethod
    def get_driver_active_request(driver_id):
        """
        Get driver's active request
        
        Args:
            driver_id: Driver ID
        
        Returns:
            Active request or None
        """
        return BuggyRequest.query.filter_by(
            accepted_by_id=driver_id,
            status=RequestStatus.ACCEPTED
        ).first()
