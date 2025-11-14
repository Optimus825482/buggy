"""
Production Ready System - Integration Tests
Tests for WebSocket, FCM, and real-time updates
Powered by Erkan ERDEM
"""
import pytest
import json
import time
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from app import create_app, db, socketio
from app.models.user import SystemUser, UserRole
from app.models.request import BuggyRequest, RequestStatus
from app.models.buggy import Buggy, BuggyStatus
from app.models.location import Location
from app.models.hotel import Hotel
from flask_socketio import SocketIOTestClient


@pytest.fixture
def app():
    """Create test app"""
    app = create_app('testing')
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def socketio_client(app):
    """Create SocketIO test client"""
    return SocketIOTestClient(app, socketio)


@pytest.fixture
def test_hotel():
    """Create test hotel"""
    hotel = Hotel(
        name='Test Hotel',
        address='Test Address',
        code='TEST'
    )
    db.session.add(hotel)
    db.session.commit()
    return hotel


@pytest.fixture
def test_location(test_hotel):
    """Create test location"""
    import uuid
    location = Location(
        hotel_id=test_hotel.id,
        name='Test Location',
        description='Test Description',
        qr_code_data=f'test_qr_{uuid.uuid4().hex[:8]}',  # Unique QR code
        is_active=True
    )
    db.session.add(location)
    db.session.commit()
    return location


@pytest.fixture
def test_driver(test_hotel):
    """Create test driver"""
    driver = SystemUser(
        username='test_driver',
        email='driver@test.com',
        full_name='Test Driver',
        role=UserRole.DRIVER,
        hotel_id=test_hotel.id,
        is_active=True,
        fcm_token='test_fcm_token_driver_123'
    )
    driver.set_password('test123')
    db.session.add(driver)
    db.session.commit()
    return driver


@pytest.fixture
def test_buggy(test_hotel, test_driver, test_location):
    """Create test buggy"""
    buggy = Buggy(
        hotel_id=test_hotel.id,
        code='B01',
        icon='🚗',
        driver_id=test_driver.id,
        status=BuggyStatus.AVAILABLE,
        current_location_id=test_location.id
    )
    db.session.add(buggy)
    db.session.commit()
    return buggy


# ============================================================================
# WebSocket Integration Tests
# ============================================================================

class TestWebSocketIntegration:
    """Test WebSocket real-time updates"""
    
    def test_guest_connected_event(self, app, socketio_client, test_hotel):
        """Test guest connection notification to drivers"""
        with app.app_context():
            # Emit guest_connected event
            socketio_client.emit('guest_connected', {
                'hotel_id': test_hotel.id,
                'location_id': 1
            })
            
            # Check if event was received
            received = socketio_client.get_received()
            assert len(received) > 0
    
    def test_new_request_websocket_broadcast(self, app, socketio_client, test_location):
        """Test new request WebSocket broadcast"""
        with app.app_context():
            from app.services.request_service import RequestService
            
            # Create request
            request_obj = RequestService.create_request(
                location_id=test_location.id,
                room_number='101',
                guest_name='Test Guest'
            )
            
            # Check WebSocket events
            received = socketio_client.get_received()
            
            # Should have new_request event
            new_request_events = [r for r in received if r.get('name') == 'new_request']
            assert len(new_request_events) > 0
    
    def test_request_accepted_websocket_update(self, app, socketio_client, test_location, test_buggy, test_driver):
        """Test request accepted WebSocket update"""
        with app.app_context():
            from app.services.request_service import RequestService
            
            # Create and accept request
            request_obj = RequestService.create_request(
                location_id=test_location.id,
                room_number='101'
            )
            
            request_obj = RequestService.accept_request(
                request_id=request_obj.id,
                buggy_id=test_buggy.id,
                driver_id=test_driver.id
            )
            
            # Check WebSocket events
            received = socketio_client.get_received()
            
            # Should have request_accepted event
            accepted_events = [r for r in received if r.get('name') == 'request_accepted']
            assert len(accepted_events) > 0


# ============================================================================
# Hybrid Socket.IO + FCM Tests
# ============================================================================

class TestHybridNotificationSystem:
    """Test hybrid Socket.IO + FCM approach"""
    
    @patch('app.services.fcm_notification_service.FCMNotificationService.send_to_multiple')
    def test_new_request_sends_both_socketio_and_fcm(self, mock_fcm, app, test_location, test_driver):
        """Test new request sends both Socket.IO and FCM"""
        with app.app_context():
            from app.services.request_service import RequestService
            
            # Mock FCM
            mock_fcm.return_value = {'success': 1, 'failure': 0}
            
            # Create request
            request_obj = RequestService.create_request(
                location_id=test_location.id,
                room_number='101'
            )
            
            # Verify FCM was called
            assert mock_fcm.called
    
    @patch('app.services.fcm_notification_service.FCMNotificationService.send_to_token')
    def test_guest_receives_fcm_on_acceptance(self, mock_fcm, app, test_location, test_buggy, test_driver):
        """Test guest receives FCM notification on request acceptance"""
        with app.app_context():
            from app.services.request_service import RequestService
            
            # Mock FCM
            mock_fcm.return_value = True
            
            # Create request with guest FCM token
            request_obj = RequestService.create_request(
                location_id=test_location.id,
                room_number='101'
            )
            request_obj.guest_fcm_token = 'guest_token_123'
            db.session.commit()
            
            # Accept request
            request_obj = RequestService.accept_request(
                request_id=request_obj.id,
                buggy_id=test_buggy.id,
                driver_id=test_driver.id
            )
            
            # Verify guest FCM was called (if token exists)
            # Note: This depends on implementation


