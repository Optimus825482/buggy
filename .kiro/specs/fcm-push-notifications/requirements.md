# Requirements Document - FCM Push Notifications

## Introduction

Bu özellik, BuggyCall uygulamasına Firebase Cloud Messaging (FCM) tabanlı push notification sistemi ekler. Hem istemde (guest) hem de driver tarafında FCM kullanılarak, uygulama kapalı veya arka planda olsa bile güvenilir bildirim teslimatı sağlanacaktır.

## Glossary

- **System**: BuggyCall web uygulaması
- **FCM**: Firebase Cloud Messaging - Google'ın push notification servisi
- **Driver**: Buggy sürücüsü rolündeki kullanıcı
- **Guest**: Misafir kullanıcı (buggy talep eden)
- **Admin**: Sistem yöneticisi rolündeki kullanıcı
- **FCM Token**: Cihaza özgü unique bildirim token'ı
- **Service Worker**: Arka planda çalışan JavaScript worker thread
- **VAPID Key**: Voluntary Application Server Identification - Web push için public key
- **Foreground Notification**: Uygulama açıkken gelen bildirim
- **Background Notification**: Uygulama kapalıyken gelen bildirim
- **Firebase Admin SDK**: Backend'de FCM kullanımı için Python kütüphanesi
- **Firebase JS SDK**: Frontend'de FCM kullanımı için JavaScript kütüphanesi
- **Service Account**: Firebase backend authentication için JSON key dosyası
- **Multicast Messaging**: Birden fazla cihaza aynı anda bildirim gönderme

## Requirements

### Requirement 1

**User Story:** As a driver, I want to receive FCM push notifications when a new buggy request is created, so that I can respond immediately even if the app is closed

#### Acceptance Criteria

1. WHEN a new buggy request is created, THE System SHALL send FCM notification to all available drivers
2. WHEN the FCM notification is sent, THE System SHALL include request details in the notification payload
3. WHEN the driver's app is in foreground, THE System SHALL display the notification as an in-app alert
4. WHEN the driver's app is in background, THE System SHALL display the notification as a system push notification
5. WHEN the driver clicks the notification, THE System SHALL open the app and navigate to the request details page

### Requirement 2

**User Story:** As a guest, I want to receive FCM push notifications when my request is accepted or completed, so that I stay informed about my buggy status

#### Acceptance Criteria

1. WHEN a driver accepts the guest's request, THE System SHALL send FCM notification to the guest
2. WHEN a driver completes the guest's request, THE System SHALL send FCM notification to the guest
3. WHEN the guest's app is in foreground, THE System SHALL display the notification as an in-app alert
4. WHEN the guest's app is in background, THE System SHALL display the notification as a system push notification
5. WHEN the guest clicks the notification, THE System SHALL open the app and show the request status

### Requirement 3

**User Story:** As a system, I want to automatically register and manage FCM tokens for all users, so that notifications can be delivered reliably

#### Acceptance Criteria

1. WHEN a user opens the app for the first time, THE System SHALL request notification permission
2. WHEN notification permission is granted, THE System SHALL generate an FCM token
3. WHEN an FCM token is generated, THE System SHALL send the token to the backend for registration
4. WHEN the backend receives an FCM token, THE System SHALL store it in the database with user association
5. WHEN an FCM token expires or becomes invalid, THE System SHALL automatically refresh and update the token

### Requirement 4

**User Story:** As a backend service, I want to send FCM notifications using Firebase Admin SDK, so that I can reliably deliver messages to mobile and web clients

#### Acceptance Criteria

1. WHEN the backend initializes, THE System SHALL authenticate with Firebase using the service account key
2. WHEN sending a notification, THE System SHALL use Firebase Admin SDK to send the message
3. WHEN sending to multiple users, THE System SHALL use multicast messaging for efficiency
4. WHEN an FCM token is invalid, THE System SHALL remove it from the database
5. WHEN a notification fails to send, THE System SHALL log the error with full context

### Requirement 5

**User Story:** As a developer, I want FCM notifications to have different priority levels, so that urgent requests get immediate attention

#### Acceptance Criteria

1. WHEN sending a new request notification, THE System SHALL set priority to "high"
2. WHEN sending a request accepted notification, THE System SHALL set priority to "normal"
3. WHEN sending a request completed notification, THE System SHALL set priority to "low"
4. WHEN priority is "high", THE System SHALL configure the notification to bypass battery optimization
5. WHEN priority is "high", THE System SHALL enable sound and vibration

### Requirement 6

**User Story:** As a system administrator, I want to monitor FCM notification delivery status, so that I can ensure the system is working correctly

#### Acceptance Criteria

1. WHEN an FCM notification is sent, THE System SHALL log the delivery attempt in the database
2. WHEN an FCM notification is successfully delivered, THE System SHALL record the status as "sent"
3. WHEN an FCM notification fails to deliver, THE System SHALL record the failure reason
4. WHEN a user clicks an FCM notification, THE System SHALL record the interaction timestamp
5. THE System SHALL provide an admin API endpoint to retrieve notification statistics

