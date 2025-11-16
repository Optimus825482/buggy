"""
Authentication ve Security test scripti
JWT ve password fonksiyonlarını test eder
"""
import sys
import os

# App modülünü import edebilmek için path ekle
sys.path.insert(0, os.path.dirname(__file__))

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token,
    extract_user_from_token,
    create_token_pair,
    validate_password_strength,
    get_token_expiry_info
)


def test_password_hashing():
    """Password hashing ve verification testleri"""
    print("\n" + "="*60)
    print("🔐 PASSWORD HASHING TESTLERİ")
    print("="*60)
    
    # Test 1: Password hashleme
    print("\n1️⃣ Password hashleme testi...")
    password = "MySecurePassword123"
    hashed = hash_password(password)
    print(f"   Plain: {password}")
    print(f"   Hash: {hashed[:50]}...")
    print("   ✅ Hash oluşturuldu")
    
    # Test 2: Doğru şifre verification
    print("\n2️⃣ Doğru şifre verification testi...")
    is_valid = verify_password(password, hashed)
    print(f"   Sonuç: {is_valid}")
    assert is_valid, "Doğru şifre verify edilemedi!"
    print("   ✅ Doğru şifre verify edildi")
    
    # Test 3: Yanlış şifre verification
    print("\n3️⃣ Yanlış şifre verification testi...")
    is_valid = verify_password("WrongPassword", hashed)
    print(f"   Sonuç: {is_valid}")
    assert not is_valid, "Yanlış şifre verify edildi!"
    print("   ✅ Yanlış şifre reddedildi")
    
    # Test 4: Password strength validation
    print("\n4️⃣ Password strength validation testi...")
    
    # Zayıf şifre
    is_valid, error = validate_password_strength("weak")
    print(f"   'weak' -> Valid: {is_valid}, Error: {error}")
    assert not is_valid, "Zayıf şifre kabul edildi!"
    
    # Güçlü şifre
    is_valid, error = validate_password_strength("StrongPass123")
    print(f"   'StrongPass123' -> Valid: {is_valid}, Error: {error}")
    assert is_valid, "Güçlü şifre reddedildi!"
    print("   ✅ Password strength validation çalışıyor")


def test_jwt_tokens():
    """JWT token testleri"""
    print("\n" + "="*60)
    print("🎫 JWT TOKEN TESTLERİ")
    print("="*60)
    
    # Test user data
    user_data = {
        "sub": "123",
        "username": "testdriver",
        "role": "driver",
        "hotel_id": 1
    }
    
    # Test 1: Access token oluşturma
    print("\n1️⃣ Access token oluşturma testi...")
    access_token = create_access_token(data=user_data)
    print(f"   Token: {access_token[:50]}...")
    print("   ✅ Access token oluşturuldu")
    
    # Test 2: Refresh token oluşturma
    print("\n2️⃣ Refresh token oluşturma testi...")
    refresh_token = create_refresh_token(data={"sub": "123"})
    print(f"   Token: {refresh_token[:50]}...")
    print("   ✅ Refresh token oluşturuldu")
    
    # Test 3: Access token doğrulama
    print("\n3️⃣ Access token doğrulama testi...")
    payload = verify_token(access_token, token_type="access")
    print(f"   Payload: {payload}")
    assert payload is not None, "Token doğrulanamadı!"
    assert payload["username"] == "testdriver", "Username yanlış!"
    assert payload["role"] == "driver", "Role yanlış!"
    print("   ✅ Access token doğrulandı")
    
    # Test 4: Refresh token doğrulama
    print("\n4️⃣ Refresh token doğrulama testi...")
    payload = verify_token(refresh_token, token_type="refresh")
    print(f"   Payload: {payload}")
    assert payload is not None, "Refresh token doğrulanamadı!"
    assert payload["sub"] == "123", "User ID yanlış!"
    print("   ✅ Refresh token doğrulandı")
    
    # Test 5: User bilgisi çıkarma
    print("\n5️⃣ Token'dan user bilgisi çıkarma testi...")
    user_info = extract_user_from_token(access_token)
    print(f"   User Info: {user_info}")
    assert user_info is not None, "User bilgisi çıkarılamadı!"
    assert user_info["user_id"] == 123, "User ID yanlış!"
    assert user_info["username"] == "testdriver", "Username yanlış!"
    assert user_info["role"] == "driver", "Role yanlış!"
    assert user_info["hotel_id"] == 1, "Hotel ID yanlış!"
    print("   ✅ User bilgisi çıkarıldı")
    
    # Test 6: Token pair oluşturma
    print("\n6️⃣ Token pair oluşturma testi...")
    tokens = create_token_pair(user_data)
    print(f"   Access Token: {tokens['access_token'][:50]}...")
    print(f"   Refresh Token: {tokens['refresh_token'][:50]}...")
    print(f"   Token Type: {tokens['token_type']}")
    assert tokens["token_type"] == "bearer", "Token type yanlış!"
    print("   ✅ Token pair oluşturuldu")
    
    # Test 7: Token expiry bilgisi
    print("\n7️⃣ Token expiry bilgisi testi...")
    expiry_info = get_token_expiry_info(access_token)
    print(f"   Expires At: {expiry_info['expires_at']}")
    print(f"   Expires In: {expiry_info['expires_in_seconds']} saniye")
    print(f"   Is Expired: {expiry_info['is_expired']}")
    assert not expiry_info['is_expired'], "Token süresi dolmuş!"
    assert expiry_info['expires_in_seconds'] > 0, "Expiry time yanlış!"
    print("   ✅ Token expiry bilgisi alındı")
    
    # Test 8: Yanlış token type ile doğrulama
    print("\n8️⃣ Yanlış token type testi...")
    payload = verify_token(access_token, token_type="refresh")
    print(f"   Payload: {payload}")
    assert payload is None, "Yanlış token type kabul edildi!"
    print("   ✅ Yanlış token type reddedildi")


def main():
    """Ana test fonksiyonu"""
    print("\n" + "="*60)
    print("🧪 AUTHENTICATION & SECURITY TEST SUITE")
    print("="*60)
    
    try:
        # Password testleri
        test_password_hashing()
        
        # JWT testleri
        test_jwt_tokens()
        
        # Başarı mesajı
        print("\n" + "="*60)
        print("✅ TÜM TESTLER BAŞARILI!")
        print("="*60)
        print("\n📋 Test Özeti:")
        print("   • Password hashing: ✅")
        print("   • Password verification: ✅")
        print("   • Password strength validation: ✅")
        print("   • JWT access token: ✅")
        print("   • JWT refresh token: ✅")
        print("   • Token verification: ✅")
        print("   • User extraction: ✅")
        print("   • Token pair creation: ✅")
        print("   • Token expiry info: ✅")
        print("\n🎉 Authentication ve Security modülü hazır!")
        
    except Exception as e:
        print("\n" + "="*60)
        print("❌ TEST HATASI!")
        print("="*60)
        print(f"Hata: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
