# Requirements Document - Production Ready System Audit & Fixes

## Introduction

Bu özellik, BuggyCall sisteminin production-ready duruma getirilmesi için kapsamlı bir audit ve iyileştirme sürecidir. Mevcut sistemdeki kritik akışlar incelenecek, özellikle iOS Safari PWA ve FCM bildirim sistemleri optimize edilecek, zaman damgası yönetimi düzeltilecek ve gerçek zamanlı güncellemeler iyileştirilecektir.

## Glossary

- **System**: BuggyCall web uygulaması
- **Guest**: Misafir kullanıcı (shuttle talep eden)
- **Driver**: Shuttle sürücüsü rolündeki kullanıcı
- **Admin**: Sistem yöneticisi rolündeki kullanıcı
- **FCM**: Firebase Cloud Messaging - Push notification servisi
- **PWA**: Progressive Web App - Tarayıcıda çalışan uygulama
- **iOS Safari**: Apple iOS cihazlardaki Safari tarayıcısı
- **WebSocket**: Socket.IO üzerinden gerçek zamanlı iletişim
- **Request**: Shuttle talebi
- **Timestamp**: Zaman damgası (talep zamanı, kabul zamanı, tamamlanma zamanı)
- **Status Update**: Durum güncelleme bildirimi
- **Connection Indicator**: Bağlantı durumu göstergesi (yanıp sönen icon)
- **Notification Permission**: Tarayıcı bildirim izni
- **Buggy Status**: Shuttle durumu (available/müsait, busy/meşgul, offline/çevrimdışı)
- **Service Worker**: Arka planda çalışan JavaScript worker thread
- **Background Sync**: Arka plan senkronizasyonu
- **Foreground**: Uygulama açık ve aktif durumda
- **Background**: Uygulama kapalı veya arka planda

## Requirements

### Requirement 1: Guest Bağlantı Bildirimi (Yanıp Sönen Icon)

**User Story:** Sürücü olarak, bir misafirin sisteme bağlandığını ve talep oluşturmak üzere olduğunu yanıp sönen bir icon ile görmek istiyorum, böylece yaklaşan taleplere hazırlıklı olabilirim.

#### Acceptance Criteria

1. WHEN a guest opens the request page, THE System SHALL emit a WebSocket event to notify all active drivers
2. WHEN a driver dashboard receives the guest connection event, THE System SHALL display a blinking notification icon
3. THE blinking icon SHALL be visible for 10 seconds or until a new request is created
4. WHEN multiple guests are connected simultaneously, THE System SHALL show the count of connected guests next to the icon
5. WHEN a guest closes the page without creating a request, THE System SHALL emit a disconnect event and remove the guest from the count

### Requirement 2: Gerçek Zamanlı Talep Görüntüleme

**User Story:** Sürücü olarak, yeni bir talep oluşturulduğunda dashboard'umda anında görmek istiyorum, böylece hızlıca kabul edebilirim.

#### Acceptance Criteria

1. WHEN a new request is created, THE System SHALL send both WebSocket and FCM notifications to all available drivers
2. WHEN a driver dashboard is in foreground, THE System SHALL display the new request immediately via WebSocket
3. WHEN a driver dashboard is in background or closed, THE System SHALL deliver the notification via FCM
4. THE new request SHALL appear in the pending requests list without page refresh
5. THE request SHALL include location name, room number, guest name, and elapsed time since creation

### Requirement 3: FCM Bildirim Gönderimi (Sürücülere)

**User Story:** Sürücü olarak, uygulama kapalıyken bile yeni talepleri FCM push notification ile almak istiyorum, böylece hiçbir talebi kaçırmam.

#### Acceptance Criteria

1. WHEN a new request is created, THE System SHALL send high-priority FCM notifications to all available drivers
2. THE FCM notification SHALL include action buttons: "Kabul Et" (Accept) and "Detaylar" (Details)
3. WHEN a driver clicks "Kabul Et" button, THE System SHALL accept the request and open the app
4. WHEN a driver clicks "Detaylar" button, THE System SHALL open the app to the request details page
5. THE FCM notification SHALL include request details in the data payload for offline access

### Requirement 4: Guest Bildirim İzni Yönetimi

**User Story:** Misafir olarak, talep oluşturduktan sonra bildirim izni vermek istiyorum, böylece talep durumu hakkında bilgilendirilirim.

#### Acceptance Criteria

