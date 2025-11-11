# Requirements Document

## Introduction

Bu özellik, BuggyCall uygulamasının push bildirim sistemini mobil ve tablet cihazlar için optimize eder. Uygulama arka planda, minimize edilmiş durumda veya kilit ekranında bile bildirimlerin güvenilir bir şekilde gösterilmesini sağlar. Progressive Web App (PWA) standartlarına uygun, gelişmiş Service Worker tabanlı bir bildirim sistemi oluşturulacaktır.

## Glossary

- **System**: BuggyCall web uygulaması
- **Driver**: Buggy sürücüsü rolündeki kullanıcı
- **Admin**: Sistem yöneticisi rolündeki kullanıcı
- **Guest**: Misafir kullanıcı (buggy talep eden)
- **Push Notification**: Sunucudan cihaza gönderilen anlık bildirim
- **Service Worker**: Arka planda çalışan JavaScript worker thread
- **PWA**: Progressive Web App - gelişmiş web uygulaması standardı
- **Lock Screen**: Cihazın kilit ekranı
- **Background Mode**: Uygulamanın arka planda çalışma durumu
- **Minimized State**: Uygulamanın simge durumuna küçültülmüş hali
- **Notification Badge**: Uygulama ikonunda görünen bildirim sayısı
- **Wake Lock**: Cihazın uykuya geçmesini engelleyen API
- **Background Sync**: Arka planda veri senkronizasyonu
- **Persistent Notification**: Kullanıcı kapatana kadar ekranda kalan bildirim

## Requirements

### Requirement 1

**User Story:** As a driver, I want to receive push notifications on my mobile device even when the app is in background or minimized, so that I never miss a guest request

#### Acceptance Criteria

1. WHEN the System sends a push notification, THE System SHALL deliver the notification to the device regardless of app state
2. WHILE the app is in background mode, THE System SHALL display notifications on the device notification center
3. WHILE the app is minimized, THE System SHALL display notifications with full content including title, body, and icon
4. WHEN a notification arrives in background, THE System SHALL play the notification sound
5. WHEN a notification arrives in background, THE System SHALL trigger device vibration with the configured pattern

### Requirement 2

**User Story:** As a driver, I want to see push notifications on my lock screen, so that I can respond to requests immediately without unlocking my device

#### Acceptance Criteria

1. WHEN the device is locked, THE System SHALL display incoming notifications on the lock screen
2. WHEN a notification is displayed on lock screen, THE System SHALL show the notification title, body, icon, and timestamp
3. WHEN a notification is displayed on lock screen, THE System SHALL play the notification sound
4. WHEN a notification is displayed on lock screen, THE System SHALL trigger device vibration
5. WHEN the user taps a lock screen notification, THE System SHALL unlock the device and open the app to the relevant screen

### Requirement 3

**User Story:** As a driver, I want the app to maintain a persistent connection for notifications, so that I receive alerts instantly without delay

#### Acceptance Criteria

1. WHEN the app is installed, THE System SHALL register a Service Worker for background notification handling
2. WHEN the Service Worker is registered, THE System SHALL establish a persistent push subscription
3. WHILE the device has network connectivity, THE System SHALL maintain an active push subscription
4. IF the push subscription expires, THEN THE System SHALL automatically renew the subscription
5. WHEN network connectivity is restored after disconnection, THE System SHALL re-establish the push subscription within 10 seconds

### Requirement 4

**User Story:** As a driver, I want notification badges on the app icon, so that I can see the number of unread requests at a glance

#### Acceptance Criteria

1. WHEN a new notification arrives, THE System SHALL increment the app icon badge count by 1
2. WHEN the user opens the app, THE System SHALL display the current badge count
3. WHEN the user views a notification, THE System SHALL decrement the badge count by 1
4. WHEN all notifications are cleared, THE System SHALL set the badge count to 0
5. THE System SHALL persist the badge count across app restarts

### Requirement 5

**User Story:** As a driver, I want high-priority notifications to stay on screen until I interact with them, so that I don't accidentally miss urgent requests

#### Acceptance Criteria

1. WHEN a notification has priority level "high", THE System SHALL set the notification as persistent
2. WHEN a persistent notification is displayed, THE System SHALL keep it visible until user interaction
3. WHEN a persistent notification is displayed, THE System SHALL set requireInteraction flag to true
4. WHEN a notification has priority level "normal", THE System SHALL auto-dismiss after 10 seconds
5. WHEN the user taps or swipes a notification, THE System SHALL mark it as interacted and remove it

### Requirement 6

**User Story:** As a driver, I want the app to work as a PWA on my mobile device, so that I get native app-like notification experience

#### Acceptance Criteria

1. WHEN the app is accessed on a mobile device, THE System SHALL provide a PWA manifest file
2. WHEN the PWA manifest is loaded, THE System SHALL include notification permission declarations
3. WHEN the user adds the app to home screen, THE System SHALL install it as a PWA
4. WHEN the PWA is installed, THE System SHALL enable full-screen mode and native-like notifications
5. WHEN the PWA is installed, THE System SHALL register for background notification handling

### Requirement 7

