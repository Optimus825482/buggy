# Design Document - Advanced Mobile Push Notifications

## Overview

Bu tasarım, BuggyCall uygulamasının push bildirim sistemini mobil ve tablet cihazlar için optimize eder. Sistem, Progressive Web App (PWA) standartlarına uygun, Service Worker tabanlı, arka planda çalışabilen ve kilit ekranında bile bildirim gösterebilen gelişmiş bir mimari kullanacaktır.

### Temel Hedefler

1. **Güvenilir Bildirim Teslimatı**: Uygulama durumundan bağımsız %99.9 teslimat oranı
2. **Düşük Gecikme**: Push bildirimlerinin 2 saniye içinde cihaza ulaşması
3. **Batarya Verimliliği**: Arka plan işlemlerinin minimal CPU ve batarya kullanımı
4. **Offline Destek**: Ağ bağlantısı olmadan bile bildirim kuyruklama
5. **Native-Like UX**: Mobil cihazlarda native app deneyimi

### Teknoloji Stack

- **Backend**: Python/Flask + pywebpush
- **Frontend**: Vanilla JavaScript + Web APIs
- **Service Worker**: Background processing ve push handling
- **Storage**: IndexedDB (offline queue) + LocalStorage (preferences)
- **PWA**: Web App Manifest + Service Worker
- **Push Protocol**: Web Push API (VAPID)

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Backend Server (Flask)                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Notification │  │   Push API   │  │  Admin API   │      │
│  │   Service    │──│   (VAPID)    │──│  (Monitor)   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ Web Push Protocol
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              Push Service (Browser Vendor)                   │
│         (FCM for Chrome, APNs for Safari, etc.)             │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ Push Message
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Mobile/Tablet Device                      │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Service Worker (sw.js)                   │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐     │  │
│  │  │   Push     │  │  Offline   │  │   Badge    │     │  │
│  │  │  Handler   │  │   Queue    │  │  Manager   │     │  │
│  │  └────────────┘  └────────────┘  └────────────┘     │  │
│  └──────────────────────────────────────────────────────┘  │
│                              │                               │
│                              ▼                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           Notification Display Layer                  │  │
│  │  • Lock Screen  • Notification Center  • In-App      │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```


### Component Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Service Worker Layer                       │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Push Event Handler (Enhanced)                 │  │
│  │  • Priority-based routing                             │  │
│  │  • Rich media processing                              │  │
│  │  • Action button handling                             │  │
│  │  • Sound & vibration control                          │  │
│  └──────────────────────────────────────────────────────┘  │
│                              │                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Notification Manager                          │  │
│  │  • Grouping logic                                     │  │
│  │  • Badge counter                                      │  │
│  │  • Persistent notifications                           │  │
│  │  • DND mode handling                                  │  │
│  └──────────────────────────────────────────────────────┘  │
│                              │                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Offline Queue Manager                         │  │
│  │  • IndexedDB storage                                  │  │
│  │  • Background sync                                    │  │
│  │  • Retry logic with exponential backoff              │  │
│  │  • Network status monitoring                          │  │
│  └──────────────────────────────────────────────────────┘  │
│                              │                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Performance Monitor                           │  │
│  │  • Battery usage tracking                             │  │
│  │  • CPU usage optimization                             │  │
│  │  • Memory management                                  │  │
│  │  • Error logging & recovery                           │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### 1. Enhanced Service Worker (sw.js)

**Sorumluluklar:**
- Push event handling ve notification display
- Offline queue management
- Background sync coordination
- Badge counter management
- Performance optimization

**Yeni Özellikler:**


```javascript
// Enhanced Push Event Handler
self.addEventListener('push', async (event) => {
  const data = event.data.json();
  const priority = data.priority || 'normal';
  
  // Priority-based handling
  const options = buildNotificationOptions(data, priority);
  
  event.waitUntil(
    Promise.all([
      // Display notification
      self.registration.showNotification(data.title, options),
      
      // Update badge
      updateBadgeCount(1),
      
      // Play sound
      playPrioritySound(priority),
      
      // Log delivery
      logNotificationDelivery(data),
      
      // Store for offline access
      storeNotification(data)
    ])
  );
});

