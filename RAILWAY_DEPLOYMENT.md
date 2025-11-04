# 🚂 Railway Deployment Guide

## Sorun Çözümü

Railway'de karşılaşılan migration sorunları için otomatik düzeltme sistemi eklendi.

### Yapılan Değişiklikler

1. **fix_railway_migration.py**: Veritabanı şemasını otomatik düzeltir
   - Eksik kolonları ekler (`push_subscription_date`, vb.)
   - Alembic version'ı günceller
   - Hata durumunda detaylı log verir

2. **railway_start.sh**: Railway başlangıç scripti
   - Environment variable kontrolü
   - Migration fix
   - Gunicorn başlatma

3. **check_railway_env.py**: Environment variable kontrolü
   - Gerekli değişkenleri kontrol eder
   - Eksik olanları raporlar

## Railway Deployment Adımları

### 1. Environment Variables

Railway dashboard'da şu değişkenleri ayarla:

```bash
# MySQL (Railway MySQL service'den otomatik gelir)
MYSQL_PUBLIC_URL=mysql://user:pass@host:port/database
MYSQLHOST=mysql.railway.internal
MYSQLPORT=3306
MYSQLUSER=root
MYSQLPASSWORD=***
MYSQLDATABASE=railway

# Flask
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here
FLASK_ENV=production

# Optional - Push Notifications
VAPID_PUBLIC_KEY=your-vapid-public-key
VAPID_PRIVATE_KEY=your-vapid-private-key
VAPID_CLAIMS_EMAIL=mailto:admin@buggycall.com
```

### 2. Deploy

```bash
# Git push ile otomatik deploy
git add .
git commit -m "Fix Railway migration"
git push

# Railway CLI ile deploy
railway up
```

### 3. Logs Kontrolü

```bash
# Railway CLI ile log izle
railway logs

# Ya da Railway dashboard'dan:
# Project → Deployments → View Logs
```

## Sorun Giderme

### Migration Hatası

Eğer hala migration hatası alıyorsan:

```bash
# Railway shell'e bağlan
railway shell

# Migration fix'i manuel çalıştır
python fix_railway_migration.py

# Sonucu kontrol et
python -c "from app import create_app, db; app = create_app('production'); app.app_context().push(); print(db.engine.table_names())"
```

### Environment Variable Eksik

```bash
# Kontrol et
railway run python check_railway_env.py

# Railway dashboard'dan ekle:
# Project → Variables → New Variable
```

### Database Connection Hatası

```bash
# MySQL service'in çalıştığını kontrol et
railway status

# MySQL logs
railway logs --service mysql

# Connection test
railway run python -c "from app import create_app, db; app = create_app('production'); app.app_context().push(); db.session.execute('SELECT 1')"
```

## Önemli Notlar

1. **Procfile**: `bash railway_start.sh` kullanıyor
2. **Migration**: Her deployment'ta otomatik çalışır
3. **Rollback**: Sorun olursa Railway'den önceki deployment'a dön
4. **Logs**: Her zaman log'ları kontrol et

## Başarı Kriterleri

Deployment başarılı olduğunda göreceğin loglar:

```
✅ Environment check passed
✅ Migration fix completed
✅ Database connection successful
✅ All required variables are set
🚀 Starting Gunicorn server...
```

## Destek

Sorun yaşarsan:
1. Railway logs'u kontrol et
2. `check_railway_env.py` çalıştır
3. MySQL service'in aktif olduğunu doğrula
4. Environment variables'ı kontrol et