1. WHEN a guest creates a request, THE System SHALL display a notification permission dialog
2. THE permission dialog SHALL appear after the request is successfully created
3. WHEN the guest grants notification permission, THE System SHALL register the FCM token with the request
4. WHEN the guest denies notification permission, THE System SHALL allow the request to proceed without notifications
5. IF notification permission is already granted, THEN THE System SHALL automatically register the FCM token

### Requirement 5: Guest Status Ekranı Gerçek Zamanlı Güncelleme

**User Story:** Misafir olarak, talebimin durumunu (kabul edildi, tamamlandı) bildirim izni vermesem bile gerçek zamanlı görmek istiyorum, böylece shuttle'ın durumunu takip edebilirim.

#### Acceptance Criteria

1. WHEN a driver accepts the guest's request, THE System SHALL update the guest status page via WebSocket immediately
2. WHEN a driver completes the guest's request, THE System SHALL update the guest status page via WebSocket immediately
3. IF the guest has granted notification permission, THEN THE System SHALL also send FCM notification
4. IF the guest has not granted notification permission, THEN THE System SHALL only update via WebSocket
5. THE status page SHALL display the current status, driver name, buggy code, and estimated arrival time

### Requirement 6: Sürücü Görev Tamamlama ve Otomatik Müsait Duruma Geçiş

**User Story:** Sürücü olarak, görevi tamamlayıp yeni lokasyon seçtiğimde buggy'min otomatik olarak müsait duruma geçmesini istiyorum, böylece yeni talepleri alabilirim.

#### Acceptance Criteria

1. WHEN a driver completes a request, THE System SHALL prompt the driver to select the current location
2. WHEN the driver selects a location, THE System SHALL update the buggy's current location
3. WHEN the location is updated, THE System SHALL automatically set the buggy status to AVAILABLE
4. WHEN the buggy status changes to AVAILABLE, THE System SHALL notify all admin dashboards via WebSocket
5. THE System SHALL log the completion time and location change in the audit trail

### Requirement 7: Zaman Damgası Yönetimi (Timestamps)

**User Story:** Sistem yöneticisi olarak, her talebin oluşturulma, kabul edilme ve tamamlanma zamanlarının doğru kaydedilmesini istiyorum, böylece performans metriklerini analiz edebilirim.

#### Acceptance Criteria

1. WHEN a request is created, THE System SHALL record the requested_at timestamp in the database
2. WHEN a driver accepts a request, THE System SHALL record the accepted_at timestamp and calculate response_time
3. WHEN a driver completes a request, THE System SHALL record the completed_at timestamp and calculate completion_time
4. THE response_time SHALL be calculated as (accepted_at - requested_at) in seconds
5. THE completion_time SHALL be calculated as (completed_at - accepted_at) in seconds

### Requirement 8: Geçen Süre Gösterimi (Elapsed Time)

**User Story:** Sürücü olarak, dashboard'da bekleyen taleplerin üzerinden geçen süreyi görmek istiyorum, böylece hangi talebin daha acil olduğunu anlayabilirim.

#### Acceptance Criteria

1. WHEN a request is displayed in the driver dashboard, THE System SHALL show the elapsed time since creation
2. THE elapsed time SHALL update every second without page refresh
3. THE elapsed time SHALL be displayed in a human-readable format (e.g., "2 dakika önce", "30 saniye önce")
4. WHEN a request is older than 5 minutes, THE System SHALL highlight it with a warning color
5. WHEN a request is older than 10 minutes, THE System SHALL highlight it with an urgent color

### Requirement 9: iOS Safari PWA Optimizasyonu

**User Story:** iOS kullanıcısı olarak, Safari'de PWA olarak çalışan uygulamanın bildirimlerini güvenilir şekilde almak istiyorum, böylece sistem sorunsuz çalışır.

#### Acceptance Criteria

1. WHEN the app is installed as PWA on iOS, THE System SHALL register a Service Worker for FCM
2. THE Service Worker SHALL handle background FCM messages even when the app is closed
3. WHEN an FCM message arrives on iOS Safari, THE System SHALL display a system notification
4. WHEN the user clicks the notification, THE System SHALL open the PWA to the relevant page
5. THE System SHALL implement iOS-specific workarounds for notification limitations

### Requirement 10: FCM Token Yönetimi ve Yenileme

**User Story:** Sistem olarak, FCM token'larını otomatik yönetmek ve yenilemek istiyorum, böylece bildirimler kesintisiz çalışır.

