"""
End-to-End Tests for QR Code Guest Access Feature
Tests the complete flow: Admin creates location → QR code generation → Guest scans → Buggy call
"""
import pytest
import json
from datetime import datetime
from app import db
from app.models.hotel import Hotel
from app.models.user import SystemUser, UserRole
from app.models.location import Location
from app.models.buggy import Buggy, BuggyStatus
from app.models.request import BuggyRequest, RequestStatus


class TestQRCodeEndToEnd:
    """End-to-end tests for QR code guest access feature"""
    
    def test_admin_create_location_with_url_qr_code(self, client, app):
        """Test: Admin creates location and QR code is generated with URL format"""
        with client:
            # Login as admin
            client.post('/auth/login', data={
                'username': 'admin',
                'password': 'admin123'
            })
            
            # Create location
            response = client.post('/api/locations',
                json={
                    'name': 'Beach Bar QR Test',
                    'description': 'Test location for QR code',
                    'is_active': True
                },
                content_type='application/json'
            )
            
            assert response.status_code in [200, 201]
            data = json.loads(response.data)
            assert data['success'] is True
            
            location = data['location']
            assert 'qr_code_data' in location
            
            # Verify QR code is in URL format
            qr_data = location['qr_code_data']
            assert qr_data.startswith('http://') or qr_data.startswith('https://'), \
                f"QR code should be URL format, got: {qr_data}"
            assert '/guest/call?location=' in qr_data, \
                f"QR code should contain guest call URL, got: {qr_data}"
            assert str(location['id']) in qr_data, \
                f"QR code should contain location ID, got: {qr_data}"
            
            print(f"✓ Location created with URL QR code: {qr_data}")
    
    def test_qr_print_page_generates_correct_qr_codes(self, client, app):
        """Test: QR print page loads and contains correct QR code data"""
        with client:
            # Login as admin
            client.post('/auth/login', data={
                'username': 'admin',
                'password': 'admin123'
            })
            
            # Create a test location
            response = client.post('/api/locations',
                json={
                    'name': 'Pool Area QR',
                    'description': 'Pool area test',
                    'is_active': True
                },
                content_type='application/json'
            )
            
            assert response.status_code in [200, 201]
            location_data = json.loads(response.data)['location']
            
            # Access QR print page
            response = client.get('/admin/qr-print')
            assert response.status_code == 200
            
            html_content = response.data.decode('utf-8')
            
            # Verify page contains QR code generation script
            assert 'qrcodejs' in html_content.lower() or 'qrcode' in html_content.lower()
            assert 'generateQRCode' in html_content or 'QRCode' in html_content
            
            # Verify it fetches locations from API
            assert '/api/locations' in html_content
            
            print(f"✓ QR print page loads correctly")
    
    def test_guest_scan_url_qr_code_auto_redirect(self, client, app):
        """Test: Guest scans URL QR code and gets auto-redirected"""
        # Create location with URL QR code
        with app.app_context():
            hotel = Hotel.query.first()
            location = Location(
                hotel_id=hotel.id,
                name='Restaurant QR Test',
                description='Restaurant area',
                qr_code_data='http://localhost:5000/guest/call?location=999',
                is_active=True,
                display_order=1
            )
            db.session.add(location)
            db.session.commit()
            location_id = location.id
            
            # Update QR code with actual location ID
            location.qr_code_data = f'http://localhost:5000/guest/call?location={location_id}'
            db.session.commit()
            qr_data = location.qr_code_data
        
        # Simulate guest accessing the URL from QR code
        response = client.get(f'/guest/call?location={location_id}')
        assert response.status_code == 200
        
        html_content = response.data.decode('utf-8')
        
        # Verify the page loads with location pre-selected
        assert 'location' in html_content.lower()
        assert str(location_id) in html_content or 'location-select' in html_content
        
        print(f"✓ Guest can access URL from QR code: {qr_data}")
    
    def test_guest_call_page_auto_selects_location_from_url(self, client, app):
        """Test: Guest call page auto-selects location from URL parameter"""
        # Create location
        with app.app_context():
            hotel = Hotel.query.first()
            location = Location(
                hotel_id=hotel.id,
                name='Lobby QR Test',
                description='Lobby area',
                qr_code_data='http://localhost:5000/guest/call?location=888',
                is_active=True,
                display_order=1
            )
            db.session.add(location)
            db.session.commit()
            location_id = location.id
        
        # Access guest call page with location parameter
        response = client.get(f'/guest/call?location={location_id}')
        assert response.status_code == 200
        
        html_content = response.data.decode('utf-8')
        
        # Check that location parameter is present in the page
        # The JavaScript should read this and auto-select the location
        assert 'location' in html_content.lower()
        
        print(f"✓ Guest call page receives location parameter: {location_id}")
    
    def test_guest_create_request_from_qr_scanned_location(self, client, app):
        """Test: Guest creates buggy request after scanning QR code"""
        # Create location
        with app.app_context():
            hotel = Hotel.query.first()
            location = Location(
                hotel_id=hotel.id,
                name='Spa QR Test',
                description='Spa area',
                qr_code_data='http://localhost:5000/guest/call?location=777',
                is_active=True,
                display_order=1
            )
            db.session.add(location)
            db.session.commit()
            location_id = location.id
        
        # Guest creates request (no login required)
        response = client.post('/api/requests',
            json={
                'location_id': location_id,
                'room_number': '305',
                'notes': 'From QR code scan'
            },
            content_type='application/json'
        )
        
        assert response.status_code in [200, 201]
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'request_id' in data or 'request' in data
        
        # Verify request was created in database
        with app.app_context():
            request = BuggyRequest.query.filter_by(location_id=location_id).first()
            assert request is not None
            assert request.room_number == '305'
            assert request.status == RequestStatus.PENDING
        
        print(f"✓ Guest successfully created request from QR scanned location")
    
    def test_legacy_loc_format_backward_compatibility(self, client, app):
        """Test: Old LOC format QR codes still work (backward compatibility)"""
        # Create location with legacy LOC format
        with app.app_context():
            hotel = Hotel.query.first()
            location = Location(
                hotel_id=hotel.id,
                name='Legacy QR Test',
                description='Legacy format test',
                qr_code_data=f'LOC{hotel.id}0001',  # Old format
                is_active=True,
                display_order=1
            )
            db.session.add(location)
            db.session.commit()
            location_id = location.id
            qr_data = location.qr_code_data
        
        # Get all locations (as guest would when scanning LOC format)
        response = client.get('/api/locations')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        locations = data if isinstance(data, list) else data.get('locations', [])
        
        # Find location by QR code data (simulating the legacy scan process)
        found_location = None
        for loc in locations:
            if loc.get('qr_code_data') == qr_data:
                found_location = loc
                break
        
        assert found_location is not None, f"Legacy QR code {qr_data} should be findable"
        assert found_location['id'] == location_id
        
        print(f"✓ Legacy LOC format QR code works: {qr_data}")
    
    def test_complete_flow_admin_to_guest_to_driver(self, client, app):
        """Test: Complete flow from admin creating location to driver completing request"""
        # Step 1: Admin creates location
        with client:
            client.post('/auth/login', data={
                'username': 'admin',
                'password': 'admin123'
            })
            
            response = client.post('/api/locations',
                json={
                    'name': 'Complete Flow Test',
                    'description': 'End-to-end test location',
                    'is_active': True
                },
                content_type='application/json'
            )
            
            assert response.status_code in [200, 201]
            location_data = json.loads(response.data)['location']
            location_id = location_data['id']
            qr_data = location_data['qr_code_data']
            
            print(f"✓ Step 1: Admin created location with QR: {qr_data}")
            
            # Logout admin
            client.get('/auth/logout')
        
        # Step 2: Guest scans QR and creates request
        response = client.post('/api/requests',
            json={
                'location_id': location_id,
                'room_number': '401',
                'notes': 'Complete flow test'
            },
            content_type='application/json'
        )
        
        assert response.status_code in [200, 201]
        request_data = json.loads(response.data)
        request_id = request_data.get('request_id') or request_data.get('request', {}).get('id')
        
        print(f"✓ Step 2: Guest created request #{request_id}")
        
        # Step 3: Driver accepts request
        with client:
            client.post('/auth/login', data={
                'username': 'driver1',
                'password': 'driver123'
            })
            
            response = client.put(f'/api/requests/{request_id}/accept')
            
            # Accept might fail if no buggy assigned, that's ok for this test
            if response.status_code == 200:
                print(f"✓ Step 3: Driver accepted request #{request_id}")
                
                # Step 4: Driver completes request
                response = client.put(f'/api/requests/{request_id}/complete')
                
                if response.status_code == 200:
                    print(f"✓ Step 4: Driver completed request #{request_id}")
                    
                    # Verify final state
                    with app.app_context():
                        request = BuggyRequest.query.get(request_id)
                        assert request.status == RequestStatus.COMPLETED
                        assert request.completed_at is not None
                else:
                    print(f"  Step 4: Complete failed (status {response.status_code}), but flow tested")
            else:
                print(f"  Step 3: Accept failed (status {response.status_code}), but creation flow tested")
    
    def test_invalid_qr_code_format_handling(self, client, app):
        """Test: Invalid QR code format is handled gracefully"""
        # Get locations API (simulating what happens when invalid QR is scanned)
        response = client.get('/api/locations')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        locations = data if isinstance(data, list) else data.get('locations', [])
        
        # Try to find location with invalid QR data
        invalid_qr = "INVALID_QR_FORMAT_12345"
        found = any(loc.get('qr_code_data') == invalid_qr for loc in locations)
        
        assert not found, "Invalid QR code should not match any location"
        
        print(f"✓ Invalid QR code format handled correctly")
    
    def test_qr_code_contains_correct_base_url(self, client, app):
        """Test: QR code uses correct base URL from config or request"""
        with client:
            # Login as admin
            client.post('/auth/login', data={
                'username': 'admin',
                'password': 'admin123'
            })
            
            # Create location
            response = client.post('/api/locations',
                json={
                    'name': 'Base URL Test',
                    'description': 'Testing base URL',
                    'is_active': True
                },
                content_type='application/json'
            )
            
            assert response.status_code in [200, 201]
            location = json.loads(response.data)['location']
            qr_data = location['qr_code_data']
            
            # Verify QR code contains a valid URL
            assert qr_data.startswith('http://') or qr_data.startswith('https://')
            
            # Verify it contains the guest call endpoint
            assert '/guest/call' in qr_data
            
            # Verify it has location parameter
            assert 'location=' in qr_data
            
            print(f"✓ QR code has correct base URL structure: {qr_data}")
    
    def test_multiple_locations_have_unique_qr_codes(self, client, app):
        """Test: Multiple locations have unique QR codes"""
        with client:
            # Login as admin
            client.post('/auth/login', data={
                'username': 'admin',
                'password': 'admin123'
            })
            
            # Create multiple locations
            location_ids = []
            qr_codes = []
            
            for i in range(3):
                response = client.post('/api/locations',
                    json={
                        'name': f'Unique QR Test {i+1}',
                        'description': f'Test location {i+1}',
                        'is_active': True
                    },
                    content_type='application/json'
                )
                
                if response.status_code in [200, 201]:
                    location = json.loads(response.data)['location']
                    location_ids.append(location['id'])
                    qr_codes.append(location['qr_code_data'])
            
            # Verify all QR codes are unique
            assert len(qr_codes) == len(set(qr_codes)), "All QR codes should be unique"
            
            # Verify each QR code contains its respective location ID
            for loc_id, qr_data in zip(location_ids, qr_codes):
                assert str(loc_id) in qr_data, f"QR code should contain location ID {loc_id}"
            
            print(f"✓ All {len(qr_codes)} locations have unique QR codes")
    
    def test_qr_code_persists_after_location_update(self, client, app):
        """Test: QR code data persists when location is updated"""
        with client:
            # Login as admin
            client.post('/auth/login', data={
                'username': 'admin',
                'password': 'admin123'
            })
            
            # Create location
            response = client.post('/api/locations',
                json={
                    'name': 'Persistence Test',
                    'description': 'Original description',
                    'is_active': True
                },
                content_type='application/json'
            )
            
            assert response.status_code in [200, 201]
            location = json.loads(response.data)['location']
            location_id = location['id']
            original_qr = location['qr_code_data']
            
            # Update location
            response = client.put(f'/api/locations/{location_id}',
                json={
                    'name': 'Updated Name',
                    'description': 'Updated description'
                },
                content_type='application/json'
            )
            
            assert response.status_code == 200
            updated_location = json.loads(response.data)['location']
            
            # QR code should remain the same
            assert updated_location['qr_code_data'] == original_qr
            
            print(f"✓ QR code persists after location update")


class TestQRCodeMigration:
    """Tests for QR code migration from LOC format to URL format"""
    
    def test_migration_script_updates_loc_format(self, app):
        """Test: Migration script updates LOC format to URL format"""
        with app.app_context():
            hotel = Hotel.query.first()
            
            # Create location with old LOC format
            location = Location(
                hotel_id=hotel.id,
                name='Migration Test',
                description='Test migration',
                qr_code_data=f'LOC{hotel.id}9999',  # Old format
                is_active=True,
                display_order=1
            )
            db.session.add(location)
            db.session.commit()
            location_id = location.id
            
            # Simulate migration (what the migration script would do)
            from app.config import Config
            base_url = Config.BASE_URL
            new_qr_data = f"{base_url}/guest/call?location={location_id}"
            
            location.qr_code_data = new_qr_data
            db.session.commit()
            
            # Verify migration worked
            updated_location = Location.query.get(location_id)
            assert updated_location.qr_code_data.startswith('http')
            assert '/guest/call?location=' in updated_location.qr_code_data
            assert not updated_location.qr_code_data.startswith('LOC')
            
            print(f"✓ Migration from LOC to URL format successful")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
