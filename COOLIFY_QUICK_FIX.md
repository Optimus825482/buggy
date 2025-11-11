# 🔧 Coolify Quick Fix - Database Boş

## ❌ Sorun

```
Table 'buggycalldb.system_users' doesn't exist
```

Database boş, tablolar henüz oluşturulmamış.

## ✅ Çözüm

### 1. RESET_DB=true Yap

Coolify → Application → Environment Variables:

```env
RESET_DB=true
```

Bu ilk kurulumda database'i oluşturacak.

### 2. Redeploy

Coolify'da **Deploy** butonuna tıkla.

### 3. Beklenen Log Çıktısı

```
============================================================
🚀 Shuttle Call - Coolify Startup
============================================================
⏳ Checking environment variables...
✅ All 8 required variables are set

🔥 RESETTING DATABASE...
✅ Database reset completed

⏳ Fixing missing columns...
⚠️  system_users table doesn't exist yet
✅ Skipping column fix (will be created by migration)

⏳ Running migration fix...
✅ Migration fix completed

⏳ Creating initial data...
✅ Initial data created

🚀 Starting Gunicorn server...
[INFO] Listening at: http://0.0.0.0:8000
```

### 4. İlk Deployment Sonrası

✅ Health check test et:
```bash
curl https://shuttlecagri.com/health
```

✅ Admin oluştur:
```bash
# Coolify Console'dan
python create_admin.py
```

✅ **ÖNEMLİ:** RESET_DB'yi kapat:
```env
RESET_DB=false
```

Aksi halde her deployment'ta database sıfırlanır! ⚠️

## 📝 Özet

1. ✅ `RESET_DB=true` yap
2. ✅ Redeploy et
3. ✅ Health check kontrol et
4. ✅ Admin oluştur
5. ✅ `RESET_DB=false` yap
6. ✅ Test et

## 🎉 Tamamlandı!

Artık uygulamanız çalışıyor! 🚀
