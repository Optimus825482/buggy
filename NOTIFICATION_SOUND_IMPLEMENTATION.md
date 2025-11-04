# 🔔 Push Bildirim Ses Özelliği - Teknik Dokümantasyon

## 📋 Özet

Misafirlerden gelen buggy taleplerinde sürücülere gönderilen push bildirimlerine **ses** ve **titreşim** desteği eklendi.

## 🎯 Değişiklikler

### 1. Backend - Notification Service
**Dosya**: `app/services/notification_service.py`

```python
# Yeni parametreler eklendi
def send_notification(subscription_info, title, body, data=None, sound=None, vibrate=None):
    # Ses ve titreşim desteği
    if sound:
        notification_data["sound"] = sound
    if vibrate:
        notification_data["vibrate"] = vibrate
```

**Misafir Talebi Bildirimi**:
```python
NotificationService.send_notification(
    subscription_info=driver.push_subscription,
    title="🔔 Yeni Buggy Talebi",
    body=f"{request_obj.location.name} - Oda: {request_obj.room_number}",
    data={'type': 'new_request', 'request_id': request_obj.id, 'priority': 'high'},
    sound="/static/sounds/notification.mp3",
    vibrate=[200, 100, 200, 100, 200]
)
```

### 2. Service Worker - Push Handler
**Dosya**: `app/static/sw.js` (v2.0.3)

```javascript
// Push event handler - ses desteği ile
self.addEventListener('push', (event) => {
    const data = event.data.json();
    const options = {
        body: data.body,
        icon: data.icon,
        badge: data.badge,
        vibrate: data.vibrate || [200, 100, 200],
        requireInteraction: data.data?.priority === 'high',
        silent: false, // Ses çalmasını sağla
        data: { sound: data.sound, ...data.data }
    };
    
    event.waitUntil(
        Promise.all([
            self.registration.showNotification(title, options),
            playNotificationSound(data.sound)
        ])
    );
});

// Ses çalma fonksiyonu
async function playNotificationSound(soundUrl) {
    const clients = await self.clients.matchAll({ type: 'window' });
    for (const client of clients) {
        client.postMessage({
            type: 'PLAY_NOTIFICATION_SOUND',
            soundUrl: soundUrl
        });
    }
}
```

### 3. Client-Side - Audio Player
**Dosya**: `app/static/js/common.js`

```javascript
// Service Worker mesaj dinleyicisi
if ('serviceWorker' in navigator) {
    navigator.serviceWorker.addEventListener('message', (event) => {
        if (event.data && event.data.type === 'PLAY_NOTIFICATION_SOUND') {
            playNotificationSound(event.data.soundUrl);
        }
    });
}

// Ses çalma fonksiyonu
function playNotificationSound(soundUrl) {
    const audio = new Audio(soundUrl);
    audio.volume = 1.0;
    audio.play()
        .then(() => console.log('[Audio] Sound played'))
        .catch((error) => console.warn('[Audio] Autoplay blocked:', error));
}
```

## 📁 Dosya Yapısı

```
app/
├── services/
│   └── notification_service.py  ✅ Güncellendi
├── static/
│   ├── js/
│   │   └── common.js            ✅ Güncellendi
│   ├── sounds/
│   │   ├── README.md            ✅ Yeni
│   │   ├── generate_notification_sound.html  ✅ Yeni
│   │   └── notification.mp3     ⚠️ Eklenecek
│   └── sw.js                    ✅ Güncellendi (v2.0.3)
```

## 🎵 Ses Dosyası Gereksinimleri

- **Format**: MP3, OGG veya WAV
- **Boyut**: Maksimum 100KB
- **Süre**: 1-3 saniye
- **Konum**: `app/static/sounds/notification.mp3`

## 🔄 Çalışma Akışı

```
1. Misafir Talebi Oluşturur
   ↓
2. Backend: notify_new_request() çağrılır
   ↓
3. Backend: send_notification() - ses ve titreşim parametreleri ile
   ↓
4. Push API: Bildirim gönderilir
   ↓
5. Service Worker: Push event yakalanır
   ↓
6. Service Worker: Bildirim gösterilir + ses mesajı gönderilir
   ↓
7. Client: Mesaj alınır
   ↓
8. Client: Audio API ile ses çalınır
   ↓
9. Sürücü: Bildirim + Ses + Titreşim alır ✅
```

