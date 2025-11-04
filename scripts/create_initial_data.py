"""
Create initial data for Railway deployment
Creates hotel, admin user, locations, and buggies
"""
import sys
import os

# Set flag to skip SocketIO initialization
os.environ['SKIP_SOCKETIO'] = '1'

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models.hotel import Hotel
from app.models.user import SystemUser, UserRole
from app.models.location import Location
from app.models.buggy import Buggy, BuggyStatus


def create_initial_data():
    """Create initial data if not exists"""
    app = create_app('production')
    
    with app.app_context():
        try:
            print("="*60)
            print("Creating Initial Data")
            print("="*60)
            
            # 1. Create Hotel
            hotel = Hotel.query.first()
            if not hotel:
                hotel = Hotel(
                    name=os.getenv('HOTEL_NAME', 'Buggy Call Hotel'),
                    code=os.getenv('HOTEL_CODE', 'HOTEL01')
                )
                db.session.add(hotel)
                db.session.flush()
                print(f"✅ Hotel created: {hotel.name} (Code: {hotel.code})")
            else:
                print(f"ℹ️  Hotel already exists: {hotel.name}")
            
            # 2. Create Admin User
            admin = SystemUser.query.filter_by(username='admin').first()
            if not admin:
                admin = SystemUser(
                    hotel_id=hotel.id,
                    username='admin',
                    full_name='System Administrator',
                    role=UserRole.ADMIN,
                    email=os.getenv('ADMIN_EMAIL', 'admin@buggycall.com'),
                    is_active=True
                )
                # Use password from environment or default
                admin_password = os.getenv('ADMIN_PASSWORD', '518518')
                admin.set_password(admin_password)
                db.session.add(admin)
                print(f"✅ Admin user created: {admin.username}")
                print(f"   Password: {admin_password}")
            else:
                print(f"ℹ️  Admin user already exists: {admin.username}")
            
            # 3. Create Default Locations
            import uuid
            locations_data = [
                {'name': 'Lobby', 'display_order': 1},
                {'name': 'Restaurant', 'display_order': 2},
                {'name': 'Pool', 'display_order': 3},
                {'name': 'Beach', 'display_order': 4},
                {'name': 'Spa', 'display_order': 5},
            ]
            
            existing_locations = Location.query.filter_by(hotel_id=hotel.id).count()
            if existing_locations == 0:
                for loc_data in locations_data:
                    # Generate unique QR code data
                    qr_code_data = f"{hotel.code}-{loc_data['name'].upper()}-{uuid.uuid4().hex[:8]}"
                    
                    location = Location(
                        hotel_id=hotel.id,
                        name=loc_data['name'],
                        display_order=loc_data['display_order'],
                        qr_code_data=qr_code_data
                    )
                    db.session.add(location)
                print(f"✅ Created {len(locations_data)} default locations")
            else:
                print(f"ℹ️  Locations already exist ({existing_locations} locations)")
            
            # 4. Create Default Buggies
            buggy_count = int(os.getenv('INITIAL_BUGGY_COUNT', '5'))
            existing_buggies = Buggy.query.filter_by(hotel_id=hotel.id).count()
            
            if existing_buggies == 0:
                for i in range(1, buggy_count + 1):
                    buggy = Buggy(
                        hotel_id=hotel.id,
                        buggy_number=f"B{i:02d}",
                        status=BuggyStatus.AVAILABLE
                    )
                    db.session.add(buggy)
                print(f"✅ Created {buggy_count} buggies")
            else:
                print(f"ℹ️  Buggies already exist ({existing_buggies} buggies)")
            
            # Commit all changes
            db.session.commit()
            
            print("="*60)
            print("✅ Initial data creation completed successfully")
            print("="*60)
            print(f"\n📝 Login Information:")
            print(f"   Username: admin")
            print(f"   Password: {os.getenv('ADMIN_PASSWORD', '518518')}")
            print(f"   Hotel: {hotel.name}")
            print("="*60)
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to create initial data: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            return False


if __name__ == "__main__":
    success = create_initial_data()
    sys.exit(0 if success else 1)
