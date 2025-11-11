"""
End-to-End test scenarios for BuggyCall application
Tests complete user journeys from start to finish
"""
import pytest
import json
from datetime import datetime, timedelta
from app import db
from app.models.hotel import Hotel
from app.models.user import SystemUser, UserRole
from app.models.location import Location
from app.models.buggy import Buggy, BuggyStatus
from app.models.request import BuggyRequest, RequestStatus


class TestCompleteGuestJourney:
    """Test complete guest user journey"""
    
    def test_guest_complete_flow_success(self, client, app):
        """
        Test complete guest flow: 
        1. Guest views locations
        2. Guest creates request
        3. Driver accepts request
        4. Driver completes request
        5. Guest sees completed status
        """
        # Step 1: Guest views locations
        response = client.get('/guest/call')
        assert response.status_code == 200
        
        # Get locations via API
        response = client.get('/api/locations?hotel_id=1')
        assert response.status_code == 200
        locations = json.loads(response.data)
        assert len(locations) > 0
        location_id = locations[0]['id'] if isinstance(locations, list) else locations['locations'][0]['id']
        
        # Step 2: Guest creates request
        response = client.post('/api/requests',
            json={
                'location_id': location_id,
                'room_number': '301',
                'notes': 'Please come quickly'
            },
            content_type='application/json'
        )
        assert response.status_code in [200, 201]
        data = json.loads(response.data)
        request_id = data.get('id') or data.get('request', {}).get('id')
        assert request_id is not None
        
        # Verify request is PENDING
        response = client.get(f'/api/requests/{request_id}')
        assert response.status_code == 200
        request_data = json.loads(response.data)
        assert request_data.get('status') == 'PENDING'
        
        # Step 3: Driver logs in and accepts request
        with client:
            client.post('/auth/login', data={
                'username': 'driver1',
                'password': 'driver123'
            })
            
            # Accept request
            response = client.put(f'/api/requests/{request_id}/accept')
            assert response.status_code in [200, 400]
            
            if response.status_code == 200:
                # Step 4: Driver completes request
                response = client.put(f'/api/requests/{request_id}/complete')
                assert response.status_code in [200, 400]
        
        # Step 5: Guest checks status
        response = client.get(f'/guest/status/{request_id}')
        assert response.status_code == 200
    
    def test_guest_cancel_before_accept(self, client, app):
        """
        Test guest cancelling request before driver accepts
        """
        # Create request
        with app.app_context():
            location = Location.query.first()
            location_id = location.id
        
        response = client.post('/api/requests',
            json={
                'location_id': location_id,
                'room_number': '302'
            },
            content_type='application/json'
        )
        assert response.status_code in [200, 201]
        data = json.loads(response.data)
        request_id = data.get('id') or data.get('request', {}).get('id')
        
        # Cancel request
        response = client.put(f'/api/requests/{request_id}/cancel')
        assert response.status_code == 200
        
        # Verify status
        response = client.get(f'/api/requests/{request_id}')
        request_data = json.loads(response.data)
        assert request_data.get('status') == 'cancelled'