// Notification grouping
function buildNotificationOptions(data, priority) {
  return {
    body: data.body,
    icon: data.icon || '/static/icons/Icon-192.png',
    badge: data.badge || '/static/icons/Icon-96.png',
    tag: data.tag || `buggy-${data.type}`, // Grouping key
    renotify: true, // Re-alert for same tag
    requireInteraction: priority === 'high',
    silent: false,
    vibrate: getVibrationPattern(priority),
    actions: buildActionButtons(data),
    data: {
      ...data.data,
      timestamp: Date.now(),
      priority: priority
    },
    image: data.image, // Rich media support
    dir: 'ltr',
    lang: 'tr'
  };
}

// Priority-based vibration patterns
function getVibrationPattern(priority) {
  const patterns = {
    'high': [200, 100, 200, 100, 200, 100, 200],    // Urgent
    'normal': [200, 100, 200],                       // Standard
    'low': [100]                                     // Subtle
  };
  return patterns[priority] || patterns.normal;
}

// Dynamic action buttons
function buildActionButtons(data) {
  if (data.type === 'new_request') {
    return [
      {
        action: 'accept',
        title: '✅ Kabul Et',
        icon: '/static/icons/Icon-96.png'
      },
      {
        action: 'details',
        title: '📋 Detaylar',
        icon: '/static/icons/Icon-72.png'
      }
    ];
  }
  return [
    {
      action: 'view',
      title: '👀 Görüntüle',
      icon: '/static/icons/Icon-96.png'
    }
  ];
}
```

### 2. Offline Queue Manager

**IndexedDB Schema:**

```javascript
const DB_SCHEMA = {
  name: 'BuggyCallDB',
  version: 2,
  stores: {
    notifications: {
      keyPath: 'id',
      autoIncrement: true,
      indexes: {
        timestamp: { unique: false },
        type: { unique: false },
        priority: { unique: false },
        status: { unique: false }
      }
    },
    pendingActions: {
      keyPath: 'id',
      autoIncrement: true,
      indexes: {
        timestamp: { unique: false },
        retries: { unique: false }
      }
    },
    deliveryLog: {
      keyPath: 'id',
      autoIncrement: true,
      indexes: {
        notificationId: { unique: false },
        status: { unique: false },
        timestamp: { unique: false }
      }
    }
  }
};
```

**Offline Queue Logic:**

```javascript
// Store notification when offline
async function queueNotification(notificationData) {
  const db = await openDB();
  const tx = db.transaction(['notifications'], 'readwrite');
  const store = tx.objectStore('notifications');
  
  await store.add({
    ...notificationData,
    status: 'queued',
    queuedAt: Date.now(),
    retries: 0
  });
  
  await tx.complete;
}

// Background sync handler
self.addEventListener('sync', async (event) => {
  if (event.tag === 'sync-notifications') {
    event.waitUntil(syncQueuedNotifications());
  }
});

async function syncQueuedNotifications() {
  const db = await openDB();
  const tx = db.transaction(['notifications'], 'readonly');
  const store = tx.objectStore('notifications');
  const index = store.index('status');
  
  const queued = await index.getAll('queued');
  
  for (const notification of queued) {
    try {
      // Display queued notification
      await self.registration.showNotification(
        notification.title,
        buildNotificationOptions(notification, notification.priority)
      );
      
      // Update status
      await updateNotificationStatus(notification.id, 'delivered');
      
      // Log delivery
      await logDelivery(notification.id, 'success', 'synced');
      
    } catch (error) {
      // Increment retry count
      await incrementRetryCount(notification.id);
      
      // Log failure
      await logDelivery(notification.id, 'failed', error.message);
    }
  }
}
```

### 3. Badge Manager

**Badge Counter Logic:**

```javascript
let badgeCount = 0;

async function updateBadgeCount(delta) {
  badgeCount += delta;
  
  if (badgeCount < 0) badgeCount = 0;
  
  // Update app badge
  if ('setAppBadge' in navigator) {
    if (badgeCount > 0) {
      await navigator.setAppBadge(badgeCount);
    } else {
      await navigator.clearAppBadge();
    }
  }
  
  // Store in IndexedDB for persistence
  await storeBadgeCount(badgeCount);
}

