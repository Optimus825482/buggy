# 🚀 Shuttle Call - Coolify Hızlı Başlangıç

## ⚡ 5 Dakikada Deploy

### 1️⃣ Coolify'da Yeni Uygulama

```
New Resource → Application → Git Repository
Build Pack: Dockerfile
```

### 2️⃣ MySQL Ekle

```
New Resource → Database → MySQL 8.0
Database Name: shuttlecall
Username: shuttlecall_user
Password: [güçlü şifre]
```

### 3️⃣ Environment Variables

Application → Environment Variables → Bulk Edit:

```env
FLASK_APP=run.py
FLASK_ENV=production
SECRET_KEY=your-32-char-secret-key-here
DEBUG=False

DB_HOST=mysql-service-name
DB_PORT=3306
DB_NAME=shuttlecall
DB_USER=shuttlecall_user
DB_PASSWORD=your-db-password

JWT_SECRET_KEY=your-32-char-jwt-secret-here
JWT_ACCESS_TOKEN_EXPIRES=3600

CORS_ORIGINS=https://yourdomain.com
BASE_URL=https://yourdomain.com

VAPID_PUBLIC_KEY=your-vapid-public-key
VAPID_PRIVATE_KEY=your-vapid-private-key
VAPID_CLAIMS_EMAIL=mailto:admin@yourdomain.com

APP_NAME=Shuttle Call
APP_TIMEZONE=Asia/Nicosia
LOG_LEVEL=INFO
PORT=3000

RESET_DB=true
```

⚠️ **İlk deployment'tan sonra `RESET_DB=false` yap!**

### 4️⃣ Domain Ekle

```
Application → Domains → Add Domain
Domain: yourdomain.com
SSL: Auto (Let's Encrypt)
```

### 5️⃣ Deploy

```
Deploy butonuna tıkla
Logları takip et
Health check: https://yourdomain.com/health
```

## 🔑 VAPID Keys Oluştur

https://vapidkeys.com/ adresine git ve keys oluştur.

## 👤 Admin Kullanıcı Oluştur

Coolify Console'dan:

```bash
python create_admin.py
```

## ✅ Test Et

```bash
# Health check
curl https://yourdomain.com/health

# Admin login
https://yourdomain.com/admin/login
```

## 📦 Persistent Storage (Opsiyonel)

```
Application → Storages → Add Storage
Mount Path: /app/app/static/uploads
```

## 🔄 Auto Deploy

```
Application → General → Auto Deploy
Branch: main
```

## 🐛 Sorun Giderme

### Logları Görüntüle
```
Application → Logs
```

### Database Test
```bash
# Console'dan
python check_railway_env.py
```

### Manuel Migration
```bash
# Console'dan
python fix_railway_migration.py
```

## 📚 Detaylı Dokümantasyon

Daha fazla bilgi için: `COOLIFY_DEPLOYMENT.md`

## 🎉 Tamamlandı!

Uygulamanız hazır:
- 🌐 Web: https://yourdomain.com
- 🔐 Admin: https://yourdomain.com/admin/login
- 📱 PWA: Tarayıcıdan "Ana Ekrana Ekle"
