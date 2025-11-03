"""
Buggy Call - Railway Database Initialization Script
Handles database setup and initial data creation for Railway deployment
"""
import sys
import os
import time
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask
from flask_migrate import upgrade
from app import db
from app.models.hotel import Hotel
from app.models.user import SystemUser, UserRole
from app.models.location import Location
from app.models.buggy import Buggy, BuggyStatus


def run_migrations(app):
    """Run Alembic migrations"""
    with app.app_context():
        try:
            app.logger.info("Running database migrations...")
            
            # Import migration directory
            from flask_migrate import upgrade as flask_migrate_upgrade
            import alembic
            from alembic import command
            from alembic.config import Config as AlembicConfig
            
            # Get migration directory
            migrations_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'migrations')
            
            if os.path.exists(migrations_dir):
                # Run migrations using Flask-Migrate
                flask_migrate_upgrade(directory=migrations_dir)
                app.logger.info("✅ Database migrations completed successfully")
            else:
                app.logger.warning("No migrations directory found, creating tables directly")
                db.create_all()
                app.logger.info("✅ Database tables created")
                
        except Exception as e:
            app.logger.error(f"❌ Migration failed: {e}")
            raise


def create_initial_data(app):
    """Create initial data for Railway deployment"""
    with app.app_context():
        try:
            # Check if data already exists
            if Hotel.query.first():
                app.logger.info("Initial data already exists, skipping creation")
                return
            
            app.logger.info("Creating initial data...")
            
            # Create default hotel
            hotel = Hotel(
                name=os.getenv('INITIAL_HOTEL_NAME', 'Railway Demo Hotel'),
                address=os.getenv('INITIAL_HOTEL_ADDRESS', 'Cloud Deployment'),
                phone=os.getenv('INITIAL_HOTEL_PHONE', '+90 242 000 0000'),
                email=os.getenv('INITIAL_HOTEL_EMAIL', 'info@buggycall.railway.app'),
                timezone=os.getenv('APP_TIMEZONE', 'Europe/Istanbul')
            )
            db.session.add(hotel)
            db.session.flush()
            app.logger.info(f"✅ Created hotel: {hotel.name}")
            
            # Create admin user with strong default password
            admin_password = os.getenv('INITIAL_ADMIN_PASSWORD', 'Admin123!Railway')
            admin = SystemUser(
                hotel_id=hotel.id,
                username=os.getenv('INITIAL_ADMIN_USERNAME', 'admin'),
                role=UserRole.ADMIN,
                full_name='System Administrator',
                email=os.getenv('INITIAL_ADMIN_EMAIL', 'admin@buggycall.railway.app'),
                is_active=True
            )
            admin.set_password(admin_password)
            db.session.add(admin)
            app.logger.info(f"✅ Created admin user: {admin.username}")
            
            # Create driver users
            driver_count = int(os.getenv('INITIAL_DRIVER_COUNT', 3))
            drivers = []
            for i in range(1, driver_count + 1):
                driver = SystemUser(
                    hotel_id=hotel.id,
                    username=f"driver{i}",
                    role=UserRole.DRIVER,
                    full_name=f"Driver {i}",
                    is_active=True
                )
                driver.set_password(os.getenv('INITIAL_DRIVER_PASSWORD', 'Driver123!'))
                db.session.add(driver)
                drivers.append(driver)
            
            db.session.flush()
            app.logger.info(f"✅ Created {len(drivers)} driver users")
            
            # Create default locations
            default_locations = [
                {'name': 'Reception', 'description': 'Main entrance and reception area'},
                {'name': 'Beach', 'description': 'Hotel beach area'},
                {'name': 'Restaurant', 'description': 'Main restaurant'},
                {'name': 'Spa', 'description': 'Spa and wellness center'},
                {'name': 'Pool', 'description': 'Swimming pool area'},
                {'name': 'Tennis Court', 'description': 'Tennis courts'},
            ]
            
            for idx, loc_data in enumerate(default_locations):
                location = Location(
                    hotel_id=hotel.id,
                    name=loc_data['name'],
                    description=loc_data['description'],
                    qr_code_data=f"LOC{hotel.id}{idx+1:03d}",
                    is_active=True
                )
                db.session.add(location)
            
            db.session.flush()
            app.logger.info(f"✅ Created {len(default_locations)} locations")
            
            # Create buggies for each driver
            for idx, driver in enumerate(drivers):
                buggy = Buggy(
                    hotel_id=hotel.id,
                    driver_id=driver.id,
                    code=f"B{idx+1:03d}",
                    model=f"Golf Cart Model {idx+1}",
                    license_plate=f"RW {1000+idx}",
                    status=BuggyStatus.AVAILABLE
                )
                db.session.add(buggy)
            
            app.logger.info(f"✅ Created {len(drivers)} buggies")
            
            # Commit all changes
            db.session.commit()
            
            app.logger.info("="*60)
            app.logger.info("✅ Initial data created successfully!")
            app.logger.info("="*60)
            app.logger.info(f"Hotel: {hotel.name}")
            app.logger.info(f"Admin: {admin.username} / {admin_password}")
            app.logger.info(f"Drivers: driver1-{driver_count} / Driver123!")
            app.logger.info(f"Locations: {len(default_locations)}")
            app.logger.info(f"Buggies: {len(drivers)}")
            app.logger.info("="*60)
            
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"❌ Failed to create initial data: {e}")
            raise


def verify_database_health(app):
    """Verify database connectivity and health"""
    with app.app_context():
        max_retries = 5
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                # Test database connection
                db.session.execute('SELECT 1')
                
                # Count tables
                from sqlalchemy import inspect
                inspector = inspect(db.engine)
                table_count = len(inspector.get_table_names())
                
                app.logger.info(f"✅ Database health check passed")
                app.logger.info(f"   - Connection: OK")
                app.logger.info(f"   - Tables: {table_count}")
                
                # Verify critical tables exist
                critical_tables = ['hotel', 'system_user', 'location', 'buggy']
                existing_tables = inspector.get_table_names()
                
                for table in critical_tables:
                    if table in existing_tables:
                        app.logger.info(f"   - Table '{table}': ✓")
                    else:
                        app.logger.warning(f"   - Table '{table}': ✗ (missing)")
                
                return True
                
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)
                    app.logger.warning(
                        f"Database connection failed (attempt {attempt + 1}/{max_retries}), "
                        f"retrying in {wait_time}s... Error: {e}"
                    )
                    time.sleep(wait_time)
                else:
                    app.logger.error(f"❌ Database health check failed after {max_retries} attempts: {e}")
                    raise


def initialize_railway_database(app):
    """Main initialization function for Railway deployment"""
    try:
        app.logger.info("="*60)
        app.logger.info("Starting Railway database initialization...")
        app.logger.info("="*60)
        
        # Step 1: Verify database health
        verify_database_health(app)
        
        # Step 2: Run migrations
        run_migrations(app)
        
        # Step 3: Create initial data if needed
        create_initial_data(app)
        
        app.logger.info("="*60)
        app.logger.info("✅ Railway initialization completed successfully!")
        app.logger.info("="*60)
        
        return True
        
    except Exception as e:
        app.logger.error("="*60)
        app.logger.error(f"❌ Railway initialization failed: {e}")
        app.logger.error("="*60)
        raise


if __name__ == "__main__":
    # For manual execution
    from app import create_app
    
    app = create_app('production')
    initialize_railway_database(app)
