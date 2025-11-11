/**
 * Shuttle Call - Common JavaScript
 * Shared functionality across all pages
 */

// Global configuration
const CONFIG = {
    API_BASE_URL: window.location.origin + '/api',
    SOCKET_URL: window.location.origin,
    THEME_COLORS: {
        primary: '#0EA5E9',
        'primary-dark': '#0284C7',
        accent: '#F59E0B',
        'accent-dark': '#D97706',
        dark: '#111827',
        light: '#F9FAFB',
        success: '#10B981',
        danger: '#EF4444',
        warning: '#F59E0B',
        info: '#3B82F6'
    }
};

// Utility Functions
const Utils = {
    /**
     * Show loading overlay with buggy animation
     * @param {string} message - Optional loading message
     */
    showLoading(message = 'Yükleniyor...') {
        // Check if buggy loader already exists
        let overlay = document.querySelector('.buggy-loading-overlay');
        
        if (!overlay) {
            // Create new buggy loading overlay
            overlay = document.createElement('div');
            overlay.className = 'buggy-loading-overlay';
            overlay.innerHTML = `
                <div class="buggy-loader"></div>
                <div class="loading-text">${message}</div>
            `;
            document.body.appendChild(overlay);
        } else {
            // Update message if exists
            const textElement = overlay.querySelector('.loading-text');
            if (textElement) {
                textElement.textContent = message;
            }
        }
        
        // Show overlay with animation
        setTimeout(() => {
            overlay.classList.add('show');
        }, 10);
    },

    /**
     * Hide loading overlay
     */
    hideLoading() {
        const overlay = document.querySelector('.buggy-loading-overlay');
        if (overlay) {
            overlay.classList.remove('show');
            // Remove from DOM after animation
            setTimeout(() => {
                if (overlay.parentNode) {
                    overlay.parentNode.removeChild(overlay);
                }
            }, 300);
        }
    },

    /**
     * Show toast notification (Tailwind CSS styled)
     * @param {string} message - Message to display
     * @param {string} type - Type of notification (success, danger, warning, info)
     */
    showToast(message, type = 'info') {
        // Create notification element with Tailwind classes
        const notification = document.createElement('div');
        
        // Map type to Tailwind colors
        const colorClasses = {
            'success': 'bg-green-500 border-green-600',
            'danger': 'bg-red-500 border-red-600',
            'warning': 'bg-yellow-500 border-yellow-600',
            'info': 'bg-blue-500 border-blue-600'
        };
        
        notification.className = `fixed top-5 right-5 min-w-[300px] max-w-[500px] ${colorClasses[type] || colorClasses.info} text-white px-6 py-4 rounded-lg shadow-2xl border-l-4 z-50 flex items-center justify-between gap-3`;
        notification.style.animation = 'slideInRight 0.3s ease-out';
        
        const icon = type === 'success' ? 'check-circle' : 
                     type === 'danger' ? 'times-circle' : 
                     type === 'warning' ? 'exclamation-triangle' : 'info-circle';
        
        notification.innerHTML = `
            <div class="flex items-center gap-3 flex-1">
                <i class="fas fa-${icon} text-xl"></i>
                <span class="font-medium">${message}</span>
            </div>
            <button class="close-btn text-white hover:text-gray-200 transition-colors ml-4">
                <i class="fas fa-times text-lg"></i>
            </button>
        `;
        
        document.body.appendChild(notification);
        
        // Close button handler
        const closeBtn = notification.querySelector('.close-btn');
        closeBtn.addEventListener('click', () => {
            notification.style.animation = 'slideOutRight 0.3s ease-in';
            setTimeout(() => notification.remove(), 300);
        });
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            notification.style.animation = 'slideOutRight 0.3s ease-in';
            setTimeout(() => notification.remove(), 300);
        }, 5000);
    },

    /**
     * Format date to locale string
     * @param {string|Date} date - Date to format
     * @returns {string}
     */
    formatDate(date) {
        if (!date) return '-';
        const d = new Date(date);
        return d.toLocaleString('tr-TR');
    },

    /**
     * Format time duration
     * @param {number} seconds - Duration in seconds
     * @returns {string}
     */
    formatDuration(seconds) {
        if (!seconds) return '-';
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = seconds % 60;
        return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
    },

    /**
     * Get badge/tag classes by status (Tailwind - Modern & Clear)
     * @param {string} status - Status value
     * @returns {string}
     */
    getBadgeClass(status) {
        const statusMap = {
            'PENDING': 'badge-PENDING',
            'accepted': 'badge-accepted',
            'completed': 'badge-completed',
            'cancelled': 'badge-cancelled',
            'available': 'badge-available',
            'busy': 'badge-busy',
            'offline': 'badge-offline'
        };
        return statusMap[status] || 'badge-offline';
    },
    
    /**
     * Get button classes by type (Tailwind - Modern Design)
     * @param {string} type - Button type
     * @returns {string}
     */
    getButtonClass(type) {
        const baseClasses = 'inline-flex items-center justify-center font-semibold rounded-lg transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2';
        const typeMap = {
            'primary': `${baseClasses} bg-sky-500 hover:bg-sky-600 active:bg-sky-700 text-white shadow-sm hover:shadow focus:ring-sky-500`,
            'success': `${baseClasses} bg-emerald-500 hover:bg-emerald-600 active:bg-emerald-700 text-white shadow-sm hover:shadow focus:ring-emerald-500`,
            'danger': `${baseClasses} bg-rose-500 hover:bg-rose-600 active:bg-rose-700 text-white shadow-sm hover:shadow focus:ring-rose-500`,
            'warning': `${baseClasses} bg-amber-500 hover:bg-amber-600 active:bg-amber-700 text-white shadow-sm hover:shadow focus:ring-amber-500`,
            'info': `${baseClasses} bg-blue-500 hover:bg-blue-600 active:bg-blue-700 text-white shadow-sm hover:shadow focus:ring-blue-500`,
            'secondary': `${baseClasses} bg-slate-100 hover:bg-slate-200 active:bg-slate-300 text-slate-900 focus:ring-slate-500`,
            'light': `${baseClasses} bg-white hover:bg-gray-50 active:bg-gray-100 text-gray-900 border border-gray-300 focus:ring-gray-500`,
            'dark': `${baseClasses} bg-slate-900 hover:bg-slate-800 active:bg-slate-950 text-white shadow-sm hover:shadow focus:ring-slate-900`
        };
        return typeMap[type] || typeMap.primary;
    },

    /**
     * Confirm action with user (Using Modal)
     * @param {string} message - Confirmation message
     * @param {string} title - Modal title
     * @returns {Promise<boolean>}
     */
    async confirm(message, title = 'Onay Gerekli') {
        if (typeof BuggyModal !== 'undefined') {
            return await BuggyModal.confirm(message, title);
        }
        // Fallback to native confirm
        return window.confirm(message);
    },
    
    /**
     * Show success modal
     * @param {string} message - Success message
     * @param {string} title - Modal title
     */
    async showSuccess(message, title = 'Başarılı!') {
        if (typeof BuggyModal !== 'undefined') {
            return await BuggyModal.success(message, title);
        }
        this.showToast(message, 'success');
    },
    
    /**
     * Show error modal
     * @param {string} message - Error message
     * @param {string} title - Modal title
     */
    async showError(message, title = 'Hata!') {
        if (typeof BuggyModal !== 'undefined') {
            return await BuggyModal.error(message, title);
        }
        this.showToast(message, 'danger');
    },
    
    /**
     * Show warning modal
     * @param {string} message - Warning message
     * @param {string} title - Modal title
     */
    async showWarning(message, title = 'Uyarı!') {
        if (typeof BuggyModal !== 'undefined') {
            return await BuggyModal.warning(message, title);
        }
        this.showToast(message, 'warning');
    },

    /**
     * Debounce function
     * @param {Function} func - Function to debounce
     * @param {number} wait - Wait time in milliseconds
     * @returns {Function}
     */
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
};

