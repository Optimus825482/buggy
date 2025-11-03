# Guest Workflow Specification

## ADDED Requirements

### Requirement: QR Code Location Redirect
The system SHALL redirect guests to the buggy request page with the scanned location pre-selected.

#### Scenario: QR code scan redirect
- **WHEN** a guest scans a location QR code
- **THEN** the system SHALL redirect to `/guest/call?location={location_id}`
- **AND** the system SHALL pre-fill the location information in the request form
- **AND** the system SHALL display the location name to the guest

#### Scenario: Invalid location handling
- **WHEN** a guest accesses the call page with an invalid location_id
- **THEN** the system SHALL display an error message
- **AND** the system SHALL prompt the guest to scan a valid QR code

### Requirement: Optional Room Number
The system SHALL allow guests to submit buggy requests without providing a room number.

#### Scenario: Request without room number
- **WHEN** a guest submits a request without entering a room number
- **THEN** the system SHALL accept the request
- **AND** the system SHALL store room_number as NULL in the database
- **AND** the system SHALL display "Room not specified" to the driver

#### Scenario: Request with room number
- **WHEN** a guest submits a request with a room number
- **THEN** the system SHALL validate the room number format
- **AND** the system SHALL store the room number in the database
- **AND** the system SHALL display the room number to the driver

### Requirement: Real-time Status Tracking
The system SHALL provide real-time updates to guests tracking their buggy request status.

#### Scenario: Status update via WebSocket
- **WHEN** a guest is viewing the status tracking page
- **THEN** the system SHALL establish a WebSocket connection
- **AND** the system SHALL automatically update the status when changed
- **AND** the system SHALL display driver information when request is accepted
- **AND** the system SHALL show completion message when request is completed

#### Scenario: Status polling fallback
- **WHEN** WebSocket connection fails or is unavailable
- **THEN** the system SHALL poll the status API every 5 seconds
- **AND** the system SHALL update the UI with the latest status

### Requirement: Estimated Arrival Time
The system SHALL display estimated arrival information to guests.

#### Scenario: Show ETA after acceptance
- **WHEN** a driver accepts a guest's request
- **THEN** the system SHALL display "Buggy is on the way" message
- **AND** the system SHALL show the driver's name and buggy code
- **AND** the system SHALL display an estimated arrival time (if available)

#### Scenario: Completion notification
- **WHEN** a driver completes the request
- **THEN** the system SHALL display "Buggy has arrived!" message
- **AND** the system SHALL show a success icon
- **AND** the system SHALL thank the guest for using the service
