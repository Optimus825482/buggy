# 🚗 Buggy Call - Otel İçi Ulaşım Yönetim Sistemi

**Progressive Web App (PWA) ile Otel İçi Buggy Çağırma Sistemi**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0-green.svg)](https://flask.palletsprojects.com)
[![MySQL](https://img.shields.io/badge/MySQL-8.0+-orange.svg)](https://mysql.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📖 Proje Hakkında

Buggy Call, otel misafirlerinin QR kod okutarak kolayca buggy (golf arabası) çağırabildiği, sürücülerin talepleri gerçek zamanlı yönetebildiği ve yöneticilerin tüm operasyonu izleyebildiği modern bir web uygulamasıdır.

### ✨ Temel Özellikler

- 🔐 **Güvenli** - Rate limiting, CSRF koruması, input validation
- ⚡ **Hızlı** - Service layer, caching, optimized queries
- 📱 **PWA** - Mobil cihazlarda uygulama gibi çalışır
- � **Gemrçek Zamanlı** - WebSocket ile anlık bildirimler
- 📊 **İzlenebilir** - Audit trail ile tüm işlemler loglanır
- 🌐 **Ölçeklenebilir** - Redis desteği, horizontal scaling ready

---

## � Hızlı Başlangıç

### 5 Dakikada Çalıştır!

```bash
# 1. Bağımlılıkları yükle
pip install -r requirements.txt

# 2. Environment variables ayarla
copy .env.example .env
# .env dosyasını düzenle

# 3. Veritabanı oluştur
mysql -u root -p
CREATE DATABASE buggycall CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
exit

# 4. Migration çalıştır
python -m flask db upgrade

# 5. İlk admin kullanıcısı oluştur
python -m flask shell
# (QUICK_START.md'deki komutları çalıştır)

# 6. Uygulamayı başlat
python run.py
```

**Detaylı kurulum:** [QUICK_START.md](QUICK_START.md)

---

## 📋 Gereksinimler

- Python 3.8+
- MySQL 8.0+
- pip

**Opsiyonel:**
- Redis (rate limiting ve cache için)

---

## 🏗️ Mimari

```
┌─────────────────────────────────────────┐
│         PWA Client (Frontend)            │
│  - Service Worker                        │
│  - WebSocket Client                      │
│  - QR Scanner                            │
└─────────────────────────────────────────┘
                    ↕ HTTPS
┌─────────────────────────────────────────┐
│      Flask Application (Backend)         │
│  - RESTful API                           │
│  - WebSocket (Socket.IO)                 │
│  - JWT Authentication                    │
│  - Rate Limiting                         │
│  - CSRF Protection                       │
└─────────────────────────────────────────┘
                    ↕
┌─────────────────────────────────────────┐
│         Service Layer                    │
│  - AuthService                           │
│  - LocationService                       │
│  - BuggyService                          │
│  - RequestService                        │
│  - AuditService                          │
└─────────────────────────────────────────┘
                    ↕
┌─────────────────────────────────────────┐
│         MySQL Database                   │
│  - Hotels, Users, Locations              │
│  - Buggies, Requests                     │
│  - Audit Trail                           │
└─────────────────────────────────────────┘
```

---

## 🎯 Kullanıcı Rolleri

### 👤 Misafir (Guest)
- QR kod okutarak buggy çağırma
- Talep durumu takibi
- Gerçek zamanlı bildirimler

### 🚗 Sürücü (Driver)
- Gelen talepleri görüntüleme
- Talep kabul etme/tamamlama
- Lokasyon bildirimi
- Diğer buggy'lerin durumunu görme

### 👨‍💼 Admin
- Lokasyon yönetimi
- QR kod oluşturma
- Buggy ve sürücü yönetimi
- Raporlama ve analiz
- Audit trail görüntüleme

---

## 🔒 Güvenlik Özellikleri

- ✅ **Rate Limiting** - DDoS koruması (Flask-Limiter)
- ✅ **CSRF Protection** - Form güvenliği (Flask-WTF)
- ✅ **Input Validation** - Marshmallow schemas (18 adet)
- ✅ **Password Hashing** - Werkzeug secure hashing
- ✅ **JWT Authentication** - Token bazlı kimlik doğrulama
- ✅ **Audit Trail** - Tüm kritik işlemler loglanır
- ✅ **Role-Based Access** - Yetki kontrolü
- ✅ **SQL Injection Protection** - SQLAlchemy ORM

---

## 📊 Teknoloji Stack

### Backend
- **Framework:** Flask 3.0
- **ORM:** SQLAlchemy
- **Migration:** Alembic (Flask-Migrate)
- **Authentication:** Flask-JWT-Extended
- **WebSocket:** Flask-SocketIO
- **Validation:** Marshmallow
- **Security:** Flask-Limiter, Flask-WTF, Flask-Talisman

### Frontend
- **HTML5, CSS3, JavaScript ES6+**
- **PWA:** Service Workers, Web App Manifest
- **QR Scanner:** HTML5-QRCode
- **WebSocket Client:** Socket.IO Client
- **Charts:** Chart.js

### Database
- **MySQL 8.0+**
- **Redis** (opsiyonel, cache ve rate limiting için)

---

## 📁 Proje Yapısı

```
buggycall/
├── app/
│   ├── models/          # Database modelleri
│   ├── routes/          # API endpoints
│   ├── schemas/         # Validation schemas (18 adet)
│   ├── services/        # Business logic (5 service)
│   ├── utils/           # Helper functions
│   ├── websocket/       # WebSocket events
│   └── static/          # Frontend assets
├── migrations/          # Database migrations
├── templates/           # HTML templates
├── tests/               # Test files
├── docs/                # Dokümantasyon
├── .env.example         # Environment variables örneği
├── requirements.txt     # Python dependencies
└── run.py              # Application entry point
```

---

## 🧪 Testing

```bash
# Tüm testleri çalıştır
pytest

# Coverage raporu
pytest --cov=app --cov-report=html

# Specific test
pytest tests/test_api.py -v
```

---

## 📚 Dokümantasyon

- [QUICK_START.md](QUICK_START.md) - 5 dakikada başla
- [KURULUM.md](KURULUM.md) - Detaylı kurulum rehberi
- [FINAL_IMPLEMENTATION_REPORT.md](FINAL_IMPLEMENTATION_REPORT.md) - Tüm özellikler
- [SISTEM_RAPOR.md](SISTEM_RAPOR.md) - Sistem analizi
- [REDIS_KURULUM.md](REDIS_KURULUM.md) - Redis alternatifleri

---

## 🔧 API Endpoints

### Authentication
- `POST /auth/login` - Kullanıcı girişi
- `POST /auth/logout` - Çıkış
- `POST /auth/refresh` - Token yenileme

### Locations
- `GET /api/locations` - Lokasyonları listele
- `POST /api/locations` - Yeni lokasyon oluştur
- `PUT /api/locations/:id` - Lokasyon güncelle
- `DELETE /api/locations/:id` - Lokasyon sil

### Buggies
- `GET /api/buggies` - Buggy'leri listele
- `POST /api/buggies` - Yeni buggy oluştur
- `PUT /api/buggies/:id` - Buggy güncelle
- `DELETE /api/buggies/:id` - Buggy sil

### Requests
- `POST /api/requests` - Buggy çağır (Guest)
- `GET /api/requests` - Talepleri listele
- `PUT /api/requests/:id/accept` - Talebi kabul et (Driver)
- `PUT /api/requests/:id/complete` - Talebi tamamla (Driver)
- `PUT /api/requests/:id/cancel` - Talebi iptal et

### Health
- `GET /health` - Sistem sağlık kontrolü
- `GET /ping` - Basit ping
- `GET /version` - Versiyon bilgisi

---

## 🎨 Özellikler

### ✅ Tamamlanan
- Güvenlik altyapısı (rate limiting, CSRF, validation)
- Service layer (5 service sınıfı)
- Marshmallow validation (18 schema)
- Database migrations
- Audit trail sistemi
- Health check endpoints
- WebSocket real-time updates
- QR kod üretimi

### 🔄 Devam Eden
- API endpoints güncelleme
- Push notifications
- Reporting module

### ⏳ Planlanan
- Setup wizard
- Multi-language support
- GPS tracking
- Mobile apps (React Native)

---

## 🤝 Katkıda Bulunma

1. Fork yapın
2. Feature branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Commit yapın (`git commit -m 'Add amazing feature'`)
4. Push yapın (`git push origin feature/amazing-feature`)
5. Pull Request açın

---

## 📝 Lisans

Bu proje MIT lisansı altında lisanslanmıştır. Detaylar için [LICENSE](LICENSE) dosyasına bakın.

---

## 👨‍💻 Geliştirici

**Erkan ERDEM**

---

## 🙏 Teşekkürler

- Flask ekibine
- Tüm açık kaynak katkıda bulunanlara
- Test eden herkese

---

## 📞 İletişim

Sorularınız için:
- GitHub Issues
- Dokümantasyon dosyaları
- SISTEM_RAPOR.md

---

## 📈 Durum

**Versiyon:** 1.0.0  
**Durum:** %60 Tamamlandı  
**Production Ready:** Temel altyapı ✅  
**Son Güncelleme:** 2 Kasım 2025

---

**Keyifli kodlamalar! 🚀**