// API Helper
const API = {
    /**
     * Get CSRF token from meta tag or hidden input
     * @returns {string|null}
     */
    getCSRFToken() {
        // Try to get from meta tag first
        const metaTag = document.querySelector('meta[name="csrf-token"]');
        if (metaTag) {
            return metaTag.getAttribute('content');
        }
        
        // Try to get from hidden input
        const hiddenInput = document.querySelector('input[name="csrf_token"]');
        if (hiddenInput) {
            return hiddenInput.value;
        }
        
        return null;
    },

    /**
     * Make API request
     * @param {string} endpoint - API endpoint
     * @param {Object} options - Fetch options
     * @returns {Promise}
     */
    async request(endpoint, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json'
            }
        };

        // Add auth token if exists
        const token = localStorage.getItem('access_token');
        if (token) {
            defaultOptions.headers['Authorization'] = `Bearer ${token}`;
        }

        // Add CSRF token for non-GET requests
        if (options.method && options.method !== 'GET') {
            const csrfToken = this.getCSRFToken();
            if (csrfToken) {
                defaultOptions.headers['X-CSRF-Token'] = csrfToken;
            }
        }

        const config = { ...defaultOptions, ...options };
        
        try {
            const response = await fetch(`${CONFIG.API_BASE_URL}${endpoint}`, config);
            const data = await response.json();
            
            if (!response.ok) {
                // Try to get error message from various fields
                const errorMessage = data.error || data.message || data.detail || 'API request failed';
                throw new Error(errorMessage);
            }
            
            return data;
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    },

    /**
     * GET request
     */
    get(endpoint) {
        return this.request(endpoint, { method: 'GET' });
    },

    /**
     * POST request
     */
    post(endpoint, data) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },

    /**
     * PUT request
     */
    put(endpoint, data) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    },

    /**
     * DELETE request
     */
    delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    }
};

