# Requirements Document

## Introduction

Bu proje, mevcut Flask tabanlı Shuttle Call web uygulamasını modern bir mobil uygulama mimarisine taşımayı amaçlamaktadır. Yeni mimari, React Native (Expo) ile geliştirilmiş mobil uygulama, FastAPI ile yazılmış backend API ve PostgreSQL veritabanından oluşacaktır. Mevcut sistemin tüm özellikleri korunacak ve mobil deneyim optimize edilecektir.

## Glossary

- **Mobile_App**: React Native (Expo) ile geliştirilmiş iOS ve Android uygulaması
- **Backend_API**: FastAPI (Python 3.10) ile yazılmış RESTful API servisi
- **Database**: PostgreSQL veritabanı (SQLAlchemy ORM + Alembic migrations)
- **FCM**: Firebase Cloud Messaging - Push notification servisi
- **QR_Scanner**: Mobil uygulamada QR kod okuma özelliği
- **JWT_Auth**: JSON Web Token tabanlı kimlik doğrulama sistemi
- **Migration_Process**: Mevcut Flask uygulamasından yeni mimariye geçiş süreci
- **Legacy_System**: Mevcut Flask tabanlı web uygulaması
- **User_Roles**: Misafir (Guest), Sürücü (Driver), Admin olmak üzere 3 kullanıcı rolü

## Requirements

### Requirement 1: Mobil Uygulama Temel Altyapısı

**User Story:** Bir geliştirici olarak, React Native (Expo) ile çalışan temel mobil uygulama altyapısını oluşturmak istiyorum, böylece iOS ve Android platformlarında çalışan bir uygulama geliştirebilirim.

#### Acceptance Criteria

1. WHEN geliştirici "npx expo init" komutunu çalıştırdığında, THE Mobile_App SHALL D:\buggycall\buggy-react-native dizininde TypeScript ile yapılandırılmış Expo projesi oluşturmalıdır
2. WHEN Mobile_App başlatıldığında, THE Mobile_App SHALL iOS ve Android simulatörlerinde hatasız çalışmalıdır
3. THE Mobile_App SHALL React Navigation kütüphanesi ile sayfa yönlendirme yapısını içermelidir
4. THE Mobile_App SHALL AsyncStorage ile local veri saklama özelliğini desteklemelidir
5. THE Mobile_App SHALL expo-camera ile QR kod okuma özelliğini içermelidir

### Requirement 2: Backend API Altyapısı

**User Story:** Bir backend geliştirici olarak, FastAPI ile RESTful API servisi oluşturmak istiyorum, böylece mobil uygulama ile güvenli ve hızlı iletişim sağlayabilirim.

#### Acceptance Criteria

1. THE Backend_API SHALL FastAPI framework (Python 3.10+) ile geliştirilmelidir
2. THE Backend_API SHALL SQLAlchemy ORM ile PostgreSQL veritabanına bağlanmalıdır
3. THE Backend_API SHALL Alembic ile database migration yönetimini desteklemelidir
4. THE Backend_API SHALL JWT tabanlı kimlik doğrulama sistemi içermelidir
5. WHEN Backend_API başlatıldığında, THE Backend_API SHALL otomatik API dokümantasyonu (/docs endpoint) sunmalıdır
6. THE Backend_API SHALL CORS yapılandırması ile mobil uygulamadan gelen istekleri kabul etmelidir

### Requirement 3: Veritabanı Migrasyonu

**User Story:** Bir veritabanı yöneticisi olarak, mevcut MySQL veritabanındaki verileri PostgreSQL'e taşımak istiyorum, böylece veri kaybı olmadan yeni sisteme geçiş yapabilirim.

#### Acceptance Criteria

