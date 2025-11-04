// Service Worker for Buggy Call PWA - Advanced Mobile Push Notifications
// Version 3.0.0 - Enhanced with offline queue, badge management, and performance optimizations
// Powered by Erkan ERDEM

const CACHE_VERSION = 'shuttlecall-v3.0.1';
const STATIC_CACHE = `${CACHE_VERSION}-static`;
const DYNAMIC_CACHE = `${CACHE_VERSION}-dynamic`;
const IMAGE_CACHE = `${CACHE_VERSION}-images`;

// IndexedDB Configuration
const DB_NAME = 'ShuttleCallDB';
const DB_VERSION = 3; // Incremented for DB name change
const STORE_NOTIFICATIONS = 'notifications';
const STORE_PENDING_ACTIONS = 'pendingActions';
const STORE_DELIVERY_LOG = 'deliveryLog';
const STORE_BADGE_COUNT = 'badgeCount';

// Performance Configuration
const MAX_NOTIFICATIONS_STORED = 100;
const LOG_BATCH_SIZE = 10;
const LOG_BATCH_INTERVAL = 5000; // 5 seconds
const SYNC_THROTTLE = 60000; // 1 minute
const PUSH_HANDLE_TARGET = 500; // Target: handle push in < 500ms
const MEMORY_CLEANUP_INTERVAL = 3600000; // 1 hour
const MAX_CACHE_SIZE = 50 * 1024 * 1024; // 50MB

// Global state
let badgeCount = 0;
let pendingLogs = [];
let lastSyncTime = 0;
let isOnline = true;
let networkStatusListeners = [];

// Performance monitoring
const performanceMetrics = {
  pushHandleTimes: [],
  clickHandleTimes: [],
  syncTimes: [],
  cacheHits: 0,
  cacheMisses: 0
};

// Static assets to cache
const STATIC_ASSETS = [
  '/',
  '/static/css/main.css',
  '/static/css/variables.css',
  '/static/js/common.js',
  '/static/manifest.json',
  '/offline.html',
  '/static/icons/Icon-72.png',
  '/static/icons/Icon-96.png',
  '/static/icons/Icon-120.png',
  '/static/icons/Icon-144.png',
  '/static/icons/Icon-152.png',
  '/static/icons/Icon-192.png',
  '/static/icons/Icon-512.png',
  '/static/sounds/urgent.mp3',
  '/static/sounds/notification.mp3',
  '/static/sounds/subtle.mp3'
];

// ============================================================================
// INSTALLATION & ACTIVATION
// ============================================================================

self.addEventListener('install', (event) => {
  console.log('[SW v3.0] Installing Service Worker');
  
  event.waitUntil(
    Promise.all([
      caches.open(STATIC_CACHE).then((cache) => {
        return Promise.allSettled(
          STATIC_ASSETS.map((url) => {
            return cache.add(url).catch((err) => {
              console.warn(`[SW] Failed to cache: ${url}`, err.message);
              return null;
            });
          })
        );
      }),
      initializeDatabase()
    ]).then(() => {
      console.log('[SW v3.0] Installation complete');
      return self.skipWaiting();
    })
  );
});

self.addEventListener('activate', (event) => {
  console.log('[SW v3.0] Activating Service Worker');
  
  event.waitUntil(
    Promise.all([
      // Clean up old caches
      caches.keys().then((cacheNames) => {
        return Promise.all(
          cacheNames.map((cacheName) => {
            if (!cacheName.startsWith(CACHE_VERSION)) {
              console.log(`[SW] Deleting old cache: ${cacheName}`);
              return caches.delete(cacheName);
            }
          })
        );
      }),
      // Clean up old database (BuggyCallDB)
      new Promise((resolve) => {
        try {
          const deleteRequest = indexedDB.deleteDatabase('BuggyCallDB');
          deleteRequest.onsuccess = () => {
            console.log('[SW] Old database (BuggyCallDB) deleted successfully');
            resolve();
          };
          deleteRequest.onerror = () => {
            console.warn('[SW] Failed to delete old database');
            resolve(); // Continue anyway
          };
        } catch (error) {
          console.warn('[SW] Error deleting old database:', error);
          resolve(); // Continue anyway
        }
      }),
      // Load badge count from storage
      loadBadgeCount()
    ]).then(() => {
      console.log('[SW v3.0] Activation complete');
      return self.clients.claim();
    })
  );
});

// ============================================================================
// PUSH NOTIFICATION HANDLER (ENHANCED)
// ============================================================================

self.addEventListener('push', (event) => {
  console.log('[SW] Push notification received');
  
  if (!event.data) {
    console.log('[SW] Push event but no data');
    return;
  }
  
  const startTime = performance.now();
  const data = event.data.json();
  const priority = data.priority || 'normal';
  
  event.waitUntil(
    handlePushQuickly(data, priority, startTime)
  );
});

async function handlePushQuickly(data, priority, startTime) {
  try {
    // Check network status
    const online = checkOnlineStatus();
    
    // Build notification options
    const options = buildNotificationOptions(data, priority);
    
    if (online) {
      // Online: Normal processing
      await Promise.all([
        // Display notification
        self.registration.showNotification(data.title, options),
        
        // Update badge
        updateBadgeCount(1),
        
        // Play sound (via client message)
        playPrioritySound(data.sound || options.sound),
        
        // Store notification
        storeNotification(data),
        
        // Log delivery
        logNotificationDelivery(data, 'delivered')
      ]);
    } else {
      // Offline: Queue for later
      console.log('[SW] Device offline, queueing notification');
      
      await Promise.all([
        // Queue notification
        queueNotification(data),
        
        // Still show notification locally
        self.registration.showNotification(data.title, options),
        
        // Update badge
        updateBadgeCount(1),
        
        // Store notification
        storeNotification(data)
      ]);
    }
    
    const duration = performance.now() - startTime;
    console.log(`[Perf] Push handled in ${duration.toFixed(2)}ms`);
    
    // Record performance metric
    recordPerformanceMetric('push', duration);
    
    if (duration > PUSH_HANDLE_TARGET) {
      console.warn(`[Perf] Push handling exceeded ${PUSH_HANDLE_TARGET}ms budget`);
    }
  } catch (error) {
    console.error('[SW] Error handling push:', error);
    
    // Try to queue on error
    try {
      await queueNotification(data);
      console.log('[SW] Notification queued after error');
    } catch (queueError) {
      console.error('[SW] Failed to queue notification:', queueError);
    }
    
    await logNotificationDelivery(data, 'failed', error.message);
  }
}

