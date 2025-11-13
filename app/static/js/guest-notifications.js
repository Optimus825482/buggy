/**
 * Guest Notification Manager
 * Guest kullanıcıları için push notification yönetimi
 * Powered by Erkan ERDEM
 */

class GuestNotificationManager {
    constructor() {
        this.fcmToken = null;
        this.requestId = null;
        this.isSupported = false;
        this.messaging = null;
    }

    /**
     * Initialize
     */
    async init() {
        try {
            // iOS kontrolü
            const isIOS = /iPhone|iPad|iPod/i.test(navigator.userAgent);
            const isPWA = window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone === true;

            // iOS'ta PWA değilse bildirim desteklenmiyor
            if (isIOS && !isPWA) {
                console.log('[Guest Notifications] iOS - PWA required for notifications');
                this.isSupported = false;
                return false;
            }

            // Firebase kontrolü
            if (typeof firebase === 'undefined') {
                console.warn('[Guest Notifications] Firebase SDK not loaded');
                this.isSupported = false;
                return false;
            }

            // Messaging desteği kontrolü
            if (!firebase.messaging.isSupported()) {
                console.warn('[Guest Notifications] FCM not supported');
                this.isSupported = false;
                return false;
            }

            this.isSupported = true;

            // Firebase'i başlat (eğer başlatılmamışsa)
            if (!firebase.apps.length) {
                firebase.initializeApp({
                    apiKey: "AIzaSyDyjVSgW8j4wY-wF0G9uUJpY_Iv-5uQx1I",
                    authDomain: "buggy-call-a5785.firebaseapp.com",
                    projectId: "buggy-call-a5785",
                    storageBucket: "buggy-call-a5785.firebasestorage.app",
                    messagingSenderId: "141355725901",
                    appId: "1:141355725901:web:a2c08a67a489ba82ca1804"
                });
            }

            this.messaging = firebase.messaging();
            console.log('[Guest Notifications] Initialized successfully');

            // Foreground mesajları dinle
            this.setupForegroundListener();

            return true;

        } catch (error) {
            console.error('[Guest Notifications] Init error:', error);
            this.isSupported = false;
            return false;
        }
    }

    /**
     * Bildirim izni iste ve token al
     */
    async requestPermissionAndGetToken(requestId) {
        try {
            if (!this.isSupported) {
                console.log('[Guest Notifications] Not supported');
                return null;
            }

            this.requestId = requestId;

            // iOS özel kontrolü
            if (window.iosNotificationHandler && window.iosNotificationHandler.isIOSDevice()) {
                const permission = await window.iosNotificationHandler.requestPermission();
                if (permission !== 'granted') {
                    return null;
                }
            } else {
                // Normal bildirim izni
                const permission = await Notification.requestPermission();
                if (permission !== 'granted') {
                    console.log('[Guest Notifications] Permission denied');
                    return null;
                }
            }

            console.log('[Guest Notifications] Permission granted');

            // Service Worker kaydı
            const registration = await this.registerServiceWorker();
            if (!registration) {
                console.error('[Guest Notifications] Service Worker registration failed');
                return null;
            }

            // FCM token al
            const token = await this.messaging.getToken({
                vapidKey: 'BB2-xRCo75G7j3UVqhbeUjv5G55uTN11XCnMt2iZD0w718faVYUZpsGxfAGzqM5Eftw8xN_PVee6X7jRAgoFeAY',
                serviceWorkerRegistration: registration
            });

            if (token) {
                console.log('[Guest Notifications] Token received:', token.substring(0, 20) + '...');
                this.fcmToken = token;

                // Token'ı backend'e kaydet
                await this.registerTokenToBackend(token, requestId);

                return token;
            } else {
                console.warn('[Guest Notifications] No token received');
                return null;
            }

        } catch (error) {
            console.error('[Guest Notifications] Error getting token:', error);
            return null;
        }
    }

