# Implementation Plan

- [x] 1. Backend: QR kod üretimini URL formatına güncelle





  - `app/routes/api.py` dosyasındaki `create_location()` fonksiyonunu güncelle
  - QR kod verisini `LOC` formatı yerine tam URL formatında oluştur (örnek: `http://domain.com/guest/call?location=123`)
  - Base URL'yi config'den veya request'ten al
  - _Requirements: 1.1, 1.3_
- [x] 2. Backend: Config'e BASE_URL ekle







- [ ] 2. Backend: Config'e BASE_URL ekle

  - `app/config.py` dosyasına `BASE_URL` konfigürasyonu ekle
  - Environment variable'dan oku, yoksa localhost kullan
  - _Requirements: 1.1_

- [x] 3. Frontend: QR kod yazdırma sayfasını güncelle



  - `templates/admin/qr_print.html` dosyasındaki `generateQRCode()` fonksiyonunu güncelle
  - JSON formatı yerine backend'den gelen URL'yi direkt kullan
  - QR kod üretimini test et
  - _Requirements: 1.4_

- [x] 4. Frontend: QR kod tarama mantığını güncelle





  - `templates/guest/call_premium.html` dosyasındaki `processQRCode()` fonksiyonunu güncelle
  - URL formatını algıla ve direkt yönlendir
  - Eski `LOC` formatını desteklemeye devam et (geriye dönük uyumluluk)
  - Geçersiz format için hata mesajı göster
  - _Requirements: 2.1, 2.4, 3.1, 3.2, 3.3, 3.4_
-

- [x] 5. Frontend: Guest call sayfasında otomatik lokasyon seçimi




  - `templates/guest/call_premium.html` veya `templates/guest/call.html` dosyasını güncelle
  - URL'den `location` query parametresini oku
  - Eğer varsa, lokasyon dropdown'ını otomatik olarak seç
  - Kullanıcı deneyimini iyileştir
  - _Requirements: 2.2, 2.3_


- [x] 6. Migration: Mevcut lokasyonların QR kodlarını güncelle




  - Mevcut lokasyonların `qr_code_data` alanını yeni URL formatına güncelle
  - Migration script'i oluştur
  - Sadece `LOC` formatındaki QR kodları güncelle
  - _Requirements: 3.1_

- [x] 7. Test: End-to-end akışı test et




  - Admin: Lokasyon oluştur → QR kod yazdır → QR kodu kontrol et
  - Guest: QR kodu tara → Otomatik yönlendirmeyi doğrula → Buggy çağır
  - Eski QR kodlarla test (geriye dönük uyumluluk)
  - _Requirements: 1.1, 1.2, 2.1, 2.2, 3.1, 3.2, 3.3, 3.4_
