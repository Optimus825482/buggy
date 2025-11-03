# Requirements Document

## Introduction

The BuggyCall driver dashboard currently has missing API endpoints that prevent drivers from viewing pending requests and their active request. The frontend JavaScript calls `/api/driver/pending-requests` and `/api/driver/active-request` endpoints which return 404 errors, breaking the driver workflow.

## Glossary

- **Driver Dashboard**: The web interface used by buggy drivers to view and manage requests
- **Pending Request**: A buggy request with status "pending" that has not been accepted by any driver
- **Active Request**: A buggy request that has been accepted by the current driver and is in "accepted" status
- **Driver API**: REST API endpoints specifically for driver operations

## Requirements

### Requirement 1

**User Story:** As a driver, I want to view all pending buggy requests for my hotel, so that I can choose which request to accept.

#### Acceptance Criteria

1. WHEN a driver accesses the pending requests endpoint, THE Driver API SHALL return all requests with status "pending" for the driver's hotel

2. THE Driver API SHALL include location information (name, coordinates) for each pending request

3. THE Driver API SHALL include guest information (name, room number, phone) for each pending request

4. THE Driver API SHALL order pending requests by requested_at timestamp in descending order (newest first)

5. THE Driver API SHALL return an empty array when no pending requests exist

### Requirement 2

**User Story:** As a driver, I want to view my currently active request, so that I can see the details of the request I'm currently handling.

#### Acceptance Criteria

1. WHEN a driver accesses the active request endpoint, THE Driver API SHALL return the request that is assigned to the driver's buggy with status "accepted"

2. THE Driver API SHALL include complete location information for the active request

3. THE Driver API SHALL include guest contact information for the active request

4. THE Driver API SHALL return null or empty response when the driver has no active request

5. THE Driver API SHALL only return requests assigned to the authenticated driver's buggy

### Requirement 3

**User Story:** As a driver, I want the API to validate my authentication and authorization, so that I can only access requests relevant to my hotel and role.

#### Acceptance Criteria

1. THE Driver API SHALL require authentication for all driver endpoints

2. THE Driver API SHALL verify the user has the "driver" role

3. THE Driver API SHALL only return requests for the driver's assigned hotel

4. IF the driver has no assigned buggy, THEN THE Driver API SHALL return an appropriate error message

5. THE Driver API SHALL apply rate limiting to prevent abuse (30 requests per minute)

### Requirement 4

**User Story:** As a system administrator, I want driver API calls to be logged in the audit trail, so that I can track driver activity and troubleshoot issues.

#### Acceptance Criteria

1. THE Driver API SHALL log when drivers fetch pending requests (for debugging purposes)

2. THE Driver API SHALL log when drivers fetch their active request

3. THE Driver API SHALL include driver_id, hotel_id, and timestamp in audit logs

4. THE Driver API SHALL handle logging failures gracefully without breaking the API response
