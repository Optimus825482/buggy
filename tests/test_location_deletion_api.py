"""
Integration tests for location deletion API endpoint
Tests Requirements: 1.1, 1.2, 1.3, 1.5, 4.3, 4.4
"""
import pytest
import uuid
from unittest.mock import patch
from app import db
from app.models.location import Location
from app.models.buggy import Buggy, BuggyStatus
from app.models.buggy_driver import BuggyDriver
from app.models.user import SystemUser, UserRole


class TestLocationDeletionAPI:
    """Integration test suite for location deletion API endpoint"""
    
    @patch('app.services.location_service.QRCodeService.delete_qr_code', create=True)
    def test_api_delete_location_with_inactive_buggies(self, mock_delete_qr, authenticated_admin_client, db_session, sample_hotel, sample_admin_user, sample_driver_user):
        """
        Test: api_delete_location_with_inactive_buggies
        Verify 200 response and location deleted with inactive buggies
        Requirements: 1.3, 1.4, 4.3
        """
        # Create location
        location = Location(
            hotel_id=sample_hotel.id,
            name=f'Test Location {uuid.uuid4().hex[:8]}',
            qr_code_data=f'QR-{uuid.uuid4().hex[:8]}',
            is_active=True
        )
        db_session.add(location)
        db_session.commit()
        
        # Create 2 inactive buggies at the location
        buggy1 = Buggy(
            hotel_id=sample_hotel.id,
            code=f'BUGGY-{uuid.uuid4().hex[:8]}',
            current_location_id=location.id,
            status=BuggyStatus.OFFLINE
        )
        buggy2 = Buggy(
            hotel_id=sample_hotel.id,
            code=f'BUGGY-{uuid.uuid4().hex[:8]}',
            current_location_id=location.id,
            status=BuggyStatus.AVAILABLE
        )
        db_session.add_all([buggy1, buggy2])
        db_session.commit()
        
        location_id = location.id
        buggy1_id = buggy1.id
        buggy2_id = buggy2.id
        
        # Delete location via API
        response = authenticated_admin_client.delete(f'/api/locations/{location_id}')
        
        # Verify response
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'başarıyla silindi' in data['message']
        
        # Verify location is deleted
        deleted_location = Location.query.get(location_id)
        assert deleted_location is None
        
        # Verify buggies' current_location_id is set to NULL
        buggy1_after = Buggy.query.get(buggy1_id)
        buggy2_after = Buggy.query.get(buggy2_id)
        assert buggy1_after.current_location_id is None
        assert buggy2_after.current_location_id is None
    
    @patch('app.services.location_service.QRCodeService.delete_qr_code', create=True)
    def test_api_delete_location_with_active_session(self, mock_delete_qr, authenticated_admin_client, db_session, sample_hotel, sample_admin_user, sample_driver_user):
        """
        Test: api_delete_location_with_active_session
        Verify 400 response with correct error message
        Requirements: 1.1, 1.2, 1.5, 4.4
        """
        # Create location
        location = Location(
            hotel_id=sample_hotel.id,
            name=f'Test Location {uuid.uuid4().hex[:8]}',
            qr_code_data=f'QR-{uuid.uuid4().hex[:8]}',
            is_active=True
        )
        db_session.add(location)
        db_session.commit()
        
        # Create buggy at the location
        buggy = Buggy(
            hotel_id=sample_hotel.id,
            code=f'BUGGY-{uuid.uuid4().hex[:8]}',
            current_location_id=location.id,
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
        
        location_id = location.id
        
        # Attempt to delete location via API
        response = authenticated_admin_client.delete(f'/api/locations/{location_id}')
        
        # Verify response
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        error_message = data['error']
        assert '1 aktif buggy bulunuyor' in error_message
        assert 'Sürücüler oturumu kapatana' in error_message
        
        # Verify location still exists
        location_after = Location.query.get(location_id)
        assert location_after is not None
        
        # Verify buggy location unchanged
        buggy_after = Buggy.query.get(buggy.id)
        assert buggy_after.current_location_id == location_id
    
    @patch('app.services.location_service.QRCodeService.delete_qr_code', create=True)
    def test_api_delete_location_authorization(self, mock_delete_qr, authenticated_admin_client, db_session, sample_hotel, sample_admin_user):
        """
        Test: api_delete_location_authorization
        Verify hotel isolation and authentication
        Requirements: 1.1, 4.3
        """
        # Create another hotel
        from app.models.hotel import Hotel
        other_hotel_obj = Hotel(
            name=f'Other Hotel {uuid.uuid4().hex[:8]}',
            address='456 Other Street',
            phone='555-9999',
            email=f'other{uuid.uuid4().hex[:8]}@hotel.com'
        )
        db_session.add(other_hotel_obj)
        db_session.commit()
        
        # Create location in other hotel
        location = Location(
            hotel_id=other_hotel_obj.id,
            name=f'Other Hotel Location {uuid.uuid4().hex[:8]}',
            qr_code_data=f'QR-{uuid.uuid4().hex[:8]}',
            is_active=True
        )
        db_session.add(location)
        db_session.commit()
        
        location_id = location.id
        
        # Attempt to delete location from other hotel
        response = authenticated_admin_client.delete(f'/api/locations/{location_id}')
        
        # Verify response - should be 404 (not found due to hotel isolation)
        assert response.status_code == 404
        data = response.get_json()
        assert 'error' in data
        assert 'bulunamadı' in data['error']
        
        # Verify location still exists
        location_after = Location.query.get(location_id)
        assert location_after is not None
    
    def test_api_delete_location_not_found(self, authenticated_admin_client, db_session):
        """
        Test: api_delete_location_not_found
        Verify 404 response for non-existent location
        Requirements: 1.1, 4.3
        """
        non_existent_id = 99999
        
        # Attempt to delete non-existent location
        response = authenticated_admin_client.delete(f'/api/locations/{non_existent_id}')
        
        # Verify response
        assert response.status_code == 404
        data = response.get_json()
        assert 'error' in data
        assert 'bulunamadı' in data['error']
    
    def test_api_delete_location_unauthenticated(self, client, db_session, sample_hotel):
        """
        Test: Verify authentication required for deletion
        Requirements: 4.3
        """
        # Create location
        location = Location(
            hotel_id=sample_hotel.id,
            name=f'Test Location {uuid.uuid4().hex[:8]}',
            qr_code_data=f'QR-{uuid.uuid4().hex[:8]}',
            is_active=True
        )
        db_session.add(location)
        db_session.commit()
        
        location_id = location.id
        
        # Attempt to delete without authentication
        response = client.delete(f'/api/locations/{location_id}')
        
        # Verify response - should be 401 or 403
        assert response.status_code in [401, 403]
        
        # Verify location still exists
        location_after = Location.query.get(location_id)
        assert location_after is not None
    
    @patch('app.services.location_service.QRCodeService.delete_qr_code', create=True)
    def test_api_delete_location_mixed_buggies(self, mock_delete_qr, authenticated_admin_client, db_session, sample_hotel, sample_admin_user, sample_driver_user):
        """
        Test: Verify deletion blocked with mix of active and inactive buggies
        Requirements: 1.1, 1.2, 1.5, 4.4
        """
        # Create location
        location = Location(
            hotel_id=sample_hotel.id,
            name=f'Test Location {uuid.uuid4().hex[:8]}',
            qr_code_data=f'QR-{uuid.uuid4().hex[:8]}',
            is_active=True
        )
        db_session.add(location)
        db_session.commit()
        
        # Create 1 active buggy
        active_buggy = Buggy(
            hotel_id=sample_hotel.id,
            code=f'BUGGY-{uuid.uuid4().hex[:8]}',
            current_location_id=location.id,
            status=BuggyStatus.AVAILABLE
        )
        db_session.add(active_buggy)
        db_session.commit()
        
        # Create active driver session
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
            current_location_id=location.id,
            status=BuggyStatus.OFFLINE
        )
        inactive_buggy2 = Buggy(
            hotel_id=sample_hotel.id,
            code=f'BUGGY-{uuid.uuid4().hex[:8]}',
            current_location_id=location.id,
            status=BuggyStatus.AVAILABLE
        )
        db_session.add_all([inactive_buggy1, inactive_buggy2])
        db_session.commit()
        
        location_id = location.id
        
        # Attempt to delete location via API
        response = authenticated_admin_client.delete(f'/api/locations/{location_id}')
        
        # Verify response
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        error_message = data['error']
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
    def test_api_delete_location_no_buggies(self, mock_delete_qr, authenticated_admin_client, db_session, sample_hotel, sample_admin_user):
        """
        Test: Verify successful deletion when no buggies present
        Requirements: 1.3, 4.3
        """
        # Create location
        location = Location(
            hotel_id=sample_hotel.id,
            name=f'Test Location {uuid.uuid4().hex[:8]}',
            qr_code_data=f'QR-{uuid.uuid4().hex[:8]}',
            is_active=True
        )
        db_session.add(location)
        db_session.commit()
        
        location_id = location.id
        
        # Delete location via API
        response = authenticated_admin_client.delete(f'/api/locations/{location_id}')
        
        # Verify response
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        
        # Verify location is deleted
        deleted_location = Location.query.get(location_id)
        assert deleted_location is None
