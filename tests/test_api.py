"""
Buggy Call - API Tests
"""
import pytest


@pytest.mark.api
def test_get_locations(client, sample_location):
    """Test GET /api/locations"""
    response = client.get('/api/locations')
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert 'data' in data or 'locations' in data


@pytest.mark.api
def test_create_location_unauthorized(client):
    """Test creating location without authentication"""
    response = client.post('/api/locations', json={
        'name': 'New Location',
        'description': 'Test'
    })
    
    assert response.status_code in [401, 403]


@pytest.mark.api
def test_health_check(client):
    """Test health check endpoint"""
    response = client.get('/health')
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'healthy'
