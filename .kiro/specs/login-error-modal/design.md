# Design Document

## Overview

Login sayfasında hatalı giriş durumlarında kullanıcıya modal dialog ile bildirim gösterilecektir. Mevcut `BuggyModal` sistemi kullanılacak ve `BuggyCall.Utils` namespace'ine entegre edilecektir. Toast bildirimleri yerine modal kullanılarak kullanıcı deneyimi iyileştirilecektir.

## Architecture

### Mevcut Yapı

Projede zaten çalışan bir modal sistemi mevcut:
- `app/static/js/modal.js` - BuggyModal sistemi
- `app/static/js/common.js` - BuggyCall.Utils namespace
- `templates/base.html` - Global template

### Değişiklikler

1. **Login sayfası** (`templates/auth/login.html`):
   - Toast yerine modal kullanımına geçiş
   - `BuggyCall.Utils.showToast()` → `BuggyCall.Utils.showError()` veya `BuggyModal.error()`

2. **Modal sistemi** (zaten mevcut, değişiklik gerekmez):
   - `BuggyModal.error()` fonksiyonu kullanılacak
   - Otomatik olarak hata ikonu ve kırmızı tema gösterir
   - ESC tuşu ve overlay tıklama ile kapatılabilir

## Components and Interfaces

### BuggyModal API (Mevcut)

```javascript
// Hata modalı gösterme
BuggyModal.error(message, title = 'Hata!')
  .then(() => {
    // Modal kapatıldıktan sonra
  });

// Alternatif kullanım
BuggyCall.Utils.showError(message, title)
```

### Login Form Handler (Güncellenecek)

**Mevcut Kod:**
```javascript
if (response.ok && data.success) {
    // Success handling
} else {
    BuggyCall.Utils.showToast(data.error || data.message || 'Giriş başarısız', 'danger');
}
```

**Yeni Kod:**
```javascript
if (response.ok && data.success) {
    // Success handling
} else {
    await BuggyCall.Utils.showError(
        data.error || data.message || 'Kullanıcı adı veya şifre hatalı',
        'Giriş Başarısız'
    );
}
```

## Data Models

Veri modeli değişikliği yok. Sadece UI gösterim şekli değişiyor.

## Error Handling

### Hata Senaryoları

1. **Yanlış kullanıcı adı/şifre**:
   - Modal başlık: "Giriş Başarısız"
   - Modal mesaj: Backend'den gelen hata mesajı veya "Kullanıcı adı veya şifre hatalı"
   - Tip: `danger` (kırmızı tema)

2. **Network hatası**:
   - Modal başlık: "Bağlantı Hatası"
   - Modal mesaj: "Sunucuya bağlanılamadı. Lütfen internet bağlantınızı kontrol edin."
   - Tip: `danger`

3. **Beklenmeyen hata**:
   - Modal başlık: "Hata"
   - Modal mesaj: "Bir hata oluştu. Lütfen tekrar deneyin."
   - Tip: `danger`

### Modal Kapatma Davranışı

- **Tamam butonu**: Modalı kapatır, kullanıcı login formuna geri döner
- **ESC tuşu**: Modalı kapatır
- **Overlay tıklama**: Modalı kapatır
- **X butonu**: Modalı kapatır

## Testing Strategy

### Manuel Test Senaryoları

1. **Yanlış şifre testi**:
   - Doğru kullanıcı adı, yanlış şifre gir
   - Modal açılmalı
   - Hata mesajı görünmeli
   - Modal kapatılabilmeli

2. **Yanlış kullanıcı adı testi**:
   - Yanlış kullanıcı adı gir
   - Modal açılmalı
   - Hata mesajı görünmeli

3. **Boş form testi**:
   - Boş form gönder
   - HTML5 validation çalışmalı (modal açılmamalı)

4. **Modal kapatma testleri**:
   - Tamam butonuna tıkla → Modal kapanmalı
   - ESC tuşuna bas → Modal kapanmalı
   - Overlay'e tıkla → Modal kapanmalı
   - X butonuna tıkla → Modal kapanmalı

5. **Animasyon testi**:
   - Modal açılırken fade-in animasyonu olmalı
   - Modal kapanırken fade-out animasyonu olmalı

### Browser Uyumluluğu

- Chrome/Edge (modern)
- Firefox
- Safari
- Mobile browsers (iOS Safari, Chrome Mobile)

## Implementation Notes

### Minimal Değişiklik

Sadece `templates/auth/login.html` dosyasında değişiklik yapılacak:
- `showToast` çağrıları `showError` ile değiştirilecek
- Catch bloğunda da modal kullanılacak

### Mevcut Sistemle Uyumluluk

- `BuggyModal` zaten yüklü ve çalışıyor
- `BuggyCall.Utils.showError()` zaten `BuggyModal.error()` çağırıyor
- CSS stilleri zaten tanımlı (`app/static/css/modal.css`)
- Hiçbir yeni bağımlılık eklenmeyecek

### Performans

- Modal lazy load değil, sayfa yüklendiğinde hazır
- Animasyonlar CSS transition ile (60fps)
- Overlay backdrop-filter kullanmıyor (performans için)

## Migration Plan

1. Login sayfasındaki toast çağrılarını modal ile değiştir
2. Hata mesajlarını test et
3. Farklı tarayıcılarda test et
4. Production'a deploy et

Rollback: Tek dosya değişikliği olduğu için kolay geri alınabilir.