// Clear badge when notification is clicked
self.addEventListener('notificationclick', async (event) => {
  event.notification.close();
  
  // Decrement badge
  await updateBadgeCount(-1);
  
  // Handle action
  if (event.action === 'accept') {
    await handleAcceptAction(event.notification.data);
  } else if (event.action === 'details') {
    await handleDetailsAction(event.notification.data);
  } else {
    await handleDefaultClick(event.notification.data);
  }
});
```

### 4. Enhanced Notification Service (Backend)

**notification_service.py Enhancements:**

```python
class NotificationService:
    
    @staticmethod
    def send_notification_v2(
        subscription_info,
        title,
        body,
        notification_type='general',
        priority='normal',
        data=None,
        image=None,
        actions=None
    ):
        """
        Enhanced notification sending with priority and rich media
        
        Args:
            subscription_info: Web push subscription
            title: Notification title
            body: Notification body
            notification_type: Type (new_request, status_update, etc.)
            priority: Priority level (high, normal, low)
            data: Additional data
            image: Image URL for rich notification
            actions: Custom action buttons
        """
        
        # Build notification payload
        notification_data = {
            "title": title,
            "body": body,
            "icon": "/static/icons/Icon-192.png",
            "badge": "/static/icons/Icon-96.png",
            "type": notification_type,
            "priority": priority,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data or {}
        }
        
        # Add rich media
        if image:
            notification_data["image"] = image
        
        # Add custom actions
        if actions:
            notification_data["actions"] = actions
        
        # Priority-based configuration
        if priority == 'high':
            notification_data["sound"] = "/static/sounds/urgent.mp3"
            notification_data["vibrate"] = [200, 100, 200, 100, 200, 100, 200]
            notification_data["requireInteraction"] = True
        elif priority == 'normal':
            notification_data["sound"] = "/static/sounds/notification.mp3"
            notification_data["vibrate"] = [200, 100, 200]
        else:  # low
            notification_data["sound"] = "/static/sounds/subtle.mp3"
            notification_data["vibrate"] = [100]
        
        try:
            # Send via Web Push
            response = webpush(
                subscription_info=subscription_info,
                data=json.dumps(notification_data),
                vapid_private_key=NotificationService.VAPID_PRIVATE_KEY,
                vapid_claims=NotificationService.VAPID_CLAIMS,
                ttl=86400  # 24 hours TTL
            )
            
            # Log delivery attempt
            NotificationService._log_delivery(
                subscription_info,
                notification_data,
                'sent',
                response.status_code
            )
            
            return True
            
        except WebPushException as e:
            # Handle specific errors
            if e.response and e.response.status_code == 410:
                # Subscription expired - remove it
                NotificationService._remove_expired_subscription(subscription_info)
            
            NotificationService._log_delivery(
                subscription_info,
                notification_data,
                'failed',
                str(e)
            )
            
            return False
    
    @staticmethod
    def notify_new_request_v2(request_obj):
        """Enhanced new request notification with rich media"""
        from app.models.buggy import Buggy
        
        buggies = Buggy.query.filter_by(
            hotel_id=request_obj.hotel_id,
            status='available'
        ).all()
        
        # Build notification content
        room_info = f"Oda {request_obj.room_number}" if request_obj.room_number else "Misafir"
        guest_info = f" - {request_obj.guest_name}" if request_obj.guest_name else ""
        
        # Generate map image (if location has coordinates)
        map_image = None
        if request_obj.location.latitude and request_obj.location.longitude:
            map_image = f"/api/map/thumbnail?lat={request_obj.location.latitude}&lng={request_obj.location.longitude}"
        
        notification_count = 0
        for buggy in buggies:
            if buggy.driver_id:
                driver = SystemUser.query.get(buggy.driver_id)
                if driver and hasattr(driver, 'push_subscription'):
                    success = NotificationService.send_notification_v2(
                        subscription_info=driver.push_subscription,
                        title="🚗 Yeni Buggy Talebi!",
                        body=f"📍 {request_obj.location.name}\n🏨 {room_info}{guest_info}",
                        notification_type='new_request',
                        priority='high',
                        data={
                            'request_id': request_obj.id,
                            'location_id': request_obj.location_id,
                            'url': '/driver/dashboard'
                        },
                        image=map_image,
                        actions=[
                            {'action': 'accept', 'title': '✅ Kabul Et'},
                            {'action': 'details', 'title': '📋 Detaylar'}
                        ]
                    )
                    if success:
                        notification_count += 1
        
        return notification_count
