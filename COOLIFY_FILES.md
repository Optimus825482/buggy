# 📁 Coolify Deployment Dosyaları

## ✅ Oluşturulan Dosyalar

### 🐳 Docker Yapılandırması
- **Dockerfile** - Coolify için production Docker image
- **docker-compose.yml** - Local test için (Coolify'da kullanılmaz)
- **.dockerignore** - Docker build'de ignore edilecek dosyalar

### 🚀 Deployment Scripts
- **coolify_start.sh** - Coolify startup script (migration + gunicorn)
- **wsgi.py** - Zaten mevcut, Gunicorn entry point

### ⚙️ Yapılandırma
- **.env.coolify.example** - Coolify environment variables şablonu
- **.gitignore** - Güncellendi (Docker/Coolify dosyaları eklendi)

### 📚 Dokümantasyon
- **COOLIFY_DEPLOYMENT.md** - Detaylı deployment rehberi
- **COOLIFY_QUICKSTART.md** - 5 dakikada deploy rehberi
- **COOLIFY_FILES.md** - Bu dosya

### 🏥 Health Check
- **app/routes/api.py** - `/health` endpoint eklendi

## 🔧 Coolify'da Yapılacaklar

### 1. Application Oluştur
```
New Resource → Application
Git Repository → Repo'nu bağla
Build Pack → Dockerfile seç
```

### 2. MySQL Ekle
```
New Resource → Database → MySQL 8.0
shuttlecall / shuttlecall_user / [şifre]
```

### 3. Environment Variables
`.env.coolify.example` dosyasındaki değişkenleri kopyala ve düzenle:
- SECRET_KEY (32+ karakter)
- JWT_SECRET_KEY (32+ karakter)
- DB_* (MySQL bilgileri)
- VAPID_* (https://vapidkeys.com/)
- CORS_ORIGINS (domain'in)
- BASE_URL (domain'in)
- RESET_DB=true (ilk deployment için)

### 4. Domain Ekle
```
Application → Domains → yourdomain.com
SSL otomatik (Let's Encrypt)
```

### 5. Deploy
```
Deploy butonuna tıkla
Logları takip et
```

### 6. İlk Kurulum Sonrası
```bash
# Console'dan admin oluştur
python create_admin.py

# RESET_DB'yi false yap
RESET_DB=false
```

## 🔍 Test

### Health Check
```bash
curl https://yourdomain.com/health
```

Beklenen yanıt:
```json
{
  "status": "healthy",
  "database": "connected",
  "app_name": "Shuttle Call",
  "timestamp": "2025-11-11T..."
}
```

### Admin Login
```
https://yourdomain.com/admin/login
```

## 📦 Opsiyonel: Persistent Storage

Upload'lar için:
```
Application → Storages → Add Storage
Mount Path: /app/app/static/uploads
```

## 🔄 Auto Deploy

Her push'ta otomatik deploy:
```
Application → General → Auto Deploy
Branch: main
```

## 🐛 Troubleshooting

### Logları Görüntüle
```
Coolify Dashboard → Application → Logs
```

### Database Bağlantı Testi
```bash
# Console'dan
python check_railway_env.py
```

### Manuel Migration
```bash
# Console'dan
python fix_railway_migration.py
```

### Container Restart
```
Application → Actions → Restart
```

## 📝 Önemli Notlar

1. ✅ İlk deployment: `RESET_DB=true`
2. ✅ Sonraki deployments: `RESET_DB=false`
3. ✅ SECRET_KEY ve JWT_SECRET_KEY güçlü olmalı (min 32 karakter)
4. ✅ VAPID keys https://vapidkeys.com/ adresinden oluştur
5. ✅ CORS_ORIGINS sadece kendi domain'ini içermeli
6. ✅ DEBUG=False production'da
7. ✅ SSL sertifikası otomatik oluşturulur

## 🎯 Deployment Checklist

- [ ] Coolify'da application oluşturuldu
- [ ] MySQL database oluşturuldu
- [ ] Environment variables ayarlandı
- [ ] Domain eklendi ve SSL aktif
- [ ] İlk deployment yapıldı (RESET_DB=true)
- [ ] Health check başarılı
- [ ] Admin kullanıcı oluşturuldu
- [ ] RESET_DB=false yapıldı
- [ ] Test edildi (login, buggy call, vb.)
- [ ] Auto deploy aktif edildi (opsiyonel)
- [ ] Persistent storage eklendi (opsiyonel)

## 🎉 Tamamlandı!

Uygulamanız Coolify'da çalışıyor! 🚀
