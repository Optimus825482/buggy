# Notification Click Handler - Implementation Guide

## Overview

Task 8 implementasyonu: Service Worker notification click handler'ı geliştirilmiş özellikleriyle tamamlandı.

## Implemented Features

### 1. ✅ Enhanced Notification Click Handler

**Location:** `app/static/sw.js` - `notificationclick` event listener

**Features:**
- Notification tıklandığında otomatik kapanma
- Badge count otomatik azaltma
- Click tracking (analytics için)
- Action button handling
- Deep linking ile doğru sayfaya yönlendirme
- Performance monitoring

**Code:**
```javascript
self.addEventListener('notificationclick', async (event) => {
  const startTime = performance.now();
  const action = event.action;
  const notification = event.notification;
  const data = notification.data || {};
  
  // Close notification
  notification.close();
  
  event.waitUntil(
    handleNotificationClickAsync(action, data, startTime)
  );
});
```

### 2. ✅ Action Button Handling

**Location:** `app/static/sw.js` - `handleNotificationAction()`

**Supported Actions:**
- **accept**: Talebi kabul et (offline queueing destekli)
- **details**: Detay sayfasına git
- **view**: Özel URL'ye git
- **default**: Notification body tıklaması

**Deep Linking Examples:**
```javascript
// Accept action
/driver/dashboard?accept=123

// Details action
/driver/request/123

// View action
/driver/messages?id=789

// Type-specific defaults
/driver/dashboard?location=5
/driver/dashboard?filter=completed
```

### 3. ✅ Badge Decrement on Click

**Location:** `app/static/sw.js` - `updateBadgeCount()`

**Features:**
- Her notification click'te badge -1 azalır
- Negatif değerlere düşmez (min: 0)
- IndexedDB'de persist edilir
- Badge API kullanır (fallback destekli)
- Client'lara bildirim gönderir

**Code:**
```javascript
await updateBadgeCount(-1);
```

### 4. ✅ Deep Linking System

**Location:** `app/static/sw.js` - `handleNotificationAction()`

**Notification Type Routing:**

| Type | Default Navigation | With Data |
|------|-------------------|-----------|
| `new_request` | `/driver/dashboard` | `/driver/request/{id}` |
| `status_update` | `/driver/dashboard` | `/driver/request/{id}` |
| `message` | `/driver/messages` | `/driver/messages?id={id}` |
| `buggy_assigned` | `/driver/dashboard` | `/driver/dashboard?buggy={id}` |
| `request_cancelled` | `/driver/dashboard?filter=cancelled` | - |
| `request_completed` | `/driver/dashboard?filter=completed` | `/driver/request/{id}?completed=true` |

### 5. ✅ Click Tracking (Analytics)

**Location:** `app/static/sw.js` - `logNotificationClick()`

**Logged Data:**
```javascript
{
  notification_id: 'notif_123456',
  status: 'clicked',
  action: 'accept', // or 'details', 'view', 'default'
  clicked_at: '2025-11-04T12:34:56.789Z',
  timestamp: 1730728496789
}
```

