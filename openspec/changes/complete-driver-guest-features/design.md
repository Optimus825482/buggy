# Design Document: Complete Driver and Guest Features

## Context

The Buggy Call system has a solid foundation with models, services, authentication, and infrastructure in place. However, the user-facing workflows are incomplete, preventing the system from being used in production. This change completes the missing pieces to enable full end-to-end functionality.

**Key stakeholders:**
- Hotel guests (need seamless QR-to-buggy experience)
- Buggy drivers (need efficient request management)
- Hotel administrators (need operational visibility and control)

**Constraints:**
- Must maintain backward compatibility with existing code
- Must work on mobile devices (primary use case)
- Must handle concurrent requests from multiple drivers
- Must be performant with WebSocket real-time updates

## Goals / Non-Goals

**Goals:**
- Complete driver workflow (location selection, accept/complete requests)
- Complete guest workflow (QR redirect, status tracking)
- Implement proper session management (single device, admin termination)
- Enable real-time updates via WebSocket and push notifications
- Maintain audit trail for all critical operations

**Non-Goals:**
- Advanced routing/optimization algorithms (future enhancement)
- SMS notifications (push notifications only for now)
- Multi-language support (Turkish only for MVP)
- Offline mode (requires internet connection)
- Driver performance analytics (future enhancement)

## Decisions

### 1. Database Schema: Add current_location_id to buggies table

**Decision:** Add nullable foreign key `current_location_id` to `buggies` table

**Rationale:**
- Tracks where each buggy is currently located
- Enables location-based filtering and reporting
- Nullable because location is set after first login, not during buggy creation
- Foreign key ensures referential integrity

**Alternatives considered:**
- Store location in separate tracking table → Rejected: Overkill for current needs
- Store location in driver session → Rejected: Lost on logout

**Implementation:**
```python
# Migration
current_location_id = Column(Integer, ForeignKey('locations.id', ondelete='SET NULL'), nullable=True)
```

### 2. Session Management: Single Device Enforcement

**Decision:** Terminate old session when new login detected from different device

**Rationale:**
- Prevents unauthorized access if device is lost/stolen
- Simplifies session management (no multi-device sync needed)
- Common pattern in banking/security-sensitive apps
- Reduces server resource usage

**Alternatives considered:**
- Allow multiple devices → Rejected: Security risk, complex state management
- Require explicit logout → Rejected: Users forget to logout

**Implementation:**
- On login, query for existing active sessions for user
- If found, mark old session as terminated
- Emit WebSocket 'force_logout' event to old device
- Create new session for new device

### 3. Request Acceptance: Race Condition Handling

**Decision:** Use database transaction with row-level locking

**Rationale:**
- Multiple drivers may click "Accept" simultaneously
- Only first driver should get the request
- Database ACID properties ensure consistency
- Prevents double-booking

**Implementation:**
```python
# Use SELECT FOR UPDATE to lock the row
request = db.session.query(BuggyRequest).filter_by(
    id=request_id,
    status=RequestStatus.PENDING
).with_for_update().first()

if not request:
    raise ValidationException('Request no longer available')

# Update status within same transaction
request.status = RequestStatus.ACCEPTED
db.session.commit()
```

### 4. Real-time Updates: WebSocket + Polling Fallback

**Decision:** Primary: WebSocket events, Fallback: HTTP polling every 5 seconds

**Rationale:**
- WebSocket provides instant updates with low overhead
- Some networks/proxies block WebSockets
- Polling ensures functionality even if WebSocket fails
- 5-second interval balances freshness vs server load

**Implementation:**
- Guest status page attempts WebSocket connection
- If connection fails or closes, switch to polling
- Polling uses existing `/api/requests/{id}` endpoint

### 5. Location Selection: Modal vs Dedicated Page

**Decision:** Use modal dialog for location selection

**Rationale:**
- Faster UX (no page navigation)
- Maintains context (driver stays on dashboard)
- Consistent with modern web app patterns
- Easier to make mandatory (blocks other actions)

**Alternatives considered:**
- Dedicated page → Rejected: Extra navigation step
- Dropdown in header → Rejected: Easy to miss, not prominent enough

### 6. QR Code URL Format

**Decision:** Generate QR codes with URL: `https://{domain}/guest/call?location={id}`

**Rationale:**
- Simple and readable
- Location ID in query parameter (easy to parse)
- Works with any QR scanner (standard URL)
- No custom URL scheme needed

**Alternatives considered:**
- Custom scheme `buggycall://` → Rejected: Requires app installation
- Encoded data in hash → Rejected: Less readable, harder to debug

## Risks / Trade-offs

### Risk: WebSocket Connection Stability
**Mitigation:** Implement automatic reconnection with exponential backoff + polling fallback

### Risk: Race Conditions on Request Acceptance
**Mitigation:** Database row-level locking + optimistic locking checks

### Risk: Push Notification Delivery Failures
**Mitigation:** Log all notification attempts, provide in-app fallback (polling)

### Risk: Session Termination Edge Cases
**Mitigation:** Comprehensive audit logging, graceful error handling

### Trade-off: Single Device vs Multi-Device
**Chosen:** Single device for security and simplicity
**Cost:** User must re-login if switching devices
**Benefit:** Simpler state management, better security

### Trade-off: Real-time vs Polling
**Chosen:** WebSocket primary, polling fallback
**Cost:** More complex client code
**Benefit:** Works in all network conditions

## Migration Plan

### Database Migration
```bash
# Create migration
flask db migrate -m "Add current_location_id to buggies"

# Review generated migration
# Edit if needed to ensure:
# - Column is nullable
# - Foreign key has ON DELETE SET NULL
# - Index is created for performance

# Apply migration
flask db upgrade
```

### Deployment Steps
1. **Pre-deployment:**
   - Backup database
   - Test migration on staging environment
   - Verify rollback procedure

2. **Deployment:**
   - Apply database migration
   - Deploy new code
   - Restart application servers
   - Verify WebSocket connections working

3. **Post-deployment:**
   - Monitor error logs for issues
   - Test complete workflows (guest, driver, admin)
   - Verify push notifications working
   - Check audit trail logging

### Rollback Plan
If critical issues found:
1. Revert code deployment
2. Rollback database migration: `flask db downgrade`
3. Restart application servers
4. Investigate issues in staging

### Data Migration
No data migration needed - new column is nullable and will be populated as drivers log in and set locations.

## Open Questions

1. **Q:** Should we limit how often a driver can change location?
   **A:** No limit for MVP. Can add rate limiting if abused.

2. **Q:** What happens if a driver goes offline mid-request?
   **A:** Request remains "accepted" but admin can manually reassign. Future: Auto-reassign after timeout.

3. **Q:** Should guests be able to cancel requests?
   **A:** Not in this change. Add in future iteration with cancellation reasons.

4. **Q:** How long should completed requests stay visible?
   **A:** Keep in database indefinitely for reporting. UI shows last 24 hours by default.

5. **Q:** Should we validate room numbers against hotel room list?
   **A:** Not for MVP (room number is optional). Future enhancement if needed.
