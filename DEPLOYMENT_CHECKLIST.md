# ✅ Railway Deployment Checklist

## Hazırlık (Tamamlandı ✅)

- [x] Migration fix scripti eklendi (`fix_railway_migration.py`)
- [x] Environment check scripti eklendi (`check_railway_env.py`)
- [x] Railway başlangıç scripti eklendi (`railway_start.sh`)
- [x] Procfile güncellendi
- [x] Deployment guide hazırlandı (`RAILWAY_DEPLOYMENT.md`)
- [x] Git commit yapıldı

## Deployment Öncesi

### 1. Railway Environment Variables Kontrolü

Railway dashboard'da şunları kontrol et:

```bash
✅ MYSQL_PUBLIC_URL
✅ MYSQLHOST
✅ MYSQLPORT
✅ MYSQLUSER
✅ MYSQLPASSWORD
✅ MYSQLDATABASE
✅ SECRET_KEY
✅ JWT_SECRET_KEY
```

### 2. Git Push

```bash
git push origin main
# veya
railway up
```

### 3. Deployment Takibi

Railway dashboard'dan:
1. Deployments sekmesine git
2. Son deployment'ı aç
3. Logs'u izle

### 4. Başarı Kontrolü

Log'larda şunları görmeli:

```
✅ Environment check passed
✅ Migration fix completed  
✅ Database connection successful
🚀 Starting Gunicorn server...
```

## Deployment Sonrası

### 1. Health Check

```bash
curl https://your-app.railway.app/health
```

Beklenen yanıt:
```json
{
  "status": "healthy",
  "database": "connected"
}
```

### 2. Admin Login Test

1. `https://your-app.railway.app/admin/login` aç
2. Admin credentials ile giriş yap
3. Dashboard'un yüklendiğini kontrol et

### 3. Database Kontrolü

Railway shell'de:

```bash
railway shell
python check_railway_env.py
python fix_railway_migration.py
```

## Sorun Giderme

### Migration Hatası Devam Ediyorsa

```bash
# Railway shell'e bağlan
railway shell

# Manuel fix
python fix_railway_migration.py

# Tabloları kontrol et
python -c "from app import create_app, db; app = create_app('production'); app.app_context().push(); from sqlalchemy import inspect; inspector = inspect(db.engine); print(inspector.get_table_names())"
```

### Environment Variable Eksik

```bash
railway run python check_railway_env.py
```

Eksik olanları Railway dashboard'dan ekle.

### Database Connection Hatası

1. MySQL service'in çalıştığını kontrol et
2. MYSQL_PUBLIC_URL'in doğru olduğunu kontrol et
3. Railway MySQL service'i restart et

## Rollback Planı

Sorun çıkarsa:

1. Railway dashboard → Deployments
2. Önceki başarılı deployment'ı bul
3. "Redeploy" butonuna tıkla

## Notlar

- Her deployment otomatik migration fix çalıştırır
- Environment variables değişirse restart gerekir
- Logs her zaman kontrol edilmeli
- Health endpoint düzenli izlenmeli

## İletişim

Sorun yaşarsan:
1. `RAILWAY_DEPLOYMENT.md` dosyasına bak
2. Railway logs'u kontrol et
3. Database connection'ı test et
