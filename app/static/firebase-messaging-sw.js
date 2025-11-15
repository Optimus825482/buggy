// Firebase Cloud Messaging Service Worker
// Buggy Call - FCM Push Notifications
// Powered by Erkan ERDEM

// Firebase SDK import (v9+)
importScripts('https://www.gstatic.com/firebasejs/10.7.0/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/10.7.0/firebase-messaging-compat.js');

// ⚠️ SERVICE WORKER SCOPE: Cannot use firebase-config.js here
// Service Workers run in different context and can't access window.firebaseConfig
// Config must be hardcoded here - keep in sync with firebase-config.js
const firebaseConfig = {
  apiKey: "AIzaSyD5brCkHqSPVCtt0XJmUMqZizrjK_HX9dc",
  authDomain: "shuttle-call-835d9.firebaseapp.com",
  projectId: "shuttle-call-835d9",
  storageBucket: "shuttle-call-835d9.firebasestorage.app",
  messagingSenderId: "1044072191950",
  appId: "1:1044072191950:web:dc780e1832d3a4ee5afd9f",
  measurementId: "G-DCP7FTRM9Q"
};

// Firebase'i başlat
try {
  firebase.initializeApp(firebaseConfig);
  const messaging = firebase.messaging();
  
  console.log('[FCM SW] Firebase Messaging initialized');
  
  // ============================================================================
  // BACKGROUND MESSAGE HANDLER
  // ============================================================================
  // NOT: Cache management ana sw.js tarafından yapılıyor
  // Install/Activate event'leri kaldırıldı - SW update döngüsünü önlemek için
  
  messaging.onBackgroundMessage((payload) => {
    console.log('[FCM SW] Background message received:', payload);
    
    // Notification data
    const notificationTitle = payload.notification?.title || 'Buggy Call';
    const notificationOptions = {
      body: payload.notification?.body || 'Yeni bir bildiriminiz var',
      icon: payload.notification?.icon || '/static/icons/Icon-192.png',
      badge: '/static/icons/Icon-96.png',
      tag: payload.data?.type || 'buggy-notification',
      data: payload.data || {},
      vibrate: [200, 100, 200, 100, 200],
      requireInteraction: payload.data?.priority === 'high',
      actions: []
    };
    
    // Bildirim tipine göre özel ayarlar ve action buttons
    if (payload.data?.type === 'new_request') {
      notificationOptions.requireInteraction = true;
      notificationOptions.vibrate = [200, 100, 200, 100, 200, 100, 200];
      notificationOptions.actions = [
        { action: 'accept', title: '✅ Kabul Et', icon: '/static/icons/Icon-96.png' },
        { action: 'details', title: '👁️ Detaylar', icon: '/static/icons/Icon-96.png' },
        { action: 'dismiss', title: '❌ Kapat', icon: '/static/icons/Icon-96.png' }
      ];
    }
    
    // Görsel varsa ekle
    if (payload.notification?.image) {
      notificationOptions.image = payload.notification.image;
    }
    
    // Bildirimi göster
    return self.registration.showNotification(notificationTitle, notificationOptions);
  });
  
  // ============================================================================
  // NOTIFICATION CLICK HANDLER
  // ============================================================================
  
  self.addEventListener('notificationclick', (event) => {
    console.log('[FCM SW] Notification clicked:', event.notification.tag, 'Action:', event.action);
    
    event.notification.close();
    
    // Action handling
    if (event.action === 'dismiss') {
      console.log('[FCM SW] Notification dismissed');
      return;
    }
    
    // Get notification data
    const notificationData = event.notification.data || {};
    let targetUrl = notificationData.url || '/driver/dashboard';
    
    // Handle "Kabul Et" action
    if (event.action === 'accept' && notificationData.type === 'new_request') {
      console.log('[FCM SW] Accept action clicked for request:', notificationData.request_id);
      targetUrl = `/driver/dashboard?auto_accept=${notificationData.request_id}`;
    }
    
    // Handle "Detaylar" action
    if (event.action === 'details' && notificationData.type === 'new_request') {
      console.log('[FCM SW] Details action clicked for request:', notificationData.request_id);
      targetUrl = `/driver/dashboard?highlight=${notificationData.request_id}`;
    }
    
    // ✅ FIX: Bildirim tipine göre DOĞRU URL belirle
    if (notificationData.type === 'new_request') {
      targetUrl = '/driver/dashboard';
    } else if (notificationData.type === 'status_update') {
      // ✅ Guest notification - status sayfasına git
      const requestId = notificationData.request_id;
      if (requestId) {
        targetUrl = `/guest/status/${requestId}`;
      }
    } else if (notificationData.type === 'request_accepted' || notificationData.type === 'request_completed') {
      // ✅ Guest notification - status sayfasına git
      const requestId = notificationData.request_id;
      if (requestId) {
        targetUrl = `/guest/status/${requestId}`;
      }
    }

    console.log('[FCM SW] Target URL:', targetUrl);

    // Pencereyi aç veya odaklan
    event.waitUntil(
      clients.matchAll({ type: 'window', includeUncontrolled: true })
        .then((clientList) => {
          console.log('[FCM SW] Found', clientList.length, 'windows');

          // ✅ DRIVER notification için - mevcut dashboard'a odaklan
          if (notificationData.type === 'new_request') {
            for (let client of clientList) {
              if (client.url.includes('/driver/dashboard') && 'focus' in client) {
                console.log('[FCM SW] Focusing existing driver dashboard');
                return client.focus();
              }
            }
          }

          // ✅ GUEST notification için - mevcut status sayfasına odaklan veya git
          if (notificationData.type === 'status_update' ||
              notificationData.type === 'request_accepted' ||
              notificationData.type === 'request_completed') {
            for (let client of clientList) {
              if (client.url.includes('/guest/status') && 'focus' in client) {
                console.log('[FCM SW] Focusing existing guest status page');
                // Sayfayı yenile (güncel durumu görmek için)
                client.navigate(targetUrl);
                return client.focus();
              }
            }
          }

          // Herhangi bir pencere varsa ona git
          for (let client of clientList) {
            if ('focus' in client) {
              console.log('[FCM SW] Navigating existing window to:', targetUrl);
              client.navigate(targetUrl);
              return client.focus();
            }
          }

          // Yeni pencere aç
          if (clients.openWindow) {
            console.log('[FCM SW] Opening new window:', targetUrl);
            return clients.openWindow(targetUrl);
          }
        })
    );
  });
  
  console.log('[FCM SW] Service Worker ready for FCM notifications');
  
} catch (error) {
  console.error('[FCM SW] Firebase initialization error:', error);
}
