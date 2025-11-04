# Railway Deployment Guide - Buggy Call

Bu doküman, Buggy Call sisteminin Railway platformuna MySQL veritabanı ile birlikte deploy edilmesi için adım adım rehberdir.

## 📋 Ön Gereksinimler

- Railway hesabı (https://railway.app)
- GitHub hesabı ve repository
- Git kurulu
- Python 3.9+ (local test için)

## 🚀 Deployment Adımları

### 1. Railway Projesi Oluşturma

1. Railway'e giriş yapın: https://railway.app
2. "New Project" butonuna tıklayın
3. "Deploy from GitHub repo" seçeneğini seçin
4. Buggy Call repository'sini seçin
5. Proje adını belirleyin (örn: "buggy-call-production")

### 2. MySQL Database Ekleme

1. Railway dashboard'da projenize gidin
2. "New" butonuna tıklayın
3. "Database" → "Add MySQL" seçin
4. MySQL servisi otomatik olarak oluşturulacak
5. MySQL servisine tıklayın ve "Variables" tab'ına gidin
6. `MYSQL_PUBLIC_URL` değerini kopyalayın

**Örnek MYSQL_PUBLIC_URL formatı:**
```
mysql://root:QwArzGTWhlXgDWHcPhttYQYArhhUVsHw@caboose.proxy.rlwy.net:44173/railway
```

### 3. Environment Variables Ayarlama

Railway dashboard'da application servisinize gidin ve "Variables" tab'ına tıklayın. Aşağıdaki değişkenleri ekleyin:

#### Zorunlu Değişkenler

```bash
# Flask Configuration
FLASK_ENV=production
FLASK_APP=wsgi.py
DEBUG=False

# Security Keys (ÖNEMLİ: Güçlü key'ler oluşturun!)
SECRET_KEY=<güçlü-random-key>
JWT_SECRET_KEY=<güçlü-jwt-key>

# Database (Railway otomatik sağlar)
MYSQL_PUBLIC_URL=<mysql-connection-string>

# CORS (Railway app URL'inizi ekleyin)
CORS_ORIGINS=https://your-app.railway.app

# Application
APP_NAME=Buggy Call
BASE_URL=https://your-app.railway.app
```

#### Güçlü Key Oluşturma

Terminal'de çalıştırın:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

#### Opsiyonel Değişkenler

```bash
# JWT Configuration
JWT_ACCESS_TOKEN_EXPIRES=3600
JWT_REFRESH_TOKEN_EXPIRES=2592000

# Application Settings
APP_TIMEZONE=Europe/Istanbul

# Initial Data (İlk kurulum için)
INITIAL_HOTEL_NAME=My Hotel
INITIAL_ADMIN_USERNAME=admin
INITIAL_ADMIN_PASSWORD=Admin123!Strong
INITIAL_ADMIN_EMAIL=admin@myhotel.com
INITIAL_DRIVER_COUNT=3

# Logging
LOG_LEVEL=INFO
```

### 4. Deployment Başlatma

1. Environment variables'ları kaydettikten sonra
2. Railway otomatik olarak deploy işlemini başlatacak
3. "Deployments" tab'ından ilerlemeyi takip edin
4. Build ve deploy loglarını kontrol edin

### 5. Deployment Doğrulama

#### Health Check

Deploy tamamlandıktan sonra:

```bash
curl https://your-app.railway.app/health
```

Başarılı response:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00",
  "environment": "production",
  "checks": {
    "database": {
      "status": "healthy",
      "table_count": 10,
      "critical_tables_ok": true
    },
    "application": {
      "status": "healthy"
    }
  }
}
```

#### Admin Login Testi

1. Railway app URL'inizi tarayıcıda açın
2. Login sayfasına gidin
3. Default credentials ile giriş yapın:
   - Username: `admin`
   - Password: `.env.railway.example`'da belirlediğiniz password

#### Database Kontrolü

Railway dashboard'da MySQL servisine gidin:
- "Data" tab'ına tıklayın
- Tabloların oluşturulduğunu kontrol edin:
  - `hotel`
  - `system_user`
  - `location`
  - `buggy`
  - `buggy_request`
  - `audit_trail`
  - `session`

### 6. Domain Bağlama (Opsiyonel)

1. Railway dashboard'da application servisinize gidin
2. "Settings" tab'ına tıklayın
3. "Domains" bölümünde "Generate Domain" veya "Custom Domain" seçin
4. Custom domain için DNS ayarlarını yapın
5. `CORS_ORIGINS` ve `BASE_URL` environment variables'ları güncelleyin

## 🔧 Troubleshooting

### Database Connection Hatası

**Sorun:** `Database connection failed`

**Çözüm:**
1. `MYSQL_PUBLIC_URL` doğru kopyalandığını kontrol edin
2. MySQL servisinin çalıştığını kontrol edin
3. Railway logs'u kontrol edin: `railway logs`

### Migration Hatası

**Sorun:** `Migration failed`

**Çözüm:**
1. Railway dashboard'da "Deployments" → "View Logs"
2. Migration hatalarını kontrol edin
3. Gerekirse manuel migration:
```bash
# Local'de Railway environment ile
railway run flask db upgrade
```

### Health Check Fail

**Sorun:** Health check 503 dönüyor

**Çözüm:**
1. Database bağlantısını kontrol edin
2. Logs'da hata mesajlarını arayın
3. Environment variables'ların doğru olduğunu kontrol edin

### Application Crash

**Sorun:** Uygulama başlamıyor

**Çözüm:**
1. Railway logs'u kontrol edin
2. `SECRET_KEY` ve `JWT_SECRET_KEY` ayarlandığını kontrol edin
3. Python dependencies'lerin yüklendiğini kontrol edin

## 📊 Monitoring

### Railway Logs

Real-time logs görüntüleme:
```bash
railway logs
```

veya Railway dashboard'da "Deployments" → "View Logs"

### Metrics

Railway dashboard'da:
- CPU usage
- Memory usage
- Network traffic
- Request count

### Health Check Monitoring

Periyodik health check için external monitoring servisi kullanın:
- UptimeRobot
- Pingdom
- StatusCake

Health check URL: `https://your-app.railway.app/health`