1. THE Migration_Process SHALL mevcut MySQL şemasını PostgreSQL uyumlu şemaya dönüştürmelidir
2. THE Migration_Process SHALL tüm tablo yapılarını (hotels, users, locations, shuttles, requests, audit_trail) PostgreSQL'e aktarmalıdır
3. THE Migration_Process SHALL tüm mevcut verileri (kullanıcılar, lokasyonlar, shuttle'lar) PostgreSQL'e aktarmalıdır
4. THE Migration_Process SHALL foreign key ilişkilerini ve index'leri koruyarak aktarmalıdır
5. WHEN migration tamamlandığında, THE Migration_Process SHALL veri bütünlüğü doğrulama raporu üretmelidir

### Requirement 4: Kimlik Doğrulama ve Yetkilendirme

**User Story:** Bir kullanıcı olarak, mobil uygulamada güvenli şekilde giriş yapmak istiyorum, böylece rolüme uygun özelliklere erişebilirim.

#### Acceptance Criteria

1. THE Backend_API SHALL kullanıcı adı ve şifre ile JWT token üretmelidir
2. THE Mobile_App SHALL JWT token'ı güvenli şekilde (AsyncStorage) saklamalıdır
3. THE Backend_API SHALL her API isteğinde JWT token'ı doğrulamalıdır
4. THE Backend_API SHALL kullanıcı rolüne (Guest, Driver, Admin) göre endpoint erişimini kısıtlamalıdır
5. WHEN JWT token süresi dolduğunda, THE Mobile_App SHALL refresh token ile yeni token almalıdır
6. THE Backend_API SHALL şifreleri bcrypt ile hashleyerek saklamalıdır

### Requirement 5: QR Kod Okuma ve Lokasyon Seçimi

**User Story:** Bir misafir olarak, mobil uygulamada QR kod okuyarak lokasyon seçmek istiyorum, böylece hızlıca shuttle çağırabilirim.

#### Acceptance Criteria

1. THE Mobile_App SHALL kamera izni isteyerek QR kod okuma ekranını açmalıdır
2. WHEN QR kod okunduğunda, THE Mobile_App SHALL QR kod içindeki lokasyon ID'sini Backend_API'ye göndermelidir
3. THE Backend_API SHALL lokasyon ID'sini doğrulayarak lokasyon bilgilerini döndürmelidir
4. THE Mobile_App SHALL okunan lokasyon bilgilerini ekranda göstermelidir
5. IF QR kod geçersizse, THEN THE Mobile_App SHALL kullanıcıya hata mesajı göstermelidir

### Requirement 6: Shuttle Çağırma İşlemi

**User Story:** Bir misafir olarak, seçtiğim lokasyondan shuttle çağırmak istiyorum, böylece otel içinde ulaşım hizmeti alabilirim.

#### Acceptance Criteria

1. WHEN misafir "Shuttle Çağır" butonuna bastığında, THE Mobile_App SHALL Backend_API'ye POST /api/requests isteği göndermelidir
2. THE Backend_API SHALL yeni shuttle request kaydı oluşturmalıdır
3. THE Backend_API SHALL request durumunu "pending" olarak işaretlemelidir
4. THE Backend_API SHALL müsait sürücülere FCM push notification göndermelidir
5. THE Mobile_App SHALL request ID'sini saklayarak durum takibi yapmalıdır

### Requirement 7: Push Notification Sistemi

**User Story:** Bir sürücü olarak, yeni shuttle çağrıları hakkında anlık bildirim almak istiyorum, böylece hızlıca müşterilere hizmet verebilirim.

#### Acceptance Criteria

1. THE Mobile_App SHALL uygulama açıldığında FCM token oluşturmalıdır
2. THE Mobile_App SHALL FCM token'ı Backend_API'ye kaydetmelidir
3. THE Backend_API SHALL firebase-admin SDK ile FCM'e push notification göndermelidir
4. WHEN yeni request oluşturulduğunda, THE Backend_API SHALL aktif sürücülere notification göndermelidir
5. THE Mobile_App SHALL notification geldiğinde ses ve titreşim ile kullanıcıyı uyarmalıdır
6. WHEN notification'a tıklandığında, THE Mobile_App SHALL ilgili request detay ekranını açmalıdır

### Requirement 8: Sürücü Request Yönetimi

**User Story:** Bir sürücü olarak, gelen shuttle çağrılarını görmek ve kabul etmek istiyorum, böylece misafirlere hizmet verebilirim.

#### Acceptance Criteria

1. THE Mobile_App SHALL sürücü dashboard'unda bekleyen requestleri listelemeli
2. WHEN sürücü request'e tıkladığında, THE Mobile_App SHALL request detaylarını (lokasyon, süre) göstermelidir
3. WHEN sürücü "Kabul Et" butonuna bastığında, THE Backend_API SHALL request durumunu "accepted" olarak güncellemeli
4. THE Backend_API SHALL misafir kullanıcıya "Sürücü yolda" notification'ı göndermelidir
5. THE Mobile_App SHALL sürücünün aktif request'ini ekranda göstermelidir
6. WHEN sürücü "Tamamla" butonuna bastığında, THE Backend_API SHALL request durumunu "completed" olarak işaretlemelidir

### Requirement 9: Admin Panel Özellikleri

**User Story:** Bir admin olarak, mobil uygulamada lokasyon, shuttle ve sürücü yönetimi yapmak istiyorum, böylece sistemi yönetebilirim.

#### Acceptance Criteria

1. THE Mobile_App SHALL admin kullanıcıları için ayrı navigation menüsü sunmalıdır
2. THE Mobile_App SHALL lokasyon ekleme, düzenleme ve silme ekranları içermelidir
3. THE Mobile_App SHALL shuttle ekleme, düzenleme ve silme ekranları içermelidir
4. THE Mobile_App SHALL sürücü ekleme, düzenleme ve silme ekranları içermelidir
5. THE Backend_API SHALL admin işlemlerini audit_trail tablosuna kaydetmelidir
6. THE Mobile_App SHALL QR kod oluşturma ve indirme özelliği sunmalıdır

### Requirement 10: Gerçek Zamanlı Durum Güncellemeleri

**User Story:** Bir kullanıcı olarak, shuttle durumlarını gerçek zamanlı görmek istiyorum, böylece güncel bilgiye sahip olabilirim.

#### Acceptance Criteria

1. THE Backend_API SHALL WebSocket bağlantısı (FastAPI WebSocket) desteklemelidir
2. THE Mobile_App SHALL uygulama açıldığında WebSocket bağlantısı kurmalıdır
3. WHEN request durumu değiştiğinde, THE Backend_API SHALL WebSocket üzerinden güncelleme göndermelidir
4. THE Mobile_App SHALL WebSocket mesajlarını dinleyerek UI'ı otomatik güncellemeli
5. IF WebSocket bağlantısı koparsa, THEN THE Mobile_App SHALL otomatik yeniden bağlanma denemesi yapmalıdır

### Requirement 11: Offline Destek ve Hata Yönetimi

**User Story:** Bir kullanıcı olarak, internet bağlantısı olmadığında bile uygulamayı kullanabilmek istiyorum, böylece kesintisiz deneyim yaşayabilirim.

#### Acceptance Criteria

1. THE Mobile_App SHALL internet bağlantısını kontrol etmelidir
2. WHEN internet bağlantısı yoksa, THE Mobile_App SHALL kullanıcıya uyarı mesajı göstermelidir
3. THE Mobile_App SHALL kritik verileri (kullanıcı bilgileri, son requestler) local cache'de saklamalıdır
4. WHEN internet bağlantısı geri geldiğinde, THE Mobile_App SHALL cache'deki verileri senkronize etmelidir
5. THE Backend_API SHALL tüm hataları (4xx, 5xx) anlamlı mesajlarla döndürmelidir
6. THE Mobile_App SHALL API hatalarını kullanıcı dostu mesajlarla göstermelidir

### Requirement 12: Performans ve Güvenlik

**User Story:** Bir sistem yöneticisi olarak, uygulamanın hızlı ve güvenli çalışmasını istiyorum, böylece kullanıcı memnuniyeti sağlayabilirim.

#### Acceptance Criteria

1. THE Backend_API SHALL API isteklerine 200ms altında yanıt vermelidir (basit GET istekleri için)
2. THE Backend_API SHALL rate limiting (100 istek/dakika) uygulamalıdır
3. THE Backend_API SHALL SQL injection koruması için parametreli sorgular kullanmalıdır
4. THE Mobile_App SHALL hassas verileri (token, şifre) şifreli şekilde saklamalıdır
5. THE Backend_API SHALL HTTPS üzerinden iletişim yapmalıdır
6. THE Backend_API SHALL input validation için Pydantic modelleri kullanmalıdır

### Requirement 13: Test ve Deployment

**User Story:** Bir geliştirici olarak, uygulamanın test edilebilir ve deploy edilebilir olmasını istiyorum, böylece kaliteli yazılım sunabilirim.

#### Acceptance Criteria

1. THE Backend_API SHALL pytest ile unit testleri içermelidir
2. THE Mobile_App SHALL Jest ile component testleri içermelidir
3. THE Backend_API SHALL Docker container olarak çalışabilmelidir
4. THE Backend_API SHALL environment variables ile yapılandırılabilir olmalıdır
5. THE Mobile_App SHALL Expo EAS Build ile iOS ve Android build alabilmelidir