// Socket.IO Helper
const Socket = {
    socket: null,

    /**
     * Initialize socket connection
     */
    init() {
        if (!this.socket) {
            this.socket = io(CONFIG.SOCKET_URL, {
                autoConnect: false
            });

            this.socket.on('connect', () => {
                console.log('Socket connected');
            });

            this.socket.on('disconnect', () => {
                console.log('Socket disconnected');
            });

            this.socket.on('error', (error) => {
                console.error('Socket error:', error);
            });
        }
        return this.socket;
    },

    /**
     * Connect socket
     */
    connect() {
        if (this.socket) {
            this.socket.connect();
        }
    },

    /**
     * Disconnect socket
     */
    disconnect() {
        if (this.socket) {
            this.socket.disconnect();
        }
    },

    /**
     * Emit event
     */
    emit(event, data) {
        if (this.socket) {
            this.socket.emit(event, data);
        }
    },

    /**
     * Listen to event
     */
    on(event, callback) {
        if (this.socket) {
            this.socket.on(event, callback);
        }
    }
};

// Form Helper
const Form = {
    /**
     * Get form data as object
     * @param {HTMLFormElement} form - Form element
     * @returns {Object}
     */
    getData(form) {
        const formData = new FormData(form);
        const data = {};
        for (let [key, value] of formData.entries()) {
            data[key] = value;
        }
        return data;
    },

    /**
     * Validate form
     * @param {HTMLFormElement} form - Form element
     * @returns {boolean}
     */
    validate(form) {
        return form.checkValidity();
    },

    /**
     * Show field error (Tailwind)
     * @param {HTMLInputElement} field - Input field
     * @param {string} message - Error message
     */
    showError(field, message) {
        field.classList.add('border-red-500', 'focus:border-red-500', 'focus:ring-red-500');
        field.classList.remove('border-gray-300', 'border-green-500');
        
        // Remove existing error
        const existingError = field.parentElement.querySelector('.error-message');
        if (existingError) {
            existingError.remove();
        }
        
        // Add new error message
        const error = document.createElement('p');
        error.className = 'error-message text-red-500 text-sm mt-1 flex items-center gap-1';
        error.innerHTML = `<i class="fas fa-exclamation-circle"></i> ${message}`;
        field.parentElement.appendChild(error);
    },

    /**
     * Clear field error
     * @param {HTMLInputElement} field - Input field
     */
    clearError(field) {
        field.classList.remove('border-red-500', 'focus:border-red-500', 'focus:ring-red-500');
        field.classList.add('border-green-500', 'focus:border-green-500', 'focus:ring-green-500');
        
        const error = field.parentElement.querySelector('.error-message');
        if (error) {
            error.remove();
        }
    }
};

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }

    @keyframes slideOutRight {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// Service Worker Mesaj Dinleyicisi - GELIŞTIRILMIŞ VERSIYON v3
if ('serviceWorker' in navigator) {
    navigator.serviceWorker.addEventListener('message', (event) => {
        const data = event.data;
        
        if (!data || !data.type) {
            return;
        }
        
        switch (data.type) {
            case 'PLAY_NOTIFICATION_SOUND':
                // Play notification sound
                if (data.soundUrl) {
                    playNotificationSound(data.soundUrl);
                }
                break;
                
            case 'NAVIGATE':
                // Handle deep linking navigation from notification click
                handleDeepLinkNavigation(data.url);
                break;
                
            case 'BADGE_UPDATE':
                // Badge update handled by BadgeManager
                break;
                
            case 'SYNC_COMPLETE':
                // Offline sync completed
                console.log('[SW] Sync complete:', data.results);
                if (data.results && data.results.delivered > 0) {
                    showToast(`${data.results.delivered} bildirim senkronize edildi`, 'success');
                }
                break;
                
            case 'NETWORK_STATUS':
                // Network status change
                handleNetworkStatusChange(data.online);
                break;
                
            default:
                console.log('[SW] Unknown message type:', data.type);
        }
    });
}

/**
 * Handle deep link navigation from Service Worker
 * @param {string} url - URL to navigate to
 */
function handleDeepLinkNavigation(url) {
    if (!url) {
        console.warn('[Navigation] No URL provided');
        return;
    }
    
    console.log('[Navigation] Deep linking to:', url);
    
    // Check if we're already on the target page
    const currentPath = window.location.pathname + window.location.search;
    if (currentPath === url) {
        console.log('[Navigation] Already on target page');
        // Reload to ensure fresh data
        window.location.reload();
        return;
    }
    
    // Navigate to URL
    window.location.href = url;
}

/**
 * Handle network status change
 * @param {boolean} online - Network online status
 */
function handleNetworkStatusChange(online) {
    console.log('[Network] Status changed:', online ? 'online' : 'offline');
    
    if (online) {
        showToast('İnternet bağlantısı geri geldi', 'success');
        
        // Trigger any PENDING syncs
        if (window.NetworkManager) {
            window.NetworkManager.handleOnline();
        }
    } else {
        showToast('İnternet bağlantısı kesildi', 'warning');
        
        if (window.NetworkManager) {
            window.NetworkManager.handleOffline();
        }
    }
}

/**
 * Show toast notification
 * @param {string} message - Message to display
 * @param {string} type - Toast type (success, error, warning, info)
 */
function showToast(message, type = 'info') {
    // Check if toast container exists
    let container = document.querySelector('.toast-container');
    
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container';
        document.body.appendChild(container);
    }
    
    // Create toast element
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    
    container.appendChild(toast);
    
    // Animate in
    setTimeout(() => toast.classList.add('show'), 10);
    
    // Remove after 3 seconds
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

/**
 * Bildirim sesi çal - GELIŞTIRILMIŞ VERSIYON v2
 * Priority-based sound selection
 * @param {string} soundUrl - Ses dosyası URL'i (opsiyonel)
 */
function playNotificationSound(soundUrl) {
    console.log('[Audio] Playing notification sound:', soundUrl);
    
    // Önce ses dosyası dene
    if (soundUrl) {
        try {
            const audio = new Audio(soundUrl);
            audio.volume = 1.0;
            
            const playPromise = audio.play();
            
            if (playPromise !== undefined) {
                playPromise
                    .then(() => {
                        console.log('[Audio] Notification sound played successfully');
                    })
                    .catch((error) => {
                        console.warn('[Audio] Could not play audio file, using generated sound:', error);
                        // Ses dosyası çalamazsa, generated sound kullan
                        playGeneratedSound();
                    });
            }
            return;
        } catch (error) {
            console.error('[Audio] Error with audio file:', error);
        }
    }
    
    // Ses dosyası yoksa veya çalamazsa, generated sound kullan
    playGeneratedSound();
}

/**
 * Web Audio API ile ses oluştur ve çal
 */
function playGeneratedSound() {
    try {
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        
        // Çift beep sesi (dikkat çekici)
        // İlk beep
        const osc1 = audioContext.createOscillator();
        const gain1 = audioContext.createGain();
        osc1.connect(gain1);
        gain1.connect(audioContext.destination);
        osc1.frequency.value = 880; // A5
        osc1.type = 'sine';
        gain1.gain.setValueAtTime(0.3, audioContext.currentTime);
        gain1.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.15);
        osc1.start(audioContext.currentTime);
        osc1.stop(audioContext.currentTime + 0.15);
        
        // İkinci beep
        const osc2 = audioContext.createOscillator();
        const gain2 = audioContext.createGain();
        osc2.connect(gain2);
        gain2.connect(audioContext.destination);
        osc2.frequency.value = 1046.5; // C6
        osc2.type = 'sine';
        gain2.gain.setValueAtTime(0.3, audioContext.currentTime + 0.2);
        gain2.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.4);
        osc2.start(audioContext.currentTime + 0.2);
        osc2.stop(audioContext.currentTime + 0.4);
        
        console.log('[Audio] Generated notification sound played');
    } catch (error) {
        console.error('[Audio] Error generating sound:', error);
    }
}

