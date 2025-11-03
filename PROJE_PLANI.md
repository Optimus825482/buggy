# BUGGY CALL - Otel İçi Ulaşım Yönetim Sistemi
## Detaylı Proje Planı ve Analiz Dokümanı

---

## 📋 İçindekiler
1. [Proje Özeti](#proje-özeti)
2. [Sistem Gereksinimleri](#sistem-gereksinimleri)
3. [Teknik Mimari](#teknik-mimari)
4. [Veritabanı Yapısı](#veritabanı-yapısı)
5. [Kullanıcı Rolleri ve Yetkiler](#kullanıcı-rolleri-ve-yetkiler)
6. [Özellikler ve Fonksiyonlar](#özellikler-ve-fonksiyonlar)
7. [Geliştirme Aşamaları](#geliştirme-aşamaları)
8. [Teknoloji Stack](#teknoloji-stack)
9. [Güvenlik ve Performans](#güvenlik-ve-performans)
10. [Test Stratejisi](#test-stratejisi)

---

## 1. Proje Özeti

### 1.1 Proje Tanımı
Buggy Call, otel içi ulaşım hizmetlerini dijitalleştirir ve optimize eden bir Progressive Web App (PWA) çözümüdür. Misafirler QR kod okutarak kolayca buggy talep edebilir, buggy sürücüleri talepleri yönetebilir ve sistem yöneticileri tüm operasyonu gerçek zamanlı izleyebilir.

### 1.2 Hedef Kullanıcılar
- **Otel Misafirleri**: QR kod ile hızlı buggy çağırma
- **Buggy Sürücüleri**: Talep yönetimi ve lokasyon bildirimi
- **Sistem Yöneticisi**: Operasyonel kontrol ve raporlama
- **Otel Yönetimi**: Performans analizi ve karar desteği

### 1.3 Temel Değer Önerileri
- ✅ Hızlı ve kolay erişim (QR kod tabanlı)
- ✅ Gerçek zamanlı koordinasyon
- ✅ Tam izlenebilirlik (Audit Trail)
- ✅ Mobil-first tasarım
- ✅ Multi-platform destek (iOS, Android, Desktop)

---

## 2. Sistem Gereksinimleri

### 2.1 Fonksiyonel Gereksinimler

#### 2.1.1 İlk Kurulum ve Yapılandırma
- Otel bilgileri girişi (isim, adres, iletişim)
- Sistem yöneticisi hesabı oluşturma
- Varsayılan ayarların yapılandırılması

#### 2.1.2 Lokasyon Yönetimi
- Lokasyon tanımlama (isim, açıklama, koordinat)
- Her lokasyon için benzersiz QR kod üretimi
- QR kod yazdırma/indirme özelliği
- Lokasyon düzenleme ve silme
- Aktif/pasif lokasyon durumu

#### 2.1.3 Buggy Yönetimi
- Buggy tanımlama (isim, kapasite, plaka)
- Buggy sürücüsü için kullanıcı adı ve şifre oluşturma
- Buggy aktif/inaktif durumu yönetimi
- Buggy bilgilerini güncelleme

#### 2.1.4 Buggy Talep Süreci (Misafir)
- QR kod okutma ile sistem erişimi
- Lokasyon otomatik tanıma
- Oda numarası girişi (opsiyonel)
- Buggy çağrısı oluşturma
- Talep durumu takibi
- Bildirim alma (talep kabul edildiğinde)

#### 2.1.5 Buggy Talep Yönetimi (Sürücü)
- Gelen talepleri görüntüleme
- Push bildirim alma
- Talep kabul etme
- Müsaitlik durumu güncelleme
- Lokasyon bildirimi
- Tamamlanan talepleri işaretleme
- Diğer buggy'lerin durumunu görme

#### 2.1.6 Admin Kontrol Paneli
- Gerçek zamanlı dashboard
- Tüm buggy'lerin lokasyonları (harita görünümü)
- Aktif/bekleyen talepler listesi
- Buggy sürücüsü oturum yönetimi
- Kapsamlı raporlama
- Audit trail görüntüleme

### 2.2 Teknik Gereksinimler

#### 2.2.1 Performans
- Sayfa yükleme süresi < 2 saniye
- Gerçek zamanlı güncelleme gecikme < 1 saniye
- 100+ eşzamanlı kullanıcı desteği
- QR kod okuma süresi < 500ms

#### 2.2.2 Güvenlik
- HTTPS zorunluluğu
- Şifreli veri iletimi (SSL/TLS)
- SQL Injection koruması
- XSS (Cross-Site Scripting) koruması
- CSRF token kullanımı
- Session yönetimi ve timeout
- Rate limiting (DDoS koruması)

#### 2.2.3 Uyumluluk
- Responsive tasarım (mobile-first)
- iOS Safari, Android Chrome uyumluluğu
- Desktop tarayıcıları (Chrome, Firefox, Edge)
- PWA standartlarına uygunluk
- Offline-first yaklaşım (sınırlı)

#### 2.2.4 Erişilebilirlik
- WCAG 2.1 AA seviyesi uyumluluk
- Çoklu dil desteği hazırlığı
- Büyük font seçenekleri
- Yüksek kontrast mod

---

## 3. Teknik Mimari

### 3.1 Sistem Mimarisi

```
┌─────────────────────────────────────────────────────┐
│                   CLIENT LAYER                       │
├─────────────────────────────────────────────────────┤
│  PWA (Progressive Web App)                           │
│  - Service Worker                                    │
│  - IndexedDB (Offline Cache)                         │
│  - Web Push Notifications                            │
│  - QR Code Scanner                                   │
└─────────────────────────────────────────────────────┘
                        ↕ HTTPS
┌─────────────────────────────────────────────────────┐
│                APPLICATION LAYER                     │
├─────────────────────────────────────────────────────┤
│  Flask Web Framework                                 │
│  - RESTful API Endpoints                             │
│  - WebSocket (Socket.IO)                             │
│  - JWT Authentication                                │
│  - Session Management                                │
└─────────────────────────────────────────────────────┘
                        ↕
┌─────────────────────────────────────────────────────┐
│                 BUSINESS LOGIC LAYER                 │
├─────────────────────────────────────────────────────┤
│  - User Management                                   │
│  - Location Management                               │
│  - Buggy Management                                  │
│  - Request Processing                                │
│  - Notification Service                              │
│  - Audit Trail Logger                                │
└─────────────────────────────────────────────────────┘
                        ↕
┌─────────────────────────────────────────────────────┐
│                   DATA LAYER                         │
├─────────────────────────────────────────────────────┤
│  MySQL Database                                      │
│  - InnoDB Engine                                     │
│  - ACID Transactions                                 │
│  - Foreign Key Constraints                           │
└─────────────────────────────────────────────────────┘
```

### 3.2 Teknoloji Stack Detayı

#### 3.2.1 Backend
- **Framework**: Flask 3.0+
- **ORM**: SQLAlchemy
- **Migration**: Alembic
- **WebSocket**: Flask-SocketIO
- **Authentication**: Flask-JWT-Extended
- **CORS**: Flask-CORS
- **Validation**: Marshmallow
- **Task Queue**: Celery (opsiyonel, bildirimler için)

#### 3.2.2 Frontend
- **HTML5**: Semantic markup
- **CSS3**: Modern CSS (Grid, Flexbox)
- **JavaScript**: ES6+ (Vanilla JS veya Vue.js)
- **PWA**: Workbox, Service Workers
- **QR Scanner**: HTML5-QRCode veya QR Scanner
- **Icons**: Font Awesome / Material Icons
- **Charts**: Chart.js (raporlama için)

#### 3.2.3 Database
- **RDBMS**: MySQL 8.0+
- **Connection Pool**: PyMySQL / mysql-connector-python
- **Backup**: Automated daily backups

#### 3.2.4 Push Notifications
- **Web Push**: PyWebPush
- **Service Worker**: Background sync
- **VAPID Keys**: Server-side key management

#### 3.2.5 QR Code Generation
- **Library**: qrcode + Pillow
- **Format**: PNG, SVG
- **Error Correction**: High (Level H)

---

## 4. Veritabanı Yapısı

### 4.1 Veri Modeli (ER Diagram)

```
┌─────────────────┐       ┌──────────────────┐
│     Hotels      │       │   System_Users   │
├─────────────────┤       ├──────────────────┤
│ id (PK)         │       │ id (PK)          │
│ name            │───┐   │ hotel_id (FK)    │
│ address         │   │   │ username         │
│ phone           │   │   │ password_hash    │
│ email           │   │   │ role             │
│ created_at      │   │   │ is_active        │
└─────────────────┘   │   │ created_at       │
                      │   │ last_login       │
                      │   └──────────────────┘
                      │            │
                      │            │
                      ├────────────┴──────────────┐
                      │                           │
                      ▼                           ▼
         ┌──────────────────┐       ┌──────────────────┐
         │    Locations     │       │     Buggies      │
         ├──────────────────┤       ├──────────────────┤
         │ id (PK)          │       │ id (PK)          │
         │ hotel_id (FK)    │       │ hotel_id (FK)    │
         │ name             │       │ user_id (FK)     │
         │ description      │       │ name             │
         │ qr_code_data     │       │ plate_number     │
         │ qr_code_image    │       │ capacity         │
         │ is_active        │       │ status           │
         │ created_at       │       │ current_loc (FK) │
         └──────────────────┘       │ created_at       │
                  │                 └──────────────────┘
                  │                          │
                  │                          │
                  └────────┬─────────────────┘
                           │
                           ▼
                  ┌──────────────────┐
                  │  Buggy_Requests  │
                  ├──────────────────┤
                  │ id (PK)          │
                  │ location_id (FK) │
                  │ buggy_id (FK)    │
                  │ room_number      │
                  │ guest_device_id  │
                  │ status           │
                  │ requested_at     │
                  │ accepted_at      │
                  │ completed_at     │
                  │ cancelled_at     │
                  └──────────────────┘
                           │
                           ▼
                  ┌──────────────────┐
                  │   Audit_Trail    │
                  ├──────────────────┤
                  │ id (PK)          │
                  │ user_id (FK)     │
                  │ action_type      │
                  │ entity_type      │
                  │ entity_id        │
                  │ old_value        │
                  │ new_value        │
                  │ ip_address       │
                  │ user_agent       │
                  │ created_at       │
                  └──────────────────┘
```

### 4.2 Tablo Detayları

#### 4.2.1 Hotels
```sql
CREATE TABLE hotels (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    address TEXT,
    phone VARCHAR(50),
    email VARCHAR(255),
    logo VARCHAR(500),
    timezone VARCHAR(50) DEFAULT 'Europe/Istanbul',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

#### 4.2.2 System_Users
```sql
CREATE TABLE system_users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    hotel_id INT NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('admin', 'driver') NOT NULL,
    full_name VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL,
    FOREIGN KEY (hotel_id) REFERENCES hotels(id) ON DELETE CASCADE,
    INDEX idx_username (username),
    INDEX idx_role (role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

#### 4.2.3 Locations
```sql
CREATE TABLE locations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    hotel_id INT NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    qr_code_data VARCHAR(500) UNIQUE NOT NULL,
    qr_code_image TEXT,
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    is_active BOOLEAN DEFAULT TRUE,
    display_order INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (hotel_id) REFERENCES hotels(id) ON DELETE CASCADE,
    INDEX idx_hotel_active (hotel_id, is_active),
    UNIQUE KEY uk_hotel_name (hotel_id, name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

#### 4.2.4 Buggies
```sql
CREATE TABLE buggies (
    id INT AUTO_INCREMENT PRIMARY KEY,
    hotel_id INT NOT NULL,
    user_id INT UNIQUE,
    name VARCHAR(100) NOT NULL,
    plate_number VARCHAR(50),
    capacity INT DEFAULT 4,
    status ENUM('available', 'busy', 'offline') DEFAULT 'offline',
    current_location_id INT,
    last_active TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (hotel_id) REFERENCES hotels(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES system_users(id) ON DELETE SET NULL,
    FOREIGN KEY (current_location_id) REFERENCES locations(id) ON DELETE SET NULL,
    INDEX idx_status (status),
    INDEX idx_hotel_status (hotel_id, status),
    UNIQUE KEY uk_hotel_name (hotel_id, name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

#### 4.2.5 Buggy_Requests
```sql
CREATE TABLE buggy_requests (
    id INT AUTO_INCREMENT PRIMARY KEY,
    hotel_id INT NOT NULL,
    location_id INT NOT NULL,
    buggy_id INT,
    room_number VARCHAR(50),
    has_room BOOLEAN DEFAULT TRUE,
    guest_device_id VARCHAR(255),
    status ENUM('pending', 'accepted', 'completed', 'cancelled') DEFAULT 'pending',
    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    accepted_at TIMESTAMP NULL,
    completed_at TIMESTAMP NULL,
    cancelled_at TIMESTAMP NULL,
    cancelled_by INT,
    notes TEXT,
    FOREIGN KEY (hotel_id) REFERENCES hotels(id) ON DELETE CASCADE,
    FOREIGN KEY (location_id) REFERENCES locations(id) ON DELETE CASCADE,
    FOREIGN KEY (buggy_id) REFERENCES buggies(id) ON DELETE SET NULL,
    FOREIGN KEY (cancelled_by) REFERENCES system_users(id) ON DELETE SET NULL,
    INDEX idx_status (status),
    INDEX idx_buggy_status (buggy_id, status),
    INDEX idx_requested_at (requested_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

#### 4.2.6 Audit_Trail
```sql
CREATE TABLE audit_trail (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    hotel_id INT NOT NULL,
    user_id INT,
    action_type VARCHAR(50) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id INT,
    old_value TEXT,
    new_value TEXT,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (hotel_id) REFERENCES hotels(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES system_users(id) ON DELETE SET NULL,
    INDEX idx_created_at (created_at),
    INDEX idx_user_action (user_id, action_type),
    INDEX idx_entity (entity_type, entity_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

#### 4.2.7 Sessions
```sql
CREATE TABLE sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    buggy_id INT,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    device_info TEXT,
    ip_address VARCHAR(45),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES system_users(id) ON DELETE CASCADE,
    FOREIGN KEY (buggy_id) REFERENCES buggies(id) ON DELETE CASCADE,
    INDEX idx_expires (expires_at),
    INDEX idx_user_active (user_id, expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

---

## 5. Kullanıcı Rolleri ve Yetkiler

### 5.1 Rol Tanımları

#### 5.1.1 Admin (Sistem Yöneticisi)
**Yetkiler:**
- ✅ Otel bilgilerini düzenleme
- ✅ Lokasyon ekleme/düzenleme/silme
- ✅ QR kod oluşturma ve yazdırma
- ✅ Buggy ekleme/düzenleme/silme
- ✅ Buggy sürücüsü hesabı oluşturma
- ✅ Tüm buggy'lerin durumunu görüntüleme
- ✅ Tüm talepleri görüntüleme
- ✅ Sürücü oturumlarını sonlandırma
- ✅ Detaylı raporlara erişim
- ✅ Audit trail görüntüleme
- ✅ Sistem ayarları yapılandırma

#### 5.1.2 Driver (Buggy Sürücüsü)
**Yetkiler:**
- ✅ Sisteme giriş/çıkış yapma
- ✅ Lokasyon bildirimi
- ✅ Gelen talepleri görüntüleme
- ✅ Talep kabul etme
- ✅ Müsaitlik durumu güncelleme
- ✅ Tamamlanan talepleri işaretleme
- ✅ Diğer buggy'lerin durumunu görme
- ✅ Kendi raporlarını görüntüleme
- ❌ Sistem ayarlarına erişim yok
- ❌ Diğer sürücülerin raporlarını görme yok

#### 5.1.3 Guest (Misafir - Kayıtsız)
**Yetkiler:**
- ✅ QR kod okutarak buggy çağırma
- ✅ Oda numarası girme (opsiyonel)
- ✅ Talep durumu takibi
- ❌ Sistem yönetimi yok
- ❌ Tarihsel verilere erişim yok

### 5.2 Yetkilendirme Matrisi

| Özellik                          | Admin | Driver | Guest |
|----------------------------------|-------|--------|-------|
| Otel Ayarları                    | ✅    | ❌     | ❌    |
| Lokasyon Yönetimi                | ✅    | ❌     | ❌    |
| QR Kod Oluşturma                 | ✅    | ❌     | ❌    |
| Buggy Yönetimi                   | ✅    | ❌     | ❌    |
| Kullanıcı Yönetimi               | ✅    | ❌     | ❌    |
| Buggy Çağırma                    | ❌    | ❌     | ✅    |
| Talep Kabul/Red                  | ❌    | ✅     | ❌    |
| Lokasyon Bildirimi               | ❌    | ✅     | ❌    |
| Tüm Buggy'leri Görüntüleme       | ✅    | ✅     | ❌    |
| Tüm Talepleri Görüntüleme        | ✅    | ✅     | ❌    |
| Kendi Raporları                  | ✅    | ✅     | ❌    |
| Tüm Raporlar                     | ✅    | ❌     | ❌    |
| Audit Trail                      | ✅    | ❌     | ❌    |
| Oturum Sonlandırma (Başkaları)   | ✅    | ❌     | ❌    |

---

## 6. Özellikler ve Fonksiyonlar

### 6.1 İlk Kurulum Modülü

#### 6.1.1 Otel Bilgileri Girişi
- **Form Alanları:**
  - Otel adı (zorunlu)
  - Adres (opsiyonel)
  - Telefon (opsiyonel)
  - E-posta (opsiyonel)
  - Logo yükleme (opsiyonel)
  - Saat dilimi seçimi

#### 6.1.2 Admin Hesabı Oluşturma
- **Form Alanları:**
  - Kullanıcı adı (benzersiz, zorunlu)
  - Şifre (minimum 8 karakter, zorunlu)
  - Şifre tekrarı
  - Ad Soyad (opsiyonel)
  - E-posta (opsiyonel)
  - Telefon (opsiyonel)

- **Şifre Gereksinimleri:**
  - Minimum 8 karakter
  - En az 1 büyük harf
  - En az 1 küçük harf
  - En az 1 rakam
  - Bcrypt ile hash'leme

### 6.2 Admin Paneli

#### 6.2.1 Dashboard
- **Gerçek Zamanlı Widget'lar:**
  - Aktif buggy sayısı
  - Bekleyen talep sayısı
  - Bugün tamamlanan talep sayısı
  - Ortalama yanıt süresi
  - Harita görünümü (tüm buggy lokasyonları)
  
- **Canlı Bildirimler:**
  - Yeni talep geldiğinde
  - Talep kabul edildiğinde
  - Talep tamamlandığında
  - Buggy online/offline olduğunda

#### 6.2.2 Lokasyon Yönetimi
**Liste Görünümü:**
- Tüm lokasyonlar (tablo formatı)
- Durum (Aktif/Pasif)
- QR kod önizleme
- Düzenle/Sil butonları

**Lokasyon Ekleme/Düzenleme Formu:**
- Lokasyon adı
- Açıklama
- Koordinatlar (opsiyonel)
- Aktif/Pasif durumu
- Sıralama numarası

**QR Kod İşlemleri:**
- Otomatik QR kod üretimi
- QR kod önizleme
- PNG/SVG indirme
- Toplu yazdırma
- QR kod yeniden oluşturma

#### 6.2.3 Buggy Yönetimi
**Liste Görünümü:**
- Buggy adı
- Plaka numarası
- Atanmış sürücü
- Mevcut durum (Available/Busy/Offline)
- Son görülme zamanı
- Aksiyon butonları

**Buggy Ekleme/Düzenleme:**
- Buggy adı/numarası
- Plaka numarası
- Kapasite
- Sürücü atama
- Kullanıcı adı ve şifre belirleme
- Durum (Aktif/Pasif)

**Sürücü Oturum Yönetimi:**
- Aktif oturumları görüntüleme
- Oturum sonlandırma
- Son aktivite takibi
- Cihaz bilgileri

#### 6.2.4 Talep Yönetimi
**Canlı Talep Listesi:**
- Talep zamanı
- Lokasyon
- Oda numarası
- Durum (Bekliyor/Kabul Edildi/Tamamlandı)
- Atanan buggy
- Yanıt süresi

**Filtreler:**
- Duruma göre
- Tarihe göre
- Lokasyona göre
- Buggy'ye göre

#### 6.2.5 Raporlama Modülü
**Rapor Türleri:**

1. **Günlük Özet Raporu:**
   - Toplam talep sayısı
   - Tamamlanan/iptal edilen talepler
   - Ortalama yanıt süresi
   - Ortalama tamamlanma süresi
   - Buggy başına performans

2. **Buggy Performans Raporu:**
   - Buggy bazında detay
   - Kabul edilen talep sayısı
   - Ortalama müdahale süresi
   - Müsaitlik oranı
   - Aktif çalışma süresi

3. **Lokasyon Analiz Raporu:**
   - Lokasyon bazında talep sayısı
   - En çok talep alan lokasyonlar
   - Saat bazında dağılım
   - Haftalık trend

4. **Detaylı İşlem Raporu:**
   - Tüm talepler (filtreli)
   - Excel export
   - PDF export

#### 6.2.6 Audit Trail
**Görüntüleme:**
- Kronolojik sıralama
- Kullanıcı bazlı filtreleme
- İşlem tipi filtreleme
- Tarih aralığı seçimi
- Detaylı değişiklik görüntüleme (eski → yeni)

**Kayıt Edilen İşlemler:**
- Kullanıcı girişi/çıkışı
- Lokasyon ekleme/düzenleme/silme
- Buggy ekleme/düzenleme/silme
- Talep oluşturma/kabul/tamamlama/iptal
- Ayar değişiklikleri
- Oturum sonlandırma

### 6.3 Buggy Sürücüsü Paneli

#### 6.3.1 Giriş Ekranı
- Kullanıcı adı
- Şifre
- "Beni Hatırla" seçeneği
- TWA kurulum prompt (ilk giriş)

#### 6.3.2 Ana Dashboard
**Durum Kartı:**
- Mevcut lokasyon
- Müsaitlik durumu (Available/Busy)
- Çevrimiçi süre
- Bugün tamamlanan talep sayısı

**Lokasyon Bildirimi:**
- Hızlı lokasyon değiştirme dropdown
- "Buradayım" butonları
- Harita görünümü (opsiyonel)

**Talep Listesi:**
- Bekleyen talepler (gerçek zamanlı)
- Lokasyon
- Oda numarası
- Bekleme süresi
- "Kabul Et" butonu
- Diğer buggy'lerin durumları

#### 6.3.3 Aktif Talep Yönetimi
- Kabul edilen talep detayı
- Zamanlayıcı (başlangıçtan itibaren)
- "Tamamlandı" butonu
- Varış lokasyonu seçimi
- İptal seçeneği (nedeni ile)

#### 6.3.4 Push Bildirimleri
- Yeni talep geldiğinde
- Ses uyarısı (opsiyonel)
- Vibrasyon (mobil)
- Badge sayısı (okunmamış talepler)

#### 6.3.5 Sürücü Raporları
- Günlük özet
- Haftalık performans
- Tamamlanan talep geçmişi
- Ortalama süre istatistikleri

### 6.4 Misafir (Guest) Arayüzü

#### 6.4.1 QR Kod Okutma Akışı
1. QR kod kameraya gösterilir
2. Otomatik URL redirect
3. Lokasyon otomatik tanınır
4. Buggy çağırma formu açılır

#### 6.4.2 Buggy Çağırma Formu
**Form Elemanları:**
- Lokasyon (otomatik, salt okunur)
- "Oda Numaranız?" input
- "Oda numaram yok" checkbox
- "Buggy Çağır" butonu (büyük, belirgin)

**Validasyon:**
- Oda numarası: alfanumerik, max 10 karakter
- Checkbox seçili ise oda numarası zorunlu değil

#### 6.4.3 Talep Takip Ekranı
- Talep durumu (Bekleniyor/Kabul Edildi/Yolda)
- Atanan buggy bilgisi
- Tahmini varış süresi
- "İptal Et" butonu (sadece bekleyen durumda)
- Otomatik yenileme (gerçek zamanlı)

#### 6.4.4 Tamamlanma Ekranı
- "Buggy'niz geldi" mesajı
- Teşekkür mesajı
- Yeni talep oluşturma linki
- Anket/Geri bildirim (opsiyonel)

---

## 7. Geliştirme Aşamaları

### Faz 1: Temel Altyapı
**Sprint 1.1: Proje Kurulumu**
- ✅ Geliştirme ortamı hazırlığı
- ✅ Flask proje yapısı oluşturma
- ✅ MySQL database kurulumu
- ✅ Git repository oluşturma
- ✅ Temel klasör yapısı

**Sprint 1.2: Veritabanı ve Modeller**
- ✅ SQLAlchemy ORM kurulumu
- ✅ Tüm tablo modellerinin oluşturulması
- ✅ Migration script'leri
- ✅ Seed data (örnek veriler)
- ✅ Database backup stratejisi

### Faz 2: Kimlik Doğrulama ve Yetkilendirme
**Sprint 2.1: Authentication**
- ✅ JWT token implementasyonu
- ✅ Login/Logout endpoints
- ✅ Password hashing (bcrypt)
- ✅ Session management
- ✅ Token refresh mekanizması

**Sprint 2.2: Authorization**
- ✅ Role-based access control
- ✅ Permission decorators
- ✅ Middleware katmanı
- ✅ Admin/Driver ayrımı

### Faz 3: İlk Kurulum ve Admin Modülü
**Sprint 3.1: Kurulum Wizard**
- ✅ Otel bilgileri formu
- ✅ Admin hesabı oluşturma
- ✅ İlk kurulum kontrolü
- ✅ Database initialization

**Sprint 3.2: Admin Paneli - Temel**
- ✅ Dashboard layout
- ✅ Lokasyon CRUD
- ✅ QR kod üretimi
- ✅ Buggy CRUD
- ✅ Kullanıcı yönetimi

### Faz 4: Gerçek Zamanlı İletişim 
**Sprint 4.1: WebSocket Setup**
- ✅ Flask-SocketIO kurulumu
- ✅ Room/namespace yapısı
- ✅ Event handlers
- ✅ Connection management

**Sprint 4.2: Canlı Güncellemeler**
- ✅ Buggy lokasyon güncellemeleri
- ✅ Talep bildirimleri
- ✅ Durum değişiklikleri
- ✅ Dashboard canlı veriler

### Faz 5: Buggy Talep Sistemi 
**Sprint 5.1: Misafir Arayüzü**
- ✅ QR kod okuyucu entegrasyonu
- ✅ Buggy çağırma formu
- ✅ Talep takip ekranı
- ✅ Responsive tasarım

**Sprint 5.2: Sürücü Arayüzü**
- ✅ Driver dashboard
- ✅ Talep listesi
- ✅ Talep kabul/red
- ✅ Lokasyon bildirimi
- ✅ Talep tamamlama

### Faz 6: Push Bildirimler
**Sprint 6.1: Web Push**
- ✅ Service Worker setup
- ✅ VAPID key üretimi
- ✅ Push subscription
- ✅ Notification payload
- ✅ Background sync

### Faz 7: PWA Özellikleri
**Sprint 7.1: PWA Implementation**
- ✅ Manifest.json
- ✅ Service Worker caching
- ✅ Offline support (sınırlı)
- ✅ Install prompts
- ✅ App icons ve splash screens

### Faz 8: Raporlama ve Audit
**Sprint 8.1: Raporlar**
- ✅ Günlük özet raporu
- ✅ Buggy performans raporu
- ✅ Lokasyon analizi
- ✅ Excel/PDF export
- ✅ Chart.js grafikleri

**Sprint 8.2: Audit Trail**
- ✅ Otomatik loglama sistemi
- ✅ Audit viewer arayüzü
- ✅ Filtreleme ve arama
- ✅ Export özelliği

### Faz 9: Test ve Optimizasyon
**Sprint 9.1: Testing**
- ✅ Unit testler
- ✅ Integration testler
- ✅ API testleri
- ✅ UI testleri
- ✅ Performance testleri

**Sprint 9.2: Optimizasyon**
- ✅ Database query optimization
- ✅ Caching stratejileri
- ✅ Frontend minification
- ✅ Image optimization
- ✅ Load testing
- ✅ Security audit

### Faz 10: Deployment ve Dokümantasyon 
**Sprint 10.1: Production Setup**
- ✅ Server configuration
- ✅ SSL certificate
- ✅ Environment variables
- ✅ Database backup automation
- ✅ Monitoring setup

**Sprint 10.2: Documentation**
- ✅ Kullanıcı kılavuzu
- ✅ Admin dokümantasyonu
- ✅ API dokümantasyonu
- ✅ Deployment guide
- ✅ Troubleshooting guide

**Toplam Süre: 14-16 hafta (3.5-4 ay)**

---

## 8. Teknoloji Stack Detayı

### 8.1 Backend Teknolojileri

#### 8.1.1 Core Framework
```
Flask==3.0.0
Flask-SQLAlchemy==3.1.1
Flask-Migrate==4.0.5
Flask-JWT-Extended==4.5.3
Flask-CORS==4.0.0
Flask-SocketIO==5.3.5
```

#### 8.1.2 Database
```
PyMySQL==1.1.0
mysqlclient==2.2.0
```

#### 8.1.3 Validation & Serialization
```
marshmallow==3.20.1
marshmallow-sqlalchemy==0.29.0
```

#### 8.1.4 Security
```
bcrypt==4.1.1
cryptography==41.0.7
pyotp==2.9.0 (2FA için opsiyonel)
```

#### 8.1.5 QR Code & Image
```
qrcode==7.4.2
Pillow==10.1.0
```

#### 8.1.6 Push Notifications
```
pywebpush==1.14.0
```

#### 8.1.7 Utilities
```
python-dotenv==1.0.0
python-dateutil==2.8.2
pytz==2023.3
```

#### 8.1.8 Testing
```
pytest==7.4.3
pytest-flask==1.3.0
pytest-cov==4.1.0
```

### 8.2 Frontend Teknolojileri

#### 8.2.1 Core
- HTML5
- CSS3 (Custom + Framework)
- Vanilla JavaScript ES6+ veya Vue.js 3

#### 8.2.2 CSS Framework (Seçenekler)
- Tailwind CSS 3.x
- Bootstrap 5.x
- Bulma CSS

#### 8.2.3 JavaScript Libraries
```javascript
// QR Code Scanner
html5-qrcode: 2.3.8

// Charts
chart.js: 4.4.0

// Icons
font-awesome: 6.5.0

// HTTP Client
axios: 1.6.0

// WebSocket Client
socket.io-client: 4.6.0
```

#### 8.2.4 PWA Tools
- Workbox 7.0
- Service Worker API
- Web App Manifest
- Push API

### 8.3 Development Tools

#### 8.3.1 Version Control
- Git
- GitHub/GitLab

#### 8.3.2 IDE/Editor
- VS Code

#### 8.3.3 API Testing
- Postman
- Insomnia
- Thunder Client (VS Code)

#### 8.3.4 Database Tools
- MySQL Workbench
- phpMyAdmin
- DBeaver

---

## 9. Güvenlik ve Performans

### 9.1 Güvenlik Önlemleri

#### 9.1.1 Kimlik Doğrulama
- **Password Hashing**: Bcrypt (cost factor: 12)
- **JWT Tokens**: 
  - Access Token: 1 saat
  - Refresh Token: 7 gün
  - Secret key: 256-bit rastgele
- **Session Management**:
  - Secure cookies
  - HTTPOnly flag
  - SameSite=Strict
  - CSRF token

#### 9.1.2 API Güvenliği
- **Rate Limiting**: 
  - Guest: 10 req/dakika
  - Driver: 60 req/dakika
  - Admin: 100 req/dakika
- **Input Validation**:
  - Marshmallow schemas
  - SQL injection koruması
  - XSS filtering
- **CORS Policy**:
  - Sadece belirli origin'lere izin
  - Credentials: true
  - Preflight caching

#### 9.1.3 Data Protection
- **Encryption at Rest**:
  - Database AES-256 encryption (opsiyonel)
  - Hassas alan encryption
- **Encryption in Transit**:
  - TLS 1.3
  - HTTPS zorunlu
  - HSTS header
- **Privacy**:
  - GDPR uyumlu veri saklama
  - Kişisel veri minimizasyonu
  - Anonim analytics

#### 9.1.4 Audit & Monitoring
- Tüm kritik işlemler loglanır
- Başarısız login denemeleri izlenir
- Anormal aktivite tespiti
- IP blacklisting

### 9.2 Performans Optimizasyonları

#### 9.2.1 Database Optimizations
- **Indexing Strategy**:
  - Primary keys (id)
  - Foreign keys
  - Frequently queried columns (status, created_at)
  - Composite indexes (hotel_id + status)
- **Query Optimization**:
  - Eager loading (avoid N+1)
  - Pagination (LIMIT/OFFSET)
  - Query result caching
- **Connection Pooling**:
  - Min: 5 connections
  - Max: 20 connections
  - Overflow: 10
  - Timeout: 30 seconds

#### 9.2.2 Caching Strategy
- **Redis Cache** (opsiyonel):
  - Session storage
  - Frequently accessed data
  - Rate limit counters
  - QR code cache
- **Browser Caching**:
  - Static assets (1 year)
  - API responses (conditional)
  - Service Worker cache

#### 9.2.3 Frontend Performance
- **Asset Optimization**:
  - Minification (CSS/JS)
  - Gzip compression
  - Image optimization (WebP)
  - Lazy loading
- **Code Splitting**:
  - Route-based chunks
  - Dynamic imports
  - Critical CSS inlining
- **CDN Usage**:
  - Static assets
  - Font files
  - Icons

#### 9.2.4 Real-time Performance
- **WebSocket Optimization**:
  - Connection pooling
  - Message batching
  - Binary protocol (MessagePack)
  - Heartbeat mechanism
- **Push Notifications**:
  - Batch sending
  - Priority queuing
  - Retry logic

### 9.3 Scalability Considerations

#### 9.3.1 Horizontal Scaling
- Load balancer ready
- Stateless design
- Shared session storage (Redis)
- Database read replicas

#### 9.3.2 Monitoring & Alerting
- Application Performance Monitoring (APM)
- Error tracking (Sentry)
- Uptime monitoring
- Database query performance
- Real-time alerts

---

## 10. Test Stratejisi

### 10.1 Test Tipleri

#### 10.1.1 Unit Tests
**Coverage Target: 80%+**

**Backend Tests:**
```python
# Örnek test case
def test_create_location(client, auth_headers):
    response = client.post('/api/locations', 
        json={'name': 'Test Location'},
        headers=auth_headers)
    assert response.status_code == 201
    assert response.json['name'] == 'Test Location'
```

**Test Konuları:**
- Model validations
- Business logic
- Helper functions
- Serializers

#### 10.1.2 Integration Tests
**API Endpoint Tests:**
- Authentication flow
- CRUD operations
- Permission checks
- Error handling
- WebSocket events

**Database Tests:**
- Transactions
- Constraints
- Cascading deletes
- Indexes

#### 10.1.3 End-to-End Tests
**User Flows:**
1. Admin oturum açma → Lokasyon oluşturma → QR kod üretimi
2. Guest QR okutma → Buggy çağırma → Talep takibi
3. Driver giriş → Talep kabul → Tamamlama
4. Admin dashboard → Raporlar → Export

**Tools:**
- Selenium/Playwright
- Cypress (alternatif)

#### 10.1.4 Performance Tests
**Load Testing:**
- 100 eşzamanlı kullanıcı
- 1000 req/dakika
- Response time < 200ms (p95)

**Stress Testing:**
- Maksimum kapasite testi
- Failure point belirleme
- Recovery testing

**Tools:**
- Apache JMeter
- Locust
- k6

### 10.2 Test Ortamları

1. **Development**: Yerel geliştirme ortamı
2. **Testing**: Otomatik test ortamı
3. **Staging**: Production benzeri test
4. **Production**: Canlı sistem

### 10.3 CI/CD Pipeline

```yaml
# GitHub Actions örnek workflow
name: CI/CD Pipeline

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: pytest --cov
      - name: Lint
        run: flake8
  
  deploy:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to production
        run: ./deploy.sh
```

---

## 11. Proje Klasör Yapısı

```
buggycall/
│
├── app/
│   ├── __init__.py              # Flask app factory
│   ├── config.py                # Konfigürasyon ayarları
│   │
│   ├── models/                  # Database modelleri
│   │   ├── __init__.py
│   │   ├── hotel.py
│   │   ├── user.py
│   │   ├── location.py
│   │   ├── buggy.py
│   │   ├── request.py
│   │   ├── audit.py
│   │   └── session.py
│   │
│   ├── schemas/                 # Marshmallow schemas
│   │   ├── __init__.py
│   │   ├── hotel_schema.py
│   │   ├── user_schema.py
│   │   └── ...
│   │
│   ├── routes/                  # API endpoints
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── admin.py
│   │   ├── driver.py
│   │   ├── guest.py
│   │   └── reports.py
│   │
│   ├── services/               # Business logic
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── location_service.py
│   │   ├── buggy_service.py
│   │   ├── request_service.py
│   │   ├── qr_service.py
│   │   ├── notification_service.py
│   │   └── audit_service.py
│   │
│   ├── utils/                   # Yardımcı fonksiyonlar
│   │   ├── __init__.py
│   │   ├── validators.py
│   │   ├── decorators.py
│   │   ├── helpers.py
│   │   └── constants.py
│   │
│   ├── websocket/              # WebSocket handlers
│   │   ├── __init__.py
│   │   ├── events.py
│   │   └── rooms.py
│   │
│   └── static/                 # Frontend assets
│       ├── css/
│       │   ├── admin.css
│       │   ├── driver.css
│       │   └── guest.css
│       ├── js/
│       │   ├── admin.js
│       │   ├── driver.js
│       │   ├── guest.js
│       │   └── common.js
│       ├── images/
│       ├── icons/
│       └── manifest.json
│
├── templates/                   # Jinja2 templates
│   ├── base.html
│   ├── admin/
│   │   ├── dashboard.html
│   │   ├── locations.html
│   │   ├── buggies.html
│   │   └── reports.html
│   ├── driver/
│   │   ├── dashboard.html
│   │   └── requests.html
│   ├── guest/
│   │   ├── call.html
│   │   └── status.html
│   └── auth/
│       ├── login.html
│       └── setup.html
│
├── migrations/                  # Alembic migrations
│   └── versions/
│
├── tests/                      # Test dosyaları
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── scripts/                    # Utility scripts
│   ├── init_db.py
│   ├── seed_data.py
│   └── backup.py
│
├── docs/                       # Dokümantasyon
│   ├── api.md
│   ├── deployment.md
│   └── user_guide.md
│
├── .env.example                # Örnek environment variables
├── .gitignore
├── requirements.txt            # Python dependencies
├── requirements-dev.txt        # Development dependencies
├── README.md
├── run.py                      # Flask app entry point
└── wsgi.py                     # Production WSGI

```



---

## 13. Gelecek Geliştirmeler (Roadmap)

### Versiyon 1.1 
- 📱 Native mobile apps (React Native)
- 📊 Gelişmiş analytics dashboard
- 🌐 Multi-language support

### Versiyon 1.2 
- 📍 GPS tracking (gerçek zamanlı)

- ⭐ Geri bildirim ve değerlendirme sistemi

  

### 
