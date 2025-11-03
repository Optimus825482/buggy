"""
Test Driver Workflow
Tests for driver location management and request handling
"""
import pytest
from app import create_app, db
from app.models.user import SystemUser, UserRole
from app.models.hotel import Hotel
from app.models.location import Location
from app.models.buggy import Buggy, BuggyStatus
from app.models.request import BuggyRequest, RequestStatus
from flask import session


@pytest.fixture
def app():
    """Create test app"""
    app = create_app('testing')
    with app.app_context():
        # Configure session to prevent DetachedInstanceError
        db.session.configure(expire_on_commit=False)
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def setup_data(app):
    """Setup test data"""
    with app.app_context():
        # Create hotel
        hotel = Hotel(name='Test Hotel', code='TEST')
        db.session.add(hotel)
        db.session.flush()
        
        # Create locations
        location1 = Location(
            hotel_id=hotel.id,
            name='Lobby',
            qr_code_data='LOC10001',
            is_active=True
        )
        location2 = Location(
            hotel_id=hotel.id,
            name='Pool',
            qr_code_data='LOC10002',
            is_active=True
        )
        db.session.add_all([location1, location2])
        db.session.flush()
        
        # Create driver
        driver = SystemUser(
            hotel_id=hotel.id,
            username='driver1',
            role=UserRole.DRIVER,
            full_name='Test Driver',
            is_active=True
        )
        driver.set_password('password123')
        db.session.add(driver)
        db.session.flush()
        
        # Create buggy
        buggy = Buggy(
            hotel_id=hotel.id,
            code='B01',
            driver_id=driver.id,
            status=BuggyStatus.OFFLINE
        )
        db.session.add(buggy)
        db.session.flush()
        
        # Create guest request
        request = BuggyRequest(
            hotel_id=hotel.id,
            location_id=location1.id,
            guest_name='Test Guest',
            room_number='101',
            status=RequestStatus.PENDING
        )
        db.session.add(request)

        db.session.commit()

        return {
            'hotel': hotel,
            'location1': location1,
            'location2': location2,
            'driver': driver,
            'buggy': buggy,
            'request': request
        }


class TestDriverLocationManagement:
    """Test driver location management"""
    
    def test_set_location_success(self, client, setup_data):
        """Test setting driver location successfully"""
        # Login as driver
        response = client.post('/auth/login', json={
            'username': 'driver1',
            'password': 'password123'
        })
        assert response.status_code == 200
        
        # Set location
        response = client.post('/api/driver/set-location', json={
            'location_id': setup_data['location1'].id
        })

        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['buggy']['current_location_id'] == setup_data['location1'].id
        assert data['buggy']['status'] == 'available'
    
    def test_set_location_without_login(self, client, setup_data):
        """Test setting location without login fails"""
        response = client.post('/api/driver/set-location', json={
            'location_id': setup_data['location1'].id
        })
        
        assert response.status_code in [401, 403]
    
    def test_set_location_invalid_location(self, client, setup_data):
        """Test setting invalid location fails"""
        # Login
        client.post('/auth/login', json={
            'username': 'driver1',
            'password': 'password123'
        })
        
        # Try invalid location
        response = client.post('/api/driver/set-location', json={
            'location_id': 99999
        })
        
        assert response.status_code == 404


class TestDriverRequestHandling:
    """Test driver request acceptance and completion"""
    
    def test_accept_request_success(self, client, setup_data):
        """Test accepting a request successfully"""
        # Login and set location
        client.post('/auth/login', json={
            'username': 'driver1',
            'password': 'password123'
        })
        client.post('/api/driver/set-location', json={
            'location_id': setup_data['location1'].id
        })
        
        # Accept request
        response = client.post(
            f'/api/driver/accept-request/{setup_data["request"].id}'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['request']['status'] == 'accepted'
    
    def test_accept_request_when_busy(self, client, setup_data):
        """Test accepting request when already busy fails"""
        # Login and set location
        client.post('/auth/login', json={
            'username': 'driver1',
            'password': 'password123'
        })
        client.post('/api/driver/set-location', json={
            'location_id': setup_data['location1'].id
        })
        
        # Accept first request
        client.post(
            f'/api/driver/accept-request/{setup_data["request"].id}'
        )
        
        # Create another request
        with client.application.app_context():
            request2 = BuggyRequest(
                hotel_id=setup_data['hotel'].id,
                location_id=setup_data['location2'].id,
                guest_name='Guest 2',
                status=RequestStatus.PENDING
            )
            db.session.add(request2)
            db.session.commit()
            request2_id = request2.id
        
        # Try to accept second request
        response = client.post(f'/api/driver/accept-request/{request2_id}')
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'müsait değil' in data['error'].lower()
    
    def test_complete_request_success(self, client, setup_data):
        """Test completing a request successfully"""
        # Login, set location, accept request
        client.post('/auth/login', json={
            'username': 'driver1',
            'password': 'password123'
        })
        client.post('/api/driver/set-location', json={
            'location_id': setup_data['location1'].id
        })
        client.post(
            f'/api/driver/accept-request/{setup_data["request"].id}'
        )
        
        # Complete request
        response = client.post(
            f'/api/driver/complete-request/{setup_data["request"].id}'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['show_location_modal'] is True
    
    def test_complete_request_not_assigned(self, client, setup_data):
        """Test completing request not assigned to driver fails"""
        # Login
        client.post('/auth/login', json={
            'username': 'driver1',
            'password': 'password123'
        })
        
        # Try to complete without accepting
        response = client.post(
            f'/api/driver/complete-request/{setup_data["request"].id}'
        )
        
        assert response.status_code == 404


class TestDriverWorkflowIntegration:
    """Test complete driver workflow"""
    
    def test_complete_workflow(self, client, setup_data):
        """Test complete driver workflow from login to completion"""
        # 1. Login
        response = client.post('/auth/login', json={
            'username': 'driver1',
            'password': 'password123'
        })
        assert response.status_code == 200
        
        # 2. Set initial location
        response = client.post('/api/driver/set-location', json={
            'location_id': setup_data['location1'].id
        })
        assert response.status_code == 200
        assert response.get_json()['buggy']['status'] == 'available'
        
        # 3. Accept request
        response = client.post(
            f'/api/driver/accept-request/{setup_data["request"].id}'
        )
        assert response.status_code == 200
        
        # Verify buggy is busy
        with client.application.app_context():
            buggy = Buggy.query.get(setup_data['buggy'].id)
            assert buggy.status == BuggyStatus.BUSY
        
        # 4. Complete request
        response = client.post(
            f'/api/driver/complete-request/{setup_data["request"].id}'
        )
        assert response.status_code == 200
        
        # Verify request is completed
        with client.application.app_context():
            request = BuggyRequest.query.get(setup_data['request'].id)
            assert request.status == RequestStatus.COMPLETED
            assert request.completed_at is not None
        
        # 5. Set new location
        response = client.post('/api/driver/set-location', json={
            'location_id': setup_data['location2'].id
        })
        assert response.status_code == 200
        assert response.get_json()['buggy']['status'] == 'available'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
