// Service Worker for Buggy Call PWA - Enhanced Version
// Powered by Erkan ERDEM
const CACHE_VERSION = 'buggycall-v2.0.2';
const STATIC_CACHE = `${CACHE_VERSION}-static`;
const DYNAMIC_CACHE = `${CACHE_VERSION}-dynamic`;
const IMAGE_CACHE = `${CACHE_VERSION}-images`;

// Static assets to cache immediately
const STATIC_ASSETS = [
  '/',
  '/static/css/main.css',
  '/static/css/variables.css',
  '/static/js/common.js',
  '/static/manifest.json',
  '/offline.html',
  // Icons
  '/static/icons/Icon-72.png',
  '/static/icons/Icon-96.png',
  '/static/icons/Icon-120.png',
  '/static/icons/Icon-144.png',
  '/static/icons/Icon-152.png',
  '/static/icons/Icon-192.png',
  '/static/icons/Icon-512.png',
  '/static/icons/apple-touch-icon.png',
  '/static/icons/favicon-32x32.png',
  '/static/icons/favicon-16x16.png'
];

// API endpoints to cache with network-first strategy
const API_ENDPOINTS = [
  '/api/driver/pending-requests',
  '/api/driver/active-requests',
  '/api/locations',
  '/api/buggies'
];

// Install event - Pre-cache static assets
self.addEventListener('install', (event) => {
  console.log('[SW] Installing Service Worker v' + CACHE_VERSION);

  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then((cache) => {
        console.log('[SW] Caching static assets');
        // Add files one by one to handle errors gracefully
        return Promise.allSettled(
          STATIC_ASSETS.map((url) => {
            return cache.add(url).catch((err) => {
              console.warn('[SW] Failed to cache:', url, err.message);
              return null;
            });
          })
        );
      })
      .then(() => {
        console.log('[SW] Static assets cached successfully');
        // Skip waiting to activate immediately
        return self.skipWaiting();
      })
      .catch((err) => {
        console.error('[SW] Installation failed:', err);
      })
  );
});

// Activate event - Clean up old caches
self.addEventListener('activate', (event) => {
  console.log('[SW] Activating Service Worker v' + CACHE_VERSION);

  event.waitUntil(
    caches.keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames.map((cacheName) => {
            if (!cacheName.startsWith(CACHE_VERSION)) {
              console.log('[SW] Deleting old cache:', cacheName);
              return caches.delete(cacheName);
            }
          })
        );
      })
      .then(() => {
        console.log('[SW] Service Worker activated');
        // Claim all clients immediately
        return self.clients.claim();
      })
  );
});

// Fetch event - Smart caching strategies
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

// Cache-first strategy - Try cache, fallback to network
async function cacheFirst(request, cacheName) {
  try {
    const cache = await caches.open(cacheName);
    const cached = await cache.match(request);

    if (cached) {
      console.log('[SW] Serving from cache:', request.url);
      return cached;
    }

    console.log('[SW] Fetching from network:', request.url);
    const response = await fetch(request);

    // Cache successful responses
    if (response.ok) {
      const clone = response.clone();
      cache.put(request, clone);
    }

    return response;
  } catch (error) {
    console.error('[SW] Cache-first failed:', error);
    return getOfflineFallback(request);
  }
}

// Network-first strategy - Try network, fallback to cache
async function networkFirst(request, cacheName) {
  try {
    console.log('[SW] Fetching from network:', request.url);
    const response = await fetch(request);

    // Cache successful responses
    if (response.ok) {
      const cache = await caches.open(cacheName);
      const clone = response.clone();
      cache.put(request, clone);
    }

    return response;
  } catch (error) {
    console.log('[SW] Network failed, trying cache:', request.url);
    const cache = await caches.open(cacheName);
    const cached = await cache.match(request);

    if (cached) {
      console.log('[SW] Serving from cache:', request.url);
      return cached;
    }

    return getOfflineFallback(request);
  }
}

// Get offline fallback based on request type
async function getOfflineFallback(request) {
  const url = new URL(request.url);

  if (isHTMLPage(url.pathname)) {
    const cache = await caches.open(STATIC_CACHE);
    const offline = await cache.match('/offline.html');
    return offline || new Response('Offline - No cached data available', {
      status: 503,
      statusText: 'Service Unavailable',
      headers: { 'Content-Type': 'text/plain' }
    });
  }

  if (isImage(url.pathname)) {
    // Return placeholder image or cached icon
    const cache = await caches.open(STATIC_CACHE);
    return cache.match('/static/icons/Icon-192.png');
  }

  if (isAPIRequest(url.pathname)) {
    return new Response(JSON.stringify({
      success: false,
      error: 'Offline - No internet connection',
      offline: true
    }), {
      status: 503,
      statusText: 'Service Unavailable',
      headers: { 'Content-Type': 'application/json' }
    });
  }

  return new Response('Offline', {
    status: 503,
    statusText: 'Service Unavailable'
  });
}

