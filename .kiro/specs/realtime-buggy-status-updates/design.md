# Design Document

## Overview

Admin panelindeki "Buggy Durumu" listesinin WebSocket üzerinden gerçek zamanlı güncellenmesi için teknik tasarım. Mevcut WebSocket altyapısı (Socket.IO) kullanılarak, buggy durum değişikliklerinin anlık olarak admin istemcilerine iletilmesi sağlanacak.

## Architecture

### Mevcut Durum

Sistem zaten Socket.IO tabanlı WebSocket altyapısına sahip:
- Backend: Flask-SocketIO (app/websocket/)
- Frontend: Socket.IO client (admin.js)
- Room-based broadcasting (hotel_id_admins)
- Mevcut event'ler: driver_location_updated, request_status_changed

### Yeni Mimari

```
┌─────────────────┐
│  Driver Action  │ (Session start/end, status change)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Backend Event  │ (emit buggy_status_update)
│   Emitter       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Socket.IO     │ (room: hotel_{id}_admins)
│   Broadcast     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Admin Client   │ (socket.on('buggy_status_update'))
│   Listener      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   DOM Update    │ (Update specific buggy row)
└─────────────────┘
```

## Components and Interfaces

### 1. Backend Event Emitter

**Lokasyon**: `app/services/buggy_service.py` (yeni helper fonksiyon)

```python
def emit_buggy_status_update(buggy_id, hotel_id):
    """
    Emit buggy status update to all admin clients
    
    Args:
        buggy_id: Buggy ID
        hotel_id: Hotel ID for room targeting
    """
    from app import socketio
    from app.models.buggy import Buggy
    from app.models.buggy_driver import BuggyDriver
    from app.models.user import SystemUser
    
    buggy = Buggy.query.get(buggy_id)
    if not buggy:
        return
    
    # Get active session info
    active_session = BuggyDriver.query.filter_by(
        buggy_id=buggy_id,
        is_active=True
    ).first()
    
    driver_name = None
    if active_session:
        driver = SystemUser.query.get(active_session.driver_id)
        driver_name = driver.name if driver else None
    
    # Determine status
    status = 'offline'
    if active_session:
        status = 'busy' if buggy.current_request_id else 'available'
    
    # Emit to admin room
    socketio.emit('buggy_status_update', {
        'buggy_id': buggy.id,
        'buggy_code': buggy.code,
        'buggy_icon': buggy.icon,
        'status': status,
        'driver_name': driver_name,
        'location_id': buggy.current_location_id,
        'timestamp': datetime.utcnow().isoformat()
    }, room=f'hotel_{hotel_id}_admins')
```

### 2. WebSocket Event Handler

**Lokasyon**: `app/websocket/events.py` (yeni event - opsiyonel, emit_buggy_status_update yeterli)

Mevcut event'ler yeterli, yeni event handler'a gerek yok. Sadece emit fonksiyonu kullanılacak.

### 3. Frontend Socket Listener

**Lokasyon**: `app/static/js/admin.js`

```javascript
// WebSocket connection status indicator
let connectionStatus = {
    connected: false,
    indicator: null
};

// Initialize connection status indicator
function initConnectionStatus() {
    const indicator = document.createElement('div');
    indicator.id = 'ws-status-indicator';
    indicator.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        background: #ef4444;
        box-shadow: 0 0 10px rgba(239, 68, 68, 0.5);
        z-index: 9999;
        transition: all 0.3s ease;
    `;
    document.body.appendChild(indicator);
    connectionStatus.indicator = indicator;
}

// Update connection status
function updateConnectionStatus(status) {
    if (!connectionStatus.indicator) return;
    
    const colors = {
        connected: '#10b981',
        connecting: '#f59e0b',
        disconnected: '#ef4444'
    };
    
    connectionStatus.indicator.style.background = colors[status] || colors.disconnected;
    connectionStatus.connected = (status === 'connected');
}

// Listen for buggy status updates
socket.on('buggy_status_update', function(data) {
    console.log('Buggy status update:', data);
    updateBuggyStatusRow(data);
});

// Update specific buggy row in DOM
function updateBuggyStatusRow(data) {
    const row = document.querySelector(`tr[data-buggy-id="${data.buggy_id}"]`);
    if (!row) {
        // Buggy row doesn't exist, reload list
        loadBuggyStatus();
        return;
    }
    
    // Update status badge
    const statusCell = row.querySelector('.status-badge');
    if (statusCell) {
        const statusConfig = {
            'available': { text: 'Çevrimiçi', class: 'badge-success' },
            'busy': { text: 'Meşgul', class: 'badge-warning' },
            'offline': { text: 'Çevrimdışı', class: 'badge-secondary' }
        };
        
        const config = statusConfig[data.status] || statusConfig.offline;
        statusCell.textContent = config.text;
        statusCell.className = `badge ${config.class}`;
        
        // Add smooth transition
        statusCell.style.transition = 'all 0.3s ease';
    }
    
    // Update driver name
    const driverCell = row.querySelector('.driver-name');
    if (driverCell) {
        driverCell.textContent = data.driver_name || '-';
    }
    
    // Update location (if available)
    if (data.location_id) {
        const locationCell = row.querySelector('.location-name');
        if (locationCell) {
            // Location name will be fetched or cached
            updateLocationName(locationCell, data.location_id);
        }
    }
}

// Connection event handlers
socket.on('connect', function() {
    console.log('WebSocket connected');
    updateConnectionStatus('connected');
    showNotification('Bağlantı kuruldu', 'success');
});

