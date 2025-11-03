# Railway Environment Variables - Buggy Call

Railway dashboard'da application servisinizde şu environment variables'ları mutlaka set etmelisiniz:

## ✅ Zorunlu (CRITICAL) Environment Variables

```bash
# Flask Environment
FLASK_ENV=production
FLASK_APP=wsgi.py
DEBUG=False

# Security Keys (MUTLAKA DEĞİŞTİRİN!)
# Oluşturmak için: python -c "import secrets; print(secrets.token_urlsafe(32))"
SECRET_KEY=your-very-long-random-secret-key-here
JWT_SECRET_KEY=your-very-long-jwt-secret-key-here

# Database (Railway MySQL servisinden alın)
# MySQL servisine tıklayın -> Variables -> MYSQL_PUBLIC_URL'yi kopyalayın
MYSQL_PUBLIC_URL=mysql://root:PASSWORD@HOST:PORT/railway

# Application URL (Railway'den domain aldıktan sonra güncelleyin)
BASE_URL=https://your-app-name.up.railway.app
CORS_ORIGINS=https://your-app-name.up.railway.app

# Application Name
APP_NAME=Buggy Call
```

## 🔧 Opsiyonel Ama Önerilen Variables

```bash
# Timezone
APP_TIMEZONE=Europe/Istanbul

# JWT Token Süreleri (saniye cinsinden)
JWT_ACCESS_TOKEN_EXPIRES=3600           # 1 saat
JWT_REFRESH_TOKEN_EXPIRES=2592000       # 30 gün

# Initial Setup (İlk deployment için)
INITIAL_HOTEL_NAME=My Hotel
INITIAL_ADMIN_USERNAME=admin
INITIAL_ADMIN_PASSWORD=VeryStrong123!Pass
INITIAL_ADMIN_EMAIL=admin@myhotel.com
INITIAL_DRIVER_COUNT=3

# Logging
LOG_LEVEL=INFO
```

## 🚀 Railway Deployment Adımları

### 1. MySQL Database Ekleme
1. Railway dashboard'da projenize gidin
2. "New" → "Database" → "MySQL" seçin
3. MySQL servisi oluşturulduktan sonra "Variables" tab'ına gidin
4. `MYSQL_PUBLIC_URL` değerini kopyalayın

### 2. Application Variables Ekleme
1. Application servisinize gidin
2. "Variables" tab'ına tıklayın
3. "New Variable" butonuyla yukarıdaki tüm variables'ları ekleyin
4. Özellikle şunlara dikkat edin:
   - `SECRET_KEY` ve `JWT_SECRET_KEY`: Güçlü random key'ler oluşturun
   - `MYSQL_PUBLIC_URL`: MySQL servisinden aldığınız değeri yapıştırın
   - `FLASK_ENV`: "production" olmalı
   - `DEBUG`: "False" olmalı

### 3. Deploy Tetikleme,

mysql://root:bHvgngTKQKWZkReGmedtcVPnyhSMhEVf@shortline.proxy.rlwy.net:33121/railway

Variables'ları kaydettikten sonra Railway otomatik deploy başlatacak. Logs'u takip edin:

**Beklenen Log Sırası:**
```
==> Building...
==> Installing dependencies...
==> Running migrations...
🚀 Buggy Call - Railway Auto Migration
Running migrations to: head
✅ Migrations completed successfully
==> Starting application...
Buggy Call starting - Environment: production
✅ Database connection successful
```

### 4. Health Check Kontrolü
Deploy tamamlandıktan sonra test edin:

```bash
curl https://your-app-name.up.railway.app/health
```

