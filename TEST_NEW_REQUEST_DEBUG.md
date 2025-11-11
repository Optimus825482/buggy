# Yeni Talep Görünmeme Sorunu - Debug Rehberi

## 🔍 Sorun
Misafirler tarafından gönderilen shuttle talepleri:
- ❌ Sürücü panelinde görünmüyor
- ❌ Admin panelinde görünmüyor  
- ❌ Bildirim gitmiyor

## ✅ Yapılan Kontroller

### 1. Backend - API Endpoint
**Dosya**: `app/routes/api.py` - `create_request()`
- ✅ Talep veritabanına kaydediliyor
- ✅ WebSocket emit yapılıyor (drivers + admin)
- ✅ Push notification eklendi

### 2. WebSocket Events
**Dosya**: `app/websocket/events.py`
- ✅ `join_hotel` event handler var
- ✅ Room join işlemi çalışıyor
- ✅ `new_request` event emit ediliyor

### 3. Frontend - Sürücü Paneli
**Dosya**: `app/static/js/driver-dashboard.js`
- ✅ Socket.io bağlantısı var
- ✅ `join_hotel` emit ediliyor
- ✅ `new_request` listener var
- ✅ `handleNewRequest()` metodu var
- ✅ `loadPendingRequests()` API çağrısı yapıyor

### 4. Frontend - Admin Paneli
**Dosya**: `app/static/js/admin-dashboard.js`
- ✅ Socket.io bağlantısı var
- ✅ `join_hotel` emit ediliyor
- ✅ `new_request` listener var

## 🐛 Debug Adımları

### Adım 1: Browser Console Kontrol
Sürücü panelinde F12 açın ve console'da şunları kontrol edin:

```javascript
// Socket bağlantısı var mı?
console.log('Socket connected:', socket.connected);

// Hangi room'a join oldu?
// "Client joined: hotel_1_drivers" mesajını görmeli

// Yeni talep geldiğinde:
// "New request received: {data}" mesajını görmeli
```

### Adım 2: Backend Log Kontrol
Terminal/log dosyasında şunları arayın:

```
✅ Push notifications sent to X driver(s)
Client joined: hotel_1_drivers
New request notification sent to hotel 1 drivers
```

### Adım 3: Network Tab Kontrol
Browser DevTools > Network sekmesinde:

1. **WebSocket bağlantısı**
   - `socket.io` connection var mı?
   - Status: 101 Switching Protocols olmalı

2. **API çağrıları**
   - `/api/requests` POST - 201 Created
   - `/api/driver/PENDING-requests` GET - 200 OK

### Adım 4: Database Kontrol
```sql
-- Pending talepler var mı?
SELECT * FROM buggy_requests WHERE status = 'PENDING' ORDER BY requested_at DESC LIMIT 5;

-- Sürücü buggy'ye atanmış mı?
SELECT u.username, bd.buggy_id, bd.is_active 
FROM system_users u 
LEFT JOIN buggy_drivers bd ON u.id = bd.driver_id 
WHERE u.role = 'driver';

-- Buggy durumu ne?
SELECT id, code, status, hotel_id FROM buggies;
```

## 🔧 Olası Sorunlar ve Çözümler

### Sorun 1: Socket.io Bağlantısı Yok
**Belirti**: Console'da "Socket connected" yok
**Çözüm**:
```javascript
// Socket.io script yüklü mü kontrol et
if (typeof io === 'undefined') {
    console.error('Socket.IO not loaded!');
}
```

### Sorun 2: Room Join Başarısız
**Belirti**: "Client joined" log'u yok
**Çözüm**:
- `hotel_id` doğru mu kontrol et
- Session aktif mi kontrol et

### Sorun 3: Sürücü Buggy'ye Atanmamış
**Belirti**: "No buggy assigned" hatası
**Çözüm**:
```sql
-- Sürücüye buggy ata
INSERT INTO buggy_drivers (buggy_id, driver_id, is_active, assigned_at)
VALUES (1, <driver_user_id>, 1, NOW());
```

### Sorun 4: Pending Requests Boş Dönüyor
**Belirti**: API 200 OK ama requests: []
**Çözüm**:
- Hotel ID eşleşiyor mu?
- Status gerçekten 'PENDING' mi?
- RequestStatus enum doğru mu?

## 🧪 Manuel Test

### Test 1: Talep Oluştur
```bash
curl -X POST http://localhost:5000/api/requests \
  -H "Content-Type: application/json" \
  -d '{
    "location_id": 1,
    "guest_name": "Test Misafir",
    "room_number": "101",
    "phone": "5551234567"
  }'
```

Beklenen:
```json
{
  "success": true,
  "request_id": 123,
  "message": "Buggy çağrınız alındı"
}
```

### Test 2: Pending Requests Çek
```bash
curl http://localhost:5000/api/driver/PENDING-requests \
  -H "Cookie: session=<session_cookie>"
```

Beklenen:
```json
{
  "success": true,
  "requests": [
    {
      "id": 123,
      "guest_name": "Test Misafir",
      "location": {"id": 1, "name": "Lobby"}
    }
  ]
}
```

### Test 3: WebSocket Event Test
Browser console'da:
```javascript
// Manuel event dinle
socket.on('new_request', (data) => {
    console.log('🎉 NEW REQUEST:', data);
    alert('Yeni talep geldi!');
});

// Manuel room join
socket.emit('join_hotel', {
    hotel_id: 1,
    role: 'driver'
});
```

## 📊 Kontrol Listesi

Sürücü panelinde yeni talep görmek için:

- [ ] Sürücü login olmuş
- [ ] Sürücüye buggy atanmış (`buggy_drivers` tablosu)
- [ ] Buggy aktif (`is_active = true`)
- [ ] Socket.io bağlantısı kurulmuş
- [ ] `hotel_X_drivers` room'una join olmuş
- [ ] Talep `PENDING` status'ünde
- [ ] Talep aynı hotel_id'ye ait
- [ ] Browser console'da hata yok

## 🚀 Hızlı Fix

Eğer hala görünmüyorsa:

1. **Hard Refresh**: Ctrl+Shift+R (cache temizle)
2. **Session Yenile**: Logout > Login
3. **Buggy Yeniden Ata**: Admin panelden buggy assignment yap
4. **Server Restart**: Flask uygulamasını yeniden başlat

## 📝 Eklenen Özellikler

### Push Notification Desteği
```python
# app/routes/api.py - create_request()
from app.services.notification_service import NotificationService
notification_count = NotificationService.notify_new_request_v2(buggy_request)
```

Bu kod:
- ✅ Tüm available sürücülere push notification gönderir
- ✅ Ses + vibrasyon ile uyarır
- ✅ Harita thumbnail gösterir
- ✅ "Kabul Et" ve "Detaylar" butonları ekler

## 🔍 Gerçek Zamanlı Monitoring

Terminal'de şu komutla log'ları izleyin:
```bash
# Windows
type app.log | findstr "new_request"

# Linux/Mac
tail -f app.log | grep "new_request"
```

Görmeli:
```
[INFO] New request created: ID=123
[INFO] WebSocket emit: new_request to hotel_1_drivers
[INFO] ✅ Push notifications sent to 2 driver(s)
[INFO] Client joined: hotel_1_drivers
```

---

**Son Güncelleme**: 2025-01-11
**Durum**: Debug rehberi hazır, test edilmeli