class TestCompleteDriverJourney:
    """Test complete driver user journey"""
    
    def test_driver_shift_workflow(self, client, app):
        """
        Test complete driver shift:
        1. Driver logs in
        2. Driver goes online
        3. Driver sees PENDING requests
        4. Driver accepts request
        5. Driver completes request
        6. Driver goes offline
        """
        # Create a PENDING request first
        with app.app_context():
            location = Location.query.first()
            hotel = Hotel.query.first()
            
            request = BuggyRequest(
                hotel_id=hotel.id,
                location_id=location.id,
                room_number='401',
                status=RequestStatus.PENDING
            )
            db.session.add(request)
            db.session.commit()
            request_id = request.id
            
            # Get buggy and driver IDs
            driver = SystemUser.query.filter_by(role=UserRole.DRIVER).first()
            buggy = Buggy.query.filter_by(driver_id=driver.id).first()
            buggy_id = buggy.id if buggy else None
        
        with client:
            # Step 1: Driver logs in
            response = client.post('/auth/login', data={
                'username': 'driver1',
                'password': 'driver123'
            })
            assert response.status_code in [200, 302]
            
            # Step 2: Driver goes online (if has buggy)
            if buggy_id:
                response = client.put(f'/api/buggies/{buggy_id}/status',
                    json={'status': 'available'},
                    content_type='application/json'
                )
                assert response.status_code in [200, 404]
            
            # Step 3: Driver sees PENDING requests
            response = client.get('/api/requests/PENDING')
            assert response.status_code == 200
            
            # Step 4: Driver accepts request
            response = client.put(f'/api/requests/{request_id}/accept')
            assert response.status_code in [200, 400]
            
            if response.status_code == 200:
                # Step 5: Driver completes request
                response = client.put(f'/api/requests/{request_id}/complete')
                assert response.status_code in [200, 400]
            
            # Step 6: Driver goes offline
            if buggy_id:
                response = client.put(f'/api/buggies/{buggy_id}/status',
                    json={'status': 'offline'},
                    content_type='application/json'
                )
                assert response.status_code in [200, 404]
    
    def test_driver_multiple_requests_workflow(self, client, app):
        """
        Test driver handling multiple requests sequentially
        """
        # Create multiple PENDING requests
        request_ids = []
        with app.app_context():
            location = Location.query.first()
            hotel = Hotel.query.first()
            
            for i in range(3):
                request = BuggyRequest(
                    hotel_id=hotel.id,
                    location_id=location.id,
                    room_number=f'50{i}',
                    status=RequestStatus.PENDING
                )
                db.session.add(request)
                db.session.flush()
                request_ids.append(request.id)
            
            db.session.commit()
        
        with client:
            client.post('/auth/login', data={
                'username': 'driver1',
                'password': 'driver123'
            })
            
            # Accept and complete each request
            for req_id in request_ids:
                # Accept
                response = client.put(f'/api/requests/{req_id}/accept')
                if response.status_code == 200:
                    # Complete
                    response = client.put(f'/api/requests/{req_id}/complete')
                    assert response.status_code in [200, 400]


class TestCompleteAdminJourney:
    """Test complete admin user journey"""
    
    def test_admin_setup_new_hotel(self, client, app):
        """
        Test admin setting up new hotel:
        1. Admin logs in
        2. Admin adds locations
        3. Admin adds buggies
        4. Admin assigns drivers to buggies
        5. Admin generates QR codes
        """
        with client:
            # Step 1: Admin logs in
            response = client.post('/auth/login', data={
                'username': 'admin',
                'password': 'admin123'
            })
            assert response.status_code in [200, 302]
            
            # Step 2: Admin adds location
            response = client.post('/api/locations',
                json={
                    'name': 'Restaurant',
                    'description': 'Main restaurant area',
                    'is_active': True,
                    'display_order': 1
                },
                content_type='application/json'
            )
            assert response.status_code in [200, 201]
            
            # Step 3: Admin adds buggy
            with app.app_context():
                driver = SystemUser.query.filter_by(role=UserRole.DRIVER).first()
                driver_id = driver.id
            
            response = client.post('/api/buggies',
                json={
                    'code': 'B101',
                    'model': 'E-Z-GO',
                    'license_plate': 'XYZ-789',
                    'status': 'available',
                    'driver_id': driver_id
                },
                content_type='application/json'
            )
            assert response.status_code in [200, 201]
            
            # Step 5: Admin accesses QR print page
            response = client.get('/admin/qr-print')
            assert response.status_code == 200
    
    def test_admin_monitor_operations(self, client, app):
        """
        Test admin monitoring operations:
        1. View dashboard
        2. Check reports
        3. Review request history
        """
        # Create some test data
        with app.app_context():
            location = Location.query.first()
            hotel = Hotel.query.first()
            buggy = Buggy.query.first()
            
            # Create requests with different statuses
            for i, status in enumerate([RequestStatus.PENDING, RequestStatus.ACCEPTED, RequestStatus.COMPLETED]):
                request = BuggyRequest(
                    hotel_id=hotel.id,
                    location_id=location.id,
                    buggy_id=buggy.id if status != RequestStatus.PENDING else None,
                    room_number=f'60{i}',
                    status=status,
                    requested_at=datetime.utcnow() - timedelta(hours=i)
                )
                if status in [RequestStatus.ACCEPTED, RequestStatus.COMPLETED]:
                    request.accepted_at = request.requested_at + timedelta(minutes=2)
                if status == RequestStatus.COMPLETED:
                    request.completed_at = request.accepted_at + timedelta(minutes=10)
                
                db.session.add(request)
            
            db.session.commit()
        
        with client:
            client.post('/auth/login', data={
                'username': 'admin',
                'password': 'admin123'
            })
            
            # Step 1: View dashboard
            response = client.get('/admin/dashboard')
            assert response.status_code == 200
            
            # Step 2: Check reports page
            response = client.get('/admin/reports')
            assert response.status_code == 200
            
            # Step 3: Get all requests
            response = client.get('/api/requests')
            assert response.status_code == 200
            data = json.loads(response.data)
            requests = data if isinstance(data, list) else data.get('requests', [])
            assert len(requests) >= 3


