# Implementation Plan

- [x] 1. Backend session management ve API endpoint oluşturma




  - Login sonrası session'a bildirim izni durumunu ekle
  - Dashboard route'larına session bilgilerini inject et
  - Bildirim izni durumunu güncellemek için API endpoint oluştur
  - _Requirements: 1.1, 2.1, 3.1, 3.2, 6.1_


- [x] 1.1 Auth service'e session field'ları ekle

  - `app/services/auth.py` dosyasında login fonksiyonunu güncelle
  - Session'a `notification_permission_asked` (False) ekle
  - Session'a `notification_permission_status` ('default') ekle
  - _Requirements: 1.1, 2.1_


- [x] 1.2 Dashboard route'larını güncelle

  - `app/routes/driver.py` dashboard fonksiyonunu güncelle
  - `app/routes/admin.py` dashboard fonksiyonunu güncelle
  - Template'e `notification_permission_asked` ve `notification_permission_status` değerlerini gönder
  - _Requirements: 1.1, 2.1_



- [x] 1.3 API endpoint oluştur


  - `app/routes/api.py` dosyasına `/api/notification-permission` POST endpoint'i ekle
  - Session'ı güncelle (asked=True, status=request.status)
  - CSRF koruması ekle
  - Login required decorator ekle
  - Role validation ekle (sadece driver ve admin)
  - Hata yönetimi ve logging ekle
  - _Requirements: 1.3, 2.3, 3.1, 6.1_

- [x] 2. Frontend notification permission handler oluşturma


  - NotificationPermissionHandler sınıfı oluştur
  - Dialog HTML ve CSS tasarımı yap
  - Kullanıcı etkileşimlerini yönet
  - Mevcut PushNotificationManager ile entegre et
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 2.1, 2.2, 2.3, 2.4, 5.1, 5.2, 5.3, 5.4, 5.5, 6.2, 6.3, 6.4, 6.5_

- [x] 2.1 notification-permission.js dosyası oluştur


  - `app/static/js/notification-permission.js` dosyası oluştur
  - NotificationPermissionHandler sınıfını implement et
  - init() metodunu yaz (role, alreadyAsked, currentStatus parametreleri)
  - checkAndShowDialog() metodunu yaz
  - getBrowserPermissionStatus() metodunu yaz
  - showDialog() metodunu yaz
  - createDialog() metodunu yaz (HTML içeriği)
  - handleAllow() metodunu yaz (browser permission request)
  - handleLater() metodunu yaz
  - updateSessionStatus() metodunu yaz (API call)
  - closeDialog() metodunu yaz (animasyonlu)
  - Global instance oluştur
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 2.1, 2.2, 2.3, 2.4, 5.4, 5.5, 6.2, 6.3, 6.4_

- [x] 2.2 notification-permission.css dosyası oluştur


  - `app/static/css/notification-permission.css` dosyası oluştur
  - Dialog overlay styling (blur effect)
  - Dialog content styling (modern, rounded)
  - Icon styling (animated pulse)
  - Button styling (gradient, hover effects)
  - Animation keyframes (show/hide, pulse)
  - Mobile responsive styling
  - _Requirements: 5.1, 5.2, 5.3_

- [x] 2.3 PushNotificationManager ile entegrasyon

  - notification-permission.js içinde global instance'ını kullan
  - handleAllow() içinde pushNotifications.requestPermission() çağır
  - Permission sonucunu handle et
  - _Requirements: 1.3, 2.3_


- [x] 3. Template entegrasyonu



  - Driver ve admin dashboard template'lerine script ve CSS ekle
  - Conditional loading (sadece driver/admin için)
  - DOMContentLoaded event listener ekle
  - notificationPermissionHandler.init() çağır
  - _Requirements: 1.1, 2.1, 4.1, 4.2, 6.5_

- [x] 3.1 Driver dashboard template güncelle


  - `templates/driver/dashboard.html` dosyasını aç
  - extra_css block'una notification-permission.css ekle
  - extra_js block'una notification-permission.js ekle
  - DOMContentLoaded içinde init() çağır (role='driver')
  - Template değişkenlerini inject et (notification_permission_asked, notification_permission_status)
  - _Requirements: 1.1, 6.5_


- [x] 3.2 Admin dashboard template güncelle

  - `templates/admin/dashboard.html` dosyasını aç
  - extra_css block'una notification-permission.css ekle
  - extra_js block'una notification-permission.js ekle
  - DOMContentLoaded içinde init() çağır (role='admin')


  - Template değişkenlerini inject et (notification_permission_asked, notification_permission_status)
  - _Requirements: 2.1, 6.5_

- [x] 4. Hata yönetimi ve güvenlik



  - Browser compatibility kontrolü ekle
  - Permission request error handling
  - Network error handling
  - Session error handling
  - CSRF token validation

  - Input validation
  - Logging ekle
  - _Requirements: 6.1, 6.3_


- [x] 4.1 Frontend error handling



  - notification-permission.js içinde try-catch blokları ekle
  - Browser support kontrolü ('Notification' in window)

  - Permission request error handling
  - Network error handling (fetch failures)
  - Console logging ekle
  - _Requirements: 6.3_


- [x] 4.2 Backend error handling ve validation



  - API endpoint'e try-catch ekle
  - Role validation (sadece driver/admin)
  - Status validation (valid_statuses listesi)
  - Session error handling
  - Logging ekle (info, warning, error)
  - _Requirements: 6.1_




- [x] 5. Accessibility ve UX iyileştirmeleri



  - Keyboard navigation (Escape tuşu)
  - Screen reader support (ARIA attributes)
  - Focus management
  - Dialog timing (2 saniye delay)
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 6.4_




- [x] 5.1 Keyboard navigation ekle

  - Dialog'a keydown event listener ekle
  - Escape tuşu ile dialog'u kapat
  - Tab navigation desteği


  - _Requirements: 5.4, 5.5_

- [x] 5.2 ARIA attributes ekle


  - Dialog'a role="dialog" ekle

  - aria-labelledby ve aria-describedby ekle
  - Button'lara aria-label ekle
  - _Requirements: 5.1, 5.2, 5.3_



- [ ] 5.3 Focus management implement et
  - Dialog açıldığında ilk button'a focus
  - Dialog kapandığında önceki focus'a dön

  - _Requirements: 5.4, 5.5_

- [x] 5.4 Timing optimization

  - DOMContentLoaded sonrası 2 saniye delay ekle
  - Non-blocking implementation
  - _Requirements: 6.2, 6.4, 6.5_

- [ ] 6. Test yazma

  - Backend unit testleri
  - Frontend unit testleri
  - Integration testleri

  - _Requirements: Tüm requirements_

- [ ] 6.1 Backend unit testleri yaz

  - `tests/test_notification_permission.py` dosyası oluştur
  - API endpoint testleri (success, error, validation)
  - Session update testleri
  - Role validation testleri
  - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.2, 2.3_

- [ ] 6.2 Frontend unit testleri yaz

  - NotificationPermissionHandler testleri
  - Role checking testleri
  - Session flag checking testleri
  - Browser permission status testleri
  - Dialog creation testleri
  - User action handling testleri
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 2.1, 2.2, 2.3, 2.4_

- [ ] 6.3 Integration testleri yaz

  - Login flow testleri (driver, admin, guest)
  - Permission flow testleri (allow, later)
  - Second login testleri (no dialog)
  - _Requirements: 1.1, 2.1, 3.1, 3.2, 4.1, 4.2_