function buildNotificationOptions(data, priority) {
  const options = {
    body: data.body,
    icon: data.icon || '/static/icons/Icon-192.png',
    badge: data.badge || '/static/icons/Icon-96.png',
    tag: data.tag || `buggy-${data.type}`,
    renotify: true,
    requireInteraction: priority === 'high',
    silent: false,
    vibrate: getVibrationPattern(priority),
    actions: buildActionButtons(data),
    data: {
      ...data.data,
      timestamp: Date.now(),
      priority: priority,
      notificationId: generateNotificationId()
    },
    dir: 'ltr',
    lang: 'tr'
  };
  
  // Add image if provided
  if (data.image) {
    options.image = data.image;
  }
  
  return options;
}

function getVibrationPattern(priority) {
  const patterns = {
    'high': [200, 100, 200, 100, 200, 100, 200],
    'normal': [200, 100, 200],
    'low': [100]
  };
  return patterns[priority] || patterns.normal;
}

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

// ============================================================================
// NOTIFICATION CLICK HANDLER (ENHANCED)
// ============================================================================

/**
 * Enhanced notification click handler
 * Handles action buttons, badge updates, click tracking, and deep linking
 */
self.addEventListener('notificationclick', async (event) => {
  const startTime = performance.now();
  const action = event.action;
  const notification = event.notification;
  const data = notification.data || {};
  
  console.log('[SW] Notification clicked:', {
    action: action || 'default',
    notificationId: data.notificationId,
    type: data.type
  });
  
  // Close notification immediately
  notification.close();
  
  event.waitUntil(
    handleNotificationClickAsync(action, data, startTime)
  );
});

/**
 * Async handler for notification click processing
 * @param {string} action - Action button clicked (or undefined for default)
 * @param {Object} data - Notification data
 * @param {number} startTime - Performance timestamp
 */
async function handleNotificationClickAsync(action, data, startTime) {
  try {
    // 1. Decrement badge count
    await updateBadgeCount(-1);
    console.log('[SW] Badge decremented after notification click');
    
    // 2. Log click event for analytics
    if (data.notificationId) {
      await logNotificationClick(data.notificationId, action);
      console.log('[SW] Click logged:', data.notificationId);
    }
    
    // 3. Handle specific action
    const result = await handleNotificationAction(action, data);
    
    // 4. Navigate to appropriate page
    await navigateToUrl(result.url, result.focusExisting);
    
    // 5. Performance tracking
    const duration = performance.now() - startTime;
    console.log(`[Perf] Notification click handled in ${duration.toFixed(2)}ms`);
    
    // Record performance metric
    recordPerformanceMetric('click', duration);
    
    if (duration > 1000) {
      console.warn('[Perf] Notification click handling exceeded 1s');
    }
    
  } catch (error) {
    console.error('[SW] Error handling notification click:', error);
    
    // Fallback: try to open dashboard
    try {
      await navigateToUrl('/driver/dashboard', true);
    } catch (fallbackError) {
      console.error('[SW] Fallback navigation also failed:', fallbackError);
    }
  }
}

/**
 * Handle notification action and return navigation info
 * @param {string} action - Action button clicked
 * @param {Object} data - Notification data
 * @returns {Promise<Object>} Navigation info {url, focusExisting}
 */
async function handleNotificationAction(action, data) {
  const type = data.type || 'general';
  
  console.log('[SW] Handling notification action:', {
    action: action || 'default',
    type,
    hasRequestId: !!data.request_id,
    hasUrl: !!data.url
  });
  
  // Handle 'accept' action
  if (action === 'accept') {
    console.log('[SW] Accept action triggered for request:', data.request_id);
    
    if (type === 'new_request' && data.request_id) {
      // Queue accept action if offline
      if (!checkOnlineStatus()) {
        await queuePendingAction({
          type: 'accept_request',
          action: 'accept_request',
          data: { request_id: data.request_id },
          timestamp: Date.now()
        });
        console.log('[SW] Accept action queued for offline sync');
        
        // Return to dashboard with offline indicator
        return {
          url: `/driver/dashboard?offline=true&queued_accept=${data.request_id}`,
          focusExisting: true
        };
      }
      
      // Online: Navigate with accept parameter
      return {
        url: `/driver/dashboard?accept=${data.request_id}`,
        focusExisting: true
      };
    }
    
    console.warn('[SW] Accept action without valid request_id');
    return {
      url: '/driver/dashboard',
      focusExisting: true
    };
  }
  
  // Handle 'details' action
  if (action === 'details') {
    console.log('[SW] Details action triggered for request:', data.request_id);
    
    if (data.request_id) {
      return {
        url: `/driver/request/${data.request_id}`,
        focusExisting: true
      };
    }
    
    if (data.location_id) {
      return {
        url: `/driver/dashboard?location=${data.location_id}`,
        focusExisting: true
      };
    }
    
    console.warn('[SW] Details action without valid identifiers');
    return {
      url: '/driver/dashboard',
      focusExisting: true
    };
  }
  
  // Handle 'view' action
  if (action === 'view') {
    console.log('[SW] View action triggered');
    
    if (data.url) {
      return {
        url: data.url,
        focusExisting: true
      };
    }
    
    if (data.request_id) {
      return {
        url: `/driver/request/${data.request_id}`,
        focusExisting: true
      };
    }
    
    console.warn('[SW] View action without valid URL');
    return {
      url: '/driver/dashboard',
      focusExisting: true
    };
  }
  
  // Default action (notification body clicked)
  console.log('[SW] Default click action - determining navigation based on type');
  
  // Type-specific default navigation with deep linking
  switch (type) {
    case 'new_request':
      if (data.request_id) {
        return {
          url: `/driver/request/${data.request_id}`,
          focusExisting: true
        };
      }
      if (data.location_id) {
        return {
          url: `/driver/dashboard?location=${data.location_id}`,
          focusExisting: true
        };
      }
      return {
        url: '/driver/dashboard',
        focusExisting: true
      };
      
    case 'status_update':
      if (data.request_id) {
        return {
          url: `/driver/request/${data.request_id}`,
          focusExisting: true
        };
      }
      return {
        url: '/driver/dashboard',
        focusExisting: true
      };
      
    case 'message':
      if (data.message_id) {
        return {
          url: `/driver/messages?id=${data.message_id}`,
          focusExisting: true
        };
      }
      return {
        url: data.url || '/driver/messages',
        focusExisting: true
      };
      
    case 'buggy_assigned':
      if (data.buggy_id) {
        return {
          url: `/driver/dashboard?buggy=${data.buggy_id}`,
          focusExisting: true
        };
      }
      return {
        url: '/driver/dashboard',
        focusExisting: true
      };
      
    case 'request_cancelled':
      return {
        url: '/driver/dashboard?filter=cancelled',
        focusExisting: true
      };
      
    case 'request_completed':
      if (data.request_id) {
        return {
          url: `/driver/request/${data.request_id}?completed=true`,
          focusExisting: true
        };
      }
      return {
        url: '/driver/dashboard?filter=completed',
        focusExisting: true
      };
      
    default:
      // Fallback to provided URL or dashboard
      return {
        url: data.url || '/driver/dashboard',
        focusExisting: true
      };
  }
}

