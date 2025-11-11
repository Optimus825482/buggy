#!/usr/bin/env python3
"""
Hotfix: Add missing push notification columns to system_users table
Railway deployment fix
"""
import os
import sys
from sqlalchemy import create_engine, text, inspect

def update_model_file():
    """Uncomment the push notification columns in user.py model"""
    try:
        model_path = 'app/models/user.py'
        
        with open(model_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Uncomment the columns
        content = content.replace(
            '    # Push notification fields - will be added via migration\n'
            '    # must_change_password = Column(Boolean, default=False, nullable=False)\n'
            '    # push_subscription = Column(Text)\n'
            '    # push_subscription_date = Column(DateTime)\n'
            '    # notification_preferences = Column(Text)',
            '    # Push notification fields\n'
            '    must_change_password = Column(Boolean, default=False, nullable=False)\n'
            '    push_subscription = Column(Text)\n'
            '    push_subscription_date = Column(DateTime)\n'
            '    notification_preferences = Column(Text)'
        )
        
        with open(model_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Model file updated")
        return True
        
    except Exception as e:
        print(f"⚠️  Could not update model file: {e}")
        return False

def fix_system_users_columns():
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
            print("❌ Database credentials not found in environment")
            return False
        
        # Use PyMySQL driver
        database_url = f"mysql+pymysql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    
    # Ensure PyMySQL driver is used
    if database_url.startswith('mysql://'):
        database_url = database_url.replace('mysql://', 'mysql+pymysql://', 1)
    
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
        
        # Now update the model file to uncomment the columns
        print("\n📝 Updating model file...")
        update_model_file()
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = fix_system_users_columns()
    sys.exit(0 if success else 1)
