import pytest
import json
from datetime import datetime, timedelta
from flask import session
from app import create_app, db
from app.models.user import SystemUser, UserRole
from app.models.hotel import Hotel
from app.models.session import Session as SessionModel


class TestSessionManagement:
    """Test session management functionality"""
    
    @pytest.fixture
    def setup_test_data(self, app, db_session):
        """Setup test data for session management tests"""
        import uuid
        unique_id = uuid.uuid4().hex[:8]
        
        # Create hotel
        hotel = Hotel(
            name=f"Test Hotel {unique_id}",
            address="Test Address",
            phone="123456789",
            email=f"test{unique_id}@hotel.com"
        )
        db_session.add(hotel)
        db_session.flush()
        
        # Create admin user
        admin = SystemUser(
            hotel_id=hotel.id,
            username=f"admin{unique_id}",
            email=f"admin{unique_id}@test.com",
            full_name="Test Admin",
            role=UserRole.ADMIN,
            is_active=True
        )
        admin.set_password("password123")
        db_session.add(admin)
        
        # Create driver user
        driver = SystemUser(
            hotel_id=hotel.id,
            username=f"driver{unique_id}",
            email=f"driver{unique_id}@test.com",
            full_name="Test Driver",
            role=UserRole.DRIVER,
            is_active=True
        )
        driver.set_password("password123")
        db_session.add(driver)
        db_session.commit()
        
        return {
            'hotel': hotel,
            'admin': admin,
            'driver': driver
        }
    
    @pytest.mark.skip(reason="Session management API endpoints not yet implemented")
    def test_admin_can_view_active_sessions(self, client, setup_test_data):
        """Test that admin can view all active sessions"""
        data = setup_test_data

        # Login as admin
        response = client.post('/auth/login', json={
            'username': data['admin'].username,
            'password': 'password123'
        })
        assert response.status_code == 200

        # Get active sessions
        response = client.get('/api/admin/sessions')

        assert response.status_code == 200
        result = response.get_json()
        assert result['success'] is True
        assert 'sessions' in result
        assert len(result['sessions']) >= 1  # At least admin's session
    
    @pytest.mark.skip(reason="Session management API endpoints not yet implemented")
    def test_non_admin_cannot_view_sessions(self, client, setup_test_data):
        """Test that non-admin users cannot view sessions"""
        data = setup_test_data
        
        # Login as driver
        response = client.post('/auth/login', json={
            'username': data['driver'].username,
            'password': 'password123'
        })
        assert response.status_code == 200
        
        # Try to get sessions
        response = client.get('/api/admin/sessions')
        
        assert response.status_code == 403
        result = response.get_json()
        assert 'error' in result
    
    @pytest.mark.skip(reason="Session management API endpoints not yet implemented")
    def test_admin_can_terminate_session(self, client, setup_test_data):
        """Test that admin can terminate user sessions"""
        data = setup_test_data
        
        # Create driver session
        driver_session = SessionModel(
            user_id=data['driver'].id,
            session_token="test_token_123",
            ip_address="127.0.0.1",
            user_agent="Test Agent",
            is_active=True,
            expires_at=datetime.utcnow() + timedelta(hours=24),
            created_at=datetime.utcnow()
        )
        db.session.add(driver_session)
        db.session.commit()
        
        # Login as admin
        client.post('/auth/login', json={
            'username': data['admin'].username,
            'password': 'password123'
        })
        
        # Terminate driver session
        response = client.post(f'/api/admin/sessions/{driver_session.id}/terminate')
        
        assert response.status_code == 200
        result = response.get_json()
        assert result['success'] is True
        
        # Verify session was terminated
        terminated_session = SessionModel.query.get(driver_session.id)
        assert terminated_session.is_active is False
        assert terminated_session.revoked_at is not None
    
    @pytest.mark.skip(reason="Session management API endpoints not yet implemented")
    def test_cannot_terminate_nonexistent_session(self, client, setup_test_data):
        """Test handling of non-existent session termination"""
        data = setup_test_data
        
        # Login as admin
        client.post('/auth/login', json={
            'username': data['admin'].username,
            'password': 'password123'
        })
        
        # Try to terminate non-existent session
        response = client.post('/api/admin/sessions/99999/terminate')
        
        assert response.status_code == 404
        result = response.get_json()
        assert 'error' in result
    
    @pytest.mark.skip(reason="Session management API endpoints not yet implemented")
    def test_cannot_terminate_already_terminated_session(self, client, setup_test_data):
        """Test handling of already terminated session"""
        data = setup_test_data
        
        # Create terminated session
        terminated_session = SessionModel(
            user_id=data['driver'].id,
            session_token="test_token_456",
            ip_address="127.0.0.1",
            user_agent="Test Agent",
            is_active=False,  # Already terminated
            expires_at=datetime.utcnow() + timedelta(hours=24),
            created_at=datetime.utcnow(),
            revoked_at=datetime.utcnow()
        )
        db.session.add(terminated_session)
        db.session.commit()
        
        # Login as admin
        client.post('/auth/login', json={
            'username': data['admin'].username,
            'password': 'password123'
        })
        
        # Try to terminate already terminated session
        response = client.post(f'/api/admin/sessions/{terminated_session.id}/terminate')
        
        assert response.status_code == 400
        result = response.get_json()
        assert 'zaten sonlandırılmış' in result['error']
    
    def test_session_cleanup_on_logout(self, client, setup_test_data):
        """Test that sessions are properly cleaned up on logout"""
        data = setup_test_data
        
        # Login as driver
        response = client.post('/auth/login', json={
            'username': data['driver'].username,
            'password': 'password123'
        })
        assert response.status_code == 200
        
        # Verify session exists
        active_sessions = SessionModel.query.filter_by(
            user_id=data['driver'].id,
            is_active=True
        ).count()
        assert active_sessions >= 1
        
        # Logout
        response = client.post('/auth/logout')
        assert response.status_code == 200
        
        # Verify session was terminated
        active_sessions = SessionModel.query.filter_by(
            user_id=data['driver'].id,
            is_active=True
        ).count()
        assert active_sessions == 0
