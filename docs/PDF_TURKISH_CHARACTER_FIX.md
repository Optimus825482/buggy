# PDF Türkçe Karakter Desteği Düzeltmesi

## 🐛 Sorun

PDF raporlarında Türkçe karakterler (ı, İ, ş, ğ, ü, ö, ç) düzgün görünmüyordu.

**Neden**: ReportLab kütüphanesi varsayılan olarak Helvetica/Roboto fontlarını kullanıyor ve bu fontlar Türkçe karakterleri tam desteklemiyor.

## ✅ Çözüm

Türkçe karakterleri destekleyen **DejaVu Sans** veya **Liberation Sans** fontları kullanılacak şekilde güncellendi.

## 📝 Güncellenen Dosyalar

### 1. `app/services/report_service.py`

#### `export_to_pdf()` Fonksiyonu

```python
# Türkçe karakter desteği için font kaydet
try:
    font_path = '/usr/share/fonts/truetype/dejavu/'
    if os.path.exists(font_path + 'DejaVuSans.ttf'):
        pdfmetrics.registerFont(TTFont('DejaVuSans', font_path + 'DejaVuSans.ttf'))
        pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', font_path + 'DejaVuSans-Bold.ttf'))
        font_name = 'DejaVuSans'
        font_name_bold = 'DejaVuSans-Bold'
    else:
        # Fallback: Helvetica
        font_name = 'Helvetica'
        font_name_bold = 'Helvetica-Bold'
except Exception:
    font_name = 'Helvetica'
    font_name_bold = 'Helvetica-Bold'
```

**Değişiklikler**:

- ❌ Eski: `'Roboto'` ve `'Roboto-bold'` (Türkçe desteği yok)
- ✅ Yeni: `'DejaVuSans'` ve `'DejaVuSans-Bold'` (Türkçe desteği var)
- ✅ Fallback: `'Helvetica'` (font bulunamazsa)

### 2. `app/routes/reports.py`

#### `export_comprehensive_pdf()` Fonksiyonu

```python
# DejaVu Sans font'u kaydet (Türkçe karakter desteği)
font_name = 'Helvetica'
font_bold = 'Helvetica-Bold'

try:
    # Farklı font yollarını dene
    font_paths = [
        '/usr/share/fonts/truetype/dejavu/',  # Linux
        '/System/Library/Fonts/',  # macOS
        'C:\\Windows\\Fonts\\',  # Windows
        '/usr/share/fonts/truetype/liberation/',  # Liberation fonts
    ]

    for font_path in font_paths:
        if os.path.exists(font_path + 'DejaVuSans.ttf'):
            pdfmetrics.registerFont(TTFont('DejaVuSans', font_path + 'DejaVuSans.ttf'))
            pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', font_path + 'DejaVuSans-Bold.ttf'))
            font_name = 'DejaVuSans'
            font_bold = 'DejaVuSans-Bold'
            break
        elif os.path.exists(font_path + 'LiberationSans-Regular.ttf'):
            pdfmetrics.registerFont(TTFont('LiberationSans', font_path + 'LiberationSans-Regular.ttf'))
            pdfmetrics.registerFont(TTFont('LiberationSans-Bold', font_path + 'LiberationSans-Bold.ttf'))
            font_name = 'LiberationSans'
            font_bold = 'LiberationSans-Bold'
            break
except Exception as e:
    print(f"⚠️ Font yüklenemedi, Helvetica kullanılacak: {str(e)}")
```

**Değişiklikler**:

- ✅ Çoklu platform desteği (Linux, macOS, Windows)
- ✅ Alternatif font desteği (DejaVu Sans veya Liberation Sans)
- ✅ Güvenli fallback mekanizması

## 🔧 Font Kurulumu

### Linux (Ubuntu/Debian)

```bash
sudo apt-get install fonts-dejavu fonts-liberation
```

### Linux (CentOS/RHEL)

```bash
sudo yum install dejavu-sans-fonts liberation-fonts
```

### macOS

DejaVu Sans fontları genellikle sistem fontları arasında bulunur. Yoksa:

```bash
brew install --cask font-dejavu
```

### Windows

DejaVu Sans fontlarını [buradan](https://dejavu-fonts.github.io/) indirebilirsin.

## 📊 Desteklenen Karakterler

DejaVu Sans ve Liberation Sans fontları şu karakterleri destekler:

### Türkçe Karakterler

- ✅ ı, İ
- ✅ ş, Ş
- ✅ ğ, Ğ
- ✅ ü, Ü
- ✅ ö, Ö
- ✅ ç, Ç

### Diğer Özel Karakterler

- ✅ €, £, ¥
- ✅ ©, ®, ™
- ✅ °, ±, ×, ÷
- ✅ Ve daha fazlası...

## 🎯 Etkilenen PDF Raporları

1. **Basit PDF Raporları** (`/api/reports/export/pdf/<report_type>`)

   - Daily Summary
   - Buggy Performance
   - Location Analytics
   - Request Details

2. **Kapsamlı PDF Raporları** (`/api/reports/export-pdf`)
   - Grafikler dahil
   - Tüm istatistikler
   - Detaylı tablolar

## 🧪 Test

PDF raporlarını test etmek için:

1. Raporlar sayfasına git
2. "PDF İndir" butonuna tıkla
3. PDF'i aç ve Türkçe karakterleri kontrol et

**Test Edilecek Kelimeler**:

- Tamamlandı ✅
- İptal Edildi ✅
- Başarı Oranı ✅
- Sürücü ✅
- Lokasyon ✅
- Ort. Tamamlanma Süresi ✅

## 🔍 Sorun Giderme

### Font Bulunamıyor Hatası

Eğer fontlar bulunamazsa, log'larda şu mesajı göreceksin:

```
⚠️ Font yüklenemedi, Helvetica kullanılacak
```

**Çözüm**:

1. DejaVu Sans fontlarını kur (yukarıdaki komutları kullan)
2. Uygulamayı yeniden başlat
3. PDF'i tekrar oluştur

### Karakterler Hala Bozuk

Eğer karakterler hala bozuksa:

1. Font yolunu kontrol et:

```bash
# Linux'ta
ls /usr/share/fonts/truetype/dejavu/

# Çıktı:
# DejaVuSans.ttf
# DejaVuSans-Bold.ttf
```

2. Font izinlerini kontrol et:

```bash
ls -la /usr/share/fonts/truetype/dejavu/
```

3. Uygulamayı yeniden başlat:

```bash
sudo systemctl restart shuttlecall
```

## 📌 Notlar

- DejaVu Sans fontları açık kaynak ve ücretsizdir
- Liberation Sans fontları Red Hat tarafından geliştirilmiştir
- Her iki font da geniş karakter desteği sunar
- Fallback mekanizması sayesinde font bulunamazsa bile uygulama çalışır

## 🚀 Deployment

Değişiklikler otomatik olarak uygulanacak:

```bash
# Sadece uygulamayı yeniden başlat
sudo systemctl restart shuttlecall
```

**Not**: Fontlar zaten projede mevcut olduğu için herhangi bir kurulum gerekmez!

---

**Tarih**: 2025-11-16  
**Geliştirici**: Erkan ERDEM  
**Durum**: ✅ Tamamlandı  
**Test**: ⏳ Test edilmeli
