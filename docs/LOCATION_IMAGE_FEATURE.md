# Lokasyon Görsel Özelliği

## Genel Bakış
Lokasyonlara görsel ekleme özelliği eklendi. Admin panelinde lokasyon oluştururken veya düzenlerken görsel yüklenebilir. Bu görseller misafir tarafında lokasyon seçiminde gösterilir.

## Değişiklikler

### 1. Database (Veritabanı)
- **Yeni Kolon**: `locations` tablosuna `location_image` (TEXT) kolonu eklendi
- Base64 encoded görsel veya dosya yolu saklar
- NULL değer alabilir (opsiyonel)

### 2. Model (app/models/location.py)
```python
location_image = Column(Text)  # Base64 encoded location image or file path
```

### 3. Schema (app/schemas/location_schema.py)
- `LocationSchema`: `location_image` field eklendi
- `LocationUpdateSchema`: `location_image` field eklendi (opsiyonel)

### 4. API Endpoints (app/routes/api.py)

#### POST /api/locations
- Yeni lokasyon oluştururken `location_image` parametresi kabul eder
- Base64 encoded görsel string olarak gönderilmeli

#### PUT /api/locations/<id>
- Lokasyon güncellerken `location_image` parametresi kabul eder
- `null` göndererek görsel kaldırılabilir

### 5. Admin Panel (templates/admin/locations.html)

#### Yeni Lokasyon Ekleme
- Dosya seçme input'u eklendi
- Görsel önizleme özelliği
- Max 5MB boyut kontrolü
- Base64'e otomatik dönüştürme

#### Lokasyon Düzenleme
- Mevcut görseli gösterme
- Yeni görsel yükleme
- Görseli kaldırma butonu
- Görsel önizleme

### 6. Misafir Arayüzü (templates/driver/select_location.html)
- Lokasyon kartlarında görsel gösterimi
- Görsel yoksa icon gösterimi (fallback)
- Responsive tasarım

### 7. Admin Panel - Lokasyon Listesi (templates/admin/locations.html)
- Tablo görünümünde görsel kolonu eklendi
- Her lokasyon için 60x60px görsel önizlemesi
- Görsel yoksa gradient background ile icon gösterimi
- Responsive tablo tasarımı

### 8. Sürücü Dashboard - Görev Tamamlama (app/static/js/driver.js)
- Görev tamamlandığında lokasyon seçim modalı
- Lokasyon kartlarında görsel gösterimi
- Görsel yoksa icon gösterimi (fallback)
- Hover efektleri ve animasyonlar
- API'ye `current_location_id` parametresi gönderimi

## Kullanım

### Admin Tarafı

1. **Yeni Lokasyon Eklerken**:
   - "Yeni Lokasyon" butonuna tıkla
   - Lokasyon bilgilerini gir
   - "Lokasyon Görseli" alanından görsel seç
   - Önizleme otomatik gösterilir
   - "Kaydet" butonuna tıkla

2. **Lokasyon Düzenlerken**:
   - Lokasyon satırında "Düzenle" butonuna tıkla
   - Mevcut görsel varsa gösterilir
   - Yeni görsel yüklemek için dosya seç
   - Görseli kaldırmak için "Görseli Kaldır" butonuna tıkla
   - "Güncelle" butonuna tıkla

### Misafir Tarafı

1. **QR Kod Okutma - Buggy Çağırma Sayfası**:
   - Misafir QR kodu okuttuğunda call_premium.html sayfası açılır
   - Lokasyon bilgisi üst kısımda gösterilir
   - Lokasyon görseli varsa: 48x48px boyutunda görsel gösterilir
   - Lokasyon görseli yoksa: Icon gösterilir
   - Görsel yuvarlak köşeli, border'lı ve güzel bir tasarımda

### Sürücü Tarafı

1. **İlk Giriş - Lokasyon Seçimi**:
   - Sürücü ilk giriş yaptığında lokasyon seçer
   - Her lokasyon kartında görsel gösterilir

2. **Görev Tamamlama - Lokasyon Güncelleme**:
   - Misafiri bıraktıktan sonra "Tamamla" butonuna tıkla
   - Lokasyon seçim modalı açılır
   - Şu anki konumunu seç
   - Görsel varsa lokasyon görseli, yoksa icon gösterilir
   - Seçilen lokasyon API'ye gönderilir

### Admin Tarafı

- **Lokasyon Listesi**:
  - Her lokasyon için görsel önizlemesi gösterilir
  - Görsel yoksa gradient background ile icon
  - 60x60px boyutunda thumbnail

## Teknik Detaylar

### Görsel Formatı
- Base64 encoded string
- Format: `data:image/png;base64,{base64_string}`
- Desteklenen formatlar: PNG, JPEG, WebP
- Max boyut: 5MB

### Güvenlik
- Dosya boyutu kontrolü (client-side)
- Base64 encoding ile güvenli saklama
- XSS koruması (escapeHtml kullanımı)

### Performans
- Görseller base64 olarak saklanır (database'de)
- Lazy loading yok (tüm görseller yüklenir)
- Optimize edilmiş görsel boyutları önerilir

## Test Senaryoları

### Admin Panel
1. ✅ Yeni lokasyon oluşturma (görselli)
2. ✅ Yeni lokasyon oluşturma (görselsiz)
3. ✅ Lokasyon güncelleme (görsel ekleme)
4. ✅ Lokasyon güncelleme (görsel değiştirme)
5. ✅ Lokasyon güncelleme (görsel kaldırma)
6. ✅ Lokasyon listesinde görsel gösterimi
7. ✅ Lokasyon listesinde fallback icon gösterimi

### Sürücü Dashboard
8. ✅ İlk giriş - lokasyon seçiminde görsel gösterimi
9. ✅ Görev tamamlama - lokasyon seçim modalı açılması
10. ✅ Görev tamamlama - lokasyon seçiminde görsel gösterimi
11. ✅ Görev tamamlama - lokasyon seçiminde fallback icon
12. ✅ Görev tamamlama - API'ye current_location_id gönderimi

### Misafir Arayüzü
13. ✅ QR kod okutma - lokasyon seçiminde görsel gösterimi
14. ✅ QR kod okutma - fallback icon gösterimi

## Gelecek İyileştirmeler

- [ ] Görsel optimizasyonu (resize, compress)
- [ ] Dosya sistemi storage (base64 yerine)
- [ ] CDN entegrasyonu
- [ ] Lazy loading
- [ ] Görsel crop/edit özelliği
- [ ] Multiple görsel desteği
