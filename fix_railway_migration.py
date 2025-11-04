"""
Railway Migration Fix Script
Veritabanı şemasını model tanımlarıyla senkronize eder
"""
import os
import sys
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import OperationalError

def get_database_url():
    """Get database URL from environment"""
    # Railway environment variables
    db_host = os.getenv('MYSQLHOST', 'localhost')
    db_port = os.getenv('MYSQLPORT', '3306')
    db_user = os.getenv('MYSQLUSER', 'root')
    db_password = os.getenv('MYSQLPASSWORD', '')
    db_name = os.getenv('MYSQLDATABASE', 'railway')
    
    return f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}?charset=utf8mb4"

def check_column_exists(engine, table_name, column_name):
    """Check if a column exists in a table"""
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns

def add_missing_columns(engine):
    """Add missing columns to system_users table"""
    print("🔍 Checking system_users table...")
    
    columns_to_add = [
        ('must_change_password', 'BOOLEAN NOT NULL DEFAULT 0'),
        ('push_subscription', 'TEXT'),
        ('push_subscription_date', 'DATETIME'),
        ('notification_preferences', 'JSON')  # JSON olarak değiştirdim
    ]
    
    with engine.connect() as conn:
        for column_name, column_def in columns_to_add:
            if not check_column_exists(engine, 'system_users', column_name):
                print(f"➕ Adding column: {column_name}")
                try:
                    conn.execute(text(f"ALTER TABLE system_users ADD COLUMN {column_name} {column_def}"))
                    conn.commit()
                    print(f"✅ Added: {column_name}")
                except Exception as e:
                    print(f"❌ Error adding {column_name}: {e}")
                    conn.rollback()
            else:
                print(f"✓ Column exists: {column_name}")

def update_alembic_version(engine):
    """Update alembic_version to latest revision"""
    print("\n🔍 Checking alembic_version...")
    
    with engine.connect() as conn:
        try:
            # Check if alembic_version table exists
            result = conn.execute(text(
                "SELECT COUNT(*) as count FROM information_schema.tables "
                "WHERE table_schema = DATABASE() AND table_name = 'alembic_version'"
            ))
            table_exists = result.fetchone()[0] > 0
            
            if not table_exists:
                print("➕ Creating alembic_version table...")
                conn.execute(text(
                    "CREATE TABLE alembic_version ("
                    "version_num VARCHAR(32) NOT NULL, "
                    "PRIMARY KEY (version_num)"
                    ") CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci"
                ))
                conn.commit()
            
            # Check current version
            result = conn.execute(text("SELECT version_num FROM alembic_version"))
            current_version = result.fetchone()
            
            if current_version:
                print(f"📌 Current version: {current_version[0]}")
                if current_version[0] != '002':
                    print("🔄 Updating to version 002...")
                    conn.execute(text("UPDATE alembic_version SET version_num = '002'"))
                    conn.commit()
                    print("✅ Updated to version 002")
            else:
                print("➕ Setting initial version to 002...")
                conn.execute(text("INSERT INTO alembic_version (version_num) VALUES ('002')"))
                conn.commit()
                print("✅ Set to version 002")
                
        except Exception as e:
            print(f"❌ Error updating alembic_version: {e}")
            conn.rollback()

def main():
    """Main execution"""
    print("=" * 60)
    print("🔧 Railway Migration Fix")
    print("=" * 60)
    
    try:
        # Get database URL
        db_url = get_database_url()
        print(f"📊 Database: {db_url.split('@')[1].split('?')[0]}")
        
        # Create engine
        engine = create_engine(db_url, echo=False)
        
        # Test connection
        print("\n⏳ Testing connection...")
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ Connection successful")
        
        # Add missing columns
        print("\n" + "=" * 60)
        add_missing_columns(engine)
        
        # Update alembic version
        print("\n" + "=" * 60)
        update_alembic_version(engine)
        
        print("\n" + "=" * 60)
        print("✅ Migration fix completed successfully!")
        print("=" * 60)
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
