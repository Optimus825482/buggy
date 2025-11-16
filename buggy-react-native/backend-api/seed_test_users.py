"""
Test kullanıcıları oluştur
"""
from app.database import get_db, init_database
from app.config import get_settings
from app.models.user import SystemUser
from app.models.hotel import Hotel
from app.core.security import hash_password
from datetime import datetime

def seed_test_data():
    """Test için örnek veri oluştur"""
    settings = get_settings()
    init_database(settings.DATABASE_URL)
    db = next(get_db())
    
    try:
        print("🌱 Test verileri oluşturuluyor...")
        
        # Hotel kontrolü
        hotel = db.query(Hotel).first()
        if not hotel:
            print("📍 Test oteli oluşturuluyor...")
            hotel = Hotel(
                name="Test Hotel",
                address="Test Address",
                phone="+90 555 000 0000",
                email="test@hotel.com"
            )
            db.add(hotel)
            db.commit()
            db.refresh(hotel)
            print(f"✅ Otel oluşturuldu: {hotel.name} (ID: {hotel.id})")
        else:
            print(f"✅ Mevcut otel kullanılıyor: {hotel.name} (ID: {hotel.id})")
        
        # Admin kullanıcısı kontrolü
        admin = db.query(SystemUser).filter_by(username="admin1").first()
        if not admin:
            print("👤 Admin kullanıcısı oluşturuluyor...")
            admin = SystemUser(
                hotel_id=hotel.id,
                username="admin1",
                password_hash=hash_password("admin123"),
                role="admin",
                full_name="Admin User",
                email="admin@hotel.com",
                phone="+90 555 111 1111",
                is_active=True,
                must_change_password=False
            )
            db.add(admin)
            db.commit()
            print(f"✅ Admin oluşturuldu: {admin.username}")
        else:
            print(f"✅ Admin zaten var: {admin.username}")
        
        # Driver kullanıcısı kontrolü
        driver = db.query(SystemUser).filter_by(username="driver1").first()
        if not driver:
            print("🚗 Driver kullanıcısı oluşturuluyor...")
            driver = SystemUser(
                hotel_id=hotel.id,
                username="driver1",
                password_hash=hash_password("driver123"),
                role="driver",
                full_name="Driver User",
                email="driver@hotel.com",
                phone="+90 555 222 2222",
                is_active=True,
                must_change_password=False
            )
            db.add(driver)
            db.commit()
            print(f"✅ Driver oluşturuldu: {driver.username}")
        else:
            print(f"✅ Driver zaten var: {driver.username}")
        
        print("\n" + "=" * 60)
        print("✅ Test verileri hazır!")
        print("=" * 60)
        print("\n📋 Test Kullanıcıları:")
        print(f"  Admin  → username: admin1,  password: admin123")
        print(f"  Driver → username: driver1, password: driver123")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Hata: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_test_data()
