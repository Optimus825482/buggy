# Railway MySQL Connection Setup

## 🔍 MySQL Bağlantı Bilgilerini Bulma

### Yöntem 1: MYSQL_PUBLIC_URL (Önerilen)

Railway dashboard'da:
1. MySQL servisinize tıklayın
2. **"Variables"** tab'ına gidin
3. **"MYSQL_PUBLIC_URL"** değişkenini bulun

Tam format:
```
mysql://root:wkLQSWfxaDMXvrBiaehnWKzphKOEXgKx@containers-us-west-xxx.railway.app:6543/railway
```

### Yöntem 2: Ayrı Değişkenler

Eğer MYSQL_PUBLIC_URL yoksa, şu değişkenleri bulun:

```bash
MYSQLHOST=containers-us-west-xxx.railway.app
MYSQLPORT=6543
MYSQLDATABASE=railway
MYSQLUSER=root
MYSQLPASSWORD=wkLQSWfxaDMXvrBiaehnWKzphKOEXgKx
```

Bu değişkenlerden tam URL'i oluşturun:
```
mysql://MYSQLUSER:MYSQLPASSWORD@MYSQLHOST:MYSQLPORT/MYSQLDATABASE
```

## ⚙️ Railway'de Environment Variables Ayarlama

### Application Servisinizde

Railway dashboard'da **Application** servisinize gidin → **Variables** tab:

```bash
# Flask Configuration
FLASK_ENV=production
FLASK_APP=wsgi.py
DEBUG=False
RAILWAY_ENVIRONMENT=production

# Security Keys (ÖNEMLİ: Güçlü key'ler oluşturun!)
SECRET_KEY=<python -c "import secrets; print(secrets.token_urlsafe(32))">
JWT_SECRET_KEY=<python -c "import secrets; print(secrets.token_urlsafe(32))">

# Database - TAM URL'i buraya yapıştırın
MYSQL_PUBLIC_URL=mysql://root:wkLQSWfxaDMXvrBiaehnWKzphKOEXgKx@containers-us-west-xxx.railway.app:6543/railway

# CORS - Railway app URL'inizi ekleyin
CORS_ORIGINS=https://your-app-name.up.railway.app

# Application
APP_NAME=Buggy Call
BASE_URL=https://your-app-name.up.railway.app
APP_TIMEZONE=Europe/Istanbul

# Initial Data (Opsiyonel)
INITIAL_HOTEL_NAME=My Hotel
INITIAL_ADMIN_USERNAME=admin
INITIAL_ADMIN_PASSWORD=Admin123!Strong
INITIAL_ADMIN_EMAIL=admin@myhotel.com
INITIAL_DRIVER_COUNT=3
```

## 🔗 MySQL URL Formatı

### Doğru Format:
```
mysql://USER:PASSWORD@HOST:PORT/DATABASE
```

### Sizin Bilgileriniz:
```
USER: root
PASSWORD: wkLQSWfxaDMXvrBiaehnWKzphKOEXgKx
HOST: [Railway'den alın - örn: containers-us-west-xxx.railway.app]
PORT: [Railway'den alın - örn: 6543]
DATABASE: railway
```

### Tam URL Örneği:
```
mysql://root:wkLQSWfxaDMXvrBiaehnWKzphKOEXgKx@containers-us-west-123.railway.app:6543/railway
```

## 🚨 Eksik Host Sorunu

Eğer URL'iniz şöyle görünüyorsa:
```
mysql://root:wkLQSWfxaDMXvrBiaehnWKzphKOEXgKx@:/railway
```

**HOST ve PORT eksik!** Railway dashboard'dan bulun:

1. MySQL servisine tıklayın
2. **"Connect"** tab'ına gidin
3. **"Public Networking"** bölümünü açın
4. **Host** ve **Port** bilgilerini kopyalayın

## ✅ Doğrulama

### 1. Railway Logs Kontrol

Deploy sonrası logs'da şunu görmelisiniz:
```
Railway MySQL configured: containers-us-west-xxx.railway.app:6543
✅ Database connection successful
✅ Database health check passed
```

### 2. Health Check

```bash
curl https://your-app.railway.app/health
```

Başarılı response:
```json
{
  "status": "healthy",
  "checks": {
    "database": {
      "status": "healthy",
      "table_count": 10
    }
  }
}
```

### 3. Verification Script

```bash
python scripts/verify_deployment.py https://your-app.railway.app
```

## 🔧 Troubleshooting

### "Database connection failed"

**Sorun:** Host bilgisi eksik

**Çözüm:**
1. Railway MySQL servisine gidin
2. "Connect" → "Public Networking"
3. Host ve Port'u kopyalayın
4. Tam URL'i oluşturun
5. Application servisinde MYSQL_PUBLIC_URL'i güncelleyin

### "Could not connect to MySQL server"

**Sorun:** Port veya host yanlış

**Çözüm:**
1. Railway MySQL servisinde "Variables" tab'ını kontrol edin
2. MYSQLHOST ve MYSQLPORT değerlerini doğrulayın
3. Public networking aktif mi kontrol edin

### "Access denied for user"

**Sorun:** Password yanlış

**Çözüm:**
1. Railway MySQL servisinde MYSQLPASSWORD'ü kontrol edin
2. URL'de özel karakterler varsa encode edin
3. Yeni password oluşturulmuş olabilir, güncel olanı alın

## 📝 Örnek Tam Konfigürasyon

Railway Application Variables:

```bash
FLASK_ENV=production
DEBUG=False
RAILWAY_ENVIRONMENT=production
SECRET_KEY=xK9mP2nQ5vR8wT1yU4zB7cD0eF3gH6jL
JWT_SECRET_KEY=aB2cD4eF6gH8iJ0kL1mN3oP5qR7sT9uV
MYSQL_PUBLIC_URL=mysql://root:wkLQSWfxaDMXvrBiaehnWKzphKOEXgKx@containers-us-west-123.railway.app:6543/railway
CORS_ORIGINS=https://buggycall-production.up.railway.app
BASE_URL=https://buggycall-production.up.railway.app
APP_NAME=Buggy Call
INITIAL_ADMIN_PASSWORD=MySecurePassword123!
```

## 🎯 Sonraki Adımlar

1. ✅ Tam MYSQL_PUBLIC_URL'i Railway'den alın
2. ✅ Application servisinde environment variables'ı ayarlayın
3. ✅ Deploy'u tetikleyin (otomatik başlar)
4. ✅ Logs'u kontrol edin
5. ✅ Health check yapın
6. ✅ Admin login test edin

---

**Not:** Railway MySQL servisi her yeniden başlatıldığında host/port değişebilir. Bu yüzden MYSQL_PUBLIC_URL değişkenini kullanmak en iyisidir - Railway otomatik günceller.
