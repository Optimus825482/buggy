# Environment Setup Guide

Bu doküman local development ve production environment'ların nasıl ayarlanacağını açıklar.

## 🔧 Local Development Setup

### 1. Environment Dosyasını Oluştur

```bash
# .env.example dosyasını kopyala
cp .env.example .env
```

### 2. Database Ayarlarını Düzenle

`.env` dosyasını açın ve database bilgilerinizi girin:

```bash
DB_HOST=localhost
DB_PORT=3306
DB_NAME=buggycalldb
DB_USER=your-username
DB_PASSWORD=your-password
```

### 3. Local Database Oluştur

```bash
# MySQL'e bağlan
mysql -u root -p

# Database oluştur
CREATE DATABASE buggycalldb CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
EXIT;
```

### 4. Database'i Initialize Et

```bash
# Virtual environment aktif et
source venv/bin/activate  # Linux/Mac
# veya
venv\Scripts\activate  # Windows

# Database tablolarını oluştur
python scripts/init_db.py
```

### 5. Uygulamayı Çalıştır

```bash
# Development server
python run.py

# Veya Flask CLI ile
flask run
```

Uygulama http://localhost:5000 adresinde çalışacak.

## 🚀 Production (Railway) Setup

### 1. GitHub'a Push

```bash
git add .
git commit -m "Your changes"
git push origin main
```

**ÖNEMLİ:** `.env` dosyası `.gitignore`'da olduğu için GitHub'a GİTMEZ. Bu güvenlik için önemlidir!

### 2. Railway'de Environment Variables Ayarla

Railway dashboard'da **Variables** tab'ına gidin ve şunları ekleyin:

```bash
# Flask
FLASK_ENV=production
FLASK_APP=wsgi.py
DEBUG=False
RAILWAY_ENVIRONMENT=production

# Security (Güçlü key'ler oluşturun!)
SECRET_KEY=<güçlü-random-key>
JWT_SECRET_KEY=<güçlü-jwt-key>

# Database (Railway otomatik sağlar)
MYSQL_PUBLIC_URL=<railway-mysql-connection-string>

# CORS (Railway app URL'iniz)
CORS_ORIGINS=https://your-app.railway.app

# Application
APP_NAME=Buggy Call
BASE_URL=https://your-app.railway.app
```

### 3. Güçlü Key Oluşturma

```bash
# Terminal'de çalıştırın
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Bu komutu iki kez çalıştırın:
- Birincisi için: `SECRET_KEY`
- İkincisi için: `JWT_SECRET_KEY`

### 4. Deploy

Railway otomatik olarak deploy edecek! Logs'u takip edin.

## 📁 Environment Dosyaları

### `.env` (Local Development)
- ✅ Local database ayarları
- ✅ Development mode
- ✅ Debug enabled
- ❌ GitHub'a GİTMEZ (.gitignore'da)

### `.env.example` (Template)
- ✅ Local development template
- ✅ GitHub'a gider
- ✅ Yeni developer'lar için örnek

### `.env.railway.example` (Production Template)
- ✅ Railway deployment template
- ✅ Production ayarları örneği
- ✅ GitHub'a gider

## 🔄 Environment Değiştirme

### Local → Production

Railway'de environment variables ayarlayın. `.env` dosyasını Railway'e yüklemeyin!

### Production → Local

```bash
# .env dosyasını local ayarlara geri çevir
FLASK_ENV=development
DEBUG=True
DB_HOST=localhost
```

## ⚠️ Önemli Notlar

### 1. .env Dosyası Asla GitHub'a Gitmesin!

```bash
# .gitignore'da olduğunu kontrol edin
cat .gitignore | grep .env
```

Çıktı:
```
.env
.env.local
.env.*.local
```

### 2. Production'da .env Kullanmayın!

Railway'de **Variables** tab'ından environment variables ayarlayın.

### 3. Güvenlik

- ❌ Asla production credentials'ları `.env` dosyasına yazmayın
- ❌ Asla `.env` dosyasını commit etmeyin
- ✅ Her environment için farklı SECRET_KEY kullanın
- ✅ Production'da güçlü password'ler kullanın

### 4. Database Bağlantıları

**Local:**
```bash
DB_HOST=localhost
DB_NAME=buggycalldb
```

**Railway:**
```bash
MYSQL_PUBLIC_URL=mysql://user:pass@host:port/railway
```

Railway'de `MYSQL_PUBLIC_URL` varsa, diğer DB_* değişkenlerini override eder.

## 🧪 Test Etme

### Local Test

```bash
# Health check
curl http://localhost:5000/health

# Database test
python scripts/run_migrations.py status
```

### Production Test

```bash
# Health check
curl https://your-app.railway.app/health

# Verification
python scripts/verify_deployment.py https://your-app.railway.app
```

## 🆘 Sorun Giderme

### "Database connection failed" (Local)

1. MySQL çalışıyor mu kontrol edin:
```bash
mysql -u root -p
```

2. Database var mı kontrol edin:
```sql
SHOW DATABASES;
```

3. `.env` dosyasındaki credentials doğru mu kontrol edin

### "Database connection failed" (Railway)

1. Railway'de MySQL servisi çalışıyor mu kontrol edin
2. `MYSQL_PUBLIC_URL` doğru kopyalandı mı kontrol edin
3. Railway logs'u kontrol edin

### ".env değişiklikleri uygulanmıyor"

```bash
# Uygulamayı yeniden başlatın
# Ctrl+C ile durdurun, sonra tekrar çalıştırın
python run.py
```

## 📚 Daha Fazla Bilgi

- **Local Development**: `README.md`
- **Railway Deployment**: `RAILWAY_DEPLOYMENT.md`
- **Production Setup**: `RAILWAY_SETUP_COMPLETE.md`

---

**Önemli:** `.env` dosyası her developer'ın kendi local ayarlarını içerir ve GitHub'a gitmez. Bu güvenlik ve esneklik için önemlidir!
