# Audit Trail Sistemi - İzlenen İşlemler Raporu

## 📋 Genel Bakış

Audit Trail sistemi, sistemdeki tüm kritik işlemleri otomatik olarak kaydeder ve izler. Her kayıt şunları içerir:
- Kullanıcı bilgisi (kim yaptı)
- İşlem tipi (ne yapıldı)
- Varlık tipi ve ID (hangi kayıt)
- Eski ve yeni değerler (ne değişti)
- IP adresi ve User Agent
- Zaman damgası

---

## 🔐 1. Kimlik Doğrulama İşlemleri (AuthService)

### ✅ İzlenen İşlemler:

#### 1.1 Giriş İşlemleri
- **Başarılı Giriş** (`login_success`)
  - Kullanıcı ID
  - Hotel ID
  - IP adresi
  - User agent
  
- **Başarısız Giriş** (`login_failed`)
  - Kullanıcı adı (varsa)
  - IP adresi
  - Başarısızlık nedeni

#### 1.2 Çıkış İşlemleri
- **Çıkış** (`logout`)
  - Kullanıcı ID
  - Hotel ID
  - Oturum süresi

#### 1.3 Şifre İşlemleri
- **Şifre Değişikliği** (`password_changed`)
  - Kullanıcı ID
  - Değişiklik zamanı

#### 1.4 Kullanıcı Yönetimi
- **Kullanıcı Oluşturma** (`create`)
  - Yeni kullanıcı bilgileri
  - Rol (admin/driver)
  - Hotel ID

- **Kullanıcı Güncelleme** (`update`)
  - Eski değerler
  - Yeni değerler
  - Değişen alanlar

---

## 📍 2. Lokasyon İşlemleri (LocationService)

### ✅ İzlenen İşlemler:

#### 2.1 CRUD İşlemleri
- **Lokasyon Oluşturma** (`create`)
  - Lokasyon adı
  - QR kod bilgisi
  - Koordinatlar
  - Hotel ID

- **Lokasyon Güncelleme** (`update`)
  - Eski değerler
  - Yeni değerler
  - Değişen alanlar

- **Lokasyon Silme** (`delete`)
  - Silinen lokasyon bilgileri
  - Silme nedeni

#### 2.2 QR Kod İşlemleri
- **QR Kod Yenileme** (`qr_code_regenerated`)
  - Lokasyon ID
  - Eski QR kod
  - Yeni QR kod

---

## 🚗 3. Buggy İşlemleri (BuggyService)

### ✅ İzlenen İşlemler:

#### 3.1 CRUD İşlemleri
- **Buggy Oluşturma** (`create`)
  - Buggy kodu
  - Model bilgisi
  - Plaka
  - Hotel ID

- **Buggy Güncelleme** (`update`)
  - Eski değerler
  - Yeni değerler
  - Değişen alanlar

- **Buggy Silme** (`delete`)
  - Silinen buggy bilgileri
  - İlişkili talepler

#### 3.2 Durum Değişiklikleri
- **Durum Değişikliği** (`status_changed`)
  - Eski durum (available/busy/offline)
  - Yeni durum
  - Değişiklik nedeni
  - Sürücü bilgisi

---

## 📞 4. Talep İşlemleri (RequestService)

### ✅ İzlenen İşlemler:

#### 4.1 Talep Yaşam Döngüsü
- **Talep Oluşturma** (`create`)
  - Misafir bilgileri
  - Lokasyon
  - Oda numarası
  - Notlar

- **Talep Kabul Etme** (`update` - acceptance)
  - Kabul eden sürücü
  - Atanan buggy
  - Kabul zamanı
  - Yanıt süresi

- **Talep Tamamlama** (`update` - completion)
  - Tamamlama zamanı
  - Toplam süre
  - Performans metrikleri

- **Talep İptali** (`update` - cancellation)
  - İptal eden (driver/guest/admin)
  - İptal nedeni
  - İptal zamanı

---

## 📊 5. Kayıt Edilen Veri Tipleri

### Entity Types (Varlık Tipleri):
- `user` - Kullanıcı işlemleri
- `location` - Lokasyon işlemleri
- `buggy` - Buggy işlemleri
- `request` - Talep işlemleri

### Action Types (İşlem Tipleri):
- `create` - Oluşturma
- `update` - Güncelleme
- `delete` - Silme
- `login_success` - Başarılı giriş
- `login_failed` - Başarısız giriş
- `logout` - Çıkış
- `password_changed` - Şifre değişikliği
- `status_changed` - Durum değişikliği
- `qr_code_regenerated` - QR kod yenileme

---

## 🔍 6. Audit Trail Sorgulama

