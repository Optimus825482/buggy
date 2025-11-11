# 🚀 Shuttle Call - Coolify Deployment Rehberi

## 📋 Gereksinimler

- Coolify kurulu bir sunucu
- MySQL veritabanı
- Redis (opsiyonel, caching ve WebSocket için)
- Domain (SSL için)

## 🔧 Adım 1: Coolify'da Proje Oluştur

1. Coolify dashboard'una gir
2. **New Resource** → **Application** seç
3. **Git Repository** seç ve repo'nu bağla
4. **Build Pack**: Dockerfile seç

## 🗄️ Adım 2: MySQL Veritabanı Oluştur

1. Coolify'da **New Resource** → **Database** → **MySQL**
2. Veritabanı bilgilerini kaydet:
   - Host: `mysql-service-name` (Coolify internal network)
   - Port: `3306`
   - Database: `shuttlecall`
   - User: `shuttlecall_user`
   - Password: Güçlü bir şifre

## 🔴 Adım 3: Redis Oluştur (Opsiyonel)

1. **New Resource** → **Database** → **Redis**
2. Redis URL'i kaydet: `redis://redis-service:6379/0`

## ⚙️ Adım 4: Environment Variables Ayarla

Application → **Environment Variables** bölümünden ekle:

### Zorunlu Değişkenler

```bash
# Flask
FLASK_APP=run.py
FLASK_ENV=production
SECRET_KEY=your-super-secret-key-min-32-chars
DEBUG=False

# Database (Coolify MySQL service'inden)
DB_HOST=mysql-service-name
DB_PORT=3306
DB_NAME=shuttlecall
DB_USER=shuttlecall_user
DB_PASSWORD=your-db-password

# JWT
JWT_SECRET_KEY=your-jwt-secret-min-32-chars
JWT_ACCESS_TOKEN_EXPIRES=3600
JWT_REFRESH_TOKEN_EXPIRES=2592000

# CORS (Kendi domain'in)
CORS_ORIGINS=https://yourdomain.com

# Base URL
BASE_URL=https://yourdomain.com

# VAPID Keys (https://vapidkeys.com/)
VAPID_PUBLIC_KEY=your-vapid-public-key
VAPID_PRIVATE_KEY=your-vapid-private-key
VAPID_CLAIMS_EMAIL=mailto:admin@yourdomain.com

# App Settings
APP_NAME=Shuttle Call
APP_TIMEZONE=Asia/Nicosia
UPLOAD_FOLDER=app/static/uploads
MAX_CONTENT_LENGTH=16777216

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/shuttlecall.log

# Port (Coolify otomatik ayarlar)
PORT=3000
```

### İlk Kurulum İçin

```bash
# İlk deployment'ta veritabanını oluşturmak için
RESET_DB=true
```

⚠️ **ÖNEMLİ**: İlk deployment'tan sonra `RESET_DB=false` yap!

### Opsiyonel (Redis kullanıyorsan)

```bash
REDIS_URL=redis://redis-service:6379/0
SOCKETIO_MESSAGE_QUEUE=redis://redis-service:6379/0
RATELIMIT_STORAGE_URL=redis://redis-service:6379/1
```

## 🌐 Adım 5: Domain ve SSL

1. Application → **Domains** bölümüne git
2. Domain'ini ekle: `yourdomain.com`
3. SSL sertifikası otomatik oluşturulacak (Let's Encrypt)

## 🚀 Adım 6: Deploy

1. **Deploy** butonuna tıkla
2. Build loglarını takip et
3. Deployment tamamlandığında health check'i kontrol et

## 🔍 Adım 7: İlk Kontroller

### Health Check

```bash
curl https://yourdomain.com/health
```

Beklenen yanıt:
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2025-11-11T..."
}
```

### Admin Kullanıcı Oluştur

Coolify'da **Console** bölümünden:

```bash
python create_admin.py
```

## 📊 Adım 8: Persistent Storage (Opsiyonel)

Upload'lar için persistent volume:

1. Application → **Storages** bölümüne git
2. **Add Storage** tıkla
3. Mount path: `/app/app/static/uploads`
4. Redeploy

## 🔄 Güncelleme

Coolify otomatik deployment yapabilir:

1. Application → **General** → **Auto Deploy**
2. Branch seç (örn: `main`)
3. Her push'ta otomatik deploy olur

## 🐛 Troubleshooting

### Logları Görüntüle

Coolify dashboard → Application → **Logs**

### Database Bağlantı Hatası

```bash
# Console'dan test et
python check_railway_env.py
```

### Migration Hatası

```bash
# Console'dan manuel çalıştır
python fix_railway_migration.py
```

### Container Restart

Application → **Actions** → **Restart**

## 📝 Önemli Notlar

1. **İlk deployment**: `RESET_DB=true` kullan
2. **Sonraki deployments**: `RESET_DB=false` yap
3. **Backup**: MySQL'i düzenli yedekle
4. **Monitoring**: Coolify metrics'i takip et
5. **Logs**: Hata durumunda logları kontrol et

## 🔐 Güvenlik

- [ ] SECRET_KEY ve JWT_SECRET_KEY güçlü olmalı (min 32 karakter)
- [ ] Database şifresi güçlü olmalı
- [ ] CORS_ORIGINS sadece kendi domain'ini içermeli
- [ ] DEBUG=False production'da
- [ ] SSL sertifikası aktif olmalı

## 📞 Destek

Sorun yaşarsan:
1. Coolify loglarını kontrol et
2. Application console'dan script'leri manuel çalıştır
3. Health endpoint'i test et

## 🎉 Tamamlandı!

Uygulamanız şimdi Coolify'da çalışıyor:
- 🌐 Web: https://yourdomain.com
- 🔐 Admin: https://yourdomain.com/admin/login
- 📱 PWA: Tarayıcıdan "Ana Ekrana Ekle"
