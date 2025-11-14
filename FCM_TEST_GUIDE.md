# FCM Push Notifications - Test Rehberi

Bu doküman, FCM push notification sisteminin manuel ve otomatik testleri için kapsamlı bir rehberdir.

## 📋 İçindekiler

1. [Otomatik Testler](#otomatik-testler)
2. [Manuel Testler](#manuel-testler)
3. [Test Senaryoları](#test-senaryoları)
4. [Troubleshooting](#troubleshooting)

---

## 🤖 Otomatik Testler

### Test Dosyasını Çalıştırma

```bash
# Tüm FCM testlerini çalıştır
pytest tests/test_fcm_notifications.py -v

# Belirli bir test class'ını çalıştır
pytest tests/test_fcm_notifications.py::TestFCMService -v

# Belirli bir test metodunu çalıştır
pytest tests/test_fcm_notifications.py::TestFCMService::test_register_token -v

# Coverage ile çalıştır
pytest tests/test_fcm_notifications.py --cov=app.services.fcm_notification_service --cov-report=html
```

### Test Kategorileri

#### 1. FCM Service Tests

- ✅ FCM initialization
- ✅ Token registration
- ✅ Token refresh
- ✅ Send to single token
- ✅ Send to multiple tokens
- ✅ New request notification
- ✅ Invalid token cleanup

#### 2. FCM API Tests

- ✅ Register token endpoint
- ✅ Refresh token endpoint
- ✅ Test notification endpoint
- ✅ Unauthorized access handling

#### 3. Guest FCM Tests

- ✅ Guest token registration
- ✅ Missing token handling
- ✅ Missing request_id handling

#### 4. Admin Stats API Tests

- ✅ Notification stats endpoint
- ✅ Timeline stats endpoint
- ✅ Admin authorization

#### 5. Priority Tests

- ✅ High priority notifications
- ✅ Normal priority notifications
- ✅ Low priority notifications

#### 6. Error Handling Tests

- ✅ Unregistered token error
- ✅ Firebase not initialized
- ✅ Network errors

#### 7. Integration Tests

- ✅ Complete request flow

---

## 🧪 Manuel Testler

### Ön Hazırlık

1. **Firebase Credentials Kontrolü**

```bash
# Service account dosyasının varlığını kontrol et
ls -la firebase-service-account.json

# Environment variables kontrolü
echo $FIREBASE_PROJECT_ID
echo $FIREBASE_API_KEY
```

2. **HTTPS Kontrolü**

```bash
# FCM sadece HTTPS'de çalışır
# Railway otomatik HTTPS sağlar
# Local test için ngrok kullan:
ngrok http 5000
```

### Test 1: Driver FCM Token Registration

**Adımlar:**

1. Driver olarak login ol
2. Browser console'u aç (F12)
3. Dashboard'a git
4. Console'da şu mesajları gör:
   ```
   ✅ FCM başlatıldı
   ✅ FCM Token alındı: [token]
   ✅ Token backend'e kaydedildi
   ```

**Beklenen Sonuç:**

- Notification permission istenir
- Token başarıyla alınır ve kaydedilir
- Database'de `fcm_token` ve `fcm_token_date` güncellenir

**Doğrulama:**

```sql
SELECT id, username, fcm_token, fcm_token_date
FROM system_users
WHERE role = 'driver';
```

---

### Test 2: Guest FCM Token Registration

**Adımlar:**

1. Guest call sayfasına git
2. QR kod tara veya lokasyon seç
3. Request oluştur
4. Console'da şu mesajları gör:
   ```
   🔔 Guest FCM başlatılıyor...
   ✅ Guest FCM token alındı
   💾 Guest FCM token kaydediliyor...
   ✅ Guest FCM token kaydedildi
   ```

**Beklenen Sonuç:**

- Token başarıyla alınır
- Backend'e `/guest/register-fcm-token` ile gönderilir
- Request ID ile ilişkilendirilir

**Doğrulama:**

```bash
# Debug endpoint ile kontrol et
curl http://localhost:5000/guest/debug-tokens
```

---

### Test 3: New Request Notification (Driver)

**Adımlar:**

1. Driver dashboard'ı aç (bir tarayıcı sekmesinde)
2. Guest olarak yeni request oluştur (başka bir sekmede)
3. Driver'da bildirim geldiğini gör

**Beklenen Sonuç:**

**Foreground (Dashboard açık):**

- In-app notification gösterilir
- Ses çalar
- Dashboard otomatik güncellenir
- Pending requests listesine yeni talep eklenir

**Background (Dashboard kapalı):**

- System notification gösterilir
- "Kabul Et" ve "Detaylar" butonları görünür
- Notification'a tıklayınca dashboard açılır

**Console Logları:**

```
📨 Foreground mesaj alındı: {type: "new_request", ...}
📬 FCM mesajı alındı: {data: {...}}
🆕 Yeni talep - Dashboard güncelleniyor...
```

**Backend Logları:**

```
✅ FCM: 2 sürücüye bildirim gönderildi
✅ FCM bildirimi gönderildi (Priority: high): message_id
```

---

### Test 4: Request Accepted Notification (Guest)

**Adımlar:**

1. Guest status sayfasını aç
2. Driver olarak talebi kabul et
3. Guest'te bildirim geldiğini gör

**Beklenen Sonuç:**

**Foreground:**

- In-app notification: "✅ Shuttle Kabul Edildi!"
- Sayfa otomatik güncellenir
- Status "ACCEPTED" olarak değişir

**Background:**

- System notification gösterilir
- Notification'a tıklayınca status sayfası açılır

**Console Logları:**

```
📬 Guest status page FCM mesajı alındı
✅ Talep kabul edildi bildirimi - Sayfa yenileniyor...
```

---

### Test 5: Request Completed Notification (Guest)

**Adımlar:**

1. Guest status sayfasını aç
2. Driver olarak talebi tamamla
3. Guest'te bildirim geldiğini gör

**Beklenen Sonuç:**

**Foreground:**

- In-app notification: "🎉 Shuttle Geldi!"
- Sayfa otomatik güncellenir
- Status "COMPLETED" olarak değişir

**Background:**

- System notification gösterilir
- Notification'a tıklayınca status sayfası açılır

---

### Test 6: Test Notification Endpoint

**cURL ile Test:**

```bash
# Login
TOKEN=$(curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"driver1","password":"password"}' \
  | jq -r '.access_token')

# Test notification gönder
curl -X POST http://localhost:5000/api/fcm/test-notification \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "🧪 Test Bildirimi",
    "body": "FCM sistemi çalışıyor!"
  }'
```

**Beklenen Sonuç:**

```json
{
  "message": "Test bildirimi başarıyla gönderildi",
  "user_id": 1,
  "status": "sent"
}
```

---

### Test 7: Token Refresh

**Adımlar:**

1. Driver dashboard'ı aç
2. Console'da token'ı kopyala
3. Firebase'de token'ı invalidate et (veya 7 gün bekle)
4. Sayfayı yenile
5. Yeni token alındığını gör

**Console Logları:**

```
🔄 FCM token yenileniyor...
✅ Yeni token alındı
✅ Token backend'de yenilendi
```

---

### Test 8: Priority-Based Notifications

**Test Senaryosu:**

| Notification Type | Priority | Sound | Vibration | Require Interaction |
| ----------------- | -------- | ----- | --------- | ------------------- |
| New Request       | HIGH     | ✅    | ✅✅✅    | ✅                  |
| Request Accepted  | NORMAL   | ❌    | ✅        | ❌                  |
| Request Completed | LOW      | ❌    | ✅        | ❌                  |

**Doğrulama:**

```sql
SELECT notification_type, priority, COUNT(*) as count
FROM notification_logs
WHERE notification_type = 'fcm'
GROUP BY notification_type, priority;
```

---

### Test 9: Admin Stats API

**Stats Endpoint:**

```bash
# Login as admin
ADMIN_TOKEN=$(curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' \
  | jq -r '.access_token')

# Get notification stats
curl -X GET "http://localhost:5000/api/admin/notifications/stats?hours=24" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  | jq
```

**Beklenen Response:**

```json
{
  "time_range_hours": 24,
  "total_sent": 150,
  "total_delivered": 145,
  "total_failed": 5,
  "delivery_rate": 96.67,
  "click_through_rate": 35.86,
  "by_priority": {
    "high": { "total": 50, "delivered": 48, "failed": 2 },
    "normal": { "total": 75, "delivered": 73, "failed": 2 },
    "low": { "total": 25, "delivered": 24, "failed": 1 }
  },
  "fcm": {
    "total_tokens": 25,
    "active_tokens": 20,
    "driver_tokens": 15,
    "guest_tokens": 10,
    "notifications_sent": 150,
    "delivery_rate": 96.67
  }
}
```

**Timeline Stats:**

```bash
curl -X GET "http://localhost:5000/api/admin/notifications/stats/timeline?period=daily&days=7" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  | jq
```

---

### Test 10: Service Worker

**Chrome DevTools ile Test:**

1. **Service Worker Kontrolü:**

   - Chrome'da `chrome://serviceworker-internals/` aç
   - `firebase-messaging-sw.js` görünmeli
   - Status: "ACTIVATED" olmalı

2. **Background Message Test:**

   - Dashboard'ı kapat
   - Yeni request oluştur
   - System notification gösterilmeli

3. **Action Buttons Test:**

   - Background notification'da "Kabul Et" butonuna tıkla
   - Dashboard açılmalı ve talep otomatik kabul edilmeli

4. **Cache Kontrolü:**
   - DevTools > Application > Cache Storage
   - `fcm-sounds-v1` cache'i görünmeli
   - Sound dosyaları cache'lenmiş olmalı

---

## 🎯 Test Senaryoları

### Senaryo 1: Çoklu Driver Bildirimi

**Durum:** 3 driver müsait, yeni talep geldi

**Beklenen:**

- 3 driver'a da bildirim gönderilir
- Multicast messaging kullanılır
- Tüm driver'lar aynı anda bildirim alır

**Doğrulama:**

```
Backend Log: ✅ FCM: 3 sürücüye bildirim gönderildi
```

---

### Senaryo 2: Invalid Token Cleanup

**Durum:** Driver'ın token'ı geçersiz hale geldi

**Beklenen:**

- Bildirim gönderimi başarısız olur
- Token otomatik olarak database'den silinir
- Log kaydedilir

**Doğrulama:**

```sql
SELECT * FROM notification_logs
WHERE status = 'failed'
AND error_message LIKE '%invalid token%';
```

---

### Senaryo 3: Offline to Online

**Durum:** Driver offline, sonra online oldu

**Beklenen:**

- Offline iken gönderilen bildirimler queue'da bekler
- Online olunca tüm bildirimler teslim edilir
- FCM otomatik retry yapar

---

### Senaryo 4: Permission Denied

**Durum:** Kullanıcı notification permission'ı reddetti

**Beklenen:**

- Permission denied mesajı gösterilir
- Token alınmaz
- Sistem çalışmaya devam eder (graceful degradation)

**Console:**

```
⚠️ Bildirim izni reddedildi
⚠️ Bildirim İzni Gerekli mesajı gösterilir
```

---

## 🔧 Troubleshooting

### Problem 1: Token Alınamıyor

**Belirtiler:**

```
⚠️ Token alınamadı
```

**Çözümler:**

1. HTTPS kontrolü yap (FCM sadece HTTPS'de çalışır)
2. VAPID key'in doğru olduğunu kontrol et
3. Service Worker'ın kayıtlı olduğunu kontrol et
4. Browser console'da hata var mı kontrol et

---

### Problem 2: Bildirim Gelmiyor

**Belirtiler:**

- Request oluşturuldu ama driver'a bildirim gelmedi

**Debug Adımları:**

1. **Backend Log Kontrolü:**

```bash
tail -f logs/shuttlecall.log | grep FCM
```

2. **Token Kontrolü:**

```sql
SELECT id, username, fcm_token
FROM system_users
WHERE role = 'driver' AND fcm_token IS NOT NULL;
```

3. **Notification Log Kontrolü:**

```sql
SELECT * FROM notification_logs
WHERE notification_type = 'fcm'
ORDER BY sent_at DESC
LIMIT 10;
```

4. **Firebase Console Kontrolü:**
   - Firebase Console > Cloud Messaging
   - Quota kontrolü
   - Error logs kontrolü

---

### Problem 3: Service Worker Çalışmıyor

**Belirtiler:**

- Background notification gelmiyor
- `chrome://serviceworker-internals/` da görünmüyor

**Çözümler:**

1. **Service Worker'ı Yeniden Kaydet:**

```javascript
// Console'da çalıştır
navigator.serviceWorker.getRegistrations().then((registrations) => {
  registrations.forEach((reg) => reg.unregister());
});
// Sayfayı yenile
```

2. **Cache Temizle:**

```javascript
caches.keys().then((names) => {
  names.forEach((name) => caches.delete(name));
});
```

3. **Hard Refresh:**
   - Ctrl + Shift + R (Windows/Linux)
   - Cmd + Shift + R (Mac)

---

### Problem 4: High Priority Çalışmıyor

**Belirtiler:**

- Bildirim geliyor ama ses/titreşim yok
- Require interaction çalışmıyor

**Kontrol:**

1. **Priority Kontrolü:**

```sql
SELECT priority, COUNT(*)
FROM notification_logs
WHERE notification_type = 'fcm'
GROUP BY priority;
```

2. **Backend Code Kontrolü:**

```python
# fcm_notification_service.py
# notify_new_request metodunda priority='high' olmalı
```

3. **Device Settings:**
   - Notification settings
   - Do Not Disturb mode
   - Battery optimization

---

## 📊 Test Metrikleri

### Başarı Kriterleri

| Metrik                     | Hedef | Kabul Edilebilir |
| -------------------------- | ----- | ---------------- |
| Delivery Rate              | >95%  | >90%             |
| Click-Through Rate         | >30%  | >20%             |
| Token Registration Success | >98%  | >95%             |
| Average Delivery Time      | <2s   | <5s              |
| Error Rate                 | <5%   | <10%             |

### Test Coverage

```bash
# Coverage raporu oluştur
pytest tests/test_fcm_notifications.py --cov=app.services.fcm_notification_service --cov=app.routes.fcm_api --cov-report=html

# Raporu aç
open htmlcov/index.html
```

**Hedef Coverage:** >80%

---

## 🚀 Production Test Checklist

- [ ] Firebase credentials production'da ayarlandı
- [ ] HTTPS aktif
- [ ] Environment variables doğru
- [ ] Service Worker production URL'de çalışıyor
- [ ] Driver token registration çalışıyor
- [ ] Guest token registration çalışıyor
- [ ] New request notification çalışıyor
- [ ] Request accepted notification çalışıyor
- [ ] Request completed notification çalışıyor
- [ ] Priority-based notifications çalışıyor
- [ ] Invalid token cleanup çalışıyor
- [ ] Admin stats API çalışıyor
- [ ] Error handling çalışıyor
- [ ] Monitoring ve logging aktif

---

## 📝 Test Raporu Şablonu

```markdown
# FCM Test Raporu

**Test Tarihi:** [Tarih]
**Test Eden:** [İsim]
**Environment:** [Development/Staging/Production]

## Test Sonuçları

### Otomatik Testler

- Total Tests: X
- Passed: X
- Failed: X
- Coverage: X%

### Manuel Testler

- Driver Token Registration: ✅/❌
- Guest Token Registration: ✅/❌
- New Request Notification: ✅/❌
- Request Accepted Notification: ✅/❌
- Request Completed Notification: ✅/❌
- Priority Levels: ✅/❌
- Service Worker: ✅/❌
- Admin Stats API: ✅/❌

### Performans Metrikleri

- Delivery Rate: X%
- Average Delivery Time: Xs
- Error Rate: X%

### Sorunlar

1. [Sorun açıklaması]
   - Severity: High/Medium/Low
   - Status: Open/Resolved

### Notlar

[Ek notlar]
```

---

**Powered by Erkan ERDEM** 🚀
