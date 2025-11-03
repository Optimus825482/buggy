"""
Create initial admin user
"""
from app import create_app, db
from app.models.hotel import Hotel
from app.models.user import SystemUser, UserRole

app = create_app()

with app.app_context():
    # Check if hotel already exists
    hotel = Hotel.query.filter_by(code='TEST').first()
    
    if not hotel:
        # Create hotel
        hotel = Hotel(name='Test Otel', code='TEST')
        db.session.add(hotel)
        db.session.flush()
        print(f"✅ Otel oluşturuldu: {hotel.name} (ID: {hotel.id})")
    else:
        print(f"ℹ️  Otel zaten mevcut: {hotel.name} (ID: {hotel.id})")
    
    # Check if admin already exists
    admin = SystemUser.query.filter_by(username='admin').first()
    
    if not admin:
        # Create admin user
        admin = SystemUser(
            hotel_id=hotel.id,
            username='admin',
            full_name='Admin User',
            role=UserRole.ADMIN,
            email='admin@test.com'
        )
        admin.set_password('Admin123')
        db.session.add(admin)
        db.session.commit()
        
        print(f"✅ Admin kullanıcısı oluşturuldu!")
        print(f"   Kullanıcı adı: {admin.username}")
        print(f"   Şifre: Admin123")
        print(f"   Rol: {admin.role.value}")
    else:
        print(f"ℹ️  Admin kullanıcısı zaten mevcut: {admin.username}")
    
    # Check if superadmin already exists
    superadmin = SystemUser.query.filter_by(username='superadmin').first()
    
    if not superadmin:
        # Create superadmin user
        superadmin = SystemUser(
            hotel_id=hotel.id,
            username='superadmin',
            full_name='Super Admin',
            role=UserRole.ADMIN,
            email='superadmin@test.com',
            is_active=True
        )
        superadmin.set_password('518518Erkan')
        db.session.add(superadmin)
        db.session.commit()
        
        print(f"✅ Superadmin kullanıcısı oluşturuldu!")
        print(f"   Kullanıcı adı: {superadmin.username}")
        print(f"   Şifre: 518518Erkan")
        print(f"   Rol: {superadmin.role.value}")
    else:
        print(f"ℹ️  Superadmin kullanıcısı zaten mevcut: {superadmin.username}")
    
    print("\n🎉 Kurulum tamamlandı!")
    print(f"\n📝 Giriş Bilgileri:")
    print(f"   URL: http://localhost:5000/auth/login")
    print(f"   Kullanıcı adı: admin veya superadmin")
    print(f"   Şifre: Admin123 veya 518518Erkan")
