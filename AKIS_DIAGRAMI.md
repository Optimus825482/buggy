# 🚗 Buggy Call - Akış Diyagramı

## 📋 Sistem Kullanım Akışı

---

## 1️⃣ ADMIN KURULUM AŞAMASI

```mermaid
graph LR
    A[ADMIN GIRIS] --> B[OTEL TANIMLA]
    B --> C[LOKASYONLARI TANIMLA]
    C --> D[QR KODLARI OLUSTUR]
    D --> E[BUGGY ARACLARI TANIMLA]
    E --> F[SURUCU HESAPLARI OLUSTUR]
    
    style A fill:#667eea,color:#fff
    style B fill:#764ba2,color:#fff
    style C fill:#667eea,color:#fff
    style D fill:#764ba2,color:#fff
    style E fill:#667eea,color:#fff
    style F fill:#764ba2,color:#fff
```

### Admin Yapılanlar:
1. **Otel Tanımlama** → Otel bilgileri sisteme girilir
2. **Lokasyon Tanımlama** → Buggy çağrı noktaları oluşturulur (Havuz, Plaj, Restoran, vb.)
3. **QR Kod Oluşturma** → Her lokasyon için benzersiz QR kod üretilir
4. **QR Kodları Yerleştirme** → QR kodlar lokasyonlara asılır/yapıştırılır
5. **Buggy Tanımlama** → Araç bilgileri sisteme girilir (Plaka, Model, vb.)
6. **Sürücü Hesapları** → Her sürücü için kullanıcı adı ve şifre oluşturulur

---

## 2️⃣ MISAFIR BUGGY TALEP AKIŞI

```mermaid
graph TD
    A[MISAFIR LOKASYONA GELIR] --> B[QR KODU OKUTIR]
    B --> C{ILK GIRIS MI?}
    
    C -->|EVET| D[ODA NUMARASI SOR]
    C -->|HAYIR| E[BUGGY TALEP FORMU]
    
    D --> D1{ODA VAR MI?}
    D1 -->|EVET| D2[ODA NUMARASI GIR]
    D1 -->|HAYIR| D3[ODA NUMARAM YOK SEC]
    
    D2 --> E
    D3 --> E
    
    E --> F[BUGGY TALEP BUTONUNA BAS]
    F --> G[TALEP OLUSTURULDU]
    G --> H[DURUM: BEKLEMEDE]
    
    style A fill:#f39c12,color:#fff
    style B fill:#e74c3c,color:#fff
    style F fill:#27ae60,color:#fff
    style G fill:#3498db,color:#fff
    style H fill:#f39c12,color:#fff
```

### Misafir Adımları:
1. **Lokasyona Gelir** → Buggy çağrı noktasına varır
2. **QR Kod Okutma** → Telefon ile QR kodu tarar
3. **İlk Giriş Kontrolü** → Sistem oda numarası sorar
   - Oda varsa → Oda numarasını girer
   - Oda yoksa → "Oda Numaram Yok" seçeneğini işaretler
4. **Buggy Talep** → "Buggy Talep Et" butonuna basar
5. **Bekleme** → Talep "Beklemede" durumuna geçer

---

## 3️⃣ SURUCU BILDIRIM VE KABUL AKIŞI

```mermaid
graph TD
    A[TALEP OLUSTURULDU] --> B[PUSH BILDIRIM GONDERILIR]
    B --> C[TUM MUSAIT SURUCULERE ULASIR]
    
    C --> D[SURUCU 1 EKRANI]
    C --> E[SURUCU 2 EKRANI]
    C --> F[SURUCU 3 EKRANI]
    
    D --> G{KABUL ET?}
    E --> G
    F --> G
    
    G -->|HAYIR| H[BEKLE]
    H --> G
    
    G -->|EVET| I[ILK KABUL EDEN KAZANIR]
    I --> J[TALEP DURUMU: ISLEME ALINDI]
    J --> K[BUGGY DURUMU: MESGUL]
    
    style A fill:#3498db,color:#fff
    style B fill:#e74c3c,color:#fff
    style C fill:#f39c12,color:#fff
    style I fill:#27ae60,color:#fff
    style J fill:#3498db,color:#fff
    style K fill:#e74c3c,color:#fff
```

### Sürücü Bildirimi:
1. **Push Notification** → Tüm müsait sürücülere bildirim gider
2. **Talep Listesi** → Sürücü ekranında "Beklemede" olarak görünür
3. **Kabul Etme** → İlk "Kabul Et" butonuna basan sürücü talebi alır
4. **Durum Değişimi** → 
   - Talep: "Beklemede" → "İşleme Alındı"
   - Buggy: "Müsait" → "Meşgul"

---

## 4️⃣ SURUCU HIZMET AKIŞI