**Başarılı Response:**
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
    }
  }
}
```

## 🔍 Troubleshooting

### Sorun 1: Health Check Başarısız (503)

**Olası Nedenler:**
- MySQL bağlantısı başarısız
- Environment variables eksik
- Migration çalışmadı

**Çözüm:**
1. Railway logs'u kontrol edin: "Deployments" → "View Logs"
2. MySQL servisinin çalıştığını kontrol edin
3. `MYSQL_PUBLIC_URL` doğru kopyalandığından emin olun
4. Loglar'da "Database connection failed" hatası varsa:
   ```
   # MySQL servisi Variables'dan MYSQL_PUBLIC_URL'yi tekrar kopyalayın
   # Format: mysql://root:PASSWORD@HOST:PORT/railway
   ```

### Sorun 2: "No module named 'MySQLdb'" Hatası

**Çözüm:**
Bu hata artık gelmemeli çünkü `pymysql` kullanıyoruz. Ancak gelirse:
- `requirements.txt`'te `pymysql` olduğundan emin olun
- Redeploy edin

### Sorun 3: Migration Hatası

**Log'da göreceğiniz:**
```
❌ Migration failed: ...
```

**Çözüm:**
1. MySQL servisinin boş olduğundan emin olun (ilk deploy için)
2. Veya Railway dashboard'da MySQL Data tab'ından tabloları silin
3. Redeploy edin

### Sorun 4: Application Crash / Restart Loop

**Çözüm:**
1. Logs'da hata mesajını bulun
2. Genelde nedeni:
   - `SECRET_KEY` veya `JWT_SECRET_KEY` eksik
   - `FLASK_ENV` yanlış set edilmiş
   - `MYSQL_PUBLIC_URL` hatalı

3. Variables'ları düzeltin ve redeploy edin

## 📊 Deployment Sonrası Kontrol Listesi

Deploy başarılı olduktan sonra:

- [ ] `/health` endpoint 200 dönüyor
- [ ] `/ping` endpoint çalışıyor
- [ ] Admin login sayfası açılıyor
- [ ] Admin credentials ile giriş yapılabiliyor
- [ ] MySQL'de tablolar oluşmuş (Railway MySQL Data tab)
- [ ] Logs'da kritik hata yok

## 🔐 Güvenlik Kontrolleri

Production'da mutlaka kontrol edin:

- [ ] `SECRET_KEY` güçlü ve unique
- [ ] `JWT_SECRET_KEY` güçlü ve unique
- [ ] `DEBUG=False`
- [ ] `FLASK_ENV=production`
- [ ] Default admin password değiştirildi
- [ ] `CORS_ORIGINS` sadece gerçek domain'i içeriyor
- [ ] MySQL credentials güvenli

## 🚨 ÖNEMLİ NOTLAR

1. **SECRET_KEY Oluşturma:**
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```
   Her deployment için farklı key kullanın!

2. **MySQL URL Formatı:**
   ```
   mysql://root:PASSWORD@HOST:PORT/railway
   ```
   Railway'den aldığınız URL'yi olduğu gibi kopyalayın, değiştirmeyin!

3. **CORS Origins:**
   Railway domain aldıktan sonra `CORS_ORIGINS`'i güncelleyin:
   ```
   CORS_ORIGINS=https://your-custom-domain.com
   ```

4. **İlk Admin Password:**
   `INITIAL_ADMIN_PASSWORD` ile belirlediğiniz password'ü not edin!
   İlk girişten sonra mutlaka değiştirin.

## 📝 Örnek Variables Konfigürasyonu

```bash
# 1. Güçlü key'ler oluşturun
SECRET_KEY=8xN9K2mP4qR7sT0vW3yZ6bC9eF2hJ5kM8nQ1rT4uW7xA0cD3fG6iL9oP2sV5yB8e
JWT_SECRET_KEY=3yB6eH9kN2qT5wZ8cF1iL4oR7uX0aD3gJ6mP9sV2xC5fI8lO1rU4xA7dG0jM3pS6

# 2. MySQL URL'yi Railway'den kopyalayın
MYSQL_PUBLIC_URL=mysql://root:aBcD1234eFgH5678@containers-us-west-123.railway.app:5432/railway

# 3. Diğer settings
FLASK_ENV=production
DEBUG=False
BASE_URL=https://buggycall-prod.up.railway.app
CORS_ORIGINS=https://buggycall-prod.up.railway.app
APP_NAME=Buggy Call
APP_TIMEZONE=Europe/Istanbul

# 4. Initial setup
INITIAL_HOTEL_NAME=Seaside Resort
INITIAL_ADMIN_USERNAME=admin
INITIAL_ADMIN_PASSWORD=Admin@123Strong!
INITIAL_ADMIN_EMAIL=admin@seasideresort.com
INITIAL_DRIVER_COUNT=3
```

## 🆘 Destek

Sorun devam ederse:
1. Railway logs'un tamamını alın
2. `/health` endpoint response'unu kontrol edin
3. GitHub Issues'da detaylı açıklama ile issue açın

---

**Deployment başarıyla tamamlandıktan sonra bu dosyayı güvenli bir yerde saklayın!**
Environment variables'ları içerdiği için hassas bilgi içerir.
