"""
Buggy Call - Request Service
Enhanced with accurate timestamp management and timezone handling
Performance optimized with monitoring and eager loading
Comprehensive logging for request lifecycle
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
from app.utils.performance_monitor import PerformanceMonitor
from app.utils.logger import (
    logger, log_request_lifecycle, log_error, 
    RequestLifecycleLogger, log_fcm_event
)
from datetime import datetime, timezone
import logging
import pytz


def get_utc_now():
    """
    Get current UTC timestamp
    Ensures consistent timezone handling across the application

    Returns:
        datetime: Current UTC datetime
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)


def get_cyprus_now():
    """
    Get current Cyprus timezone timestamp (UTC+2/UTC+3)
    Cyprus uses Europe/Nicosia timezone (EET/EEST)

    Returns:
        datetime: Current Cyprus datetime (timezone-naive for DB storage)
    """
    cyprus_tz = pytz.timezone('Europe/Nicosia')  # Cyprus timezone
    cyprus_time = datetime.now(cyprus_tz)
    return cyprus_time.replace(tzinfo=None)  # Remove timezone info for DB storage


def format_cyprus_datetime(dt):
    """
    Format datetime as ISO string with Cyprus timezone indicator
    
    Args:
        dt: timezone-naive datetime (stored as Cyprus time in DB)
    
    Returns:
        str: ISO format string with +02:00 or +03:00 offset
    """
    if not dt:
        return None
    
    cyprus_tz = pytz.timezone('Europe/Nicosia')
    # Localize the naive datetime to Cyprus timezone
    cyprus_dt = cyprus_tz.localize(dt)
    # Return ISO format with timezone info
    return cyprus_dt.isoformat()