**User Story:** As a driver, I want notifications to include action buttons, so that I can respond to requests directly from the notification

#### Acceptance Criteria

1. WHEN a buggy request notification is displayed, THE System SHALL include "Kabul Et" (Accept) action button
2. WHEN a buggy request notification is displayed, THE System SHALL include "Detaylar" (Details) action button
3. WHEN the user taps "Kabul Et" button, THE System SHALL accept the request and open the app
4. WHEN the user taps "Detaylar" button, THE System SHALL open the app to the request details page
5. WHEN an action button is tapped, THE System SHALL close the notification

### Requirement 8

**User Story:** As a driver, I want notifications to work offline and sync when connection is restored, so that I don't lose any requests during network issues

#### Acceptance Criteria

1. WHEN the device loses network connectivity, THE System SHALL queue incoming notifications locally
2. WHILE the device is offline, THE System SHALL store notification data in IndexedDB
3. WHEN network connectivity is restored, THE System SHALL sync queued notifications with the server
4. WHEN syncing notifications, THE System SHALL display all queued notifications in chronological order
5. WHEN sync is complete, THE System SHALL clear the local notification queue

### Requirement 9

**User Story:** As a driver, I want the notification system to be battery-efficient, so that my device battery lasts throughout my shift

#### Acceptance Criteria

1. WHEN handling notifications, THE System SHALL use efficient Service Worker event listeners
2. WHEN the app is in background, THE System SHALL minimize CPU usage to less than 5%
3. WHEN processing notifications, THE System SHALL complete all operations within 500 milliseconds
4. THE System SHALL not use Wake Lock API unless explicitly required for active requests
5. WHEN no notifications are PENDING, THE System SHALL allow the device to enter sleep mode

### Requirement 10

**User Story:** As a driver, I want notifications to be grouped by type, so that multiple requests don't clutter my notification center

#### Acceptance Criteria

1. WHEN multiple notifications of the same type arrive, THE System SHALL group them under a single notification
2. WHEN notifications are grouped, THE System SHALL display the count of grouped notifications
3. WHEN the user expands a grouped notification, THE System SHALL show all individual notifications
4. WHEN a new notification arrives for an existing group, THE System SHALL update the group count
5. WHEN the user clears a grouped notification, THE System SHALL clear all notifications in that group

### Requirement 11

**User Story:** As an admin, I want to monitor notification delivery status, so that I can ensure drivers are receiving alerts reliably

#### Acceptance Criteria

1. WHEN a notification is sent, THE System SHALL log the delivery attempt with timestamp
2. WHEN a notification is successfully delivered, THE System SHALL record the delivery status as "delivered"
3. WHEN a notification fails to deliver, THE System SHALL record the failure reason
4. WHEN a notification is opened by the user, THE System SHALL record the interaction timestamp
5. THE System SHALL provide an admin dashboard showing notification delivery statistics

### Requirement 12

**User Story:** As a driver, I want different notification sounds for different priority levels, so that I can identify urgent requests by sound alone

#### Acceptance Criteria

1. WHEN a high-priority notification arrives, THE System SHALL play the urgent notification sound
2. WHEN a normal-priority notification arrives, THE System SHALL play the standard notification sound
3. WHEN a low-priority notification arrives, THE System SHALL play a subtle notification sound
4. THE System SHALL store notification sounds in the static assets folder
5. THE System SHALL cache notification sounds for offline playback

### Requirement 13

**User Story:** As a driver, I want notifications to respect my device's Do Not Disturb settings, so that I'm not disturbed during break times

#### Acceptance Criteria

1. WHEN the device is in Do Not Disturb mode, THE System SHALL check the device notification settings
2. IF Do Not Disturb allows priority notifications, THEN THE System SHALL deliver high-priority notifications
3. IF Do Not Disturb blocks all notifications, THEN THE System SHALL queue notifications for later delivery
4. WHEN Do Not Disturb mode is disabled, THE System SHALL deliver all queued notifications
5. THE System SHALL respect device-level notification channel settings

### Requirement 14

**User Story:** As a developer, I want comprehensive error handling for notification failures, so that the system remains stable even when notifications fail

#### Acceptance Criteria

1. WHEN a notification fails to send, THE System SHALL log the error with full context
2. WHEN a Service Worker error occurs, THE System SHALL attempt to recover automatically
3. IF automatic recovery fails, THEN THE System SHALL notify the admin of the failure
4. WHEN push subscription fails, THE System SHALL retry subscription up to 3 times with exponential backoff
5. THE System SHALL provide fallback mechanisms for critical notifications

### Requirement 15

**User Story:** As a driver, I want notifications to include rich media like images and maps, so that I can see request location visually

#### Acceptance Criteria

1. WHEN a notification includes location data, THE System SHALL display a map thumbnail in the notification
2. WHEN a notification includes an image, THE System SHALL display the image with maximum dimensions of 400x300 pixels
3. WHEN rich media fails to load, THE System SHALL display the notification with text content only
4. THE System SHALL cache rich media assets for offline viewing
5. THE System SHALL compress images to maximum 200KB before including in notifications
