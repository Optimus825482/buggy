# Implementation Plan

- [x] 1. Backend WebSocket emit fonksiyonu oluştur


  - `app/services/buggy_service.py` dosyasına `emit_buggy_status_update()` fonksiyonunu ekle
  - Buggy bilgilerini, aktif session'ı ve driver bilgisini sorgula
  - Status'u belirle (offline/available/busy)
  - Socket.IO ile `hotel_{id}_admins` room'una emit et
  - _Requirements: 1.1, 1.2, 1.3_

- [x] 2. Backend trigger noktalarına emit çağrıları ekle


  - [x] 2.1 Driver session start endpoint'ine emit ekle

    - `app/routes/driver.py` içindeki `start_session` fonksiyonuna emit çağrısı ekle
    - Session başarıyla oluşturulduktan sonra çağır
    - _Requirements: 1.2, 3.1_

  - [x] 2.2 Driver session end endpoint'ine emit ekle

    - `app/routes/driver.py` içindeki `end_session` fonksiyonuna emit çağrısı ekle
    - Session sonlandırıldıktan sonra çağır
    - _Requirements: 1.2, 3.2_

  - [x] 2.3 Request accept endpoint'ine emit ekle


    - `app/routes/driver.py` içindeki `accept_request` fonksiyonuna emit çağrısı ekle
    - Request kabul edildikten sonra çağır
    - _Requirements: 1.2, 2.2_

  - [x] 2.4 Request complete endpoint'ine emit ekle


    - `app/routes/driver.py` içindeki `complete_request` fonksiyonuna emit çağrısı ekle
    - Request tamamlandıktan sonra çağır
    - _Requirements: 1.2, 2.1_

- [x] 3. Frontend WebSocket listener ve DOM update implementasyonu

  - [x] 3.1 Connection status indicator ekle


    - `app/static/js/admin.js` dosyasına bağlantı durumu göstergesi ekle
    - Sayfanın sağ üst köşesine yeşil/sarı/kırmızı nokta ekle
    - Connect/disconnect/reconnecting event'lerini dinle
    - _Requirements: 4.1, 4.2, 4.3_

  - [x] 3.2 Buggy status update listener ekle

    - `socket.on('buggy_status_update')` event listener'ı ekle
    - Gelen data'yı console'a logla
    - `updateBuggyStatusRow()` fonksiyonunu çağır
    - _Requirements: 1.3, 1.4_


  - [x] 3.3 DOM update fonksiyonu implementasyonu

    - `updateBuggyStatusRow(data)` fonksiyonunu yaz
    - Buggy row'unu `data-buggy-id` ile bul
    - Status badge'ini güncelle (Çevrimiçi/Meşgul/Çevrimdışı)
    - Driver name'i güncelle
    - CSS transition ekle (smooth animation)
    - Row bulunamazsa tüm listeyi reload et
    - _Requirements: 1.4, 2.1, 2.2, 2.3, 2.5, 3.3, 3.4_


  - [x] 3.4 Throttling mekanizması ekle

    - Update throttle Map'i oluştur
    - Her buggy için max 100ms'de bir güncelleme yap (10 update/saniye)
    - Throttle map'i periyodik olarak temizle

    - _Requirements: 5.2_

  - [x] 3.5 Connection event handler'ları ekle

    - `socket.on('connect')` - Yeşil gösterge + bildirim
    - `socket.on('disconnect')` - Kırmızı gösterge + bildirim
    - `socket.on('reconnecting')` - Sarı gösterge
    - _Requirements: 1.5, 4.1, 4.2, 4.3, 4.4_

- [x] 4. Admin dashboard HTML'e data attribute ekle


  - `templates/admin/dashboard.html` içindeki buggy listesi table row'larına `data-buggy-id` attribute'u ekle
  - Status badge'lere class ekle (kolay seçim için)
  - Driver name cell'lerine class ekle
  - _Requirements: 1.4, 2.5_

- [x] 5. Page lifecycle yönetimi

  - [x] 5.1 Page unload event handler ekle


    - WebSocket bağlantısını temiz kapat
    - Event listener'ları temizle
    - Throttle map'i temizle
    - _Requirements: 5.3_

  - [x] 5.2 Page visibility API entegrasyonu

    - Page arka plana gittiğinde DOM update'leri ertele
    - Page ön plana geldiğinde ertelenen update'leri uygula
    - WebSocket bağlantısını aktif tut
    - _Requirements: 5.4, 5.5_

- [x] 6. Test implementasyonu


  - [x] 6.1 Backend unit testleri yaz


    - `test_emit_buggy_status_update()` - Doğru data format
    - `test_emit_with_active_session()` - Status = available/busy
    - `test_emit_without_session()` - Status = offline
    - `test_emit_invalid_buggy()` - Graceful failure
    - _Requirements: 1.1, 1.2, 1.3_
