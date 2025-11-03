# Driver Workflow Specification

## ADDED Requirements

### Requirement: Driver Location Management
The system SHALL enable drivers to set and update their current location.

#### Scenario: First login location selection
- **WHEN** a driver logs in for the first time
- **THEN** the system SHALL prompt the driver to select their current location from available hotel locations
- **AND** the system SHALL prevent access to the dashboard until a location is selected

#### Scenario: Location update after task completion
- **WHEN** a driver completes a buggy request
- **THEN** the system SHALL prompt the driver to update their current location
- **AND** the system SHALL update the buggy status to 'available' after location is set

#### Scenario: Manual location update
- **WHEN** a driver manually updates their location
- **THEN** the system SHALL update the buggy's current_location_id in the database
- **AND** the system SHALL log the location change in the audit trail
- **AND** the system SHALL emit a WebSocket event to notify administrators

### Requirement: Request Acceptance
The system SHALL allow available drivers to accept pending buggy requests.

#### Scenario: Accept pending request
- **WHEN** a driver with status 'available' accepts a pending request
- **THEN** the system SHALL update the request status to 'accepted'
- **AND** the system SHALL update the buggy status to 'busy'
- **AND** the system SHALL record the acceptance timestamp
- **AND** the system SHALL send a push notification to the guest (if subscribed)
- **AND** the system SHALL log the acceptance in the audit trail

#### Scenario: Prevent multiple acceptances
- **WHEN** a driver attempts to accept a request while already busy
- **THEN** the system SHALL reject the acceptance with an error message
- **AND** the system SHALL not modify any request or buggy status

#### Scenario: Race condition handling
- **WHEN** multiple drivers attempt to accept the same request simultaneously
- **THEN** the system SHALL accept only the first driver's request
- **AND** the system SHALL notify other drivers that the request is no longer available

### Requirement: Request Completion
The system SHALL allow drivers to mark accepted requests as completed.

#### Scenario: Complete accepted request
- **WHEN** a driver completes an accepted request
- **THEN** the system SHALL update the request status to 'completed'
- **AND** the system SHALL record the completion timestamp
- **AND** the system SHALL send a push notification to the guest (if subscribed)
- **AND** the system SHALL prompt the driver to update their location
- **AND** the system SHALL log the completion in the audit trail

#### Scenario: Prevent unauthorized completion
- **WHEN** a driver attempts to complete a request not assigned to them
- **THEN** the system SHALL reject the completion with an error message
- **AND** the system SHALL not modify the request status

### Requirement: Real-time Request Notifications
The system SHALL deliver real-time push notifications to available drivers when new requests are created.

#### Scenario: New request notification
- **WHEN** a guest creates a new buggy request
- **THEN** the system SHALL send push notifications to all drivers with status 'available' in the same hotel
- **AND** the notification SHALL include the location name and room number (if provided)
- **AND** the system SHALL play an audio alert in the driver's browser
- **AND** the system SHALL refresh the pending requests list automatically

#### Scenario: No notification when busy
- **WHEN** a new request is created
- **THEN** the system SHALL NOT send notifications to drivers with status 'busy' or 'offline'
