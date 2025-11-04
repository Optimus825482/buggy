# Notification Permission Request Feature

## Özet

Bu özellik, sürücü ve admin kullanıcılarının login olduktan sonra tarayıcı bildirim izinlerinin otomatik olarak kontrol edilmesini ve gerektiğinde kullanıcıdan izin talep edilmesini sağlar. Bu sayede misafirlerden gelen buggy çağrı taleplerinin anlık bildirimleri alınabilir.

## Özellikler

✅ **Otomatik İzin Kontrolü**: Login sonrası tarayıcı bildirim izni durumu otomatik kontrol edilir
✅ **Akıllı Dialog**: Sadece izin verilmemişse modern bir dialog gösterilir
✅ **Oturum Bazlı**: Aynı oturumda tekrar sorulmaz
✅ **Role-Based**: Sadece driver ve admin için aktif (guest kullanıcılar için değil)
✅ **Non-Blocking**: Sayfa yüklenmesini engellemez, 2 saniye delay ile gösterilir
✅ **Accessibility**: ARIA attributes, keyboard navigation, focus management
✅ **Mobile Responsive**: Tüm ekran boyutlarında çalışır
✅ **Error Handling**: Kapsamlı hata yönetimi ve logging

## Teknik Detaylar

### Backend

**Değişiklikler:**
- `app/services/auth_service.py`: Login sonrası session'a bildirim izni field'ları eklendi
- `app/routes/driver.py`: Dashboard'a session bilgileri inject edildi
- `app/routes/admin.py`: Dashboard'a session bilgileri inject edildi
- `app/routes/api.py`: `/api/notification-permission` POST endpoint'i eklendi

**Session Fields:**
```python
session['notification_permission_asked'] = False  # İzin soruldu mu?
session['notification_permission_status'] = 'default'  # 'default', 'granted', 'denied'
```

### Frontend

**Yeni Dosyalar:**
- `app/static/js/notification-permission.js`: Ana handler sınıfı
- `app/static/css/notification-permission.css`: Dialog ve toast stilleri

**Değişiklikler:**
- `templates/driver/dashboard.html`: Script ve CSS eklendi, init çağrısı yapıldı
- `templates/admin/dashboard.html`: Script ve CSS eklendi, init çağrısı yapıldı

### API Endpoint

**POST /api/notification-permission**

Request:
```json
{
  "status": "granted" | "denied" | "default"
}
```

Response:
```json
{
  "success": true
}
```

## Kullanım

### Kullanıcı Deneyimi

1. Sürücü veya admin login olur
2. Dashboard yüklenir
3. 2 saniye sonra bildirim izni dialog'u gösterilir (eğer daha önce sorulmadıysa)
4. Kullanıcı "İzin Ver" veya "Şimdi Değil" seçer
5. Dialog kapanır ve session güncellenir
6. Aynı oturumda tekrar sorulmaz

### Developer Kullanımı

```javascript
// Initialize handler
notificationPermissionHandler.init(
    'driver',  // or 'admin'
    false,     // alreadyAsked
    'default'  // currentStatus
);

// Manually show dialog
notificationPermissionHandler.showDialog();

// Get permission status
const status = await notificationPermissionHandler.getBrowserPermissionStatus();
```

## Test Etme

### Manuel Test

1. Tarayıcıda bildirim izinlerini sıfırla (Settings > Site Settings > Notifications)
2. Driver veya admin olarak login ol
3. Dashboard'da 2 saniye sonra dialog'un göründüğünü doğrula
4. "İzin Ver" butonuna tıkla
5. Tarayıcının native permission dialog'unun göründüğünü doğrula
6. İzin ver ve dialog'un kapandığını doğrula
7. Logout yap ve tekrar login ol
8. Dialog'un gösterilmediğini doğrula (çünkü izin zaten verilmiş)

### Browser Compatibility

- ✅ Chrome/Edge (Chromium)
- ✅ Firefox
- ✅ Safari (iOS/macOS)
- ✅ Mobile browsers

## Konfigürasyon

### Feature Flag (Opsiyonel)

```python
# config.py
NOTIFICATION_PERMISSION_ENABLED = True
```

### Timing Ayarları

```javascript
// notification-permission.js
setTimeout(() => {
    this.checkAndShowDialog();
}, 2000); // 2 saniye delay
```

## Troubleshooting

### Dialog Gösterilmiyor

1. Console'da hata var mı kontrol et
2. User role'ü driver veya admin mi kontrol et
3. Session'da `notification_permission_asked` değeri kontrol et
4. Tarayıcı bildirim izni durumu kontrol et

### Permission Request Çalışmıyor

1. HTTPS kullanıldığından emin ol (localhost hariç)
2. Tarayıcı bildirim izinlerini destekliyor mu kontrol et
3. Console'da `pushNotifications` global instance'ı var mı kontrol et

### API Endpoint Hata Veriyor

1. CSRF token doğru gönderiliyor mu kontrol et
2. User authenticated mi kontrol et
3. User role'ü driver veya admin mi kontrol et
4. Backend log'larını kontrol et

## Güvenlik

- ✅ CSRF koruması aktif
- ✅ Authentication required
- ✅ Role-based authorization (sadece driver/admin)
- ✅ Input validation (status değerleri)
- ✅ Session-based tracking
- ✅ No sensitive data exposure

## Performance

- ⚡ Non-blocking implementation
- ⚡ 2 saniye delay ile UX optimize edildi
- ⚡ Lazy loading (sadece driver/admin için yüklenir)
- ⚡ Minimal session storage
- ⚡ Asenkron API çağrıları

## Accessibility

- ♿ ARIA attributes (role, aria-labelledby, aria-describedby)
- ♿ Keyboard navigation (Escape tuşu ile kapatma)
- ♿ Focus management (dialog açıldığında ilk button'a focus)
- ♿ Screen reader support
- ♿ High contrast mode support

## Gelecek İyileştirmeler

1. **Reminder System**: X gün sonra tekrar sor
2. **Settings Page**: Kullanıcı ayarlarından bildirim tercihlerini değiştirme
3. **Notification Types**: Hangi bildirimleri almak istediğini seçme
4. **Sound Preferences**: Bildirim sesini özelleştirme
5. **Do Not Disturb**: Sessiz saatler belirleme
6. **Analytics**: Bildirim engagement metrikleri

## Deployment

### Checklist

- [x] Backend değişiklikleri deploy edildi
- [x] Frontend dosyaları deploy edildi
- [x] Template değişiklikleri deploy edildi
- [x] Database migration yok (sadece session kullanılıyor)
- [x] HTTPS aktif (production için gerekli)
- [x] Error monitoring aktif
- [x] Logging aktif

### Rollback

Eğer sorun çıkarsa:

1. Feature flag'i kapat (opsiyonel)
2. Template'lerden script ve CSS satırlarını comment out et
3. Session field'larını temizle (otomatik olarak expire olacak)

## Lisans

Bu özellik BuggyCall projesinin bir parçasıdır.
© 2025 Erkan ERDEM
