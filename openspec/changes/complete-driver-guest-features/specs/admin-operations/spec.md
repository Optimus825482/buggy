# Admin Operations Specification

## ADDED Requirements

### Requirement: Active Sessions Management
The system SHALL provide administrators with visibility and control over active user sessions.

#### Scenario: View active sessions
- **WHEN** an administrator accesses the sessions management page
- **THEN** the system SHALL display all active sessions
- **AND** the system SHALL show user name, role, login time, IP address, and device info for each session
- **AND** the system SHALL highlight sessions older than 24 hours

#### Scenario: Terminate session from admin panel
- **WHEN** an administrator clicks "Terminate Session" for an active session
- **THEN** the system SHALL prompt for confirmation
- **AND** upon confirmation, the system SHALL terminate the session
- **AND** the system SHALL refresh the sessions list
- **AND** the system SHALL show a success message

## MODIFIED Requirements

### Requirement: Real-time Buggy Status Monitoring
The system SHALL display real-time buggy locations and status in the admin dashboard.

#### Scenario: View buggy locations
- **WHEN** an administrator views the buggy status list
- **THEN** the system SHALL display each buggy's current location
- **AND** the system SHALL show the buggy status (available, busy, offline)
- **AND** the system SHALL show the assigned driver name
- **AND** the system SHALL update automatically when locations change

#### Scenario: Location update notification
- **WHEN** a driver updates their buggy location
- **THEN** the admin dashboard SHALL automatically reflect the new location
- **AND** the system SHALL update the buggy status to 'available' if it was previously 'busy'
