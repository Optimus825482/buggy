# Design Document

## Overview

The buggy call completion feature enables drivers to mark requests as completed while simultaneously updating their buggy's location. This is a critical workflow step that transitions the buggy from BUSY back to AVAILABLE status and enables location-based dispatch optimization.

## Architecture

### Current State
- No completion endpoint exists
- Drivers cannot mark requests as completed
- Buggy locations are not updated after deliveries
- No completion workflow in driver dashboard

### Target State
- `PUT /api/requests/{request_id}/complete` endpoint implemented
- Atomic transaction handling for state updates
- Location tracking integrated with completion
- Real-time notifications via WebSocket
- Audit logging for all completions

## Components and Interfaces

### 1. Request Completion Endpoint

**Endpoint:** `PUT /api/requests/{request_id}/complete`

**File:** `app/routes/api.py`

**Request Body:**
```json
{
  "current_location_id": 5,
  "notes": "Guest delivered to beach area"
}
```

**Implementation:**
```python
@api_bp.route('/requests/<int:request_id>/complete', methods=['PUT'])
@login_required
@role_required(UserRole.DRIVER)
def complete_request(request_id):
    """Complete a buggy request and update buggy location"""
    user = SystemUser.query.get(session['user_id'])
    
    if not user.buggy:
        return jsonify({'success': False, 'error': 'No buggy assigned'}), 400
    
    data = request.get_json()
    current_location_id = data.get('current_location_id')
    notes = data.get('notes', '')
    
    # Validation
    if not current_location_id:
        return jsonify({'success': False, 'error': 'Current location is required'}), 400
    
    # Verify location exists
    location = Location.query.get(current_location_id)
    if not location or location.hotel_id != user.hotel_id:
        return jsonify({'success': False, 'error': 'Invalid location'}), 400
    
    # Get the request
    buggy_request = BuggyRequest.query.get(request_id)
    if not buggy_request:
        return jsonify({'success': False, 'error': 'Request not found'}), 404
    
    # Verify request is assigned to driver's buggy
    if buggy_request.buggy_id != user.buggy.id:
        return jsonify({'success': False, 'error': 'Request not assigned to your buggy'}), 403
    
    # Verify request status
    if buggy_request.status != RequestStatus.ACCEPTED:
        return jsonify({'success': False, 'error': 'Request is not in accepted status'}), 400
    
    try:
        # Atomic transaction
        buggy_request.status = RequestStatus.COMPLETED
        buggy_request.completed_at = datetime.utcnow()
        if notes:
            buggy_request.notes = (buggy_request.notes or '') + f"\nCompletion: {notes}"
        
        # Update buggy status and location
        user.buggy.status = BuggyStatus.AVAILABLE
        user.buggy.current_location_id = current_location_id
        
        db.session.commit()
        
        # Audit log
        create_audit_log(
            action='request_completed',
            entity_type='request',
            entity_id=request_id,
            user_id=user.id,
            hotel_id=user.hotel_id,
            details={
                'buggy_id': user.buggy.id,
                'location_id': current_location_id,
                'location_name': location.name,
                'notes': notes
            }
        )
        
        # WebSocket notification
        try:
            socketio.emit('request_completed', {
                'request_id': request_id,
                'buggy_id': user.buggy.id,
                'buggy_code': user.buggy.code,
                'location_id': current_location_id,
                'location_name': location.name,
                'completed_at': buggy_request.completed_at.isoformat()
            }, room=f'hotel_{user.hotel_id}')
        except Exception as e:
            # Log but don't fail the request
            print(f"WebSocket notification failed: {e}")
        
        return jsonify({
            'success': True,
            'message': 'Request completed successfully',
            'request': {
                'id': buggy_request.id,
                'status': buggy_request.status.value,
                'completed_at': buggy_request.completed_at.isoformat()
            },
            'buggy': {
                'id': user.buggy.id,
                'status': user.buggy.status.value,
                'current_location': {
                    'id': location.id,
                    'name': location.name
                }
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Completion failed'}), 500
```

