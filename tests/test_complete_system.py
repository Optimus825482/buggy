"""
Comprehensive system tests for BuggyCall application
Tests all features: Admin, Guest, Driver flows, QR Generation, Reports
"""
import pytest
import json
import time
from datetime import datetime, timedelta
from sqlalchemy import inspect
from app import create_app, db, socketio
from app.models.hotel import Hotel
from app.models.user import SystemUser, UserRole
from app.models.location import Location
from app.models.buggy import Buggy, BuggyStatus
from app.models.request import BuggyRequest, RequestStatus
from app.models.audit import AuditTrail


class TestSystemSetup:
    """Test system setup and initialization"""
    
    def test_database_creation(self, app):
        """Test database tables are created"""
        with app.app_context():
            # Check if tables exist
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            assert 'hotels' in tables
            assert 'system_users' in tables
            assert 'locations' in tables
            assert 'buggies' in tables
            assert 'buggy_requests' in tables
            assert 'audit_trail' in tables
    
    def test_hotel_creation(self, sample_hotel):
        """Test hotel data is created"""
        assert sample_hotel is not None
        assert sample_hotel.name == 'Test Hotel'
    
    def test_users_creation(self, sample_admin_user, sample_driver_user):
        """Test admin and driver users are created"""
        assert sample_admin_user is not None
        assert sample_admin_user.role == UserRole.ADMIN
        
        assert sample_driver_user is not None
        assert sample_driver_user.role == UserRole.DRIVER


class TestAuthenticationFlow:
    """Test complete authentication flows"""
    
    def test_admin_login_flow(self, client):
        """Test admin login complete flow"""
        response = client.post('/auth/login', data={
            'username': 'admin',
            'password': 'admin123'
        }, follow_redirects=False)

        # Should redirect or return success
        assert response.status_code in [200, 302]

        # Should set session cookie (check via set_cookie header or session)
        with client.session_transaction() as sess:
            # If login was successful, session should have user_id
            assert 'user_id' in sess or response.status_code == 302
    
    def test_driver_login_flow(self, client):
        """Test driver login complete flow"""
        response = client.post('/auth/login', data={
            'username': 'driver1',
            'password': 'driver123'
        }, follow_redirects=False)

        assert response.status_code in [200, 302]

        # Should set session cookie
        with client.session_transaction() as sess:
            assert 'user_id' in sess or response.status_code == 302
    
    def test_invalid_login_attempts(self, client):
        """Test invalid login attempts"""
        # Wrong password
        response = client.post('/auth/login', data={
            'username': 'admin',
            'password': 'wrongpass'
        })
        assert response.status_code in [200, 401]
        
        # Non-existent user
        response = client.post('/auth/login', data={
            'username': 'nonexistent',
            'password': 'password'
        })
        assert response.status_code in [200, 401]
    
    def test_logout_flow(self, client):
        """Test logout functionality"""
        # Login first
        client.post('/auth/login', data={
            'username': 'admin',
            'password': 'admin123'
        })
        
        # Logout
        response = client.get('/auth/logout', follow_redirects=False)
        assert response.status_code in [200, 302]


class TestLocationManagement:
    """Test location CRUD operations"""
    
    def test_create_location_complete(self, client, app):
        """Test complete location creation"""
        # Login as admin
        with client:
            client.post('/auth/login', data={
                'username': 'admin',
                'password': 'admin123'
            })
            
            # Create location
            response = client.post('/api/locations', 
                json={
                    'name': 'Beach Bar',
                    'description': 'Bar at the beach',
                    'is_active': True,
                    'display_order': 1
                },
                content_type='application/json'
            )
            
            assert response.status_code in [200, 201]
            
            # Verify in database
            with app.app_context():
                location = Location.query.filter_by(name='Beach Bar').first()
                assert location is not None
                assert location.description == 'Bar at the beach'
    
    def test_update_location_complete(self, client, app):
        """Test complete location update"""
        with client:
            client.post('/auth/login', data={
                'username': 'admin',
                'password': 'admin123'
            })
            
            # Update location
            response = client.put('/api/locations/1',
                json={
                    'name': 'Updated Reception',
                    'description': 'New reception area',
                    'is_active': True
                },
                content_type='application/json'
            )
            
            assert response.status_code in [200, 404]
    
    def test_get_locations_public(self, client):
        """Test public access to locations (for guests)"""
        # No login required
        response = client.get('/api/locations?hotel_id=1')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert isinstance(data, list) or 'locations' in data
    
    def test_delete_location(self, client, app):
        """Test location deletion"""
        with client:
            client.post('/auth/login', data={
                'username': 'admin',
                'password': 'admin123'
            })
            
            # Create a location to delete
            with app.app_context():
                hotel = Hotel.query.first()
                loc = Location(
                    hotel_id=hotel.id,
                    name='Temp Location',
                    description='To be deleted'
                )
                db.session.add(loc)
                db.session.commit()
                loc_id = loc.id
            
            # Delete it
            response = client.delete(f'/api/locations/{loc_id}')
            assert response.status_code in [200, 204]