#### Acceptance Criteria

1. WHEN a user opens the app, THE System SHALL check if the FCM token is valid
2. WHEN the FCM token is expired or invalid, THE System SHALL automatically refresh it
3. WHEN a new token is generated, THE System SHALL send it to the backend for registration
4. WHEN the backend receives a token update, THE System SHALL update the user's token in the database
5. THE System SHALL log all token refresh operations for debugging

### Requirement 11: Geçersiz Token Temizleme

**User Story:** Sistem olarak, geçersiz FCM token'larını otomatik temizlemek istiyorum, böylece veritabanı temiz ve verimli kalır.

#### Acceptance Criteria

1. WHEN an FCM notification fails with "invalid token" error, THE System SHALL mark the token as invalid
2. WHEN a token is marked as invalid, THE System SHALL remove it from the database
3. WHEN sending to multiple tokens, THE System SHALL collect all invalid tokens
4. WHEN invalid tokens are collected, THE System SHALL remove them in a single database operation
5. THE System SHALL log all token cleanup operations

### Requirement 12: WebSocket Bağlantı Durumu Göstergesi

**User Story:** Kullanıcı olarak, WebSocket bağlantı durumunu görmek istiyorum, böylece gerçek zamanlı güncellemelerin çalışıp çalışmadığını bilebilirim.

#### Acceptance Criteria

1. WHEN WebSocket connection is established, THE System SHALL display a green connection indicator
2. WHEN WebSocket connection is lost, THE System SHALL display a red connection indicator
3. WHEN reconnection is in progress, THE System SHALL display a yellow connection indicator
4. WHEN connection status changes, THE System SHALL show a brief notification to the user
5. WHEN connection is lost for more than 30 seconds, THE System SHALL show an error message

### Requirement 13: Hybrid Socket.IO + FCM Yaklaşımı

**User Story:** Sistem olarak, uygulama açıkken Socket.IO, kapalıyken FCM kullanmak istiyorum, böylece en iyi performansı sağlarım.

#### Acceptance Criteria

1. WHEN the app is in foreground, THE System SHALL use Socket.IO for real-time updates
2. WHEN the app is in background or closed, THE System SHALL use FCM for push notifications
3. WHEN both Socket.IO and FCM are available, THE System SHALL prefer Socket.IO for lower latency
4. WHEN Socket.IO connection fails, THE System SHALL fall back to FCM
5. THE System SHALL send both Socket.IO and FCM messages to ensure delivery

### Requirement 14: Service Worker Lifecycle Yönetimi

**User Story:** Geliştirici olarak, Service Worker'ın doğru şekilde yüklenmesini ve güncellenmesini istiyorum, böylece FCM bildirimleri kesintisiz çalışır.

#### Acceptance Criteria

1. WHEN the app loads, THE System SHALL register the Service Worker if not already registered
2. WHEN a new Service Worker version is available, THE System SHALL update it automatically
3. WHEN the Service Worker is updated, THE System SHALL notify the user to refresh the page
4. WHEN the Service Worker fails to register, THE System SHALL log the error and retry
5. THE Service Worker SHALL cache notification sounds for offline playback

### Requirement 15: iOS Safari Notification Workarounds

**User Story:** Geliştirici olarak, iOS Safari'nin bildirim kısıtlamalarını aşmak istiyorum, böylece kullanıcılar güvenilir bildirimler alır.

#### Acceptance Criteria

1. WHEN detecting iOS Safari, THE System SHALL implement platform-specific notification handling
2. THE System SHALL use APNs (Apple Push Notification service) configuration for iOS devices
3. WHEN the app is in background on iOS, THE System SHALL ensure notifications wake the device
4. THE System SHALL handle iOS notification permission states correctly (granted, denied, default)
5. THE System SHALL provide fallback mechanisms for iOS notification limitations

### Requirement 16: Notification Priority Yönetimi

**User Story:** Sistem olarak, bildirimleri öncelik seviyelerine göre göndermek istiyorum, böylece acil talepler hemen iletilir.

#### Acceptance Criteria

1. WHEN sending a new request notification, THE System SHALL set priority to "high"
2. WHEN sending a request accepted notification, THE System SHALL set priority to "normal"
3. WHEN sending a request completed notification, THE System SHALL set priority to "low"
4. WHEN priority is "high", THE System SHALL configure the notification to bypass battery optimization
5. WHEN priority is "high", THE System SHALL enable sound and vibration