### Filtreleme Seçenekleri:
- **Kullanıcıya göre** - Belirli bir kullanıcının tüm işlemleri
- **İşlem tipine göre** - Sadece create, update, delete vb.
- **Varlık tipine göre** - Sadece buggy, location, request vb.
- **Tarih aralığına göre** - Belirli bir zaman dilimi
- **Hotel'e göre** - Belirli bir otel

### Sayfalama:
- Varsayılan: 50 kayıt/sayfa
- Özelleştirilebilir sayfa boyutu
- Toplam kayıt sayısı

---

## 📈 7. Audit Trail Endpoint'leri

### API Endpoint'leri:
```
GET /api/audit-trail
- Audit kayıtlarını listeler
- Filtreleme ve sayfalama destekler

Query Parameters:
- user_id: Kullanıcı ID
- action: İşlem tipi
- entity_type: Varlık tipi
- date_from: Başlangıç tarihi
- date_to: Bitiş tarihi
- page: Sayfa numarası
- per_page: Sayfa başına kayıt
```

---

## ⚠️ 8. İzlenmeyen İşlemler

Şu anda audit trail sisteminde **İZLENMEYEN** işlemler:

### 8.1 Raporlama İşlemleri
- Rapor görüntüleme
- Excel/PDF export
- Dashboard istatistikleri

### 8.2 Oturum İşlemleri
- Session oluşturma
- Session yenileme
- Session silme

### 8.3 Push Notification İşlemleri
- Bildirim gönderme
- Subscription oluşturma
- Subscription silme

### 8.4 Sistem İşlemleri
- Health check
- Setup wizard
- **System Reset** ⚠️

### 8.5 Okuma İşlemleri
- Liste görüntüleme (GET requests)
- Detay görüntüleme
- Arama işlemleri

---

## 💡 9. Öneriler

### Eklenmesi Önerilen Audit Trail Kayıtları:

#### 9.1 Yüksek Öncelikli
1. **System Reset İşlemi**
   - Kim resetledi
   - Ne kadar veri silindi
   - Reset zamanı
   
2. **Toplu Silme İşlemleri**
   - Toplu buggy silme
   - Toplu lokasyon silme
   
3. **Kritik Ayar Değişiklikleri**
   - Hotel bilgileri güncelleme
   - Sistem ayarları değişikliği

#### 9.2 Orta Öncelikli
1. **Rapor Export İşlemleri**
   - Hangi rapor export edildi
   - Kim export etti
   - Tarih aralığı

2. **Push Notification İşlemleri**
   - Toplu bildirim gönderme
   - Bildirim ayarları değişikliği

#### 9.3 Düşük Öncelikli
1. **Okuma İşlemleri** (opsiyonel)
   - Hassas veri görüntüleme
   - Toplu veri export
   - Kritik rapor görüntüleme

---

## 🛡️ 10. Güvenlik Özellikleri

### Mevcut Güvenlik:
- ✅ IP adresi kaydı
- ✅ User agent kaydı
- ✅ Zaman damgası
- ✅ Kullanıcı kimliği
- ✅ Eski/yeni değer karşılaştırması

### Eksik Güvenlik:
- ❌ Audit log'ların değiştirilmesini engelleme
- ❌ Audit log silme yetkisi kontrolü
- ❌ Şüpheli aktivite tespiti
- ❌ Otomatik uyarı sistemi

---

## 📝 11. Kullanım Örnekleri

### Örnek 1: Bir lokasyonun kim tarafından silindiğini bulma
```sql
SELECT * FROM audit_trail 
WHERE entity_type = 'location' 
  AND entity_id = 123 
  AND action = 'delete'
```

### Örnek 2: Başarısız giriş denemelerini listeleme
```sql
SELECT * FROM audit_trail 
WHERE action = 'login_failed' 
  AND created_at > NOW() - INTERVAL 1 DAY
```

### Örnek 3: Bir kullanıcının tüm işlemlerini görme
```sql
SELECT * FROM audit_trail 
WHERE user_id = 5 
ORDER BY created_at DESC
```

---

## 🎯 Sonuç

Audit Trail sistemi şu anda **temel CRUD işlemlerini** ve **kimlik doğrulama işlemlerini** başarıyla izliyor. 

**Kapsam:**
- ✅ Kullanıcı işlemleri (login, logout, create, update)
- ✅ Lokasyon işlemleri (create, update, delete, QR regenerate)
- ✅ Buggy işlemleri (create, update, delete, status change)
- ✅ Talep işlemleri (create, accept, complete, cancel)

**Eksikler:**
- ❌ System reset işlemi
- ❌ Toplu işlemler
- ❌ Rapor export işlemleri
- ❌ Push notification işlemleri
- ❌ Kritik ayar değişiklikleri

**Öneri:** Yukarıda belirtilen "Yüksek Öncelikli" işlemlerin audit trail'e eklenmesi önerilir.
