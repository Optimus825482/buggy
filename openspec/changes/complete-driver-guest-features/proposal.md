# Complete Driver and Guest Features

## Why

The Buggy Call system has core infrastructure in place (models, services, authentication, QR codes, push notifications) but is missing critical user-facing features that complete the end-to-end workflow:

1. **Driver location management** - Drivers cannot set their location after login or after completing a task
2. **Session management** - Multiple device logins not handled, admin cannot terminate sessions
3. **Guest QR workflow** - QR code scanning doesn't redirect with location ID
4. **Driver request handling** - No UI for accepting/completing requests
5. **Real-time updates** - Push notifications configured but not fully integrated

Without these features, the system cannot function as intended for actual hotel operations.

## What Changes

### Driver Features
- Add location selection modal on first login
- Add location selection after completing a request
- Implement request acceptance workflow
- Implement request completion workflow
- Add real-time push notification handling
- Update buggy status based on driver actions

### Guest Features
- Fix QR code redirect to include location_id parameter
- Make room number truly optional in UI
- Add real-time status updates on tracking page
- Improve mobile responsiveness

### Session Management
- Implement single-device-per-user enforcement
- Add admin session termination endpoint
- Add logout functionality that properly closes sessions

### API Endpoints (New)
- `POST /api/driver/set-location` - Update driver's current location
- `POST /api/driver/accept-request/{id}` - Accept a pending request
- `POST /api/driver/complete-request/{id}` - Mark request as completed
- `POST /api/admin/sessions/{id}/terminate` - Force logout a user session

### Database Changes
- Add `current_location_id` to `buggies` table (if not exists)
- Ensure `Session` model tracks device info properly

## Impact

**Affected capabilities:**
- driver-workflow (NEW)
- guest-workflow (NEW)  
- session-management (NEW)
- admin-operations (MODIFIED)

**Affected code:**
- `app/routes/api.py` - New driver endpoints
- `app/routes/admin.py` - Session termination
- `app/routes/auth.py` - Enhanced logout
- `app/services/buggy_service.py` - Location updates
- `app/services/request_service.py` - Accept/complete logic
- `app/templates/driver/dashboard.html` - UI enhancements
- `app/templates/guest/call_premium.html` - QR redirect fix
- `app/static/js/driver-dashboard.js` - Request handling
- `app/static/js/guest.js` - Real-time updates

**Breaking changes:** None - All additions are backward compatible

**Migration required:** Database migration to add `current_location_id` column if missing