### Requirement 17: Bildirim Teslim Durumu İzleme

**User Story:** Sistem yöneticisi olarak, FCM bildirimlerinin teslim durumunu izlemek istiyorum, böylece sistemin doğru çalıştığından emin olabilirim.

#### Acceptance Criteria

1. WHEN an FCM notification is sent, THE System SHALL log the delivery attempt in the database
2. WHEN an FCM notification is successfully delivered, THE System SHALL record the status as "sent"
3. WHEN an FCM notification fails to deliver, THE System SHALL record the failure reason
4. WHEN a user clicks an FCM notification, THE System SHALL record the interaction timestamp
5. THE System SHALL provide an admin API endpoint to retrieve notification statistics

### Requirement 18: Hata Yönetimi ve Fallback Mekanizmaları

**User Story:** Geliştirici olarak, FCM hatalarını düzgün yönetmek ve fallback mekanizmaları sağlamak istiyorum, böylece sistem stabil kalır.

#### Acceptance Criteria

1. WHEN Firebase Admin SDK initialization fails, THE System SHALL log the error and continue without FCM
2. WHEN an FCM notification fails to send, THE System SHALL log the error with full context
3. WHEN a Service Worker error occurs, THE System SHALL attempt to recover automatically
4. IF automatic recovery fails, THEN THE System SHALL notify the admin of the failure
5. THE System SHALL provide fallback mechanisms for critical notifications

### Requirement 19: Admin Dashboard Gerçek Zamanlı Güncellemeler

**User Story:** Admin olarak, tüm taleplerin ve buggy durumlarının gerçek zamanlı güncellenmesini istiyorum, böylece sistemi etkin şekilde yönetebilirim.

#### Acceptance Criteria

1. WHEN a new request is created, THE System SHALL update the admin dashboard via WebSocket
2. WHEN a request status changes, THE System SHALL update the admin dashboard via WebSocket
3. WHEN a buggy status changes, THE System SHALL update the admin dashboard via WebSocket
4. WHEN a driver session starts or ends, THE System SHALL update the admin dashboard via WebSocket
5. THE admin dashboard SHALL display real-time statistics without page refresh

### Requirement 20: Performance Optimizasyonu

**User Story:** Kullanıcı olarak, sistemin hızlı ve responsive olmasını istiyorum, böylece sorunsuz bir deneyim yaşarım.

#### Acceptance Criteria

1. WHEN multiple WebSocket updates arrive, THE System SHALL throttle updates to maximum 10 per second
2. WHEN updating the DOM, THE System SHALL only update changed elements
3. WHEN the page is in background, THE System SHALL defer DOM updates until the page is active
4. WHEN the page becomes active, THE System SHALL apply deferred updates in batch
5. THE System SHALL use efficient database queries with proper indexing

### Requirement 21: Audit Trail ve Logging

**User Story:** Sistem yöneticisi olarak, tüm kritik işlemlerin loglanmasını istiyorum, böylece sorunları kolayca debug edebilirim.

#### Acceptance Criteria

1. WHEN a request is created, THE System SHALL log the action with full context
2. WHEN a request is accepted, THE System SHALL log the driver, buggy, and response time
3. WHEN a request is completed, THE System SHALL log the completion time and location
4. WHEN an FCM notification is sent, THE System SHALL log the delivery status
5. THE System SHALL provide admin access to all audit logs with filtering and search

### Requirement 22: Test Endpoint ve Debugging

**User Story:** Geliştirici olarak, FCM sistemini test edebilmek istiyorum, böylece sorunları hızlıca tespit edebilirim.

#### Acceptance Criteria

1. THE System SHALL provide a POST endpoint at /api/fcm/test-notification
2. WHEN the test endpoint is called, THE System SHALL send a test notification to the current user
3. WHEN the test notification is sent, THE System SHALL return the delivery status
4. THE test endpoint SHALL require authentication
5. THE test endpoint SHALL log all test notification attempts

### Requirement 23: Environment Configuration

**User Story:** Geliştirici olarak, farklı ortamlar için farklı Firebase konfigürasyonları kullanmak istiyorum, böylece development ve production ayrı çalışır.

#### Acceptance Criteria

