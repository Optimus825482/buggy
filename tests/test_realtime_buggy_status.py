"""
Test suite for real-time buggy status updates via WebSocket
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from app.services.buggy_service import BuggyService
from app.models.buggy import Buggy, BuggyStatus
from app.models.buggy_driver import BuggyDriver
from app.models.user import SystemUser, UserRole
from app.models.request import BuggyRequest, RequestStatus
from datetime import datetime


class TestEmitBuggyStatusUpdate:
    """Test emit_buggy_status_update function"""
    
    @patch('app.services.buggy_service.socketio')
    def test_emit_with_active_session_no_request(self, mock_socketio, app, db_session):
        """Test emit with active session but no active request (status = available)"""
        # Create test data
        hotel_id = 1
        buggy = Buggy(
            hotel_id=hotel_id,
            code='BUGGY_TEST1',
            icon='🚗',
            status=BuggyStatus.AVAILABLE,
            current_location_id=1
        )
        db_session.add(buggy)
        db_session.flush()  # Get ID
        
        driver = SystemUser(
            hotel_id=hotel_id,
            username='driver_test1',
            full_name='Test Driver',
            role=UserRole.DRIVER
        )
        driver.set_password('password')
        db_session.add(driver)
        db_session.flush()  # Get ID
        
        # Create active session
        session = BuggyDriver(
            buggy_id=buggy.id,
            driver_id=driver.id,
            is_active=True
        )
        db_session.add(session)
        db_session.commit()
        
        # Call emit function
        BuggyService.emit_buggy_status_update(buggy.id, hotel_id)
        
        # Verify emit was called
        assert mock_socketio.emit.called
        call_args = mock_socketio.emit.call_args
        
        # Check event name
        assert call_args[0][0] == 'buggy_status_update'
        
        # Check payload
        payload = call_args[0][1]
        assert payload['buggy_id'] == buggy.id
        assert payload['buggy_code'] == 'BUGGY_TEST1'
        assert payload['buggy_icon'] == '🚗'
        assert payload['status'] == 'available'
        assert payload['driver_name'] == 'Test Driver'
        assert payload['location_id'] == 1
        assert 'timestamp' in payload
        
        # Check room
        assert call_args[1]['room'] == f'hotel_{hotel_id}_admins'
    
    @patch('app.services.buggy_service.socketio')
    def test_emit_with_active_session_and_request(self, mock_socketio, app, db_session):
        """Test emit with active session and active request (status = busy)"""
        # Create test data
        hotel_id = 1
        buggy = Buggy(
            hotel_id=hotel_id,
            code='BUGGY_TEST2',
            icon='🚗',
            status=BuggyStatus.BUSY,
            current_location_id=1
        )
        db_session.add(buggy)
        db_session.flush()
        
        driver = SystemUser(
            hotel_id=hotel_id,
            username='driver_test2',
            full_name='Test Driver',
            role=UserRole.DRIVER
        )
        driver.set_password('password')
        db_session.add(driver)
        db_session.flush()
        
        # Create active session
        session = BuggyDriver(
            buggy_id=buggy.id,
            driver_id=driver.id,
            is_active=True
        )
        db_session.add(session)
        
        # Create active request
        request = BuggyRequest(
            hotel_id=hotel_id,
            buggy_id=buggy.id,
            location_id=1,
            status=RequestStatus.ACCEPTED,
            accepted_by_id=driver.id
        )
        db_session.add(request)
        db_session.commit()
        
        # Call emit function
        BuggyService.emit_buggy_status_update(buggy.id, hotel_id)
        
        # Verify emit was called
        assert mock_socketio.emit.called
        payload = mock_socketio.emit.call_args[0][1]
        
        # Status should be busy
        assert payload['status'] == 'busy'
        assert payload['driver_name'] == 'Test Driver'
    
    @patch('app.services.buggy_service.socketio')
    def test_emit_without_active_session(self, mock_socketio, app, db_session):
        """Test emit without active session (status = offline)"""
        # Create test data
        hotel_id = 1
        buggy = Buggy(
            hotel_id=hotel_id,
            code='BUGGY_TEST3',
            icon='🚗',
            status=BuggyStatus.OFFLINE,
            current_location_id=1
        )
        db_session.add(buggy)
        db_session.flush()
        db_session.commit()
        
        # Call emit function
        BuggyService.emit_buggy_status_update(buggy.id, hotel_id)
        
        # Verify emit was called
        assert mock_socketio.emit.called
        payload = mock_socketio.emit.call_args[0][1]
        
        # Status should be offline
        assert payload['status'] == 'offline'
        assert payload['driver_name'] is None
    
    @patch('app.services.buggy_service.socketio')
    def test_emit_invalid_buggy(self, mock_socketio, app, db_session):
        """Test emit with invalid buggy ID (graceful failure)"""
        # Call with non-existent buggy
        BuggyService.emit_buggy_status_update(999, 1)
        
        # Should not raise exception
        # Should not emit
        assert not mock_socketio.emit.called
    
    @patch('app.services.buggy_service.socketio')
    def test_emit_with_username_fallback(self, mock_socketio, app, db_session):
        """Test emit uses username when full_name is not set"""
        # Create test data
        hotel_id = 1
        buggy = Buggy(
            hotel_id=hotel_id,
            code='BUGGY_TEST4',
            icon='🚗',
            status=BuggyStatus.AVAILABLE
        )
        db_session.add(buggy)
        db_session.flush()
        
        driver = SystemUser(
            hotel_id=hotel_id,
            username='driver_test4',
            full_name='',  # Empty full name to test username fallback
            role=UserRole.DRIVER
        )
        driver.set_password('password')
        db_session.add(driver)
        db_session.flush()
        
        # Create active session
        session = BuggyDriver(
            buggy_id=buggy.id,
            driver_id=driver.id,
            is_active=True
        )
        db_session.add(session)
        db_session.commit()
        
        # Call emit function
        BuggyService.emit_buggy_status_update(buggy.id, hotel_id)
        
        # Verify driver_name falls back to username
        payload = mock_socketio.emit.call_args[0][1]
        assert payload['driver_name'] == 'driver_test4'
    
    @patch('app.services.buggy_service.socketio')
    def test_emit_data_format(self, mock_socketio, app, db_session):
        """Test emit payload has correct data format"""
        # Create minimal test data
        hotel_id = 1
        buggy = Buggy(
            hotel_id=hotel_id,
            code='BUGGY_TEST5',
            icon='🚗',
            status=BuggyStatus.OFFLINE
        )
        db_session.add(buggy)
        db_session.flush()
        db_session.commit()
        
        # Call emit function
        BuggyService.emit_buggy_status_update(buggy.id, hotel_id)
        
        # Verify payload structure
        payload = mock_socketio.emit.call_args[0][1]
        
        # Check all required fields
        assert 'buggy_id' in payload
        assert 'buggy_code' in payload
        assert 'buggy_icon' in payload
        assert 'status' in payload
        assert 'driver_name' in payload
        assert 'location_id' in payload
        assert 'timestamp' in payload
        
        # Check types
        assert isinstance(payload['buggy_id'], int)
        assert isinstance(payload['buggy_code'], str)
        assert isinstance(payload['status'], str)
        assert isinstance(payload['timestamp'], str)
        
        # Check status is valid
        assert payload['status'] in ['available', 'busy', 'offline']
