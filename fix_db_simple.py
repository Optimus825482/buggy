#!/usr/bin/env python3
"""
App context kullanarak system_users tablosunu düzelt
"""
from app import create_app, db

def fix_system_users():
    """system_users tablosuna eksik kolonları ekle"""
    app = create_app()
    
    with app.app_context():
        try:
            # Mevcut kolonları kontrol et
            result = db.session.execute(db.text("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'system_users' 
                AND TABLE_SCHEMA = DATABASE()
            """))
            
            existing_columns = [row[0] for row in result]
            print(f"✅ Mevcut kolonlar: {len(existing_columns)} adet")
            
            # Eksik kolonları ekle
            if 'push_subscription_date' not in existing_columns:
                print("⏳ push_subscription_date ekleniyor...")
                db.session.execute(db.text(
                    "ALTER TABLE system_users ADD COLUMN push_subscription_date DATETIME"
                ))
                db.session.commit()
                print("✅ push_subscription_date eklendi!")
            else:
                print("✅ push_subscription_date zaten var")
            
            if 'notification_preferences' not in existing_columns:
                print("⏳ notification_preferences ekleniyor...")
                db.session.execute(db.text(
                    "ALTER TABLE system_users ADD COLUMN notification_preferences JSON"
                ))
                db.session.commit()
                print("✅ notification_preferences eklendi!")
            else:
                print("✅ notification_preferences zaten var")
            
            print("\n✅ Tablo düzeltme tamamlandı!")
            return True
            
        except Exception as e:
            print(f"❌ Hata: {e}")
            db.session.rollback()
            return False

if __name__ == '__main__':
    print("=" * 60)
    print("System Users Tablo Düzeltme (App Context)")
    print("=" * 60)
    fix_system_users()