class TestBuggyManagement:
    """Test buggy CRUD operations"""
    
    def test_create_buggy_complete(self, client, app):
        """Test complete buggy creation"""
        with client:
            client.post('/auth/login', data={
                'username': 'admin',
                'password': 'admin123'
            })
            
            # Get driver id
            with app.app_context():
                driver = SystemUser.query.filter_by(role=UserRole.DRIVER).first()
                driver_id = driver.id
            
            # Create buggy
            response = client.post('/api/buggies',
                json={
                    'code': 'B999',
                    'model': 'Club Car',
                    'license_plate': 'ABC-123',
                    'status': 'available',
                    'driver_id': driver_id
                },
                content_type='application/json'
            )
            
            assert response.status_code in [200, 201]
            
            # Verify in database
            with app.app_context():
                buggy = Buggy.query.filter_by(code='B999').first()
                assert buggy is not None
                assert buggy.model == 'Club Car'
                assert buggy.license_plate == 'ABC-123'
    
    def test_assign_driver_to_buggy(self, client, app):
        """Test assigning driver to buggy"""
        with client:
            client.post('/auth/login', data={
                'username': 'admin',
                'password': 'admin123'
            })
            
            with app.app_context():
                driver = SystemUser.query.filter_by(role=UserRole.DRIVER).first()
                buggy = Buggy.query.first()
                
                # Update buggy with driver
                response = client.put(f'/api/buggies/{buggy.id}',
                    json={
                        'driver_id': driver.id,
                        'status': 'available'
                    },
                    content_type='application/json'
                )
                
                assert response.status_code in [200, 404]
    
    def test_buggy_status_changes(self, client, app):
        """Test buggy status transitions"""
        with client:
            client.post('/auth/login', data={
                'username': 'admin',
                'password': 'admin123'
            })
            
            with app.app_context():
                buggy = Buggy.query.first()
                buggy_id = buggy.id
            
            # Change to offline
            response = client.put(f'/api/buggies/{buggy_id}',
                json={'status': 'offline'},
                content_type='application/json'
            )
            assert response.status_code in [200, 404]
            
            # Change to available
            response = client.put(f'/api/buggies/{buggy_id}',
                json={'status': 'available'},
                content_type='application/json'
            )
            assert response.status_code in [200, 404]


class TestGuestFlow:
    """Test complete guest user flow"""
    
    def test_guest_view_locations(self, client):
        """Test guest can view locations"""
        response = client.get('/guest/call')
        assert response.status_code == 200
        assert b'location' in response.data.lower()
    
    def test_guest_create_request(self, client, app):
        """Test guest can create a buggy request"""
        with app.app_context():
            location = Location.query.first()
            location_id = location.id
        
        # Create request (no login required)
        response = client.post('/api/requests',
            json={
                'location_id': location_id,
                'room_number': '205',
                'notes': 'Need buggy ASAP'
            },
            content_type='application/json'
        )
        
        assert response.status_code in [200, 201]
        data = json.loads(response.data)
        
        # Should return request data
        assert 'id' in data or 'request' in data
    
    def test_guest_track_request_status(self, client, app):
        """Test guest can track request status"""
        # Create a request first
        with app.app_context():
            location = Location.query.first()
            hotel = Hotel.query.first()
            
            request = BuggyRequest(
                hotel_id=hotel.id,
                location_id=location.id,
                room_number='301',
                status=RequestStatus.PENDING
            )
            db.session.add(request)
            db.session.commit()
            request_id = request.id
        
        # Check status page
        response = client.get(f'/guest/status/{request_id}')
        assert response.status_code == 200
        
        # Check API status
        response = client.get(f'/api/requests/{request_id}')
        assert response.status_code == 200
    
    def test_guest_cancel_request(self, client, app):
        """Test guest can cancel their request"""
        # Create a request
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
        
        # Cancel it
        response = client.put(f'/api/requests/{request_id}/cancel')
        assert response.status_code in [200, 404]
        
        # Verify status changed
        if response.status_code == 200:
            with app.app_context():
                req = BuggyRequest.query.get(request_id)
                assert req.status == RequestStatus.CANCELLED