## 🔄 Güncelleme ve Rollback

### Yeni Version Deploy

1. GitHub'a kod push edin:
```bash
git add .
git commit -m "Update: description"
git push origin main
```

2. Railway otomatik olarak yeni deploy başlatır
3. Health check başarılı olursa yeni version aktif olur

### Rollback

Railway dashboard'da:
1. "Deployments" tab'ına gidin
2. Önceki başarılı deployment'ı bulun
3. "..." menüsünden "Redeploy" seçin

## 🔐 Güvenlik Önerileri

### Production Checklist

- [ ] Güçlü `SECRET_KEY` ve `JWT_SECRET_KEY` kullanıldı
- [ ] Default admin password değiştirildi
- [ ] `DEBUG=False` ayarlandı
- [ ] CORS origins sadece gerçek domain'leri içeriyor
- [ ] HTTPS zorunlu (Railway otomatik sağlar)
- [ ] Database credentials güvenli
- [ ] Environment variables Railway'de saklanıyor (kod içinde değil)

### Düzenli Bakım

- Admin password'ü düzenli değiştirin
- Railway logs'u düzenli kontrol edin
- Database backup stratejisi oluşturun
- Güvenlik güncellemelerini takip edin

## 📞 Destek

### Railway Destek

- Documentation: https://docs.railway.app
- Discord: https://discord.gg/railway
- Status: https://status.railway.app

### Buggy Call

- GitHub Issues: Repository issues sayfası
- Documentation: README.md

## 🎯 Sonraki Adımlar

1. **QR Kodları Oluşturun**
   - Admin panel'den lokasyonlar için QR kodları generate edin
   - QR kodları yazdırın ve lokasyonlara yerleştirin

2. **Driver'ları Ekleyin**
   - Admin panel'den driver kullanıcıları oluşturun
   - Buggy'leri driver'lara atayın

3. **Test Edin**
   - QR kod tarama test edin
   - Buggy çağrı sistemi test edin
   - WebSocket real-time güncellemeleri test edin

4. **Monitoring Kurun**
   - External health check monitoring
   - Error tracking (Sentry gibi)
   - Analytics (opsiyonel)

5. **Backup Stratejisi**
   - Railway database backup'ları aktif edin
   - Düzenli backup schedule oluşturun

## 📝 Notlar

- Railway free tier limitleri: https://railway.app/pricing
- MySQL database boyutu ve connection limitleri kontrol edin
- Production'da Redis eklemek için Railway'e Redis servisi ekleyin
- Scaling için worker count artırılabilir (Procfile'da `-w` parametresi)

---

**Başarılı Deployment! 🎉**

Sorularınız için GitHub Issues kullanın veya documentation'ı kontrol edin.