/**
 * Navigate to URL with smart window management and deep linking
 * @param {string} url - URL to navigate to
 * @param {boolean} focusExisting - Try to focus existing window
 */
async function navigateToUrl(url, focusExisting = true) {
  console.log('[SW] Navigating to:', url);
  
  // Parse URL for better matching
  const targetUrl = new URL(url, self.location.origin);
  const targetPath = targetUrl.pathname;
  const targetParams = targetUrl.searchParams;
  
  const clientList = await clients.matchAll({
    type: 'window',
    includeUncontrolled: true
  });
  
  console.log(`[SW] Found ${clientList.length} open window(s)`);
  
  // Try to focus existing window if requested
  if (focusExisting && clientList.length > 0) {
    // Find best matching client with priority system
    let targetClient = null;
    let matchScore = 0;
    
    for (const client of clientList) {
      try {
        const clientUrl = new URL(client.url);
        const clientPath = clientUrl.pathname;
        let score = 0;
        
        // Priority 1: Exact URL match (highest score)
        if (client.url === targetUrl.href) {
          score = 100;
        }
        // Priority 2: Same path with different params
        else if (clientPath === targetPath) {
          score = 80;
        }
        // Priority 3: Same base path (e.g., /driver/request/123 vs /driver/request/456)
        else if (clientPath.startsWith(targetPath.split('/').slice(0, 3).join('/'))) {
          score = 60;
        }
        // Priority 4: Same section (e.g., both /driver/*)
        else if (clientPath.startsWith('/' + targetPath.split('/')[1])) {
          score = 40;
        }
        // Priority 5: Any app window
        else if (clientPath !== '/') {
          score = 20;
        }
        
        // Update best match
        if (score > matchScore) {
          matchScore = score;
          targetClient = client;
        }
      } catch (error) {
        console.warn('[SW] Error parsing client URL:', error);
      }
    }
    
    // Focus and navigate existing client
    if (targetClient && 'focus' in targetClient) {
      try {
        console.log(`[SW] Found matching window (score: ${matchScore}), focusing...`);
        
        // Focus the window
        await targetClient.focus();
        
        // Send navigation message with full URL
        targetClient.postMessage({
          type: 'NAVIGATE',
          url: targetUrl.href,
          pathname: targetPath,
          search: targetUrl.search,
          hash: targetUrl.hash,
          timestamp: Date.now()
        });
        
        console.log('[SW] Focused existing window and sent navigation message');
        
        // Wait a bit to ensure navigation happens
        await new Promise(resolve => setTimeout(resolve, 100));
        
        return targetClient;
      } catch (error) {
        console.warn('[SW] Failed to focus existing window:', error);
        // Continue to open new window
      }
    } else {
      console.log('[SW] No suitable window found for focusing');
    }
  }
  
  // Open new window
  if (clients.openWindow) {
    try {
      console.log('[SW] Opening new window for:', targetUrl.href);
      const newClient = await clients.openWindow(targetUrl.href);
      
      if (newClient) {
        console.log('[SW] New window opened successfully');
        return newClient;
      } else {
        console.warn('[SW] openWindow returned null');
        throw new Error('Failed to open new window');
      }
    } catch (error) {
      console.error('[SW] Failed to open new window:', error);
      
      // Last resort: try to open without full URL
      try {
        const fallbackClient = await clients.openWindow(url);
        console.log('[SW] Fallback window opened');
        return fallbackClient;
      } catch (fallbackError) {
        console.error('[SW] Fallback also failed:', fallbackError);
        throw error;
      }
    }
  } else {
    console.error('[SW] openWindow not supported in this browser');
    throw new Error('openWindow not supported');
  }
}

/**
 * Log notification click for analytics
 * @param {string} notificationId - Notification ID
 * @param {string} action - Action clicked (or undefined for default)
 */
async function logNotificationClick(notificationId, action = 'default') {
  const logEntry = {
    notification_id: notificationId,
    notificationId: notificationId,
    status: 'clicked',
    action: action,
    clicked_at: new Date().toISOString(),
    timestamp: Date.now()
  };
  
  console.log('[SW] Logging notification click:', {
    notificationId,
    action,
    timestamp: logEntry.timestamp
  });
  
  // Store in delivery log
  try {
    const db = await openDB();
    const tx = db.transaction([STORE_DELIVERY_LOG], 'readwrite');
    const store = tx.objectStore(STORE_DELIVERY_LOG);
    await promisifyRequest(store.add(logEntry));
    console.log('[SW] Click logged to IndexedDB successfully');
  } catch (error) {
    console.error('[SW] Error storing click log to IndexedDB:', error);
  }
  
  // Queue for batch API sync
  pendingLogs.push(logEntry);
  console.log(`[SW] Click log queued for batch sync (${pendingLogs.length}/${LOG_BATCH_SIZE})`);
  
  if (pendingLogs.length >= LOG_BATCH_SIZE) {
    await flushLogs();
  }
}

// ============================================================================
// BADGE MANAGER
// ============================================================================

/**
 * Update badge count with delta (increment/decrement)
 * @param {number} delta - Amount to change badge count (positive or negative)
 * @returns {Promise<number>} Updated badge count
 */
async function updateBadgeCount(delta) {
  try {
    // Update count
    badgeCount += delta;
    
    // Ensure non-negative
    if (badgeCount < 0) {
      console.warn('[SW] Badge count went negative, resetting to 0');
      badgeCount = 0;
    }
    
    // Cap at reasonable maximum
    if (badgeCount > 99) {
      console.warn('[SW] Badge count exceeds 99, capping');
      badgeCount = 99;
    }
    
    console.log(`[SW] Badge count updated: ${badgeCount} (delta: ${delta})`);
    
    // Update app badge using Badge API
    await setAppBadge(badgeCount);
    
    // Store in IndexedDB for persistence
    await storeBadgeCount(badgeCount);
    
    // Notify clients about badge update
    await notifyClients({
      type: 'BADGE_UPDATE',
      count: badgeCount
    });
    
    return badgeCount;
  } catch (error) {
    console.error('[SW] Error updating badge count:', error);
    return badgeCount;
  }
}