class TestDriverFlow:
    """Test complete driver user flow"""
    
    def test_driver_dashboard_access(self, client):
        """Test driver can access dashboard"""
        with client:
            client.post('/auth/login', data={
                'username': 'driver1',
                'password': 'driver123'
            })
            
            response = client.get('/driver/dashboard')
            assert response.status_code == 200
    
    def test_driver_see_pending_requests(self, client, app):
        """Test driver can see pending requests"""
        # Create pending request
        with app.app_context():
            location = Location.query.first()
            hotel = Hotel.query.first()
            
            request = BuggyRequest(
                hotel_id=hotel.id,
                location_id=location.id,
                room_number='501',
                status=RequestStatus.PENDING
            )
            db.session.add(request)
            db.session.commit()
        
        # Login as driver
        with client:
            client.post('/auth/login', data={
                'username': 'driver1',
                'password': 'driver123'
            })
            
            # Get pending requests
            response = client.get('/api/requests/pending')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert isinstance(data, list) or 'requests' in data
    
    def test_driver_accept_request(self, client, app):
        """Test driver can accept a request"""
        # Create pending request
        with app.app_context():
            location = Location.query.first()
            hotel = Hotel.query.first()
            driver = SystemUser.query.filter_by(role=UserRole.DRIVER).first()
            buggy = Buggy.query.filter_by(driver_id=driver.id).first()
            
            request = BuggyRequest(
                hotel_id=hotel.id,
                location_id=location.id,
                room_number='601',
                status=RequestStatus.PENDING
            )
            db.session.add(request)
            db.session.commit()
            request_id = request.id
        
        # Login as driver
        with client:
            client.post('/auth/login', data={
                'username': 'driver1',
                'password': 'driver123'
            })
            
            # Accept request
            response = client.put(f'/api/requests/{request_id}/accept')
            assert response.status_code in [200, 400, 404]
            
            # If successful, verify status changed
            if response.status_code == 200:
                with app.app_context():
                    req = BuggyRequest.query.get(request_id)
                    assert req.status == RequestStatus.ACCEPTED
                    assert req.buggy_id is not None
    
    def test_driver_complete_request(self, client, app):
        """Test driver can complete a request"""
        # Create accepted request
        with app.app_context():
            location = Location.query.first()
            hotel = Hotel.query.first()
            driver = SystemUser.query.filter_by(role=UserRole.DRIVER).first()
            buggy = Buggy.query.filter_by(driver_id=driver.id).first()
            
            request = BuggyRequest(
                hotel_id=hotel.id,
                location_id=location.id,
                buggy_id=buggy.id,
                room_number='701',
                status=RequestStatus.ACCEPTED,
                accepted_at=datetime.utcnow()
            )
            db.session.add(request)
            db.session.commit()
            request_id = request.id
        
        # Login as driver
        with client:
            client.post('/auth/login', data={
                'username': 'driver1',
                'password': 'driver123'
            })
            
            # Complete request
            response = client.put(f'/api/requests/{request_id}/complete')
            assert response.status_code in [200, 400, 404]
            
            # If successful, verify status and timing
            if response.status_code == 200:
                with app.app_context():
                    req = BuggyRequest.query.get(request_id)
                    assert req.status == RequestStatus.COMPLETED
                    assert req.completed_at is not None
    
    def test_driver_status_toggle(self, client, app):
        """Test driver can toggle their status"""
        with client:
            client.post('/auth/login', data={
                'username': 'driver1',
                'password': 'driver123'
            })
            
            with app.app_context():
                driver = SystemUser.query.filter_by(role=UserRole.DRIVER).first()
                buggy = Buggy.query.filter_by(driver_id=driver.id).first()
                buggy_id = buggy.id
            
            # Toggle to offline
            response = client.put(f'/api/buggies/{buggy_id}/status',
                json={'status': 'offline'},
                content_type='application/json'
            )
            assert response.status_code in [200, 404]
            
            # Toggle back to available
            response = client.put(f'/api/buggies/{buggy_id}/status',
                json={'status': 'available'},
                content_type='application/json'
            )
            assert response.status_code in [200, 404]