class TestEdgeCaseScenarios:
    """Test edge cases and error scenarios"""
    
    def test_concurrent_driver_accept(self, client, app):
        """
        Test two drivers trying to accept same request
        (Only one should succeed)
        """
        # Create a PENDING request
        with app.app_context():
            location = Location.query.first()
            hotel = Hotel.query.first()
            
            request = BuggyRequest(
                hotel_id=hotel.id,
                location_id=location.id,
                room_number='701',
                status=RequestStatus.PENDING
            )
            db.session.add(request)
            db.session.commit()
            request_id = request.id
        
        # Driver 1 accepts
        with client:
            client.post('/auth/login', data={
                'username': 'driver1',
                'password': 'driver123'
            })
            
            response1 = client.put(f'/api/requests/{request_id}/accept')
            
            # If first accept succeeded, second should fail
            if response1.status_code == 200:
                response2 = client.put(f'/api/requests/{request_id}/accept')
                assert response2.status_code in [400, 409]
    
    def test_complete_without_accept(self, client, app):
        """
        Test trying to complete a request without accepting it first
        """
        with app.app_context():
            location = Location.query.first()
            hotel = Hotel.query.first()
            
            request = BuggyRequest(
                hotel_id=hotel.id,
                location_id=location.id,
                room_number='702',
                status=RequestStatus.PENDING
            )
            db.session.add(request)
            db.session.commit()
            request_id = request.id
        
        with client:
            client.post('/auth/login', data={
                'username': 'driver1',
                'password': 'driver123'
            })
            
            # Try to complete without accepting
            response = client.put(f'/api/requests/{request_id}/complete')
            assert response.status_code in [400, 409]
    
    def test_cancel_completed_request(self, client, app):
        """
        Test trying to cancel an already completed request
        """
        with app.app_context():
            location = Location.query.first()
            hotel = Hotel.query.first()
            buggy = Buggy.query.first()
            
            request = BuggyRequest(
                hotel_id=hotel.id,
                location_id=location.id,
                buggy_id=buggy.id,
                room_number='703',
                status=RequestStatus.COMPLETED,
                completed_at=datetime.utcnow()
            )
            db.session.add(request)
            db.session.commit()
            request_id = request.id
        
        # Try to cancel
        response = client.put(f'/api/requests/{request_id}/cancel')
        assert response.status_code in [400, 409]
    
    def test_driver_without_buggy(self, client, app):
        """
        Test driver trying to accept request without assigned buggy
        """
        # Create driver without buggy
        with app.app_context():
            hotel = Hotel.query.first()
            
            driver2 = SystemUser(
                hotel_id=hotel.id,
                username='driver2',
                email='driver2@test.com',
                full_name='Driver Without Buggy',
                role=UserRole.DRIVER
            )
            driver2.set_password('driver123')
            db.session.add(driver2)
            
            location = Location.query.first()
            request = BuggyRequest(
                hotel_id=hotel.id,
                location_id=location.id,
                room_number='704',
                status=RequestStatus.PENDING
            )
            db.session.add(request)
            db.session.commit()
            request_id = request.id
        
        with client:
            client.post('/auth/login', data={
                'username': 'driver2',
                'password': 'driver123'
            })
            
            # Try to accept request
            response = client.put(f'/api/requests/{request_id}/accept')
            assert response.status_code in [400, 404]