**Success Response:**
```json
{
  "success": true,
  "message": "Request completed successfully",
  "request": {
    "id": 123,
    "status": "completed",
    "completed_at": "2025-11-03T15:30:00"
  },
  "buggy": {
    "id": 1,
    "status": "available",
    "current_location": {
      "id": 5,
      "name": "Plaj"
    }
  }
}
```

**Error Responses:**
```json
// Missing location
{
  "success": false,
  "error": "Current location is required"
}

// Invalid location
{
  "success": false,
  "error": "Invalid location"
}

// Wrong buggy
{
  "success": false,
  "error": "Request not assigned to your buggy"
}

// Wrong status
{
  "success": false,
  "error": "Request is not in accepted status"
}
```

## Data Models

### BuggyRequest Model Updates
No schema changes needed. Using existing fields:
- `status` - Updated to COMPLETED
- `completed_at` - Set to current timestamp
- `notes` - Append completion notes

### Buggy Model Updates
No schema changes needed. Using existing fields:
- `status` - Updated to AVAILABLE
- `current_location_id` - Updated to driver's current location

## State Transitions

### Request Status Flow
```
PENDING → ACCEPTED → COMPLETED
                  ↓
              CANCELLED
```

### Buggy Status Flow
```
OFFLINE → AVAILABLE → BUSY → AVAILABLE
                            ↓
                        OFFLINE
```

### Completion Transition
```
Before Completion:
- Request: ACCEPTED
- Buggy: BUSY
- Location: Previous location

After Completion:
- Request: COMPLETED
- Buggy: AVAILABLE
- Location: Driver-specified location
```

## Error Handling

### 1. No Buggy Assigned
- **Scenario:** Driver has no assigned buggy
- **Response:** `400 Bad Request`
- **Message:** "No buggy assigned"

### 2. Missing Location
- **Scenario:** current_location_id not provided
- **Response:** `400 Bad Request`
- **Message:** "Current location is required"

### 3. Invalid Location
- **Scenario:** Location doesn't exist or belongs to different hotel
- **Response:** `400 Bad Request`
- **Message:** "Invalid location"

### 4. Request Not Found
- **Scenario:** request_id doesn't exist
- **Response:** `404 Not Found`
- **Message:** "Request not found"

### 5. Wrong Buggy
- **Scenario:** Request assigned to different buggy
- **Response:** `403 Forbidden`
- **Message:** "Request not assigned to your buggy"

### 6. Wrong Status
- **Scenario:** Request not in ACCEPTED status
- **Response:** `400 Bad Request`
- **Message:** "Request is not in accepted status"

### 7. Database Error
- **Scenario:** Transaction fails
- **Response:** `500 Internal Server Error`
- **Handling:** Rollback all changes

## Security Considerations

### Authentication & Authorization
- Require authentication via `@login_required`
- Require driver role via `@role_required(UserRole.DRIVER)`
- Verify request belongs to driver's buggy
- Verify location belongs to driver's hotel

### Data Validation
- Validate location_id exists and is valid
- Validate notes length (max 500 characters)
- Validate request status before completion
- Prevent duplicate completions

### Concurrency Control
- Use database transactions for atomicity
- Handle race conditions (multiple completion attempts)
- Lock request record during update

## Performance Considerations

### Database Optimization
- Use single transaction for all updates
- Minimize database queries (3 queries total)
- Add index on `(buggy_id, status)` if not exists

### Response Time
- Target: < 2 seconds under normal load
- Database transaction: < 500ms
- WebSocket notification: Async, non-blocking
- Audit logging: Async, non-blocking

### Caching
- No caching needed (write operation)
- Invalidate any cached driver state after completion

## WebSocket Integration

### Event Name
`request_completed`

