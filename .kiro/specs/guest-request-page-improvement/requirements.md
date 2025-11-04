# Requirements Document

## Introduction

Bu doküman, misafirlerin QR kod okuttuktan sonra buggy talep etmek için kullandıkları sayfanın görünüm ve kullanıcı deneyimi iyileştirmelerini tanımlar. Mevcut sayfa temel işlevselliğe sahip ancak görsel tasarım, kullanıcı etkileşimi ve mobil deneyim açısından geliştirilmeye ihtiyaç duyuyor.

## Glossary

- **Guest Request Page**: Misafirlerin QR kod okuttuktan sonra buggy talep etmek için kullandıkları sayfa (call_premium.html)
- **QR Scanner Card**: QR kod okutma butonunu içeren kart bileşeni
- **Room Number Card**: Oda numarası girişi ve buggy çağırma butonunu içeren kart
- **Guest Hero Section**: Sayfanın üst kısmındaki logo, başlık ve alt başlık alanı
- **Mobile-First Design**: Öncelikle mobil cihazlar için optimize edilmiş tasarım yaklaşımı
- **Glass Morphism**: Cam efekti veren modern UI tasarım stili
- **Ripple Effect**: Butona tıklandığında dalga efekti animasyonu
- **Loading State**: Yükleme durumunu gösteren görsel geri bildirim
- **Success Feedback**: Başarılı işlem sonrası kullanıcıya verilen görsel geri bildirim

## Requirements

### Requirement 1

**User Story:** Misafir olarak, QR kod okuttuktan sonra buggy talep sayfasının modern ve profesyonel görünmesini istiyorum, böylece uygulamaya güven duyarım.

#### Acceptance Criteria