### Requirement 7

**User Story:** As a frontend developer, I want a Service Worker to handle background FCM messages, so that notifications work even when the app is closed

#### Acceptance Criteria

1. WHEN the app loads, THE System SHALL register a Service Worker for FCM messaging
2. WHEN an FCM message arrives in background, THE Service Worker SHALL display a system notification
3. WHEN the user clicks a background notification, THE Service Worker SHALL open the app to the relevant page
4. WHEN an FCM message arrives in foreground, THE System SHALL handle it in the main app context
5. THE Service Worker SHALL cache notification sounds for offline playback

### Requirement 8

**User Story:** As a driver, I want FCM notifications to include action buttons, so that I can respond to requests directly from the notification

#### Acceptance Criteria

1. WHEN a new request notification is displayed, THE System SHALL include "Kabul Et" (Accept) action button
2. WHEN a new request notification is displayed, THE System SHALL include "Detaylar" (Details) action button
3. WHEN the driver clicks "Kabul Et" button, THE System SHALL accept the request and open the app
4. WHEN the driver clicks "Detaylar" button, THE System SHALL open the app to the request details page
5. WHEN an action button is clicked, THE System SHALL close the notification

### Requirement 9

**User Story:** As a system, I want to handle FCM token refresh automatically, so that notifications continue working after token expiration

#### Acceptance Criteria

1. WHEN an FCM token is refreshed by Firebase, THE System SHALL detect the token change
2. WHEN a token change is detected, THE System SHALL send the new token to the backend
3. WHEN the backend receives a new token, THE System SHALL update the user's token in the database
4. WHEN updating a token, THE System SHALL preserve the user association
5. THE System SHALL log all token refresh operations for debugging

### Requirement 10

**User Story:** As a backend service, I want to clean up invalid FCM tokens automatically, so that the database stays clean and efficient

#### Acceptance Criteria

1. WHEN an FCM notification fails with "invalid token" error, THE System SHALL mark the token as invalid
2. WHEN a token is marked as invalid, THE System SHALL remove it from the database
3. WHEN sending to multiple tokens, THE System SHALL collect all invalid tokens
4. WHEN invalid tokens are collected, THE System SHALL remove them in a single database operation
5. THE System SHALL log all token cleanup operations

### Requirement 11

**User Story:** As a developer, I want FCM notifications to include rich media, so that users get more context about the request

#### Acceptance Criteria

1. WHEN a notification includes location data, THE System SHALL include a map thumbnail URL in the payload
2. WHEN a notification includes an image, THE System SHALL include the image URL in the payload
3. WHEN rich media fails to load, THE System SHALL display the notification with text content only
4. THE System SHALL compress images to maximum 200KB before including in notifications
5. THE System SHALL cache rich media assets in the Service Worker for offline viewing

### Requirement 12

**User Story:** As a system, I want to use a hybrid Socket.IO + FCM approach, so that real-time updates work when the app is open and push notifications work when it's closed

#### Acceptance Criteria

1. WHEN the app is in foreground, THE System SHALL use Socket.IO for real-time updates
2. WHEN the app is in background, THE System SHALL use FCM for push notifications
3. WHEN both Socket.IO and FCM are available, THE System SHALL prefer Socket.IO for lower latency
4. WHEN Socket.IO connection fails, THE System SHALL fall back to FCM
5. THE System SHALL send both Socket.IO and FCM messages to ensure delivery

### Requirement 13

**User Story:** As a developer, I want comprehensive error handling for FCM operations, so that the system remains stable even when notifications fail

#### Acceptance Criteria

1. WHEN Firebase Admin SDK initialization fails, THE System SHALL log the error and continue without FCM
2. WHEN an FCM notification fails to send, THE System SHALL log the error with full context
3. WHEN a Service Worker error occurs, THE System SHALL attempt to recover automatically
4. IF automatic recovery fails, THEN THE System SHALL notify the admin of the failure
5. THE System SHALL provide fallback mechanisms for critical notifications

### Requirement 14

**User Story:** As a system administrator, I want a test endpoint to verify FCM functionality, so that I can quickly diagnose issues

#### Acceptance Criteria

1. THE System SHALL provide a POST endpoint at /api/fcm/test-notification
2. WHEN the test endpoint is called, THE System SHALL send a test notification to the current user
3. WHEN the test notification is sent, THE System SHALL return the delivery status
4. THE test endpoint SHALL require authentication
5. THE test endpoint SHALL log all test notification attempts

### Requirement 15

**User Story:** As a developer, I want FCM configuration to be managed through environment variables, so that different environments can use different Firebase projects

#### Acceptance Criteria

1. THE System SHALL read Firebase configuration from environment variables
2. WHEN environment variables are missing, THE System SHALL log a warning and disable FCM
3. THE System SHALL support separate Firebase projects for development and production
4. THE System SHALL validate Firebase configuration on startup
5. THE System SHALL provide clear error messages for configuration issues