/**
 * Set badge to specific count
 * @param {number} count - Exact badge count to set
 * @returns {Promise<number>} Updated badge count
 */
async function setBadgeCount(count) {
  try {
    badgeCount = Math.max(0, Math.min(99, count));
    
    console.log(`[SW] Badge count set to: ${badgeCount}`);
    
    await setAppBadge(badgeCount);
    await storeBadgeCount(badgeCount);
    
    await notifyClients({
      type: 'BADGE_UPDATE',
      count: badgeCount
    });
    
    return badgeCount;
  } catch (error) {
    console.error('[SW] Error setting badge count:', error);
    return badgeCount;
  }
}

/**
 * Reset badge count to zero
 * @returns {Promise<number>} Updated badge count (0)
 */
async function resetBadgeCount() {
  console.log('[SW] Resetting badge count to 0');
  return await setBadgeCount(0);
}

/**
 * Get current badge count
 * @returns {number} Current badge count
 */
function getBadgeCount() {
  return badgeCount;
}

/**
 * Set app badge using Badge API with fallback
 * @param {number} count - Badge count to display
 */
async function setAppBadge(count) {
  // Check if Badge API is supported
  if (!('setAppBadge' in navigator)) {
    console.warn('[SW] Badge API not supported on this platform');
    return;
  }
  
  try {
    if (count > 0) {
      await navigator.setAppBadge(count);
      console.log(`[SW] App badge set to: ${count}`);
    } else {
      await navigator.clearAppBadge();
      console.log('[SW] App badge cleared');
    }
  } catch (error) {
    console.error('[SW] Error setting app badge:', error);
    
    // Fallback: Try to use title badge (for some browsers)
    try {
      const clients = await self.clients.matchAll({ type: 'window' });
      for (const client of clients) {
        client.postMessage({
          type: 'BADGE_FALLBACK',
          count: count
        });
      }
    } catch (fallbackError) {
      console.error('[SW] Badge fallback also failed:', fallbackError);
    }
  }
}

/**
 * Load badge count from IndexedDB on startup
 * @returns {Promise<number>} Loaded badge count
 */
async function loadBadgeCount() {
  try {
    const db = await openDB();
    const tx = db.transaction([STORE_BADGE_COUNT], 'readonly');
    const store = tx.objectStore(STORE_BADGE_COUNT);
    const result = await promisifyRequest(store.get('count'));
    
    if (result && typeof result.value === 'number') {
      badgeCount = Math.max(0, Math.min(99, result.value));
      console.log(`[SW] Badge count loaded from storage: ${badgeCount}`);
      
      // Restore badge on app icon
      if (badgeCount > 0) {
        await setAppBadge(badgeCount);
      }
    } else {
      console.log('[SW] No stored badge count found, starting at 0');
      badgeCount = 0;
    }
    
    return badgeCount;
  } catch (error) {
    console.error('[SW] Error loading badge count:', error);
    badgeCount = 0;
    return 0;
  }
}

/**
 * Store badge count to IndexedDB for persistence
 * @param {number} count - Badge count to store
 */
async function storeBadgeCount(count) {
  try {
    const db = await openDB();
    const tx = db.transaction([STORE_BADGE_COUNT], 'readwrite');
    const store = tx.objectStore(STORE_BADGE_COUNT);
    await promisifyRequest(store.put({ id: 'count', value: count, updatedAt: Date.now() }));
    console.log(`[SW] Badge count stored: ${count}`);
  } catch (error) {
    console.error('[SW] Error storing badge count:', error);
  }
}

/**
 * Store badge count to IndexedDB for persistence
 * @param {number} count - Badge count to store
 */
async function storeBadgeCount(count) {
  try {
    const db = await openDB();
    const tx = db.transaction([STORE_BADGE_COUNT], 'readwrite');
    const store = tx.objectStore(STORE_BADGE_COUNT);
    await promisifyRequest(store.put({ id: 'count', value: count, updatedAt: Date.now() }));
    console.log(`[SW] Badge count stored: ${count}`);
  } catch (error) {
    console.error('[SW] Error storing badge count:', error);
  }
}

// ============================================================================
// OFFLINE QUEUE MANAGER
// ============================================================================

/**
 * Store notification for offline access
 * @param {Object} notificationData - Notification data to store
 */
async function storeNotification(notificationData) {
  try {
    const db = await openDB();
    const tx = db.transaction([STORE_NOTIFICATIONS], 'readwrite');
    const store = tx.objectStore(STORE_NOTIFICATIONS);
    
    await promisifyRequest(store.add({
      ...notificationData,
      status: 'stored',
      storedAt: Date.now(),
      retries: 0
    }));
    
    // Prune old notifications
    await pruneOldNotifications();
  } catch (error) {
    console.error('[SW] Error storing notification:', error);
  }
}

/**
 * Queue notification for later delivery when offline
 * @param {Object} notificationData - Notification data to queue
 * @returns {Promise<boolean>} Success status
 */
async function queueNotification(notificationData) {
  try {
    const db = await openDB();
    const tx = db.transaction([STORE_NOTIFICATIONS], 'readwrite');
    const store = tx.objectStore(STORE_NOTIFICATIONS);
    
    const queuedData = {
      ...notificationData,
      status: 'queued',
      queuedAt: Date.now(),
      retries: 0,
      notificationId: notificationData.notificationId || generateNotificationId()
    };
    
    await promisifyRequest(store.add(queuedData));
    
    console.log('[SW] Notification queued for offline delivery:', queuedData.notificationId);
    
    // Register background sync if supported
    if ('sync' in self.registration) {
      try {
        await self.registration.sync.register('sync-notifications');
        console.log('[SW] Background sync registered');
      } catch (error) {
        console.warn('[SW] Background sync registration failed:', error);
      }
    }
    
    return true;
  } catch (error) {
    console.error('[SW] Error queueing notification:', error);
    return false;
  }
}

/**
 * Get all queued notifications
 * @returns {Promise<Array>} Array of queued notifications
 */
