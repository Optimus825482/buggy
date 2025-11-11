"""
Fix Request Status Enum Definition in MySQL
Değerleri lowercase'den uppercase'e çevir
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db

app = create_app()

with app.app_context():
    print("=" * 60)
    print("REQUEST STATUS ENUM FIX")
    print("=" * 60)
    
    try:
        # MySQL enum'unu güncelle
        print("\n🔄 MySQL enum tanımını güncelliyorum...")
        
        # Enum'u yeniden tanımla (uppercase değerlerle)
        sql = """
        ALTER TABLE buggy_requests 
        MODIFY COLUMN status 
        ENUM('PENDING', 'ACCEPTED', 'COMPLETED', 'CANCELLED', 'UNANSWERED') 
        NOT NULL DEFAULT 'PENDING'
        """
        
        db.session.execute(db.text(sql))
        db.session.commit()
        
        print("✅ Enum tanımı güncellendi!")
        
        # Kontrol et
        result = db.session.execute(db.text(
            "SHOW COLUMNS FROM buggy_requests WHERE Field = 'status'"
        )).fetchone()
        
        print(f"\n📊 Yeni enum tanımı:")
        print(f"   Type: {result[1]}")
        
        print("\n✅ İşlem başarılı!")
        
    except Exception as e:
        print(f"\n❌ Hata: {e}")
        db.session.rollback()
        sys.exit(1)
