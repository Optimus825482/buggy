"""
Unit tests for enhanced location deletion logic
Tests Requirements: 1.1, 1.2, 1.3, 1.4, 2.1, 2.2, 3.2, 3.3, 4.1, 4.2
"""
import pytest
import uuid
from unittest.mock import patch, MagicMock
from app import db
from app.models.location import Location
from app.models.buggy import Buggy, BuggyStatus
from app.models.buggy_driver import BuggyDriver
from app.models.audit import AuditTrail
from app.models.request import BuggyRequest, RequestStatus
from app.services.location_service import LocationService
from app.utils.exceptions import ResourceNotFoundException, ValidationException


class TestLocationDeletion:
    """Test suite for enhanced location deletion logic"""
    
    @patch('app.services.location_service.QRCodeService.delete_qr_code', create=True)
    def test_delete_location_with_inactive_buggies(self, mock_delete_qr, db_session, sample_hotel, sample_location, sample_driver_user):
        """
        Test: delete_location_with_inactive_buggies
        Verify location deleted and buggies' current_location_id set to NULL
        Requirements: 1.3, 1.4, 2.2, 3.1
        """
        # Create 2 inactive buggies at the location (no active driver sessions)
        buggy1 = Buggy(
            hotel_id=sample_hotel.id,
            code=f'BUGGY-{uuid.uuid4().hex[:8]}',
            current_location_id=sample_location.id,
            status=BuggyStatus.OFFLINE
        )
        buggy2 = Buggy(
            hotel_id=sample_hotel.id,
            code=f'BUGGY-{uuid.uuid4().hex[:8]}',
            current_location_id=sample_location.id,
            status=BuggyStatus.AVAILABLE
        )
        db_session.add_all([buggy1, buggy2])
        db_session.commit()
        
        buggy1_id = buggy1.id
        buggy2_id = buggy2.id
        location_id = sample_location.id
        
        # Delete location
        LocationService.delete_location(location_id)
        
        # Verify location is deleted
        deleted_location = Location.query.get(location_id)
        assert deleted_location is None
        
        # Verify buggies' current_location_id is set to NULL
        buggy1_after = Buggy.query.get(buggy1_id)
        buggy2_after = Buggy.query.get(buggy2_id)
        assert buggy1_after.current_location_id is None
        assert buggy2_after.current_location_id is None
        
        # Verify QR code deletion was called
        mock_delete_qr.assert_called_once_with(location_id)
    
    def test_delete_location_blocked_by_active_buggy(self, db_session, sample_hotel, sample_location, sample_driver_user):
        """
        Test: delete_location_blocked_by_active_buggy
        Verify ValidationException raised when active session exists
        Requirements: 1.1, 1.2, 2.1
        """
        # Create buggy at the location
        buggy = Buggy(
            hotel_id=sample_hotel.id,
            code=f'BUGGY-{uuid.uuid4().hex[:8]}',
            current_location_id=sample_location.id,
            status=BuggyStatus.AVAILABLE
        )
        db_session.add(buggy)
        db_session.commit()
        
        # Create active driver session
        driver_session = BuggyDriver(
            buggy_id=buggy.id,
            driver_id=sample_driver_user.id,
            is_active=True
        )
        db_session.add(driver_session)
        db_session.commit()
        
        location_id = sample_location.id
        
        # Attempt to delete location - should raise ValidationException
        with pytest.raises(ValidationException) as exc_info:
            LocationService.delete_location(location_id)
        
        # Verify error message
        error_message = exc_info.value.message
        assert '1 aktif buggy bulunuyor' in error_message
        assert 'Sürücüler oturumu kapatana' in error_message
        
        # Verify location still exists
        location_after = Location.query.get(location_id)
        assert location_after is not None
        
        # Verify buggy location unchanged
        buggy_after = Buggy.query.get(buggy.id)
        assert buggy_after.current_location_id == location_id
    
    def test_delete_location_mixed_buggies(self, db_session, sample_hotel, sample_location, sample_driver_user):
        """
        Test: delete_location_mixed_buggies
        Verify blocked when mix of active and inactive buggies
        Requirements: 1.1, 1.2, 2.1, 2.4
        """
        # Create 1 active buggy
        active_buggy = Buggy(
            hotel_id=sample_hotel.id,
            code=f'BUGGY-{uuid.uuid4().hex[:8]}',
            current_location_id=sample_location.id,
            status=BuggyStatus.AVAILABLE
        )
        db_session.add(active_buggy)
        db_session.commit()
        
        # Create active driver session for first buggy
        active_session = BuggyDriver(
            buggy_id=active_buggy.id,
            driver_id=sample_driver_user.id,
            is_active=True
        )
        db_session.add(active_session)
        
        # Create 2 inactive buggies
        inactive_buggy1 = Buggy(
            hotel_id=sample_hotel.id,
            code=f'BUGGY-{uuid.uuid4().hex[:8]}',
            current_location_id=sample_location.id,
            status=BuggyStatus.OFFLINE
        )
        inactive_buggy2 = Buggy(
            hotel_id=sample_hotel.id,
            code=f'BUGGY-{uuid.uuid4().hex[:8]}',
            current_location_id=sample_location.id,
            status=BuggyStatus.AVAILABLE
        )
        db_session.add_all([inactive_buggy1, inactive_buggy2])
        db_session.commit()
        
        location_id = sample_location.id
        
        # Attempt to delete location - should raise ValidationException
        with pytest.raises(ValidationException) as exc_info:
            LocationService.delete_location(location_id)
        
        # Verify error message mentions active buggy
        error_message = exc_info.value.message
        assert '1 aktif buggy bulunuyor' in error_message
        
        # Verify location still exists
        location_after = Location.query.get(location_id)
        assert location_after is not None
        
        # Verify all buggies' locations unchanged
        active_after = Buggy.query.get(active_buggy.id)
        inactive1_after = Buggy.query.get(inactive_buggy1.id)
        inactive2_after = Buggy.query.get(inactive_buggy2.id)
        assert active_after.current_location_id == location_id
        assert inactive1_after.current_location_id == location_id
        assert inactive2_after.current_location_id == location_id
    
    @patch('app.services.location_service.QRCodeService.delete_qr_code', create=True)
    def test_delete_location_no_buggies(self, mock_delete_qr, db_session, sample_hotel, sample_location):
        """
        Test: delete_location_no_buggies
        Verify successful deletion when no buggies present
        Requirements: 1.3
        """
        location_id = sample_location.id
        
        # Delete location (no buggies at this location)
        LocationService.delete_location(location_id)
        
        # Verify location is deleted
        deleted_location = Location.query.get(location_id)
        assert deleted_location is None
        
        # Verify QR code deletion was called
        mock_delete_qr.assert_called_once_with(location_id)
    
    @patch('app.services.location_service.QRCodeService.delete_qr_code', create=True)
    @patch('app.services.location_service.AuditService.log_delete')
    @patch('app.services.location_service.AuditService.log_action')
    def test_delete_location_audit_trail(self, mock_log_action, mock_log_delete, mock_delete_qr, db_session, sample_hotel, sample_location, sample_admin_user):
        """
        Test: delete_location_audit_trail
        Verify audit log contains affected buggy information
        Requirements: 4.1, 4.2
        """
        # Create 3 inactive buggies at the location
        buggies = []
        for i in range(3):
            buggy = Buggy(
                hotel_id=sample_hotel.id,
                code=f'BUGGY-{uuid.uuid4().hex[:8]}',
                current_location_id=sample_location.id,
                status=BuggyStatus.OFFLINE
            )
            buggies.append(buggy)
            db_session.add(buggy)
        db_session.commit()
        
        buggy_ids = [b.id for b in buggies]
        location_id = sample_location.id
        
        # Delete location
        LocationService.delete_location(location_id)
        
        # Verify location is deleted
        deleted_location = Location.query.get(location_id)
        assert deleted_location is None
        
        # Verify audit logging was called for deletion
        mock_log_delete.assert_called_once()
        delete_call_args = mock_log_delete.call_args
        assert delete_call_args[1]['entity_type'] == 'location'
        assert delete_call_args[1]['entity_id'] == location_id
        assert delete_call_args[1]['hotel_id'] == sample_hotel.id
        
        # Verify additional audit log for affected buggies was called
        mock_log_action.assert_called_once()
        action_call_args = mock_log_action.call_args
        assert action_call_args[1]['action'] == 'location_deleted_with_buggies'
        assert action_call_args[1]['entity_type'] == 'location'
        assert action_call_args[1]['entity_id'] == location_id
        assert action_call_args[1]['hotel_id'] == sample_hotel.id
        
        # Verify affected buggy information
        new_values = action_call_args[1]['new_values']
        assert new_values['affected_buggies_count'] == 3
        assert set(new_values['affected_buggy_ids']) == set(buggy_ids)
    
    @patch('app.services.location_service.QRCodeService.delete_qr_code', create=True)
    def test_delete_location_transaction_rollback(self, mock_delete_qr, db_session, sample_hotel, sample_location, monkeypatch):
        """
        Test: delete_location_transaction_rollback
        Verify rollback on database error
        Requirements: 3.2, 3.3
        """
        # Create inactive buggy at the location
        buggy = Buggy(
            hotel_id=sample_hotel.id,
            code=f'BUGGY-{uuid.uuid4().hex[:8]}',
            current_location_id=sample_location.id,
            status=BuggyStatus.OFFLINE
        )
        db_session.add(buggy)
        db_session.commit()
        
        location_id = sample_location.id
        buggy_id = buggy.id
        
        # Mock db.session.commit to raise an exception
        original_commit = db.session.commit
        def mock_commit():
            raise Exception("Database error")
        
        monkeypatch.setattr(db.session, 'commit', mock_commit)
        
        # Attempt to delete location - should raise exception
        with pytest.raises(Exception) as exc_info:
            LocationService.delete_location(location_id)
        
        assert "Database error" in str(exc_info.value)
        
        # Restore original commit
        monkeypatch.setattr(db.session, 'commit', original_commit)
        
        # Rollback the failed transaction
        db_session.rollback()
        
        # Verify location still exists (transaction rolled back)
        location_after = Location.query.get(location_id)
        assert location_after is not None
        
        # Verify buggy location unchanged (transaction rolled back)
        buggy_after = Buggy.query.get(buggy_id)
        assert buggy_after.current_location_id == location_id
    
    def test_delete_location_with_active_requests(self, db_session, sample_hotel, sample_location):
        """
        Test: Verify deletion blocked when active requests exist
        Requirements: 1.1
        """
        # Create active request at the location
        request = BuggyRequest(
            hotel_id=sample_hotel.id,
            location_id=sample_location.id,
            guest_name="Test Guest",
            room_number="101",
            status=RequestStatus.PENDING
        )
        db_session.add(request)
        db_session.commit()
        
        location_id = sample_location.id
        
        # Attempt to delete location - should raise ValidationException
        with pytest.raises(ValidationException) as exc_info:
            LocationService.delete_location(location_id)
        
        # Verify error message about active requests
        error_message = exc_info.value.message
        assert '1 aktif talep var' in error_message
        assert 'talepleri tamamlayın veya iptal edin' in error_message
        
        # Verify location still exists
        location_after = Location.query.get(location_id)
        assert location_after is not None
    
    def test_delete_location_not_found(self, db_session):
        """
        Test: Verify ResourceNotFoundException for non-existent location
        Requirements: 1.1
        """
        non_existent_id = 99999
        
        # Attempt to delete non-existent location
        with pytest.raises(ResourceNotFoundException) as exc_info:
            LocationService.delete_location(non_existent_id)
        
        assert 'Location' in exc_info.value.message
    
    @patch('app.services.location_service.QRCodeService.delete_qr_code', create=True)
    def test_delete_location_inactive_session_not_blocking(self, mock_delete_qr, db_session, sample_hotel, sample_location, sample_driver_user):
        """
        Test: Verify inactive driver sessions don't block deletion
        Requirements: 2.1, 2.2
        """
        # Create buggy at the location
        buggy = Buggy(
            hotel_id=sample_hotel.id,
            code=f'BUGGY-{uuid.uuid4().hex[:8]}',
            current_location_id=sample_location.id,
            status=BuggyStatus.OFFLINE
        )
        db_session.add(buggy)
        db_session.commit()
        
        # Create INACTIVE driver session (is_active=False)
        inactive_session = BuggyDriver(
            buggy_id=buggy.id,
            driver_id=sample_driver_user.id,
            is_active=False
        )
        db_session.add(inactive_session)
        db_session.commit()
        
        location_id = sample_location.id
        buggy_id = buggy.id
        
        # Delete location - should succeed
        LocationService.delete_location(location_id)
        
        # Verify location is deleted
        deleted_location = Location.query.get(location_id)
        assert deleted_location is None
        
        # Verify buggy's current_location_id is set to NULL
        buggy_after = Buggy.query.get(buggy_id)
        assert buggy_after.current_location_id is None
        
        # Verify QR code deletion was called
        mock_delete_qr.assert_called_once_with(location_id)