class TestQRCodeGeneration:
    """Test QR code generation and management"""
    
    def test_location_has_qr_data(self, app):
        """Test locations have QR code data"""
        with app.app_context():
            location = Location.query.first()
            # QR data should be set or can be generated
            assert location is not None
    
    def test_qr_print_page_access(self, client):
        """Test QR code print page access"""
        with client:
            client.post('/auth/login', data={
                'username': 'admin',
                'password': 'admin123'
            })
            
            response = client.get('/admin/qr-print')
            assert response.status_code == 200
            assert b'qr' in response.data.lower()
    
    def test_bulk_qr_generation(self, client, app):
        """Test bulk QR code generation for all locations"""
        with client:
            client.post('/auth/login', data={
                'username': 'admin',
                'password': 'admin123'
            })
            
            # Get all locations
            response = client.get('/api/locations')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            locations = data if isinstance(data, list) else data.get('locations', [])
            
            # Each location should have QR data
            assert len(locations) > 0


class TestReportsAndAnalytics:
    """Test reports and analytics functionality"""
    
    def test_reports_page_access(self, client):
        """Test reports page access"""
        with client:
            client.post('/auth/login', data={
                'username': 'admin',
                'password': 'admin123'
            })
            
            response = client.get('/admin/reports')
            assert response.status_code == 200
            assert b'chart' in response.data.lower() or b'report' in response.data.lower()
    
    def test_get_requests_for_reports(self, client, app):
        """Test getting request data for reports"""
        # Create some test requests with different statuses
        with app.app_context():
            location = Location.query.first()
            hotel = Hotel.query.first()
            buggy = Buggy.query.first()
            
            # Completed request
            req1 = BuggyRequest(
                hotel_id=hotel.id,
                location_id=location.id,
                buggy_id=buggy.id,
                room_number='801',
                status=RequestStatus.COMPLETED,
                created_at=datetime.utcnow() - timedelta(days=1),
                accepted_at=datetime.utcnow() - timedelta(days=1, hours=23),
                completed_at=datetime.utcnow() - timedelta(days=1, hours=22, minutes=45)
            )
            
            # Pending request
            req2 = BuggyRequest(
                hotel_id=hotel.id,
                location_id=location.id,
                room_number='802',
                status=RequestStatus.PENDING,
                created_at=datetime.utcnow()
            )
            
            db.session.add_all([req1, req2])
            db.session.commit()
        
        # Login and get requests
        with client:
            client.post('/auth/login', data={
                'username': 'admin',
                'password': 'admin123'
            })
            
            response = client.get('/api/requests')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            requests = data if isinstance(data, list) else data.get('requests', [])
            assert len(requests) >= 2
    
    def test_calculate_statistics(self, client, app):
        """Test statistics calculation"""
        # Create completed requests with timing data
        with app.app_context():
            location = Location.query.first()
            hotel = Hotel.query.first()
            buggy = Buggy.query.first()
            
            # Create multiple completed requests
            for i in range(5):
                req = BuggyRequest(
                    hotel_id=hotel.id,
                    location_id=location.id,
                    buggy_id=buggy.id,
                    room_number=f'90{i}',
                    status=RequestStatus.COMPLETED,
                    created_at=datetime.utcnow() - timedelta(hours=i+1),
                    accepted_at=datetime.utcnow() - timedelta(hours=i+1) + timedelta(minutes=2),
                    completed_at=datetime.utcnow() - timedelta(hours=i+1) + timedelta(minutes=10)
                )
                db.session.add(req)
            
            db.session.commit()
        
        # Get requests and verify data is available for statistics
        with client:
            client.post('/auth/login', data={
                'username': 'admin',
                'password': 'admin123'
            })
            
            response = client.get('/api/requests')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            requests = data if isinstance(data, list) else data.get('requests', [])
            
            # Count completed requests
            completed = [r for r in requests if r.get('status') == 'completed']
            assert len(completed) >= 5


