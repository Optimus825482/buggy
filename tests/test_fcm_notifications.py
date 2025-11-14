"""
FCM Push Notifications - Comprehensive Test Suite
Tests for Firebase Cloud Messaging implementation
Powered by Erkan ERDEM
"""
import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from app import create_app, db
from app.models.user import SystemUser, UserRole
from app.models.request import BuggyRequest, RequestStatus
from app.models.buggy import Buggy, BuggyStatus
from app.models.location import Location
from app.models.hotel import Hotel
from app.models.notification_log import NotificationLog
from app.services.fcm_notification_service import FCMNotificationService


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
def auth_headers(client, test_hotel):
    """Get authentication headers"""
    # Create test user
    user = SystemUser(
        username='test_driver',
        email='driver@test.com',
        role=UserRole.DRIVER,
        hotel_id=test_hotel.id,
        is_active=True
    )
    user.set_password('test123')
    db.session.add(user)
    db.session.commit()
    
    # Login
    response = client.post('/api/auth/login', json={
        'username': 'test_driver',
        'password': 'test123'
    })
    
    data = json.loads(response.data)
    token = data.get('access_token')
    
    return {'Authorization': f'Bearer {token}'}


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
    location = Location(
        hotel_id=test_hotel.id,
        name='Test Location',
        description='Test Description',
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
def test_buggy(test_hotel, test_driver):
    """Create test buggy"""
    buggy = Buggy(
        hotel_id=test_hotel.id,
        code='B01',
        icon='🚗',
        driver_id=test_driver.id,
        status=BuggyStatus.AVAILABLE
    )
    db.session.add(buggy)
    db.session.commit()
    return buggy


# ============================================================================
# FCM Service Tests
# ============================================================================

class TestFCMService:
    """Test FCM Notification Service"""
    
    def test_fcm_initialization(self, app):
        """Test FCM service initialization"""
        with app.app_context():
            # Mock Firebase Admin SDK
            with patch('firebase_admin.get_app') as mock_get_app:
                mock_get_app.side_effect = ValueError('No app')
                
                with patch('firebase_admin.initialize_app') as mock_init:
                    result = FCMNotificationService.initialize()
                    assert result is True
                    assert FCMNotificationService._initialized is True
    
    def test_register_token(self, app, test_driver):
        """Test FCM token registration"""
        with app.app_context():
            token = 'new_fcm_token_123'
            
            success = FCMNotificationService.register_token(test_driver.id, token)
            
            assert success is True
            
            # Verify token saved
            user = SystemUser.query.get(test_driver.id)
            assert user.fcm_token == token
            assert user.fcm_token_date is not None
    
    def test_refresh_token(self, app, test_driver):
        """Test FCM token refresh"""
        with app.app_context():
            old_token = test_driver.fcm_token
            new_token = 'refreshed_fcm_token_456'
            
            success = FCMNotificationService.refresh_token(
                test_driver.id, 
                old_token, 
                new_token
            )
            
            assert success is True
            
            # Verify token updated
            user = SystemUser.query.get(test_driver.id)
            assert user.fcm_token == new_token
    
    @patch('firebase_admin.messaging.send')
    def test_send_to_token_high_priority(self, mock_send, app, test_driver):
        """Test sending high priority notification"""
        with app.app_context():
            # Mock Firebase
            with patch.object(FCMNotificationService, 'initialize', return_value=True):
                mock_send.return_value = 'message_id_123'
                
                success = FCMNotificationService.send_to_token(
                    token=test_driver.fcm_token,
                    title='Test Notification',
                    body='Test Body',
                    data={'type': 'test'},
                    priority='high'
                )
                
                assert success is True
                assert mock_send.called
    
    @patch('firebase_admin.messaging.send_multicast')
    def test_send_to_multiple(self, mock_send_multicast, app, test_driver):
        """Test sending to multiple tokens"""
        with app.app_context():
            # Mock Firebase
            with patch.object(FCMNotificationService, 'initialize', return_value=True):
                # Mock response
                mock_response = Mock()
                mock_response.success_count = 2
                mock_response.failure_count = 0
                mock_send_multicast.return_value = mock_response
                
                tokens = ['token1', 'token2']
                
                result = FCMNotificationService.send_to_multiple(
                    tokens=tokens,
                    title='Test Notification',
                    body='Test Body',
                    priority='high'
                )
                
                assert result['success'] == 2
                assert result['failure'] == 0
    
    @patch('firebase_admin.messaging.send_multicast')
    def test_notify_new_request(self, mock_send_multicast, app, test_driver, test_buggy, test_location):
        """Test new request notification"""
        with app.app_context():
            # Create request
            request_obj = BuggyRequest(
                hotel_id=test_driver.hotel_id,
                location_id=test_location.id,
                room_number='101',
                guest_name='Test Guest',
                status=RequestStatus.PENDING
            )
            db.session.add(request_obj)
            db.session.commit()
            
            # Mock Firebase
            with patch.object(FCMNotificationService, 'initialize', return_value=True):
                mock_response = Mock()
                mock_response.success_count = 1
                mock_response.failure_count = 0
                mock_send_multicast.return_value = mock_response
                
                count = FCMNotificationService.notify_new_request(request_obj)
                
                assert count == 1
                assert mock_send_multicast.called
    
    def test_invalid_token_cleanup(self, app, test_driver):
        """Test invalid token cleanup"""
        with app.app_context():
            token = test_driver.fcm_token
            
            FCMNotificationService._remove_invalid_token(token)
            
            # Verify token removed
            user = SystemUser.query.get(test_driver.id)
            assert user.fcm_token is None
            assert user.fcm_token_date is None


# ============================================================================
# FCM API Tests
# ============================================================================

class TestFCMAPI:
    """Test FCM API endpoints"""
    
    def test_register_token_endpoint(self, client, auth_headers):
        """Test /api/fcm/register-token endpoint"""
        response = client.post(
            '/api/fcm/register-token',
            headers=auth_headers,
            json={'token': 'new_fcm_token_789'}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['message'] == 'FCM token başarıyla kaydedildi'
    
    def test_register_token_missing_token(self, client, auth_headers):
        """Test register token with missing token"""
        response = client.post(
            '/api/fcm/register-token',
            headers=auth_headers,
            json={}
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_refresh_token_endpoint(self, client, auth_headers):
        """Test /api/fcm/refresh-token endpoint"""
        response = client.post(
            '/api/fcm/refresh-token',
            headers=auth_headers,
            json={
                'old_token': 'old_token_123',
                'new_token': 'new_token_456'
            }
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['message'] == 'FCM token başarıyla yenilendi'
    
    @patch('app.services.fcm_notification_service.FCMNotificationService.send_to_token')
    def test_test_notification_endpoint(self, mock_send, client, auth_headers, test_driver):
        """Test /api/fcm/test-notification endpoint"""
        mock_send.return_value = True
        
        response = client.post(
            '/api/fcm/test-notification',
            headers=auth_headers,
            json={
                'title': 'Test Title',
                'body': 'Test Body'
            }
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'sent'
    
    def test_unauthorized_access(self, client):
        """Test unauthorized access to FCM endpoints"""
        response = client.post(
            '/api/fcm/register-token',
            json={'token': 'test_token'}
        )
        
        assert response.status_code == 401


# ============================================================================
# Guest FCM Tests
# ============================================================================

class TestGuestFCM:
    """Test Guest FCM functionality"""
    
    def test_guest_register_fcm_token(self, client):
        """Test guest FCM token registration"""
        response = client.post(
            '/api/guest/register-fcm-token',
            json={
                'token': 'guest_fcm_token_123',
                'request_id': 1
            }
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
    
    def test_guest_register_missing_token(self, client):
        """Test guest registration with missing token"""
        response = client.post(
            '/api/guest/register-fcm-token',
            json={'request_id': 1}
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
    
    def test_guest_register_missing_request_id(self, client):
        """Test guest registration with missing request_id"""
        response = client.post(
            '/api/guest/register-fcm-token',
            json={'token': 'guest_token_123'}
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False


# ============================================================================
# Admin Stats API Tests
# ============================================================================

class TestAdminStatsAPI:
    """Test Admin Notification Stats API"""
    
    @pytest.fixture
    def admin_user(self, test_hotel):
        """Create admin user"""
        admin = SystemUser(
            username='admin',
            email='admin@test.com',
            role=UserRole.ADMIN,
            hotel_id=test_hotel.id,
            is_active=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        return admin
    
    @pytest.fixture
    def admin_headers(self, client, admin_user):
        """Get admin authentication headers"""
        response = client.post('/api/auth/login', json={
            'username': 'admin',
            'password': 'admin123'
        })
        
        data = json.loads(response.data)
        token = data.get('access_token')
        
        return {'Authorization': f'Bearer {token}'}
    
    def test_get_notification_stats(self, client, admin_headers, test_driver):
        """Test /api/admin/notifications/stats endpoint"""
        # Create test notification logs
        log = NotificationLog(
            user_id=test_driver.id,
            notification_type='fcm',
            priority='high',
            title='Test Notification',
            body='Test Body',
            status='sent',
            sent_at=datetime.utcnow()
        )
        db.session.add(log)
        db.session.commit()
        
        response = client.get(
            '/api/admin/notifications/stats?hours=24',
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'total_sent' in data
        assert 'delivery_rate' in data
        assert 'fcm' in data
    
    def test_get_timeline_stats(self, client, admin_headers, test_driver):
        """Test /api/admin/notifications/stats/timeline endpoint"""
        # Create test notification logs
        for i in range(5):
            log = NotificationLog(
                user_id=test_driver.id,
                notification_type='fcm',
                priority='normal',
                title=f'Test {i}',
                body='Test Body',
                status='sent',
                sent_at=datetime.utcnow() - timedelta(days=i)
            )
            db.session.add(log)
        db.session.commit()
        
        response = client.get(
            '/api/admin/notifications/stats/timeline?period=daily&days=7',
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'timeline' in data
        assert 'period' in data
        assert data['period'] == 'daily'
    
    def test_unauthorized_admin_access(self, client, auth_headers):
        """Test non-admin cannot access admin endpoints"""
        response = client.get(
            '/api/admin/notifications/stats',
            headers=auth_headers
        )
        
        assert response.status_code == 403


# ============================================================================
# Priority Tests
# ============================================================================

class TestNotificationPriority:
    """Test notification priority levels"""
    
    @patch('firebase_admin.messaging.send')
    def test_high_priority_notification(self, mock_send, app, test_driver):
        """Test high priority notification settings"""
        with app.app_context():
            with patch.object(FCMNotificationService, 'initialize', return_value=True):
                mock_send.return_value = 'msg_id'
                
                FCMNotificationService.send_to_token(
                    token=test_driver.fcm_token,
                    title='Urgent',
                    body='High priority message',
                    priority='high'
                )
                
                # Verify high priority settings
                call_args = mock_send.call_args
                message = call_args[0][0]
                assert message.android.priority == 'high'
    
    @patch('firebase_admin.messaging.send')
    def test_normal_priority_notification(self, mock_send, app, test_driver):
        """Test normal priority notification settings"""
        with app.app_context():
            with patch.object(FCMNotificationService, 'initialize', return_value=True):
                mock_send.return_value = 'msg_id'
                
                FCMNotificationService.send_to_token(
                    token=test_driver.fcm_token,
                    title='Info',
                    body='Normal priority message',
                    priority='normal'
                )
                
                # Verify normal priority settings
                call_args = mock_send.call_args
                message = call_args[0][0]
                assert message.android.priority == 'normal'


# ============================================================================
# Error Handling Tests
# ============================================================================

class TestErrorHandling:
    """Test error handling and recovery"""
    
    @patch('firebase_admin.messaging.send')
    def test_unregistered_token_error(self, mock_send, app, test_driver):
        """Test handling of unregistered token error"""
        with app.app_context():
            with patch.object(FCMNotificationService, 'initialize', return_value=True):
                from firebase_admin import messaging
                mock_send.side_effect = messaging.UnregisteredError('Token not registered')
                
                success = FCMNotificationService.send_to_token(
                    token=test_driver.fcm_token,
                    title='Test',
                    body='Test'
                )
                
                assert success is False
                
                # Verify token was removed
                user = SystemUser.query.get(test_driver.id)
                assert user.fcm_token is None
    
    def test_firebase_not_initialized(self, app, test_driver):
        """Test behavior when Firebase is not initialized"""
        with app.app_context():
            # Force initialization to fail
            FCMNotificationService._initialized = False
            
            with patch.object(FCMNotificationService, 'initialize', return_value=False):
                success = FCMNotificationService.send_to_token(
                    token=test_driver.fcm_token,
                    title='Test',
                    body='Test'
                )
                
                assert success is False


# ============================================================================
# Integration Tests
# ============================================================================

class TestFCMIntegration:
    """Test end-to-end FCM integration"""
    
    @patch('firebase_admin.messaging.send_multicast')
    def test_complete_request_flow(self, mock_send_multicast, app, test_driver, test_buggy, test_location):
        """Test complete request flow with FCM notifications"""
        with app.app_context():
            # Mock Firebase
            with patch.object(FCMNotificationService, 'initialize', return_value=True):
                mock_response = Mock()
                mock_response.success_count = 1
                mock_response.failure_count = 0
                mock_send_multicast.return_value = mock_response
                
                # Create request
                request_obj = BuggyRequest(
                    hotel_id=test_driver.hotel_id,
                    location_id=test_location.id,
                    room_number='101',
                    status=RequestStatus.PENDING
                )
                db.session.add(request_obj)
                db.session.commit()
                
                # Notify drivers
                count = FCMNotificationService.notify_new_request(request_obj)
                assert count == 1
                
                # Accept request
                request_obj.status = RequestStatus.ACCEPTED
                request_obj.buggy_id = test_buggy.id
                db.session.commit()
                
                # Complete request
                request_obj.status = RequestStatus.COMPLETED
                db.session.commit()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
