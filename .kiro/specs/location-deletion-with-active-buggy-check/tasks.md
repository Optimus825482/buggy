# Implementation Plan

- [x] 1. Enhance LocationService.delete_location() method





  - Implement active buggy session detection logic
  - Add query to get all buggies at the target location
  - Iterate through buggies and check for active driver sessions via BuggyDriver table
  - Categorize buggies as active (has is_active=True session) or inactive
  - Raise ValidationException if any active buggies found with appropriate Turkish error message
  - Set current_location_id to NULL for all inactive buggies before deletion
  - Enhance audit logging to include count and IDs of affected buggies
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 2.1, 2.2, 2.4, 3.1, 3.2, 4.1, 4.2_

- [x] 2. Refactor API route to use service layer

  - Update app/routes/api.py delete_location endpoint (lines 262-300)
  - Remove inline validation logic for buggy checking
  - Delegate to LocationService.delete_location() for all validation and deletion logic
  - Update exception handling to catch ResourceNotFoundException and ValidationException
  - Maintain existing response format for backward compatibility
  - _Requirements: 1.1, 1.2, 1.3, 1.5, 4.3, 4.4_
-


- [x] 3. Write unit tests for enhanced deletion logic







  - Create tests/test_location_deletion.py
  - Test: delete_location_with_inactive_buggies - verify location deleted and buggies' current_location_id set to NULL
  - Test: delete_location_blocked_by_active_buggy - verify ValidationException raised when active session exists
  - Test: delete_location_mixed_buggies - verify blocked when mix of active and inactive buggies
  - Test: delete_location_no_buggies - verify successful deletion when no buggies present
  - Test: delete_location_audit_trail - verify audit log contains affected buggy information
  - Test: delete_location_transaction_rollback - verify rollback on database error

erify rollback on database error
  --_Requirements: 1.1, 1.2, 1.3, 1.4, 2.1, 2.2, 
3.2, 3.3, 4.1, 4.2_

- [x] 4. Write integration tests for API endpoint







  - Create tests/test_location_deletion_api.py
  - Test: api_delete_location_authoriziacgies - verifhot l irolatisn apdsauanantibaaion

hanges
  - Test: api_delete_location_with_active_session - verify 400 response with correct error message
  - Test: api_delete_location_authorization - verify hotel isolation and authentication
  - Test: api_delete_location_not_found - verify 404 response for non-existent location
  - _Requirements: 1.1, 1.2, 1.3, 1.5, 4.3, 4.4_


- [x] 5. Update error messages and validation




- [ ] 5. Update error messages and validation


  - Ensure error message includes count of active buggies
okasyonda X aktif buggy bulunuyor. Sürücüler oturumu kapatana veya farklı lokasyon seçene kadar bu lokasyon silinemez."
  - Ensure error message includes count of active buggies
  - Verify existing error messages for active requests remain unchanged
  - _Requirements: 1.5, 4.4_
