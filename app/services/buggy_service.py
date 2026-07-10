"""
Buggy Call - Buggy Service
Updated: deprecated driver_id removed, BuggyDriver association used
"""
from app import db, socketio
from app.models.buggy import Buggy, BuggyStatus
from app.models.buggy_driver import BuggyDriver
from app.models.user import SystemUser, UserRole
from app.models.hotel import Hotel
from app.models.location import Location
from app.services.audit_service import AuditService
from app.utils.exceptions import ResourceNotFoundException, ValidationException, BusinessLogicException
from app.utils.helpers import Pagination
from app.utils.buggy_icons import assign_buggy_icon
from datetime import datetime


class BuggyService:
    """Service for buggy management"""

    @staticmethod
    def get_all_buggies(hotel_id, status=None, page=1, per_page=50):
        query = Buggy.query.filter_by(hotel_id=hotel_id)
        if status:
            query = query.filter_by(status=BuggyStatus[status.upper()])
        query = query.order_by(Buggy.code)
        return Pagination.paginate(query, page, per_page)

    @staticmethod
    def get_buggy(buggy_id):
        buggy = Buggy.query.get(buggy_id)
        if not buggy:
            raise ResourceNotFoundException('Buggy', buggy_id)
        return buggy

    @staticmethod
    def get_available_buggies(hotel_id):
        return Buggy.query.filter_by(
            hotel_id=hotel_id, status=BuggyStatus.AVAILABLE
        ).all()

    @staticmethod
    def create_buggy(hotel_id, code, model=None, license_plate=None,
                    icon=None, driver_id=None):
        hotel = Hotel.query.get(hotel_id)
        if not hotel:
            raise ResourceNotFoundException('Hotel', hotel_id)

        existing = Buggy.query.filter_by(hotel_id=hotel_id, code=code).first()
        if existing:
            raise ValidationException(f'Buggy kodu "{code}" bu otel icin zaten kullaniliyor')

        buggy_icon = icon or assign_buggy_icon(hotel_id)

        buggy = Buggy(
            hotel_id=hotel_id, code=code,
            model=model, license_plate=license_plate,
            icon=buggy_icon, status=BuggyStatus.OFFLINE
        )
        db.session.add(buggy)
        db.session.flush()

        if driver_id:
            driver = SystemUser.query.get(driver_id)
            if not driver or driver.role != UserRole.DRIVER:
                raise ValidationException('Gecersiz surucu')
            if driver.hotel_id != hotel_id:
                raise ValidationException('Surucu farkli bir otele ait')

            existing_assoc = BuggyDriver.query.filter_by(
                driver_id=driver_id, is_active=True
            ).first()
            if existing_assoc:
                raise ValidationException('Bu surucu zaten bir buggy\'ye atanmis')

            db.session.add(BuggyDriver(
                buggy_id=buggy.id, driver_id=driver_id,
                is_active=False, is_primary=True,
                assigned_at=datetime.utcnow()
            ))

        db.session.commit()
        AuditService.log_create(
            entity_type='buggy', entity_id=buggy.id,
            new_values=buggy.to_dict(), hotel_id=hotel_id
        )
        return buggy

    @staticmethod
    def update_buggy(buggy_id, **kwargs):
        buggy = Buggy.query.get(buggy_id)
        if not buggy:
            raise ResourceNotFoundException('Buggy', buggy_id)

        old_values = buggy.to_dict()

        if 'code' in kwargs and kwargs['code'] != buggy.code:
            existing = Buggy.query.filter_by(
                hotel_id=buggy.hotel_id, code=kwargs['code']
            ).first()
            if existing:
                raise ValidationException(f'Buggy kodu "{kwargs["code"]}" zaten kullaniliyor')

        if 'driver_id' in kwargs:
            new_driver_id = kwargs.pop('driver_id')
            current_driver_id = buggy.get_active_driver()
            if new_driver_id != current_driver_id:
                existing_primary = BuggyDriver.query.filter_by(
                    buggy_id=buggy_id, is_primary=True
                ).first()
                if existing_primary:
                    existing_primary.is_primary = False
                if new_driver_id:
                    driver = SystemUser.query.get(new_driver_id)
                    if not driver or driver.role != UserRole.DRIVER:
                        raise ValidationException('Gecersiz surucu')
                    assoc = BuggyDriver.query.filter_by(
                        buggy_id=buggy_id, driver_id=new_driver_id
                    ).first()
                    if assoc:
                        assoc.is_primary = True
                    else:
                        db.session.add(BuggyDriver(
                            buggy_id=buggy_id, driver_id=new_driver_id,
                            is_active=False, is_primary=True,
                            assigned_at=datetime.utcnow()
                        ))

        allowed_fields = ['code', 'icon', 'model', 'license_plate', 'status']
        for field in allowed_fields:
            if field in kwargs:
                if field == 'status' and isinstance(kwargs[field], str):
                    setattr(buggy, field, BuggyStatus[kwargs[field].upper()])
                else:
                    setattr(buggy, field, kwargs[field])

        db.session.commit()
        AuditService.log_update(
            entity_type='buggy', entity_id=buggy.id,
            old_values=old_values, new_values=buggy.to_dict(),
            hotel_id=buggy.hotel_id
        )
        return buggy

    @staticmethod
    def update_status(buggy_id, status, location_id=None):
        buggy = Buggy.query.get(buggy_id)
        if not buggy:
            raise ResourceNotFoundException('Buggy', buggy_id)

        old_status = buggy.status
        new_status = BuggyStatus[status.upper()] if isinstance(status, str) else status

        if old_status == BuggyStatus.BUSY and new_status == BuggyStatus.AVAILABLE:
            from app.models.request import BuggyRequest, RequestStatus
            if BuggyRequest.query.filter_by(
                buggy_id=buggy_id, status=RequestStatus.ACCEPTED
            ).first():
                raise BusinessLogicException('Buggy\'nin aktif talebi var. Once talebi tamamlayin.')

        buggy.status = new_status
        db.session.commit()
        AuditService.log_action(
            action='status_changed', entity_type='buggy', entity_id=buggy.id,
            old_values={'status': old_status.value},
            new_values={'status': new_status.value, 'location_id': location_id},
            hotel_id=buggy.hotel_id
        )
        return buggy

    @staticmethod
    def delete_buggy(buggy_id):
        buggy = Buggy.query.get(buggy_id)
        if not buggy:
            raise ResourceNotFoundException('Buggy', buggy_id)

        from app.models.request import BuggyRequest, RequestStatus
        active = BuggyRequest.query.filter(
            BuggyRequest.buggy_id == buggy_id,
            BuggyRequest.status.in_([RequestStatus.PENDING, RequestStatus.ACCEPTED])
        ).count()
        if active > 0:
            raise ValidationException(f'Bu buggy\'nin {active} aktif talebi var.')

        old_values = buggy.to_dict()
        hotel_id = buggy.hotel_id
        BuggyDriver.query.filter_by(buggy_id=buggy_id).delete()
        db.session.delete(buggy)
        db.session.commit()
        AuditService.log_delete(
            entity_type='buggy', entity_id=buggy_id,
            old_values=old_values, hotel_id=hotel_id
        )

    @staticmethod
    def get_buggy_by_driver(driver_id):
        """Get buggy assigned to a driver (via BuggyDriver)"""
        assoc = BuggyDriver.query.filter_by(
            driver_id=driver_id, is_active=True
        ).first()
        return assoc.buggy if assoc else None

    @staticmethod
    def update_location(buggy_id, location_id):
        buggy = Buggy.query.get(buggy_id)
        if not buggy:
            raise ResourceNotFoundException('Buggy', buggy_id)
        location = Location.query.get(location_id)
        if not location:
            raise ResourceNotFoundException('Location', location_id)
        if location.hotel_id != buggy.hotel_id:
            raise ValidationException('Lokasyon farkli bir otele ait')

        old_location_id = buggy.current_location_id
        old_location_name = buggy.current_location.name if buggy.current_location else None
        buggy.current_location_id = location_id
        buggy.status = BuggyStatus.AVAILABLE
        db.session.commit()

        AuditService.log_action(
            action='location_updated', entity_type='buggy', entity_id=buggy.id,
            old_values={'location_id': old_location_id, 'location_name': old_location_name},
            new_values={'location_id': location_id, 'location_name': location.name},
            hotel_id=buggy.hotel_id
        )
        return buggy

    @staticmethod
    def get_available_buggies_by_location(hotel_id, location_id=None):
        query = Buggy.query.filter_by(hotel_id=hotel_id, status=BuggyStatus.AVAILABLE)
        if location_id:
            query = query.filter_by(current_location_id=location_id)
        return [{
            **buggy.to_dict(),
            'current_location': {
                'id': buggy.current_location.id, 'name': buggy.current_location.name
            } if buggy.current_location else None
        } for buggy in query.all()]

    @staticmethod
    def emit_buggy_status_update(buggy_id, hotel_id):
        try:
            buggy = Buggy.query.get(buggy_id)
            if not buggy:
                return
            active = BuggyDriver.query.filter_by(buggy_id=buggy_id, is_active=True).first()
            driver_name = None
            if active:
                d = SystemUser.query.get(active.driver_id)
                driver_name = d.full_name or d.username if d else None
            status = 'offline'
            if active:
                from app.models.request import BuggyRequest, RequestStatus
                ar = BuggyRequest.query.filter_by(buggy_id=buggy_id, status=RequestStatus.ACCEPTED).first()
                status = 'busy' if ar else 'available'
            loc_name = buggy.current_location.name if buggy.current_location else None
            socketio.emit('buggy_status_update', {
                'buggy_id': buggy.id, 'buggy_code': buggy.code,
                'buggy_icon': buggy.icon, 'status': status,
                'driver_name': driver_name,
                'location_id': buggy.current_location_id, 'location_name': loc_name,
                'timestamp': datetime.utcnow().isoformat()
            }, room=f'hotel_{hotel_id}_admin')
        except Exception as e:
            print(f'Error emitting buggy status update: {e}')