1. THE System SHALL read Firebase configuration from environment variables
2. WHEN environment variables are missing, THE System SHALL log a warning and disable FCM
3. THE System SHALL support separate Firebase projects for development and production
4. THE System SHALL validate Firebase configuration on startup
5. THE System SHALL provide clear error messages for configuration issues

### Requirement 24: Guest FCM Token Yönetimi

**User Story:** Sistem olarak, misafir FCM token'larını talep bazında yönetmek istiyorum, böylece misafirlere doğru bildirimler gönderilir.

#### Acceptance Criteria

1. WHEN a guest grants notification permission, THE System SHALL store the FCM token with the request ID
2. THE FCM token SHALL be stored in memory (not database) for security
3. WHEN a request is accepted, THE System SHALL use the stored token to send notification
4. WHEN a request is completed, THE System SHALL use the stored token to send notification
5. WHEN a request is closed, THE System SHALL remove the token from memory

### Requirement 25: Notification Action Handling

**User Story:** Sürücü olarak, bildirim üzerindeki action butonlarına tıkladığımda doğru sayfaya yönlendirilmek istiyorum, böylece hızlıca işlem yapabilirim.

#### Acceptance Criteria

1. WHEN a driver clicks "Kabul Et" action button, THE System SHALL accept the request via API
2. WHEN the accept action succeeds, THE System SHALL open the app to the driver dashboard
3. WHEN a driver clicks "Detaylar" action button, THE System SHALL open the app to the request details page
4. WHEN an action button is clicked, THE System SHALL close the notification
5. THE System SHALL handle action button clicks even when the app is closed

### Requirement 26: Offline Support ve Background Sync

**User Story:** Kullanıcı olarak, internet bağlantısı kesildiğinde bile temel işlevlerin çalışmasını istiyorum, böylece kesintisiz hizmet alırım.

#### Acceptance Criteria

1. WHEN the app goes offline, THE System SHALL display an offline indicator
2. WHEN offline, THE System SHALL cache critical data in IndexedDB
3. WHEN the connection is restored, THE System SHALL sync pending actions automatically
4. THE Service Worker SHALL cache static assets for offline access
5. THE System SHALL queue failed FCM notifications for retry when online

### Requirement 27: Multi-Device Support

**User Story:** Kullanıcı olarak, birden fazla cihazda aynı anda login olabilmek istiyorum, böylece esnek şekilde çalışabilirim.

#### Acceptance Criteria

1. WHEN a user logs in from multiple devices, THE System SHALL register separate FCM tokens for each device
2. WHEN sending notifications, THE System SHALL send to all registered devices
3. WHEN a user logs out from one device, THE System SHALL only remove that device's FCM token
4. THE System SHALL limit maximum 5 active devices per user
5. THE System SHALL provide a UI to manage registered devices

### Requirement 28: Notification Sound Customization

**User Story:** Sürücü olarak, farklı öncelik seviyelerinde farklı bildirim sesleri duymak istiyorum, böylece acil talepleri hemen fark edebilirim.

#### Acceptance Criteria

1. WHEN a high-priority notification arrives, THE System SHALL play an urgent sound
2. WHEN a normal-priority notification arrives, THE System SHALL play a standard sound
3. WHEN a low-priority notification arrives, THE System SHALL play a subtle sound
4. THE System SHALL cache notification sounds in the Service Worker
5. THE System SHALL allow users to customize notification sounds in settings

### Requirement 29: Battery Optimization Bypass

**User Story:** Sürücü olarak, cihazımın pil tasarrufu modunda bile bildirimleri almak istiyorum, böylece hiçbir talebi kaçırmam.

#### Acceptance Criteria

1. WHEN sending high-priority notifications, THE System SHALL configure them to bypass battery optimization
2. THE System SHALL use FCM high-priority delivery for urgent notifications
3. THE System SHALL provide instructions to users on disabling battery optimization for the app
4. THE System SHALL detect if battery optimization is enabled and warn the user
5. THE System SHALL test notification delivery in battery saver mode

### Requirement 30: Production Readiness Checklist

**User Story:** Geliştirici olarak, sistemin production-ready olduğundan emin olmak istiyorum, böylece güvenle deploy edebilirim.

#### Acceptance Criteria

1. THE System SHALL have comprehensive error handling for all critical paths
2. THE System SHALL have proper logging for debugging and monitoring
3. THE System SHALL have automated tests for critical functionality
4. THE System SHALL have performance monitoring and alerting
5. THE System SHALL have documentation for deployment and maintenance
