"""
Update QR codes for all locations with correct BASE_URL
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models.location import Location
import qrcode
import io
import base64

def update_qr_codes(base_url=None):
    """Update QR codes for all locations"""
    app = create_app()
    
    with app.app_context():
        # Get base URL
        if not base_url:
            from app.config import Config
            base_url = Config.BASE_URL
            
            # If still localhost, ask user
            if base_url == 'http://localhost:5000':
                print("⚠️  BASE_URL is set to localhost!")
                print("Please provide your server's public URL (e.g., https://buggycall.yourdomain.com)")
                base_url = input("Enter BASE_URL: ").strip()
                
                if not base_url:
                    print("❌ No URL provided. Exiting.")
                    return
        
        # Remove trailing slash
        base_url = base_url.rstrip('/')
        
        print(f"🔄 Updating QR codes with BASE_URL: {base_url}")
        print()
        
        # Get all locations
        locations = Location.query.all()
        
        if not locations:
            print("❌ No locations found in database")
            return
        
        updated_count = 0
        
        for location in locations:
            old_qr_data = location.qr_code_data
            
            # Generate new QR code data
            new_qr_data = f"{base_url}/guest/call?location={location.id}"
            
            # Update location
            location.qr_code_data = new_qr_data
            
            # Generate QR code image
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(new_qr_data)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            img_base64 = base64.b64encode(buffer.getvalue()).decode()
            location.qr_code_image = f"data:image/png;base64,{img_base64}"
            
            print(f"✅ Updated: {location.name}")
            print(f"   Old: {old_qr_data}")
            print(f"   New: {new_qr_data}")
            print()
            
            updated_count += 1
        
        # Commit changes
        db.session.commit()
        
        print(f"✅ Successfully updated {updated_count} location(s)")
        print()
        print("📱 You can now download the new QR codes from the admin panel")


if __name__ == '__main__':
    # Check if BASE_URL provided as argument
    base_url = sys.argv[1] if len(sys.argv) > 1 else None
    update_qr_codes(base_url)