    /**
     * Service Worker kaydet
     */
    async registerServiceWorker() {
        try {
            if (!('serviceWorker' in navigator)) {
                console.error('[Guest Notifications] Service Worker not supported');
                return null;
            }

            // Firebase Messaging Service Worker'ı kaydet
            const registration = await navigator.serviceWorker.register('/static/firebase-messaging-sw.js');
            console.log('[Guest Notifications] Service Worker registered');

            // Service Worker'ın hazır olmasını bekle
            await navigator.serviceWorker.ready;

            return registration;

        } catch (error) {
            console.error('[Guest Notifications] Service Worker registration error:', error);
            return null;
        }
    }

    /**
     * Token'ı backend'e kaydet
     */
    async registerTokenToBackend(token, requestId) {
        try {
            const response = await fetch('/api/guest/register-fcm-token', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    token: token,
                    request_id: requestId
                })
            });

            const data = await response.json();

            if (data.success) {
                console.log('[Guest Notifications] Token registered to backend');
                
                // Local storage'a kaydet
                localStorage.setItem('guest_fcm_token', token);
                localStorage.setItem('guest_fcm_token_date', new Date().toISOString());
                
                return true;
            } else {
                console.error('[Guest Notifications] Token registration failed:', data.message);
                return false;
            }

        } catch (error) {
            console.error('[Guest Notifications] Backend registration error:', error);
            return false;
        }
    }

    /**
     * Foreground mesajları dinle
     */
    setupForegroundListener() {
        if (!this.messaging) return;

        this.messaging.onMessage((payload) => {
            console.log('[Guest Notifications] Foreground message received:', payload);

            // Bildirim göster
            this.showForegroundNotification(payload);

            // Özel event tetikle (status güncellemesi için)
            const event = new CustomEvent('guest-fcm-message', { detail: payload });
            window.dispatchEvent(event);
        });
    }

    /**
     * Foreground bildirim göster
     */
    showForegroundNotification(payload) {
        const title = payload.notification?.title || 'Shuttle Call';
        const options = {
            body: payload.notification?.body || 'Yeni bildirim',
            icon: payload.notification?.icon || '/static/icons/Icon-192.png',
            badge: '/static/icons/Icon-96.png',
            tag: payload.data?.type || 'guest-notification',
            data: payload.data || {},
            requireInteraction: payload.data?.priority === 'high',
            vibrate: [200, 100, 200, 100, 200]
        };

        // Tarayıcı bildirimi göster
        if (Notification.permission === 'granted') {
            new Notification(title, options);
        }

        // Ses çal
        if (payload.data?.type === 'request_accepted') {
            this.playNotificationSound();
        }
    }

    /**
     * Bildirim sesi çal
     */
    playNotificationSound() {
        try {
            // Web Audio API ile ses oluştur
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            
            // Başarı melodisi (C-E-G akor)
            const frequencies = [523.25, 659.25, 783.99];
            
            frequencies.forEach((freq, index) => {
                setTimeout(() => {
                    const oscillator = audioContext.createOscillator();
                    const gainNode = audioContext.createGain();
                    
                    oscillator.connect(gainNode);
                    gainNode.connect(audioContext.destination);
                    
                    oscillator.frequency.value = freq;
                    oscillator.type = 'sine';
                    
                    gainNode.gain.setValueAtTime(0, audioContext.currentTime);
                    gainNode.gain.linearRampToValueAtTime(0.3, audioContext.currentTime + 0.01);
                    gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.4);
                    
                    oscillator.start(audioContext.currentTime);
                    oscillator.stop(audioContext.currentTime + 0.4);
                }, index * 150);
            });

            // Vibrate
            if (window.navigator && window.navigator.vibrate) {
                window.navigator.vibrate([200, 100, 200, 100, 200]);
            }

        } catch (error) {
            console.warn('[Guest Notifications] Sound play error:', error);
        }
    }

    /**
     * Bildirim durumunu kontrol et
     */
    getStatus() {
        return {
            isSupported: this.isSupported,
            permission: this.isSupported ? Notification.permission : 'denied',
            hasToken: !!this.fcmToken
        };
    }
}

// Global instance
window.guestNotificationManager = new GuestNotificationManager();

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = GuestNotificationManager;
}

console.log('[Guest Notifications] Manager loaded');
