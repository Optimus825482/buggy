# 📦 Coolify Volume Setup - Uploads Klasörü

## 🎯 Problem

Her deploy'da `app/static/uploads` klasöründeki dosyalar siliniyor.

## ✅ Çözüm: Persistent Volume

### 1️⃣ Coolify Dashboard'da Volume Ekle

**Coolify** → **Projen** → **Storages** → **Add Volume**

```
Source Path (Host):     /var/lib/coolify/volumes/shuttle-uploads
Destination Path (Container):  /app/app/static/uploads
```

### 2️⃣ Alternatif: Docker Compose Override

Eğer Coolify'da manuel volume ekleyemiyorsan, `docker-compose.override.yml` oluştur:

```yaml
version: "3.8"

services:
  app:
    volumes:
      - uploads-data:/app/app/static/uploads

volumes:
  uploads-data:
    driver: local
```

### 3️⃣ Mevcut Dosyaları Kopyala (İlk Kurulum)

Deploy sonrası SSH ile bağlan:

```bash
# Container'a gir
docker exec -it <container_name> bash

# Uploads klasörünü kontrol et
ls -la /app/app/static/uploads/

# Eğer boşsa, local'den kopyala (opsiyonel)
```

## 📊 Sonuç

- ✅ Uploads klasörü **persistent volume**'de saklanır
- ✅ Her deploy'da dosyalar **korunur**
- ✅ Git'e **commit edilmez** (gereksiz)
- ✅ Coolify otomatik **backup** alır

## 🔍 Kontrol

Deploy sonrası:

```bash
# Container'da kontrol et
docker exec -it <container_name> ls -la /app/app/static/uploads/locations/
```

Dosyalar duruyorsa ✅ başarılı!
