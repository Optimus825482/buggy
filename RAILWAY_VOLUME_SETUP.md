# Railway Volume Setup - Uploads Klasörü

## 🔴 Sorun
Railway'de her deploy'da `app/static/uploads/` klasörü sıfırlanıyor çünkü:
- Dosyalar `.gitignore`'da
- Railway ephemeral filesystem kullanıyor

## ✅ Çözüm: Railway Volume

### Adım 1: Volume Oluştur
1. Railway Dashboard → Service Settings
2. **Volumes** sekmesine git
3. **Add Volume** tıkla
4. Ayarlar:
   ```
   Mount Path: /app/app/static/uploads
   Size: 1GB
   ```

### Adım 2: Redeploy
Volume ekledikten sonra service'i redeploy et.

### Adım 3: Mevcut Dosyaları Yükle
Local'deki dosyaları Railway'e yüklemek için:

```bash
# Railway CLI ile bağlan
railway link

# Shell aç
railway run bash

# Dosyaları kopyala (local'den Railway'e)
# Veya admin panel'den yeniden yükle
```

## 🔄 Alternatif: Cloud Storage
Daha profesyonel çözüm için:
- **AWS S3**
- **Cloudinary** (önerilen - ücretsiz tier var)
- **Railway Volume** (basit projeler için yeterli)

## 📊 Volume Durumu Kontrol
```bash
railway run python scripts/check_uploads.py
```

## ⚠️ Önemli Notlar
- Volume mount edildikten sonra dosyalar kalıcı olur
- Volume silersen dosyalar kaybolur
- Backup almayı unutma!
