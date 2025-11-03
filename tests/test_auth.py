"""
Buggy Call - Authentication Tests
"""
import pytest


@pytest.mark.unit
def test_login_success(client, sample_admin_user):
    """Test successful login"""
    response = client.post('/auth/login', json={
        'username': sample_admin_user.username,
        'password': 'testpassword'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert 'access_token' in data
    assert 'user' in data
    assert data['user']['username'] == sample_admin_user.username


@pytest.mark.unit
def test_login_invalid_credentials(client, sample_admin_user):
    """Test login with invalid credentials"""
    response = client.post('/auth/login', json={
        'username': sample_admin_user.username,
        'password': 'wrongpassword'
    })
    
    assert response.status_code == 401
    data = response.get_json()
    assert data['success'] is False


@pytest.mark.unit
def test_login_missing_fields(client):
    """Test login with missing fields"""
    response = client.post('/auth/login', json={
        'username': 'admin'
    })
    
    assert response.status_code == 400


@pytest.mark.security
def test_login_rate_limiting(client, sample_admin_user):
    """Test rate limiting on login endpoint"""
    # Make multiple requests
    for _ in range(6):
        client.post('/auth/login', json={
            'username': sample_admin_user.username,
            'password': 'wrongpassword'
        })
    
    # 6th request should be rate limited
    response = client.post('/auth/login', json={
        'username': sample_admin_user.username,
        'password': 'testpassword'
    })
    
    assert response.status_code == 429
