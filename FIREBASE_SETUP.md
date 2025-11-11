# 🔥 Firebase Cloud Messaging (FCM) Kurulum Rehberi
## Buggy Call - Push Notification Sistemi

Bu dokümantasyon, Buggy Call sistemine Firebase Cloud Messaging (FCM) entegrasyonunu adım adım açıklar.

---

## 📋 İçindekiler

1. [Firebase Projesi Oluşturma](#1-firebase-projesi-oluşturma)
2. [Firebase Yapılandırması](#2-firebase-yapılandırması)
3. [Backend Kurulumu](#3-backend-kurulumu)
4. [Frontend Kurulumu](#4-frontend-kurulumu)
5. [Test Etme](#5-test-etme)
6. [Sorun Giderme](#6-sorun-giderme)

---

## 1. Firebase Projesi Oluşturma

### Adım 1.1: Firebase Console'a Git
- https://console.firebase.google.com/ adresine git
- Google hesabınla giriş yap

### Adım 1.2: Yeni Proje Oluştur
1. **"Add project"** butonuna tıkla
2. Proje adı: `BuggyCall` (veya istediğin isim)
3. Google Analytics'i etkinleştir (opsiyonel)
4. **"Create project"** tıkla

### Adım 1.3: Web App Ekle
1. Proje dashboard'unda **"Web"** ikonuna tıkla (`</>`)
2. App nickname: `Buggy Call Web`
3. **"Register app"** tıkla
4. **Firebase SDK configuration** bilgilerini kopyala (sonra kullanacağız)

```javascript
// Bu bilgileri kopyala
const firebaseConfig = {
  apiKey: "AIzaSy...",
  authDomain: "buggycall-xxxxx.firebaseapp.com",
  projectId: "buggycall-xxxxx",
  storageBucket: "buggycall-xxxxx.appspot.com",
  messagingSenderId: "123456789",
  appId: "1:123456789:web:xxxxx"
};
```

---

## 2. Firebase Yapılandırması

### Adım 2.1: Cloud Messaging Aktifleştir
1. Sol menüden **"Build"** > **"Cloud Messaging"** seç
2. **"Get started"** tıkla
3. Cloud Messaging API'yi etkinleştir

### Adım 2.2: VAPID Key Al
1. **"Cloud Messaging"** sayfasında
2. **"Web configuration"** sekmesine git
3. **"Web Push certificates"** bölümünde
4. **"Generate key pair"** tıkla
5. **VAPID key**'i kopyala (örn: `BNxxx...`)

### Adım 2.3: Service Account Key İndir
1. Sol üstteki ⚙️ **"Project settings"** tıkla
2. **"Service accounts"** sekmesine git
3. **"Generate new private key"** tıkla
4. JSON dosyasını indir
5. Dosyayı `firebase-service-account.json` olarak proje kök dizinine kaydet

```bash
# Dosya yapısı
buggycall/
├── firebase-service-account.json  ← Buraya kaydet
├── app/
├── requirements.txt
└── ...
```

⚠️ **ÖNEMLİ:** Bu dosyayı `.gitignore`'a ekle!

```bash
# .gitignore'a ekle
firebase-service-account.json
```

---

## 3. Backend Kurulumu

### Adım 3.1: Environment Variables Ayarla

`.env` dosyasını düzenle:

```bash
# Firebase Cloud Messaging (FCM)
FIREBASE_SERVICE_ACCOUNT_PATH=firebase-service-account.json
FIREBASE_API_KEY=AIzaSy...
FIREBASE_AUTH_DOMAIN=buggycall-xxxxx.firebaseapp.com
FIREBASE_PROJECT_ID=buggycall-xxxxx
FIREBASE_STORAGE_BUCKET=buggycall-xxxxx.appspot.com
FIREBASE_MESSAGING_SENDER_ID=123456789
FIREBASE_APP_ID=1:123456789:web:xxxxx
FIREBASE_VAPID_KEY=BNxxx...
```

### Adım 3.2: Bağımlılıkları Kontrol Et

`requirements.txt` zaten `firebase-admin` içeriyor:

```bash
firebase-admin==6.3.0
```

Eğer yeni kurulum yapıyorsan:

```bash
pip install firebase-admin==6.3.0
```

### Adım 3.3: Database Migration (Opsiyonel)

FCM token alanları zaten `system_users` tablosunda mevcut:
- `fcm_token` (String 255)
- `fcm_token_date` (DateTime)

Eğer yoksa migration çalıştır:

```bash
flask db migrate -m "Add FCM token fields"
flask db upgrade
```

---

## 4. Frontend Kurulumu

### Adım 4.1: Firebase Config Güncelle

**Dosya:** `app/static/js/fcm-notifications.js`

```javascript
// Firebase Config'i güncelle (satır 11-18)
this.firebaseConfig = {
    apiKey: "AIzaSy...",                              // ← Buraya kopyala
    authDomain: "buggycall-xxxxx.firebaseapp.com",   // ← Buraya kopyala
    projectId: "buggycall-xxxxx",                     // ← Buraya kopyala
    storageBucket: "buggycall-xxxxx.appspot.com",    // ← Buraya kopyala
    messagingSenderId: "123456789",                   // ← Buraya kopyala
    appId: "1:123456789:web:xxxxx"                   // ← Buraya kopyala
};
```

### Adım 4.2: VAPID Key Ekle

**Aynı dosyada** (satır 82):

```javascript
const token = await this.messaging.getToken({
    vapidKey: 'BNxxx...',  // ← VAPID key'ini buraya kopyala
    serviceWorkerRegistration: registration
});
```

### Adım 4.3: Service Worker Config Güncelle

**Dosya:** `app/static/firebase-messaging-sw.js`

```javascript
// Firebase Configuration (satır 10-17)
const firebaseConfig = {
  apiKey: "AIzaSy...",                              // ← Buraya kopyala
  authDomain: "buggycall-xxxxx.firebaseapp.com",   // ← Buraya kopyala
  projectId: "buggycall-xxxxx",                     // ← Buraya kopyala
  storageBucket: "buggycall-xxxxx.appspot.com",    // ← Buraya kopyala
  messagingSenderId: "123456789",                   // ← Buraya kopyala
  appId: "1:123456789:web:xxxxx"                   // ← Buraya kopyala
};
```

---

## 5. Test Etme

### Adım 5.1: Uygulamayı Başlat

```bash
# Development
python run.py

# Production (Railway)
gunicorn --worker-class gevent --workers 1 --bind 0.0.0.0:$PORT wsgi:app
```

### Adım 5.2: Driver Dashboard'a Giriş Yap

1. Tarayıcıda `http://localhost:5000` aç
2. Driver hesabıyla giriş yap
3. Dashboard açıldığında:
   - Bildirim izni istenir
   - **"İzin Ver"** tıkla
   - Console'da şu mesajları göreceksin:

```
✅ FCM başlatıldı
✅ Bildirim izni verildi
✅ Service Worker kaydedildi
✅ FCM Token alındı: xxxxxx...
✅ Token backend'e kaydedildi
```

### Adım 5.3: Test Bildirimi Gönder

**Browser Console'da:**

```javascript
// Test bildirimi gönder
await window.fcmManager.sendTestNotification();
```

Veya **API ile:**

```bash
curl -X POST http://localhost:5000/api/fcm/test-notification \
  -H "Content-Type: application/json" \
  -H "Cookie: session=YOUR_SESSION_COOKIE" \
  -d '{"title": "Test", "body": "FCM çalışıyor!"}'
```

### Adım 5.4: Gerçek Talep Testi

1. Başka bir tarayıcıda misafir olarak QR kod okut
2. Yeni talep oluştur
3. Driver dashboard'da:
   - ✅ Push notification gelir
   - ✅ Ses çalar
   - ✅ Liste güncellenir

---

## 6. Sorun Giderme

### ❌ "Firebase SDK yüklenmemiş" Hatası

**Çözüm:** Firebase SDK script'lerinin yüklendiğinden emin ol

```html
<!-- templates/driver/dashboard.html -->
<script src="https://www.gstatic.com/firebasejs/10.7.0/firebase-app-compat.js"></script>
<script src="https://www.gstatic.com/firebasejs/10.7.0/firebase-messaging-compat.js"></script>
```

### ❌ "Service Worker kaydedilemedi" Hatası

**Çözüm 1:** HTTPS kullan (localhost'ta HTTP de çalışır)

**Çözüm 2:** Service Worker dosyasının doğru yolda olduğunu kontrol et:
```
http://localhost:5000/static/firebase-messaging-sw.js
```

### ❌ "Token alınamadı" Hatası

**Çözüm:** VAPID key'in doğru olduğundan emin ol

```javascript
// fcm-notifications.js içinde
vapidKey: 'BNxxx...'  // ← Firebase Console'dan aldığın key
```

### ❌ "Bildirim izni reddedildi"

**Çözüm:** Tarayıcı ayarlarından bildirimleri sıfırla

**Chrome:**
1. Adres çubuğundaki 🔒 ikona tıkla
2. "Site settings" > "Notifications"
3. "Ask (default)" seç
4. Sayfayı yenile

**Firefox:**
1. Adres çubuğundaki 🔒 ikona tıkla
2. "Clear permissions and reload"

### ❌ Backend'de "Firebase başlatılamadı" Hatası

**Çözüm:** Service account dosyasını kontrol et

```bash
# Dosya var mı?
ls -la firebase-service-account.json

# İçeriği geçerli mi?
cat firebase-service-account.json | python -m json.tool
```

### ❌ "Token backend'e kaydedilemedi" Hatası

**Çözüm:** Session kontrolü

```javascript
// Browser console'da
console.log(document.cookie);  // Session cookie var mı?
```

---

## 📊 Sistem Akışı

```
┌─────────────┐
│   Misafir   │
│  QR Okuttu  │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│ Flask Backend   │
│ create_request()│
└──────┬──────────┘
       │
       ├─────────────────────┐
       │                     │
       ▼                     ▼
┌─────────────┐      ┌──────────────┐
│  Socket.IO  │      │ FCM Service  │
│   (Gerçek   │      │ (Push Notif) │
│    Zamanlı) │      └──────┬───────┘
└──────┬──────┘             │
       │                    │
       │                    ▼
       │            ┌───────────────┐
       │            │ Firebase FCM  │
       │            │    Sunucu     │
       │            └───────┬───────┘
       │                    │
       ▼                    ▼
┌──────────────────────────────┐
│   Sürücü Tarayıcısı          │
│   - Uygulama Açık: Foreground│
│   - Uygulama Kapalı: Background│
└──────────────────────────────┘
```

---

## 🎯 Özellikler

### ✅ Çalışan Özellikler

- ✅ Yeni talep bildirimleri (tüm sürücülere)
- ✅ Talep kabul bildirimi (misafire)
- ✅ Talep tamamlandı bildirimi (misafire)
- ✅ Foreground notifications (uygulama açıkken)
- ✅ Background notifications (uygulama kapalıyken)
- ✅ Ses ve titreşim
- ✅ Token yönetimi (kayıt, yenileme, silme)
- ✅ Geçersiz token temizleme
- ✅ Notification log (veritabanı)
- ✅ Test endpoint'i

### 🔄 Socket.IO + FCM Hibrit Sistem

Sistem hem Socket.IO hem de FCM kullanır:

| Durum | Socket.IO | FCM |
|-------|-----------|-----|
| Uygulama açık | ✅ Gerçek zamanlı | ✅ Yedek |
| Uygulama kapalı | ❌ Çalışmaz | ✅ Push |
| Ağ yok | ❌ Çalışmaz | ⏳ Kuyruğa alır |
| Tarayıcı kapalı | ❌ Çalışmaz | ✅ Push |

---

## 🔐 Güvenlik Notları

### ⚠️ Önemli Güvenlik Kuralları

1. **Service Account Key'i GİZLE**
   ```bash
   # .gitignore'a ekle
   firebase-service-account.json
   *.json
   ```

2. **Environment Variables Kullan**
   - Asla config'leri kod içine yazma
   - `.env` dosyasını commit etme

3. **Firebase Security Rules**
   - Firebase Console > Firestore/Storage > Rules
   - Sadece authenticated kullanıcılara izin ver

4. **Token Rotation**
   - Token'lar periyodik olarak yenilenmeli
   - Geçersiz token'lar otomatik temizlenir

---

## 📈 Monitoring & Analytics

### Firebase Console'da İzleme

1. **Cloud Messaging** > **Reports**
   - Gönderilen bildirim sayısı
   - Açılma oranı
   - Hata oranı

2. **Analytics** (eğer aktifse)
   - Kullanıcı davranışları
   - Bildirim etkileşimleri

### Backend Logs

```python
# app/services/fcm_notification_service.py
# Her bildirim loglanır:
# - notification_log tablosuna kaydedilir
# - Console'a yazdırılır
```

---

## 🚀 Production Deployment

### Railway Deployment

1. **Environment Variables Ekle**
   ```
   FIREBASE_SERVICE_ACCOUNT_PATH=firebase-service-account.json
   FIREBASE_API_KEY=...
   FIREBASE_PROJECT_ID=...
   # ... diğer değişkenler
   ```

2. **Service Account JSON'u Ekle**
   
   **Seçenek 1:** Railway Dashboard
   - Settings > Variables
   - `FIREBASE_SERVICE_ACCOUNT_JSON` adında yeni variable
   - JSON içeriğini yapıştır

   **Seçenek 2:** Base64 Encode
   ```bash
   # Local'de
   cat firebase-service-account.json | base64 > firebase-base64.txt
   
   # Railway'de decode et
   echo $FIREBASE_SERVICE_ACCOUNT_BASE64 | base64 -d > firebase-service-account.json
   ```

3. **HTTPS Zorunlu**
   - FCM sadece HTTPS'de çalışır
   - Railway otomatik HTTPS sağlar

---

## 📚 Ek Kaynaklar

- [Firebase Cloud Messaging Docs](https://firebase.google.com/docs/cloud-messaging)
- [Web Push Notifications](https://web.dev/push-notifications-overview/)
- [Service Worker API](https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API)

---

## ✅ Kurulum Checklist

- [ ] Firebase projesi oluşturuldu
- [ ] Web app eklendi
- [ ] Cloud Messaging aktif
- [ ] VAPID key alındı
- [ ] Service account key indirildi
- [ ] `.env` dosyası güncellendi
- [ ] Frontend config'ler güncellendi
- [ ] Service worker config güncellendi
- [ ] Test bildirimi başarılı
- [ ] Gerçek talep testi başarılı
- [ ] Production'a deploy edildi

---

**🎉 Tebrikler! FCM sistemi hazır.**

Sorular için: [GitHub Issues](https://github.com/your-repo/issues)
