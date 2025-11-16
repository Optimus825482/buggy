#!/usr/bin/env python3
"""
Firebase Configuration Checker
FIREBASE_SERVICE_ACCOUNT_BASE64 environment variable'ını kontrol eder
"""
import os
import base64
import json

print("🔍 Firebase Configuration Check")
print("=" * 50)

# 1. Environment variable kontrolü
base64_env = os.getenv('FIREBASE_SERVICE_ACCOUNT_BASE64')

if not base64_env:
    print("❌ FIREBASE_SERVICE_ACCOUNT_BASE64 environment variable bulunamadı!")
    print("💡 Environment variable'ı set etmelisiniz")
    exit(1)

print(f"✅ FIREBASE_SERVICE_ACCOUNT_BASE64 bulundu")
print(f"   Uzunluk: {len(base64_env)} karakter")

# 2. Base64 decode kontrolü
try:
    decoded_json = base64.b64decode(base64_env).decode('utf-8')
    print("✅ Base64 decode başarılı")
except Exception as e:
    print(f"❌ Base64 decode hatası: {e}")
    exit(1)

# 3. JSON parse kontrolü
try:
    service_account = json.loads(decoded_json)
    print("✅ JSON parse başarılı")
except Exception as e:
    print(f"❌ JSON parse hatası: {e}")
    exit(1)

# 4. Gerekli alanları kontrol et
required_fields = [
    'type',
    'project_id',
    'private_key_id',
    'private_key',
    'client_email',
    'client_id'
]

print("\n📋 Service Account Bilgileri:")
print("-" * 50)

missing_fields = []
for field in required_fields:
    if field in service_account:
        if field == 'private_key':
            print(f"✅ {field}: [HIDDEN]")
        else:
            value = service_account[field]
            if len(str(value)) > 50:
                print(f"✅ {field}: {str(value)[:50]}...")
            else:
                print(f"✅ {field}: {value}")
    else:
        print(f"❌ {field}: EKSIK!")
        missing_fields.append(field)

if missing_fields:
    print(f"\n❌ Eksik alanlar: {', '.join(missing_fields)}")
    exit(1)

# 5. Project ID kontrolü
project_id = service_account.get('project_id')
print(f"\n🏷️ Firebase Project ID: {project_id}")

# 6. Loglardan project ID'yi kontrol et
print("\n🔍 Log'lardaki Project ID:")
print("   shuttle-call-835d9")

if project_id != 'shuttle-call-835d9':
    print(f"\n⚠️ UYARI: Project ID uyuşmazlığı!")
    print(f"   Service Account: {project_id}")
    print(f"   Log'larda görünen: shuttle-call-835d9")
    print(f"   Bu FCM token'larının çalışmamasına neden olabilir!")
else:
    print(f"✅ Project ID eşleşiyor")

# 7. Private key formatı kontrolü
private_key = service_account.get('private_key', '')
if private_key.startswith('-----BEGIN PRIVATE KEY-----'):
    print("✅ Private key formatı doğru")
else:
    print("❌ Private key formatı hatalı!")
    exit(1)

print("\n" + "=" * 50)
print("✅ Firebase configuration geçerli görünüyor!")
print("\n💡 Eğer hala FCM 500 hatası alıyorsanız:")
print("   1. Firebase Console'da API quota kontrolü yapın")
print("   2. Service Account'un FCM izinleri olduğunu kontrol edin")
print("   3. Token'ların bu project'e ait olduğunu doğrulayın")
