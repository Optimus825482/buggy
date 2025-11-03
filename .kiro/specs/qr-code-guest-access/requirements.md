# Requirements Document

## Introduction

QR kod sistemi, sistem tanımlanan lokasyonlar için oluşturulan QR kodların hem lokasyon bilgisini hem de misafirlerin sisteme doğrudan erişebilmesi için gerekli URL'yi içermesini sağlamalıdır. Şu anda QR kodlar sadece lokasyon ID'si içeriyor ve misafirler QR kodu taradıklarında sisteme erişemiyor.

## Glossary

- **QR Code System**: Lokasyonlar için QR kod oluşturma ve tarama sistemi
- **Guest Access URL**: Misafirlerin buggy çağırma sayfasına doğrudan erişmelerini sağlayan URL
- **Location ID**: Veritabanında her lokasyonun benzersiz kimlik numarası
- **QR Code Data**: QR kod içinde saklanan veri (URL formatında)

## Requirements

### Requirement 1

**User Story:** Bir admin olarak, lokasyonlar için oluşturduğum QR kodların misafirlerin doğrudan sisteme erişmesini sağlamasını istiyorum, böylece misafirler QR kodu taradıklarında otomatik olarak buggy çağırma sayfasına yönlendirilsin.

#### Acceptance Criteria

1. WHEN admin bir lokasyon için QR kod oluşturduğunda, THE QR Code System SHALL tam bir URL içeren QR kod üretmeli (örnek: `https://domain.com/guest/call?location=123`)

2. WHEN misafir QR kodu taradığında, THE QR Code System SHALL misafiri otomatik olarak ilgili lokasyon için buggy çağırma sayfasına yönlendirmeli

3. THE QR Code System SHALL QR kod verisini `qr_code_data` alanında URL formatında saklamalı

4. WHEN QR kod yazdırma sayfası açıldığında, THE QR Code System SHALL her lokasyon için doğru URL içeren QR kodlar oluşturmalı

### Requirement 2

**User Story:** Bir misafir olarak, lokasyondaki QR kodu taradığımda doğrudan buggy çağırma sayfasına erişmek istiyorum, böylece ekstra adım atmadan hızlıca buggy çağırabilirim.

#### Acceptance Criteria

1. WHEN misafir QR kodu taradığında, THE QR Code System SHALL URL'yi otomatik olarak açmalı

2. THE QR Code System SHALL URL'de lokasyon ID'sini query parameter olarak içermeli

3. WHEN buggy çağırma sayfası açıldığında, THE QR Code System SHALL lokasyon bilgisini otomatik olarak doldurmalı

4. IF QR kod geçersiz bir URL içeriyorsa, THEN THE QR Code System SHALL kullanıcıya hata mesajı göstermeli

### Requirement 3

**User Story:** Bir sistem yöneticisi olarak, mevcut lokasyonların QR kod verilerinin yeni URL formatına güncellenmesini istiyorum, böylece eski QR kodlar da çalışmaya devam etsin.

#### Acceptance Criteria

1. THE QR Code System SHALL mevcut `LOC` formatındaki QR kodları desteklemeye devam etmeli (geriye dönük uyumluluk)

2. WHEN sistem yeni URL formatını algıladığında, THE QR Code System SHALL URL'yi parse edip lokasyon ID'sini çıkarmalı

3. WHEN sistem eski `LOC` formatını algıladığında, THE QR Code System SHALL eski mantığı kullanarak lokasyonu bulmalı

4. THE QR Code System SHALL her iki formatı da doğru şekilde işleyebilmeli
