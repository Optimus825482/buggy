// Service Worker for Buggy Call PWA - Advanced Mobile Push Notifications
// Version 3.0.0 - Enhanced with offline queue, badge management, and performance optimizations
// Powered by Erkan ERDEM

const CACHE_VERSION = 'buggycall-v3.0.0';
const STATIC_CACHE = `${CACHE_VERSION}-static`;
const DYNAMIC_CACHE = `${CACHE_VERSION}-dynamic`;
const IMAGE_CACHE = `${CACHE_VERSION}-images`;

// IndexedDB Configuration
const DB_NAME = 'BuggyCallDB';
const DB_VERSION = 2;
const STORE_NOTIFICATIONS = 'notifications';
const STORE_PENDING_ACTIONS = 'pendingActions';
const STORE_DELIVERY_LOG = 'deliveryLog';
const STORE_BADGE_COUNT = 'badgeCount';

// Performance Configuration
const MAX_NOTIFICATIONS_STORED = 100;
const LOG_BATCH_SIZE = 10;
const LOG_BATCH_INTERVAL = 5000; // 5 seconds
const SYNC_THROTTLE = 60000; // 1 minute

// Global state
let badgeCount = 0;
let pendingLogs = [];
let lastSyncTime = 0;

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
    // Build notification options
    const options = buildNotificationOptions(data, priority);
    
    // Execute all operations in parallel for speed
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
    
    const duration = performance.now() - startTime;
    console.log(`[Perf] Push handled in ${duration.toFixed(2)}ms`);
    
    if (duration > 500) {
      console.warn('[Perf] Push handling exceeded 500ms budget');
    }
  } catch (error) {
    console.error('[SW] Error handling push:', error);
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
// NOTIFICATION CLICK HANDLER
// ============================================================================

self.addEventListener('notificationclick', async (event) => {
  console.log('[SW] Notification clicked:', event.action);
  
  event.notification.close();
  
  // Decrement badge
  await updateBadgeCount(-1);
  
  // Log click
  if (event.notification.data && event.notification.data.notificationId) {
    await logNotificationClick(event.notification.data.notificationId);
  }
  
  // Handle action
  const urlToOpen = await handleNotificationAction(event.action, event.notification.data);
  
  // Open or focus window
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true })
      .then((clientList) => {
        // Try to focus existing window
        for (const client of clientList) {
          if (client.url.includes('driver') && 'focus' in client) {
            return client.focus().then(() => {
              if (urlToOpen) {
                client.postMessage({
                  type: 'NAVIGATE',
                  url: urlToOpen
                });
              }
            });
          }
        }
        // Open new window
        if (clients.openWindow) {
          return clients.openWindow(urlToOpen || '/driver/dashboard');
        }
      })
  );
});

async function handleNotificationAction(action, data) {
  if (action === 'accept') {
    // Handle accept action
    if (data && data.request_id) {
      return `/driver/dashboard?accept=${data.request_id}`;
    }
  } else if (action === 'details') {
    // Handle details action
    if (data && data.request_id) {
      return `/driver/request/${data.request_id}`;
    }
  }
  
  // Default action
  return data && data.url ? data.url : '/driver/dashboard';
}

// ============================================================================
// BADGE MANAGER
// ============================================================================

async function updateBadgeCount(delta) {
  badgeCount += delta;
  
  if (badgeCount < 0) badgeCount = 0;
  
  // Update app badge
  if ('setAppBadge' in navigator) {
    try {
      if (badgeCount > 0) {
        await navigator.setAppBadge(badgeCount);
      } else {
        await navigator.clearAppBadge();
      }
    } catch (error) {
      console.warn('[SW] Badge API not supported:', error);
    }
  }
  
  // Store in IndexedDB for persistence
  await storeBadgeCount(badgeCount);
}

async function loadBadgeCount() {
  try {
    const db = await openDB();
    const tx = db.transaction([STORE_BADGE_COUNT], 'readonly');
    const store = tx.objectStore(STORE_BADGE_COUNT);
    const result = await promisifyRequest(store.get('count'));
    
    if (result) {
      badgeCount = result.value || 0;
      if (badgeCount > 0 && 'setAppBadge' in navigator) {
        await navigator.setAppBadge(badgeCount);
      }
    }
  } catch (error) {
    console.warn('[SW] Error loading badge count:', error);
  }
}

async function storeBadgeCount(count) {
  try {
    const db = await openDB();
    const tx = db.transaction([STORE_BADGE_COUNT], 'readwrite');
    const store = tx.objectStore(STORE_BADGE_COUNT);
    await promisifyRequest(store.put({ id: 'count', value: count }));
  } catch (error) {
    console.warn('[SW] Error storing badge count:', error);
  }
}

// ============================================================================
// OFFLINE QUEUE MANAGER
// ============================================================================

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

async function queueNotification(notificationData) {
  try {
    const db = await openDB();
    const tx = db.transaction([STORE_NOTIFICATIONS], 'readwrite');
    const store = tx.objectStore(STORE_NOTIFICATIONS);
    
    await promisifyRequest(store.add({
      ...notificationData,
      status: 'queued',
      queuedAt: Date.now(),
      retries: 0
    }));
  } catch (error) {
    console.error('[SW] Error queueing notification:', error);
  }
}

// ============================================================================
// BACKGROUND SYNC
// ============================================================================

self.addEventListener('sync', (event) => {
  const now = Date.now();
  
  // Throttle sync events
  if (now - lastSyncTime < SYNC_THROTTLE) {
    console.log('[SW] Sync throttled');
    return;
  }
  
  lastSyncTime = now;
  console.log('[SW] Background sync triggered:', event.tag);
  
  if (event.tag === 'sync-notifications') {
    event.waitUntil(syncQueuedNotifications());
  }
});

async function syncQueuedNotifications() {
  try {
    const db = await openDB();
    const tx = db.transaction([STORE_NOTIFICATIONS], 'readonly');
    const store = tx.objectStore(STORE_NOTIFICATIONS);
    const index = store.index('status');
    
    const queued = await promisifyRequest(index.getAll('queued'));
    
    console.log(`[SW] Syncing ${queued.length} queued notifications`);
    
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
        await logNotificationDelivery(notification, 'delivered', 'synced');
        
      } catch (error) {
        // Increment retry count
        await incrementRetryCount(notification.id);
        
        // Log failure
        await logNotificationDelivery(notification, 'failed', error.message);
      }
    }
  } catch (error) {
    console.error('[SW] Error syncing notifications:', error);
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
    status: status,
    timestamp: Date.now(),
    error_message: errorMessage
  };
  
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
      return cached;
    }
    
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
      return cached;
    }
    
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

self.addEventListener('message', (event) => {
  console.log('[SW] Message received:', event.data);
  
  if (event.data.action === 'skipWaiting') {
    self.skipWaiting();
  }
  
  if (event.data.action === 'clearCaches') {
    event.waitUntil(
      caches.keys().then((names) => {
        return Promise.all(names.map((name) => caches.delete(name)));
      })
    );
  }
});

console.log('[SW v3.0] Service Worker loaded successfully');
