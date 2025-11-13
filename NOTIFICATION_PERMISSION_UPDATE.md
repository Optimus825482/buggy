# 🔔 Bildirim İzni Güncellemesi

## ✅ Yapılan Değişiklikler

### 1. Brand Name Çevirisi

- "Shuttle Call System" artık çevrilebilir
- `data-i18n="brand.name"` attribute eklendi
- Tüm dillerde aynı kalıyor (brand name)

### 2. Bildirim İzni Prompt'u

**Önceki Durum:**

```
❌ Bildirimler Kapalı
   Tarayıcı ayarlarından bildirimleri açabilirsiniz.
```

**Yeni Durum:**

```
⚠️ Bildirimler Kapalı
   Shuttle durumu hakkında bildirim almak için izin verin.
   [İzin Ver] [Kapat]
```

### 3. Otomatik Prompt Gösterimi

- Request kabul edildiğinde bildirim izni yoksa otomatik gösterilir
- 10 saniye sonra otomatik kapanır
- Kullanıcı "İzin Ver" butonuna basınca tarayıcı izni ister

### 4. iOS Desteği

- iOS cihazlarda özel handler kullanılır
- PWA kontrolü yapılır
- Uygun mesajlar gösterilir

## 🎨 Yeni Özellikler

### Call Page (call_premium.html)

- Shuttle kabul edildiğinde izin yoksa prompt gösterilir
- Modern, gradient butonlar
- Animasyonlu giriş/çıkış

### Status Page (status_premium.html)

- Sayfa yüklendiğinde izin kontrolü
- Banner'da "İzin Ver" butonu
- Toast bildirimleri

## 🌍 Çeviriler

Tüm dillerde eklendi:

- `brand.name`: "Shuttle Call System"
- `notif.permission_denied`: "Bildirimler Kapalı"
- `notif.permission_denied_msg`: "Shuttle durumu hakkında bildirim almak için izin verin."
- `btn.enable_notifications`: "İzin Ver"

## 🧪 Test

1. Bildirim izni olmadan shuttle çağır
2. Driver kabul etsin
3. Otomatik prompt gösterilir
4. "İzin Ver" butonuna bas
5. Tarayıcı izni iste
6. İzin ver
7. FCM token kaydedilir

## 📱 Kullanıcı Akışı

```
Guest shuttle çağırır
    ↓
Driver kabul eder
    ↓
Bildirim izni var mı? → EVET → Bildirim gönder
    ↓ HAYIR
Prompt göster
    ↓
Kullanıcı "İzin Ver" butonuna basar
    ↓
Tarayıcı izin penceresi açılır
    ↓
İzin verilir → FCM token kaydedilir
    ↓
Sonraki bildirimleri alır
```

**Powered by Erkan ERDEM** 🚀
