// Service Worker for Shuttle Call PWA - Optimized Version
// Version 5.1.0 - Cache Fixed
// Powered by Erkan ERDEM

const CACHE_VERSION = 'shuttlecall-v5.1.0';
const CACHE_NAME = `${CACHE_VERSION}-cache`;

// Offline sayfası için cache
const OFFLINE_URL = '/offline';

// ============================================================================
// INSTALLATION
// ============================================================================

self.addEventListener('install', (event) => {
  console.log('[SW v5.1] Installing Service Worker');
  
  event.waitUntil(
    caches.open(CACHE_NAME).then(async (cache) => {
      console.log('[SW] Caching offline resources');
      
      // Her dosyayı tek tek cache'le - hata olursa devam et
      const urlsToCache = [
        '/static/icons/Icon-192.png',
        '/static/css/main.css'
      ];
      
      for (const url of urlsToCache) {
        try {
          const response = await fetch(url);
          if (response.ok) {
            await cache.put(url, response);
            console.log('[SW] Cached:', url);
          }
        } catch (err) {
          console.warn('[SW] Failed to cache:', url, err.message);
        }
      }
      
      console.log('[SW] Installation complete');
    })
    // skipWaiting() kaldırıldı - sadece mesaj geldiğinde aktif olacak
  );
});

// ============================================================================
// ACTIVATION
// ============================================================================

self.addEventListener('activate', (event) => {
  console.log('[SW v5.1] Activating Service Worker');
  
  event.waitUntil(
    Promise.all([
      self.clients.claim(),
      caches.keys().then((cacheNames) => {
        return Promise.all(
          cacheNames.map((cacheName) => {
            if (cacheName !== CACHE_NAME) {
              console.log(`[SW] Deleting old cache: ${cacheName}`);
              return caches.delete(cacheName);
            }
          })
        );
      })
    ]).then(() => {
      console.log('[SW v5.0] Activation complete');
    })
  );
});

// ============================================================================
// FETCH - Network First with Offline Fallback
// ============================================================================

self.addEventListener('fetch', (event) => {
  // Sadece GET isteklerini işle
  if (event.request.method !== 'GET') {
    return;
  }

  // API isteklerini cache'leme
  if (event.request.url.includes('/api/')) {
    return;
  }

  event.respondWith(
    fetch(event.request)
      .then((response) => {
        // Başarılı response'u cache'e kaydet
        // Sadece http/https URL'leri cache'le (chrome-extension, data: vb. hariç)
        if (response && response.status === 200 && 
            (event.request.url.startsWith('http://') || event.request.url.startsWith('https://'))) {
          const responseClone = response.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(event.request, responseClone).catch((err) => {
              console.warn('[SW] Cache put error:', err.message);
            });
          });
        }
        return response;
      })
      .catch(() => {
        // Network başarısız, cache'den dene
        return caches.match(event.request).then((cachedResponse) => {
          if (cachedResponse) {
            return cachedResponse;
          }
          
          // HTML sayfası için offline sayfasını göster
          if (event.request.headers.get('accept').includes('text/html')) {
            return caches.match(OFFLINE_URL);
          }
          
          // Diğer kaynaklar için boş response
          return new Response('Offline', {
            status: 503,
            statusText: 'Service Unavailable'
          });
        });
      })
  );
});

// ============================================================================
// PUSH NOTIFICATIONS
// ============================================================================

self.addEventListener('push', (event) => {
  console.log('[SW] Push notification received');
  
  let data = {};
  try {
    data = event.data ? event.data.json() : {};
  } catch (e) {
    console.error('[SW] Error parsing push data:', e);
    data = { title: 'Yeni Bildirim', body: 'Yeni bir bildiriminiz var' };
  }
  
  const title = data.title || 'Shuttle Call';
  const options = {
    body: data.body || 'Yeni bir bildiriminiz var',
    icon: data.icon || '/static/icons/Icon-192.png',
    badge: '/static/icons/Icon-96.png',
    vibrate: [200, 100, 200],
    tag: data.tag || 'shuttle-notification',
    requireInteraction: data.requireInteraction || false,
    data: data.data || {}
  };
  
  event.waitUntil(
    self.registration.showNotification(title, options)
  );
});

// ============================================================================
// NOTIFICATION CLICK
// ============================================================================

self.addEventListener('notificationclick', (event) => {
  console.log('[SW] Notification clicked:', event.notification.tag);
  event.notification.close();
  
  // Get notification data
  const notificationData = event.notification.data || {};
  const targetUrl = notificationData.url || '/driver/dashboard';
  
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clientList) => {
      // Try to find existing driver dashboard window
      for (let client of clientList) {
        if (client.url.includes('/driver/dashboard') && 'focus' in client) {
          console.log('[SW] Focusing existing dashboard window');
          return client.focus();
        }
      }
      
      // Try to find any window in scope
      for (let client of clientList) {
        if (client.url.includes(self.registration.scope) && 'focus' in client) {
          console.log('[SW] Focusing existing window and navigating');
          client.navigate(targetUrl);
          return client.focus();
        }
      }
      
      // Open new window
      if (clients.openWindow) {
        console.log('[SW] Opening new window:', targetUrl);
        return clients.openWindow(targetUrl);
      }
    })
  );
});

// ============================================================================
// MESSAGE HANDLER
// ============================================================================

self.addEventListener('message', (event) => {
  console.log('[SW] Message received:', event.data);
  
  if (event.data && event.data.action === 'skipWaiting') {
    self.skipWaiting();
  }
  
  // Badge reset handler
  if (event.data && event.data.action === 'resetBadgeCount') {
    // Badge API desteği varsa sıfırla
    if ('setAppBadge' in self.navigator) {
      self.navigator.clearAppBadge()
        .then(() => {
          // MessageChannel ile cevap gönder
          if (event.ports && event.ports[0]) {
            event.ports[0].postMessage({ success: true, count: 0 });
          }
        })
        .catch((error) => {
          console.warn('[SW] Badge clear error:', error);
          if (event.ports && event.ports[0]) {
            event.ports[0].postMessage({ success: false, count: 0 });
          }
        });
    } else {
      // Badge API desteklenmiyorsa direkt cevap gönder
      if (event.ports && event.ports[0]) {
        event.ports[0].postMessage({ success: true, count: 0 });
      }
    }
  }
  
  // Network status handler
  if (event.data && event.data.action === 'getNetworkStatus') {
    if (event.ports && event.ports[0]) {
      event.ports[0].postMessage({ 
        online: self.navigator.onLine,
        type: self.navigator.connection?.effectiveType || 'unknown'
      });
    }
  }
});

console.log('[SW v5.1] Service Worker loaded successfully - PWA Ready!');
