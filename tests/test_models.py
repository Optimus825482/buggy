"""
Buggy Call - Model Tests
"""
import pytest
from app.models.user import SystemUser, UserRole
from app.models.location import Location


@pytest.mark.models
def test_user_password_hashing(db_session, sample_hotel):
    """Test password hashing"""
    user = SystemUser(
        username='testuser',
        email='test@test.com',
        hotel_id=sample_hotel.id,
        role=UserRole.DRIVER
    )
    user.set_password('password123')
    
    assert user.password_hash is not None
    assert user.password_hash != 'password123'
    assert user.check_password('password123') is True
    assert user.check_password('wrongpassword') is False


@pytest.mark.models
def test_user_to_dict(db_session, sample_hotel):
    """Test user to_dict method"""
    import uuid
    unique_username = f'admin{uuid.uuid4().hex[:6]}'
    
    user = SystemUser(
        username=unique_username,
        email=f'{unique_username}@test.com',
        full_name='Admin User',
        role=UserRole.ADMIN,
        hotel_id=sample_hotel.id,
        is_active=True
    )
    user.set_password('admin123')
    db_session.add(user)
    db_session.commit()
    
    data = user.to_dict()
    
    assert 'id' in data
    assert 'username' in data
    assert data['username'] == unique_username
    assert 'password_hash' not in data
    assert 'role' in data


@pytest.mark.models
def test_location_creation(db_session, sample_hotel):
    """Test location creation"""
    import uuid
    unique_code = f'LOC{uuid.uuid4().hex[:8].upper()}'
    
    location = Location(
        name='Beach',
        description='Hotel Beach',
        hotel_id=sample_hotel.id,
        qr_code_data=unique_code,
        latitude=41.0082,
        longitude=28.9784,
        is_active=True
    )
    db_session.add(location)
    db_session.commit()
    
    assert location.id is not None
    assert location.qr_code_data is not None
    assert location.qr_code_data.startswith('LOC')
