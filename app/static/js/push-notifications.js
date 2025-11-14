/**
 * Push Notifications Manager
 * Shuttle Call - Progressive Web App
 */

class PushNotificationManager {
    constructor() {
        this.registration = null;
        this.subscription = null;
        this.publicKey = null; // Server will provide this
        this.isSupported = 'Notification' in window && 'PushManager' in window;
        this.permission = this.isSupported ? Notification.permission : 'denied';
        this.init();
    }

    async init() {
        if (!this.isSupported) {
            console.warn('[Push] Push notifications not supported');
            return;
        }

        try {
            // Get service worker registration
            if ('serviceWorker' in navigator) {
                this.registration = await navigator.serviceWorker.ready;
                // Service worker ready

                // Check for existing subscription
                this.subscription = await this.registration.pushManager.getSubscription();
                if (this.subscription) {
                    console.log('[Push] Existing subscription found');
                }
            }
        } catch (error) {
            console.error('[Push] Initialization error:', error);
        }
    }

    /**
     * Request notification permission
     * Note: Must be called from a user gesture (click, touch, etc.)
     */
    async requestPermission() {
        if (!this.isSupported) {
            console.warn('[Push] Notifications not supported');
            return 'denied';
        }

        if (this.permission === 'granted') {
            console.log('[Push] Permission already granted');
            return 'granted';
        }

        try {
            // Edge/Chrome requires synchronous call in user gesture
            // Use promise-based API for better compatibility
            const permission = await new Promise((resolve, reject) => {
                const permissionPromise = Notification.requestPermission();
                
                if (permissionPromise) {
                    permissionPromise.then(resolve).catch(reject);
                } else {
                    // Fallback for older browsers
                    Notification.requestPermission(resolve);
                }
            });
            
            this.permission = permission;
            console.log('[Push] Permission result:', this.permission);

            if (this.permission === 'granted') {
                // Subscribe to push notifications
                await this.subscribe();
            }

            return this.permission;
        } catch (error) {
            console.error('[Push] Permission request error:', error);
            this.permission = 'denied';
            return 'denied';
        }
    }

    /**
     * Subscribe to push notifications
     */
    async subscribe() {
        if (!this.isSupported || this.permission !== 'granted') {
            console.warn('[Push] Cannot subscribe - not supported or not permitted');
            return null;
        }

        try {
            if (!this.registration) {
                await this.init();
            }

            // Check if already subscribed
            if (this.subscription) {
                console.log('[Push] Already subscribed');
                return this.subscription;
            }

            // Get public key from server
            if (!this.publicKey) {
                await this.fetchPublicKey();
            }

            // Subscribe
            this.subscription = await this.registration.pushManager.subscribe({
                userVisibleOnly: true,
                applicationServerKey: this.urlBase64ToUint8Array(this.publicKey)
            });

            console.log('[Push] Subscribed successfully');

            // Send subscription to server
            await this.sendSubscriptionToServer(this.subscription);

            return this.subscription;
        } catch (error) {
            console.error('[Push] Subscription error:', error);
            return null;
        }
    }

    /**
     * Unsubscribe from push notifications
     */
    async unsubscribe() {
        if (!this.subscription) {
            console.log('[Push] No active subscription');
            return true;
        }

        try {
            // Unsubscribe
            await this.subscription.unsubscribe();
            console.log('[Push] Unsubscribed successfully');

            // Notify server
            await this.removeSubscriptionFromServer();

            this.subscription = null;
            return true;
        } catch (error) {
            console.error('[Push] Unsubscribe error:', error);
            return false;
        }
    }

    /**
     * Fetch public key from server
     */
    async fetchPublicKey() {
        try {
            const response = await fetch('/api/push/vapid-public-key');
            const data = await response.json();
            this.publicKey = data.public_key;
            console.log('[Push] Public key fetched:', this.publicKey);
        } catch (error) {
            console.error('[Push] Error fetching public key:', error);
            // Use a default key for development (should be replaced with actual key)
            this.publicKey = 'BNxZ8j9gVwXqFGqcqvqkQqKQqKQqKQqKQqKQqKQqKQqKQqKQqKQqKQqKQqKQqKQqKQqKQqKQqKQqKQqKQqKQqKQ=';
        }
    }

