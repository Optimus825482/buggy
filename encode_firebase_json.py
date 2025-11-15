#!/usr/bin/env python3
"""
Firebase Service Account JSON'u Base64'e encode eder
Coolify'da decode edilecek
"""
import json
import base64

# JSON dosyasını oku
with open('firebase-service-account.json', 'r', encoding='utf-8') as f:
    firebase_json = json.load(f)

# JSON'u string'e çevir (minified)
json_string = json.dumps(firebase_json, separators=(',', ':'))

# Base64'e encode et
encoded = base64.b64encode(json_string.encode('utf-8')).decode('utf-8')

print("=" * 80)
print("🔐 BASE64 ENCODED FIREBASE JSON (Coolify'a yapıştır)")
print("=" * 80)
print(encoded)
print()
print("=" * 80)
print(f"📊 Karakter Sayısı: {len(encoded)}")
print("=" * 80)
print()
print("💡 Coolify'da Environment Variable:")
print("   Key:   FIREBASE_SERVICE_ACCOUNT_BASE64")
print("   Value: [Yukarıdaki base64 string]")
print()