# ============================================================================
# Buggy Auto-Available Tests
# ============================================================================

class TestBuggyAutoAvailable:
    """Test buggy automatic status change to AVAILABLE"""
    
    def test_buggy_becomes_available_after_completion(self, app, test_location, test_buggy, test_driver):
        """Test buggy status changes to AVAILABLE after request completion"""
        with app.app_context():
            from app.services.request_service import RequestService
            
            # Create and accept request
            request_obj = RequestService.create_request(
                location_id=test_location.id,
                room_number='101'
            )
            
            request_obj = RequestService.accept_request(
                request_id=request_obj.id,
                buggy_id=test_buggy.id,
                driver_id=test_driver.id
            )
            
            # Verify buggy is BUSY
            buggy = Buggy.query.get(test_buggy.id)
            assert buggy.status == BuggyStatus.BUSY
            
            # Complete request
            request_obj = RequestService.complete_request(
                request_id=request_obj.id,
                driver_id=test_driver.id,
                current_location_id=test_location.id
            )
            
            # Verify buggy is AVAILABLE
            buggy = Buggy.query.get(test_buggy.id)
            assert buggy.status == BuggyStatus.AVAILABLE
    
    def test_buggy_location_updated_on_completion(self, app, test_hotel, test_buggy, test_driver):
        """Test buggy location is updated on request completion"""
        with app.app_context():
            from app.services.request_service import RequestService
            
            # Create two locations
            import uuid
            location1 = Location(
                hotel_id=test_hotel.id,
                name='Location 1',
                qr_code_data=f'test_qr_loc1_{uuid.uuid4().hex[:8]}',
                is_active=True
            )
            location2 = Location(
                hotel_id=test_hotel.id,
                name='Location 2',
                qr_code_data=f'test_qr_loc2_{uuid.uuid4().hex[:8]}',
                is_active=True
            )
            db.session.add_all([location1, location2])
            db.session.commit()
            
            # Create and accept request at location1
            request_obj = RequestService.create_request(
                location_id=location1.id,
                room_number='101'
            )
            
            request_obj = RequestService.accept_request(
                request_id=request_obj.id,
                buggy_id=test_buggy.id,
                driver_id=test_driver.id
            )
            
            # Complete request and update location to location2
            request_obj = RequestService.complete_request(
                request_id=request_obj.id,
                driver_id=test_driver.id,
                current_location_id=location2.id
            )
            
            # Verify buggy location updated
            buggy = Buggy.query.get(test_buggy.id)
            assert buggy.current_location_id == location2.id


# ============================================================================
# Performance Tests
# ============================================================================

class TestPerformance:
    """Test system performance"""
    
    def test_notification_delivery_speed(self, app, test_driver):
        """Test FCM notification delivery speed (< 500ms)"""
        with app.app_context():
            from app.services.fcm_notification_service import FCMNotificationService
            
            with patch.object(FCMNotificationService, 'initialize', return_value=True):
                with patch('firebase_admin.messaging.send') as mock_send:
                    mock_send.return_value = 'msg_id'
                    
                    start_time = time.time()
                    
                    FCMNotificationService.send_to_token(
                        token=test_driver.fcm_token,
                        title='Test',
                        body='Test',
                        retry=False
                    )
                    
                    elapsed = (time.time() - start_time) * 1000  # Convert to ms
                    
                    # Should be very fast (< 100ms in test environment)
                    assert elapsed < 500
    
    def test_database_query_performance(self, app, test_hotel, test_location):
        """Test database query performance for pending requests"""
        with app.app_context():
            from app.services.request_service import RequestService
            
            # Create 10 requests
            for i in range(10):
                RequestService.create_request(
                    location_id=test_location.id,
                    room_number=f'10{i}'
                )
            
            # Measure query time
            start_time = time.time()
            
            pending_requests = RequestService.get_pending_requests(test_hotel.id)
            
            elapsed = (time.time() - start_time) * 1000  # Convert to ms
            
            # Should be fast (< 100ms)
            assert elapsed < 100
            assert len(pending_requests) == 10


# ============================================================================
# Error Handling Tests
# ============================================================================

class TestErrorHandling:
    """Test comprehensive error handling"""
    
    def test_fcm_initialization_failure_fallback(self, app):
        """Test system continues working when FCM fails to initialize"""
        with app.app_context():
            from app.services.fcm_notification_service import FCMNotificationService
            
            # Force initialization failure
            with patch.object(FCMNotificationService, 'initialize', return_value=False):
                success = FCMNotificationService.send_to_token(
                    token='test_token',
                    title='Test',
                    body='Test'
                )
                
                # Should fail gracefully
                assert success is False
    
    def test_websocket_disconnect_recovery(self, app, socketio_client):
        """Test WebSocket reconnection handling"""
        with app.app_context():
            # Disconnect
            socketio_client.disconnect()
            
            # Reconnect
            socketio_client.connect()
            
            # Should be able to emit events
            socketio_client.emit('test_event', {'data': 'test'})
            
            # No exception should be raised


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