```



### 5. PWA Manifest Enhancements

**manifest.json Updates:**

```json
{
  "name": "Buggy Call",
  "short_name": "BuggyCall",
  "display": "standalone",
  "background_color": "#1BA5A8",
  "theme_color": "#1BA5A8",
  
  "permissions": [
    "notifications",
    "push",
    "background-sync",
    "badge"
  ],
  
  "prefer_related_applications": false,
  
  "protocol_handlers": [
    {
      "protocol": "web+buggycall",
      "url": "/handle?url=%s"
    }
  ],
  
  "share_target": {
    "action": "/share",
    "method": "POST",
    "enctype": "multipart/form-data",
    "params": {
      "title": "title",
      "text": "text",
      "url": "url"
    }
  }
}
```

### 6. Admin Monitoring Dashboard

**Yeni API Endpoints:**

```python
# app/routes/admin_api.py

@admin_api.route('/notifications/stats', methods=['GET'])
@login_required
@admin_required
def get_notification_stats():
    """Get notification delivery statistics"""
    
    # Query delivery logs
    stats = {
        'total_sent': NotificationLog.query.filter_by(status='sent').count(),
        'total_delivered': NotificationLog.query.filter_by(status='delivered').count(),
        'total_failed': NotificationLog.query.filter_by(status='failed').count(),
        'avg_delivery_time': calculate_avg_delivery_time(),
        'by_priority': get_stats_by_priority(),
        'by_type': get_stats_by_type(),
        'recent_failures': get_recent_failures(limit=10)
    }
    
    return jsonify(stats)

@admin_api.route('/notifications/active-subscriptions', methods=['GET'])
@login_required
@admin_required
def get_active_subscriptions():
    """Get list of active push subscriptions"""
    
    users = SystemUser.query.filter(
        SystemUser.push_subscription.isnot(None)
    ).all()
    
    subscriptions = []
    for user in users:
        subscriptions.append({
            'user_id': user.id,
            'username': user.username,
            'role': user.role,
            'subscribed_at': user.push_subscription_date,
            'last_notification': get_last_notification_time(user.id)
        })
    
    return jsonify(subscriptions)
```

## Data Models

### 1. NotificationLog Model (New)

```python
# app/models/notification_log.py

class NotificationLog(db.Model):
    """Log for notification delivery tracking"""
    
    __tablename__ = 'notification_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('system_users.id'), nullable=False)
    notification_type = db.Column(db.String(50), nullable=False)
    priority = db.Column(db.String(20), default='normal')
    title = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text)
    status = db.Column(db.String(20), nullable=False)  # sent, delivered, failed, clicked
    error_message = db.Column(db.Text)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    delivered_at = db.Column(db.DateTime)
    clicked_at = db.Column(db.DateTime)
    
    # Relationships
    user = db.relationship('SystemUser', backref='notification_logs')
    
    def __repr__(self):
        return f'<NotificationLog {self.id}: {self.notification_type} to {self.user_id}>'
```

### 2. SystemUser Model Updates

```python
# app/models/user.py - Add new fields

class SystemUser(db.Model):
    # ... existing fields ...
    
    # Push notification fields
    push_subscription = db.Column(db.JSON)
    push_subscription_date = db.Column(db.DateTime)
    notification_preferences = db.Column(db.JSON, default={
        'enabled': True,
        'sound': True,
        'vibration': True,
        'priority_only': False,
        'quiet_hours': {
            'enabled': False,
            'start': '22:00',
            'end': '08:00'
        }
    })
