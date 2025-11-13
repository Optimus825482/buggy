# 🎯 i18n Kalite Güvence Rehberi

## Otomatik Testler

### Console'da Çalıştır

```javascript
// 1. Tüm çevirileri test et
window.testI18n();

// 2. Çeviri doğrulama
window.guestI18n.validateTranslations();

// 3. Belirli bir key'i test et
window.guestI18n
  .t("brand.name")

  [
    // 4. Tüm dilleri dene
    ("tr", "en", "de", "ru", "ar")
  ].forEach((lang) => {
    window.guestI18n.changeLanguage(lang);
    console.log(`${lang}: ${document.title}`);
  });
```

## Beklenen Console Çıktısı

### Başarılı Yükleme

```
╔════════════════════════════════════════════════════════════╗
║  🌍 Guest i18n System Initializing                        ║
╠════════════════════════════════════════════════════════════╣
║  Detected Language: TR                                    ║
║  Supported Languages: TR, EN, DE, RU, AR                  ║
╚════════════════════════════════════════════════════════════╝

[i18n] 📄 DOM loaded, starting translation...
[i18n] ✓ Text: "Shuttle Çağır" → "Shuttle Çağır"
[i18n] ✓ Text: "QR Kod Okut" → "QR Kod Okut"
...

╔════════════════════════════════════════════════════════════╗
║  🌍 Translation Report - TR                               ║
╠════════════════════════════════════════════════════════════╣
║  ✅ Success: 25  elements translated                      ║
║  ❌ Errors:  0   elements failed                          ║
║  📊 Total:   25  elements processed                       ║
╚════════════════════════════════════════════════════════════╝

[i18n] ✅ Perfect! 100% translation success rate
```

### Hata Durumu

```
[i18n] ⚠️ Translation not found: "invalid.key" for language "tr"
[i18n] 📝 Using English fallback for "invalid.key"

╔════════════════════════════════════════════════════════════╗
║  🌍 Translation Report - TR                               ║
╠════════════════════════════════════════════════════════════╣
║  ✅ Success: 24  elements translated                      ║
║  ❌ Errors:  1   elements failed                          ║
║  📊 Total:   25  elements processed                       ║
╚════════════════════════════════════════════════════════════╝

[i18n] ⚠️ Success rate: 96.0% - Some translations may be missing!
[i18n] ⚠️ Translation errors: [{...}]
```

## Validation Report

```javascript
window.guestI18n.validateTranslations();
```

### Beklenen Çıktı

```
┌─────────┬───────┬────────────┬─────────┬──────────┐
│ (index) │ total │ translated │ missing │ coverage │
├─────────┼───────┼────────────┼─────────┼──────────┤
│   tr    │  45   │     45     │    0    │ '100.0%' │
│   en    │  45   │     45     │    0    │ '100.0%' │
│   de    │  45   │     45     │    0    │ '100.0%' │
│   ru    │  45   │     45     │    0    │ '100.0%' │
│   ar    │  45   │     45     │    0    │ '100.0%' │
└─────────┴───────┴────────────┴─────────┴──────────┘

[i18n] ✅ TR: Complete (45 translations)
[i18n] ✅ EN: Complete (45 translations)
[i18n] ✅ DE: Complete (45 translations)
[i18n] ✅ RU: Complete (45 translations)
[i18n] ✅ AR: Complete (45 translations)
```

## Manuel Test Checklist

### 1. Sayfa Yükleme

- [ ] Console'da hata yok
- [ ] 100% success rate
- [ ] Tüm elementler çevrilmiş

### 2. Dil Değiştirme

- [ ] Bayrak ikonu çalışıyor
- [ ] Tüm text'ler değişiyor
- [ ] Page title değişiyor
- [ ] Console'da hata yok

### 3. Her Dil İçin

