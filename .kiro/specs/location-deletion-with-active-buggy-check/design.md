# Design Document

## Overview

This design enhances the location deletion logic to distinguish between buggies with active driver sessions and inactive buggies. The current implementation blocks location deletion when any buggy exists at that location. The enhanced implementation will only block deletion when buggies with active driver sessions are present, and will automatically set `current_location_id` to NULL for inactive buggies during deletion.

## Architecture

### Current Flow
```
Admin requests location deletion
    ↓
Check for active requests → Block if found
    ↓
Check for ANY buggies at location → Block if found
    ↓
Delete location
```

### Enhanced Flow
```
Admin requests location deletion
    ↓
Check for active requests → Block if found
    ↓
Check for buggies with ACTIVE driver sessions → Block if found
    ↓
Set current_location_id = NULL for inactive buggies
    ↓
Delete location
    ↓
Log audit trail with affected buggy count
```

## Components and Interfaces

### 1. LocationService.delete_location() Enhancement

**Current Implementation:**
- Checks for active requests
- No buggy session validation
- Direct deletion

**Enhanced Implementation:**
```python
@staticmethod
def delete_location(location_id):
    """
    Delete location with enhanced active buggy validation
    
    Args:
        location_id: Location ID
    
    Raises:
        ResourceNotFoundException: If location not found
        ValidationException: If location has active requests or active buggies
    """
    location = Location.query.get(location_id)
    if not location:
        raise ResourceNotFoundException('Location', location_id)
    
    # Check for active requests (existing logic)
    from app.models.request import BuggyRequest, RequestStatus
    active_requests = BuggyRequest.query.filter_by(
        location_id=location_id,
        status=RequestStatus.PENDING
    ).count()
    
    if active_requests > 0:
        raise ValidationException(
            f'Bu lokasyonda {active_requests} aktif talep var. '
            'Önce talepleri tamamlayın veya iptal edin.'
        )
    
    # NEW: Check for buggies with active driver sessions
    from app.models.buggy import Buggy
    from app.models.buggy_driver import BuggyDriver
    
    # Get all buggies at this location
    buggies_at_location = Buggy.query.filter_by(
        current_location_id=location_id
    ).all()
    
    # Count buggies with active driver sessions
    active_buggies = []
    inactive_buggies = []
    
    for buggy in buggies_at_location:
        has_active_session = BuggyDriver.query.filter_by(
            buggy_id=buggy.id,
            is_active=True
        ).first() is not None
        
        if has_active_session:
            active_buggies.append(buggy)
        else:
            inactive_buggies.append(buggy)
    
    # Block deletion if any buggy has an active driver session
    if active_buggies:
        raise ValidationException(
            f'Bu lokasyonda {len(active_buggies)} aktif buggy bulunuyor. '
            'Sürücüler oturumu kapatana veya farklı lokasyon seçene kadar bu lokasyon silinemez.'
        )
    
    # NEW: Set current_location_id to NULL for inactive buggies
    for buggy in inactive_buggies:
        buggy.current_location_id = None
    
    # Store values for audit
    old_values = location.to_dict()
    hotel_id = location.hotel_id
    affected_buggy_ids = [b.id for b in inactive_buggies]
    
    # Delete QR code file
    QRCodeService.delete_qr_code(location.id)
    
    # Delete location
    db.session.delete(location)
    db.session.commit()
    
    # NEW: Enhanced audit logging with affected buggies
    AuditService.log_delete(
        entity_type='location',
        entity_id=location_id,
        old_values=old_values,
        hotel_id=hotel_id,
        notes=f'Deleted with {len(inactive_buggies)} inactive buggies. Affected buggy IDs: {affected_buggy_ids}'
    )
```

### 2. API Route Update

**File:** `app/routes/api.py`

**Current Implementation (lines 262-300):**
```python
@api_bp.route('/locations/<int:location_id>', methods=['DELETE'])
@require_login
def delete_location(location_id):
    # Direct validation in route
    # Checks for any buggies at location
```

