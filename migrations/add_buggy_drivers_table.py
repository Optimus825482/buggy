"""
Migration: Add buggy_drivers association table for many-to-many relationship
This allows multiple drivers to be assigned to a single buggy
"""
from app import db, create_app
from app.models.buggy import Buggy
from app.models.user import SystemUser
from app.models.buggy_driver import BuggyDriver
from datetime import datetime


def migrate_up():
    """
    Create buggy_drivers table and migrate existing driver_id data
    """
    app = create_app()
    
    with app.app_context():
        print("Starting migration: add_buggy_drivers_table")
        
        # Create the new table
        print("Creating buggy_drivers table...")
        BuggyDriver.__table__.create(db.engine, checkfirst=True)
        
        # Migrate existing data from buggy.driver_id to buggy_drivers
        print("Migrating existing driver assignments...")
        buggies = Buggy.query.all()
        migrated_count = 0
        
        for buggy in buggies:
            # Check if buggy has old driver_id column (for backward compatibility)
            try:
                if hasattr(buggy, 'driver_id') and buggy.driver_id:
                    # Create association
                    association = BuggyDriver(
                        buggy_id=buggy.id,
                        driver_id=buggy.driver_id,
                        is_active=False,  # Will be set to True when driver logs in
                        is_primary=True,  # First driver is primary
                        assigned_at=datetime.utcnow()
                    )
                    db.session.add(association)
                    migrated_count += 1
            except Exception as e:
                print(f"Warning: Could not migrate buggy {buggy.id}: {e}")
                continue
        
        db.session.commit()
        print(f"Migrated {migrated_count} driver assignments")
        
        # Now we can safely drop the driver_id column from buggies table
        # Note: This is done in the model, SQLAlchemy will handle it
        print("Migration completed successfully!")
        print("Note: The driver_id column in buggies table is now deprecated")
        print("      It will be removed in the next migration after verification")


def migrate_down():
    """
    Rollback: Drop buggy_drivers table and restore driver_id column
    """
    app = create_app()
    
    with app.app_context():
        print("Rolling back migration: add_buggy_drivers_table")
        
        # Drop the table
        print("Dropping buggy_drivers table...")
        BuggyDriver.__table__.drop(db.engine, checkfirst=True)
        
        print("Rollback completed!")
        print("Warning: You may need to manually restore the driver_id column in buggies table")


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python migrations/add_buggy_drivers_table.py [up|down]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == 'up':
        migrate_up()
    elif command == 'down':
        migrate_down()
    else:
        print(f"Unknown command: {command}")
        print("Usage: python migrations/add_buggy_drivers_table.py [up|down]")
        sys.exit(1)
