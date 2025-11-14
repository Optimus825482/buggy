# FCM Push Notifications - Implementation Guide

## 📱 Firebase Cloud Messaging Entegrasyonu

Bu doküman, BuggyCall uygulamasına entegre edilen FCM (Firebase Cloud Messaging) push notification sisteminin kurulum ve kullanım kılavuzudur.

## 🎯 Özellikler

### ✅ Tamamlanan Özellikler

1. **Priority-Based Notifications**

   - HIGH: Yeni talep bildirimleri (anında, ses + titreşim)
   - NORMAL: Talep kabul bildirimleri
   - LOW: Talep tamamlanma bildirimleri

2. **Rich Media Support**

   - Google Maps static API ile harita thumbnails
   - Görsel URL desteği
   - Fallback handling

3. **Action Buttons**

   - "Kabul Et" - Talebi direkt kabul et
   - "Detaylar" - Talep detaylarını gör
   - "Kapat" - Bildirimi kapat

4. **Token Management**

   - Otomatik token kayıt
   - Token refresh mekanizması
   - Invalid token cleanup

5. **Service Worker**

   - Background message handling
   - Notification click handling
   - Sound caching (offline playback)

6. **Error Handling**
   - Firebase initialization errors
   - Token validation errors
   - Network errors
   - Automatic recovery

## 🔧 Kurulum

### 1. Firebase Projesi Kurulumu

```bash
# Firebase Console'da proje oluştur
# https://console.firebase.google.com

# Web app ekle ve config bilgilerini al
# Cloud Messaging'i aktifleştir
# VAPID key oluştur
```

### 2. Environment Variables

`.env` dosyasına ekle:

```env
# Firebase Configuration
FIREBASE_SERVICE_ACCOUNT_PATH=firebase-service-account.json
FIREBASE_API_KEY=your_api_key
FIREBASE_AUTH_DOMAIN=your_project.firebaseapp.com
FIREBASE_PROJECT_ID=your_project_id
FIREBASE_STORAGE_BUCKET=your_project.firebasestorage.app
FIREBASE_MESSAGING_SENDER_ID=your_sender_id
FIREBASE_APP_ID=your_app_id
FIREBASE_VAPID_KEY=your_vapid_key
```

### 3. Service Account Key