1. WHEN Guest Request Page yüklendiğinde, THE system SHALL modern gradient arka plan ve glass morphism efektli kartlar gösterecek
2. WHEN Guest Request Page görüntülendiğinde, THE system SHALL tutarlı renk paleti (primary: #1BA5A8, secondary: #F28C38) kullanacak
3. WHEN Guest Request Page açıldığında, THE system SHALL yumuşak gölge efektleri ve border-radius ile modern görünüm sağlayacak
4. WHEN Guest Request Page render edildiğinde, THE system SHALL responsive tasarım ile tüm ekran boyutlarında düzgün görünüm sunacak
5. WHEN Guest Request Page yüklendiğinde, THE system SHALL animasyonlu geçişler ve hover efektleri ile interaktif deneyim sağlayacak

### Requirement 2

**User Story:** Misafir olarak, QR kod okutma butonunun dikkat çekici ve kullanımı kolay olmasını istiyorum, böylece hızlıca işlemi başlatabilirim.

#### Acceptance Criteria

1. WHEN QR Scanner Card görüntülendiğinde, THE system SHALL büyük ve belirgin QR kod ikonu gösterecek
2. WHEN QR Scanner Card render edildiğinde, THE system SHALL açıklayıcı başlık ve alt metin içerecek
3. WHEN kullanıcı QR kod okutma butonuna dokunduğunda, THE system SHALL ripple effect animasyonu gösterecek
4. WHEN QR Scanner Card görüntülendiğinde, THE system SHALL minimum 56px yükseklikte dokunma alanı sağlayacak (mobil için)
5. WHEN kullanıcı butona hover yaptığında, THE system SHALL yukarı kayma ve gölge artışı animasyonu gösterecek

### Requirement 3

**User Story:** Misafir olarak, oda numarası girişi ve buggy çağırma işleminin net ve anlaşılır olmasını istiyorum, böylece kolayca talepte bulunabilirim.

#### Acceptance Criteria

1. WHEN Room Number Card görüntülendiğinde, THE system SHALL ikon ile birlikte açıklayıcı başlık gösterecek
2. WHEN oda numarası input alanı görüntülendiğinde, THE system SHALL placeholder metin ve maksimum karakter sınırı (20) içerecek
3. WHEN kullanıcı buggy çağır butonuna tıkladığında, THE system SHALL loading state ile görsel geri bildirim sağlayacak
4. WHEN buggy çağır butonu görüntülendiğinde, THE system SHALL tam genişlikte ve belirgin gradient arka plana sahip olacak
5. WHEN kullanıcı form alanlarıyla etkileşime geçtiğinde, THE system SHALL focus state ile görsel geri bildirim verecek

### Requirement 4

**User Story:** Misafir olarak, sayfanın mobil cihazlarda mükemmel çalışmasını istiyorum, çünkü çoğunlukla telefonumdan kullanacağım.

#### Acceptance Criteria

1. WHEN sayfa mobil cihazda görüntülendiğinde, THE system SHALL viewport genişliğine göre responsive layout gösterecek
2. WHEN mobil cihazda butonlara dokunulduğunda, THE system SHALL minimum 56px dokunma alanı sağlayacak
3. WHEN mobil cihazda form elemanları görüntülendiğinde, THE system SHALL uygun font boyutları (minimum 16px) kullanacak
4. WHEN sayfa mobil cihazda yüklendiğinde, THE system SHALL hızlı yükleme için optimize edilmiş görseller kullanacak
5. WHEN mobil cihazda scroll yapıldığında, THE system SHALL smooth scrolling davranışı gösterecek

### Requirement 5

**User Story:** Misafir olarak, işlem sırasında ne olduğunu anlamak istiyorum, böylece talebimin durumunu takip edebilirim.

#### Acceptance Criteria

1. WHEN kullanıcı QR kod okuttuğunda, THE system SHALL başarılı okuma için toast notification gösterecek
2. WHEN kullanıcı buggy çağır butonuna tıkladığında, THE system SHALL loading spinner ve "Buggy çağrılıyor..." mesajı gösterecek
3. WHEN talep başarıyla oluşturulduğunda, THE system SHALL success modal ile 5 saniye uyarı mesajı gösterecek
4. WHEN hata oluştuğunda, THE system SHALL kullanıcı dostu hata mesajı gösterecek
5. WHEN işlem tamamlandığında, THE system SHALL otomatik olarak status sayfasına yönlendirecek

### Requirement 6

**User Story:** Misafir olarak, sayfanın görsel hiyerarşisinin net olmasını istiyorum, böylece hangi adımı takip edeceğimi kolayca anlayabilirim.

#### Acceptance Criteria

1. WHEN sayfa yüklendiğinde, THE system SHALL hero section'ı en üstte belirgin şekilde gösterecek
2. WHEN QR kod okutulmadığında, THE system SHALL QR Scanner Card'ı öncelikli olarak gösterecek
3. WHEN QR kod okutulduğunda, THE system SHALL QR Scanner Card'ı gizleyip Room Number Card'ı gösterecek
4. WHEN kartlar görüntülendiğinde, THE system SHALL aralarında uygun spacing (24px) kullanacak
5. WHEN sayfa elemanları render edildiğinde, THE system SHALL z-index ile doğru katmanlama sağlayacak

### Requirement 7

**User Story:** Misafir olarak, sayfanın erişilebilir olmasını istiyorum, böylece farklı yeteneklere sahip kullanıcılar da kullanabilir.

#### Acceptance Criteria

1. WHEN form elemanları render edildiğinde, THE system SHALL uygun label ve aria-label attribute'ları içerecek
2. WHEN butonlar görüntülendiğinde, THE system SHALL anlamlı ikon ve metin kombinasyonu kullanacak
3. WHEN renk kullanıldığında, THE system SHALL WCAG AA standardına uygun kontrast oranı sağlayacak
4. WHEN klavye ile navigasyon yapıldığında, THE system SHALL görünür focus indicator gösterecek
5. WHEN ekran okuyucu kullanıldığında, THE system SHALL anlamlı semantik HTML yapısı sunacak

### Requirement 8

**User Story:** Misafir olarak, sayfanın performanslı olmasını istiyorum, böylece hızlı bir şekilde buggy çağırabilirim.

#### Acceptance Criteria

1. WHEN sayfa yüklendiğinde, THE system SHALL 2 saniyeden kısa sürede First Contentful Paint gerçekleştirecek
2. WHEN animasyonlar çalıştığında, THE system SHALL 60 FPS performans sağlayacak
3. WHEN görseller yüklendiğinde, THE system SHALL lazy loading kullanacak
4. WHEN CSS ve JS dosyaları yüklendiğinde, THE system SHALL minified versiyonları kullanacak
5. WHEN API çağrıları yapıldığında, THE system SHALL debounce/throttle teknikleri uygulayacak
