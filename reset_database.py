#!/usr/bin/env python3
"""
Railway Database Reset Script
TÜM TABLOLARI SİLER VE YENİDEN OLUŞTURUR!
⚠️ DİKKAT: TÜM VERİLER SİLİNECEK!
"""
import os
import sys
from sqlalchemy import create_engine, text, inspect

def reset_database():
    """Veritabanını sıfırdan kur"""
    
    # Get database URL from environment
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not found in environment")
        return False
    
    try:
        print("=" * 60)
        print("🔥 RAILWAY DATABASE RESET")
        print("=" * 60)
        print("⚠️  TÜM TABLOLAR SİLİNECEK!")
        print("=" * 60)
        
        # Create engine
        engine = create_engine(database_url, echo=False)
        
        # Get all tables
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        print(f"\n📋 Mevcut tablolar ({len(tables)}):")
        for table in tables:
            print(f"   - {table}")
        
        # Drop all tables
        print("\n🗑️  Tablolar siliniyor...")
        with engine.connect() as conn:
            # Disable foreign key checks
            conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
            conn.commit()
            
            # Drop each table
            for table in tables:
                print(f"   ❌ Dropping: {table}")
                conn.execute(text(f"DROP TABLE IF EXISTS `{table}`"))
                conn.commit()
            
            # Re-enable foreign key checks
            conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
            conn.commit()
        
        print("\n✅ Tüm tablolar silindi!")
        
        # Verify tables are gone
        inspector = inspect(engine)
        remaining_tables = inspector.get_table_names()
        
        if remaining_tables:
            print(f"⚠️  Bazı tablolar kaldı: {remaining_tables}")
            return False
        
        print("\n✅ Veritabanı tamamen temizlendi!")
        print("=" * 60)
        print("ℹ️  Şimdi migration çalışacak ve tablolar yeniden oluşturulacak")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = reset_database()
    sys.exit(0 if success else 1)