**Storage:**
- IndexedDB (STORE_DELIVERY_LOG)
- Batch API sync (10 log'da bir flush)

### 6. ✅ Smart Window Management

**Location:** `app/static/sw.js` - `navigateToUrl()`

**Priority System:**
1. **Score 100**: Exact URL match
2. **Score 80**: Same path, different params
3. **Score 60**: Same base path
4. **Score 40**: Same section (/driver/*)
5. **Score 20**: Any app window

**Features:**
- Mevcut window'u focus eder
- Navigation message gönderir
- Yeni window açar (gerekirse)
- Fallback mekanizması

### 7. ✅ Client-Side Navigation Handler

**Location:** `app/static/js/common.js` - `ServiceWorkerHandler`

**Message Types:**
- `NAVIGATE`: Sayfa navigasyonu
- `PLAY_NOTIFICATION_SOUND`: Ses çalma
- `BADGE_UPDATE`: Badge güncelleme
- `NETWORK_STATUS`: Ağ durumu
- `SYNC_COMPLETE`: Senkronizasyon tamamlandı
- `BADGE_FALLBACK`: Badge API fallback

**Code:**
```javascript
ServiceWorkerHandler.handleNavigation({
  url: '/driver/dashboard?accept=123',
  pathname: '/driver/dashboard',
  search: '?accept=123',
  timestamp: Date.now()
});
```

### 8. ✅ Offline Action Queueing

**Location:** `app/static/sw.js` - `queuePendingAction()`

**Features:**
- Offline durumda action'ları kuyruğa alır
- Background sync ile senkronize eder
- Retry logic (max 3 deneme)
- Accept request offline desteği

**Example:**
```javascript
await queuePendingAction({
  type: 'accept_request',
  action: 'accept_request',
  data: { request_id: 123 },
  timestamp: Date.now()
});
```

## Performance Metrics

**Target:** < 1000ms notification click handling

**Measured:**
- Click handle time
- Navigation time
- Badge update time
- Log write time

**Monitoring:**
```javascript
const duration = performance.now() - startTime;
recordPerformanceMetric('click', duration);
```

## Testing

**Test File:** `tests/test_notification_click_handler.py`

**Test Coverage:**
- ✅ Click tracking logging
- ✅ Badge decrement logic
- ✅ Action button handling
- ✅ Deep linking (all types)
- ✅ Offline action queueing
- ✅ Window focus priority
- ✅ Navigation message structure
- ✅ Log batch threshold

**Run Tests:**
```bash
python tests/test_notification_click_handler.py
```

## Requirements Mapping

| Requirement | Implementation | Status |
|-------------|----------------|--------|
| 7.1 - Accept button | `handleNotificationAction()` accept case | ✅ |
| 7.2 - Details button | `handleNotificationAction()` details case | ✅ |
| 7.3 - Accept action | Accept + navigate + offline queue | ✅ |
| 7.4 - Details action | Navigate to request details | ✅ |
| 7.5 - Close notification | `notification.close()` + badge update | ✅ |
| 11.4 - Click tracking | `logNotificationClick()` + IndexedDB | ✅ |

## Usage Examples

### Example 1: New Request Notification Click

```javascript
// User clicks "Kabul Et" button
// Service Worker:
1. Closes notification
2. Decrements badge: 5 → 4
3. Logs click: { action: 'accept', notification_id: 'notif_123' }
4. Checks online status
5. If online: navigates to /driver/dashboard?accept=123
6. If offline: queues action + navigates with offline indicator
```

### Example 2: Details Button Click

```javascript
// User clicks "Detaylar" button
// Service Worker:
1. Closes notification
2. Decrements badge: 3 → 2
3. Logs click: { action: 'details', notification_id: 'notif_456' }
4. Finds best matching window (score-based)
5. Focuses window + sends NAVIGATE message
6. Client navigates to /driver/request/456
```

### Example 3: Default Click (Body)

```javascript
// User clicks notification body
// Service Worker:
1. Closes notification
2. Decrements badge: 2 → 1
3. Logs click: { action: 'default', notification_id: 'notif_789' }
4. Determines navigation based on type
5. For 'new_request': /driver/request/789
6. Opens or focuses appropriate window
```

## Error Handling

**Scenarios:**
1. **Navigation fails**: Fallback to dashboard
2. **Badge API not supported**: Title badge fallback
3. **IndexedDB error**: Continue without logging
4. **Window focus fails**: Open new window
5. **Offline**: Queue action for later sync

## Browser Compatibility

| Feature | Chrome | Firefox | Safari | Edge |
|---------|--------|---------|--------|------|
| Notification Click | ✅ | ✅ | ✅ | ✅ |
| Action Buttons | ✅ | ✅ | ⚠️ iOS | ✅ |
| Badge API | ✅ | ❌ | ⚠️ | ✅ |
| Window Focus | ✅ | ✅ | ✅ | ✅ |
| Deep Linking | ✅ | ✅ | ✅ | ✅ |

## Next Steps

Task 8 tamamlandı! Sıradaki task'lar:
- Task 11: PWA Manifest Enhancements
- Task 13: Admin Monitoring Dashboard
- Task 16: Map Thumbnail Generation
- Task 19: Notification Retry System

## Notes

- Click handler < 1000ms hedefini karşılıyor
- Badge management güvenilir çalışıyor
- Deep linking tüm notification type'ları destekliyor
- Offline action queueing implement edildi
- Performance monitoring aktif
- Error handling comprehensive

---

**Implemented by:** Erkan ERDEM  
**Date:** November 4, 2025  
**Version:** 3.0.0
