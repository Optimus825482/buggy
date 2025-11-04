# Design Document

## Overview

Bu tasarım, sürücü ve admin kullanıcılarının login olduktan sonra tarayıcı bildirim izinlerinin otomatik olarak kontrol edilmesini ve gerektiğinde kullanıcıdan izin talep edilmesini sağlar. Mevcut `PushNotificationManager` sınıfı üzerine inşa edilecek ve kullanıcı deneyimini bozmadan, oturum bazlı akıllı bir izin talep mekanizması sunacaktır.

## Architecture

### High-Level Flow

```
Login Success
    ↓
Check User Role (Driver/Admin?)
    ↓
Check Session Flag (Already Asked?)
    ↓
Check Browser Permission Status
    ↓
Display Permission Dialog (if needed)
    ↓
Handle User Response
    ↓
Store Session Flag
    ↓
Continue to Dashboard
```

### Component Interaction

```
┌─────────────────┐
│  Login Page     │
│  (auth.py)      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Auth Service   │
│  (login)        │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────┐
│  Dashboard Template         │
│  (driver/admin)             │
│  - Inject user role         │
│  - Inject session flag      │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  notification-permission.js │
│  - Check conditions         │
│  - Show dialog if needed    │
│  - Handle responses         │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  PushNotificationManager    │
│  - Request permission       │
│  - Subscribe to push        │
└─────────────────────────────┘
```

## Components and Interfaces

### 1. Backend Components

#### Session Management (app/services/auth.py)

Mevcut login fonksiyonuna ekleme yapılacak:

```python
# Session'a bildirim izni durumunu ekle
session['notification_permission_asked'] = False
session['notification_permission_status'] = 'default'
```

#### Dashboard Routes (app/routes/driver.py, app/routes/admin.py)

Template'e session bilgilerini inject et:

```python
@driver_bp.route('/dashboard')
def dashboard():
    return render_template('driver/dashboard.html',
        notification_permission_asked=session.get('notification_permission_asked', False),
        notification_permission_status=session.get('notification_permission_status', 'default')
    )
```

#### API Endpoint (app/routes/api.py)

Bildirim izni durumunu kaydetmek için yeni endpoint:

```python
@api_bp.route('/notification-permission', methods=['POST'])
def update_notification_permission():
    """Update notification permission status in session"""
    data = request.get_json()
    session['notification_permission_asked'] = True
    session['notification_permission_status'] = data.get('status', 'default')
    return jsonify({'success': True})
```

### 2. Frontend Components

#### notification-permission.js (Yeni Dosya)

Ana kontrol ve dialog yönetimi:

```javascript
class NotificationPermissionHandler {
    constructor() {
        this.userRole = null;
        this.alreadyAsked = false;
        this.currentStatus = 'default';
        this.dialog = null;
    }

    init(userRole, alreadyAsked, currentStatus) {
        this.userRole = userRole;
        this.alreadyAsked = alreadyAsked;
        this.currentStatus = currentStatus;

        // Only for driver and admin
        if (this.userRole !== 'driver' && this.userRole !== 'admin') {
            return;
        }

        // Check if we should show dialog
        this.checkAndShowDialog();
    }

    async checkAndShowDialog() {
        // Don't show if already asked in this session
        if (this.alreadyAsked) {
            return;
        }

        // Check browser permission status
        const browserStatus = await this.getBrowserPermissionStatus();

        // Only show if permission is 'default' (not granted or denied)
        if (browserStatus === 'default') {
            this.showDialog();
        } else {
            // Update session with current status
            await this.updateSessionStatus(browserStatus);
        }
    }

    async getBrowserPermissionStatus() {
        if (!('Notification' in window)) {
            return 'denied';
        }
        return Notification.permission;
    }

    showDialog() {
        // Create and show custom dialog
        this.dialog = this.createDialog();
        document.body.appendChild(this.dialog);

        // Animate in
        setTimeout(() => {
            this.dialog.classList.add('show');
        }, 100);
    }

    createDialog() {
        const dialog = document.createElement('div');
        dialog.className = 'notification-permission-dialog';
        dialog.innerHTML = `
            <div class="notification-permission-overlay"></div>
            <div class="notification-permission-content">
                <div class="notification-permission-icon">
                    <i class="fas fa-bell"></i>
                </div>
                <h3>Bildirimler</h3>
                <p>Misafirlerden gelen buggy taleplerini anında almak için bildirim izni verin.</p>
                <div class="notification-permission-actions">
                    <button class="btn-allow" onclick="notificationPermissionHandler.handleAllow()">
                        <i class="fas fa-check"></i> İzin Ver
                    </button>
                    <button class="btn-later" onclick="notificationPermissionHandler.handleLater()">
                        Şimdi Değil
                    </button>
                </div>
            </div>
        `;
        return dialog;
    }

    async handleAllow() {
        // Request browser permission
        const permission = await pushNotifications.requestPermission();

        // Update session
        await this.updateSessionStatus(permission);

        // Close dialog
        this.closeDialog();
    }

    async handleLater() {
        // Update session (asked but not granted)
        await this.updateSessionStatus('default');

        // Close dialog
        this.closeDialog();
    }

    async updateSessionStatus(status) {
        try {
            await fetch('/api/notification-permission', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                },
                body: JSON.stringify({ status })
            });
        } catch (error) {
            console.error('[NotificationPermission] Error updating session:', error);
        }
    }

    closeDialog() {
        if (this.dialog) {
            this.dialog.classList.remove('show');
            setTimeout(() => {
                this.dialog.remove();
                this.dialog = null;
            }, 300);
        }
    }
}

// Global instance
const notificationPermissionHandler = new NotificationPermissionHandler();
```