class RequestService:
    """Service for buggy request management"""
    
    @staticmethod
    def create_request(location_id, room_number=None, guest_name=None, 
                      phone=None, has_room=True, notes=None):
        """
        Create new buggy request (Guest)
        
        Args:
            location_id: Location ID
            room_number: Room number (optional if has_room=False)
            guest_name: Guest name (optional)
            phone: Phone number (optional)
            has_room: Whether guest has a room
            notes: Additional notes (optional)
        
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
            log_error('REQUEST_CREATE', f'Location not found: {location_id}', {
                'location_id': location_id
            })
            raise ResourceNotFoundException('Location', location_id)
        
        if not location.is_active:
            log_error('REQUEST_CREATE', 'Location not active', {
                'location_id': location_id,
                'location_name': location.name
            })
            raise ValidationException('Bu lokasyon şu anda aktif değil')
        
        # Validate room number if has_room is True
        if has_room and not room_number:
            log_error('REQUEST_CREATE', 'Room number required but not provided', {
                'location_id': location_id,
                'has_room': has_room
            })
            raise ValidationException('Oda numarası gereklidir')
        
        # Check if there are any available buggies
        available_buggies = Buggy.query.filter_by(
            hotel_id=location.hotel_id,
            status=BuggyStatus.AVAILABLE
        ).count()
        
        if available_buggies == 0:
            log_error('REQUEST_CREATE', 'No available buggies', {
                'hotel_id': location.hotel_id,
                'location_id': location_id
            })
            raise BusinessLogicException(
                'Şu anda müsait buggy bulunmamaktadır. Lütfen daha sonra tekrar deneyin.'
            )
        
        # Create request with Cyprus timezone timestamp
        current_time = get_cyprus_now()
        
        # ✅ DEBUG: Log the timestamp being saved
        import pytz
        from datetime import datetime
        utc_now = datetime.now(pytz.UTC)
        logger.info(f'🕐 [TIMEZONE_DEBUG] UTC now: {utc_now}')
        logger.info(f'🕐 [TIMEZONE_DEBUG] Cyprus now (from get_cyprus_now): {current_time}')
        logger.info(f'🕐 [TIMEZONE_DEBUG] Difference: {(current_time.replace(tzinfo=pytz.UTC) - utc_now).total_seconds() / 3600} hours')
        
        request_obj = BuggyRequest(
            hotel_id=location.hotel_id,
            location_id=location_id,
            room_number=room_number,
            guest_name=guest_name,
            phone=phone,
            has_room=has_room,
            notes=notes,
            status=RequestStatus.PENDING,
            requested_at=current_time  # ✅ Cyprus timezone (timezone-naive for DB)
        )
        
        db.session.add(request_obj)
        db.session.commit()
        
        # Comprehensive logging
        log_request_lifecycle('CREATED', request_obj.id, {
            'hotel_id': location.hotel_id,
            'location_id': location_id,
            'location_name': location.name,
            'room_number': room_number,
            'guest_name': guest_name,
            'has_room': has_room,
            'available_buggies': available_buggies,
            'requested_at': current_time.isoformat()
        })
        
        logger.info(f"✅ Request created: ID={request_obj.id}, requested_at={request_obj.requested_at.isoformat()}")
        
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
        # Get request with row-level lock (race condition prevention)
        request_obj = BuggyRequest.query.filter_by(id=request_id).with_for_update().first()
        if not request_obj:
            raise ResourceNotFoundException('Request', request_id)
        
        # Check if request is still PENDING
        if request_obj.status != RequestStatus.PENDING:
            raise BusinessLogicException('Bu talep zaten işleme alınmış')
        
        # Get buggy
        buggy = Buggy.query.get(buggy_id)
        if not buggy:
            raise ResourceNotFoundException('Buggy', buggy_id)
        
        # Check if driver is assigned to this buggy (via BuggyDriver association)
        from app.models.buggy_driver import BuggyDriver
        is_assigned = BuggyDriver.query.filter_by(
            buggy_id=buggy_id,
            driver_id=driver_id,
            is_active=True
        ).first() is not None
        if not is_assigned:
            raise ForbiddenException('Bu buggy size atanmamış')
        
        # Check if buggy is available
        if buggy.status != BuggyStatus.AVAILABLE:
            raise BusinessLogicException('Bu buggy şu anda müsait değil')
        
        # Check if buggy belongs to same hotel
        if buggy.hotel_id != request_obj.hotel_id:
            raise ValidationException('Buggy farklı bir otele ait')
        
        # Store old values for audit
        old_values = request_obj.to_dict()
        
        # Update request with Cyprus timezone timestamp
        current_time = get_cyprus_now()
        request_obj.buggy_id = buggy_id
        request_obj.accepted_by_id = driver_id
        request_obj.accepted_at = current_time
        request_obj.status = RequestStatus.ACCEPTED
        
        # Calculate response time (seconds from request to acceptance)
        if request_obj.requested_at:
            delta = request_obj.accepted_at - request_obj.requested_at
            request_obj.response_time = int(delta.total_seconds())
            logger.info(f"📊 Response time calculated: {request_obj.response_time}s for request {request_id}")
        else:
            logger.warning(f"⚠️ requested_at is None for request {request_id}, cannot calculate response_time")
        
        # Update buggy status
        buggy.status = BuggyStatus.BUSY
        
        db.session.commit()
        
        # Comprehensive logging
        log_request_lifecycle('ACCEPTED', request_id, {
            'driver_id': driver_id,
            'buggy_id': buggy_id,
            'buggy_code': buggy.code,
            'response_time_seconds': request_obj.response_time,
            'accepted_at': request_obj.accepted_at.isoformat(),
            'hotel_id': request_obj.hotel_id
        })
        
        logger.info(f"✅ Request accepted: ID={request_id}, accepted_at={request_obj.accepted_at.isoformat()}, response_time={request_obj.response_time}s")
        
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
            from app.routes.guest_notification_api import get_guest_token, send_fcm_http_notification

            guest_token = get_guest_token(request_id)
            if guest_token:
                message_data = {
                    'title': '🎉 Shuttle Kabul Edildi!',
                    'body': f'Shuttle size doğru geliyor. Buggy: {buggy.code}'
                }

                # Direkt FCM gönder - request_id ve type ekle
                success, fcm_message = send_fcm_http_notification(
                    guest_token, 
                    message_data, 
                    'accepted', 
                    request_id=request_id
                )
                
                if success:
                    logger.info(f"✅ Guest FCM bildirimi gönderildi - Request ID: {request_id}")
                    log_fcm_event('GUEST_NOTIFIED', request_id, {
                        'type': 'accepted',
                        'buggy_code': buggy.code,
                        'driver_id': driver_id
                    })
                else:
                    logger.warning(f"⚠️ Guest FCM bildirimi gönderilemedi - Request ID: {request_id}")
            else:
                logger.info(f"ℹ️ Guest FCM token bulunamadı - Request ID: {request_id}")
                
        except Exception as e:
            import traceback
            logger.error(f"❌ Guest FCM bildirim hatası: {str(e)}")
            logger.error(traceback.format_exc())
        
        # WebSocket: Notify guest and dashboards
        try:
            # Broadcast to all
            socketio.emit('request_accepted', {
                'request_id': request_id,
                'buggy_code': buggy.code,
                'driver_name': request_obj.accepted_by_driver.full_name if request_obj.accepted_by_driver else 'Sürücü',
                'hotel_id': request_obj.hotel_id
            })
            
            # Notify guest room specifically
            guest_room = f'request_{request_id}'
            socketio.emit('request_accepted', {
                'request_id': request_id,
                'buggy_code': buggy.code,
                'driver_name': request_obj.accepted_by_driver.full_name if request_obj.accepted_by_driver else 'Sürücü',
                'hotel_id': request_obj.hotel_id
            }, room=guest_room)
            
            # Notify admin room
            admin_room = f'hotel_{request_obj.hotel_id}_admin'
            socketio.emit('request_accepted', {
                'request_id': request_id,
                'buggy_code': buggy.code,
                'driver_name': request_obj.accepted_by_driver.full_name if request_obj.accepted_by_driver else 'Sürücü',
                'hotel_id': request_obj.hotel_id
            }, room=admin_room)
            
            logger.info(f"📡 WebSocket: request_accepted emitted for request {request_id} to all rooms")
        except Exception as e:
            import traceback
            logger.error(f"❌ WebSocket emit hatası: {str(e)}")
            logger.error(traceback.format_exc())
        
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
        
        # Update request with Cyprus timezone timestamp
        current_time = get_cyprus_now()
        request_obj.completed_at = current_time
        request_obj.status = RequestStatus.COMPLETED
        if notes:
            request_obj.notes = (request_obj.notes or '') + '\n' + notes
        
        # Calculate completion time (seconds from REQUEST to completion - TOPLAM SÜRE)
        if request_obj.requested_at:
            delta = request_obj.completed_at - request_obj.requested_at
            request_obj.completion_time = int(delta.total_seconds())
            logger.info(f"📊 Completion time calculated (requested_at -> completed_at): {request_obj.completion_time}s for request {request_id}")
        else:
            logger.warning(f"⚠️ requested_at is None for request {request_id}, cannot calculate completion_time")
        
        # Update buggy status to available
        if request_obj.buggy:
            request_obj.buggy.status = BuggyStatus.AVAILABLE
            logger.info(f"✅ Buggy {request_obj.buggy.code} status set to AVAILABLE")
            
            # Update buggy's current location if provided
            if current_location_id:
                # Validate location exists and belongs to same hotel
                location = Location.query.get(current_location_id)
                if not location:
                    raise ResourceNotFoundException('Location', current_location_id)
                
                if location.hotel_id != request_obj.hotel_id:
                    raise ValidationException('Lokasyon farklı bir otele ait')
                
                request_obj.buggy.current_location_id = current_location_id
                logger.info(f"📍 Buggy {request_obj.buggy.code} location updated to {location.name}")
        
        db.session.commit()
        
        # Comprehensive logging
        log_request_lifecycle('COMPLETED', request_id, {
            'driver_id': driver_id,
            'buggy_id': request_obj.buggy_id,
            'buggy_code': request_obj.buggy.code if request_obj.buggy else None,
            'completion_time_seconds': request_obj.completion_time,
            'completed_at': request_obj.completed_at.isoformat(),
            'current_location_id': current_location_id,
            'hotel_id': request_obj.hotel_id
        })
        
        logger.info(f"✅ Request completed: ID={request_id}, completed_at={request_obj.completed_at.isoformat()}, completion_time={request_obj.completion_time}s")
        
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
            from app.routes.guest_notification_api import get_guest_token, send_fcm_http_notification

            guest_token = get_guest_token(request_id)
            if guest_token:
                message_data = {
                    'title': '✅ Shuttle Ulaştı!',
                    'body': 'Shuttle\'ınız hedefe ulaştı. İyi yolculuklar!'
                }

                # Direkt FCM gönder - request_id ekle
                send_fcm_http_notification(guest_token, message_data, 'completed', request_id=request_id)
                logger.info(f"✅ Guest tamamlanma FCM bildirimi gönderildi - Request ID: {request_id}")
            else:
                logger.info(f"ℹ️ Guest FCM token bulunamadı - Request ID: {request_id}")
                
        except Exception as e:
            logger.error(f"❌ Guest tamamlanma FCM bildirim hatası: {str(e)}")
        
        # WebSocket: Notify guest, drivers and dashboards
        try:
            event_data = {
                'request_id': request_id,
                'hotel_id': request_obj.hotel_id,
                'buggy_id': request_obj.buggy_id,
                'location_id': current_location_id
            }
            
            # Broadcast to all
            socketio.emit('request_completed', event_data)
            
            # Notify drivers room specifically
            drivers_room = f'hotel_{request_obj.hotel_id}_drivers'
            socketio.emit('request_completed', event_data, room=drivers_room)
            
            # Notify admin room
            admin_room = f'hotel_{request_obj.hotel_id}_admin'
            socketio.emit('request_completed', event_data, room=admin_room)
            
            logger.info(f"📡 WebSocket: request_completed emitted for request {request_id} to all rooms")
        except Exception as e:
            logger.error(f"❌ WebSocket emit hatası: {str(e)}")
        
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
        
        # Update request with UTC timestamp
        request_obj.cancelled_at = get_utc_now()
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
    @PerformanceMonitor.track('get_requests')
    def get_requests(hotel_id, status=None, location_id=None, buggy_id=None,
                    date_from=None, date_to=None, page=1, per_page=50):
        """
        Get requests with filters (optimized with eager loading)
        
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
        from sqlalchemy.orm import joinedload
        
        # Eager load related entities to avoid N+1 queries
        query = BuggyRequest.query.options(
            joinedload(BuggyRequest.location),
            joinedload(BuggyRequest.buggy),
            joinedload(BuggyRequest.accepted_by_driver)
        ).filter_by(hotel_id=hotel_id)
        
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
    @PerformanceMonitor.track('get_pending_requests')
    def get_PENDING_requests(hotel_id):
        """
        Get all PENDING requests for a hotel (optimized with eager loading)
        
        Args:
            hotel_id: Hotel ID
        
        Returns:
            List of PENDING requests
        """
        from sqlalchemy.orm import joinedload
        
        # Eager load related entities to avoid N+1 queries
        # Limit to 50 to prevent performance issues
        return BuggyRequest.query.options(
            joinedload(BuggyRequest.location),
            joinedload(BuggyRequest.buggy)
        ).filter_by(
            hotel_id=hotel_id,
            status=RequestStatus.PENDING
        ).order_by(BuggyRequest.requested_at).limit(50).all()
    
    @staticmethod
    @PerformanceMonitor.track('get_driver_active_request')
    def get_driver_active_request(driver_id):
        """
        Get driver's active request (optimized with eager loading)
        
        Args:
            driver_id: Driver ID
        
        Returns:
            Active request or None
        """
        from sqlalchemy.orm import joinedload
        
        # Eager load related entities to avoid N+1 queries
        return BuggyRequest.query.options(
            joinedload(BuggyRequest.location),
            joinedload(BuggyRequest.buggy)
        ).filter_by(
            accepted_by_id=driver_id,
            status=RequestStatus.ACCEPTED
        ).first()
