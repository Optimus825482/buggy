# Implementation Plan

## 1. Backend API Endpoints

- [ ] 1.1 Create assign driver to buggy endpoint
  - Implement `POST /api/admin/assign-driver-to-buggy` endpoint in `app/routes/api.py`
  - Add validation for admin role, buggy_id, and driver_id
  - Update buggy.driver_id in database
  - Add audit log entry for driver assignment
  - Return success response with updated buggy data
  - _Requirements: 2.1, 2.2, 2.3, 5.4_

- [ ] 1.2 Create driver transfer endpoint
  - Implement `POST /api/admin/transfer-driver` endpoint in `app/routes/api.py`
  - Add validation for admin role, driver_id, source_buggy_id, target_buggy_id
  - Check for active driver session and terminate if exists
  - Set both source and target buggies to OFFLINE if session was active
  - Update source buggy: set driver_id to None
  - Update target buggy: set driver_id to transferred driver
  - Add audit log entry with source and target buggy information
  - Emit WebSocket event for real-time updates
  - Return success response with both buggy data
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 5.4_

- [ ] 1.3 Add audit log types for new operations
  - Add `driver_assigned_to_buggy` audit log type in `app/services/audit_service.py`
  - Add `driver_transferred` audit log type with source and target buggy fields
  - Ensure audit logs include admin name, driver name, and buggy codes
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

## 2. Frontend - Driver Dashboard

- [ ] 2.1 Remove offline switch from driver dashboard
  - Open `templates/driver/dashboard.html`
  - Remove the status-toggle div containing the toggle switch (lines ~90-100)
  - Remove the status toggle event listener in `app/static/js/driver-dashboard.js` (setupEventListeners function)
  - Keep only the "Çıkış Yap" (Logout) button in the header
  - Test that logout button still works correctly
  - _Requirements: 1.1, 1.2, 1.5_

## 3. Frontend - Admin Buggy Management

- [ ] 3.1 Enhance buggy list table with driver information
  - Open `templates/admin/buggies.html`
  - The "Sürücü" column already exists in the table
  - Update renderBuggies() function to show driver active status badge
  - Add action buttons for "Sürücü Ata" and "Transfer Et" in the İşlemler column
  - _Requirements: 2.1, 2.5, 4.1, 4.6_

- [ ] 3.2 Create assign driver modal dialog
  - Add modal HTML structure for driver assignment in `templates/admin/buggies.html`
  - Create dropdown to select available drivers (filter out already assigned drivers)
  - Add "Ata" (Assign) and "İptal" (Cancel) buttons
  - Implement `showAssignDriverModal(buggyId)` JavaScript function
  - Implement `assignDriverToBuggy()` JavaScript function to call new API endpoint
  - Display success/error messages using existing modal system
  - Refresh buggy list after successful assignment
  - _Requirements: 2.2, 2.3, 4.2, 4.3, 4.5_

- [ ] 3.3 Create transfer driver modal dialog
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

- [ ] 3.4 Add real-time updates via WebSocket
  - Listen for `driver_assigned` WebSocket event in admin buggy page
  - Listen for `driver_transferred` WebSocket event in admin buggy page
  - Update buggy list UI when events received
  - Show notification toast for successful operations
  - _Requirements: 4.5_
