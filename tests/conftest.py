"""
Buggy Call - Pytest Configuration and Fixtures
"""
import pytest
import tempfile
import os
from app import create_app, db as _db
from app.models.user import SystemUser, UserRole
from app.models.hotel import Hotel
from app.models.location import Location
from app.models.buggy import Buggy
from app.models.request import BuggyRequest
from app.models.session import Session
from app.models.audit import AuditTrail


@pytest.fixture(scope='session')
def app():
    """Create application for testing."""
    # Use MySQL test database (configured in config.py TestingConfig)
    app = create_app('testing')

    with app.app_context():
        # Drop all tables and recreate
        _db.drop_all()
        _db.create_all()

        # Create test hotel and users for test_complete_system.py tests
        test_hotel = Hotel(
            name="Test Hotel",
            address="123 Test Street",
            phone="555-0123",
            email="test@hotel.com"
        )
        _db.session.add(test_hotel)
        _db.session.commit()

        # Create admin user
        admin = SystemUser(
            hotel_id=test_hotel.id,
            username="admin",
            email="admin@test.com",
            full_name="Test Admin",
            role=UserRole.ADMIN,
            is_active=True
        )
        admin.set_password("admin123")
        _db.session.add(admin)

        # Create driver user
        driver = SystemUser(
            hotel_id=test_hotel.id,
            username="driver1",
            email="driver1@test.com",
            full_name="Test Driver",
            role=UserRole.DRIVER,
            is_active=True
        )
        driver.set_password("driver123")
        _db.session.add(driver)

        _db.session.commit()

        yield app

        # Cleanup - drop all tables after tests
        _db.drop_all()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def db_session(app):
    """Create database session for testing."""
    with app.app_context():
        connection = _db.engine.connect()
        transaction = connection.begin()

        # Configure session to use the connection
        # expire_on_commit=False prevents DetachedInstanceError
        _db.session.configure(bind=connection, expire_on_commit=False)

        yield _db.session

        # Rollback transaction
        _db.session.close()
        transaction.rollback()
        connection.close()
        _db.session.remove()


@pytest.fixture
def runner(app):
    """Create test runner."""
    return app.test_cli_runner()


# Helper fixtures for common test data
@pytest.fixture
def sample_hotel(db_session):
    """Create a sample hotel for testing."""
    hotel = Hotel(
        name="Test Hotel",
        address="123 Test Street",
        phone="555-0123",
        email="test@hotel.com"
    )
    db_session.add(hotel)
    db_session.commit()
    return hotel


@pytest.fixture
def sample_admin_user(db_session, sample_hotel):
    """Create a sample admin user for testing."""
    import uuid
    unique_username = f'admin{uuid.uuid4().hex[:8]}'

    admin = SystemUser(
        hotel_id=sample_hotel.id,
        username=unique_username,
        email=f"{unique_username}@test.com",
        full_name="Test Admin",
        role=UserRole.ADMIN,
        is_active=True
    )
    admin.set_password("testpassword")
    db_session.add(admin)
    db_session.commit()
    return admin


@pytest.fixture
def sample_driver_user(db_session, sample_hotel):
    """Create a sample driver user for testing."""
    import uuid
    unique_username = f'driver{uuid.uuid4().hex[:8]}'

    driver = SystemUser(
        hotel_id=sample_hotel.id,
        username=unique_username,
        email=f"{unique_username}@test.com",
        full_name="Test Driver",
        role=UserRole.DRIVER,
        is_active=True
    )
    driver.set_password("testpassword")
    db_session.add(driver)
    db_session.commit()
    return driver


@pytest.fixture
def authenticated_admin_client(client, sample_admin_user):
    """Create authenticated admin client."""
    client.post('/auth/login', json={
        'username': sample_admin_user.username,
        'password': 'testpassword'
    })
    return client


@pytest.fixture
def authenticated_driver_client(client, sample_driver_user):
    """Create authenticated driver client."""
    client.post('/auth/login', json={
        'username': sample_driver_user.username,
        'password': 'testpassword'
    })
    return client


@pytest.fixture
def sample_location(db_session, sample_hotel):
    """Create a sample location for testing."""
    import uuid
    unique_code = f'LOC{uuid.uuid4().hex[:8].upper()}'
    
    location = Location(
        hotel_id=sample_hotel.id,
        name="Test Location",
        description="Test location description",
        qr_code_data=unique_code,
        latitude=41.0082,
        longitude=28.9784,
        is_active=True
    )
    db_session.add(location)
    db_session.commit()
    return location


@pytest.fixture
def sample_buggy(db_session, sample_hotel, sample_driver_user):
    """Create a sample buggy for testing."""
    buggy = Buggy(
        hotel_id=sample_hotel.id,
        user_id=sample_driver_user.id,
        name="Test Buggy 1",
        plate_number="TEST-001",
        capacity=4,
        status="available"
    )
    db_session.add(buggy)
    db_session.commit()
    return buggy


@pytest.fixture
def sample_request(db_session, sample_hotel, sample_location):
    """Create a sample buggy request for testing."""
    request = BuggyRequest(
        hotel_id=sample_hotel.id,
        location_id=sample_location.id,
        guest_name="Test Guest",
        room_number="101",
        guest_count=2,
        status="PENDING"
    )
    db_session.add(request)
    db_session.commit()
    return request



