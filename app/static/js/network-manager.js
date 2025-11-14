/**
 * Network Manager - Handle Online/Offline Status and Sync
 * Shuttle Call - Progressive Web App
 */

class NetworkManager {
    constructor() {
        this.isOnline = navigator.onLine;
        this.syncInProgress = false;
        this.serviceWorker = null;
        this.listeners = {
            online: [],
            offline: [],
            syncComplete: []
        };
        this.init();
    }

    init() {
        // Listen for online/offline events
        window.addEventListener('online', () => this.handleOnline());
        window.addEventListener('offline', () => this.handleOffline());

        // Check connection on load
        this.checkConnection();

        // Periodic connection check
        setInterval(() => this.checkConnection(), 30000); // Every 30 seconds

        // Initialize Service Worker communication
        this.initServiceWorker();

        // Network manager initialized
    }

    /**
     * Initialize Service Worker communication
     */
    async initServiceWorker() {
        if ('serviceWorker' in navigator) {
            try {
                const registration = await navigator.serviceWorker.ready;
                this.serviceWorker = registration.active;

                // Listen for messages from Service Worker
                navigator.serviceWorker.addEventListener('message', (event) => {
                    this.handleServiceWorkerMessage(event.data);
                });

                // Service Worker communication initialized

                // Get initial network status from SW
                const status = await this.getServiceWorkerNetworkStatus();
                // SW network status checked
            } catch (error) {
                console.error('[Network] Service Worker initialization error:', error);
            }
        }
    }

    /**
     * Handle messages from Service Worker
     */
    handleServiceWorkerMessage(message) {
        const { type, data } = message;

        switch (type) {
            case 'NETWORK_STATUS':
                console.log('[Network] SW network status update:', data.online);
                if (data.online !== this.isOnline) {
                    this.isOnline = data.online;
                    this.updateConnectionUI(data.online);
                }
                break;

            case 'SYNC_COMPLETE':
                console.log('[Network] SW sync complete:', data.results);
                this.listeners.syncComplete.forEach(callback => callback(data.results));
                
                if (data.results.delivered > 0) {
                    this.showNotification(
                        'Bildirimler Senkronize Edildi',
                        `${data.results.delivered} bildirim başarıyla senkronize edildi.`,
                        'success'
                    );
                }
                break;

            default:
                console.log('[Network] Unknown SW message:', type);
        }
    }

    /**
     * Get network status from Service Worker
     */
    async getServiceWorkerNetworkStatus() {
        if (!this.serviceWorker) return null;

        return new Promise((resolve) => {
            const messageChannel = new MessageChannel();
            
            messageChannel.port1.onmessage = (event) => {
                resolve(event.data);
            };

            this.serviceWorker.postMessage(
                { action: 'getNetworkStatus' },
                [messageChannel.port2]
            );

            // Timeout after 5 seconds
            setTimeout(() => resolve(null), 5000);
        });
    }

    /**
     * Get queued notifications from Service Worker
     */
    async getQueuedNotifications() {
        if (!this.serviceWorker) return [];

        return new Promise((resolve) => {
            const messageChannel = new MessageChannel();
            
            messageChannel.port1.onmessage = (event) => {
                resolve(event.data || []);
            };

            this.serviceWorker.postMessage(
                { action: 'getQueuedNotifications' },
                [messageChannel.port2]
            );

            // Timeout after 5 seconds
            setTimeout(() => resolve([]), 5000);
        });
    }

    /**
     * Trigger manual sync via Service Worker
     */
    async triggerSync() {
        if (!this.serviceWorker) {
            console.warn('[Network] Service Worker not available');
            return;
        }

        try {
            this.serviceWorker.postMessage({ action: 'syncNow' });
            console.log('[Network] Manual sync triggered');
        } catch (error) {
            console.error('[Network] Error triggering sync:', error);
        }
    }

    /**
     * Queue action in Service Worker
     */
    async queueAction(actionType, actionData) {
        if (!this.serviceWorker) {
            console.warn('[Network] Service Worker not available');
            return false;
        }

        try {
            this.serviceWorker.postMessage({
                action: 'queueAction',
                data: {
                    type: actionType,
                    data: actionData
                }
            });
            console.log('[Network] Action queued:', actionType);
            return true;
        } catch (error) {
            console.error('[Network] Error queueing action:', error);
            return false;
        }
    }

    /**
     * Check actual network connectivity (not just navigator.onLine)
     */
    async checkConnection() {
        const previousStatus = this.isOnline;

        try {
            // Try to fetch a small resource to verify actual connectivity
            const response = await fetch('/static/icons/favicon-16x16.png', {
                method: 'HEAD',
                cache: 'no-cache'
            });

            this.isOnline = response.ok;
        } catch (error) {
            this.isOnline = false;
        }

        // If status changed, trigger appropriate event
        if (previousStatus !== this.isOnline) {
            if (this.isOnline) {
                this.handleOnline();
            } else {
                this.handleOffline();
            }
        }

        return this.isOnline;
    }