/**
 * Priority-based sound selection helper
 * @param {string} priority - Priority level (high, normal, low)
 * @returns {string} Sound URL
 */
function getPrioritySoundUrl(priority) {
    const sounds = {
        'high': '/static/sounds/urgent.mp3',
        'normal': '/static/sounds/notification.mp3',
        'low': '/static/sounds/subtle.mp3'
    };
    return sounds[priority] || sounds.normal;
}

// ============================================================================
// BADGE MANAGER (CLIENT-SIDE)
// ============================================================================

/**
 * Badge Manager - Client-side helper for badge operations
 */
const BadgeManager = {
    /**
     * Get current badge count from Service Worker
     * @returns {Promise<number>} Current badge count
     */
    async getBadgeCount() {
        try {
            if (!navigator.serviceWorker || !navigator.serviceWorker.controller) {
                console.warn('[Badge] Service Worker not available');
                return 0;
            }

            return new Promise((resolve, reject) => {
                const messageChannel = new MessageChannel();
                
                messageChannel.port1.onmessage = (event) => {
                    resolve(event.data.count || 0);
                };

                navigator.serviceWorker.controller.postMessage(
                    { action: 'getBadgeCount' },
                    [messageChannel.port2]
                );

                // Timeout after 5 seconds
                setTimeout(() => reject(new Error('Timeout')), 5000);
            });
        } catch (error) {
            console.error('[Badge] Error getting badge count:', error);
            return 0;
        }
    },

    /**
     * Set badge count to specific value
     * @param {number} count - Badge count to set
     * @returns {Promise<number>} Updated badge count
     */
    async setBadgeCount(count) {
        try {
            if (!navigator.serviceWorker || !navigator.serviceWorker.controller) {
                console.warn('[Badge] Service Worker not available');
                return 0;
            }

            return new Promise((resolve, reject) => {
                const messageChannel = new MessageChannel();
                
                messageChannel.port1.onmessage = (event) => {
                    resolve(event.data.count || 0);
                };

                navigator.serviceWorker.controller.postMessage(
                    { action: 'setBadgeCount', data: { count } },
                    [messageChannel.port2]
                );

                setTimeout(() => reject(new Error('Timeout')), 5000);
            });
        } catch (error) {
            console.error('[Badge] Error setting badge count:', error);
            return 0;
        }
    },

    /**
     * Reset badge count to zero
     * @returns {Promise<number>} Updated badge count (0)
     */
    async resetBadgeCount() {
        try {
            if (!navigator.serviceWorker || !navigator.serviceWorker.controller) {
                console.warn('[Badge] Service Worker not available');
                return 0;
            }

            return new Promise((resolve, reject) => {
                const messageChannel = new MessageChannel();
                
                messageChannel.port1.onmessage = (event) => {
                    resolve(event.data.count || 0);
                };

                navigator.serviceWorker.controller.postMessage(
                    { action: 'resetBadgeCount' },
                    [messageChannel.port2]
                );

                // Timeout with proper cleanup
                const timeoutId = setTimeout(() => {
                    messageChannel.port1.close();
                    messageChannel.port2.close();
                    reject(new Error('Badge reset timeout'));
                }, 5000);
                
                // Clear timeout on success
                messageChannel.port1.onmessage = (event) => {
                    clearTimeout(timeoutId);
                    messageChannel.port1.close();
                    messageChannel.port2.close();
                    resolve(event.data.count || 0);
                };
            });
        } catch (error) {
            console.warn('[Badge] Error resetting badge count:', error);
            return 0;
        }
    },

    /**
     * Update badge count with delta (increment/decrement)
     * @param {number} delta - Amount to change (positive or negative)
     * @returns {Promise<number>} Updated badge count
     */
    async updateBadgeCount(delta) {
        try {
            if (!navigator.serviceWorker || !navigator.serviceWorker.controller) {
                console.warn('[Badge] Service Worker not available');
                return 0;
            }

            return new Promise((resolve, reject) => {
                const messageChannel = new MessageChannel();
                
                messageChannel.port1.onmessage = (event) => {
                    resolve(event.data.count || 0);
                };

                navigator.serviceWorker.controller.postMessage(
                    { action: 'updateBadgeCount', data: { delta } },
                    [messageChannel.port2]
                );

                setTimeout(() => reject(new Error('Timeout')), 5000);
            });
        } catch (error) {
            console.error('[Badge] Error updating badge count:', error);
            return 0;
        }
    },

    /**
     * Increment badge count by 1
     * @returns {Promise<number>} Updated badge count
     */
    async increment() {
        return await this.updateBadgeCount(1);
    },

    /**
     * Decrement badge count by 1
     * @returns {Promise<number>} Updated badge count
     */
    async decrement() {
        return await this.updateBadgeCount(-1);
    },

    /**
     * Display badge count in page title (fallback for unsupported browsers)
     * @param {number} count - Badge count to display
     */
    updateTitleBadge(count) {
        const originalTitle = document.title.replace(/^\(\d+\)\s*/, '');
        
        if (count > 0) {
            document.title = `(${count}) ${originalTitle}`;
        } else {
            document.title = originalTitle;
        }
    },

    /**
     * Initialize badge manager and listen for updates
     */
    init() {
        console.log('[Badge] Initializing Badge Manager');

        // Listen for badge updates from Service Worker
        if (navigator.serviceWorker) {
            navigator.serviceWorker.addEventListener('message', (event) => {
                if (event.data.type === 'BADGE_UPDATE') {
                    console.log('[Badge] Badge updated:', event.data.count);
                    
                    // Update title badge as fallback
                    this.updateTitleBadge(event.data.count);
                    
                    // Dispatch custom event for app to listen
                    window.dispatchEvent(new CustomEvent('badgeupdate', {
                        detail: { count: event.data.count }
                    }));
                } else if (event.data.type === 'BADGE_FALLBACK') {
                    // Fallback for browsers without Badge API
                    console.log('[Badge] Using title badge fallback');
                    this.updateTitleBadge(event.data.count);
                }
            });
        }

        // Reset badge when page becomes visible
        document.addEventListener('visibilitychange', async () => {
            if (!document.hidden) {
                console.log('[Badge] Page visible, resetting badge');
                await this.resetBadgeCount();
            }
        });

        console.log('[Badge] Badge Manager initialized');
    }
};

