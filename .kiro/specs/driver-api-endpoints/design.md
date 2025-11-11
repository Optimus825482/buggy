# Design Document

## Overview

The driver dashboard requires two critical API endpoints to function properly: one for fetching PENDING requests and another for fetching the driver's active request. These endpoints will enable drivers to view available requests and track their current assignment.

## Architecture

### Current State
- Frontend JavaScript calls `/api/driver/PENDING-requests` and `/api/driver/active-request`
- Both endpoints return 404 errors
- Driver dashboard is non-functional

### Target State
- Two new endpoints implemented in `app/routes/api.py`
- Proper authentication and authorization
- Efficient database queries with proper joins
- Audit logging for driver actions

## Components and Interfaces

### 1. Pending Requests Endpoint

**Endpoint:** `GET /api/driver/PENDING-requests`

**File:** `app/routes/api.py`

**Implementation:**
```python
@api_bp.route('/driver/PENDING-requests', methods=['GET'])
@login_required
@role_required(UserRole.DRIVER)
def get_PENDING_requests():
    """Get all PENDING requests for driver's hotel"""
    user = SystemUser.query.get(session['user_id'])
    
    if not user.buggy:
        return jsonify({'success': False, 'error': 'No buggy assigned'}), 400
    
    # Query PENDING requests for the hotel
    PENDING_requests = BuggyRequest.query.filter_by(
        hotel_id=user.hotel_id,
        status=RequestStatus.PENDING
    ).order_by(BuggyRequest.requested_at.desc()).all()
    
    # Serialize with location and guest info
    requests_data = [{
        'id': req.id,
        'guest_name': req.guest_name,
        'room_number': req.room_number,
        'phone_number': req.phone_number,
        'location': {
            'id': req.location.id,
            'name': req.location.name
        } if req.location else None,
        'requested_at': req.requested_at.isoformat(),
        'notes': req.notes
    } for req in PENDING_requests]
    
    return jsonify({
        'success': True,
        'requests': requests_data,
        'total': len(requests_data)
    })
```

**Response Format:**
```json
{
  "success": true,
  "requests": [
    {
      "id": 123,
      "guest_name": "John Doe",
      "room_number": "305",
      "phone_number": "+905551234567",
      "location": {
        "id": 5,
        "name": "Plaj"
      },
      "requested_at": "2025-11-03T14:30:00",
      "notes": "Acil"
    }
  ],
  "total": 1
}
```

### 2. Active Request Endpoint

**Endpoint:** `GET /api/driver/active-request`

**File:** `app/routes/api.py`

**Implementation:**
```python
@api_bp.route('/driver/active-request', methods=['GET'])
@login_required
@role_required(UserRole.DRIVER)
def get_active_request():
    """Get driver's currently active request"""
    user = SystemUser.query.get(session['user_id'])
    
    if not user.buggy:
        return jsonify({'success': False, 'error': 'No buggy assigned'}), 400
    
    # Find accepted request assigned to this buggy
    active_request = BuggyRequest.query.filter_by(
        buggy_id=user.buggy.id,
        status=RequestStatus.ACCEPTED
    ).first()
    
    if not active_request:
        return jsonify({
            'success': True,
            'request': None
        })
    
    # Serialize with full details
    request_data = {
        'id': active_request.id,
        'guest_name': active_request.guest_name,
        'room_number': active_request.room_number,
        'phone_number': active_request.phone_number,
        'location': {
            'id': active_request.location.id,
            'name': active_request.location.name
        } if active_request.location else None,
        'requested_at': active_request.requested_at.isoformat(),
        'accepted_at': active_request.accepted_at.isoformat() if active_request.accepted_at else None,
        'notes': active_request.notes,
        'status': active_request.status.value
    }
    
    return jsonify({
        'success': True,
        'request': request_data
    })
```

**Response Format (with active request):**
```json
{
  "success": true,
  "request": {
    "id": 123,
    "guest_name": "John Doe",
    "room_number": "305",
    "phone_number": "+905551234567",
    "location": {
      "id": 5,
      "name": "Plaj"
    },
    "requested_at": "2025-11-03T14:30:00",
    "accepted_at": "2025-11-03T14:32:00",
    "notes": "Acil",
    "status": "accepted"
  }
}
```

