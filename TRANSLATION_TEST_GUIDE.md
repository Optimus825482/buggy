# 🧪 Çeviri Test Rehberi

## Test Adımları

### 1. Call Premium Sayfası

```
URL: http://localhost:5000/guest/call
```

**Test Edilecek Elementler:**

- ✅ Page Title (tarayıcı sekmesi)
- ✅ "Shuttle Call System" (brand name)
- ✅ "QR Kod Okut" butonu
- ✅ "Shuttle Çağır" butonu
- ✅ "Oda Numaranız" label
- ✅ Input placeholder'ları

**Test:**

1. Sayfayı aç
2. Sağ üst köşedeki bayrak ikonuna tıkla
3. Farklı diller seç
4. Tüm text'lerin değiştiğini kontrol et

### 2. Confirmation Modal

**Tetikleme:**

1. Lokasyon seç
2. "Shuttle Çağır" butonuna bas

**Test Edilecek:**

- ✅ "Shuttle Çağırmak İstiyor musunuz?"
- ✅ "Talebinizi onaylayın"
- ✅ "Lokasyon:", "Oda:", "Not:"
- ✅ "İptal" butonu
- ✅ "Evet, Çağır" butonu

### 3. Success Notification

**Tetikleme:**

1. Confirmation modal'da "Evet, Çağır" bas

**Test Edilecek:**

- ✅ "Talebiniz Alındı!"
- ✅ "Shuttle çağrınız başarıyla gönderildi..."
- ✅ "Bu pencereyi 5 saniye boyunca kapatmayın!"

### 4. Status Page

```
URL: http://localhost:5000/guest/status/1
```

**Test Edilecek:**

- ✅ Page Title
- ✅ "Talebiniz Alındı"
- ✅ "Talebiniz başarıyla oluşturuldu..."
- ✅ "Lokasyon", "Oda No"
- ✅ Timeline: "Talep Oluşturuldu", "İşleme Alındı", "Bekleniyor...", "Shuttle Yolda", "Geldi"
- ✅ Bildirim banner: "Bildirimler Kapalı", "İzin Ver"

## Console Debug

### Brand Name Kontrolü

```javascript
// Console'da çalıştır
console.log(window.guestI18n.t("brand.name"));
// Çıktı: "Shuttle Call System" (tüm dillerde aynı)
```

### Element Kontrolü

```javascript
// Brand name element'i bul
const brandElement = document.querySelector('[data-i18n="brand.name"]');
console.log({
  element: brandElement,
  textContent: brandElement.textContent,
  hasChildren: brandElement.children.length,
  innerHTML: brandElement.innerHTML,
});
```

### Dil Değiştirme

```javascript
// Dil değiştir
window.guestI18n.changeLanguage("en");
window.guestI18n.changeLanguage("de");
window.guestI18n.changeLanguage("ru");
window.guestI18n.changeLanguage("ar");
window.guestI18n.changeLanguage("tr");
```

## Sorun Giderme

### Problem: Text değişmiyor

**Çözüm 1:** Console'da kontrol et

```javascript
// Element var mı?
document.querySelector('[data-i18n="brand.name"]');

// i18n yüklü mü?
window.guestI18n;

// Çeviri var mı?
window.guestI18n.t("brand.name");
```

**Çözüm 2:** Sayfayı yenile

```javascript
// Hard refresh
Ctrl + Shift + R(Windows / Linux);
Cmd + Shift + R(Mac);
```

**Çözüm 3:** Cache temizle

```javascript
// LocalStorage temizle
localStorage.clear();
location.reload();
```

### Problem: Bazı elementler çevrilmiyor

**Kontrol Et:**

1. `data-i18n` attribute var mı?
2. Çeviri key'i doğru mu?
3. Element DOM'da var mı? (dinamik oluşturulmuş olabilir)

**Debug:**

```javascript
// Tüm i18n elementleri listele
document.querySelectorAll("[data-i18n]").forEach((el) => {
  console.log(el.getAttribute("data-i18n"), el.textContent);
});
```

### Problem: Dil değişmiyor

**Kontrol Et:**

```javascript
// Mevcut dil
console.log(window.guestI18n.currentLang);

// LocalStorage
console.log(localStorage.getItem("guest_language"));

// Desteklenen diller
console.log(["tr", "en", "de", "ru", "ar"]);
```

## Test Checklist

### Türkçe (TR) 🇹🇷

- [ ] Brand name: "Shuttle Call System"
- [ ] Call button: "Shuttle Çağır"
- [ ] Confirmation: "Shuttle Çağırmak İstiyor musunuz?"
- [ ] Status: "Talebiniz Alındı"
- [ ] Timeline: "Talep Oluşturuldu"

### English (EN) 🇬🇧

- [ ] Brand name: "Shuttle Call System"
- [ ] Call button: "Call Shuttle"
- [ ] Confirmation: "Do You Want to Call Shuttle?"
- [ ] Status: "Request Received"
- [ ] Timeline: "Request Created"

### Deutsch (DE) 🇩🇪

- [ ] Brand name: "Shuttle Call System"
- [ ] Call button: "Shuttle Rufen"
- [ ] Confirmation: "Möchten Sie Shuttle Rufen?"
- [ ] Status: "Anfrage Erhalten"
- [ ] Timeline: "Anfrage Erstellt"

### Русский (RU) 🇷🇺

- [ ] Brand name: "Shuttle Call System"
- [ ] Call button: "Вызвать Шаттл"
- [ ] Confirmation: "Вы Хотите Вызвать Шаттл?"
- [ ] Status: "Запрос Получен"
- [ ] Timeline: "Запрос Создан"

### العربية (AR) 🇸🇦

- [ ] Brand name: "Shuttle Call System"
- [ ] Call button: "استدعاء الحافلة"
- [ ] Confirmation: "هل تريد استدعاء الحافلة؟"
- [ ] Status: "تم استلام الطلب"
- [ ] Timeline: "تم إنشاء الطلب"
- [ ] RTL layout aktif mi?

## Performans Testi

### Yükleme Süresi

```javascript
console.time("i18n-load");
// Sayfa yüklensin
console.timeEnd("i18n-load");
// Beklenen: <100ms
```

### Çeviri Süresi

```javascript
console.time("translate");
window.guestI18n.changeLanguage("en");
console.timeEnd("translate");
// Beklenen: <50ms
```

### Bellek Kullanımı

```javascript
// Chrome DevTools > Memory > Take snapshot
// Beklenen: ~100KB
```

## Otomatik Test Script

```javascript
// Tüm dilleri test et
const languages = ["tr", "en", "de", "ru", "ar"];
const testResults = {};

languages.forEach((lang) => {
  window.guestI18n.changeLanguage(lang);

  const brandName = document.querySelector(
    '[data-i18n="brand.name"]'
  ).textContent;
  const callButton = document.querySelector(
    '[data-i18n="call.call_shuttle"]'
  )?.textContent;

  testResults[lang] = {
    brandName: brandName === "Shuttle Call System",
    callButton: callButton !== undefined && callButton.length > 0,
    pageTitle: document.title.includes("Shuttle Call System"),
  };
});

console.table(testResults);
```

## Beklenen Sonuçlar

### Tüm Diller

```javascript
{
  tr: { brandName: true, callButton: true, pageTitle: true },
  en: { brandName: true, callButton: true, pageTitle: true },
  de: { brandName: true, callButton: true, pageTitle: true },
  ru: { brandName: true, callButton: true, pageTitle: true },
  ar: { brandName: true, callButton: true, pageTitle: true }
}
```

**Powered by Erkan ERDEM** 🚀
