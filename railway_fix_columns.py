#!/usr/bin/env python3
"""
Railway Hotfix: Add missing columns to system_users table
Run this directly on Railway to fix the database schema
"""
import os
import sys
from sqlalchemy import create_engine, text, inspect

def fix_columns():
    """Add missing columns to system_users table"""
    
    # Get database URL from environment
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not found")
        return False
    
    print(f"🔗 Connecting to database...")
    
    try:
        # Create engine
        engine = create_engine(database_url, echo=False)
        
        # Check existing columns
        inspector = inspect(engine)
        existing_columns = [col['name'] for col in inspector.get_columns('system_users')]
        
        print(f"📋 Existing columns: {', '.join(existing_columns)}")
        
        # Define columns to add
        columns_to_add = {
            'must_change_password': "ALTER TABLE system_users ADD COLUMN must_change_password TINYINT(1) NOT NULL DEFAULT 0",
            'push_subscription': "ALTER TABLE system_users ADD COLUMN push_subscription TEXT",
            'push_subscription_date': "ALTER TABLE system_users ADD COLUMN push_subscription_date DATETIME",
            'notification_preferences': "ALTER TABLE system_users ADD COLUMN notification_preferences TEXT"
        }
        
        # Add missing columns
        added_count = 0
        with engine.connect() as conn:
            for col_name, sql in columns_to_add.items():
                if col_name not in existing_columns:
                    print(f"➕ Adding column: {col_name}")
                    try:
                        conn.execute(text(sql))
                        conn.commit()
                        print(f"✅ Added: {col_name}")
                        added_count += 1
                    except Exception as e:
                        print(f"⚠️  Error adding {col_name}: {e}")
                else:
                    print(f"⏭️  Already exists: {col_name}")
        
        if added_count > 0:
            print(f"\n✅ Successfully added {added_count} column(s)!")
        else:
            print(f"\n✅ All columns already exist!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("🔧 Railway Column Fix Script")
    print("=" * 60)
    success = fix_columns()
    print("=" * 60)
    sys.exit(0 if success else 1)