socket.on('disconnect', function() {
    console.log('WebSocket disconnected');
    updateConnectionStatus('disconnected');
    showNotification('Bağlantı koptu', 'error');
});

socket.on('reconnecting', function() {
    console.log('WebSocket reconnecting...');
    updateConnectionStatus('connecting');
});
```

### 4. Backend Integration Points

**Trigger noktaları** (emit_buggy_status_update çağrılacak yerler):

1. **Driver Session Start** (`app/routes/driver.py` - start_session)
   ```python
   # After session created
   emit_buggy_status_update(buggy_id, hotel_id)
   ```

2. **Driver Session End** (`app/routes/driver.py` - end_session)
   ```python
   # After session ended
   emit_buggy_status_update(buggy_id, hotel_id)
   ```

3. **Request Accepted** (`app/routes/driver.py` - accept_request)
   ```python
   # After request accepted
   emit_buggy_status_update(buggy_id, hotel_id)
   ```

4. **Request Completed** (`app/routes/driver.py` - complete_request)
   ```python
   # After request completed
   emit_buggy_status_update(buggy_id, hotel_id)
   ```

5. **Admin Manual Status Change** (eğer varsa)
   ```python
   # After admin changes buggy status
   emit_buggy_status_update(buggy_id, hotel_id)
   ```

## Data Models

### WebSocket Event Payload

```typescript
interface BuggyStatusUpdate {
    buggy_id: number;
    buggy_code: string;
    buggy_icon: string;
    status: 'available' | 'busy' | 'offline';
    driver_name: string | null;
    location_id: number | null;
    timestamp: string; // ISO 8601
}
```

### Frontend State

```javascript
// No persistent state needed
// Updates are applied directly to DOM
// Fallback: reload entire list if row not found
```

## Error Handling

### Backend Errors

1. **Buggy Not Found**
   - Log warning
   - Skip emit
   - No error to client

2. **Socket.IO Emit Failure**
   - Log error
   - Continue execution (non-blocking)
   - Client will see stale data until next update

3. **Database Query Failure**
   - Log error
   - Skip emit
   - Return gracefully

### Frontend Errors

1. **WebSocket Disconnection**
   - Show red indicator
   - Auto-reconnect (Socket.IO default)
   - Show notification on reconnect

2. **Missing DOM Element**
   - Reload entire buggy list
   - Log warning

3. **Invalid Data Format**
   - Log error
   - Skip update
   - Keep existing data

## Testing Strategy

### Unit Tests

1. **Backend**
   - `test_emit_buggy_status_update()` - Verify correct data format
   - `test_emit_with_active_session()` - Status = busy/available
   - `test_emit_without_session()` - Status = offline
   - `test_emit_invalid_buggy()` - Graceful failure

2. **Frontend**
   - `test_updateBuggyStatusRow()` - DOM update
   - `test_updateBuggyStatusRow_missing()` - Fallback to reload
   - `test_connectionStatus()` - Indicator updates

### Integration Tests

1. **Session Flow**
   - Start session → Admin sees "Çevrimiçi"
   - Accept request → Admin sees "Meşgul"
   - Complete request → Admin sees "Çevrimiçi"
   - End session → Admin sees "Çevrimdışı"

2. **Multi-Admin**
   - Multiple admin clients receive same update
   - Updates are synchronized

3. **Reconnection**
   - Disconnect → Reconnect → Updates resume

### Manual Testing

1. Open admin dashboard in 2 browser tabs
2. Start driver session
3. Verify both admin tabs update instantly
4. Accept/complete request
5. Verify status changes in real-time
6. End session
7. Verify offline status

## Performance Considerations

### Throttling

```javascript
// Throttle updates to max 10/second per buggy
const updateThrottle = new Map();

function updateBuggyStatusRow(data) {
    const key = `buggy_${data.buggy_id}`;
    const now = Date.now();
    const lastUpdate = updateThrottle.get(key) || 0;
    
    if (now - lastUpdate < 100) { // 100ms = max 10 updates/sec
        return;
    }
    
    updateThrottle.set(key, now);
    // ... actual update logic
}
```

### DOM Optimization

- Update only changed cells (not entire row)
- Use CSS transitions for smooth visual updates
- Batch updates if multiple buggies change simultaneously

### Memory Management

- Clean up throttle map periodically
- Remove event listeners on page unload
- Close WebSocket connection properly

## Security Considerations

1. **Room Authorization**
   - Only admins can join `hotel_{id}_admins` room
   - Verify user role on join_hotel event

2. **Data Validation**
   - Validate buggy_id belongs to hotel
   - Sanitize all emitted data

3. **Rate Limiting**
   - Throttle emit calls (max 10/sec per buggy)
   - Prevent spam attacks

## Migration Plan

### Phase 1: Backend Implementation
1. Create `emit_buggy_status_update()` helper
2. Add emit calls to all trigger points
3. Test with existing WebSocket infrastructure

### Phase 2: Frontend Implementation
1. Add connection status indicator
2. Add `buggy_status_update` listener
3. Implement `updateBuggyStatusRow()`
4. Add throttling logic

### Phase 3: Testing & Rollout
1. Unit tests
2. Integration tests
3. Manual testing with multiple clients
4. Deploy to production

### Rollback Plan

If issues occur:
1. Remove emit calls from backend (comment out)
2. Frontend will continue to work with polling/refresh
3. No data loss or corruption risk

## Open Questions

1. ~~Should we cache location names on frontend?~~ → Yes, fetch once and cache
2. ~~Should we show timestamp of last update?~~ → No, not needed for MVP
3. ~~Should we add sound notification for status changes?~~ → No, visual only for MVP