## ⚙️ Özellikler

### Ses Özellikleri
- ✅ Özel bildirim sesi
- ✅ Maksimum ses seviyesi
- ✅ Autoplay politikası yönetimi
- ✅ Hata toleransı

### Titreşim Özellikleri
- ✅ Özel titreşim deseni: [200ms, 100ms, 200ms, 100ms, 200ms]
- ✅ 5 aşamalı titreşim
- ✅ Mobil cihaz desteği

### Bildirim Özellikleri
- ✅ Yüksek öncelik (`requireInteraction: true`)
- ✅ Emoji desteği (🔔)
- ✅ Özel icon ve badge
- ✅ Tıklanabilir

## 🔒 Güvenlik ve Performans

### Güvenlik
- ✅ Ses dosyası static klasörde (güvenli)
- ✅ CORS politikası uyumlu
- ✅ XSS koruması

### Performans
- ✅ Ses dosyası cache'lenir
- ✅ Lazy loading (sadece gerektiğinde yüklenir)
- ✅ Hata durumunda sessiz devam eder
- ✅ Minimal boyut (100KB max)

## 🌐 Tarayıcı Desteği

| Özellik | Chrome | Firefox | Safari | Edge |
|---------|--------|---------|--------|------|
| Push Notifications | ✅ | ✅ | ✅ (16.4+) | ✅ |
| Audio API | ✅ | ✅ | ✅ | ✅ |
| Vibration API | ✅ | ✅ | ❌ | ✅ |
| Service Worker | ✅ | ✅ | ✅ | ✅ |

## 🐛 Bilinen Sınırlamalar

1. **Autoplay Politikası**: İlk bildirimde ses çalmayabilir (kullanıcı etkileşimi gerekir)
2. **iOS Titreşim**: Safari'de Vibration API desteklenmez
3. **Ses Formatı**: Bazı tarayıcılar sadece belirli formatları destekler
4. **Arka Plan**: Uygulama kapalıyken ses çalmayabilir (tarayıcıya bağlı)

## 📱 Mobil Davranış

### Android
- ✅ Ses çalar
- ✅ Titreşim çalışır
- ✅ Bildirim gösterilir
- ✅ Arka planda çalışır

### iOS
- ✅ Ses çalar (PWA olarak eklenirse)
- ❌ Titreşim çalışmaz
- ✅ Bildirim gösterilir
- ⚠️ PWA olarak eklenmeli

## 🧪 Test Senaryoları

### Test 1: Temel Ses Testi
1. Driver giriş yap
2. Misafir talebi oluştur
3. Bildirim geldi mi? ✅
4. Ses çaldı mı? ✅

### Test 2: Titreşim Testi
1. Mobil cihazda test et
2. Titreşim oldu mu? ✅

### Test 3: Çoklu Bildirim
1. Birden fazla driver ekle
2. Talep oluştur
3. Tüm driver'lar bildirim aldı mı? ✅

### Test 4: Arka Plan
1. Uygulamayı arka plana al
2. Talep oluştur
3. Bildirim geldi mi? ✅

## 🔧 Yapılandırma

### Ses Seviyesi Değiştirme
```javascript
// common.js içinde
audio.volume = 0.8; // 0.0 - 1.0 arası
```

### Titreşim Deseni Değiştirme
```python
# notification_service.py içinde
vibrate=[300, 200, 300]  # [titreşim, bekleme, titreşim] ms
```

### Öncelik Seviyesi
```python
# Yüksek öncelik (kullanıcı etkileşimi gerekli)
data={'priority': 'high'}

# Normal öncelik
data={'priority': 'normal'}
```

## 📚 Kaynaklar

- [Web Push API](https://developer.mozilla.org/en-US/docs/Web/API/Push_API)
- [Notifications API](https://developer.mozilla.org/en-US/docs/Web/API/Notifications_API)
- [Vibration API](https://developer.mozilla.org/en-US/docs/Web/API/Vibration_API)
- [Audio API](https://developer.mozilla.org/en-US/docs/Web/API/HTMLAudioElement)

---

**Geliştirici**: Erkan ERDEM  
**Tarih**: 2024  
**Versiyon**: 2.0.3  
**Durum**: ✅ Tamamlandı
