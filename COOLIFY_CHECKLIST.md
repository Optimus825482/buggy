# ✅ Shuttle Call - Coolify Deployment Checklist

## 📋 Ön Hazırlık

- [x] Coolify sunucusu hazır
- [x] MySQL database oluşturuldu
  - Host: `ic8c8ss4s800gws0cg0wow0k`
  - Database: `buggycalldb`
  - User: `buggy`
  - Password: `518518Erkan`
- [x] Redis oluşturuldu
  - URL: `redis://default:WRwJClTqLZjdcm3tgVC73Ch5YD6dJJrhv94EFQgxv1N6fylIzpHdKo7hKZWMkIdv@zgsc4gk0scg0os8w88w4k0ck:6379/0`
- [x] Domain'ler hazır:
  - shuttlecagri.com
  - shuttlecagri.xyz
  - shuttlecagri.online

## 🚀 Deployment Adımları

### 1. Application Oluştur
- [ ] Coolify → New Resource → Application
- [ ] Git Repository bağla
- [ ] Build Pack: **Dockerfile** seç
- [ ] Branch: `main` (veya kullandığın branch)

### 2. Environment Variables Ayarla
- [ ] Application → Environment Variables → **Bulk Edit**
- [ ] `COOLIFY_ENV_READY.txt` dosyasındaki tüm değişkenleri kopyala-yapıştır
- [ ] **ÖNEMLİ**: İlk deployment için `RESET_DB=true` yap
- [ ] Save

### 3. Port Ayarları
- [ ] Application → General → Port Mappings
- [ ] Container Port: **8000**
- [ ] Public Port: **80** (veya Coolify'ın otomatik ayarı)

### 4. Domain Ekle
- [ ] Application → Domains → Add Domain
- [ ] Domain 1: `shuttlecagri.com`
- [ ] Domain 2: `www.shuttlecagri.com`
- [ ] Domain 3: `shuttlecagri.xyz`
- [ ] Domain 4: `www.shuttlecagri.xyz`
- [ ] Domain 5: `shuttlecagri.online`
- [ ] Domain 6: `www.shuttlecagri.online`
- [ ] SSL: **Auto (Let's Encrypt)** aktif

### 5. İlk Deployment
- [ ] **Deploy** butonuna tıkla
- [ ] Build loglarını takip et
- [ ] Hata varsa logları kontrol et
- [ ] Deployment tamamlanana kadar bekle (3-5 dakika)

### 6. Health Check
- [ ] Browser'da aç: `https://shuttlecagri.com/health`
- [ ] Beklenen yanıt:
```json
{
  "status": "healthy",
  "database": "connected",
  "app_name": "Shuttle Call",
  "timestamp": "2025-11-11T..."
}
```

### 7. Admin Kullanıcı Oluştur
- [ ] Coolify → Application → Console
- [ ] Komutu çalıştır: `python create_admin.py`
- [ ] Admin bilgilerini kaydet

### 8. İlk Test
- [ ] Ana sayfa: `https://shuttlecagri.com`
- [ ] Admin login: `https://shuttlecagri.com/admin/login`
- [ ] Admin ile giriş yap
- [ ] Dashboard'u kontrol et

### 9. RESET_DB'yi Kapat
- [ ] Application → Environment Variables
- [ ] `RESET_DB=false` yap
- [ ] Save
- [ ] **Redeploy YAPMA** (sadece kaydet)

### 10. Persistent Storage (Opsiyonel)
- [ ] Application → Storages → Add Storage
- [ ] Mount Path: `/app/app/static/uploads`
- [ ] Size: 5GB (veya ihtiyacına göre)
- [ ] Save
- [ ] Redeploy

### 11. Auto Deploy (Opsiyonel)
- [ ] Application → General → Auto Deploy
- [ ] Enable: **Yes**
- [ ] Branch: `main`
- [ ] Save

## 🔍 Test Senaryoları

### Guest (Misafir) Testi
- [ ] Ana sayfayı aç
- [ ] Location seç
- [ ] Buggy çağır
- [ ] QR kod göründü mü?
- [ ] Push notification izni iste
- [ ] Bildirim geldi mi?

### Driver (Sürücü) Testi
- [ ] Admin'den driver oluştur
- [ ] Driver ile login ol
- [ ] Location seç
- [ ] Buggy seç
- [ ] Çağrı geldi mi?
- [ ] Çağrıyı kabul et
- [ ] Tamamla

### Admin Testi
- [ ] Admin login
- [ ] Location oluştur
- [ ] Buggy oluştur
- [ ] Driver oluştur
- [ ] Raporları kontrol et
- [ ] Ayarları değiştir

## 📊 Monitoring

### Logları Kontrol Et
- [ ] Coolify → Application → Logs
- [ ] Error log'ları kontrol et
- [ ] Warning'leri kontrol et

### Performance
- [ ] Sayfa yüklenme hızı
- [ ] API response time
- [ ] WebSocket bağlantısı
- [ ] Redis bağlantısı

### Database
- [ ] MySQL bağlantısı
- [ ] Tablo yapıları
- [ ] İlk data'lar oluştu mu?

## 🔐 Güvenlik Kontrolleri

- [x] SECRET_KEY güçlü (32+ karakter)
- [x] JWT_SECRET_KEY güçlü (32+ karakter)
- [x] Database şifresi güçlü
- [x] DEBUG=False
- [x] CORS sadece kendi domain'leri
- [x] SSL aktif (HTTPS)
- [ ] Firewall kuralları (Coolify otomatik)

## 🎯 Production Checklist

- [ ] Tüm domain'ler çalışıyor
- [ ] SSL sertifikaları aktif
- [ ] Health check başarılı
- [ ] Admin paneli erişilebilir
- [ ] Guest flow çalışıyor
- [ ] Driver flow çalışıyor
- [ ] Push notifications çalışıyor
- [ ] WebSocket çalışıyor
- [ ] Redis bağlantısı OK
- [ ] MySQL bağlantısı OK
- [ ] Loglar temiz
- [ ] RESET_DB=false

## 🐛 Sorun Giderme

### Build Hatası
```bash
# Coolify Logs'u kontrol et
# Dockerfile syntax hatası varsa düzelt
# requirements.txt eksik paket varsa ekle
```

### Database Bağlantı Hatası
```bash
# Console'dan test et
python check_railway_env.py

# DB_HOST doğru mu kontrol et
# DB_PASSWORD doğru mu kontrol et
```

### Redis Bağlantı Hatası
```bash
# Redis URL'i kontrol et
# Redis service çalışıyor mu kontrol et
```

### Port Hatası
```bash
# PORT=8000 olmalı
# Dockerfile EXPOSE 8000 olmalı
# Health check localhost:8000 olmalı
```

## 📞 Destek

Sorun yaşarsan:
1. Coolify logs'u kontrol et
2. Application console'dan script'leri manuel çalıştır
3. Health endpoint'i test et
4. Database bağlantısını test et

## 🎉 Tamamlandı!

Tüm checklistler tamamlandıysa, uygulamanız production'da! 🚀

**Ana Domain**: https://shuttlecagri.com
**Admin Panel**: https://shuttlecagri.com/admin/login
**Health Check**: https://shuttlecagri.com/health
