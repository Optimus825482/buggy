#!/usr/bin/env python3
"""
Railway için system_users tablosuna eksik kolonları ekler
"""
import os
import sys
import pymysql
from sqlalchemy import create_engine, text

# PyMySQL'i MySQLdb olarak kullan
pymysql.install_as_MySQLdb()

def fix_system_users_table():
    """system_users tablosuna eksik kolonları ekle"""
    
    # Railway database URL'ini al
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL bulunamadı!")
        return False
    
    try:
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            # Mevcut kolonları kontrol et
            result = conn.execute(text("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'system_users' 
                AND TABLE_SCHEMA = DATABASE()
            """))
            
            existing_columns = [row[0] for row in result]
            print(f"✅ Mevcut kolonlar: {', '.join(existing_columns)}")
            
            # Eksik kolonları ekle
            columns_to_add = []
            
            if 'push_subscription_date' not in existing_columns:
                columns_to_add.append(
                    "ALTER TABLE system_users ADD COLUMN push_subscription_date DATETIME"
                )
            
            if 'notification_preferences' not in existing_columns:
                columns_to_add.append(
                    "ALTER TABLE system_users ADD COLUMN notification_preferences JSON"
                )
            
            if not columns_to_add:
                print("✅ Tüm kolonlar mevcut!")
                return True
            
            # Kolonları ekle
            for sql in columns_to_add:
                print(f"⏳ Çalıştırılıyor: {sql}")
                conn.execute(text(sql))
                conn.commit()
                print("✅ Başarılı!")
            
            print(f"\n✅ {len(columns_to_add)} kolon eklendi!")
            return True
            
    except Exception as e:
        print(f"❌ Hata: {e}")
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("System Users Tablo Düzeltme")
    print("=" * 60)
    
    success = fix_system_users_table()
    sys.exit(0 if success else 1)