```

## Error Handling

### 1. Subscription Management

```javascript
// Handle subscription errors
async function handleSubscriptionError(error) {
  console.error('[SW] Subscription error:', error);
  
  if (error.name === 'NotAllowedError') {
    // User denied permission
    await logError('permission_denied', error.message);
    return 'permission_denied';
  }
  
  if (error.name === 'NotSupportedError') {
    // Push not supported
    await logError('not_supported', error.message);
    return 'not_supported';
  }
  
  // Generic error - retry with exponential backoff
  const retryCount = await getRetryCount();
  if (retryCount < 3) {
    const delay = Math.pow(2, retryCount) * 1000;
    setTimeout(() => resubscribe(), delay);
  }
  
  return 'retry_scheduled';
}
```

### 2. Network Error Handling

```javascript
// Graceful degradation for network errors
async function handleNetworkError(error, notificationData) {
  console.error('[SW] Network error:', error);
  
  // Queue for later delivery
  await queueNotification(notificationData);
  
  // Register background sync
  if ('sync' in self.registration) {
    await self.registration.sync.register('sync-notifications');
  }
  
  // Show offline indicator
  await showOfflineNotification();
}
```

### 3. Delivery Failure Recovery

```python
# Backend retry logic
class NotificationService:
    
    @staticmethod
    def retry_failed_notifications():
        """Retry failed notifications with exponential backoff"""
        
        # Get failed notifications from last 24 hours
        failed = NotificationLog.query.filter(
            NotificationLog.status == 'failed',
            NotificationLog.sent_at >= datetime.utcnow() - timedelta(hours=24),
            NotificationLog.retry_count < 3
        ).all()
        
        for log in failed:
            # Calculate backoff delay
            delay = min(300, 30 * (2 ** log.retry_count))  # Max 5 minutes
            
            if (datetime.utcnow() - log.sent_at).seconds >= delay:
                # Retry sending
                user = SystemUser.query.get(log.user_id)
                if user and user.push_subscription:
                    success = NotificationService.send_notification_v2(
                        subscription_info=user.push_subscription,
                        title=log.title,
                        body=log.body,
                        notification_type=log.notification_type,
                        priority=log.priority
                    )
                    
                    if success:
                        log.status = 'sent'
                        log.retry_count += 1
                    else:
                        log.retry_count += 1
                        if log.retry_count >= 3:
                            log.status = 'permanently_failed'
                    
                    db.session.commit()
```

## Testing Strategy

### 1. Unit Tests

```python
# tests/test_notification_service.py

def test_send_high_priority_notification():
    """Test high priority notification sending"""
    service = NotificationService()
    
    result = service.send_notification_v2(
        subscription_info=mock_subscription,
        title="Test",
        body="High priority test",
        priority='high'
    )
    
    assert result == True
    assert mock_subscription.vibrate == [200, 100, 200, 100, 200, 100, 200]

def test_offline_queue():
    """Test offline notification queueing"""
    # Simulate offline state
    with mock_offline():
        result = queue_notification(test_notification)
        assert result == True
    
    # Verify stored in IndexedDB
    queued = get_queued_notifications()
    assert len(queued) == 1
```

### 2. Integration Tests

```javascript
// tests/sw.test.js

describe('Service Worker Push Handling', () => {
  it('should display notification on push event', async () => {
    const pushEvent = new PushEvent('push', {
      data: {
        title: 'Test',
        body: 'Test notification',
        priority: 'high'
      }
    });
    
    await handlePushEvent(pushEvent);
    
    const notifications = await getNotifications();
    expect(notifications.length).toBe(1);
    expect(notifications[0].title).toBe('Test');
  });
  
  it('should queue notification when offline', async () => {
    // Simulate offline
    mockOffline();
    
    const pushEvent = new PushEvent('push', {
      data: testNotification
    });
    
    await handlePushEvent(pushEvent);
    
    const queued = await getQueuedNotifications();
    expect(queued.length).toBe(1);
  });
});
```

### 3. E2E Tests

```python
# tests/e2e/test_push_notifications.py

def test_end_to_end_notification_flow(driver_client, guest_client):
    """Test complete notification flow from request to delivery"""
    
    # 1. Guest creates request
    response = guest_client.post('/api/guest/request', json={
        'location_id': 1,
        'room_number': '101'
    })
    assert response.status_code == 201
    
    # 2. Verify notification sent to driver
    time.sleep(2)  # Wait for async processing
    
    logs = NotificationLog.query.filter_by(
        notification_type='new_request'
    ).all()
    assert len(logs) > 0
    assert logs[0].status == 'sent'
    
    # 3. Simulate driver receiving notification
    # (This would require browser automation)
