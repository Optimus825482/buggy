#!/usr/bin/env python3
"""
Quick fix: Add missing columns directly to Railway MySQL
"""
import pymysql

# Railway MySQL credentials
config = {
    'host': 'caboose.proxy.rlwy.net',
    'port': 18758,
    'user': 'root',
    'password': 'knwndfscXAWpdkPaSHGxvtdPIaGhBYtc',
    'database': 'railway',
    'charset': 'utf8mb4'
}

def main():
    print("=" * 60)
    print("🔧 Quick Column Fix")
    print("=" * 60)
    
    try:
        # Connect
        print("🔗 Connecting to Railway MySQL...")
        conn = pymysql.connect(**config)
        cursor = conn.cursor()
        print("✅ Connected!")
        
        # Check existing columns in locations table
        print("\n📋 Checking locations columns...")
        cursor.execute("SHOW COLUMNS FROM locations")
        existing_columns = [row[0] for row in cursor.fetchall()]
        print(f"Found {len(existing_columns)} columns")
        
        # Define columns to add
        columns_to_add = {
            'location_image': 'VARCHAR(500)'
        }
        
        # Add missing columns
        print("\n🔧 Adding missing columns to locations...")
        added = 0
        for col_name, col_def in columns_to_add.items():
            if col_name not in existing_columns:
                print(f"  ➕ Adding: {col_name}")
                sql = f"ALTER TABLE locations ADD COLUMN {col_name} {col_def}"
                cursor.execute(sql)
                conn.commit()
                print(f"  ✅ Added: {col_name}")
                added += 1
            else:
                print(f"  ✓ Exists: {col_name}")
        
        # Verify
        print("\n🔍 Verifying...")
        cursor.execute("SHOW COLUMNS FROM locations")
        final_columns = [row[0] for row in cursor.fetchall()]
        print(f"Total columns now: {len(final_columns)}")
        
        # Close
        cursor.close()
        conn.close()
        
        print("\n" + "=" * 60)
        if added > 0:
            print(f"✅ Successfully added {added} column(s)!")
        else:
            print("✅ All columns already exist!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main())
