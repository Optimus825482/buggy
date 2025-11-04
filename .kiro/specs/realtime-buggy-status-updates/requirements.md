# Requirements Document

## Introduction

Admin panelindeki "Buggy Durumu" listesinin WebSocket üzerinden gerçek zamanlı güncellenmesi. Sayfa yenilenmeden buggy durumlarının (müsait, meşgul, çevrimdışı) anlık olarak güncellenmesi sağlanacak.

## Glossary

- **Admin Dashboard**: Sistem yöneticisinin buggy'leri, talepleri ve istatistikleri görüntülediği ana panel
- **Buggy Durumu Listesi**: Tüm buggy'lerin durumlarını gösteren liste bileşeni
- **WebSocket**: İstemci ve sunucu arasında çift yönlü, gerçek zamanlı iletişim sağlayan protokol
- **Buggy Status**: Buggy'nin mevcut durumu (available/müsait, busy/meşgul, offline/çevrimdışı)
- **Real-time Update**: Sayfa yenilenmeden otomatik veri güncellenmesi
- **Socket.IO**: WebSocket bağlantılarını yöneten JavaScript kütüphanesi
- **Status Change Event**: Buggy durumu değiştiğinde tetiklenen WebSocket olayı

## Requirements

### Requirement 1

**User Story:** Admin olarak, buggy durumlarının sayfa yenilenmeden otomatik güncellenmesini istiyorum, böylece her zaman güncel bilgileri görebilirim.

#### Acceptance Criteria

1. WHEN admin dashboard yüklendiğinde, THE Admin Dashboard SHALL WebSocket bağlantısı kurar
2. WHEN bir buggy'nin durumu değiştiğinde, THE System SHALL tüm bağlı admin istemcilerine durum değişikliği bildirir
3. WHEN durum değişikliği bildirimi alındığında, THE Admin Dashboard SHALL ilgili buggy'nin durumunu listede günceller
4. WHEN güncelleme yapılırken, THE Admin Dashboard SHALL sayfa yenilenmeden DOM'u günceller
5. WHEN WebSocket bağlantısı koptuğunda, THE Admin Dashboard SHALL otomatik yeniden bağlanma dener

### Requirement 2

**User Story:** Admin olarak, buggy durumlarının görsel olarak net bir şekilde gösterilmesini istiyorum, böylece hangi buggy'nin hangi durumda olduğunu hızlıca anlayabilirim.

#### Acceptance Criteria

1. WHEN buggy müsait durumuna geçtiğinde, THE Admin Dashboard SHALL "Çevrimiçi" etiketini yeşil renkte gösterir
2. WHEN buggy meşgul durumuna geçtiğinde, THE Admin Dashboard SHALL "Meşgul" etiketini turuncu/sarı renkte gösterir
3. WHEN buggy çevrimdışı durumuna geçtiğinde, THE Admin Dashboard SHALL "Çevrimdışı" etiketini gri renkte gösterir
4. WHEN durum değiştiğinde, THE Admin Dashboard SHALL yumuşak bir geçiş animasyonu uygular
5. WHEN durum güncellendiğinde, THE Admin Dashboard SHALL buggy sıralamasını korur

### Requirement 3

**User Story:** Admin olarak, driver session durumlarının da gerçek zamanlı güncellenmesini istiyorum, böylece hangi driver'ın hangi buggy'yi kullandığını anlık görebilirim.

#### Acceptance Criteria

1. WHEN bir driver session başladığında, THE System SHALL admin istemcilerine session başlangıç bildirimi gönderir
2. WHEN bir driver session sonlandığında, THE System SHALL admin istemcilerine session bitiş bildirimi gönderir
3. WHEN session bildirimi alındığında, THE Admin Dashboard SHALL ilgili buggy'nin driver bilgisini günceller
4. WHEN aktif session varsa, THE Admin Dashboard SHALL driver adını buggy yanında gösterir
5. WHEN session yoksa, THE Admin Dashboard SHALL driver bilgisini boş bırakır

### Requirement 4

**User Story:** Admin olarak, WebSocket bağlantı durumunu görmek istiyorum, böylece gerçek zamanlı güncellemelerin çalışıp çalışmadığını bilebilirim.

#### Acceptance Criteria

1. WHEN WebSocket bağlantısı başarılı olduğunda, THE Admin Dashboard SHALL bağlantı durumu göstergesini yeşil yapar
2. WHEN WebSocket bağlantısı koptuğunda, THE Admin Dashboard SHALL bağlantı durumu göstergesini kırmızı yapar
3. WHEN yeniden bağlanma denenirken, THE Admin Dashboard SHALL bağlantı durumu göstergesini sarı yapar
4. WHEN bağlantı durumu değiştiğinde, THE Admin Dashboard SHALL kullanıcıya kısa bir bildirim gösterir
5. WHEN bağlantı 30 saniye boyunca kurulamazsa, THE Admin Dashboard SHALL kullanıcıya hata mesajı gösterir

### Requirement 5

**User Story:** Admin olarak, sistem performansının etkilenmemesini istiyorum, böylece gerçek zamanlı güncellemeler dashboard'u yavaşlatmaz.

#### Acceptance Criteria

1. WHEN durum güncellemeleri alındığında, THE Admin Dashboard SHALL sadece değişen buggy'lerin DOM elementlerini günceller
2. WHEN çok sayıda güncelleme geldiğinde, THE System SHALL güncellemeleri throttle eder (maksimum 1 saniyede 10 güncelleme)
3. WHEN admin dashboard kapatıldığında, THE System SHALL WebSocket bağlantısını temiz bir şekilde kapatır
4. WHEN sayfa arka planda olduğunda, THE System SHALL WebSocket bağlantısını aktif tutar ama DOM güncellemelerini erteler
5. WHEN sayfa tekrar ön plana geldiğinde, THE Admin Dashboard SHALL ertelenen güncellemeleri toplu olarak uygular