**Enhanced Implementation:**
```python
@api_bp.route('/locations/<int:location_id>', methods=['DELETE'])
@require_login
def delete_location(location_id):
    """Delete location"""
    try:
        user = SystemUser.query.get(session['user_id'])
        
        # Delegate to service layer for enhanced validation
        LocationService.delete_location(location_id)
        
        return jsonify({
            'success': True,
            'message': 'Lokasyon başarıyla silindi'
        }), 200
        
    except ResourceNotFoundException as e:
        return jsonify({'error': str(e)}), 404
    except ValidationException as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        import traceback
        print(f"Error deleting location {location_id}: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': f'Lokasyon silinirken hata oluştu: {str(e)}'}), 500
```

### 3. Database Transaction Flow

```
BEGIN TRANSACTION
    ↓
1. Validate location exists
    ↓
2. Check active requests
    ↓
3. Query buggies at location
    ↓
4. For each buggy:
   - Check BuggyDriver.is_active
   - Categorize as active/inactive
    ↓
5. If active_buggies > 0:
   - ROLLBACK
   - Raise ValidationException
    ↓
6. For each inactive buggy:
   - SET current_location_id = NULL
    ↓
7. Delete QR code file
    ↓
8. DELETE location record
    ↓
9. Log audit trail
    ↓
COMMIT TRANSACTION
```

## Data Models

### Affected Tables

**buggies**
- `current_location_id` (FK to locations.id, ON DELETE SET NULL)
- Will be explicitly set to NULL before location deletion

**buggy_drivers**
- `is_active` (Boolean) - Used to determine if buggy has active session
- `buggy_id` (FK to buggies.id)

**locations**
- Primary table being deleted

### Query Patterns

**Check for active driver session:**
```sql
SELECT COUNT(*) 
FROM buggy_drivers 
WHERE buggy_id = ? AND is_active = TRUE
```

**Get buggies at location:**
```sql
SELECT * 
FROM buggies 
WHERE current_location_id = ?
```

**Update inactive buggies:**
```sql
UPDATE buggies 
SET current_location_id = NULL 
WHERE id IN (?)
```

## Error Handling

### Error Scenarios

1. **Location not found**
   - Exception: `ResourceNotFoundException`
   - HTTP Status: 404
   - Message: "Lokasyon bulunamadı"

2. **Active requests exist**
   - Exception: `ValidationException`
   - HTTP Status: 400
   - Message: "Bu lokasyonda X aktif talep var. Önce talepleri tamamlayın veya iptal edin."

3. **Active buggies exist**
   - Exception: `ValidationException`
   - HTTP Status: 400
   - Message: "Bu lokasyonda X aktif buggy bulunuyor. Sürücüler oturumu kapatana veya farklı lokasyon seçene kadar bu lokasyon silinemez."

4. **Database transaction failure**
   - Exception: Generic Exception
   - HTTP Status: 500
   - Action: Rollback all changes
   - Message: "Lokasyon silinirken hata oluştu: [error details]"

### Rollback Strategy

All database operations are wrapped in a transaction. If any step fails:
1. Automatic rollback via SQLAlchemy session
2. No partial updates (atomic operation)
3. Error logged and returned to client

## Testing Strategy

### Unit Tests

**Test File:** `tests/test_location_service.py`

1. **test_delete_location_with_inactive_buggies**
   - Setup: Location with 2 inactive buggies (no active sessions)
   - Action: Delete location
   - Assert: Location deleted, buggies' current_location_id = NULL

2. **test_delete_location_blocked_by_active_buggy**
   - Setup: Location with 1 active buggy (has active driver session)
   - Action: Attempt to delete location
   - Assert: ValidationException raised, location not deleted

3. **test_delete_location_mixed_buggies**
   - Setup: Location with 1 active and 2 inactive buggies
   - Action: Attempt to delete location
   - Assert: ValidationException raised, no changes made