async function getQueuedNotifications() {
  try {
    const db = await openDB();
    const tx = db.transaction([STORE_NOTIFICATIONS], 'readonly');
    const store = tx.objectStore(STORE_NOTIFICATIONS);
    const index = store.index('status');
    
    const queued = await promisifyRequest(index.getAll('queued'));
    return queued || [];
  } catch (error) {
    console.error('[SW] Error getting queued notifications:', error);
    return [];
  }
}

/**
 * Queue pending action for later execution
 * @param {Object} actionData - Action data to queue
 * @returns {Promise<boolean>} Success status
 */
async function queuePendingAction(actionData) {
  try {
    const db = await openDB();
    const tx = db.transaction([STORE_PENDING_ACTIONS], 'readwrite');
    const store = tx.objectStore(STORE_PENDING_ACTIONS);
    
    await promisifyRequest(store.add({
      ...actionData,
      queuedAt: Date.now(),
      retries: 0
    }));
    
    console.log('[SW] Action queued:', actionData.action);
    
    // Register background sync
    if ('sync' in self.registration) {
      await self.registration.sync.register('sync-actions');
    }
    
    return true;
  } catch (error) {
    console.error('[SW] Error queueing action:', error);
    return false;
  }
}

// ============================================================================
// BACKGROUND SYNC
// ============================================================================

/**
 * Background sync event handler
 * Syncs queued notifications and actions when connection is restored
 */
self.addEventListener('sync', (event) => {
  const now = Date.now();
  
  console.log('[SW] Background sync triggered:', event.tag);
  
  if (event.tag === 'sync-notifications') {
    // Throttle notification sync
    if (now - lastSyncTime < SYNC_THROTTLE) {
      console.log('[SW] Notification sync throttled');
      return;
    }
    lastSyncTime = now;
    
    event.waitUntil(syncQueuedNotifications());
  } else if (event.tag === 'sync-actions') {
    event.waitUntil(syncPendingActions());
  }
});

/**
 * Sync all queued notifications
 * @returns {Promise<Object>} Sync results
 */
async function syncQueuedNotifications() {
  console.log('[SW] Starting notification sync...');
  
  const results = {
    total: 0,
    delivered: 0,
    failed: 0
  };
  
  try {
    const queued = await getQueuedNotifications();
    results.total = queued.length;
    
    console.log(`[SW] Syncing ${queued.length} queued notifications`);
    
    for (const notification of queued) {
      try {
        // Check retry limit
        if (notification.retries >= 3) {
          console.warn('[SW] Max retries reached for notification:', notification.id);
          await updateNotificationStatus(notification.id, 'permanently_failed');
          results.failed++;
          continue;
        }
        
        // Display queued notification
        const options = buildNotificationOptions(notification, notification.priority || 'normal');
        await self.registration.showNotification(notification.title, options);
        
        // Update badge
        await updateBadgeCount(1);
        
        // Update status
        await updateNotificationStatus(notification.id, 'delivered');
        
        // Log delivery
        await logNotificationDelivery(notification, 'delivered', 'synced');
        
        results.delivered++;
        console.log('[SW] Notification synced successfully:', notification.id);
        
      } catch (error) {
        console.error('[SW] Error syncing notification:', error);
        
        // Increment retry count
        await incrementRetryCount(notification.id);
        
        // Log failure
        await logNotificationDelivery(notification, 'failed', error.message);
        
        results.failed++;
      }
    }
    
    console.log('[SW] Notification sync complete:', results);
    
    // Notify clients about sync completion
    await notifyClients({
      type: 'SYNC_COMPLETE',
      results: results
    });
    
  } catch (error) {
    console.error('[SW] Error in notification sync:', error);
  }
  
  return results;
}

/**
 * Sync pending actions
 * @returns {Promise<Object>} Sync results
 */
async function syncPendingActions() {
  console.log('[SW] Starting action sync...');
  
  const results = {
    total: 0,
    synced: 0,
    failed: 0
  };
  
  try {
    const db = await openDB();
    const tx = db.transaction([STORE_PENDING_ACTIONS], 'readonly');
    const store = tx.objectStore(STORE_PENDING_ACTIONS);
    
    const pending = await promisifyRequest(store.getAll());
    results.total = pending.length;
    
    console.log(`[SW] Syncing ${pending.length} pending actions`);
    
    for (const action of pending) {
      try {
        // Execute action
        await executeAction(action);
        
        // Remove from queue
        await removePendingAction(action.id);
        
        results.synced++;
      } catch (error) {
        console.error('[SW] Error syncing action:', error);
        
        // Increment retry count
        await incrementActionRetryCount(action.id);
        
        results.failed++;
      }
    }
    
    console.log('[SW] Action sync complete:', results);
    
  } catch (error) {
    console.error('[SW] Error in action sync:', error);
  }
  
  return results;
}

/**
 * Execute a pending action
 * @param {Object} action - Action to execute
 */
async function executeAction(action) {
  const { type, data } = action;
  
  switch (type) {
    case 'accept_request':
      await fetch('/api/driver/accept-request', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ request_id: data.request_id })
      });
      break;
      
    case 'update_status':
      await fetch('/api/driver/update-status', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
      break;
      
    default:
      console.warn('[SW] Unknown action type:', type);
  }
}

/**
 * Remove pending action from queue
 * @param {number} id - Action ID
 */
async function removePendingAction(id) {
  try {
    const db = await openDB();
    const tx = db.transaction([STORE_PENDING_ACTIONS], 'readwrite');
    const store = tx.objectStore(STORE_PENDING_ACTIONS);
    await promisifyRequest(store.delete(id));
  } catch (error) {
    console.error('[SW] Error removing pending action:', error);
  }
}

/**
 * Increment action retry count
 * @param {number} id - Action ID
 */
async function incrementActionRetryCount(id) {
  try {
    const db = await openDB();
    const tx = db.transaction([STORE_PENDING_ACTIONS], 'readwrite');
    const store = tx.objectStore(STORE_PENDING_ACTIONS);
    
    const action = await promisifyRequest(store.get(id));
    if (action) {
      action.retries = (action.retries || 0) + 1;
      await promisifyRequest(store.put(action));
    }
  } catch (error) {
    console.error('[SW] Error incrementing action retry count:', error);
  }
}

async function updateNotificationStatus(id, status) {
  try {
    const db = await openDB();
    const tx = db.transaction([STORE_NOTIFICATIONS], 'readwrite');
    const store = tx.objectStore(STORE_NOTIFICATIONS);
    
    const notification = await promisifyRequest(store.get(id));
    if (notification) {
      notification.status = status;
      await promisifyRequest(store.put(notification));
    }
  } catch (error) {
    console.error('[SW] Error updating notification status:', error);
  }
}

