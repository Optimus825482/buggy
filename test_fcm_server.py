#!/usr/bin/env python3
"""
FCM Server Test - Sunucuda çalıştırılacak
Firebase credentials ve FCM API'yi test eder
"""
import os
import sys
import base64
import json

# Flask app context
from app import create_app, db
app = create_app()

with app.app_context():
    print("🔍 FCM SERVER TEST")
    print("=" * 60)
    
    # 1. Environment variable kontrolü
    base64_env = os.getenv('FIREBASE_SERVICE_ACCOUNT_BASE64')
    json_env = os.getenv('FIREBASE_SERVICE_ACCOUNT_JSON')
    file_path = os.getenv('FIREBASE_SERVICE_ACCOUNT_PATH', 'firebase-service-account.json')
    
    print("\n📋 Environment Variables:")
    print(f"   FIREBASE_SERVICE_ACCOUNT_BASE64: {'✅ SET' if base64_env else '❌ NOT SET'}")
    print(f"   FIREBASE_SERVICE_ACCOUNT_JSON: {'✅ SET' if json_env else '❌ NOT SET'}")
    print(f"   FIREBASE_SERVICE_ACCOUNT_PATH: {file_path}")
    print(f"   File exists: {'✅ YES' if os.path.exists(file_path) else '❌ NO'}")
    
    # 2. Credentials yükle
    service_account = None
    source = None
    
    if base64_env:
        try:
            decoded = base64.b64decode(base64_env).decode('utf-8')
            service_account = json.loads(decoded)
            source = "BASE64 ENV"
            print(f"\n✅ Credentials loaded from: {source}")
        except Exception as e:
            print(f"\n❌ BASE64 decode error: {e}")
    
    if not service_account and json_env:
        try:
            service_account = json.loads(json_env)
            source = "JSON ENV"
            print(f"\n✅ Credentials loaded from: {source}")
        except Exception as e:
            print(f"\n❌ JSON parse error: {e}")
    
    if not service_account and os.path.exists(file_path):
        try:
            with open(file_path, 'r') as f:
                service_account = json.load(f)
            source = "FILE"
            print(f"\n✅ Credentials loaded from: {source}")
        except Exception as e:
            print(f"\n❌ File read error: {e}")
    
    if not service_account:
        print("\n❌ CRITICAL: Firebase credentials bulunamadı!")
        sys.exit(1)
    
    # 3. Project ID kontrolü
    project_id = service_account.get('project_id')
    print(f"\n🏷️ Firebase Project ID: {project_id}")
    print(f"   Expected (from logs): shuttle-call-835d9")
    
    if project_id != 'shuttle-call-835d9':
        print(f"\n⚠️ WARNING: Project ID mismatch!")
        print(f"   This will cause FCM token errors!")
    
    # 4. FCM Service'i başlat
    print("\n🔧 Initializing FCM Service...")
    from app.services.fcm_notification_service import FCMNotificationService
    
    if FCMNotificationService.initialize():
        print("✅ FCM Service initialized successfully")
    else:
        print("❌ FCM Service initialization failed")
        sys.exit(1)
    
    # 5. Test token ile gönderim dene
    print("\n📤 Testing FCM send...")
    
    # Veritabanından bir driver token al
    from app.models.user import SystemUser
    driver = SystemUser.query.filter(
        SystemUser.fcm_token.isnot(None)
    ).first()
    
    if not driver:
        print("⚠️ No driver with FCM token found in database")
        print("✅ FCM Service is ready but no tokens to test")
    else:
        print(f"   Driver: {driver.full_name} (ID: {driver.id})")
        print(f"   Token: {driver.fcm_token[:30]}...")
        
        # Test bildirimi gönder
        try:
            result = FCMNotificationService.send_to_token(
                token=driver.fcm_token,
                title="🧪 Test Notification",
                body="FCM test - sunucu tarafından gönderildi",
                data={'type': 'test', 'timestamp': str(os.times())},
                priority='normal',
                retry=False  # Tek deneme
            )
            
            if result:
                print("✅ TEST NOTIFICATION SENT SUCCESSFULLY!")
                print("   FCM is working correctly")
            else:
                print("❌ TEST NOTIFICATION FAILED")
                print("   Check Firebase Console and logs above")
                
        except Exception as e:
            print(f"❌ TEST ERROR: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("🏁 Test completed")
    print("\n💡 If FCM 500 errors persist:")
    print("   1. Check Firebase Console > Project Settings > Service Accounts")
    print("   2. Verify FCM API is enabled in Google Cloud Console")
    print("   3. Check if tokens are from the correct Firebase project")
    print("   4. Review Firebase quota limits")