    /**
     * Send subscription to server
     */
    async sendSubscriptionToServer(subscription) {
        try {
            const response = await fetch('/api/push/subscribe', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ subscription: subscription })
            });

            if (response.ok) {
                const data = await response.json();
                console.log('[Push] Subscription sent to server:', data);
            } else {
                const error = await response.json();
                console.error('[Push] Failed to send subscription to server:', error);
            }
        } catch (error) {
            console.error('[Push] Error sending subscription:', error);
        }
    }

    /**
     * Remove subscription from server
     */
    async removeSubscriptionFromServer() {
        try {
            const response = await fetch('/api/push/unsubscribe', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(this.subscription)
            });

            if (response.ok) {
                console.log('[Push] Subscription removed from server');
            }
        } catch (error) {
            console.error('[Push] Error removing subscription:', error);
        }
    }

    /**
     * Show a local notification (doesn't require push)
     */
    async showNotification(title, options = {}) {
        if (!this.isSupported) {
            console.warn('[Push] Notifications not supported');
            return;
        }

        if (this.permission !== 'granted') {
            await this.requestPermission();
            if (this.permission !== 'granted') {
                return;
            }
        }

        try {
            const defaultOptions = {
                body: '',
                icon: '/static/icons/Icon-192.png',
                badge: '/static/icons/Icon-96.png',
                vibrate: [200, 100, 200],
                tag: 'buggy-call-notification',
                requireInteraction: false,
                data: {
                    timestamp: Date.now()
                }
            };

            const notificationOptions = { ...defaultOptions, ...options };

            if (this.registration) {
                await this.registration.showNotification(title, notificationOptions);
            } else {
                new Notification(title, notificationOptions);
            }

            console.log('[Push] Notification shown:', title);
        } catch (error) {
            console.error('[Push] Error showing notification:', error);
        }
    }

    /**
     * Show notification for new buggy request
     */
    async notifyNewRequest(request) {
        await this.showNotification('Yeni Shuttle Talebi', {
            body: `${request.location_name} konumundan yeni bir talep var`,
            icon: '/static/icons/Icon-192.png',
            tag: `request-${request.id}`,
            data: {
                type: 'new_request',
                requestId: request.id,
                url: '/driver/dashboard'
            },
            actions: [
                {
                    action: 'view',
                    title: 'Görüntüle',
                    icon: '/static/icons/Icon-96.png'
                },
                {
                    action: 'dismiss',
                    title: 'Kapat'
                }
            ]
        });
    }

    /**
     * Show notification for request status change
     */
    async notifyStatusChange(request, newStatus) {
        const statusMessages = {
            'accepted': 'Talebiniz kabul edildi',
            'in_progress': 'Shuttle yolda',
            'completed': 'Talep tamamlandı',
            'cancelled': 'Talep iptal edildi'
        };

        await this.showNotification('Talep Durumu Güncellendi', {
            body: statusMessages[newStatus] || 'Talep durumunuz değişti',
            icon: '/static/icons/Icon-192.png',
            tag: `request-${request.id}`,
            data: {
                type: 'status_change',
                requestId: request.id,
                status: newStatus
            }
        });
    }

    /**
     * Get notification permission status
     */
    getPermissionStatus() {
        return {
            isSupported: this.isSupported,
            permission: this.permission,
            isSubscribed: !!this.subscription
        };
    }

    /**
     * Convert URL-safe base64 to Uint8Array
     */
    urlBase64ToUint8Array(base64String) {
        const padding = '='.repeat((4 - base64String.length % 4) % 4);
        const base64 = (base64String + padding)
            .replace(/\-/g, '+')
            .replace(/_/g, '/');

        const rawData = window.atob(base64);
        const outputArray = new Uint8Array(rawData.length);

        for (let i = 0; i < rawData.length; ++i) {
            outputArray[i] = rawData.charCodeAt(i);
        }

        return outputArray;
    }

    /**
     * Test push notification
     */
    async testNotification() {
        await this.showNotification('Test Bildirimi', {
            body: 'Bu bir test bildirimidir. Push bildirimler çalışıyor!',
            icon: '/static/icons/Icon-192.png',
            badge: '/static/icons/Icon-96.png'
        });
    }
}

// Create global instance
const pushNotifications = new PushNotificationManager();

// Auto-request permission when user interacts with the page (if not already decided)
let interactionHandled = false;
const handleFirstInteraction = () => {
    if (!interactionHandled && pushNotifications.permission === 'default') {
        interactionHandled = true;
        // Don't request immediately, wait for a more appropriate moment
        console.log('[Push] User interaction detected, ready to request permission');
    }
};

document.addEventListener('click', handleFirstInteraction, { once: true });
document.addEventListener('touchstart', handleFirstInteraction, { once: true });

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = pushNotifications;
}

// Push notification manager loaded
