#!/usr/bin/env python3
"""
Hotfix: Add missing push notification columns to system_users table
Railway deployment fix
"""
import os
import sys
from sqlalchemy import create_engine, text, inspect

def fix_system_users_columns():
    """Add missing columns to system_users table"""
    
    # Get database URL from environment
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not found in environment")
        return False
    
    try:
        # Create engine
        engine = create_engine(database_url, echo=True)
        
        # Check existing columns
        inspector = inspect(engine)
        existing_columns = [col['name'] for col in inspector.get_columns('system_users')]
        
        print(f"\n📋 Existing columns: {existing_columns}\n")
        
        # Define columns to add
        columns_to_add = {
            'must_change_password': "ALTER TABLE system_users ADD COLUMN must_change_password TINYINT(1) NOT NULL DEFAULT 0",
            'push_subscription': "ALTER TABLE system_users ADD COLUMN push_subscription TEXT",
            'push_subscription_date': "ALTER TABLE system_users ADD COLUMN push_subscription_date DATETIME",
            'notification_preferences': "ALTER TABLE system_users ADD COLUMN notification_preferences TEXT"
        }
        
        # Add missing columns
        with engine.connect() as conn:
            for col_name, sql in columns_to_add.items():
                if col_name not in existing_columns:
                    print(f"➕ Adding column: {col_name}")
                    conn.execute(text(sql))
                    conn.commit()
                    print(f"✅ Added: {col_name}")
                else:
                    print(f"⏭️  Column already exists: {col_name}")
        
        print("\n✅ All columns checked/added successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = fix_system_users_columns()
    sys.exit(0 if success else 1)