async function incrementRetryCount(id) {
  try {
    const db = await openDB();
    const tx = db.transaction([STORE_NOTIFICATIONS], 'readwrite');
    const store = tx.objectStore(STORE_NOTIFICATIONS);
    
    const notification = await promisifyRequest(store.get(id));
    if (notification) {
      notification.retries = (notification.retries || 0) + 1;
      await promisifyRequest(store.put(notification));
    }
  } catch (error) {
    console.error('[SW] Error incrementing retry count:', error);
  }
}

// ============================================================================
// PERFORMANCE OPTIMIZATIONS
// ============================================================================

async function pruneOldNotifications() {
  try {
    const db = await openDB();
    const tx = db.transaction([STORE_NOTIFICATIONS], 'readwrite');
    const store = tx.objectStore(STORE_NOTIFICATIONS);
    const index = store.index('timestamp');
    
    const all = await promisifyRequest(index.getAll());
    
    if (all.length > MAX_NOTIFICATIONS_STORED) {
      // Sort by timestamp and delete oldest
      const sorted = all.sort((a, b) => (a.timestamp || 0) - (b.timestamp || 0));
      const toDelete = sorted.slice(0, all.length - MAX_NOTIFICATIONS_STORED);
      
      for (const item of toDelete) {
        await promisifyRequest(store.delete(item.id));
      }
      
      console.log(`[SW] Pruned ${toDelete.length} old notifications`);
    }
  } catch (error) {
    console.error('[SW] Error pruning notifications:', error);
  }
}

// Run cleanup periodically (every hour)
setInterval(pruneOldNotifications, 3600000);

// ============================================================================
// LOGGING & ANALYTICS
// ============================================================================

async function logNotificationDelivery(data, status, errorMessage = null) {
  const logEntry = {
    notification_id: data.notificationId || generateNotificationId(),
    notificationId: data.notificationId || generateNotificationId(),
    status: status,
    timestamp: Date.now(),
    error_message: errorMessage
  };
  
  // Store in delivery log
  try {
    const db = await openDB();
    const tx = db.transaction([STORE_DELIVERY_LOG], 'readwrite');
    const store = tx.objectStore(STORE_DELIVERY_LOG);
    await promisifyRequest(store.add(logEntry));
  } catch (error) {
    console.error('[SW] Error storing delivery log:', error);
  }
  
  // Also queue for batch API sync
  pendingLogs.push(logEntry);
  
  if (pendingLogs.length >= LOG_BATCH_SIZE) {
    await flushLogs();
  }
}

async function logNotificationClick(notificationId) {
  const logEntry = {
    notification_id: notificationId,
    status: 'clicked',
    timestamp: Date.now()
  };
  
  pendingLogs.push(logEntry);
  
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
    
    console.log(`[SW] Flushed ${batch.length} log entries`);
  } catch (error) {
    // Re-queue on failure
    pendingLogs.unshift(...batch);
    console.error('[SW] Error flushing logs:', error);
  }
}

// Flush logs periodically
setInterval(flushLogs, LOG_BATCH_INTERVAL);

// ============================================================================
// SOUND PLAYBACK
// ============================================================================

async function playPrioritySound(soundUrl) {
  if (!soundUrl) return;
  
  try {
    const clients = await self.clients.matchAll({ type: 'window', includeUncontrolled: true });
    
    for (const client of clients) {
      client.postMessage({
        type: 'PLAY_NOTIFICATION_SOUND',
        soundUrl: soundUrl
      });
    }
    
    console.log('[SW] Sound message sent to clients');
  } catch (error) {
    console.error('[SW] Error playing sound:', error);
  }
}

// ============================================================================
// INDEXEDDB HELPERS
// ============================================================================

async function initializeDatabase() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);
    
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);
    
    request.onupgradeneeded = (event) => {
      const db = event.target.result;
      
      // Notifications store
      if (!db.objectStoreNames.contains(STORE_NOTIFICATIONS)) {
        const store = db.createObjectStore(STORE_NOTIFICATIONS, {
          keyPath: 'id',
          autoIncrement: true
        });
        store.createIndex('timestamp', 'timestamp', { unique: false });
        store.createIndex('type', 'type', { unique: false });
        store.createIndex('priority', 'priority', { unique: false });
        store.createIndex('status', 'status', { unique: false });
      }
      
      // Pending actions store
      if (!db.objectStoreNames.contains(STORE_PENDING_ACTIONS)) {
        const store = db.createObjectStore(STORE_PENDING_ACTIONS, {
          keyPath: 'id',
          autoIncrement: true
        });
        store.createIndex('timestamp', 'timestamp', { unique: false });
        store.createIndex('retries', 'retries', { unique: false });
      }
      
      // Delivery log store
      if (!db.objectStoreNames.contains(STORE_DELIVERY_LOG)) {
        const store = db.createObjectStore(STORE_DELIVERY_LOG, {
          keyPath: 'id',
          autoIncrement: true
        });
        store.createIndex('notificationId', 'notificationId', { unique: false });
        store.createIndex('status', 'status', { unique: false });
        store.createIndex('timestamp', 'timestamp', { unique: false });
      }
      
      // Badge count store
      if (!db.objectStoreNames.contains(STORE_BADGE_COUNT)) {
        db.createObjectStore(STORE_BADGE_COUNT, { keyPath: 'id' });
      }
    };
  });
}

async function openDB() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);
  });
}

