"""
Buggy Call - Database Initialization Script
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models.hotel import Hotel
from app.models.user import SystemUser, UserRole
from app.models.location import Location
from app.models.buggy import Buggy, BuggyStatus

def init_database():
    """Initialize database with sample data"""
    app = create_app()
    
    with app.app_context():
        # Drop all tables and recreate
        print("Dropping all tables...")
        db.drop_all()
        
        print("Creating all tables...")
        db.create_all()
        
        # Create sample hotel
        print("Creating sample hotel...")
        hotel = Hotel(
            name="Grand Paradise Hotel",
            address="Belek, Antalya, Turkey",
            phone="+90 242 123 4567",
            email="info@grandparadise.com",
            timezone="Europe/Istanbul"
        )
        db.session.add(hotel)
        db.session.flush()
        
        # Create admin user
        print("Creating admin user...")
        admin = SystemUser(
            hotel_id=hotel.id,
            username="admin",
            role=UserRole.ADMIN,
            full_name="Admin User",
            email="admin@grandparadise.com",
            is_active=True
        )
        admin.set_password("admin123")
        db.session.add(admin)
        
        # Create driver users
        print("Creating driver users...")
        for i in range(1, 4):
            driver = SystemUser(
                hotel_id=hotel.id,
                username=f"driver{i}",
                role=UserRole.DRIVER,
                full_name=f"Driver {i}",
                is_active=True
            )
            driver.set_password("driver123")
            db.session.add(driver)
        
        db.session.flush()
        
        # Create sample locations
        print("Creating sample locations...")
        locations_data = [
            {"name": "Resepsiyon", "description": "Ana giriş ve resepsiyon alanı"},
            {"name": "Plaj", "description": "Otel plajı"},
            {"name": "Restaurant", "description": "Ana restaurant"},
            {"name": "Spa", "description": "Spa ve wellness merkezi"},
            {"name": "Aquapark", "description": "Aquapark alanı"},
            {"name": "Tenis Kortu", "description": "Tenis kortları"},
        ]
        
        for idx, loc_data in enumerate(locations_data):
            location = Location(
                hotel_id=hotel.id,
                name=loc_data["name"],
                description=loc_data["description"],
                qr_code_data=f"LOC{hotel.id}{idx+1:03d}",
                is_active=True
            )
            db.session.add(location)
        
        db.session.flush()
        
        # Create sample buggies
        print("Creating sample buggies...")
        drivers = SystemUser.query.filter_by(role=UserRole.DRIVER).all()
        for idx, driver in enumerate(drivers):
            buggy = Buggy(
                hotel_id=hotel.id,
                driver_id=driver.id,
                code=f"B{idx+1:03d}",
                model=f"Golf Cart Model {idx+1}",
                license_plate=f"34 BC {1000+idx}",
                status=BuggyStatus.AVAILABLE
            )
            db.session.add(buggy)
        
        # Commit all changes
        db.session.commit()
        
        print("\n" + "="*50)
        print("✅ Database initialized successfully!")
        print("="*50)
        print(f"\n🏨 Hotel: {hotel.name}")
        print(f"📍 Locations: {len(locations_data)}")
        print(f"🚗 Buggies: {len(drivers)}")
        print(f"\n👤 Admin Login:")
        print(f"   Username: admin")
        print(f"   Password: admin123")
        print(f"\n👤 Driver Login:")
        print(f"   Username: driver1, driver2, driver3")
        print(f"   Password: driver123")
        print("="*50 + "\n")

if __name__ == "__main__":
    init_database()
