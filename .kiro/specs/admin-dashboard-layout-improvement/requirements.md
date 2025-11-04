# Requirements Document

## Introduction

Admin dashboard'un kullanıcı deneyimini iyileştirmek için layout düzenlemesi ve buggy görselleştirme sistemi. Widget'ların konumlandırılması optimize edilecek ve her buggy için benzersiz icon sistemi eklenecek.

## Glossary

- **Admin Dashboard**: Sistem yöneticisinin buggy'leri, talepleri ve istatistikleri görüntülediği ana panel
- **Widget**: Dashboard'da istatistik bilgilerini gösteren küçük bilgi kutuları (Aktif Buggy, Bekleyen Talepler, vb.)
- **Buggy Durumu Listesi**: Tüm buggy'lerin durumlarını gösteren liste bileşeni
- **Aktif Talepler Listesi**: Bekleyen ve işlemdeki talepleri gösteren liste bileşeni
- **Buggy Icon**: Her buggy'yi temsil eden benzersiz emoji/sembol
- **Icon Set**: Buggy'lere atanabilecek 33 araç/taşıt temalı emoji koleksiyonu

## Requirements

### Requirement 1

**User Story:** Admin olarak, dashboard'da önce önemli listeleri (aktif talepler ve buggy durumu) görmek, ardından özet istatistikleri görmek istiyorum, böylece acil durumları hızlıca fark edebilirim.

#### Acceptance Criteria

1. WHEN admin dashboard yüklendiğinde, THE Admin Dashboard SHALL "Aktif Talepler" listesini sayfanın üst kısmında gösterir
2. WHEN admin dashboard yüklendiğinde, THE Admin Dashboard SHALL "Buggy Durumu" listesini "Aktif Talepler" listesinin hemen altında gösterir
3. WHEN admin dashboard yüklendiğinde, THE Admin Dashboard SHALL widget'ları (Aktif Buggy, Bekleyen Talepler, Bugün Tamamlanan, Toplam Lokasyon) listelerin altında gösterir
4. WHEN layout değiştirildiğinde, THE Admin Dashboard SHALL responsive tasarımı korur

### Requirement 2

**User Story:** Admin olarak, her buggy'yi farklı bir icon ile görmek istiyorum, böylece buggy'leri hızlıca ayırt edebilirim.

#### Acceptance Criteria

1. WHEN yeni bir buggy kaydedildiğinde, THE System SHALL tanımlı icon setinden (🏎 🚁 ✈ 💺 🚂 🚊 🚉 🚞 🚆 🚄 🚅 🚈 🚇 🚝 🚋 🚃 🚎 🚌 🚍 🚙 🚘 🚗 🚕 🚖 🚛 🚚 🚨 🚓 🚔 🚒 🚑 🚐 🚜) bir icon seçer ve buggy'ye atar
2. WHEN icon seçimi yapılırken, THE System SHALL mevcut tüm buggy'lerin kullandığı icon'ları kontrol eder
3. WHEN kullanılmamış icon bulunduğunda, THE System SHALL kullanılmamış icon'lardan birini seçer
4. WHEN tüm icon'lar kullanıldığında, THE System SHALL icon setinden herhangi birini seçer
5. WHEN buggy durumu listesi görüntülendiğinde, THE Admin Dashboard SHALL her buggy'nin yanında atanmış icon'unu gösterir

### Requirement 3

**User Story:** Admin olarak, buggy icon'larının görsel olarak tutarlı ve anlamlı olmasını istiyorum, böylece profesyonel bir arayüz deneyimi yaşarım.

#### Acceptance Criteria

1. WHEN buggy listesi görüntülendiğinde, THE Admin Dashboard SHALL icon'ları buggy adının önünde gösterir
2. WHEN icon görüntülendiğinde, THE Admin Dashboard SHALL icon boyutunu okunabilir bir şekilde ayarlar
3. WHEN icon seti kullanıldığında, THE System SHALL toplam 33 farklı araç/taşıt temalı icon içerir
4. WHEN database'de icon saklanırken, THE System SHALL icon'u text/emoji formatında saklar

### Requirement 4

**User Story:** Admin olarak, widget'ların hala görünür ve erişilebilir olmasını istiyorum, böylece genel istatistiklere hızlıca bakabilirim.

#### Acceptance Criteria

1. WHEN widget'lar listelerin altına taşındığında, THE Admin Dashboard SHALL tüm widget'ları grid layout ile düzenler
2. WHEN widget'lar görüntülendiğinde, THE Admin Dashboard SHALL her widget'ın başlığını ve değerini net bir şekilde gösterir
3. WHEN sayfa scroll edildiğinde, THE Admin Dashboard SHALL widget'lara kolayca erişim sağlar
4. WHEN mobil cihazda görüntülendiğinde, THE Admin Dashboard SHALL widget'ları tek sütunda gösterir
