# Design Document

## Overview

QR kod sistemini güncelleyerek, oluşturulan QR kodların tam URL içermesini ve misafirlerin QR kodu taradıklarında doğrudan buggy çağırma sayfasına yönlendirilmesini sağlayacağız. Mevcut sistem sadece lokasyon ID'si içeren QR kodlar üretiyor, bu da misafirlerin manuel olarak sayfaya gitmesini gerektiriyor.

## Architecture

### Current State
- QR kodlar JSON formatında: `{"hotel_id": X, "location_id": Y}`
- Misafirler QR kodu taradıktan sonra manuel olarak lokasyon seçmek zorunda
- `qr_code_data` alanı sadece ID içeriyor

### Target State
- QR kodlar tam URL içerecek: `http://domain.com/guest/call?location=123`
- Misafirler QR kodu taradığında otomatik olarak ilgili sayfaya yönlendirilecek
- Geriye dönük uyumluluk için eski `LOC` formatı da desteklenecek

## Components and Interfaces

### 1. QR Code Generation (Backend)

**File:** `app/routes/api.py` - `create_location()` fonksiyonu

**Changes:**
```python
# Eski format:
qr_code_data = f"LOC{user.hotel_id}{Location.query.filter_by(hotel_id=user.hotel_id).count() + 1:04d}"

# Yeni format:
from flask import request
base_url = request.host_url.rstrip('/')
qr_code_data = f"{base_url}/guest/call?location={location.id}"
```

**Rationale:** URL formatı kullanarak QR kod tarayıcılar otomatik olarak tarayıcıda açabilir.

### 2. QR Code Print Page (Frontend)

**File:** `templates/admin/qr_print.html` - `generateQRCode()` fonksiyonu

**Changes:**
```javascript
// Eski format:
const qrData = JSON.stringify({
    hotel_id: hotelId,
    location_id: location.id
});

// Yeni format:
const qrData = location.qr_code_data; // Direkt URL kullan
```

**Rationale:** Backend'den gelen URL'yi direkt kullanarak tutarlılık sağlanır.

### 3. QR Code Scanning (Guest Side)

**File:** `templates/guest/call_premium.html` - `processQRCode()` fonksiyonu

**Changes:**
- URL formatını algıla ve parse et
- Eski `LOC` formatını desteklemeye devam et
- URL'den lokasyon ID'sini çıkar ve sayfaya yönlendir

```javascript
function processQRCode(qrData) {
    // URL formatı mı kontrol et
    if (qrData.startsWith('http://') || qrData.startsWith('https://')) {
        // URL'yi direkt aç
        window.location.href = qrData;
    } 
    // Eski LOC formatı
    else if (qrData.startsWith('LOC')) {
        // Mevcut mantık
        fetch(`/api/locations`)
            .then(response => response.json())
            .then(data => {
                const location = data.locations.find(loc => loc.qr_code_data === qrData);
                if (location) {
                    window.location.href = `/guest/call?location=${location.id}`;
                }
            });
    }
    else {
        Utils.showToast('Geçersiz QR kod', 'error');
    }
}
```

### 4. Guest Call Page Enhancement

**File:** `templates/guest/call.html` veya `templates/guest/call_premium.html`

**Changes:**
- URL'den `location` query parametresini oku
- Eğer varsa, lokasyon dropdown'ını otomatik olarak seç
- Kullanıcı deneyimini iyileştir

```javascript
// Sayfa yüklendiğinde
const urlParams = new URLSearchParams(window.location.search);
const locationId = urlParams.get('location');
if (locationId) {
    document.getElementById('location-select').value = locationId;
    // Otomatik olarak form alanlarını göster
}
```

## Data Models

### Location Model

**File:** `app/models/location.py`

**No schema changes required** - `qr_code_data` alanı zaten String(500) ve URL'yi saklayabilir.

**Migration Strategy:**
- Yeni lokasyonlar otomatik olarak URL formatında oluşturulacak
- Mevcut lokasyonlar için migration script'i (opsiyonel):
  ```python
  # Migration script to update existing QR codes
  for location in Location.query.all():
      if location.qr_code_data.startswith('LOC'):
          base_url = "http://yourdomain.com"  # Config'den al
          location.qr_code_data = f"{base_url}/guest/call?location={location.id}"
  db.session.commit()
  ```

## Error Handling

### 1. Invalid QR Code Format
- **Scenario:** Misafir geçersiz QR kod taradı
- **Handling:** Toast mesajı göster: "Geçersiz QR kod"

### 2. Location Not Found
- **Scenario:** URL'deki lokasyon ID geçersiz
- **Handling:** Hata sayfası göster veya lokasyon seçim sayfasına yönlendir

### 3. Network Error
- **Scenario:** API çağrısı başarısız
- **Handling:** Retry mekanizması veya hata mesajı

## Testing Strategy

### Unit Tests
1. QR kod URL formatının doğru oluşturulduğunu test et
2. URL parsing fonksiyonunu test et
3. Geriye dönük uyumluluk testleri (eski LOC formatı)

### Integration Tests
1. Lokasyon oluşturma ve QR kod üretimi end-to-end test
2. QR kod tarama ve yönlendirme testi
3. Guest call sayfasında otomatik lokasyon seçimi testi

### Manual Testing
1. Admin: Lokasyon oluştur → QR kod yazdır → QR kodu kontrol et
2. Guest: QR kodu tara → Otomatik yönlendirmeyi doğrula → Buggy çağır
3. Eski QR kodlarla test (geriye dönük uyumluluk)

## Configuration

### Base URL Configuration

**File:** `app/config.py`

```python
class Config:
    # ...
    BASE_URL = os.environ.get('BASE_URL', 'http://localhost:5000')
```

**Usage:**
```python
from app.config import Config
qr_code_data = f"{Config.BASE_URL}/guest/call?location={location.id}"
```

## Security Considerations

1. **URL Validation:** QR kod tarama sırasında URL'nin kendi domain'imize ait olduğunu doğrula
2. **Location ID Validation:** URL'deki lokasyon ID'sinin geçerli olduğunu kontrol et
3. **HTTPS:** Production'da HTTPS kullan

## Performance Considerations

- QR kod üretimi zaten client-side (qrcodejs kütüphanesi)
- URL formatı JSON'dan daha kısa ve okunabilir
- Geriye dönük uyumluluk için minimal overhead

## Rollout Plan

### Phase 1: Backend Update
1. `create_location()` fonksiyonunu güncelle
2. URL formatında QR kod üret
3. Test et

### Phase 2: Frontend Update
1. QR print sayfasını güncelle
2. QR tarama mantığını güncelle
3. Guest call sayfasını güncelle

### Phase 3: Migration (Optional)
1. Mevcut lokasyonların QR kodlarını güncelle
2. Eski QR kodları yeniden yazdır

### Phase 4: Validation
1. Tüm akışları test et
2. Geriye dönük uyumluluğu doğrula
3. Production'a deploy et