`firebase-service-account.json` dosyasını root dizine ekle (Firebase Console'dan indir).

**ÖNEMLİ:** Bu dosya `.gitignore`'da olmalı!

## 📡 API Endpoints

### Token Management

#### Register Token

```http
POST /api/fcm/register-token
Content-Type: application/json
Authorization: Bearer <jwt_token>

{
  "token": "fcm_device_token"
}
```

#### Refresh Token

```http
POST /api/fcm/refresh-token
Content-Type: application/json
Authorization: Bearer <jwt_token>

{
  "old_token": "old_fcm_token",
  "new_token": "new_fcm_token"
}
```

#### Test Notification

```http
POST /api/fcm/test-notification
Content-Type: application/json
Authorization: Bearer <jwt_token>

{
  "title": "Test Başlık",
  "body": "Test Mesaj"
}
```

## 🎨 Frontend Kullanımı

### Driver Dashboard

FCM otomatik olarak başlatılır:

```javascript
// Otomatik başlatma (fcm-notifications.js)
document.addEventListener("DOMContentLoaded", async () => {
  if (window.location.pathname.includes("/driver")) {
    const initialized = await window.fcmManager.initialize();
    if (initialized) {
      await window.fcmManager.requestPermissionAndGetToken();
    }
  }
});
```

### FCM Mesajlarını Dinleme

```javascript
// Custom event listener
window.addEventListener("fcm-message", (event) => {
  const payload = event.detail;

  if (payload.data?.type === "new_request") {
    // Dashboard'ı güncelle
    loadPendingRequests();
  }
});
```

### Manuel Test

```javascript
// Test notification gönder
await window.fcmManager.sendTestNotification();
```

## 🔔 Notification Types

### 1. New Request (Driver)

```json
{
  "type": "new_request",
  "priority": "high",
  "title": "🚗 Yeni Shuttle Talebi!",
  "body": "📍 Lokasyon\n🏨 Oda 101",
  "data": {
    "request_id": "123",
    "location_name": "Havuz",
    "room_number": "101"
  },
  "actions": [
    { "action": "accept", "title": "✅ Kabul Et" },
    { "action": "details", "title": "👁️ Detaylar" }
  ]
}
```

### 2. Request Accepted (Guest)

```json
{
  "type": "request_accepted",
  "priority": "normal",
  "title": "✅ Shuttle Kabul Edildi",
  "body": "Shuttle'ınız yola çıktı!",
  "data": {
    "request_id": "123",
    "buggy_code": "B01"
  }
}
```

### 3. Request Completed (Guest)

```json
{
  "type": "request_completed",
  "priority": "low",
  "title": "🎉 Shuttle Geldi!",
  "body": "İyi yolculuklar!",
  "data": {
    "request_id": "123"
  }
}
```

## 🐛 Troubleshooting

### Firebase Başlatma Hatası

```bash
# Service account dosyasını kontrol et
ls -la firebase-service-account.json

# Environment variables kontrol et
echo $FIREBASE_PROJECT_ID
```

### Token Alınamıyor

1. HTTPS kullanıldığından emin ol (FCM sadece HTTPS'de çalışır)
2. Service Worker kaydını kontrol et
3. Notification permission'ı kontrol et
4. VAPID key'in doğru olduğunu kontrol et

### Bildirimler Gelmiyor

1. FCM token'ın backend'e kaydedildiğini kontrol et
2. Browser console'da hata var mı kontrol et
3. Service Worker'ın çalıştığını kontrol et: `chrome://serviceworker-internals/`
4. Test endpoint ile test et: `/api/fcm/test-notification`

## 📊 Monitoring

### Backend Logs

```python
# FCM service logs
logger.info(f"✅ FCM bildirimi gönderildi: {response}")
logger.error(f"❌ FCM bildirim hatası: {str(e)}")
```

### Frontend Console

```javascript
// FCM Manager logs
console.log("✅ FCM başlatıldı");
console.log("📨 Foreground mesaj alındı:", payload);
console.log("🔄 FCM token yenileniyor...");
```

### Database

```sql
-- Notification logs
SELECT * FROM notification_log
WHERE notification_type = 'fcm'
ORDER BY sent_at DESC
LIMIT 100;

-- Token status
SELECT id, username, fcm_token, fcm_token_date
FROM system_users
WHERE fcm_token IS NOT NULL;
```

## 🚀 Production Deployment

### Railway Environment Variables

```bash
# Railway dashboard'da ayarla
FIREBASE_SERVICE_ACCOUNT_PATH=firebase-service-account.json
FIREBASE_API_KEY=...
FIREBASE_PROJECT_ID=...
# ... diğer Firebase variables
```

### Service Account (Base64)

```bash
# Service account'u base64 encode et
cat firebase-service-account.json | base64

# Railway'de FIREBASE_SERVICE_ACCOUNT_BASE64 olarak kaydet
```

### HTTPS Kontrolü

Railway otomatik HTTPS sağlar. FCM sadece HTTPS'de çalışır.

## 📝 Notlar

- Socket.IO kaldırıldı, tüm bildirimler FCM üzerinden
- Token'lar otomatik olarak yenilenir
- Invalid token'lar otomatik temizlenir
- Sound dosyaları Service Worker'da cache'lenir
- Action buttons sadece Chrome/Edge'de çalışır

## 🔗 Kaynaklar

- [Firebase Cloud Messaging Docs](https://firebase.google.com/docs/cloud-messaging)
- [Web Push Notifications](https://web.dev/push-notifications-overview/)
- [Service Worker API](https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API)

---

**Powered by Erkan ERDEM**