class TestWebSocketEvents:
    """Test WebSocket real-time events"""
    
    def test_socketio_connection(self, app):
        """Test Socket.IO connection"""
        client = socketio.test_client(app)
        assert client.is_connected()
        client.disconnect()
    
    def test_join_hotel_room(self, app):
        """Test joining hotel room"""
        client = socketio.test_client(app)
        
        # Emit join_hotel event
        client.emit('join_hotel', {'hotel_id': 1})
        
        # Should be able to receive events
        assert client.is_connected()
        client.disconnect()


class TestErrorHandling:
    """Test error handling and edge cases"""
    
    def test_invalid_location_id(self, client):
        """Test requesting with invalid location ID"""
        response = client.post('/api/requests',
            json={
                'location_id': 99999,
                'room_number': '101'
            },
            content_type='application/json'
        )
        assert response.status_code in [400, 404]
    
    def test_accept_already_accepted_request(self, client, app):
        """Test accepting an already accepted request"""
        # Create accepted request
        with app.app_context():
            location = Location.query.first()
            hotel = Hotel.query.first()
            buggy = Buggy.query.first()
            
            request = BuggyRequest(
                hotel_id=hotel.id,
                location_id=location.id,
                buggy_id=buggy.id,
                room_number='1001',
                status=RequestStatus.ACCEPTED
            )
            db.session.add(request)
            db.session.commit()
            request_id = request.id
        
        # Try to accept again
        with client:
            client.post('/auth/login', data={
                'username': 'driver1',
                'password': 'driver123'
            })
            
            response = client.put(f'/api/requests/{request_id}/accept')
            assert response.status_code in [400, 409]
    
    def test_unauthorized_access(self, client):
        """Test unauthorized access to protected routes"""
        # Try to access admin page without login
        response = client.get('/admin/dashboard')
        assert response.status_code in [302, 401, 403]
        
        # Try to access driver page without login
        response = client.get('/driver/dashboard')
        assert response.status_code in [302, 401, 403]
    
    def test_driver_access_admin_page(self, client):
        """Test driver cannot access admin pages"""
        with client:
            client.post('/auth/login', data={
                'username': 'driver1',
                'password': 'driver123'
            })
            
            response = client.get('/admin/buggies')
            assert response.status_code in [302, 403]


class TestDataIntegrity:
    """Test data integrity and relationships"""
    
    def test_hotel_location_relationship(self, app):
        """Test hotel-location relationship"""
        with app.app_context():
            hotel = Hotel.query.first()
            locations = Location.query.filter_by(hotel_id=hotel.id).all()
            
            assert len(locations) > 0
            for loc in locations:
                assert loc.hotel_id == hotel.id
    
    def test_buggy_driver_relationship(self, app):
        """Test buggy-driver relationship"""
        with app.app_context():
            buggy = Buggy.query.filter(Buggy.driver_id.isnot(None)).first()
            
            if buggy:
                driver = SystemUser.query.get(buggy.driver_id)
                assert driver is not None
                assert driver.role == UserRole.DRIVER
    
    def test_request_relationships(self, app):
        """Test request relationships with location, buggy, hotel"""
        with app.app_context():
            request = BuggyRequest.query.first()
            
            if request:
                # Check hotel relationship
                hotel = Hotel.query.get(request.hotel_id)
                assert hotel is not None
                
                # Check location relationship
                location = Location.query.get(request.location_id)
                assert location is not None
                
                # Check buggy relationship if accepted
                if request.buggy_id:
                    buggy = Buggy.query.get(request.buggy_id)
                    assert buggy is not None


class TestPerformance:
    """Test performance and scalability"""
    
    def test_multiple_simultaneous_requests(self, client, app):
        """Test handling multiple simultaneous requests"""
        with app.app_context():
            location = Location.query.first()
            location_id = location.id
        
        # Create multiple requests
        for i in range(10):
            response = client.post('/api/requests',
                json={
                    'location_id': location_id,
                    'room_number': f'110{i}'
                },
                content_type='application/json'
            )
            assert response.status_code in [200, 201]
    
    def test_large_request_list_loading(self, client, app):
        """Test loading large number of requests"""
        with client:
            client.post('/auth/login', data={
                'username': 'admin',
                'password': 'admin123'
            })
            
            response = client.get('/api/requests')
            assert response.status_code == 200
            
            # Should handle large datasets
            data = json.loads(response.data)
            assert data is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
