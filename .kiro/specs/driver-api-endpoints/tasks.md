# Implementation Plan

- [x] 1. Implement PENDING requests endpoint


  - Add `GET /api/driver/PENDING-requests` endpoint to `app/routes/api.py`
  - Apply `@login_required` and `@role_required(UserRole.DRIVER)` decorators
  - Query PENDING requests filtered by hotel_id and status=PENDING
  - Order results by requested_at descending
  - Include location and guest information in response
  - Handle case where driver has no assigned buggy
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 3.1, 3.2, 3.3, 3.4_


- [x] 2. Implement active request endpoint





  - Add `GET /api/driver/active-request` endpoint to `app/routes/api.py`
  - Apply `@login_required` and `@role_required(UserRole.DRIVER)` decorators
  - Query request filtered by buggy_id and status=ACCEPTED
  - Return null when no active request exists
  - Include complete location and guest information
  - Ensure only driver's own buggy requests are returned
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 3.2, 3.3, 3.4_




- [ ] 3. Add audit logging



  - Log when drivers fetch PENDING requests
  - Log when drivers fetch active request
  - Include driver_id, hotel_id, and timestamp in logs
  - Handle logging failures gracefully
  - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [x] 4. Add rate limiting configuration

  - Configure rate limiting for driver endpoints (30 requests per minute)
  - Add rate limiter to both endpoints
  - Test rate limiting behavior
  - _Requirements: 3.5_



- [ ] 5. Add database indexes for performance


  - Add index on buggy_requests(hotel_id, status)
  - Add index on buggy_requests(buggy_id, status)
  - Test query performance improvements
  - _Requirements: Performance optimization_

- [ ]* 6. Write unit tests
  - Test PENDING requests endpoint with multiple scenarios
  - Test active request endpoint with and without active request
  - Test authentication and authorization
  - Test error handling (no buggy assigned, wrong role)
  - _Requirements: All requirements_

- [ ]* 7. Integration testing
  - Test complete driver workflow end-to-end
  - Test with multiple concurrent drivers
  - Verify driver dashboard functionality
  - Test rate limiting behavior
  - _Requirements: All requirements_
