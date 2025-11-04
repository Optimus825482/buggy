# Requirements Document

## Introduction

This specification defines the enhanced location deletion logic for the admin panel. Currently, the system prevents location deletion when any buggy exists at that location. The enhancement will allow location deletion when buggies exist but have no active driver sessions, automatically setting their `current_location_id` to NULL. Location deletion will only be blocked when buggies with active driver sessions are present at that location.

## Glossary

- **Location**: A physical pickup/dropoff point within a hotel where guests can request buggy service
- **Buggy**: A golf cart vehicle used for guest transportation
- **Active Driver Session**: A logged-in driver session indicated by `is_active=True` in the `buggy_drivers` table
- **Admin Panel**: The administrative interface used by hotel staff to manage locations, buggies, and drivers
- **Location Service**: The backend service responsible for location CRUD operations
- **current_location_id**: The foreign key field in the `buggies` table that references the location where a buggy is currently positioned

## Requirements

### Requirement 1: Location Deletion Validation

**User Story:** As an admin, I want to delete locations that have inactive buggies, so that I can clean up unused locations without being blocked by buggies that are not currently in active service.

#### Acceptance Criteria

1. WHEN an admin attempts to delete a location, THE Location Service SHALL check if any buggies at that location have active driver sessions (where `buggy_drivers.is_active = True`)

2. IF one or more buggies at the location have active driver sessions, THEN THE Location Service SHALL reject the deletion request with an error message indicating the number of active buggies

3. IF no buggies at the location have active driver sessions, THEN THE Location Service SHALL allow the deletion and set `current_location_id` to NULL for all buggies at that location

4. WHEN a location is successfully deleted with inactive buggies present, THE Location Service SHALL update all affected buggies' `current_location_id` field to NULL before deleting the location record

5. THE error message for blocked deletion SHALL clearly state: "Bu lokasyonda X aktif buggy bulunuyor. Sürücüler oturumu kapatana veya farklı lokasyon seçene kadar bu lokasyon silinemez."

### Requirement 2: Active Buggy Detection

**User Story:** As a system, I need to accurately identify which buggies have active driver sessions, so that location deletion logic can make correct decisions.

#### Acceptance Criteria

1. THE Location Service SHALL consider a buggy as "active" WHEN there exists a record in `buggy_drivers` table WHERE `buggy_id` matches AND `is_active = True`

2. THE Location Service SHALL consider a buggy as "inactive" WHEN no record exists in `buggy_drivers` table with `is_active = True` for that buggy

3. THE Location Service SHALL ignore the buggy's status field (`available`, `busy`, `offline`) when determining if a location can be deleted

4. WHEN counting active buggies at a location, THE Location Service SHALL only count buggies that have both `current_location_id` matching the location AND an active driver session

### Requirement 3: Database Integrity

**User Story:** As a system, I need to maintain database integrity when deleting locations with inactive buggies, so that no orphaned references or data inconsistencies occur.

#### Acceptance Criteria

1. WHEN a location is deleted with inactive buggies present, THE Location Service SHALL update all affected buggies' `current_location_id` to NULL within the same database transaction

2. THE Location Service SHALL ensure the location deletion and buggy updates are atomic (all succeed or all fail together)

3. WHEN the deletion transaction fails, THE Location Service SHALL rollback all changes and return an appropriate error message

4. THE Location Service SHALL maintain the existing foreign key constraint behavior (`ON DELETE SET NULL`) as a safety mechanism

### Requirement 4: Audit Trail

**User Story:** As an admin, I want deletion actions to be logged with details about affected buggies, so that I can track what happened during location cleanup operations.

#### Acceptance Criteria

1. WHEN a location is successfully deleted, THE Location Service SHALL log the deletion action including the number of buggies whose `current_location_id` was set to NULL

2. THE audit log entry SHALL include the location details and a list of affected buggy IDs

3. THE audit log SHALL record the admin user who performed the deletion action

4. WHEN deletion is blocked due to active buggies, THE Location Service SHALL log the attempted deletion with the reason for rejection