// Helper functions
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

// Background Sync for offline requests
self.addEventListener('sync', (event) => {
  console.log('[SW] Background sync triggered:', event.tag);

  if (event.tag === 'sync-buggy-requests') {
    event.waitUntil(syncBuggyRequests());
  }
});

async function syncBuggyRequests() {
  try {
    // Get pending requests from IndexedDB
    const requests = await getPendingRequests();

    for (const req of requests) {
      try {
        await fetch(req.url, {
          method: req.method,
          headers: req.headers,
          body: req.body
        });

        // Remove from pending if successful
        await removePendingRequest(req.id);
      } catch (error) {
        console.error('[SW] Failed to sync request:', error);
      }
    }
  } catch (error) {
    console.error('[SW] Background sync failed:', error);
  }
}

// Push notification handler
self.addEventListener('push', (event) => {
  console.log('[SW] Push notification received');

  if (!event.data) {
    console.log('[SW] Push event but no data');
    return;
  }

  const data = event.data.json();
  const title = data.title || 'Buggy Call';
  const options = {
    body: data.body || 'Yeni bir bildiriminiz var',
    icon: '/static/icons/Icon-192.png',
    badge: '/static/icons/Icon-96.png',
    vibrate: [200, 100, 200],
    tag: data.tag || 'buggy-call-notification',
    data: {
      url: data.url || '/',
      timestamp: Date.now()
    },
    actions: data.actions || []
  };

  event.waitUntil(
    self.registration.showNotification(title, options)
  );
});

// Notification click handler
self.addEventListener('notificationclick', (event) => {
  console.log('[SW] Notification clicked');

  event.notification.close();

  const urlToOpen = event.notification.data?.url || '/';

  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true })
      .then((clientList) => {
        // Check if there's already a window open
        for (const client of clientList) {
          if (client.url === urlToOpen && 'focus' in client) {
            return client.focus();
          }
        }
        // Open new window if none exists
        if (clients.openWindow) {
          return clients.openWindow(urlToOpen);
        }
      })
  );
});

// Message handler for communication with main thread
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

// IndexedDB Helper Functions
const DB_NAME = 'BuggyCallDB';
const DB_VERSION = 1;
const STORE_NAME = 'pendingRequests';

async function openDB() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);

    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);

    request.onupgradeneeded = (event) => {
      const db = event.target.result;
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        const store = db.createObjectStore(STORE_NAME, {
          keyPath: 'id',
          autoIncrement: true
        });
        store.createIndex('timestamp', 'timestamp', { unique: false });
        store.createIndex('type', 'type', { unique: false });
      }
    };
  });
}

async function getPendingRequests() {
  try {
    const db = await openDB();
    const transaction = db.transaction([STORE_NAME], 'readonly');
    const store = transaction.objectStore(STORE_NAME);

    return new Promise((resolve, reject) => {
      const request = store.getAll();
      request.onsuccess = () => resolve(request.result || []);
      request.onerror = () => reject(request.error);
    });
  } catch (error) {
    console.error('[SW] Error getting pending requests:', error);
    return [];
  }
}

async function removePendingRequest(id) {
  try {
    const db = await openDB();
    const transaction = db.transaction([STORE_NAME], 'readwrite');
    const store = transaction.objectStore(STORE_NAME);

    return new Promise((resolve, reject) => {
      const request = store.delete(id);
      request.onsuccess = () => resolve(true);
      request.onerror = () => reject(request.error);
    });
  } catch (error) {
    console.error('[SW] Error removing pending request:', error);
    return false;
  }
}

async function addPendingRequest(requestData) {
  try {
    const db = await openDB();
    const transaction = db.transaction([STORE_NAME], 'readwrite');
    const store = transaction.objectStore(STORE_NAME);

    return new Promise((resolve, reject) => {
      const request = store.add({
        url: requestData.url,
        method: requestData.method,
        headers: requestData.headers,
        body: requestData.body,
        type: requestData.type || 'general',
        timestamp: Date.now(),
        retries: 0
      });
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  } catch (error) {
    console.error('[SW] Error adding pending request:', error);
    return null;
  }
}

console.log('[SW] Service Worker loaded successfully');
