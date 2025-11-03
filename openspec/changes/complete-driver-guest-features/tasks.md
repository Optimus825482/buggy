# Implementation Tasks

## 1. Database Schema Updates
- [ ] 1.1 Add `current_location_id` column to `buggies` table (Foreign Key to locations)
  - Create migration file
  - Add nullable foreign key with ON DELETE SET NULL
  - _Requirements: Driver Workflow 1.1_

## 2. Driver Location Management
- [ ] 2.1 Create location selection modal component
  - HTML modal with location dropdown
  - Fetch available locations from API
  - Submit selected location
  - _Requirements: Driver Workflow 1.1, 1.2_

- [ ] 2.2 Implement POST /api/driver/set-location endpoint
  - Validate driver is authenticated
  - Update buggy.current_location_id
  - Update buggy.status to 'available'
  - Log action in audit trail
  - Return updated buggy status
  - _Requirements: Driver Workflow 1.1_

- [ ] 2.3 Add location selection on first login
  - Check if driver has current_location set
  - Show modal if not set
  - Prevent dashboard access until location selected
  - _Requirements: Driver Workflow 1.2_

- [ ] 2.4 Add location selection after request completion
  - Show modal after completing request
  - Update location and set status to available
  - _Requirements: Driver Workflow 1.3_

## 3. Driver Request Handling
- [ ] 3.1 Implement POST /api/driver/accept-request/{id} endpoint
  - Validate request is pending
  - Validate driver's buggy is available
  - Update request status to 'accepted'
  - Update buggy status to 'busy'
  - Set accepted_by_id and accepted_at timestamp
  - Send notification to guest (if subscribed)
  - Log action in audit trail
  - _Requirements: Driver Workflow 2.1_

- [ ] 3.2 Implement POST /api/driver/complete-request/{id} endpoint
  - Validate request is accepted by this driver
  - Update request status to 'completed'
  - Set completed_at timestamp
  - Send notification to guest (if subscribed)
  - Log action in audit trail
  - Trigger location selection modal
  - _Requirements: Driver Workflow 2.2_

- [ ] 3.3 Update driver dashboard UI for request actions
  - Add "Accept" button for pending requests
  - Add "Complete" button for active request
  - Show current active request prominently
  - Disable accept buttons when busy
  - _Requirements: Driver Workflow 2.1, 2.2_

- [ ] 3.4 Implement real-time push notification handling
  - Listen for 'new_request' events
  - Show browser notification
  - Play sound alert
  - Refresh pending requests list
  - _Requirements: Driver Workflow 2.3_

## 4. Session Management
- [ ] 4.1 Implement single-device enforcement on login
  - Check for existing active sessions
  - Terminate old session when new login detected
  - Update Session model with device_token
  - Log session termination in audit trail
  - _Requirements: Session Management 1.1_

- [ ] 4.2 Create POST /api/admin/sessions/{id}/terminate endpoint
  - Admin-only access
  - Find session by ID
  - Mark session as terminated
  - Invalidate session token
  - Log action in audit trail
  - _Requirements: Session Management 1.2_

- [ ] 4.3 Add session termination UI in admin panel
  - Show active sessions list
  - Add "Terminate Session" button per session
  - Confirm before terminating
  - Refresh list after termination
  - _Requirements: Session Management 1.2_

- [ ] 4.4 Enhance logout to properly close sessions
  - Delete session from database
  - Clear session cookie
  - Emit WebSocket disconnect event
  - Log logout in audit trail
  - _Requirements: Session Management 1.3_

## 5. Guest QR Code Workflow
- [ ] 5.1 Fix QR code URL generation to include location_id
  - Update QRCodeService.generate_qr_code()
  - Generate URL: `/guest/call?location={id}`
  - Test QR code scanning redirects correctly
  - _Requirements: Guest Workflow 1.1_

- [ ] 5.2 Update guest call page to parse location_id from URL
  - Read location_id from query parameter
  - Pre-fill location in request
  - Show location name in UI
  - _Requirements: Guest Workflow 1.1_

- [ ] 5.3 Make room number truly optional in UI
  - Remove 'required' attribute from room number input
  - Update placeholder text to indicate optional
  - Handle null room_number in backend
  - _Requirements: Guest Workflow 1.2_

## 6. Guest Status Tracking
- [ ] 6.1 Implement real-time status updates on guest/status page
  - Connect to WebSocket
  - Listen for request status changes
  - Update UI when status changes
  - Show driver info when accepted
  - _Requirements: Guest Workflow 2.1_

- [ ] 6.2 Add estimated time display
  - Calculate ETA based on status
  - Show "Buggy arriving soon" message
  - Update progress indicator
  - _Requirements: Guest Workflow 2.2_

## 7. Buggy Service Enhancements
- [ ] 7.1 Add update_location() method to BuggyService
  - Validate buggy exists
  - Validate location exists
  - Update current_location_id
  - Update status to 'available'
  - Log in audit trail
  - _Requirements: Driver Workflow 1.1_

- [ ] 7.2 Add get_available_buggies_by_location() method
  - Filter by hotel_id and status='available'
  - Include current_location info
  - Order by location proximity (future enhancement)
  - _Requirements: Admin Operations 1.1_

## 8. Request Service Enhancements
- [ ] 8.1 Add accept_request() method to RequestService
  - Validate request is pending
  - Validate buggy is available
  - Update request and buggy status atomically
  - Send notifications
  - Log in audit trail
  - _Requirements: Driver Workflow 2.1_

- [ ] 8.2 Add complete_request() method to RequestService
  - Validate request is accepted
  - Update request status
  - Keep buggy status as 'busy' until location set
  - Send notifications
  - Log in audit trail
  - _Requirements: Driver Workflow 2.2_

## 9. WebSocket Event Handlers
- [ ] 9.1 Add 'request_accepted' event handler
  - Emit to guest room
  - Include driver and buggy info
  - Update guest UI in real-time
  - _Requirements: Guest Workflow 2.1_

- [ ] 9.2 Add 'request_completed' event handler
  - Emit to guest room
  - Show completion message
  - _Requirements: Guest Workflow 2.1_

- [ ] 9.3 Add 'driver_location_updated' event handler
  - Emit to admin room
  - Update buggy status in admin dashboard
  - _Requirements: Admin Operations 1.1_

## 10. Testing & Validation
- [ ] 10.1 Test complete driver workflow
  - Login → Select location → Accept request → Complete → Select new location
  - Verify buggy status changes correctly
  - Verify notifications sent
  - _Requirements: All Driver Workflow_

- [ ] 10.2 Test complete guest workflow
  - Scan QR → Enter details → Submit → Track status → Receive completion
  - Verify real-time updates work
  - _Requirements: All Guest Workflow_

- [ ] 10.3 Test session management
  - Login on device A → Login on device B → Verify A logged out
  - Admin terminates session → Verify user logged out
  - _Requirements: All Session Management_

- [ ] 10.4 Test multi-driver scenarios
  - Multiple drivers online
  - Request sent to all available drivers
  - First to accept gets the request
  - Others see request disappear
  - _Requirements: Driver Workflow 2.1, 2.3_