    /**
     * Handle online event
     */
    async handleOnline() {
        console.log('[Network] Connection restored');
        this.isOnline = true;

        // Update UI
        this.updateConnectionUI(true);

        // Trigger registered listeners
        this.listeners.online.forEach(callback => callback());

        // Trigger Service Worker sync
        await this.triggerSync();

        // Sync PENDING requests (legacy support)
        await this.syncPendingRequests();

        // Show notification
        this.showNotification('Bağlantı Geri Geldi', 'İnternet bağlantınız geri geldi. Bekleyen işlemler senkronize ediliyor...', 'success');
    }

    /**
     * Handle offline event
     */
    handleOffline() {
        console.log('[Network] Connection lost');
        this.isOnline = false;

        // Update UI
        this.updateConnectionUI(false);

        // Trigger registered listeners
        this.listeners.offline.forEach(callback => callback());

        // Show notification
        this.showNotification('Bağlantı Kesildi', 'İnternet bağlantınız kesildi. Çevrimdışı modda çalışıyorsunuz.', 'warning');
    }

    /**
     * Update connection status UI
     */
    updateConnectionUI(isOnline) {
        // Add/remove body class
        document.body.classList.toggle('offline', !isOnline);
        document.body.classList.toggle('online', isOnline);

        // Update any connection indicators
        const indicators = document.querySelectorAll('.connection-indicator');
        indicators.forEach(indicator => {
            indicator.classList.toggle('online', isOnline);
            indicator.classList.toggle('offline', !isOnline);
            indicator.textContent = isOnline ? 'Çevrimiçi' : 'Çevrimdışı';
        });
    }

    /**
     * Sync PENDING requests when connection is restored
     */
    async syncPendingRequests() {
        if (this.syncInProgress) {
            console.log('[Network] Sync already in progress');
            return;
        }

        this.syncInProgress = true;

        try {
            console.log('[Network] Starting background sync...');

            // Get PENDING requests from IndexedDB
            if (typeof offlineStorage === 'undefined') {
                console.warn('[Network] Offline storage not available');
                return;
            }

            const PENDINGRequests = await offlineStorage.getPendingRequests();

            if (PENDINGRequests.length === 0) {
                console.log('[Network] No PENDING requests to sync');
                return;
            }

            console.log(`[Network] Syncing ${PENDINGRequests.length} PENDING requests`);

            let successCount = 0;
            let failCount = 0;

            for (const req of PENDINGRequests) {
                try {
                    // Reconstruct the request
                    const response = await fetch(req.url, {
                        method: req.method,
                        headers: req.headers,
                        body: req.body
                    });

                    if (response.ok) {
                        // Remove from PENDING if successful
                        await offlineStorage.removePendingRequest(req.id);
                        successCount++;
                        console.log('[Network] Synced request:', req.url);
                    } else {
                        // Update retry count
                        await offlineStorage.updateRetryCount(req.id, req.retries + 1);
                        failCount++;
                        console.warn('[Network] Failed to sync request:', req.url, response.status);
                    }
                } catch (error) {
                    // Update retry count
                    await offlineStorage.updateRetryCount(req.id, req.retries + 1);
                    failCount++;
                    console.error('[Network] Error syncing request:', req.url, error);
                }
            }

            console.log(`[Network] Sync complete: ${successCount} successful, ${failCount} failed`);

            // Trigger sync complete listeners
            this.listeners.syncComplete.forEach(callback => callback({
                success: successCount,
                failed: failCount
            }));

            // Show notification
            if (successCount > 0) {
                this.showNotification(
                    'Senkronizasyon Tamamlandı',
                    `${successCount} bekleyen işlem başarıyla senkronize edildi.`,
                    'success'
                );
            }

            // Trigger service worker sync if available
            if ('serviceWorker' in navigator && 'sync' in navigator.serviceWorker) {
                const registration = await navigator.serviceWorker.ready;
                await registration.sync.register('sync-buggy-requests');
            }
        } catch (error) {
            console.error('[Network] Sync error:', error);
        } finally {
            this.syncInProgress = false;
        }
    }