4. **test_delete_location_no_buggies**
   - Setup: Location with no buggies
   - Action: Delete location
   - Assert: Location deleted successfully

5. **test_delete_location_audit_trail**
   - Setup: Location with 3 inactive buggies
   - Action: Delete location
   - Assert: Audit log contains affected buggy count and IDs

### Integration Tests

**Test File:** `tests/test_location_deletion_integration.py`

1. **test_api_delete_location_with_inactive_buggies**
   - Setup: Create location, create buggies, assign to location
   - Action: DELETE /api/locations/{id}
   - Assert: 200 response, location deleted, buggies updated

2. **test_api_delete_location_with_active_session**
   - Setup: Create location, buggy, driver, start session
   - Action: DELETE /api/locations/{id}
   - Assert: 400 response, error message about active buggy

3. **test_transaction_rollback_on_error**
   - Setup: Mock database error during deletion
   - Action: DELETE /api/locations/{id}
   - Assert: 500 response, no changes persisted

### Manual Testing Scenarios

1. **Admin Panel - Delete location with offline buggies**
   - Navigate to Locations page
   - Create test location
   - Assign 2 buggies (offline status)
   - Click delete
   - Verify: Success message, location removed, buggies show "Bilinmiyor"

2. **Admin Panel - Delete location with active driver**
   - Create location
   - Assign buggy with logged-in driver
   - Click delete
   - Verify: Error message about active buggy

3. **Driver logs out, then delete location**
   - Driver logs in and selects location
   - Driver logs out
   - Admin deletes location
   - Verify: Success, buggy location cleared

## Migration Plan

### Deployment Steps

1. **Pre-deployment**
   - Review current locations with buggies
   - Identify any locations that should be cleaned up
   - Backup database

2. **Deployment**
   - Deploy updated code
   - No database schema changes required
   - No data migration needed

3. **Post-deployment**
   - Test location deletion with inactive buggies
   - Test location deletion blocked by active buggies
   - Verify audit logs are being created correctly

### Rollback Plan

If issues arise:
1. Revert code to previous version
2. Previous behavior (block all deletions with buggies) will be restored
3. No data cleanup needed (changes are backward compatible)

### Backward Compatibility

- No breaking changes to API contracts
- Same endpoint: `DELETE /api/locations/{id}`
- Same response format
- Enhanced behavior is more permissive (allows more deletions)
- Existing integrations will continue to work

## Performance Considerations

### Query Optimization

**Current queries per deletion:**
- 1 query: Get location
- 1 query: Count active requests
- 1 query: Count buggies at location

**Enhanced queries per deletion:**
- 1 query: Get location
- 1 query: Count active requests
- 1 query: Get all buggies at location (with JOIN to buggy_drivers)
- N queries: Check active session for each buggy (can be optimized)

**Optimization opportunity:**
```python
# Instead of N queries, use a single JOIN query
buggies_with_sessions = db.session.query(
    Buggy,
    BuggyDriver.is_active
).outerjoin(
    BuggyDriver,
    (BuggyDriver.buggy_id == Buggy.id) & (BuggyDriver.is_active == True)
).filter(
    Buggy.current_location_id == location_id
).all()
```

### Expected Performance

- Typical case: 0-5 buggies per location
- Query time: < 50ms
- Total deletion time: < 200ms
- No performance degradation expected

## Security Considerations

### Authorization

- Existing `@require_login` decorator ensures authenticated user
- Hotel isolation: Location must belong to user's hotel
- No additional authorization changes needed

### Data Integrity

- Foreign key constraint `ON DELETE SET NULL` provides safety net
- Explicit NULL setting before deletion ensures consistency
- Transaction ensures atomic operation

### Audit Trail

- All deletions logged with user ID
- Affected buggy IDs recorded
- Timestamp and reason captured
- Supports compliance and troubleshooting

## Open Questions

None - design is complete and ready for implementation.
