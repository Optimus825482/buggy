class DriverFCMSystem {
    constructor() {
        this.messaging = null;
        this.currentToken = null;
        this.isInitialized = false;
        this.retryCount = 0;
        this.maxRetries = 3;

        // ✅ FCM CONFIG SIMPLIFY: Use global config from firebase-config.js
        this.firebaseConfig = window.firebaseConfig || {
            // Fallback if firebase-config.js not loaded
            apiKey: "AIzaSyD5brCkHqSPVCtt0XJmUMqZizrjK_HX9dc",
            authDomain: "shuttle-call-835d9.firebaseapp.com",
            projectId: "shuttle-call-835d9",
            storageBucket: "shuttle-call-835d9.firebasestorage.app",
            messagingSenderId: "1044072191950",
            appId: "1:1044072191950:web:dc780e1832d3a4ee5afd9f",
            measurementId: "G-DCP7FTRM9Q",
            vapidKey: "BBrNGl2-VPA-iuLasrj8jpS2Sj2FrYr-FQq57GET6ofRV4QOljRwyLg--HMI-bV7m-lmdBk5NJxSyy3nVpNLzA4"
        };

        console.log('🔔 [DRIVER_FCM] System initialized');
    }

    /**
     * ========================================
     * STEP 1: INITIALIZE FIREBASE
     * ========================================
     */
    async initialize() {
        console.log('🚀 [DRIVER_FCM] Starting initialization...');

        try {
            // Check if Firebase SDK is loaded
            if (typeof firebase === 'undefined') {
                console.error('❌ [DRIVER_FCM] Firebase SDK not loaded!');
                this.showErrorAlert('Firebase SDK yüklenmedi. Lütfen sayfayı yenileyin.');
                return false;
            }

            // Check messaging support
            if (!firebase.messaging.isSupported()) {
                console.warn('⚠️ [DRIVER_FCM] FCM not supported on this browser');
                this.showErrorAlert('Bu tarayıcı bildirim sistemi desteklemiyor. Lütfen Chrome, Firefox veya Edge kullanın.');
                return false;
            }

            // Initialize Firebase App
            if (!firebase.apps.length) {
                firebase.initializeApp(this.firebaseConfig);
                console.log('✅ [DRIVER_FCM] Firebase app initialized');
            }

            // Get messaging instance
            this.messaging = firebase.messaging();
            console.log('✅ [DRIVER_FCM] Messaging instance created');

            // Setup foreground message listener
            this.setupForegroundListener();

            this.isInitialized = true;
            console.log('✅ [DRIVER_FCM] Initialization complete');

            return true;

        } catch (error) {
            console.error('❌ [DRIVER_FCM] Initialization failed:', error);
            this.showErrorAlert('Bildirim sistemi başlatılamadı: ' + error.message);
            return false;
        }
    }

    /**
     * ========================================
     * STEP 2: REQUEST NOTIFICATION PERMISSION
     * ========================================
     */
    async requestPermission() {
        console.log('🔐 [DRIVER_FCM] Requesting notification permission...');

        try {
            // ✅ iOS kontrolü
            const isIOS = /iPhone|iPad|iPod/i.test(navigator.userAgent);
            const isPWA = window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone === true;

            if (isIOS) {
                console.log('📱 [DRIVER_FCM] iOS detected');

                // iOS 16.4 kontrolü
                const match = navigator.userAgent.match(/OS (\d+)_(\d+)_?(\d+)?/);
                if (match) {
                    const iosVersion = parseInt(match[1], 10);
                    const iosMinor = parseInt(match[2], 10);

                    if (iosVersion < 16 || (iosVersion === 16 && iosMinor < 4)) {
                        console.warn(`⚠️ [DRIVER_FCM] iOS ${match[1]}.${match[2]} - Web Push requires iOS 16.4+`);
                        this.showErrorAlert(`iOS ${match[1]}.${match[2]} - Bildirimler için iOS 16.4+ gerekli`);
                        return false;
                    }
                }

                // PWA kontrolü
                if (!isPWA) {
                    console.warn('⚠️ [DRIVER_FCM] iOS requires PWA mode');
                    this.showErrorAlert('iOS\'ta bildirimler için uygulamayı Ana Ekrana eklemelisiniz');
                    return false;
                }

                console.log('✅ [DRIVER_FCM] iOS 16.4+ PWA mode - proceeding');

                // iOS için iosNotificationHandler kullan
                if (window.iosNotificationHandler) {
                    console.log('📱 [DRIVER_FCM] Using iOS notification handler');
                    const permission = await window.iosNotificationHandler.requestPermission();
                    return permission === 'granted';
                }
            }

            // Check current permission status
            const currentPermission = Notification.permission;
            console.log('📋 [DRIVER_FCM] Current permission:', currentPermission);

            if (currentPermission === 'denied') {
                console.error('❌ [DRIVER_FCM] Permission permanently denied');
                this.showPermissionDeniedAlert();
                return false;
            }

            if (currentPermission === 'granted') {
                console.log('✅ [DRIVER_FCM] Permission already granted');
                return true;
            }

            // Request permission
            console.log('📱 [DRIVER_FCM] Showing permission dialog...');
            const permission = await Notification.requestPermission();
            console.log('📋 [DRIVER_FCM] Permission result:', permission);

            if (permission === 'granted') {
                console.log('✅ [DRIVER_FCM] Permission granted!');
                return true;
            } else {
                console.warn('⚠️ [DRIVER_FCM] Permission denied by user');
                this.showPermissionDeniedAlert();
                return false;
            }

        } catch (error) {
            console.error('❌ [DRIVER_FCM] Permission request failed:', error);
            this.showErrorAlert('Bildirim izni istenemedi: ' + error.message);
            return false;
        }
    }

    /**
     * ========================================
     * STEP 3: REGISTER SERVICE WORKER
     * ========================================
     */
    async registerServiceWorker() {
        console.log('⚙️ [DRIVER_FCM] Registering service worker...');

        try {
            if (!('serviceWorker' in navigator)) {
                console.error('❌ [DRIVER_FCM] Service Worker not supported');
                return null;
            }

            // Register SW at root scope for maximum compatibility
            const registration = await navigator.serviceWorker.register(
                '/firebase-messaging-sw.js',
                { scope: '/' }
            );

            console.log('✅ [DRIVER_FCM] Service Worker registered:', registration.scope);

            // Wait for service worker to be ready
            await navigator.serviceWorker.ready;
            console.log('✅ [DRIVER_FCM] Service Worker ready');

            // Check if SW is active
            if (registration.active) {
                console.log('✅ [DRIVER_FCM] Service Worker is active');
            } else if (registration.installing) {
                console.log('⏳ [DRIVER_FCM] Service Worker is installing...');
            } else if (registration.waiting) {
                console.log('⏳ [DRIVER_FCM] Service Worker is waiting...');
            }

            return registration;

        } catch (error) {
            console.error('❌ [DRIVER_FCM] Service Worker registration failed:', error);
            this.showErrorAlert('Service Worker kaydedilemedi: ' + error.message);
            return null;
        }
    }

    /**
     * ========================================
     * STEP 4: GET FCM TOKEN
     * ========================================
     */
    async getToken(registration) {
        console.log('🎫 [DRIVER_FCM] Getting FCM token...');
        console.log('🔑 [DRIVER_FCM] VAPID Key:', this.firebaseConfig.vapidKey ? this.firebaseConfig.vapidKey.substring(0, 20) + '...' : 'MISSING!');

        try {
            if (!this.messaging) {
                console.error('❌ [DRIVER_FCM] Messaging not initialized');
                return null;
            }

            if (!registration) {
                console.error('❌ [DRIVER_FCM] No service worker registration');
                return null;
            }

            if (!this.firebaseConfig.vapidKey) {
                console.error('❌ [DRIVER_FCM] VAPID key is missing!');
                return null;
            }

            console.log('📤 [DRIVER_FCM] Requesting token from Firebase...');

            // ✅ Add timeout to prevent hanging
            const tokenPromise = this.messaging.getToken({
                vapidKey: this.firebaseConfig.vapidKey,
                serviceWorkerRegistration: registration
            });

            const timeoutPromise = new Promise((_, reject) =>
                setTimeout(() => reject(new Error('Token request timeout after 15s')), 15000)
            );

            const token = await Promise.race([tokenPromise, timeoutPromise]);

            if (token) {
                console.log('✅ [DRIVER_FCM] Token received:', token.substring(0, 20) + '...');
                this.currentToken = token;

                // Save to localStorage
                localStorage.setItem('fcm_token', token);
                localStorage.setItem('fcm_token_date', new Date().toISOString());

                return token;
            } else {
                console.error('❌ [DRIVER_FCM] No token received');
                return null;
            }

        } catch (error) {
            console.error('❌ [DRIVER_FCM] Token retrieval failed:', error);

            // Detailed error logging
            if (error.code) {
                console.error('   Error code:', error.code);
            }
            if (error.message) {
                console.error('   Error message:', error.message);
            }
            if (error.stack) {
                console.error('   Stack:', error.stack);
            }

            return null;
        }
    }

    /**
     * ========================================
     * STEP 5: REGISTER TOKEN WITH BACKEND
     * ========================================
     */
    async registerTokenWithBackend(token) {
        console.log('📤 [DRIVER_FCM] Registering token with backend...');

        try {
            const response = await fetch('/api/fcm/register-token', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include',
                body: JSON.stringify({ token: token })
            });

            console.log('📡 [DRIVER_FCM] Backend response status:', response.status);

            if (!response.ok) {
                const errorText = await response.text();
                console.error('❌ [DRIVER_FCM] Backend registration failed:', errorText);
                throw new Error(`Server error: ${response.status}`);
            }

            const data = await response.json();
            console.log('📦 [DRIVER_FCM] Backend response:', data);

            if (data.success) {
                console.log('✅ [DRIVER_FCM] Token registered with backend successfully');
                return true;
            } else {
                console.error('❌ [DRIVER_FCM] Backend returned error:', data.message);
                return false;
            }

        } catch (error) {
            console.error('❌ [DRIVER_FCM] Backend registration error:', error);

            // Retry logic
            if (this.retryCount < this.maxRetries) {
                this.retryCount++;
                console.log(`🔄 [DRIVER_FCM] Retrying (${this.retryCount}/${this.maxRetries})...`);
                await new Promise(resolve => setTimeout(resolve, 2000));
                return await this.registerTokenWithBackend(token);
            }

            return false;
        }
    }

    /**
     * ========================================
     * COMPLETE SETUP - ALL STEPS
     * ========================================
     */
    async setupComplete() {
        console.log('🎬 [DRIVER_FCM] Starting complete setup...');
        console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');

        try {
            // STEP 1: Initialize Firebase
            console.log('📍 STEP 1/5: Initializing Firebase...');
            const initialized = await this.initialize();
            if (!initialized) {
                console.error('❌ Setup failed at STEP 1');
                return false;
            }

            // STEP 2: Request Permission
            console.log('📍 STEP 2/5: Requesting permission...');
            const permissionGranted = await this.requestPermission();
            if (!permissionGranted) {
                console.error('❌ Setup failed at STEP 2');
                return false;
            }

            // STEP 3: Register Service Worker
            console.log('📍 STEP 3/5: Registering service worker...');
            const registration = await this.registerServiceWorker();
            if (!registration) {
                console.error('❌ Setup failed at STEP 3');
                return false;
            }

            // STEP 4: Get FCM Token
            console.log('📍 STEP 4/5: Getting FCM token...');
            const token = await this.getToken(registration);
            if (!token) {
                console.error('❌ Setup failed at STEP 4');
                return false;
            }

            // STEP 5: Register with Backend
            console.log('📍 STEP 5/5: Registering with backend...');
            const backendSuccess = await this.registerTokenWithBackend(token);
            if (!backendSuccess) {
                console.warn('⚠️ Backend registration failed, but token is saved locally');
                // Don't fail - driver can still receive notifications
            }

            console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
            console.log('✅ [DRIVER_FCM] COMPLETE SETUP SUCCESSFUL!');
            console.log('🔔 Sürücü artık bildirim alabilir');
            console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');

            // Show success message
            this.showSuccessAlert();

            return true;

        } catch (error) {
            console.error('❌ [DRIVER_FCM] Setup failed:', error);
            console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
            return false;
        }
    }

    /**
     * ========================================
     * FOREGROUND MESSAGE LISTENER
     * ========================================
     */
    setupForegroundListener() {
        if (!this.messaging) return;

        console.log('👂 [DRIVER_FCM] Setting up foreground message listener...');

        this.messaging.onMessage((payload) => {
            console.log('📨 [DRIVER_FCM] FOREGROUND MESSAGE RECEIVED!');
            console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
            console.log('📦 Payload:', payload);
            console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');

            // Show browser notification
            this.showBrowserNotification(payload);

            // Play sound
            this.playNotificationSound();

            // ✅ Show dialog with notification details
            this.showNotificationDialog(payload);

            // Dispatch custom event for dashboard to handle
            const event = new CustomEvent('fcm-notification', {
                detail: payload
            });
            window.dispatchEvent(event);

            // If it's a new request, trigger dashboard refresh
            if (payload.data?.type === 'new_request') {
                console.log('🆕 [DRIVER_FCM] New request notification - refreshing dashboard');

                // Force refresh with slight delay to ensure backend has processed
                setTimeout(() => {
                    if (window.DriverDashboard) {
                        console.log('🔄 [DRIVER_FCM] Refreshing pending requests...');
                        if (typeof window.DriverDashboard.loadPendingRequests === 'function') {
                            window.DriverDashboard.loadPendingRequests();
                        }
                        if (typeof window.DriverDashboard.loadDriverData === 'function') {
                            window.DriverDashboard.loadDriverData();
                        }
                    }
                }, 500);
            }
        });

        console.log('✅ [DRIVER_FCM] Foreground listener active');
    }

    /**
     * ========================================
     * SHOW BROWSER NOTIFICATION
     * ========================================
     */
    showBrowserNotification(payload) {
        const title = payload.notification?.title || 'Shuttle Call';
        const options = {
            body: payload.notification?.body || 'Yeni bildirim',
            icon: '/static/icons/Icon-192.png',
            badge: '/static/icons/Icon-96.png',
            tag: payload.data?.type || 'notification',
            requireInteraction: payload.data?.type === 'new_request',
            vibrate: [200, 100, 200, 100, 200],
            data: payload.data
        };

        if (payload.notification?.image) {
            options.image = payload.notification.image;
        }

        new Notification(title, options);
    }

    /**
     * ========================================
     * PLAY NOTIFICATION SOUND
     * ========================================
     */
    playNotificationSound() {
        try {
            const audio = new Audio('/static/sounds/notification.mp3');
            audio.volume = 0.7;
            audio.play().catch(err => {
                console.warn('⚠️ [DRIVER_FCM] Sound play failed:', err);
            });
        } catch (error) {
            console.warn('⚠️ [DRIVER_FCM] Sound error:', error);
        }
    }

    /**
     * ========================================
     * SHOW NOTIFICATION DIALOG
     * ========================================
     */
    showNotificationDialog(payload) {
        try {
            const title = payload.notification?.title || 'Yeni Bildirim';
            const body = payload.notification?.body || '';
            const data = payload.data || {};

            // Format notification content
            let content = `<div style="text-align: left; padding: 10px;">`;
            content += `<p style="font-size: 16px; font-weight: bold; margin-bottom: 10px;">${body}</p>`;

            // Add detailed info if available
            if (data.location_name) {
                content += `<p style="margin: 8px 0;"><strong>📍 Lokasyon:</strong> ${data.location_name}</p>`;
            }
            if (data.room_number) {
                content += `<p style="margin: 8px 0;"><strong>🏨 Oda:</strong> ${data.room_number}</p>`;
            }
            if (data.guest_name) {
                content += `<p style="margin: 8px 0;"><strong>👤 Misafir:</strong> ${data.guest_name}</p>`;
            }
            if (data.phone) {
                content += `<p style="margin: 8px 0;"><strong>📞 Telefon:</strong> ${data.phone}</p>`;
            }
            if (data.notes) {
                content += `<p style="margin: 8px 0;"><strong>📝 Notlar:</strong> ${data.notes}</p>`;
            }

            content += `</div>`;

            // Create dialog overlay
            const overlay = document.createElement('div');
            overlay.id = 'fcm-dialog-overlay';
            overlay.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0, 0, 0, 0.7);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 10000;
                animation: fadeIn 0.3s ease-out;
            `;

            // Create dialog
            const dialog = document.createElement('div');
            dialog.style.cssText = `
                background: white;
                border-radius: 12px;
                padding: 24px;
                max-width: 500px;
                width: 90%;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
                animation: slideInDialog 0.3s ease-out;
            `;

            dialog.innerHTML = `
                <div style="text-align: center; margin-bottom: 20px;">
                    <h2 style="margin: 0; color: #2563eb; font-size: 24px;">${title}</h2>
                </div>
                ${content}
                <div style="text-align: center; margin-top: 20px;">
                    <button id="fcm-dialog-close" style="
                        background: #2563eb;
                        color: white;
                        border: none;
                        border-radius: 8px;
                        padding: 12px 32px;
                        font-size: 16px;
                        font-weight: bold;
                        cursor: pointer;
                        box-shadow: 0 2px 8px rgba(37, 99, 235, 0.3);
                    ">Tamam</button>
                </div>
            `;

            overlay.appendChild(dialog);
            document.body.appendChild(overlay);

            // Close handlers
            const closeDialog = () => {
                overlay.style.animation = 'fadeOut 0.3s ease-out';
                setTimeout(() => {
                    if (overlay.parentNode) {
                        overlay.parentNode.removeChild(overlay);
                    }
                }, 300);
            };

            document.getElementById('fcm-dialog-close').addEventListener('click', closeDialog);
            overlay.addEventListener('click', (e) => {
                if (e.target === overlay) {
                    closeDialog();
                }
            });

            // Auto-close after 10 seconds
            setTimeout(closeDialog, 10000);

            console.log('✅ [DRIVER_FCM] Dialog shown');

        } catch (error) {
            console.error('❌ [DRIVER_FCM] Dialog error:', error);
        }
    }

    /**
     * ========================================
     * TEST NOTIFICATION
     * ========================================
     */
    async sendTestNotification() {
        console.log('🧪 [DRIVER_FCM] Sending test notification...');

        try {
            const response = await fetch('/api/fcm/test-notification', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include',
                body: JSON.stringify({
                    title: '🧪 Test Bildirimi',
                    body: 'FCM sistemi çalışıyor! Yeni talepler bu şekilde gelecek.'
                })
            });

            const data = await response.json();

            if (data.success) {
                console.log('✅ [DRIVER_FCM] Test notification sent');
                alert('✅ Test bildirimi gönderildi! Birkaç saniye içinde gelecek.');
                return true;
            } else {
                console.error('❌ [DRIVER_FCM] Test failed:', data.message);
                alert('❌ Test bildirimi gönderilemedi: ' + data.message);
                return false;
            }

        } catch (error) {
            console.error('❌ [DRIVER_FCM] Test error:', error);
            alert('❌ Test hatası: ' + error.message);
            return false;
        }
    }

    /**
     * ========================================
     * UI ALERTS
     * ========================================
     */
    showSuccessAlert() {
        const alert = document.createElement('div');
        alert.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: linear-gradient(135deg, #27AE60 0%, #229954 100%);
            color: white;
            padding: 1.5rem;
            border-radius: 12px;
            box-shadow: 0 8px 24px rgba(39, 174, 96, 0.3);
            z-index: 10000;
            max-width: 400px;
            animation: slideIn 0.3s ease-out;
        `;

        alert.innerHTML = `
            <div style="display: flex; align-items: start; gap: 1rem;">
                <div style="font-size: 2rem;">✅</div>
                <div>
                    <div style="font-weight: 700; font-size: 1.1rem; margin-bottom: 0.5rem;">
                        Bildirimler Aktif!
                    </div>
                    <div style="font-size: 0.9rem; opacity: 0.95;">
                        Yeni talepler anında size ulaşacak.
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(alert);

        setTimeout(() => {
            alert.style.animation = 'slideOut 0.3s ease-in';
            setTimeout(() => alert.remove(), 300);
        }, 5000);
    }

    showPermissionDeniedAlert() {
        const alert = document.createElement('div');
        alert.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: linear-gradient(135deg, #E74C3C 0%, #C0392B 100%);
            color: white;
            padding: 1.5rem;
            border-radius: 12px;
            box-shadow: 0 8px 24px rgba(231, 76, 60, 0.3);
            z-index: 10000;
            max-width: 400px;
        `;

        alert.innerHTML = `
            <div style="display: flex; align-items: start; gap: 1rem;">
                <div style="font-size: 2rem;">⚠️</div>
                <div>
                    <div style="font-weight: 700; font-size: 1.1rem; margin-bottom: 0.5rem;">
                        Bildirim İzni Gerekli
                    </div>
                    <div style="font-size: 0.9rem; opacity: 0.95; margin-bottom: 1rem;">
                        Yeni talepleri alabilmek için bildirim iznini açmanız gerekiyor.
                    </div>
                    <div style="font-size: 0.8rem; opacity: 0.9;">
                        <strong>Nasıl açarım?</strong><br>
                        1. Adres çubuğundaki 🔒 simgesine tıklayın<br>
                        2. "Bildirimler" → "İzin ver" seçin<br>
                        3. Sayfayı yenileyin
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(alert);
    }

    showErrorAlert(message) {
        console.error('❌ [DRIVER_FCM] Error alert:', message);
        // You can show a modal or toast here
    }
}

// ============================================================================
// AUTO-INITIALIZE ON PAGE LOAD
// ============================================================================
window.driverFCM = new DriverFCMSystem();

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', async () => {
    // Only run on driver pages
    if (!window.location.pathname.includes('/driver')) {
        console.log('ℹ️ [DRIVER_FCM] Not a driver page, skipping initialization');
        return;
    }

    console.log('🏁 [DRIVER_FCM] DOM ready, starting auto-initialization...');

    // Wait a bit for page to fully load
    await new Promise(resolve => setTimeout(resolve, 1000));

    // Check if token already exists
    const savedToken = localStorage.getItem('fcm_token');
    const tokenDate = localStorage.getItem('fcm_token_date');

    if (savedToken && tokenDate) {
        // Check if token is less than 7 days old
        const tokenAge = Date.now() - new Date(tokenDate).getTime();
        const sevenDays = 7 * 24 * 60 * 60 * 1000;

        if (tokenAge < sevenDays) {
            console.log('✅ [DRIVER_FCM] Valid token found in localStorage');
            console.log('📅 [DRIVER_FCM] Token age:', Math.floor(tokenAge / (24 * 60 * 60 * 1000)), 'days');

            // Re-register with backend to ensure it's still valid
            window.driverFCM.currentToken = savedToken;
            await window.driverFCM.initialize();
            await window.driverFCM.registerTokenWithBackend(savedToken);

            console.log('✅ [DRIVER_FCM] Existing token re-registered');
            return;
        } else {
            console.log('⏰ [DRIVER_FCM] Token is old (>7 days), refreshing...');
        }
    } else {
        console.log('ℹ️ [DRIVER_FCM] No saved token found');
    }

    // Run complete setup
    console.log('🚀 [DRIVER_FCM] Starting fresh setup...');
    const success = await window.driverFCM.setupComplete();

    if (success) {
        console.log('🎉 [DRIVER_FCM] Auto-initialization completed successfully');
    } else {
        console.error('❌ [DRIVER_FCM] Auto-initialization failed');
    }
});

// Add CSS animations - Unique variable name to avoid conflicts
if (!document.getElementById('driver-fcm-animations')) {
    const fcmAnimationStyle = document.createElement('style');
    fcmAnimationStyle.id = 'driver-fcm-animations';
    fcmAnimationStyle.textContent = `
        @keyframes slideIn {
            from {
                transform: translateX(400px);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }

        @keyframes slideOut {
            from {
                transform: translateX(0);
                opacity: 1;
            }
            to {
                transform: translateX(400px);
                opacity: 0;
            }
        }

        @keyframes fadeIn {
            from {
                opacity: 0;
            }
            to {
                opacity: 1;
            }
        }

        @keyframes fadeOut {
            from {
                opacity: 1;
            }
            to {
                opacity: 0;
            }
        }

        @keyframes slideInDialog {
            from {
                transform: scale(0.8) translateY(-50px);
                opacity: 0;
            }
            to {
                transform: scale(1) translateY(0);
                opacity: 1;
            }
        }
    `;
    document.head.appendChild(fcmAnimationStyle);
}

/**
 * ========================================
 * TOKEN REFRESH HEARTBEAT
 * ========================================
 */
function startTokenRefreshHeartbeat() {
    // Re-register token every 10 minutes to ensure backend has it
    setInterval(async () => {
        console.log('💓 [DRIVER_FCM] Token refresh heartbeat...');

        const savedToken = localStorage.getItem('fcm_token');
        if (savedToken && window.driverFCM) {
            console.log('🔄 [DRIVER_FCM] Re-registering token with backend...');
            const success = await window.driverFCM.registerTokenWithBackend(savedToken);
            if (success) {
                console.log('✅ [DRIVER_FCM] Token re-registered successfully');
            } else {
                console.warn('⚠️ [DRIVER_FCM] Token re-registration failed');
            }
        }
    }, 10 * 60 * 1000); // Every 10 minutes
}

// Start heartbeat when driver logs in
if (document.body.dataset.userId) {
    console.log('💓 [DRIVER_FCM] Starting token refresh heartbeat (every 10 min)');
    startTokenRefreshHeartbeat();
}

console.log('📦 [DRIVER_FCM] Module loaded and ready');
