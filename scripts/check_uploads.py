#!/usr/bin/env python3
"""
Check uploads directory and create if missing
"""
import os
from pathlib import Path

def check_uploads():
    """Check and create uploads directory structure"""
    base_dir = Path(__file__).parent.parent
    uploads_dir = base_dir / 'app' / 'static' / 'uploads' / 'locations'
    
    print(f"📁 Checking uploads directory: {uploads_dir}")
    
    if not uploads_dir.exists():
        print("⚠️  Uploads directory not found, creating...")
        uploads_dir.mkdir(parents=True, exist_ok=True)
        print("✅ Uploads directory created")
    else:
        print("✅ Uploads directory exists")
        
        # List files
        files = list(uploads_dir.glob('*'))
        print(f"📄 Found {len(files)} files:")
        for f in files[:10]:  # Show first 10
            print(f"   - {f.name}")
    
    # Create .gitkeep
    gitkeep = uploads_dir / '.gitkeep'
    if not gitkeep.exists():
        gitkeep.touch()
        print("✅ Created .gitkeep")

if __name__ == '__main__':
    check_uploads()
