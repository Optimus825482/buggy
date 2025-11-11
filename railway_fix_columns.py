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
    
    # If DATABASE_URL not found, build from individual variables
    if not database_url:
        db_user = os.environ.get('MYSQLUSER') or os.environ.get('DB_USER')
        db_pass = os.environ.get('MYSQLPASSWORD') or os.environ.get('DB_PASSWORD')
        db_host = os.environ.get('MYSQLHOST') or os.environ.get('DB_HOST')
        db_port = os.environ.get('MYSQLPORT') or os.environ.get('DB_PORT', '3306')
        db_name = os.environ.get('MYSQLDATABASE') or os.environ.get('DB_NAME')
        
        if not all([db_user, db_pass, db_host, db_name]):
            print("❌ Database credentials not found")
            return False
        
        # Use PyMySQL driver
        database_url = f"mysql+pymysql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    
    # Ensure PyMySQL driver is used
    if database_url.startswith('mysql://'):
        database_url = database_url.replace('mysql://', 'mysql+pymysql://', 1)
    
    print(f"🔗 Connecting to database...")
    
    try:
        # Create engine
        engine = create_engine(database_url, echo=False)
        
        # Check if table exists
        inspector = inspect(engine)
        if 'system_users' not in inspector.get_table_names():
            print("⚠️  system_users table doesn't exist yet")
            print("✅ Skipping column fix (will be created by migration)")
            return True
        
        # Check existing columns
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
