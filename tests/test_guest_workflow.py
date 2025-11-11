"""
Test Guest Workflow
Tests for guest QR code scanning and request tracking
"""
import pytest
from app import create_app, db
from app.models.user import SystemUser, UserRole
from app.models.hotel import Hotel
from app.models.location import Location
from app.models.buggy import Buggy, BuggyStatus
from app.models.request import BuggyRequest, RequestStatus


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
        
        # Create location
        location = Location(
            hotel_id=hotel.id,
            name='Lobby',
            qr_code_data='LOC10001',
            is_active=True
        )
        db.session.add(location)
        db.session.flush()
        
        # Create driver and buggy
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
        
        buggy = Buggy(
            hotel_id=hotel.id,
            code='B01',
            driver_id=driver.id,
            current_location_id=location.id,
            status=BuggyStatus.AVAILABLE
        )
        db.session.add(buggy)
        
        db.session.commit()
        
        return {
            'hotel': hotel,
            'location': location,
            'driver': driver,
            'buggy': buggy
        }


class TestGuestQRWorkflow:
    """Test guest QR code workflow"""
    
    def test_qr_redirect_with_location(self, client, setup_data):
        """Test QR code redirects to call page with location ID"""
        response = client.get(
            f'/guest/call?location={setup_data["location"].id}'
        )
        
        assert response.status_code == 200
        assert b'Buggy' in response.data
    
    def test_create_request_with_room_number(self, client, setup_data):
        """Test creating request with room number"""
        response = client.post('/api/requests', json={
            'hotel_id': setup_data['hotel'].id,
            'location_id': setup_data['location'].id,
            'guest_name': 'John Doe',
            'room_number': '101',
            'guest_count': 2
        })
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['request']['room_number'] == '101'
        assert data['request']['status'] == 'PENDING'
    
    def test_create_request_without_room_number(self, client, setup_data):
        """Test creating request without room number (optional)"""
        response = client.post('/api/requests', json={
            'hotel_id': setup_data['hotel'].id,
            'location_id': setup_data['location'].id,
            'guest_name': 'Jane Doe',
            'room_number': None,
            'guest_count': 1
        })
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['request']['room_number'] is None
        assert data['request']['status'] == 'PENDING'
    
    def test_create_request_no_available_buggies(self, client, setup_data):
        """Test creating request when no buggies available"""
        # Set buggy to offline
        with client.application.app_context():
            buggy = Buggy.query.get(setup_data['buggy'].id)
            buggy.status = BuggyStatus.OFFLINE
            db.session.commit()
        
        response = client.post('/api/requests', json={
            'hotel_id': setup_data['hotel'].id,
            'location_id': setup_data['location'].id,
            'guest_name': 'Test Guest',
            'guest_count': 1
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'müsait buggy' in data['error'].lower()


class TestGuestStatusTracking:
    """Test guest request status tracking"""
    
    def test_get_request_status(self, client, setup_data):
        """Test getting request status"""
        # Create request
        with client.application.app_context():
            request = BuggyRequest(
                hotel_id=setup_data['hotel'].id,
                location_id=setup_data['location'].id,
                guest_name='Test Guest',
                room_number='202',
                status=RequestStatus.PENDING
            )
            db.session.add(request)
            db.session.commit()
            request_id = request.id
        
        # Get status
        response = client.get(f'/api/requests/{request_id}')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['request']['id'] == request_id
        assert data['request']['status'] == 'PENDING'
    
    def test_status_page_renders(self, client, setup_data):
        """Test status tracking page renders"""
        # Create request
        with client.application.app_context():
            request = BuggyRequest(
                hotel_id=setup_data['hotel'].id,
                location_id=setup_data['location'].id,
                guest_name='Test Guest',
                status=RequestStatus.PENDING
            )
            db.session.add(request)
            db.session.commit()
            request_id = request.id
        
        response = client.get(f'/guest/status/{request_id}')
        
        assert response.status_code == 200
        assert b'status' in response.data.lower()


class TestGuestWorkflowIntegration:
    """Test complete guest workflow"""
    
    def test_complete_guest_workflow(self, client, setup_data):
        """Test complete guest workflow from QR scan to completion"""
        # 1. Access call page via QR (with location)
        response = client.get(
            f'/guest/call?location={setup_data["location"].id}'
        )
        assert response.status_code == 200
        
        # 2. Create request
        response = client.post('/api/requests', json={
            'hotel_id': setup_data['hotel'].id,
            'location_id': setup_data['location'].id,
            'guest_name': 'Integration Test Guest',
            'room_number': '303',
            'guest_count': 2
        })
        assert response.status_code == 201
        request_id = response.get_json()['request']['id']
        
        # 3. Check status (PENDING)
        response = client.get(f'/api/requests/{request_id}')
        assert response.status_code == 200
        assert response.get_json()['request']['status'] == 'PENDING'
        
        # 4. Driver accepts (simulate)
        with client.application.app_context():
            request = BuggyRequest.query.get(request_id)
            request.status = RequestStatus.ACCEPTED
            request.buggy_id = setup_data['buggy'].id
            request.accepted_by_id = setup_data['driver'].id
            db.session.commit()
        
        # 5. Check status (accepted)
        response = client.get(f'/api/requests/{request_id}')
        assert response.status_code == 200
        data = response.get_json()
        assert data['request']['status'] == 'accepted'
        assert data['request']['buggy'] is not None
        
        # 6. Driver completes (simulate)
        with client.application.app_context():
            request = BuggyRequest.query.get(request_id)
            request.status = RequestStatus.COMPLETED
            db.session.commit()
        
        # 7. Check status (completed)
        response = client.get(f'/api/requests/{request_id}')
        assert response.status_code == 200
        assert response.get_json()['request']['status'] == 'completed'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