function promisifyRequest(request) {
  return new Promise((resolve, reject) => {
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

// ============================================================================
// NETWORK STATUS MONITORING
// ============================================================================

/**
 * Initialize network status monitoring
 */
function initNetworkMonitoring() {
  // Check initial online status
  isOnline = self.navigator.onLine;
  console.log('[SW] Initial network status:', isOnline ? 'online' : 'offline');
  
  // Monitor network status changes
  self.addEventListener('online', handleOnline);
  self.addEventListener('offline', handleOffline);
}

/**
 * Handle online event
 */
async function handleOnline() {
  console.log('[SW] Network connection restored');
  isOnline = true;
  
  // Notify clients
  await notifyClients({
    type: 'NETWORK_STATUS',
    online: true
  });
  
  // Trigger background sync
  if ('sync' in self.registration) {
    try {
      await self.registration.sync.register('sync-notifications');
      await self.registration.sync.register('sync-actions');
      console.log('[SW] Background sync triggered after reconnection');
    } catch (error) {
      console.warn('[SW] Failed to register background sync:', error);
      
      // Fallback: sync immediately
      await syncQueuedNotifications();
      await syncPendingActions();
    }
  } else {
    // No background sync support - sync immediately
    await syncQueuedNotifications();
    await syncPendingActions();
  }
}

/**
 * Handle offline event
 */
async function handleOffline() {
  console.log('[SW] Network connection lost');
  isOnline = false;
  
  // Notify clients
  await notifyClients({
    type: 'NETWORK_STATUS',
    online: false
  });
  
  // Show offline notification
  await showOfflineNotification();
}

/**
 * Check if device is online
 * @returns {boolean} Online status
 */
function checkOnlineStatus() {
  return isOnline && self.navigator.onLine;
}

/**
 * Show offline notification to user
 */
async function showOfflineNotification() {
  try {
    await self.registration.showNotification('Bağlantı Kesildi', {
      body: 'İnternet bağlantınız kesildi. Bildirimler bağlantı geri geldiğinde senkronize edilecek.',
      icon: '/static/icons/Icon-192.png',
      badge: '/static/icons/Icon-96.png',
      tag: 'offline-status',
      requireInteraction: false,
      silent: true,
      data: {
        type: 'offline_status'
      }
    });
  } catch (error) {
    console.error('[SW] Error showing offline notification:', error);
  }
}

/**
 * Notify all clients with a message
 * @param {Object} message - Message to send
 */
async function notifyClients(message) {
  try {
    const clients = await self.clients.matchAll({ 
      type: 'window', 
      includeUncontrolled: true 
    });
    
    for (const client of clients) {
      client.postMessage(message);
    }
    
    console.log('[SW] Message sent to', clients.length, 'clients');
  } catch (error) {
    console.error('[SW] Error notifying clients:', error);
  }
}

/**
 * Get network status information
 * @returns {Object} Network status info
 */
async function getNetworkStatus() {
  const queued = await getQueuedNotifications();
  
  return {
    online: checkOnlineStatus(),
    queuedNotifications: queued.length,
    lastSyncTime: lastSyncTime,
    syncAvailable: 'sync' in self.registration
  };
}

// Initialize network monitoring on load
initNetworkMonitoring();

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

function generateNotificationId() {
  return `notif_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

// ============================================================================
// FETCH HANDLER (CACHING STRATEGY)
// ============================================================================

self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);
  
  // Skip cross-origin requests
  if (url.origin !== self.location.origin) {
    return;
  }
  
  // Only handle GET requests
  if (request.method !== 'GET') {
    return;
  }
  
  // Route requests to appropriate strategy
  if (isStaticAsset(url.pathname)) {
    event.respondWith(cacheFirst(request, STATIC_CACHE));
  } else if (isAPIRequest(url.pathname)) {
    event.respondWith(networkFirst(request, DYNAMIC_CACHE));
  } else if (isImage(url.pathname)) {
    event.respondWith(cacheFirst(request, IMAGE_CACHE));
  } else if (isHTMLPage(url.pathname)) {
    event.respondWith(networkFirst(request, DYNAMIC_CACHE));
  } else {
    event.respondWith(networkFirst(request, DYNAMIC_CACHE));
  }
});

async function cacheFirst(request, cacheName) {
  try {
    const cache = await caches.open(cacheName);
    const cached = await cache.match(request);
    
    if (cached) {
      performanceMetrics.cacheHits++;
      return cached;
    }
    
    performanceMetrics.cacheMisses++;
    const response = await fetch(request);
    
    if (response.ok) {
      const clone = response.clone();
      cache.put(request, clone);
    }
    
    return response;
  } catch (error) {
    return getOfflineFallback(request);
  }
}

async function networkFirst(request, cacheName) {
  try {
    const response = await fetch(request);
    
    if (response.ok) {
      const cache = await caches.open(cacheName);
      const clone = response.clone();
      cache.put(request, clone);
    }
    
    return response;
  } catch (error) {
    const cache = await caches.open(cacheName);
    const cached = await cache.match(request);
    
    if (cached) {
      performanceMetrics.cacheHits++;
      return cached;
    }
    
    performanceMetrics.cacheMisses++;
    return getOfflineFallback(request);
  }
}

async function getOfflineFallback(request) {
  const url = new URL(request.url);
  
  if (isHTMLPage(url.pathname)) {
    const cache = await caches.open(STATIC_CACHE);
    const offline = await cache.match('/offline.html');
    return offline || new Response('Offline', { status: 503 });
  }
  
  if (isImage(url.pathname)) {
    const cache = await caches.open(STATIC_CACHE);
    return cache.match('/static/icons/Icon-192.png');
  }
  
  if (isAPIRequest(url.pathname)) {
    return new Response(JSON.stringify({
      success: false,
      error: 'Offline',
      offline: true
    }), {
      status: 503,
      headers: { 'Content-Type': 'application/json' }
    });
  }
  
  return new Response('Offline', { status: 503 });
}

function isStaticAsset(pathname) {
  return pathname.startsWith('/static/') ||
         pathname.includes('.css') ||
         pathname.includes('.js') ||
         pathname === '/manifest.json';
}

function isAPIRequest(pathname) {
  return pathname.startsWith('/api/');
}

function isImage(pathname) {
  return /\.(jpg|jpeg|png|gif|svg|webp|ico)$/i.test(pathname);
}

function isHTMLPage(pathname) {
  return !pathname.includes('.') || pathname.endsWith('.html');
}

// ============================================================================
// MESSAGE HANDLER
// ============================================================================

self.addEventListener('message', async (event) => {
  console.log('[SW] Message received:', event.data);
  
  const { action, data } = event.data;
  
  switch (action) {
    case 'skipWaiting':
      self.skipWaiting();
      break;
      
    case 'clearCaches':
      event.waitUntil(
        caches.keys().then((names) => {
          return Promise.all(names.map((name) => caches.delete(name)));
        })
      );
      break;
      
    case 'getNetworkStatus':
      const status = await getNetworkStatus();
      event.ports[0].postMessage(status);
      break;
      
    case 'syncNow':
      event.waitUntil(
        Promise.all([
          syncQueuedNotifications(),
          syncPendingActions()
        ])
      );
      break;
      
    case 'queueAction':
      await queuePendingAction(data);
      break;
      
    case 'getQueuedNotifications':
      const queued = await getQueuedNotifications();
      event.ports[0].postMessage(queued);
      break;
      
    case 'getBadgeCount':
      event.ports[0].postMessage({ count: getBadgeCount() });
      break;
      
    case 'setBadgeCount':
      const newCount = await setBadgeCount(data.count);
      event.ports[0].postMessage({ count: newCount });
      break;
      
    case 'resetBadgeCount':
      const resetCount = await resetBadgeCount();
      event.ports[0].postMessage({ count: resetCount });
      break;
      
    case 'updateBadgeCount':
      const updatedCount = await updateBadgeCount(data.delta);
      event.ports[0].postMessage({ count: updatedCount });
      break;
      
    case 'getPerformanceMetrics':
      event.ports[0].postMessage(getPerformanceMetrics());
      break;
      
    case 'clearPerformanceMetrics':
      clearPerformanceMetrics();
      event.ports[0].postMessage({ success: true });
      break;
      
    default:
      console.warn('[SW] Unknown message action:', action);
  }
});

// ============================================================================
// PERFORMANCE MONITORING & OPTIMIZATION
// ============================================================================

/**
 * Record performance metric
 * @param {string} type - Metric type (push, click, sync)
 * @param {number} duration - Duration in milliseconds
 */
function recordPerformanceMetric(type, duration) {
  const metrics = performanceMetrics[`${type}HandleTimes`];
  
  if (metrics) {
    metrics.push(duration);
    
    // Keep only last 100 measurements
    if (metrics.length > 100) {
      metrics.shift();
    }
    
    // Log warning if exceeding targets
    if (type === 'push' && duration > PUSH_HANDLE_TARGET) {
      console.warn(`[Perf] Push handling exceeded target: ${duration.toFixed(2)}ms > ${PUSH_HANDLE_TARGET}ms`);
    }
  }
}

/**
 * Get performance metrics summary
 * @returns {Object} Performance metrics
 */
function getPerformanceMetrics() {
  const calculateStats = (times) => {
    if (times.length === 0) return { avg: 0, min: 0, max: 0, count: 0 };
    
    const sum = times.reduce((a, b) => a + b, 0);
    return {
      avg: sum / times.length,
      min: Math.min(...times),
      max: Math.max(...times),
      count: times.length
    };
  };
  
  return {
    push: calculateStats(performanceMetrics.pushHandleTimes),
    click: calculateStats(performanceMetrics.clickHandleTimes),
    sync: calculateStats(performanceMetrics.syncTimes),
    cache: {
      hits: performanceMetrics.cacheHits,
      misses: performanceMetrics.cacheMisses,
      hitRate: performanceMetrics.cacheHits / (performanceMetrics.cacheHits + performanceMetrics.cacheMisses) || 0
    },
    timestamp: Date.now()
  };
}

/**
 * Clear performance metrics
 */
function clearPerformanceMetrics() {
  performanceMetrics.pushHandleTimes = [];
  performanceMetrics.clickHandleTimes = [];
  performanceMetrics.syncTimes = [];
  performanceMetrics.cacheHits = 0;
  performanceMetrics.cacheMisses = 0;
  console.log('[Perf] Performance metrics cleared');
}

/**
 * Memory cleanup - Remove old data
 */
async function performMemoryCleanup() {
  console.log('[Perf] Starting memory cleanup...');
  
  try {
    // Prune old notifications
    await pruneOldNotifications();
    
    // Clean old delivery logs (> 7 days)
    await cleanOldDeliveryLogs();
    
    // Check cache size
    await checkCacheSize();
    
    console.log('[Perf] Memory cleanup complete');
  } catch (error) {
    console.error('[Perf] Error during memory cleanup:', error);
  }
}

/**
 * Clean old delivery logs
 */
async function cleanOldDeliveryLogs() {
  try {
    const db = await openDB();
    const tx = db.transaction([STORE_DELIVERY_LOG], 'readwrite');
    const store = tx.objectStore(STORE_DELIVERY_LOG);
    const index = store.index('timestamp');
    
    const sevenDaysAgo = Date.now() - (7 * 24 * 60 * 60 * 1000);
    const oldLogs = await promisifyRequest(index.getAll());
    
    let deletedCount = 0;
    for (const log of oldLogs) {
      if (log.timestamp < sevenDaysAgo) {
        await promisifyRequest(store.delete(log.id));
        deletedCount++;
      }
    }
    
    if (deletedCount > 0) {
      console.log(`[Perf] Deleted ${deletedCount} old delivery logs`);
    }
  } catch (error) {
    console.error('[Perf] Error cleaning old logs:', error);
  }
}

/**
 * Check and manage cache size
 */
async function checkCacheSize() {
  if ('storage' in navigator && 'estimate' in navigator.storage) {
    try {
      const estimate = await navigator.storage.estimate();
      const usage = estimate.usage || 0;
      const quota = estimate.quota || 0;
      const usagePercent = (usage / quota) * 100;
      
      console.log(`[Perf] Storage: ${(usage / 1024 / 1024).toFixed(2)}MB / ${(quota / 1024 / 1024).toFixed(2)}MB (${usagePercent.toFixed(1)}%)`);
      
      // If using > 80% of quota, clean up
      if (usagePercent > 80) {
        console.warn('[Perf] Storage usage high, cleaning up...');
        await cleanupOldCaches();
      }
    } catch (error) {
      console.error('[Perf] Error checking storage:', error);
    }
  }
}

/**
 * Cleanup old caches
 */
async function cleanupOldCaches() {
  try {
    const cacheNames = await caches.keys();
    const currentCaches = [STATIC_CACHE, DYNAMIC_CACHE, IMAGE_CACHE];
    
    for (const cacheName of cacheNames) {
      if (!currentCaches.includes(cacheName)) {
        await caches.delete(cacheName);
        console.log(`[Perf] Deleted old cache: ${cacheName}`);
      }
    }
  } catch (error) {
    console.error('[Perf] Error cleaning up caches:', error);
  }
}

/**
 * Optimize batch operations
 * @param {Array} operations - Array of async operations
 * @param {number} batchSize - Batch size
 * @returns {Promise<Array>} Results
 */
async function batchOperations(operations, batchSize = 5) {
  const results = [];
  
  for (let i = 0; i < operations.length; i += batchSize) {
    const batch = operations.slice(i, i + batchSize);
    const batchResults = await Promise.allSettled(batch.map(op => op()));
    results.push(...batchResults);
  }
  
  return results;
}

// Schedule periodic memory cleanup
setInterval(performMemoryCleanup, MEMORY_CLEANUP_INTERVAL);

// Initial cleanup after 1 minute
setTimeout(performMemoryCleanup, 60000);

console.log('[SW v3.0] Service Worker loaded successfully with performance optimizations');