- [ ] TR: Türkçe karakterler doğru (ş, ğ, ı, ü, ö, ç)
- [ ] EN: İngilizce doğru
- [ ] DE: Almanca karakterler doğru (ä, ö, ü, ß)
- [ ] RU: Kiril alfabesi doğru (Ш, Щ, Ж, Ч, Ю, Я)
- [ ] AR: Arapça doğru + RTL layout aktif

### 4. Özel Durumlar

- [ ] Confirmation modal çevirisi
- [ ] Success notification çevirisi
- [ ] Error mesajları çevirisi
- [ ] Placeholder'lar çevirisi
- [ ] Button text'leri çevirisi

## Hata Ayıklama

### Problem: Çeviri çalışmıyor

**Adım 1: Element kontrolü**

```javascript
// Element var mı?
document.querySelector('[data-i18n="brand.name"]');

// Attribute doğru mu?
document.querySelector('[data-i18n="brand.name"]').getAttribute("data-i18n");
```

**Adım 2: Çeviri kontrolü**

```javascript
// Çeviri var mı?
window.guestI18n.t("brand.name");

// Hangi dil aktif?
window.guestI18n.currentLang;
```

**Adım 3: Manuel çeviri**

```javascript
// Manuel olarak çevir
window.guestI18n.translatePage();
```

### Problem: Bazı elementler çevrilmiyor

**Console'da kontrol et:**

```javascript
// Tüm i18n elementleri listele
document.querySelectorAll("[data-i18n]").forEach((el, i) => {
  console.log(i, el.getAttribute("data-i18n"), el.textContent);
});
```

**Eksik çevirileri bul:**

```javascript
const report = window.guestI18n.validateTranslations();
console.log("Missing translations:", report);
```

### Problem: Console'da çok fazla log

**Production modunda log'ları kapat:**

```javascript
// i18n-guest.js içinde
if (window.location.hostname !== "localhost") {
  console.log = () => {};
}
```

## Performans Metrikleri

### Kabul Edilebilir Değerler

- ✅ Yükleme süresi: <100ms
- ✅ Çeviri süresi: <50ms
- ✅ Success rate: 100%
- ✅ Bellek kullanımı: <200KB

### Ölçüm

```javascript
// Yükleme süresi
console.time("i18n-load");
// Sayfa yüklensin...
console.timeEnd("i18n-load");

// Çeviri süresi
console.time("translate");
window.guestI18n.changeLanguage("en");
console.timeEnd("translate");

// Bellek kullanımı
// Chrome DevTools > Memory > Take snapshot
```

## Deployment Checklist

### Production'a Çıkmadan Önce

- [ ] `window.testI18n()` çalıştır - tüm testler geçmeli
- [ ] `validateTranslations()` çalıştır - %100 coverage olmalı
- [ ] Her dilde manuel test yap
- [ ] Console'da hata olmamalı
- [ ] Performance test yap
- [ ] Mobile'da test et
- [ ] iOS Safari'de test et
- [ ] Android Chrome'da test et

### Production'da İzleme

```javascript
// Error tracking
window.addEventListener("error", (e) => {
  if (e.message.includes("i18n")) {
    // Log to monitoring service
    console.error("i18n error:", e);
  }
});

// Translation success rate monitoring
setInterval(() => {
  const elements = document.querySelectorAll("[data-i18n]");
  const untranslated = Array.from(elements).filter((el) => {
    const key = el.getAttribute("data-i18n");
    return el.textContent.trim() === key;
  });

  if (untranslated.length > 0) {
    console.warn("Untranslated elements:", untranslated);
  }
}, 5000);
```

## Başarı Kriterleri

### ✅ Mükemmel

- 100% success rate
- 0 console errors
- Tüm diller %100 coverage
- <50ms çeviri süresi

### ⚠️ Kabul Edilebilir

- > 95% success rate
- <3 console warnings
- Tüm diller >95% coverage
- <100ms çeviri süresi

### ❌ Kabul Edilemez

- <95% success rate
- Console errors var
- Herhangi bir dil <90% coverage
- > 200ms çeviri süresi

**Powered by Erkan ERDEM** 🚀