#### CSS Styling (app/static/css/notification-permission.css)

Modern ve profesyonel dialog tasarımı:

```css
.notification-permission-dialog {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    z-index: 10000;
    display: flex;
    align-items: center;
    justify-content: center;
    opacity: 0;
    transition: opacity 0.3s ease;
}

.notification-permission-dialog.show {
    opacity: 1;
}

.notification-permission-overlay {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    backdrop-filter: blur(4px);
}

.notification-permission-content {
    position: relative;
    background: white;
    border-radius: 20px;
    padding: 32px;
    max-width: 400px;
    width: calc(100% - 40px);
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
    text-align: center;
    transform: scale(0.9);
    transition: transform 0.3s ease;
}

.notification-permission-dialog.show .notification-permission-content {
    transform: scale(1);
}

.notification-permission-icon {
    width: 80px;
    height: 80px;
    margin: 0 auto 20px;
    background: linear-gradient(135deg, #1BA5A8 0%, #158B8E 100%);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 36px;
    color: white;
    animation: pulse 2s infinite;
}

@keyframes pulse {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.05); }
}

.notification-permission-content h3 {
    font-size: 24px;
    font-weight: 700;
    color: #1a1a1a;
    margin: 0 0 12px 0;
}

.notification-permission-content p {
    font-size: 16px;
    color: #666;
    line-height: 1.6;
    margin: 0 0 24px 0;
}

.notification-permission-actions {
    display: flex;
    flex-direction: column;
    gap: 12px;
}

.notification-permission-actions button {
    padding: 14px 24px;
    border: none;
    border-radius: 12px;
    font-size: 16px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
}

.btn-allow {
    background: linear-gradient(135deg, #1BA5A8 0%, #158B8E 100%);
    color: white;
    box-shadow: 0 4px 12px rgba(27, 165, 168, 0.3);
}

.btn-allow:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(27, 165, 168, 0.4);
}

.btn-later {
    background: #f5f5f5;
    color: #666;
}

.btn-later:hover {
    background: #e5e5e5;
}

@media (max-width: 768px) {
    .notification-permission-content {
        padding: 24px;
    }

    .notification-permission-icon {
        width: 64px;
        height: 64px;
        font-size: 28px;
    }

    .notification-permission-content h3 {
        font-size: 20px;
    }

    .notification-permission-content p {
        font-size: 14px;
    }
}
```

### 3. Template Integration

#### Driver Dashboard (templates/driver/dashboard.html)

```html
{% block extra_js %}
<script>
    // Initialize notification permission handler
    document.addEventListener('DOMContentLoaded', function() {
        notificationPermissionHandler.init(
            'driver',
            {{ notification_permission_asked|tojson }},
            '{{ notification_permission_status }}'
        );
    });
</script>
{% endblock %}
```

#### Admin Dashboard (templates/admin/dashboard.html)

