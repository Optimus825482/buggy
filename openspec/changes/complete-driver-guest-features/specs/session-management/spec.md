# Session Management Specification

## ADDED Requirements

### Requirement: Single Device Enforcement
The system SHALL enforce single active session per driver account.

#### Scenario: New login terminates old session
- **WHEN** a driver logs in on a new device while already logged in elsewhere
- **THEN** the system SHALL terminate the existing session
- **AND** the system SHALL create a new session for the new device
- **AND** the system SHALL log the session termination in the audit trail
- **AND** the system SHALL emit a WebSocket event to disconnect the old device

#### Scenario: Session termination notification
- **WHEN** a driver's session is terminated due to new login
- **THEN** the old device SHALL receive a "Session expired" message
- **AND** the old device SHALL be redirected to the login page
- **AND** the system SHALL clear all session data on the old device

### Requirement: Admin Session Termination
The system SHALL allow administrators to forcefully terminate driver sessions.

#### Scenario: Admin terminates driver session
- **WHEN** an administrator terminates a driver's active session
- **THEN** the system SHALL mark the session as terminated in the database
- **AND** the system SHALL invalidate the session token
- **AND** the system SHALL emit a WebSocket disconnect event to the driver
- **AND** the system SHALL log the termination in the audit trail with admin user ID

#### Scenario: Driver receives termination notification
- **WHEN** an admin terminates a driver's session
- **THEN** the driver's device SHALL receive a "Session terminated by administrator" message
- **AND** the driver SHALL be redirected to the login page
- **AND** the system SHALL clear all session data

### Requirement: Proper Logout Handling
The system SHALL properly clean up sessions when users log out.

#### Scenario: User-initiated logout
- **WHEN** a user clicks the logout button
- **THEN** the system SHALL delete the session from the database
- **AND** the system SHALL clear the session cookie
- **AND** the system SHALL emit a WebSocket disconnect event
- **AND** the system SHALL log the logout in the audit trail
- **AND** the system SHALL redirect to the login page

#### Scenario: Session cleanup on logout
- **WHEN** a user logs out
- **THEN** the system SHALL remove all session-related data
- **AND** the system SHALL close any active WebSocket connections
- **AND** the system SHALL clear any cached user data
