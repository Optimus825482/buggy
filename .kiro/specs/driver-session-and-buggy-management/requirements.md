# Requirements Document

## Introduction

Bu doküman, sürücü oturum yönetimi ve buggy tanımlama sistemindeki iyileştirmeleri tanımlar. Mevcut sistemde sürücülerin "çevrimdışı durumuna alma" switch'i bulunmaktadır ve buggy tanımlama ekranında sürücü yönetimi sınırlıdır. Bu değişiklikler ile:

1. Çevrimdışı durumuna alma switch'i kaldırılacak ve oturum kapatma sadece belirli senaryolarda otomatik gerçekleşecek
2. Buggy tanımlama ekranına sürücü atama ve transfer özellikleri eklenecek

## Glossary

- **System**: Buggy Call uygulaması
- **Driver**: Buggy kullanan sürücü kullanıcısı
- **Buggy**: Golf arabası/elektrikli araç
- **Session**: Sürücünün aktif oturumu
- **Admin**: Sistem yöneticisi
- **Offline Switch**: Sürücünün kendini çevrimdışı yapma butonu (kaldırılacak)
- **Driver Assignment**: Bir buggy'ye sürücü atama işlemi
- **Driver Transfer**: Bir sürücüyü bir buggy'den başka bir buggy'ye taşıma işlemi

## Requirements

### Requirement 1: Otomatik Oturum Kapatma

**User Story:** Admin veya sürücü olarak, sürücü oturumlarının manuel switch olmadan otomatik yönetilmesini istiyorum, böylece sistem daha basit ve güvenilir olur.

#### Acceptance Criteria

1. THE System SHALL remove the offline status toggle switch from the driver interface
2. WHEN a driver clicks the logout button, THE System SHALL terminate the driver's session and set the associated buggy status to OFFLINE
3. WHEN a different driver logs in to the same buggy, THE System SHALL automatically terminate the previous driver's active session and set the new driver as active
4. WHEN an admin terminates a driver session from the admin panel, THE System SHALL close the driver's session and set the associated buggy status to OFFLINE
5. THE System SHALL NOT provide any manual offline/online toggle functionality to drivers

### Requirement 2: Buggy Sürücü Atama

**User Story:** Admin olarak, daha önce tanımlanmış buggy'lere yeni sürücü atayabilmek istiyorum, böylece mevcut buggy'lere kolayca sürücü ekleyebilirim.

#### Acceptance Criteria

1. WHEN an admin accesses the buggy management screen, THE System SHALL display a list of all existing buggies with their currently assigned drivers
2. WHEN an admin selects an existing buggy, THE System SHALL provide an option to assign a new driver to that buggy
3. WHEN an admin assigns a new driver to a buggy, THE System SHALL update the buggy's driver assignment and display a success confirmation
4. THE System SHALL allow multiple drivers to be assigned to the same buggy over time (one active at a time)
5. WHEN displaying buggy information, THE System SHALL show the currently assigned driver's name and status

### Requirement 3: Sürücü Transfer İşlemi

**User Story:** Admin olarak, bir sürücüyü bir buggy'den başka bir buggy'ye transfer edebilmek istiyorum, böylece sürücü atamaları esnek bir şekilde yönetilebilir.

#### Acceptance Criteria

1. WHEN an admin views the driver list in buggy management, THE System SHALL provide a transfer option for each driver
2. WHEN an admin initiates a driver transfer, THE System SHALL display a list of available buggies to transfer the driver to
3. WHEN an admin completes a driver transfer, THE System SHALL update the driver's buggy assignment from the source buggy to the target buggy
4. IF the driver has an active session during transfer, THEN THE System SHALL terminate the active session and set both buggies to OFFLINE status
5. WHEN a driver transfer is completed, THE System SHALL log the transfer action in the audit trail with source and target buggy information
6. THE System SHALL prevent transferring a driver to a buggy that already has an active driver session

### Requirement 4: Buggy Tanımlama Ekranı İyileştirmeleri

**User Story:** Admin olarak, buggy tanımlama ekranında sürücü yönetimi işlemlerini kolayca yapabilmek istiyorum, böylece tüm buggy ve sürücü işlemlerini tek bir yerden yönetebilirim.

#### Acceptance Criteria

1. WHEN an admin accesses the buggy management screen, THE System SHALL display a comprehensive view showing buggy code, model, license plate, current driver, and status
2. THE System SHALL provide inline actions for each buggy including "Assign Driver", "Transfer Driver", and "View Details"
3. WHEN an admin clicks "Assign Driver", THE System SHALL open a modal dialog showing available drivers who are not currently assigned to any buggy
4. WHEN an admin clicks "Transfer Driver", THE System SHALL open a modal dialog showing the current driver and available target buggies
5. THE System SHALL display real-time status updates when driver assignments or transfers are completed
6. THE System SHALL show visual indicators for buggies with active driver sessions versus those without assigned drivers

### Requirement 5: Oturum Yönetimi Audit Trail

**User Story:** Admin olarak, tüm oturum kapatma ve sürücü transfer işlemlerinin kaydını görebilmek istiyorum, böylece sistem değişikliklerini takip edebilirim.

#### Acceptance Criteria

1. WHEN a driver session is terminated by logout, THE System SHALL log the action with timestamp, driver name, and reason "driver_logout"
2. WHEN a driver session is terminated by another driver login, THE System SHALL log the action with timestamp, both driver names, buggy code, and reason "session_replaced"
3. WHEN an admin terminates a driver session, THE System SHALL log the action with timestamp, admin name, driver name, and reason "admin_terminated"
4. WHEN a driver is transferred between buggies, THE System SHALL log the action with timestamp, admin name, driver name, source buggy, and target buggy
5. THE System SHALL make all session management audit logs accessible through the admin audit trail interface
