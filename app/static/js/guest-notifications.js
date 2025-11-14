/**
 * Guest Notification Manager
 * FCM (Firebase Cloud Messaging) for Guest Users
 * Powered by Erkan ERDEM
 */

class GuestNotificationManager {
    constructor() {
        this.messaging = null;
        this.token = null;
        this.initialized = false;
    }

    /**
     * Initialize FCM for guest
     */
    async init() {
        try {
            console.log('🔔 [Guest FCM] Initializing...');

            // Check if FCM is supported
            if (!('serviceWorker' in navigator)) {
                console.warn('⚠️ [Guest FCM] Service Worker not supported');
                return false;
            }

            if (!('PushManager' in window)) {
                console.warn('⚠️ [Guest FCM] Push notifications not supported');
                return false;
            }

            // Check if firebase is loaded
            if (typeof firebase === 'undefined') {
                console.error('❌ [Guest FCM] Firebase SDK not loaded');
                return false;
            }

            // Get Firebase config from window

            const firebaseConfig = window.firebaseConfig || {
                apiKey: "AIzaSyD5brCkHqSPVCtt0XJmUMqZizrjK_HX9dc",
                authDomain: "shuttle-call-835d9.firebaseapp.com",
                projectId: "shuttle-call-835d9",
                storageBucket: "shuttle-call-835d9.firebasestorage.app",
                messagingSenderId: "1044072191950",
                appId: "1:1044072191950:web:dc780e1832d3a4ee5afd9f",
                measurementId: "G-DCP7FTRM9Q",
                vapidKey: "BBrNGl2-VPA-iuLasrj8jpS2Sj2FrYr-FQq57GET6ofRV4QOljRwyLg--HMI-bV7m-lmdBk5NJxSyy3nVpNLzA4"
            };

            // Initialize Firebase
            if (!firebase.apps.length) {
                firebase.initializeApp(firebaseConfig);
            }

            this.messaging = firebase.messaging();
            this.initialized = true;

            console.log('✅ [Guest FCM] Initialized successfully');
            return true;

        } catch (error) {
            console.error('❌ [Guest FCM] Initialization error:', error);
            return false;
        }
    }

    /**
     * Request permission and get FCM token
     */
    async requestPermissionAndGetToken(requestId = null) {
        try {
            if (!this.initialized) {
                console.warn('⚠️ [Guest FCM] Not initialized');
                return null;
            }

            // Request notification permission
            const permission = await Notification.requestPermission();
            
            if (permission !== 'granted') {
                console.warn('⚠️ [Guest FCM] Permission denied');
                return null;
            }

            console.log('✅ [Guest FCM] Permission granted');

            // Get service worker registration
            const registration = await navigator.serviceWorker.ready;
            
            if (!registration) {
                console.error('❌ [Guest FCM] Service Worker not ready');
                return null;
            }

            console.log('✅ [Guest FCM] Service Worker ready');

            // Get FCM token with VAPID key from config
            const firebaseConfig = window.firebaseConfig || {
                apiKey: "AIzaSyD5brCkHqSPVCtt0XJmUMqZizrjK_HX9dc",
                authDomain: "shuttle-call-835d9.firebaseapp.com",
                projectId: "shuttle-call-835d9",
                storageBucket: "shuttle-call-835d9.firebasestorage.app",
                messagingSenderId: "1044072191950",
                appId: "1:1044072191950:web:dc780e1832d3a4ee5afd9f",
                measurementId: "G-DCP7FTRM9Q",
                vapidKey: "BBrNGl2-VPA-iuLasrj8jpS2Sj2FrYr-FQq57GET6ofRV4QOljRwyLg--HMI-bV7m-lmdBk5NJxSyy3nVpNLzA4"
            };
            
            const vapidKey = firebaseConfig.vapidKey;
            
            if (!vapidKey) {
                console.error('❌ [Guest FCM] VAPID key not found in config');
                return null;
            }

            console.log('🔑 [Guest FCM] Using VAPID key from config');

            this.token = await this.messaging.getToken({
                vapidKey: vapidKey,
                serviceWorkerRegistration: registration
            });

            if (this.token) {
                console.log('🔑 [Guest FCM] Token received:', this.token.substring(0, 20) + '...');
                
                // Register token to backend if requestId provided
                if (requestId) {
                    await this.registerToken(requestId);
                }
                
                return this.token;
            } else {
                console.warn('⚠️ [Guest FCM] No token received');
                return null;
            }

        } catch (error) {
            console.error('❌ [Guest FCM] Token error:', error);
            return null;
        }
    }

    /**
     * Register FCM token to backend
     */
    async registerToken(requestId) {
        try {
            if (!this.token) {
                console.warn('⚠️ [Guest FCM] No token to register');
                return false;
            }

            console.log('💾 [Guest FCM] Registering token for request:', requestId);

            const response = await fetch('/api/guest/register-fcm-token', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    token: this.token,
                    request_id: requestId
                })
            });

            const data = await response.json();

            if (data.success) {
                console.log('✅ [Guest FCM] Token registered successfully');
                return true;
            } else {
                console.error('❌ [Guest FCM] Token registration failed:', data.message);
                return false;
            }

        } catch (error) {
            console.error('❌ [Guest FCM] Token registration error:', error);
            return false;
        }
    }

    /**
     * Setup foreground message listener
     */
    setupMessageListener(callback) {
        if (!this.messaging) {
            console.warn('⚠️ [Guest FCM] Messaging not initialized');
            return;
        }

        this.messaging.onMessage((payload) => {
            console.log('📬 [Guest FCM] Foreground message received:', payload);
            
            if (callback && typeof callback === 'function') {
                callback(payload);
            }

            // Show notification
            this.showNotification(payload);
        });
    }

    /**
     * Show notification
     */
    showNotification(payload) {
        try {
            const title = payload.notification?.title || 'Shuttle Call';
            const options = {
                body: payload.notification?.body || 'Yeni bildirim',
                icon: payload.notification?.icon || '/static/icons/Icon-192.png',
                badge: '/static/icons/Icon-96.png',
                vibrate: [200, 100, 200],
                tag: 'shuttle-notification',
                requireInteraction: false,
                data: payload.data || {}
            };

            if (Notification.permission === 'granted') {
                new Notification(title, options);
            }

        } catch (error) {
            console.error('❌ [Guest FCM] Show notification error:', error);
        }
    }
}

// Export to global scope
window.GuestNotificationManager = GuestNotificationManager;

console.log('✅ [Guest FCM] GuestNotificationManager loaded');
