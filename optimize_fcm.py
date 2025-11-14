#!/usr/bin/env python3
"""
FCM Notification Service Optimizer
Priority-based & Rich Media Support ekler
"""

# Optimize edilmiş FCM service içeriği
optimized_content = '''"""
Buggy Call - Firebase Cloud Messaging (FCM) Notification Service
Priority-based & Rich Media Support - Optimize edilmiş
"""
import firebase_admin
from firebase_admin import credentials, messaging
import os
import json
from datetime import datetime, timedelta
from app import db
from app.models.user import SystemUser
from app.models.notification_log import NotificationLog
from typing import List, Dict, Optional


class FCMNotificationService:
    """Firebase Cloud Messaging servisi - Optimize edilmiş"""
    
    _initialized = False
    
    @staticmethod
    def initialize():
        """Firebase Admin SDK'yı başlat - Error handling ile"""
        if FCMNotificationService._initialized:
            return True
        
        try:
            firebase_admin.get_app()
            FCMNotificationService._initialized = True
            print("✅ Firebase Admin SDK zaten başlatılmış")
            return True
        except ValueError:
            try:
                service_account_path = os.getenv('FIREBASE_SERVICE_ACCOUNT_PATH', 'firebase-service-account.json')
                
                if not os.path.exists(service_account_path):
                    print(f"❌ Firebase service account dosyası bulunamadı: {service_account_path}")
                    return False
                
                cred = credentials.Certificate(service_account_path)
                firebase_admin.initialize_app(cred)
                FCMNotificationService._initialized = True
                print("✅ Firebase Admin SDK başlatıldı")
                return True
                
            except Exception as e:
                print(f"❌ Firebase Admin SDK başlatma hatası: {str(e)}")
                return False
'''

# Dosyayı yaz
with open('app/services/fcm_notification_service.py', 'w', encoding='utf-8') as f:
    f.write(optimized_content)

print("✅ FCM service başlangıç kısmı optimize edildi")