```



## Performance Optimization

### 1. Battery Efficiency

**Stratejiler:**

```javascript
// Efficient event listeners - passive mode
self.addEventListener('push', (event) => {
  // Process quickly and exit
  event.waitUntil(
    handlePushQuickly(event.data)
      .then(() => {
        // Release resources immediately
        return Promise.resolve();
      })
  );
}, { passive: true });

// Throttle background sync
let lastSyncTime = 0;
const SYNC_THROTTLE = 60000; // 1 minute

self.addEventListener('sync', (event) => {
  const now = Date.now();
  if (now - lastSyncTime < SYNC_THROTTLE) {
    return; // Skip if synced recently
  }
  
  lastSyncTime = now;
  event.waitUntil(syncQueuedNotifications());
});

// Minimize wake locks
async function handlePushQuickly(data) {
  // Process in under 500ms
  const startTime = performance.now();
  
  await Promise.all([
    showNotification(data),
    updateBadge(1),
    logDelivery(data)
  ]);
  
  const duration = performance.now() - startTime;
  console.log(`[Perf] Push handled in ${duration}ms`);
  
  // Ensure we're under budget
  if (duration > 500) {
    console.warn('[Perf] Push handling exceeded 500ms budget');
  }
}
```

### 2. Memory Management

```javascript
// Limit cache size
const MAX_CACHE_SIZE = 50 * 1024 * 1024; // 50MB
const MAX_NOTIFICATIONS_STORED = 100;

async function pruneOldNotifications() {
  const db = await openDB();
  const tx = db.transaction(['notifications'], 'readwrite');
  const store = tx.objectStore('notifications');
  const index = store.index('timestamp');
  
  const all = await index.getAll();
  
  if (all.length > MAX_NOTIFICATIONS_STORED) {
    // Keep only most recent
    const toDelete = all
      .sort((a, b) => a.timestamp - b.timestamp)
      .slice(0, all.length - MAX_NOTIFICATIONS_STORED);
    
    for (const item of toDelete) {
      await store.delete(item.id);
    }
  }
  
  await tx.complete;
}

// Run cleanup periodically
setInterval(pruneOldNotifications, 3600000); // Every hour
```

### 3. Network Optimization

```javascript
// Batch API calls
const pendingLogs = [];
const LOG_BATCH_SIZE = 10;
const LOG_BATCH_INTERVAL = 5000; // 5 seconds

async function logDelivery(notificationData) {
  pendingLogs.push({
    notification_id: notificationData.id,
    status: 'delivered',
    timestamp: Date.now()
  });
  
  if (pendingLogs.length >= LOG_BATCH_SIZE) {
    await flushLogs();
  }
}

async function flushLogs() {
  if (pendingLogs.length === 0) return;
  
  const batch = pendingLogs.splice(0, LOG_BATCH_SIZE);
  
  try {
    await fetch('/api/notifications/log-batch', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ logs: batch })
    });
  } catch (error) {
    // Re-queue on failure
    pendingLogs.unshift(...batch);
  }
}

// Flush periodically
setInterval(flushLogs, LOG_BATCH_INTERVAL);
```

## Security Considerations

### 1. VAPID Key Management

```python
# Secure VAPID key storage
import os
from cryptography.fernet import Fernet

class VAPIDKeyManager:
    
    @staticmethod
    def encrypt_private_key(private_key):
        """Encrypt VAPID private key"""
        encryption_key = os.getenv('ENCRYPTION_KEY')
        f = Fernet(encryption_key)
        return f.encrypt(private_key.encode()).decode()
    
    @staticmethod
    def decrypt_private_key(encrypted_key):
        """Decrypt VAPID private key"""
        encryption_key = os.getenv('ENCRYPTION_KEY')
        f = Fernet(encryption_key)
        return f.decrypt(encrypted_key.encode()).decode()