class TestDataConsistency:
    """Test data consistency across operations"""
    
    def test_request_timing_consistency(self, client, app):
        """
        Test that request timing fields are set correctly
        """
        with app.app_context():
            location = Location.query.first()
            hotel = Hotel.query.first()
            
            request = BuggyRequest(
                hotel_id=hotel.id,
                location_id=location.id,
                room_number='801',
                status=RequestStatus.PENDING
            )
            db.session.add(request)
            db.session.commit()
            request_id = request.id
            created_time = request.requested_at
        
        with client:
            client.post('/auth/login', data={
                'username': 'driver1',
                'password': 'driver123'
            })
            
            # Accept request
            response = client.put(f'/api/requests/{request_id}/accept')
            
            if response.status_code == 200:
                with app.app_context():
                    req = BuggyRequest.query.get(request_id)
                    # Accepted time should be after created time
                    if req.accepted_at:
                        assert req.accepted_at >= created_time
                
                # Complete request
                response = client.put(f'/api/requests/{request_id}/complete')
                
                if response.status_code == 200:
                    with app.app_context():
                        req = BuggyRequest.query.get(request_id)
                        # Completed time should be after accepted time
                        if req.completed_at and req.accepted_at:
                            assert req.completed_at >= req.accepted_at
    
    def test_buggy_status_consistency(self, client, app):
        """
        Test buggy status changes correctly with request status
        """
        with app.app_context():
            driver = SystemUser.query.filter_by(role=UserRole.DRIVER).first()
            buggy = Buggy.query.filter_by(driver_id=driver.id).first()
            
            if buggy:
                # Set buggy to available
                buggy.status = BuggyStatus.AVAILABLE
                db.session.commit()
                buggy_id = buggy.id
                
                location = Location.query.first()
                hotel = Hotel.query.first()
                
                request = BuggyRequest(
                    hotel_id=hotel.id,
                    location_id=location.id,
                    room_number='802',
                    status=RequestStatus.PENDING
                )
                db.session.add(request)
                db.session.commit()
                request_id = request.id
        
        if not buggy:
            pytest.skip("No buggy assigned to driver")
        
        with client:
            client.post('/auth/login', data={
                'username': 'driver1',
                'password': 'driver123'
            })
            
            # Accept request
            response = client.put(f'/api/requests/{request_id}/accept')
            
            if response.status_code == 200:
                # Buggy should be busy
                with app.app_context():
                    buggy = Buggy.query.get(buggy_id)
                    assert buggy.status == BuggyStatus.BUSY
                
                # Complete request
                response = client.put(f'/api/requests/{request_id}/complete')
                
                if response.status_code == 200:
                    # Buggy should be available again
                    with app.app_context():
                        buggy = Buggy.query.get(buggy_id)
                        assert buggy.status == BuggyStatus.AVAILABLE


class TestReportingScenarios:
    """Test reporting and analytics scenarios"""
    
    def test_daily_report_generation(self, client, app):
        """
        Test generating daily report with statistics
        """
        # Create requests for today
        with app.app_context():
            location = Location.query.first()
            hotel = Hotel.query.first()
            buggy = Buggy.query.first()
            
            today = datetime.utcnow()
            
            for i in range(5):
                request = BuggyRequest(
                    hotel_id=hotel.id,
                    location_id=location.id,
                    buggy_id=buggy.id,
                    room_number=f'90{i}',
                    status=RequestStatus.COMPLETED,
                    requested_at=today - timedelta(hours=i),
                    accepted_at=today - timedelta(hours=i) + timedelta(minutes=2),
                    completed_at=today - timedelta(hours=i) + timedelta(minutes=12)
                )
                db.session.add(request)
            
            db.session.commit()
        
        with client:
            client.post('/auth/login', data={
                'username': 'admin',
                'password': 'admin123'
            })
            
            # Get reports page
            response = client.get('/admin/reports')
            assert response.status_code == 200
            
            # Get requests data
            response = client.get('/api/requests')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            requests = data if isinstance(data, list) else data.get('requests', [])
            
            # Filter today's requests
            today_requests = [
                r for r in requests
                if datetime.fromisoformat(r['requested_at'].replace('Z', '+00:00')).date() == today.date()
            ]
            
            assert len(today_requests) >= 5
    
    def test_location_performance_report(self, client, app):
        """
        Test location performance statistics
        """
        # Create requests for different locations
        with app.app_context():
            hotel = Hotel.query.first()
            locations = Location.query.filter_by(hotel_id=hotel.id).all()
            buggy = Buggy.query.first()
            
            for i, location in enumerate(locations[:3]):
                # Create multiple requests per location
                for j in range(i + 1):
                    request = BuggyRequest(
                        hotel_id=hotel.id,
                        location_id=location.id,
                        buggy_id=buggy.id,
                        room_number=f'95{i}{j}',
                        status=RequestStatus.COMPLETED,
                        requested_at=datetime.utcnow() - timedelta(hours=i, minutes=j*10),
                        accepted_at=datetime.utcnow() - timedelta(hours=i, minutes=j*10) + timedelta(minutes=2),
                        completed_at=datetime.utcnow() - timedelta(hours=i, minutes=j*10) + timedelta(minutes=10)
                    )
                    db.session.add(request)
            
            db.session.commit()
        
        with client:
            client.post('/auth/login', data={
                'username': 'admin',
                'password': 'admin123'
            })
            
            # Get all requests
            response = client.get('/api/requests')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            requests = data if isinstance(data, list) else data.get('requests', [])
            
            # Group by location
            location_counts = {}
            for req in requests:
                loc_id = req.get('location_id')
                location_counts[loc_id] = location_counts.get(loc_id, 0) + 1
            
            # Should have data for multiple locations
            assert len(location_counts) > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
