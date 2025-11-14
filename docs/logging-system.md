# Shuttle Call - Logging System

## 📋 Genel Bakış

Merkezi logging sistemi tüm önemli olayları `logs/app.log` dosyasına kaydeder.

## 📁 Dosya Yapısı

```
logs/
├── app.log          # Ana log dosyası
├── app.log.1        # Backup 1 (10MB dolunca)
├── app.log.2        # Backup 2
├── app.log.3        # Backup 3
├── app.log.4        # Backup 4
└── app.log.5        # Backup 5 (en eski)
```

## 🎯 Log Seviyeleri

- 🔍 **DEBUG**: Detaylı debug bilgileri
- ✅ **INFO**: Genel bilgi mesajları
- ⚠️ **WARNING**: Uyarı mesajları
- ❌ **ERROR**: Hata mesajları
- 🔥 **CRITICAL**: Kritik hatalar

## 📝 Log Formatı

```
2025-11-14 20:30:45 ✅ [INFO] [shuttle_call] 🚗 Request Event: CREATED | Request ID: 123 | Data: {...}
```

## 🔧 Kullanım

### Import

```python
from app.utils.logger import logger, log_fcm_event, log_request_event, log_driver_event, log_websocket_event, log_error, log_api_call
```

### FCM Olayları

```python
log_fcm_event('TOKEN_REGISTERED', {
    'driver_id': 1,
    'token': 'fcm_token...'
})
```

### Talep Olayları

```python
log_request_event('CREATED', request_id, {
    'guest_name': 'John Doe',
    'location': 'Merit Royal Diamond',
    'hotel_id': 1
})

log_request_event('ACCEPTED', request_id, {
    'driver': 'Ayla KAYA',
    'buggy': 'SHUTTLE-10',
    'response_time': 45
})

log_request_event('COMPLETED', request_id, {
    'driver': 'Ayla KAYA',
    'duration': 300
})
```

### Sürücü Olayları

```python
log_driver_event('LOGIN', driver_id, {
    'buggy': 'SHUTTLE-10',
    'hotel_id': 1
})

log_driver_event('LOGOUT', driver_id)

log_driver_event('STATUS_CHANGED', driver_id, {
    'old_status': 'available',
    'new_status': 'busy'
})
```

### WebSocket Olayları

```python
log_websocket_event('SSE_NEW_REQUEST', {
    'request_id': 123,
    'drivers_notified': 5
})

log_websocket_event('WS_NEW_REQUEST_ADMIN', {
    'request_id': 123,
    'room': 'hotel_1_admin'
})
```

### Hata Loglama

```python
log_error('FCM_NOTIFICATION', 'Token geçersiz', {
    'driver_id': 1,
    'token': 'invalid_token'
})
```

### API Çağrıları

```python
log_api_call('POST', '/api/requests', 200, duration_ms=150)
```

## 📊 Log Örnekleri

### Yeni Talep Oluşturma

```
2025-11-14 20:30:45 ✅ [INFO] 🚗 Request Event: CREATED | Request ID: 123 | Data: {"guest_name": "John Doe", "location": "Merit Royal Diamond", "hotel_id": 1, "room_number": "205"}
2025-11-14 20:30:45 ✅ [INFO] 🔌 WebSocket Event: SSE_NEW_REQUEST | Data: {"request_id": 123, "drivers_notified": 5}
2025-11-14 20:30:45 ✅ [INFO] 🔌 WebSocket Event: WS_NEW_REQUEST_ADMIN | Data: {"request_id": 123, "room": "hotel_1_admin"}
2025-11-14 20:30:46 ✅ [INFO] 🚗 Request Event: FCM_SENT | Request ID: 123 | Data: {"drivers_notified": 5}
```

### Talep Kabul Etme

```
2025-11-14 20:31:15 ✅ [INFO] 🚗 Request Event: ACCEPTED | Request ID: 123 | Data: {"driver": "Ayla KAYA", "buggy": "SHUTTLE-10", "response_time": 30}
2025-11-14 20:31:15 ✅ [INFO] 🔌 WebSocket Event: WS_REQUEST_ACCEPTED | Data: {"request_id": 123, "buggy_id": 10}
```

### FCM Token Kaydı

```
2025-11-14 20:25:30 ✅ [INFO] 📱 FCM Event: TOKEN_REGISTERED | Data: {"driver_id": 1, "token": "fcm_token_abc123..."}
```

### Hata Durumu

```
2025-11-14 20:32:00 ❌ [ERROR] ❌ Error: FCM_NOTIFICATION | Message: Token geçersiz | Data: {"driver_id": 1, "token": "invalid_token"}
```

## 🔍 Log Analizi

### Tüm logları görüntüle

```bash
cat logs/app.log
```

### Son 100 satırı görüntüle

```bash
tail -n 100 logs/app.log
```

### Canlı log takibi

```bash
tail -f logs/app.log
```

### Sadece hataları göster

```bash
grep "ERROR" logs/app.log
```

### Belirli bir request'i takip et

```bash
grep "Request ID: 123" logs/app.log
```

### FCM olaylarını göster

```bash
grep "FCM Event" logs/app.log
```

### Bugün oluşturulan talepleri say

```bash
grep "$(date +%Y-%m-%d)" logs/app.log | grep "Request Event: CREATED" | wc -l
```

## 🎯 Loglanan Olaylar

### Request Events

- ✅ CREATED - Yeni talep oluşturuldu
- ✅ ACCEPTED - Talep kabul edildi
- ✅ COMPLETED - Talep tamamlandı
- ✅ CANCELLED - Talep iptal edildi
- ✅ FCM_SENT - FCM bildirimi gönderildi

### Driver Events

- ✅ LOGIN - Sürücü giriş yaptı
- ✅ LOGOUT - Sürücü çıkış yaptı
- ✅ STATUS_CHANGED - Sürücü durumu değişti
- ✅ FCM_TOKEN_REGISTERED - FCM token kaydedildi

### WebSocket Events

- ✅ SSE_NEW_REQUEST - SSE ile yeni talep bildirimi
- ✅ WS_NEW_REQUEST_ADMIN - WebSocket ile admin bildirimi
- ✅ WS_REQUEST_ACCEPTED - Talep kabul bildirimi
- ✅ WS_REQUEST_COMPLETED - Talep tamamlama bildirimi

### FCM Events

- ✅ SDK_INITIALIZED - Firebase SDK başlatıldı
- ✅ TOKEN_REGISTERED - Token kaydedildi
- ✅ NOTIFICATION_SENT - Bildirim gönderildi
- ❌ TOKEN_INVALID - Geçersiz token
- ❌ SEND_FAILED - Gönderim başarısız

## 📈 Performans

- **Dosya Boyutu**: Max 10MB (otomatik rotation)
- **Backup Sayısı**: 5 dosya
- **Toplam Kapasite**: ~50MB
- **Encoding**: UTF-8 (Türkçe karakter desteği)

## 🔒 Güvenlik

- Log dosyaları `.gitignore`'da
- Hassas bilgiler (şifreler, tokenlar) loglanmaz
- Sadece gerekli bilgiler kaydedilir

## ✅ Tamamlandı!

Logging sistemi aktif ve çalışıyor. Tüm önemli olaylar `logs/app.log` dosyasına kaydediliyor.
