import pytest
import json
from datetime import datetime
from flask import session
from app import create_app, db
from app.models.user import SystemUser, UserRole
from app.models.buggy import Buggy, BuggyStatus
from app.models.location import Location
from app.models.request import BuggyRequest, RequestStatus
from app.models.hotel import Hotel


class TestIntegration:
    """Integration tests for complete workflows"""
    
    @pytest.fixture
    def setup_complete_scenario(self, app, db_session):
        """Setup complete test scenario with hotel, locations, buggies, drivers"""
        # Create hotel
        hotel = Hotel(
            name="Test Resort",
            address="Test Address",
            phone="123456789",
            email="test@resort.com"
        )
        db_session.add(hotel)
        db_session.flush()
        
        # Create locations with unique QR codes
        import uuid
        unique_id = uuid.uuid4().hex[:8]
        
        pool_area = Location(
            hotel_id=hotel.id,
            name="Pool Area",
            description="Resort pool area",
            qr_code_data=f"LOC{unique_id}001",
            is_active=True
        )
        main_entrance = Location(
            hotel_id=hotel.id,
            name="Main Entrance",
            description="Resort main entrance",
            qr_code_data=f"LOC{unique_id}002",
            is_active=True
        )
        restaurant = Location(
            hotel_id=hotel.id,
            name="Restaurant",
            description="Resort restaurant",
            qr_code_data=f"LOC{unique_id}003",
            is_active=True
        )
        db_session.add_all([pool_area, main_entrance, restaurant])
        db_session.flush()
        
        # Create buggies with unique codes
        buggy1 = Buggy(
            hotel_id=hotel.id,
            code=f"B{unique_id}001",
            license_plate=f"34 {unique_id[:3].upper()} 001",
            model="Club Car",
            status=BuggyStatus.AVAILABLE,
            current_location_id=pool_area.id
        )
        buggy2 = Buggy(
            hotel_id=hotel.id,
            code=f"B{unique_id}002",
            license_plate=f"34 {unique_id[:3].upper()} 002",
            model="Club Car",
            status=BuggyStatus.AVAILABLE,
            current_location_id=main_entrance.id
        )
        db_session.add_all([buggy1, buggy2])
        db_session.flush()
        
        # Create drivers with unique usernames
        driver1 = SystemUser(
            hotel_id=hotel.id,
            username=f"driver1_{unique_id}",
            email=f"driver1_{unique_id}@test.com",
            full_name="John Driver",
            role=UserRole.DRIVER,
            is_active=True
        )
        driver1.set_password("password123")

        driver2 = SystemUser(
            hotel_id=hotel.id,
            username=f"driver2_{unique_id}",
            email=f"driver2_{unique_id}@test.com",
            full_name="Jane Driver",
            role=UserRole.DRIVER,
            is_active=True
        )
        driver2.set_password("password123")

        # Assign buggies to drivers
        buggy1.driver_id = driver1.id
        buggy2.driver_id = driver2.id

        # Create admin with unique username
        admin = SystemUser(
            hotel_id=hotel.id,
            username=f"admin_{unique_id}",
            email=f"admin_{unique_id}@test.com",
            full_name="Admin User",
            role=UserRole.ADMIN,
            is_active=True
        )
        admin.set_password("admin123")
        
        db_session.add_all([driver1, driver2, admin])
        db_session.commit()
        
        return {
            'hotel': hotel,
            'locations': {
                'pool': pool_area,
                'entrance': main_entrance,
                'restaurant': restaurant
            },
            'buggies': {
                'b001': buggy1,
                'b002': buggy2
            },
            'drivers': {
                'driver1': driver1,
                'driver2': driver2
            },
            'admin': admin
        }
    
    def test_complete_guest_to_driver_workflow(self, client, setup_complete_scenario):
        """Test complete workflow from guest request to driver completion"""
        data = setup_complete_scenario
        
        # Step 1: Guest creates request from pool area
        guest_response = client.post('/api/requests', json={
            'hotel_id': data['hotel'].id,
            'location_id': data['locations']['pool'].id,
            'guest_name': 'Alice Guest',
            'room_number': '205',
            'guest_count': 2
        })
        
        assert guest_response.status_code == 201
        request_data = guest_response.get_json()
        request_id = request_data['request']['id']
        
        # Step 2: Driver1 logs in and accepts the request
        login_response = client.post('/auth/login', json={
            'username': 'driver1',
            'password': 'password123'
        })
        assert login_response.status_code == 200
        
        # Accept the request
        accept_response = client.post(f'/api/driver/accept-request/{request_id}')
        assert accept_response.status_code == 200
        
        # Verify request status changed
        status_response = client.get(f'/api/requests/{request_id}')
        status_data = status_response.get_json()
        assert status_data['request']['status'] == 'accepted'
        assert status_data['request']['buggy_code'] == 'B001'
        
        # Verify buggy status changed to busy
        buggy = Buggy.query.get(data['buggies']['b001'].id)
        assert buggy.status == BuggyStatus.BUSY
        
        # Step 3: Driver completes the request
        complete_response = client.post(f'/api/driver/complete-request/{request_id}')
        assert complete_response.status_code == 200
        
        # Verify request was completed
        final_status = client.get(f'/api/requests/{request_id}')
        final_data = final_status.get_json()
        assert final_data['request']['status'] == 'completed'
        
        # Step 4: Driver sets new location
        location_response = client.post('/api/driver/set-location', json={
            'location_id': data['locations']['restaurant'].id
        })
        assert location_response.status_code == 200
        
        # Verify buggy is available at new location
        updated_buggy = Buggy.query.get(data['buggies']['b001'].id)
        assert updated_buggy.status == BuggyStatus.AVAILABLE
        assert updated_buggy.current_location_id == data['locations']['restaurant'].id
    
    def test_multiple_drivers_race_condition(self, client, setup_complete_scenario):
        """Test race condition when multiple drivers try to accept same request"""
        data = setup_complete_scenario
        
        # Create request
        guest_response = client.post('/api/requests', json={
            'hotel_id': data['hotel'].id,
            'location_id': data['locations']['entrance'].id,
            'guest_name': 'Bob Guest',
            'room_number': '301',
            'guest_count': 1
        })
        request_id = guest_response.get_json()['request']['id']
        
        # Driver1 accepts first
        client.post('/auth/login', json={
            'username': 'driver1',
            'password': 'password123'
        })
        
        accept1_response = client.post(f'/api/driver/accept-request/{request_id}')
        assert accept1_response.status_code == 200
        
        # Driver2 tries to accept same request
        client.post('/auth/logout')
        client.post('/auth/login', json={
            'username': 'driver2',
            'password': 'password123'
        })
        
        accept2_response = client.post(f'/api/driver/accept-request/{request_id}')
        assert accept2_response.status_code == 404  # Request no longer available
        
        # Verify only driver1 got the request
        request = BuggyRequest.query.get(request_id)
        assert request.buggy_id == data['buggies']['b001'].id
        assert request.accepted_by_id == data['drivers']['driver1'].id
    
    def test_admin_session_management_workflow(self, client, setup_complete_scenario):
        """Test admin managing driver sessions"""
        data = setup_complete_scenario
        
        # Driver logs in
        client.post('/auth/login', json={
            'username': 'driver1',
            'password': 'password123'
        })
        
        # Admin logs in (new client session)
        client.post('/auth/logout')
        admin_login = client.post('/auth/login', json={
            'username': 'admin',
            'password': 'admin123'
        })
        assert admin_login.status_code == 200
        
        # Admin views active sessions
        sessions_response = client.get('/api/admin/sessions')
        assert sessions_response.status_code == 200
        sessions_data = sessions_response.get_json()
        
        # Find driver session
        driver_session = None
        for session in sessions_data['sessions']:
            if session['user_id'] == data['drivers']['driver1'].id:
                driver_session = session
                break
        
        assert driver_session is not None
        assert driver_session['is_active'] is True
        
        # Admin terminates driver session
        terminate_response = client.post(f'/api/admin/sessions/{driver_session["id"]}/terminate')
        assert terminate_response.status_code == 200
        
        # Verify session was terminated
        updated_sessions = client.get('/api/admin/sessions')
        updated_data = updated_sessions.get_json()
        
        terminated_session = None
        for session in updated_data['sessions']:
            if session['id'] == driver_session['id']:
                terminated_session = session
                break
        
        # Session should either be gone or marked inactive
        if terminated_session:
            assert terminated_session['is_active'] is False
    
    def test_guest_status_tracking_real_time(self, client, setup_complete_scenario):
        """Test guest can track request status through different stages"""
        data = setup_complete_scenario
        
        # Guest creates request
        guest_response = client.post('/api/requests', json={
            'hotel_id': data['hotel'].id,
            'location_id': data['locations']['pool'].id,
            'guest_name': 'Charlie Guest',
            'room_number': '101',
            'guest_count': 3
        })
        request_id = guest_response.get_json()['request']['id']
        
        # Check initial status (PENDING)
        status1 = client.get(f'/api/requests/{request_id}')
        assert status1.get_json()['request']['status'] == 'PENDING'
        
        # Driver accepts
        client.post('/auth/login', json={
            'username': 'driver2',
            'password': 'password123'
        })
        client.post(f'/api/driver/accept-request/{request_id}')
        
        # Check status (accepted)
        status2 = client.get(f'/api/requests/{request_id}')
        request_data = status2.get_json()['request']
        assert request_data['status'] == 'accepted'
        assert request_data['buggy_code'] == 'B002'
        assert request_data['driver_name'] == 'Jane Driver'
        
        # Driver completes
        client.post(f'/api/driver/complete-request/{request_id}')
        
        # Check final status (completed)
        status3 = client.get(f'/api/requests/{request_id}')
        assert status3.get_json()['request']['status'] == 'completed'