```html
{% block extra_js %}
<script>
    // Initialize notification permission handler
    document.addEventListener('DOMContentLoaded', function() {
        notificationPermissionHandler.init(
            'admin',
            {{ notification_permission_asked|tojson }},
            '{{ notification_permission_status }}'
        );
    });
</script>
{% endblock %}
```

## Data Models

### Session Data Structure

```python
session = {
    'user_id': int,
    'role': str,  # 'driver', 'admin', 'guest'
    'notification_permission_asked': bool,  # Yeni
    'notification_permission_status': str,  # 'default', 'granted', 'denied'
    # ... diğer session verileri
}
```

### API Request/Response

#### POST /api/notification-permission

**Request:**
```json
{
    "status": "granted" | "denied" | "default"
}
```

**Response:**
```json
{
    "success": true
}
```

## Error Handling

### Browser Compatibility

```javascript
// Check if notifications are supported
if (!('Notification' in window)) {
    console.warn('[NotificationPermission] Notifications not supported');
    // Don't show dialog
    return;
}
```

### Permission Request Failure

```javascript
try {
    const permission = await Notification.requestPermission();
    // Handle permission
} catch (error) {
    console.error('[NotificationPermission] Request failed:', error);
    // Update session with 'denied' status
    await this.updateSessionStatus('denied');
}
```

### Network Errors

```javascript
try {
    await fetch('/api/notification-permission', { ... });
} catch (error) {
    console.error('[NotificationPermission] Network error:', error);
    // Continue without blocking user
    // Session will be updated on next login
}
```

### Session Errors

```python
@api_bp.route('/notification-permission', methods=['POST'])
def update_notification_permission():
    try:
        data = request.get_json()
        session['notification_permission_asked'] = True
        session['notification_permission_status'] = data.get('status', 'default')
        return jsonify({'success': True})
    except Exception as e:
        app.logger.error(f'Error updating notification permission: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500
```

## Testing Strategy

### Unit Tests

1. **NotificationPermissionHandler Tests**
   - Test role checking (driver, admin, guest)
   - Test session flag checking
   - Test browser permission status detection
   - Test dialog creation and display
   - Test user action handling (allow, later)

2. **API Endpoint Tests**
   - Test session update
   - Test error handling
   - Test authentication requirement

### Integration Tests

1. **Login Flow Tests**
   - Test driver login → permission dialog shown
   - Test admin login → permission dialog shown
   - Test guest login → no permission dialog
   - Test second login → no permission dialog (already asked)

2. **Permission Flow Tests**
   - Test "İzin Ver" → browser permission requested
   - Test "Şimdi Değil" → dialog closed, session updated
   - Test browser permission granted → session updated
   - Test browser permission denied → session updated

### E2E Tests

1. **Complete User Journey**
   - Login as driver
   - See permission dialog
   - Grant permission
   - Verify notifications work
   - Logout and login again
   - Verify no dialog shown

2. **Cross-Browser Tests**
   - Chrome/Edge (Chromium)
   - Firefox
   - Safari (iOS/macOS)
   - Mobile browsers

### Manual Testing Checklist

- [ ] Driver login shows dialog (first time)
- [ ] Admin login shows dialog (first time)
- [ ] Guest login doesn't show dialog
- [ ] "İzin Ver" triggers browser permission
- [ ] "Şimdi Değil" closes dialog
- [ ] Second login doesn't show dialog
- [ ] Logout/login cycle works correctly
- [ ] Dialog is responsive on mobile
- [ ] Dialog is accessible (keyboard navigation)
- [ ] Dialog works with screen readers

## Performance Considerations

### Non-Blocking Implementation

```javascript
// Check permission asynchronously after page load
document.addEventListener('DOMContentLoaded', function() {
    // Wait 2 seconds after page load to show dialog
    setTimeout(() => {
        notificationPermissionHandler.init(...);
    }, 2000);
});
```

### Lazy Loading

```html
<!-- Load notification permission script only for driver/admin -->
{% if session.role in ['driver', 'admin'] %}
<link rel="stylesheet" href="{{ url_for('static', filename='css/notification-permission.css') }}">
<script src="{{ url_for('static', filename='js/notification-permission.js') }}"></script>
{% endif %}
```

### Session Storage Optimization

