# Requirements Document

## Introduction

Bu özellik, sürücüler ve sistem yöneticilerinin (admin) login olduktan sonra tarayıcı bildirim izinlerinin durumunu kontrol eder ve eğer izin verilmemişse kullanıcıdan izin talep eder. Bu sayede misafirlerden gelen buggy çağrı taleplerinin anlık bildirimleri alınabilir.

## Glossary

- **System**: BuggyCall web uygulaması
- **Driver**: Buggy sürücüsü rolündeki kullanıcı
- **Admin**: Sistem yöneticisi rolündeki kullanıcı
- **Guest**: Misafir kullanıcı (buggy talep eden)
- **Notification Permission**: Tarayıcının push bildirimleri gösterme izni
- **Login Session**: Kullanıcının başarılı giriş yaptıktan sonraki oturum

## Requirements

### Requirement 1

**User Story:** As a driver, I want to be prompted for notification permissions after login, so that I can receive real-time alerts when guests request a buggy

#### Acceptance Criteria

1. WHEN a driver successfully logs in, THE System SHALL check the current browser notification permission status
2. IF the notification permission is "default" (not granted or denied), THEN THE System SHALL display a permission request dialog
3. WHEN the driver grants notification permission, THE System SHALL store the permission status and enable real-time notifications
4. WHEN the driver denies notification permission, THE System SHALL allow continued use without notifications
5. IF the notification permission is already "granted", THEN THE System SHALL not display the permission request dialog

### Requirement 2

**User Story:** As an admin, I want to be prompted for notification permissions after login, so that I can monitor and respond to guest requests in real-time

#### Acceptance Criteria

1. WHEN an admin successfully logs in, THE System SHALL check the current browser notification permission status
2. IF the notification permission is "default" (not granted or denied), THEN THE System SHALL display a permission request dialog
3. WHEN the admin grants notification permission, THE System SHALL store the permission status and enable real-time notifications
4. WHEN the admin denies notification permission, THE System SHALL allow continued use without notifications
5. IF the notification permission is already "granted", THEN THE System SHALL not display the permission request dialog

### Requirement 3

**User Story:** As a driver or admin, I want the notification permission request to appear only once per session, so that I am not repeatedly interrupted

#### Acceptance Criteria

1. WHEN a user grants or denies notification permission, THE System SHALL record this action in the current session
2. WHILE the user remains logged in, THE System SHALL not display the permission request dialog again
3. WHEN the user logs out and logs back in, THE System SHALL check the browser permission status again
4. IF the browser permission status has changed externally, THEN THE System SHALL respect the new status

### Requirement 4

**User Story:** As a guest user, I want to not be prompted for notification permissions, so that my experience remains simple and focused on requesting a buggy

#### Acceptance Criteria

1. WHEN a guest user accesses the system, THE System SHALL not check notification permission status
2. WHEN a guest user submits a buggy request, THE System SHALL not display any notification permission dialogs
3. THE System SHALL only check notification permissions for authenticated driver and admin users

### Requirement 5

**User Story:** As a driver or admin, I want a clear and informative permission request message, so that I understand why the system needs notification access

#### Acceptance Criteria

1. WHEN the permission request dialog is displayed, THE System SHALL show a clear message explaining the purpose of notifications
2. THE System SHALL include text mentioning "misafir talepleri" (guest requests) in the permission request message
3. THE System SHALL provide both "İzin Ver" (Allow) and "Şimdi Değil" (Not Now) options
4. WHEN the user clicks "İzin Ver", THE System SHALL trigger the browser's native notification permission request
5. WHEN the user clicks "Şimdi Değil", THE System SHALL close the dialog without requesting browser permission

### Requirement 6

**User Story:** As a developer, I want the notification permission check to be non-blocking, so that login performance is not affected

#### Acceptance Criteria

1. WHEN checking notification permission status, THE System SHALL perform the check asynchronously
2. THE System SHALL complete the login process before displaying the permission request dialog
3. IF the permission check fails, THEN THE System SHALL log the error and continue without blocking the user
4. THE System SHALL display the permission request dialog within 2 seconds after successful login
5. THE System SHALL not delay the rendering of the main dashboard while checking permissions