// ============================================================================
// SERVICE WORKER MESSAGE HANDLER
// ============================================================================

/**
 * Service Worker Navigation Handler
 * Handles navigation messages from Service Worker (notification clicks)
 */
const ServiceWorkerHandler = {
    /**
     * Initialize Service Worker message listener
     */
    init() {
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.addEventListener('message', (event) => {
                this.handleMessage(event.data);
            });
            
            console.log('[SW Handler] Service Worker message listener initialized');
        } else {
            console.warn('[SW Handler] Service Worker not supported');
        }
    },
    
    /**
     * Handle incoming messages from Service Worker
     * @param {Object} data - Message data
     */
    handleMessage(data) {
        const { type } = data;
        
        console.log('[SW Handler] Received message:', type, data);
        
        switch (type) {
            case 'NAVIGATE':
                this.handleNavigation(data);
                break;
                
            case 'PLAY_NOTIFICATION_SOUND':
                this.handlePlaySound(data);
                break;
                
            case 'BADGE_UPDATE':
                this.handleBadgeUpdate(data);
                break;
                
            case 'NETWORK_STATUS':
                this.handleNetworkStatus(data);
                break;
                
            case 'SYNC_COMPLETE':
                this.handleSyncComplete(data);
                break;
                
            case 'BADGE_FALLBACK':
                this.handleBadgeFallback(data);
                break;
                
            default:
                console.warn('[SW Handler] Unknown message type:', type);
        }
    },
    
    /**
     * Handle navigation request from notification click
     * @param {Object} data - Navigation data
     */
    handleNavigation(data) {
        const { url, pathname, search, hash } = data;
        
        console.log('[SW Handler] Navigating to:', url);
        
        try {
            // Check if we're already on the target page
            const currentPath = window.location.pathname;
            const targetPath = pathname || new URL(url, window.location.origin).pathname;
            
            if (currentPath === targetPath && !search && !hash) {
                console.log('[SW Handler] Already on target page, refreshing...');
                window.location.reload();
                return;
            }
            
            // Navigate to the URL
            window.location.href = url;
            
        } catch (error) {
            console.error('[SW Handler] Navigation error:', error);
            
            // Fallback: try simple navigation
            try {
                window.location.href = url;
            } catch (fallbackError) {
                console.error('[SW Handler] Fallback navigation also failed:', fallbackError);
                Utils.showToast('Sayfa yüklenirken hata oluştu', 'danger');
            }
        }
    },
    
    /**
     * Handle play sound request
     * @param {Object} data - Sound data
     */
    handlePlaySound(data) {
        const { soundUrl } = data;
        
        console.log('[SW Handler] Playing sound:', soundUrl);
        
        try {
            if (typeof playNotificationSound === 'function') {
                playNotificationSound(soundUrl);
            } else {
                console.warn('[SW Handler] playNotificationSound function not available');
            }
        } catch (error) {
            console.error('[SW Handler] Error playing sound:', error);
        }
    },
    
    /**
     * Handle badge update notification
     * @param {Object} data - Badge data
     */
    handleBadgeUpdate(data) {
        const { count } = data;
        
        console.log('[SW Handler] Badge updated:', count);
        
        // Update UI if needed
        if (typeof BadgeManager !== 'undefined' && BadgeManager.updateUI) {
            BadgeManager.updateUI(count);
        }
    },
    
    /**
     * Handle network status change
     * @param {Object} data - Network status data
     */
    handleNetworkStatus(data) {
        const { online } = data;
        
        console.log('[SW Handler] Network status changed:', online ? 'online' : 'offline');
        
        if (online) {
            Utils.showToast('İnternet bağlantısı geri geldi', 'success');
        } else {
            Utils.showToast('İnternet bağlantısı kesildi. Bildirimler senkronize edilecek.', 'warning');
        }
    },
    
    /**
     * Handle sync completion notification
     * @param {Object} data - Sync results
     */
    handleSyncComplete(data) {
        const { results } = data;
        
        console.log('[SW Handler] Sync complete:', results);
        
        if (results && results.delivered > 0) {
            Utils.showToast(`${results.delivered} bildirim senkronize edildi`, 'success');
        }
    },
    
    /**
     * Handle badge fallback (for browsers without Badge API)
     * @param {Object} data - Badge data
     */
    handleBadgeFallback(data) {
        const { count } = data;
        
        console.log('[SW Handler] Badge fallback:', count);
        
        // Update page title with badge count
        const baseTitle = document.title.replace(/^\(\d+\)\s*/, '');
        
        if (count > 0) {
            document.title = `(${count}) ${baseTitle}`;
        } else {
            document.title = baseTitle;
        }
    }
};

// Initialize Badge Manager on load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        BadgeManager.init();
        ServiceWorkerHandler.init();
    });
} else {
    BadgeManager.init();
    ServiceWorkerHandler.init();
}

// Export globals
window.ShuttleCall = {
    Utils,
    API,
    Socket,
    Form,
    CONFIG,
    playNotificationSound, // Ses çalma fonksiyonunu export et
    getPrioritySoundUrl, // Priority-based sound selection
    BadgeManager, // Badge yönetimi
    ServiceWorkerHandler // Service Worker message handler
};

// Backward compatibility
window.BuggyCall = window.ShuttleCall;

console.log('Shuttle Call initialized - Enhanced v3.0 with SW Navigation Handler');
