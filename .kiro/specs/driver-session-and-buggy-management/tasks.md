# Implementation Plan

## 1. Backend API Endpoints

- [x] 1.1 Implement WebSocket disconnect handler for automatic session termination
  - Add `@socketio.on('disconnect')` handler in WebSocket module
  - Detect when driver disconnects (browser/app closed)
  - Find and terminate active driver session (set is_active=False, revoked_at=now)
  - Set driver's buggy status to OFFLINE
  - Add audit log entry with reason "connection_lost"
  - Emit WebSocket event to admin panel for real-time status update
  - _Requirements: 1.5, 5.1_
  - **Status: COMPLETED** ✅

- [x] 1.2 Create assign driver to buggy endpoint
  - Implement `POST /api/admin/assign-driver-to-buggy` endpoint in `app/routes/api.py`
  - Add validation for admin role, buggy_id, and driver_id
  - Update buggy.driver_id in database
  - Add audit log entry for driver assignment
  - Return success response with updated buggy data
  - _Requirements: 2.1, 2.2, 2.3, 5.4_
  - **Status: COMPLETED** ✅

- [x] 1.3 Fix driver transfer endpoint to use buggy_drivers table
  - Update `POST /api/admin/transfer-driver` endpoint in `app/routes/api.py`
  - Replace direct `buggy.driver_id` manipulation with `buggy_drivers` table operations
  - Deactivate driver association from source buggy
  - Create or activate driver association with target buggy
  - Maintain existing session termination logic
  - Maintain existing audit logging and WebSocket events
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 5.4_
  - **Status: COMPLETED** ✅

- [x] 1.4 Add audit log types for new operations
  - Add `driver_assigned_to_buggy` audit log type in `app/services/audit_service.py`
  - Add `driver_transferred` audit log type with source and target buggy fields
  - Ensure audit logs include admin name, driver name, and buggy codes
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_
  - **Status: COMPLETED** ✅

- [x] 1.5 Create initial location setup endpoint
  - Implement `POST /api/driver/set-initial-location` endpoint in `app/routes/api.py`
  - Add validation for driver role and location_id
  - Verify location exists and belongs to driver's hotel
  - Update buggy's current_location_id
  - Set buggy status to AVAILABLE
  - Clear `needs_location_setup` session flag
  - Add audit log entry for initial location setup
  - Return success response with buggy and location data
  - _Requirements: 1.1, 1.2_
  - **Status: COMPLETED** ✅

- [x] 1.6 Create admin close driver session endpoint
  - Implement `POST /api/admin/close-driver-session/<driver_id>` endpoint in `app/routes/api.py`
  - Add validation for admin role
  - Find and terminate active driver session (set is_active=False, revoked_at=now)
  - Set driver's buggy status to OFFLINE
  - Add audit log entry with admin name, driver name, and reason
  - Emit WebSocket event to force driver logout
  - Return success response
  - _Requirements: 1.4, 5.3_
  - **Status: COMPLETED** ✅

## 2. Frontend - Driver Dashboard

- [x] 2.1 Remove offline switch from driver dashboard
  - Open `templates/driver/dashboard.html`
  - Remove the status-toggle div containing the toggle switch (lines ~90-100)
  - Remove the status toggle event listener in `app/static/js/driver-dashboard.js` (setupEventListeners function)
  - Keep only the "Çıkış Yap" (Logout) button in the header
  - Test that logout button still works correctly
  - _Requirements: 1.1, 1.2, 1.5_
  - **Status: COMPLETED** ✅

- [x] 2.2 Add initial location setup modal
  - Create location setup modal in `templates/driver/dashboard.html`
  - Show modal automatically when `needs_location_setup` flag is true
  - Display dropdown with available locations
  - Add "Devam Et" (Continue) button
  - Implement `setInitialLocation()` JavaScript function to call API
  - Prevent dashboard access until location is set
  - Show success message and reload dashboard after location is set
  - _Requirements: 1.1, 1.2_
  - **Status: COMPLETED** ✅

## 3. Frontend - Admin Buggy Management

- [x] 3.1 Enhance buggy list table with driver information
  - Open `templates/admin/buggies.html`
  - The "Sürücü" column already exists in the table
  - Update renderBuggies() function to show driver active status badge
  - Add action buttons for "Sürücü Ata" and "Transfer Et" in the İşlemler column
  - _Requirements: 2.1, 2.5, 4.1, 4.6_
  - **Status: COMPLETED** ✅

- [x] 3.2 Create assign driver modal dialog
  - Add modal HTML structure for driver assignment in `templates/admin/buggies.html`
  - Create dropdown to select available drivers (filter out already assigned drivers)
  - Add "Ata" (Assign) and "İptal" (Cancel) buttons
  - Implement `showAssignDriverModal(buggyId)` JavaScript function
  - Implement `assignDriverToBuggy()` JavaScript function to call new API endpoint
  - Display success/error messages using existing modal system
  - Refresh buggy list after successful assignment
  - _Requirements: 2.2, 2.3, 4.2, 4.3, 4.5_
  - **Status: COMPLETED** ✅

- [x] 3.3 Create transfer driver modal dialog
  - Add modal HTML structure for driver transfer in `templates/admin/buggies.html`
  - Display current driver name and source buggy code
  - Create dropdown to select target buggy (exclude source buggy)
  - Add warning message about active session termination
  - Add "Transfer Et" (Transfer) and "İptal" (Cancel) buttons
  - Implement `showTransferDriverModal(buggyId)` JavaScript function
  - Implement `transferDriver()` JavaScript function to call new API endpoint
  - Display success/error messages using existing modal system
  - Refresh buggy list after successful transfer
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 4.2, 4.4, 4.5_
  - **Status: COMPLETED** ✅

- [x] 3.4 Add real-time updates via WebSocket
  - Listen for `driver_assigned` WebSocket event in admin buggy page
  - Listen for `driver_transferred` WebSocket event in admin buggy page
  - Update buggy list UI when events received
  - Show notification toast for successful operations
  - _Requirements: 4.5_
  - **Status: COMPLETED** ✅

- [x] 3.5 Add close driver session button in admin panel
  - Add "Oturumu Kapat" button for each active driver in buggy list
  - Show button only when driver has active session (status is AVAILABLE or BUSY)
  - Implement `closeDriverSession(driverId)` JavaScript function
  - Call `/api/admin/close-driver-session/<driver_id>` endpoint
  - Show confirmation dialog before closing session
  - Display success message and refresh buggy list
  - _Requirements: 1.4, 5.3_
  - **Status: COMPLETED** ✅
