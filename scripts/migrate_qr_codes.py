"""
Migration Script: Update Location QR Codes to URL Format
Updates existing location QR codes from LOC format to full URL format
"""
import sys
import os

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models.location import Location
from app.config import Config


def migrate_qr_codes(dry_run=True):
    """
    Migrate existing QR codes from LOC format to URL format
    
    Args:
        dry_run (bool): If True, only show what would be updated without making changes
    """
    app = create_app()
    
    with app.app_context():
        # Get base URL from config
        base_url = Config.BASE_URL.rstrip('/')
        
        # Find all locations with LOC format QR codes
        locations = Location.query.filter(
            Location.qr_code_data.like('LOC%')
        ).all()
        
        if not locations:
            print("✓ No locations found with LOC format QR codes")
            return
        
        print(f"Found {len(locations)} location(s) with LOC format QR codes\n")
        
        updated_count = 0
        
        for location in locations:
            old_qr_code = location.qr_code_data
            new_qr_code = f"{base_url}/guest/call?location={location.id}"
            
            print(f"Location ID: {location.id}")
            print(f"  Name: {location.name}")
            print(f"  Old QR: {old_qr_code}")
            print(f"  New QR: {new_qr_code}")
            
            if not dry_run:
                location.qr_code_data = new_qr_code
                updated_count += 1
                print("  Status: ✓ Updated")
            else:
                print("  Status: [DRY RUN - Not updated]")
            
            print()
        
        if not dry_run:
            try:
                db.session.commit()
                print(f"✓ Successfully updated {updated_count} location(s)")
            except Exception as e:
                db.session.rollback()
                print(f"✗ Error updating locations: {str(e)}")
                raise
        else:
            print(f"[DRY RUN] Would update {len(locations)} location(s)")
            print("\nTo apply changes, run: python scripts/migrate_qr_codes.py --apply")


if __name__ == '__main__':
    # Check if --apply flag is provided
    apply_changes = '--apply' in sys.argv
    
    if apply_changes:
        print("=" * 60)
        print("APPLYING QR CODE MIGRATION")
        print("=" * 60)
        print()
        migrate_qr_codes(dry_run=False)
    else:
        print("=" * 60)
        print("QR CODE MIGRATION - DRY RUN")
        print("=" * 60)
        print()
        migrate_qr_codes(dry_run=True)