**Response Format (no active request):**
```json
{
  "success": true,
  "request": null
}
```

## Data Models

No schema changes required. Using existing models:
- `BuggyRequest` - Main request entity
- `Location` - Location information
- `Buggy` - Driver's assigned buggy
- `SystemUser` - Driver authentication

## Error Handling

### 1. No Buggy Assigned
- **Scenario:** Driver has no assigned buggy
- **Response:** `400 Bad Request` with error message
- **Message:** "No buggy assigned"

### 2. Unauthenticated Access
- **Scenario:** User not logged in
- **Response:** `401 Unauthorized`
- **Handled by:** `@login_required` decorator

### 3. Unauthorized Role
- **Scenario:** User is not a driver
- **Response:** `403 Forbidden`
- **Handled by:** `@role_required(UserRole.DRIVER)` decorator

### 4. Database Errors
- **Scenario:** Database query fails
- **Response:** `500 Internal Server Error`
- **Handling:** Try-catch block with error logging

## Security Considerations

### Authentication & Authorization
- Both endpoints require authentication via `@login_required`
- Role verification via `@role_required(UserRole.DRIVER)`
- Hotel isolation: Only return requests for driver's hotel
- Buggy isolation: Active request only for driver's assigned buggy

### Rate Limiting
- Implement rate limiting: 30 requests per minute per driver
- Use Flask-Limiter or similar middleware
- Configuration in `app/config.py`

### Data Privacy
- Only expose necessary guest information
- No sensitive data in logs
- Audit trail for compliance

## Performance Considerations

### Database Optimization
- Add index on `(hotel_id, status)` for PENDING requests query
- Add index on `(buggy_id, status)` for active request query
- Use eager loading for location relationship: `.options(joinedload(BuggyRequest.location))`

### Caching Strategy
- Pending requests: No caching (real-time data)
- Active request: Short TTL cache (5 seconds) to reduce DB load
- Cache invalidation on request status changes

### Query Optimization
```python
# Optimized PENDING requests query
PENDING_requests = BuggyRequest.query\
    .options(joinedload(BuggyRequest.location))\
    .filter_by(hotel_id=user.hotel_id, status=RequestStatus.PENDING)\
    .order_by(BuggyRequest.requested_at.desc())\
    .all()
```

## Audit Logging

### Log Format
```python
create_audit_log(
    action='driver_fetched_PENDING_requests',
    entity_type='request',
    entity_id=None,
    user_id=user.id,
    hotel_id=user.hotel_id,
    details={'count': len(PENDING_requests)}
)
```

### Logged Events
1. `driver_fetched_PENDING_requests` - When driver views PENDING list
2. `driver_fetched_active_request` - When driver checks active request
3. Include timestamp, driver_id, hotel_id, and result count

## Testing Strategy

### Unit Tests
1. Test PENDING requests endpoint with various scenarios:
   - Multiple PENDING requests
   - No PENDING requests
   - Driver without buggy
   - Non-driver user
2. Test active request endpoint:
   - With active request
   - Without active request
   - Multiple requests (should return only one)

### Integration Tests
1. End-to-end driver workflow:
   - Login as driver
   - Fetch PENDING requests
   - Accept a request
   - Fetch active request
   - Complete request

### Manual Testing
1. Driver dashboard: Verify PENDING requests display
2. Driver dashboard: Verify active request display
3. Test with multiple drivers simultaneously
4. Test rate limiting behavior

## Migration Plan

No database migrations required. Only code changes:

1. Add endpoints to `app/routes/api.py`
2. Add rate limiting configuration
3. Add database indexes (optional but recommended)
4. Deploy and test

## Rollout Plan

### Phase 1: Implementation
1. Implement both endpoints in `app/routes/api.py`
2. Add unit tests
3. Local testing

### Phase 2: Testing
1. Integration testing
2. Manual testing with driver dashboard
3. Performance testing

### Phase 3: Deployment
1. Deploy to staging
2. Verify driver dashboard functionality
3. Deploy to production
4. Monitor logs and performance