    /**
     * Queue a request for later sync when offline
     */
    async queueRequest(url, options = {}) {
        if (this.isOnline) {
            // If online, make the request immediately
            return fetch(url, options);
        }

        // If offline, queue for later
        console.log('[Network] Queueing request for later sync:', url);

        if (typeof offlineStorage !== 'undefined') {
            await offlineStorage.addPendingRequest({
                url: url,
                method: options.method || 'GET',
                headers: options.headers || {},
                body: options.body || null,
                type: options.type || 'general'
            });

            this.showNotification(
                'İşlem Kuyruğa Alındı',
                'İnternet bağlantınız geri geldiğinde işlem otomatik olarak gerçekleştirilecek.',
                'info'
            );
        }

        // Return a rejected promise to indicate offline
        return Promise.reject(new Error('Offline - request queued'));
    }

    /**
     * Enhanced fetch wrapper with offline support
     */
    async fetch(url, options = {}) {
        // Check if online
        if (!this.isOnline) {
            // Check if this is a GET request - we can try to serve from cache
            if (!options.method || options.method === 'GET') {
                try {
                    const cache = await caches.open('shuttlecall-v2.0.0-dynamic');
                    const cached = await cache.match(url);
                    if (cached) {
                        console.log('[Network] Serving from cache while offline:', url);
                        return cached;
                    }
                } catch (error) {
                    console.error('[Network] Cache error:', error);
                }
            }

            // Queue non-GET requests or if no cache available
            return this.queueRequest(url, options);
        }

        // Online - make the request normally
        try {
            const response = await fetch(url, options);

            // Cache successful GET requests
            if (response.ok && (!options.method || options.method === 'GET')) {
                try {
                    const cache = await caches.open('shuttlecall-v2.0.0-dynamic');
                    cache.put(url, response.clone());
                } catch (error) {
                    console.error('[Network] Cache put error:', error);
                }
            }

            return response;
        } catch (error) {
            // Network error - queue the request
            return this.queueRequest(url, options);
        }
    }

    /**
     * Register event listener
     */
    on(event, callback) {
        if (this.listeners[event]) {
            this.listeners[event].push(callback);
        }
    }

    /**
     * Remove event listener
     */
    off(event, callback) {
        if (this.listeners[event]) {
            this.listeners[event] = this.listeners[event].filter(cb => cb !== callback);
        }
    }

    /**
     * Show notification
     */
    showNotification(title, message, type = 'info') {
        // Create toast notification
        const toast = document.createElement('div');
        toast.className = `network-toast network-toast-${type}`;
        toast.innerHTML = `
            <div class="network-toast-content">
                <strong>${title}</strong>
                <p>${message}</p>
            </div>
            <button class="network-toast-close" onclick="this.parentElement.remove()">×</button>
        `;

        // Add styles if not already present
        if (!document.getElementById('network-toast-styles')) {
            const style = document.createElement('style');
            style.id = 'network-toast-styles';
            style.textContent = `
                .network-toast {
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    min-width: 300px;
                    max-width: 400px;
                    background: white;
                    border-radius: 8px;
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                    padding: 16px;
                    z-index: 10000;
                    animation: slideInRight 0.3s ease-out;
                    display: flex;
                    gap: 12px;
                }

                @keyframes slideInRight {
                    from { transform: translateX(400px); opacity: 0; }
                    to { transform: translateX(0); opacity: 1; }
                }

                .network-toast-success { border-left: 4px solid #10b981; }
                .network-toast-warning { border-left: 4px solid #f59e0b; }
                .network-toast-info { border-left: 4px solid #3b82f6; }
                .network-toast-error { border-left: 4px solid #ef4444; }

                .network-toast-content { flex: 1; }
                .network-toast-content strong { display: block; margin-bottom: 4px; color: #1f2937; }
                .network-toast-content p { margin: 0; font-size: 14px; color: #6b7280; }

                .network-toast-close {
                    background: none;
                    border: none;
                    font-size: 24px;
                    color: #9ca3af;
                    cursor: pointer;
                    padding: 0;
                    width: 24px;
                    height: 24px;
                    line-height: 1;
                }

                .network-toast-close:hover { color: #6b7280; }

                @media (max-width: 768px) {
                    .network-toast {
                        top: 10px;
                        right: 10px;
                        left: 10px;
                        min-width: auto;
                    }
                }

                body.offline .offline-indicator {
                    display: block;
                }

                body.online .offline-indicator {
                    display: none;
                }
            `;
            document.head.appendChild(style);
        }

        document.body.appendChild(toast);

        // Auto remove after 5 seconds
        setTimeout(() => {
            toast.style.animation = 'slideInRight 0.3s ease-in reverse';
            setTimeout(() => toast.remove(), 300);
        }, 5000);
    }

    /**
     * Get current status
     */
    getStatus() {
        return {
            isOnline: this.isOnline,
            syncInProgress: this.syncInProgress
        };
    }
}

// Create global instance
const networkManager = new NetworkManager();

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = networkManager;
}

// Network manager loaded