```

### 2. Subscription Validation

```python
# Validate push subscriptions
def validate_subscription(subscription_info):
    """Validate push subscription structure"""
    
    required_fields = ['endpoint', 'keys']
    if not all(field in subscription_info for field in required_fields):
        raise ValueError('Invalid subscription structure')
    
    required_keys = ['p256dh', 'auth']
    if not all(key in subscription_info['keys'] for key in required_keys):
        raise ValueError('Invalid subscription keys')
    
    # Validate endpoint URL
    if not subscription_info['endpoint'].startswith('https://'):
        raise ValueError('Subscription endpoint must use HTTPS')
    
    return True
```

### 3. Content Security Policy

```python
# CSP headers for notification content
CSP_POLICY = {
    "default-src": ["'self'"],
    "script-src": ["'self'", "'unsafe-inline'"],
    "img-src": ["'self'", "data:", "https:"],
    "connect-src": ["'self'", "wss:", "https:"],
    "worker-src": ["'self'"]
}
```

## Platform-Specific Considerations

### 1. Android (Chrome/Edge)

**Özellikler:**
- ✅ Full push notification support
- ✅ Background sync
- ✅ Badge API
- ✅ Vibration API
- ✅ Lock screen notifications

**Optimizasyonlar:**
```javascript
// Android-specific optimizations
if (isAndroid()) {
  // Use longer vibration patterns
  options.vibrate = [300, 200, 300, 200, 300];
  
  // Enable notification grouping
  options.tag = `buggy-${data.type}`;
  
  // Use high priority for urgent notifications
  if (data.priority === 'high') {
    options.requireInteraction = true;
  }
}
```

### 2. iOS (Safari)

**Özellikler:**
- ✅ Push notifications (iOS 16.4+)
- ⚠️ Requires PWA installation
- ❌ No Vibration API
- ⚠️ Limited background sync

**Optimizasyonlar:**
```javascript
// iOS-specific handling
if (isIOS()) {
  // No vibration support
  delete options.vibrate;
  
  // Ensure PWA is installed
  if (!isPWAInstalled()) {
    showPWAInstallPrompt();
  }
  
  // Use sound for alerts
  options.silent = false;
  options.sound = data.sound;
}
```

### 3. Desktop (Chrome/Firefox/Edge)

**Özellikler:**
- ✅ Full support
- ✅ Rich notifications
- ✅ Action buttons
- ❌ No vibration

**Optimizasyonlar:**
```javascript
// Desktop-specific optimizations
if (isDesktop()) {
  // No vibration
  delete options.vibrate;
  
  // Use larger images
  if (data.image) {
    options.image = data.image;
  }
  
  // More action buttons
  options.actions = [
    { action: 'accept', title: 'Kabul Et' },
    { action: 'details', title: 'Detaylar' },
    { action: 'snooze', title: 'Ertele' }
  ];
}
```

## Monitoring and Analytics

### 1. Delivery Metrics

```python
# Track key metrics
class NotificationMetrics:
    
    @staticmethod
    def get_delivery_rate():
        """Calculate notification delivery rate"""
        total = NotificationLog.query.count()
        delivered = NotificationLog.query.filter_by(status='delivered').count()
        return (delivered / total * 100) if total > 0 else 0
    
    @staticmethod
    def get_avg_delivery_time():
        """Calculate average delivery time"""
        logs = NotificationLog.query.filter(
            NotificationLog.delivered_at.isnot(None)
        ).all()
        
        if not logs:
            return 0
        
        total_time = sum([
            (log.delivered_at - log.sent_at).total_seconds()
            for log in logs
        ])
        
        return total_time / len(logs)
    
    @staticmethod
    def get_click_through_rate():
        """Calculate notification click-through rate"""
        delivered = NotificationLog.query.filter_by(status='delivered').count()
        clicked = NotificationLog.query.filter(
            NotificationLog.clicked_at.isnot(None)
        ).count()
        
        return (clicked / delivered * 100) if delivered > 0 else 0
