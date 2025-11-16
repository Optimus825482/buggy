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

            // ✅ iOS Safari kontrolü
            const isIOS = /iPhone|iPad|iPod/i.test(navigator.userAgent);
            const isSafari = /Safari/i.test(navigator.userAgent) && !/Chrome|CriOS|FxiOS/i.test(navigator.userAgent);
            const isPWA = window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone === true;

            if (isIOS) {
                console.log('📱 [Guest FCM] iOS detected');

                // iOS 16.4 altı kontrol
                const match = navigator.userAgent.match(/OS (\d+)_(\d+)_?(\d+)?/);
                if (match) {
                    const iosVersion = parseInt(match[1], 10);
                    const iosMinor = parseInt(match[2], 10);

                    if (iosVersion < 16 || (iosVersion === 16 && iosMinor < 4)) {
                        console.warn(`⚠️ [Guest FCM] iOS ${match[1]}.${match[2]} - Web Push requires iOS 16.4+`);
                        return false;
                    }
                }

                // iOS PWA kontrolü
                if (!isPWA) {
                    console.warn('⚠️ [Guest FCM] iOS requires PWA mode for notifications');
                    return false;
                }

                console.log('✅ [Guest FCM] iOS 16.4+ PWA mode - supported');
            }

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

            // ✅ FCM CONFIG SIMPLIFY: Use global config from firebase-config.js
            const firebaseConfig = window.firebaseConfig;

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

            // ✅ İzin durumunu kontrol et - zaten verilmişse tekrar isteme
            let currentPermission = Notification.permission;
            
            if (currentPermission === 'granted') {
                console.log('✅ [Guest FCM] Permission already granted, skipping request');
            } else {
                // İzin verilmemişse iste
                console.log('🔔 [Guest FCM] Requesting notification permission...');
                
                // ✅ iOS için özel işlem - iosNotificationHandler kullan
                const isIOS = /iPhone|iPad|iPod/i.test(navigator.userAgent);
                if (isIOS && window.iosNotificationHandler) {
                    console.log('📱 [Guest FCM] Using iOS notification handler');
                    currentPermission = await window.iosNotificationHandler.requestPermission();
                } else {
                    // Normal tarayıcılar için
                    currentPermission = await Notification.requestPermission();
                }

                if (currentPermission !== 'granted') {
                    console.warn('⚠️ [Guest FCM] Permission denied');
                    return null;
                }
                
                console.log('✅ [Guest FCM] Permission granted');
            }

            // Get service worker registration
            const registration = await navigator.serviceWorker.ready;
            
            if (!registration) {
                console.error('❌ [Guest FCM] Service Worker not ready');
                return null;
            }

            console.log('✅ [Guest FCM] Service Worker ready');

            // ✅ FCM CONFIG SIMPLIFY: Use global config
            const vapidKey = window.firebaseConfig?.vapidKey;
            
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
