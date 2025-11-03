# Requirements Document

## Introduction

The buggy call completion feature allows drivers to mark requests as completed after delivering the guest to their destination. When completing a request, the driver must specify their current location so the system can track buggy positions for optimal dispatch. This feature is critical for the driver workflow and enables location-based analytics.

## Glossary

- **Request Completion**: The process of marking a buggy request as finished after the guest has been delivered
- **Current Location**: The location where the buggy is positioned after completing a request
- **Completion Notes**: Optional text notes that drivers can add when completing a request
- **Buggy Status**: The operational state of a buggy (OFFLINE, AVAILABLE, BUSY)
- **Request Status**: The state of a buggy request (PENDING, ACCEPTED, COMPLETED, CANCELLED)

## Requirements

### Requirement 1

**User Story:** As a driver, I want to complete a request and specify my current location, so that the system knows where my buggy is positioned for the next request.

#### Acceptance Criteria

1. WHEN a driver completes a request, THE Completion System SHALL require the driver to select their current location from available locations

2. THE Completion System SHALL update the request status to COMPLETED

3. THE Completion System SHALL update the buggy's current_location_id to the selected location

4. THE Completion System SHALL change the buggy status from BUSY to AVAILABLE

5. THE Completion System SHALL record the completion timestamp (completed_at)

### Requirement 2

**User Story:** As a driver, I want to add optional notes when completing a request, so that I can document any important information about the delivery.

#### Acceptance Criteria

1. THE Completion System SHALL allow drivers to provide optional text notes during completion

2. THE Completion System SHALL store completion notes in the request record

3. THE Completion System SHALL accept notes up to 500 characters in length

4. THE Completion System SHALL allow completion without notes (notes are optional)

### Requirement 3

**User Story:** As a driver, I want the system to validate that I can only complete requests assigned to my buggy, so that the system maintains data integrity.

#### Acceptance Criteria

1. THE Completion System SHALL verify the request is assigned to the driver's buggy

2. THE Completion System SHALL verify the request status is ACCEPTED before allowing completion

3. IF the request is not assigned to the driver's buggy, THEN THE Completion System SHALL return an error message

4. IF the request status is not ACCEPTED, THEN THE Completion System SHALL return an error message

5. THE Completion System SHALL require authentication and driver role verification

### Requirement 4

**User Story:** As a driver, I want the completion to happen atomically, so that the system state remains consistent even if errors occur.

#### Acceptance Criteria

1. THE Completion System SHALL use database transactions for all completion operations

2. IF any step fails during completion, THEN THE Completion System SHALL roll back all changes

3. THE Completion System SHALL ensure the buggy status, request status, and location are updated together

4. THE Completion System SHALL handle concurrent completion attempts gracefully

### Requirement 5

**User Story:** As a system administrator, I want completion events to be logged in the audit trail, so that I can track driver activity and analyze service patterns.

#### Acceptance Criteria

1. THE Completion System SHALL create an audit log entry when a request is completed

2. THE Completion System SHALL include driver_id, request_id, buggy_id, and location_id in the audit log

3. THE Completion System SHALL log the completion timestamp and any notes provided

4. THE Completion System SHALL handle audit logging failures without blocking the completion

### Requirement 6

**User Story:** As a driver, I want to receive immediate feedback after completing a request, so that I know the operation was successful and can proceed to the next request.

#### Acceptance Criteria

1. THE Completion System SHALL return a success response with updated request details

2. THE Completion System SHALL include the new buggy status in the response

3. THE Completion System SHALL return appropriate error messages for validation failures

4. THE Completion System SHALL respond within 2 seconds under normal load

### Requirement 7

**User Story:** As an admin, I want the system to send real-time notifications when requests are completed, so that I can monitor operations in real-time.

#### Acceptance Criteria

1. THE Completion System SHALL emit a WebSocket event when a request is completed

2. THE Completion System SHALL include request_id, buggy_id, and location information in the event

3. THE Completion System SHALL send the event to all connected admin users for the hotel

4. THE Completion System SHALL handle WebSocket failures gracefully without blocking completion