```python
# Only store necessary data in session
session['notification_permission_asked'] = True  # Boolean, minimal size
session['notification_permission_status'] = 'granted'  # String, minimal size
```

## Security Considerations

### CSRF Protection

```javascript
// Include CSRF token in API requests
headers: {
    'Content-Type': 'application/json',
    'X-CSRFToken': getCSRFToken()
}
```

### Session Validation

```python
@api_bp.route('/notification-permission', methods=['POST'])
@login_required  # Ensure user is authenticated
def update_notification_permission():
    # Validate user role
    if session.get('role') not in ['driver', 'admin']:
        return jsonify({'error': 'Unauthorized'}), 403
    # ...
```

### Input Validation

```python
# Validate status value
valid_statuses = ['default', 'granted', 'denied']
status = data.get('status', 'default')
if status not in valid_statuses:
    return jsonify({'error': 'Invalid status'}), 400
```

## Accessibility

### Keyboard Navigation

```javascript
// Add keyboard event listeners
dialog.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        this.handleLater();
    }
});
```

### Screen Reader Support

```html
<div class="notification-permission-content" role="dialog" aria-labelledby="dialog-title" aria-describedby="dialog-description">
    <h3 id="dialog-title">Bildirimler</h3>
    <p id="dialog-description">Misafirlerden gelen buggy taleplerini anında almak için bildirim izni verin.</p>
    <button aria-label="Bildirim izni ver">İzin Ver</button>
    <button aria-label="Şimdi bildirim izni verme">Şimdi Değil</button>
</div>
```

### Focus Management

```javascript
showDialog() {
    this.dialog = this.createDialog();
    document.body.appendChild(this.dialog);

    // Focus first button
    setTimeout(() => {
        const firstButton = this.dialog.querySelector('.btn-allow');
        if (firstButton) {
            firstButton.focus();
        }
    }, 100);
}
```

## Migration Plan

### Phase 1: Backend Setup
1. Add session fields to auth service
2. Create API endpoint
3. Update dashboard routes

### Phase 2: Frontend Implementation
1. Create notification-permission.js
2. Create notification-permission.css
3. Integrate with existing PushNotificationManager

### Phase 3: Template Integration
1. Update driver dashboard template
2. Update admin dashboard template
3. Add conditional script loading

### Phase 4: Testing
1. Unit tests
2. Integration tests
3. E2E tests
4. Manual testing

### Phase 5: Deployment
1. Deploy to staging
2. Test with real users
3. Monitor logs and errors
4. Deploy to production

## Rollback Plan

If issues occur:

1. **Disable feature via feature flag:**
```python
# In config.py
NOTIFICATION_PERMISSION_ENABLED = False

# In dashboard routes
if app.config.get('NOTIFICATION_PERMISSION_ENABLED', False):
    # Include notification permission logic
```

2. **Remove session fields:**
```python
# Clean up session
session.pop('notification_permission_asked', None)
session.pop('notification_permission_status', None)
```

3. **Revert template changes:**
```html
<!-- Comment out notification permission scripts -->
{% if False %}
<script src="{{ url_for('static', filename='js/notification-permission.js') }}"></script>
{% endif %}
```

## Monitoring and Logging

### Backend Logging

```python
app.logger.info(f'[NotificationPermission] User {user_id} permission status: {status}')
app.logger.warning(f'[NotificationPermission] Failed to update session for user {user_id}')
app.logger.error(f'[NotificationPermission] Error: {error}')
```

### Frontend Logging

```javascript
console.log('[NotificationPermission] Dialog shown for user role:', this.userRole);
console.log('[NotificationPermission] Permission granted:', permission);
console.error('[NotificationPermission] Error:', error);
```

### Metrics to Track

- Number of permission dialogs shown
- Number of permissions granted vs denied
- Number of "Şimdi Değil" clicks
- Time to grant permission
- Error rates
- Browser compatibility issues

## Future Enhancements

1. **Reminder System**: Show dialog again after X days if user clicked "Şimdi Değil"
2. **Settings Page**: Allow users to change notification preferences
3. **Notification Types**: Let users choose which notifications to receive
4. **Sound Preferences**: Allow users to customize notification sounds
5. **Do Not Disturb**: Implement quiet hours for notifications
6. **Analytics Dashboard**: Show notification engagement metrics to admins