```mermaid
graph TD
    A[TALEP KABUL EDILDI] --> B[SURUCU MISAFIRIN YANINA GIDER]
    B --> C[MISAFIRI ALIR]
    C --> D[HEDEFE GOTURUR]
    D --> E[MISAFIRI BIRAKIR]
    E --> F[ISLEM TAMAMLANDI BUTONUNA BASAR]
    
    F --> G[SISTEM SORAR: HANGI LOKASYONDASIN?]
    G --> H[SURUCU LOKASYON SECER]
    H --> I[TALEP DURUMU: TAMAMLANDI]
    I --> J[BUGGY DURUMU: MUSAIT]
    J --> K[YENI TALEP BEKLE]
    
    style A fill:#3498db,color:#fff
    style B fill:#f39c12,color:#fff
    style C fill:#f39c12,color:#fff
    style D fill:#f39c12,color:#fff
    style E fill:#f39c12,color:#fff
    style F fill:#27ae60,color:#fff
    style G fill:#3498db,color:#fff
    style H fill:#3498db,color:#fff
    style I fill:#27ae60,color:#fff
    style J fill:#27ae60,color:#fff
```

### Hizmet Süreci:
1. **Misafirin Yanına Git** → Sürücü talep lokasyonuna gider
2. **Misafiri Al** → Misafir buggy'ye biner
3. **Hedefe Götür** → İstenen yere ulaştırır
4. **Misafiri Bırak** → Misafir iner
5. **İşlem Tamamla** → "İşlem Tamamlandı" butonuna basar
6. **Lokasyon Seç** → Sistem sorar: "Hangi lokasyondasın?"
7. **Lokasyon Belirt** → Önceden tanımlı lokasyonlardan birini seçer
8. **Durum Güncelleme** →
   - Talep: "İşleme Alındı" → "Tamamlandı"
   - Buggy: "Meşgul" → "Müsait"
9. **Yeni Talep Bekle** → Sistem yeni taleplere hazır

---

## 🔄 TAM SISTEM AKIŞI (ÖZET)

```mermaid
graph TD
    subgraph ADMIN
    A1[Otel Tanimla]
    A2[Lokasyon Tanimla]
    A3[QR Kod Olustur]
    A4[Buggy Tanimla]
    A5[Surucu Olustur]
    end
    
    subgraph MISAFIR
    M1[QR Kod Okut]
    M2[Oda Numarasi Gir]
    M3[Buggy Talep Et]
    M4[Bekle]
    end
    
    subgraph SISTEM
    S1[Push Bildirim Gonder]
    S2[Talep: BEKLEMEDE]
    S3[Talep: ISLEME ALINDI]
    S4[Talep: TAMAMLANDI]
    end
    
    subgraph SURUCU
    D1[Bildirim Al]
    D2[Kabul Et]
    D3[Misafiri Al]
    D4[Hedefe Gotur]
    D5[Islem Tamamla]
    D6[Lokasyon Sec]
    end
    
    A1 --> A2 --> A3 --> A4 --> A5
    A5 --> M1
    
    M1 --> M2 --> M3 --> M4
    M3 --> S1
    S1 --> S2
    S2 --> D1
    
    D1 --> D2
    D2 --> S3
    S3 --> D3 --> D4 --> D5 --> D6
    D6 --> S4
    
    S4 --> M1
    
    style A1 fill:#667eea,color:#fff
    style A2 fill:#667eea,color:#fff
    style A3 fill:#667eea,color:#fff
    style A4 fill:#667eea,color:#fff
    style A5 fill:#667eea,color:#fff
    
    style M1 fill:#f39c12,color:#fff
    style M2 fill:#f39c12,color:#fff
    style M3 fill:#27ae60,color:#fff
    style M4 fill:#f39c12,color:#fff
    
    style S1 fill:#e74c3c,color:#fff
    style S2 fill:#f39c12,color:#fff
    style S3 fill:#3498db,color:#fff
    style S4 fill:#27ae60,color:#fff
    
    style D1 fill:#3498db,color:#fff
    style D2 fill:#27ae60,color:#fff
    style D3 fill:#f39c12,color:#fff
    style D4 fill:#f39c12,color:#fff
    style D5 fill:#27ae60,color:#fff
    style D6 fill:#3498db,color:#fff
```

---

## 📊 DURUM GEÇIŞLERI

### Talep Durumları:
```
BEKLEMEDE → ISLEME ALINDI → TAMAMLANDI
   ↓              ↓              ↓
 (Yeni)      (Kabul Edildi)  (Bitti)
```

### Buggy Durumları:
```
MUSAIT → MESGUL → MUSAIT
  ↓         ↓         ↓
(Bos)   (Calisiyor) (Bos)
```

---

## 🎯 ÖZET AKIŞ

1. **ADMIN** → Sistemi kurar (Otel, Lokasyon, QR, Buggy, Sürücü)
2. **MISAFIR** → QR okutup buggy talep eder
3. **SISTEM** → Tüm müsait sürücülere bildirim gönderir
4. **SÜRÜCÜ** → Talebi kabul edip hizmeti tamamlar
5. **DÖNGÜ** → Sistem yeni taleplere hazır

---

## 🔑 ÖNEMLİ NOKTALAR

✅ **QR Kod** → Her lokasyon için benzersiz  
✅ **Oda Numarası** → Opsiyonel (Oda numaram yok seçeneği var)  
✅ **Push Bildirim** → Sadece müsait sürücülere gider  
✅ **İlk Kabul Eden** → Talebi alan sürücü olur  
✅ **Otomatik Durum** → Buggy durumu otomatik güncellenir  
✅ **Lokasyon Seçimi** → İşlem sonunda sürücü konumunu belirtir  