### Event Payload
```json
{
  "request_id": 123,
  "buggy_id": 1,
  "buggy_code": "BUGGY-01",
  "location_id": 5,
  "location_name": "Plaj",
  "completed_at": "2025-11-03T15:30:00"
}
```

### Recipients
- All admin users connected to `hotel_{hotel_id}` room
- Driver dashboard (for confirmation)

### Error Handling
- WebSocket failures should not block completion
- Log errors but continue with success response

## Audit Logging

### Log Entry Format
```python
{
    'action': 'request_completed',
    'entity_type': 'request',
    'entity_id': 123,
    'user_id': 5,
    'hotel_id': 1,
    'details': {
        'buggy_id': 1,
        'location_id': 5,
        'location_name': 'Plaj',
        'notes': 'Guest delivered to beach area'
    },
    'timestamp': '2025-11-03T15:30:00'
}
```

### Logged Information
- Request ID and status change
- Buggy ID and status change
- Location ID and name
- Driver ID and hotel ID
- Completion notes
- Timestamp

## Testing Strategy

### Unit Tests
1. Test successful completion with all fields
2. Test completion without notes
3. Test validation errors (missing location, wrong status, etc.)
4. Test authorization (wrong buggy, wrong role)
5. Test transaction rollback on error

### Integration Tests
1. Complete driver workflow:
   - Login → Accept request → Complete request
2. Test concurrent completion attempts
3. Test WebSocket notification delivery
4. Test audit log creation

### Manual Testing
1. Driver completes request via dashboard
2. Verify buggy status changes to AVAILABLE
3. Verify location is updated
4. Verify admin receives real-time notification
5. Test error scenarios

## Frontend Integration

### Driver Dashboard - Completion Form
```html
<div class="complete-request-form">
  <h3>İşlemi Tamamla</h3>
  
  <div class="form-group">
    <label>Şu anda hangi lokasyondasınız? *</label>
    <select id="current-location" required>
      <option value="">Lokasyon Seçin</option>
      <!-- Populated from /api/locations -->
    </select>
  </div>
  
  <div class="form-group">
    <label>Notlar (Opsiyonel)</label>
    <textarea id="completion-notes" maxlength="500"></textarea>
  </div>
  
  <button onclick="completeRequest()">
    İşlemi Tamamla
  </button>
</div>

<script>
async function completeRequest() {
  const locationId = document.getElementById('current-location').value;
  const notes = document.getElementById('completion-notes').value;
  
  if (!locationId) {
    Utils.showToast('Lütfen lokasyon seçin!', 'error');
    return;
  }
  
  try {
    const response = await fetch(`/api/requests/${activeRequestId}/complete`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        current_location_id: parseInt(locationId),
        notes: notes
      })
    });
    
    const data = await response.json();
    
    if (data.success) {
      Utils.showToast('İşlem tamamlandı!', 'success');
      window.location.href = '/driver/dashboard';
    } else {
      Utils.showToast(data.error, 'error');
    }
  } catch (error) {
    Utils.showToast('Bir hata oluştu', 'error');
  }
}
</script>
```

## Migration Plan

No database migrations required. Only code changes:

1. Add completion endpoint to `app/routes/api.py`
2. Add frontend completion form to driver dashboard
3. Add WebSocket event handling
4. Deploy and test

## Rollout Plan

### Phase 1: Backend Implementation
1. Implement completion endpoint
2. Add validation and error handling
3. Add audit logging
4. Unit tests

### Phase 2: Frontend Integration
1. Add completion form to driver dashboard
2. Add location dropdown
3. Add success/error handling
4. Integration tests

### Phase 3: Testing
1. Manual testing with real drivers
2. Test concurrent scenarios
3. Test WebSocket notifications
4. Performance testing

### Phase 4: Deployment
1. Deploy to staging
2. Verify complete workflow
3. Deploy to production
4. Monitor logs and metrics