```

### 2. Error Tracking

```javascript
// Client-side error tracking
async function trackError(errorType, errorMessage, context) {
  try {
    await fetch('/api/notifications/error', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        error_type: errorType,
        error_message: errorMessage,
        context: context,
        user_agent: navigator.userAgent,
        timestamp: Date.now()
      })
    });
  } catch (e) {
    console.error('[Tracking] Failed to log error:', e);
  }
}
```

## Deployment Strategy

### 1. Phased Rollout

**Phase 1: Internal Testing (Week 1)**
- Deploy to staging environment
- Test with internal team
- Monitor metrics and errors

**Phase 2: Beta Testing (Week 2)**
- Deploy to 10% of users
- Collect feedback
- Fix critical issues

**Phase 3: Full Rollout (Week 3)**
- Deploy to all users
- Monitor performance
- Optimize based on real-world data

### 2. Feature Flags

```python
# Feature flag configuration
FEATURE_FLAGS = {
    'advanced_notifications': {
        'enabled': True,
        'rollout_percentage': 100,
        'allowed_roles': ['driver', 'admin']
    },
    'notification_grouping': {
        'enabled': True,
        'rollout_percentage': 50
    },
    'rich_media_notifications': {
        'enabled': False,  # Not yet ready
        'rollout_percentage': 0
    }
}

def is_feature_enabled(feature_name, user=None):
    """Check if feature is enabled for user"""
    flag = FEATURE_FLAGS.get(feature_name)
    if not flag or not flag['enabled']:
        return False
    
    # Check role restrictions
    if user and 'allowed_roles' in flag:
        if user.role not in flag['allowed_roles']:
            return False
    
    # Check rollout percentage
    if user:
        user_hash = hash(user.id) % 100
        return user_hash < flag['rollout_percentage']
    
    return True
```

### 3. Rollback Plan

```bash
# Quick rollback script
#!/bin/bash

echo "Rolling back to previous version..."

# Revert Service Worker
git checkout HEAD~1 -- app/static/sw.js

# Revert notification service
git checkout HEAD~1 -- app/services/notification_service.py

# Restart application
systemctl restart buggycall

echo "Rollback complete"
```

## Documentation and Training

### 1. User Guide

- **Driver Guide**: How to enable notifications, manage preferences
- **Admin Guide**: How to monitor delivery, troubleshoot issues
- **Developer Guide**: API documentation, integration examples

### 2. Troubleshooting Guide

**Common Issues:**

1. **Notifications not appearing**
   - Check browser permissions
   - Verify Service Worker is active
   - Check push subscription status

2. **Notifications delayed**
   - Check network connectivity
   - Verify server is sending notifications
   - Check background sync status

3. **Battery drain**
   - Review notification frequency
   - Check for excessive background sync
   - Optimize Service Worker code

## Success Metrics

### Key Performance Indicators (KPIs)

1. **Delivery Rate**: Target 99.5%
2. **Average Delivery Time**: Target < 2 seconds
3. **Click-Through Rate**: Target > 60%
4. **Battery Impact**: Target < 5% per hour
5. **Error Rate**: Target < 0.5%

### Monitoring Dashboard

```python
# Real-time metrics endpoint
@admin_api.route('/notifications/metrics/realtime', methods=['GET'])
def get_realtime_metrics():
    """Get real-time notification metrics"""
    
    # Last hour stats
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)
    
    metrics = {
        'delivery_rate': NotificationMetrics.get_delivery_rate(),
        'avg_delivery_time': NotificationMetrics.get_avg_delivery_time(),
        'click_through_rate': NotificationMetrics.get_click_through_rate(),
        'notifications_sent_last_hour': NotificationLog.query.filter(
            NotificationLog.sent_at >= one_hour_ago
        ).count(),
        'active_subscriptions': SystemUser.query.filter(
            SystemUser.push_subscription.isnot(None)
        ).count(),
        'error_rate': calculate_error_rate(one_hour_ago)
    }
    
    return jsonify(metrics)
```

## Conclusion

Bu tasarım, BuggyCall uygulamasının push bildirim sistemini mobil ve tablet cihazlar için optimize eder. Sistem:

- ✅ Arka planda ve kilit ekranında güvenilir bildirim teslimatı
- ✅ Offline destek ve background sync
- ✅ Batarya verimli işlem
- ✅ Zengin bildirim içeriği (resim, aksiyon butonları)
- ✅ Kapsamlı monitoring ve analytics
- ✅ Platform-specific optimizasyonlar

Implementasyon, mevcut sisteme minimal değişiklikle entegre edilebilir ve geriye dönük uyumludur.
