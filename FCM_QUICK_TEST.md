# FCM Push Notifications - Hızlı Test Rehberi

## 🚀 5 Dakikada FCM Testi

### 1. Otomatik Test (30 saniye)

```bash
# Test suite'i çalıştır
pytest tests/test_fcm_notifications.py -v

# Beklenen çıktı:
# ✅ 25+ tests passed
```

---

### 2. Driver Test (1 dakika)

**Adımlar:**

1. Driver olarak login ol
2. Dashboard'a git
3. F12 > Console aç

**Beklenen Console Logları:**

```
✅ FCM başlatıldı
✅ FCM Token alındı: [token]
✅ Token backend'e kaydedildi
```

**Doğrulama:**

```bash
# Backend'de token kontrolü
curl http://localhost:5000/api/fcm/test-notification \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"Test","body":"Test mesajı"}'
```

---

### 3. Guest Test (1 dakika)

**Adımlar:**

1. Guest call sayfasına git
2. QR kod tara veya lokasyon seç
3. Request oluştur
4. Console'da token kaydını gör

**Beklenen:**

```
✅ Guest FCM token kaydedildi
```

---

### 4. End-to-End Test (2 dakika)

**Senaryo:** Yeni talep → Kabul → Tamamlama

1. **Driver dashboard'ı aç** (Sekme 1)
2. **Guest olarak request oluştur** (Sekme 2)
3. **Driver'da bildirim geldiğini gör** ✅
4. **Talebi kabul et**
5. **Guest'te "Kabul Edildi" bildirimi gelir** ✅
6. **Talebi tamamla**
7. **Guest'te "Tamamlandı" bildirimi gelir** ✅

---

### 5. Admin Stats Test (30 saniye)

```bash
# Admin olarak login ol
ADMIN_TOKEN="your_admin_token"

# Stats al
curl "http://localhost:5000/api/admin/notifications/stats?hours=24" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq

# Beklenen:
# {
#   "total_sent": X,
#   "delivery_rate": X%,
#   "fcm": {...}
# }
```

---

## ✅ Başarı Kriterleri

- [ ] Otomatik testler geçti
- [ ] Driver token kaydedildi
- [ ] Guest token kaydedildi
- [ ] Bildirimler geldi
- [ ] Priority seviyeleri çalışıyor
- [ ] Admin stats API çalışıyor

---

## 🐛 Hızlı Troubleshooting

### Token Alınamıyor?

```bash
# HTTPS kontrolü
echo "FCM sadece HTTPS'de çalışır"

# VAPID key kontrolü
grep FIREBASE_VAPID_KEY .env
```

### Bildirim Gelmiyor?

```bash
# Backend log kontrolü
tail -f logs/shuttlecall.log | grep FCM

# Token kontrolü
sqlite3 app.db "SELECT username, fcm_token FROM system_users WHERE fcm_token IS NOT NULL;"
```

### Service Worker Çalışmıyor?

```
1. chrome://serviceworker-internals/ aç
2. firebase-messaging-sw.js görünmeli
3. Status: ACTIVATED olmalı
```

---

## 📊 Test Sonuçları

| Test             | Durum | Süre   |
| ---------------- | ----- | ------ |
| Otomatik Testler | ⏳    | 30s    |
| Driver Token     | ⏳    | 1m     |
| Guest Token      | ⏳    | 1m     |
| End-to-End       | ⏳    | 2m     |
| Admin Stats      | ⏳    | 30s    |
| **TOPLAM**       | ⏳    | **5m** |

---

**Powered by Erkan ERDEM** 🚀
