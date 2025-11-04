/**
 * Shuttle Call - Platform Detection and Optimization
 * Detects device platform and applies appropriate optimizations
 */

const PlatformDetection = {
    /**
     * Detect if device is Android
     */
    isAndroid() {
        return /Android/i.test(navigator.userAgent);
    },
    
    /**
     * Detect if device is iOS
     */
    isIOS() {
        return /iPhone|iPad|iPod/i.test(navigator.userAgent);
    },
    
    /**
     * Detect if device is desktop
     */
    isDesktop() {
        return !this.isMobile() && !this.isTablet();
    },
    
    /**
     * Detect if device is mobile
     */
    isMobile() {
        return /Android|webOS|iPhone|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    },
    
    /**
     * Detect if device is tablet
     */
    isTablet() {
        return /iPad|Android/i.test(navigator.userAgent) && !/Mobile/i.test(navigator.userAgent);
    },
    
    /**
     * Check if PWA is installed
     */
    isPWAInstalled() {
        return window.matchMedia('(display-mode: standalone)').matches ||
               window.navigator.standalone === true;
    },
    
    /**
     * Get platform-specific notification options
     */
    getNotificationOptions(baseOptions, priority) {
        const options = { ...baseOptions };
        
        if (this.isAndroid()) {
            // Android optimizations
            options.vibrate = this.getAndroidVibrationPattern(priority);
            options.tag = options.tag || 'buggy-notification';
            options.renotify = true;
            
            if (priority === 'high') {
                options.requireInteraction = true;
            }
        } else if (this.isIOS()) {
            // iOS optimizations
            delete options.vibrate; // iOS doesn't support Vibration API
            
            // Ensure PWA is installed for notifications
            if (!this.isPWAInstalled()) {
                console.warn('[Platform] iOS notifications require PWA installation');
            }
            
            // Use sound for alerts
            options.silent = false;
        } else if (this.isDesktop()) {
            // Desktop optimizations
            delete options.vibrate; // No vibration on desktop
            
            // More action buttons on desktop
            if (options.actions && options.actions.length < 3) {
                options.actions.push({
                    action: 'snooze',
                    title: '⏰ Ertele',
                    icon: '/static/icons/Icon-72.png'
                });
            }
            
            // Larger images on desktop
            if (options.image) {
                options.image = options.image; // Keep as is
            }
        }
        
        return options;
    },
    
    /**
     * Get Android-specific vibration pattern
     */
    getAndroidVibrationPattern(priority) {
        const patterns = {
            'high': [300, 200, 300, 200, 300],
            'normal': [200, 100, 200],
            'low': [100]
        };
        return patterns[priority] || patterns.normal;
    },
    
    /**
     * Check if notifications are supported
     */
    isNotificationSupported() {
        return 'Notification' in window && 'serviceWorker' in navigator;
    },
    
    /**
     * Check if push notifications are supported
     */
    isPushSupported() {
        return 'PushManager' in window;
    },
    
    /**
     * Check if badge API is supported
     */
    isBadgeSupported() {
        return 'setAppBadge' in navigator;
    },
    
    /**
     * Check if vibration API is supported
     */
    isVibrationSupported() {
        return 'vibrate' in navigator;
    },
    
    /**
     * Get platform info
     */
    getPlatformInfo() {
        return {
            platform: this.isAndroid() ? 'Android' : 
                     this.isIOS() ? 'iOS' : 
                     this.isDesktop() ? 'Desktop' : 'Unknown',
            isMobile: this.isMobile(),
            isTablet: this.isTablet(),
            isPWA: this.isPWAInstalled(),
            features: {
                notifications: this.isNotificationSupported(),
                push: this.isPushSupported(),
                badge: this.isBadgeSupported(),
                vibration: this.isVibrationSupported()
            }
        };
    },
    
    /**
     * Log platform info to console
     */
    logPlatformInfo() {
        const info = this.getPlatformInfo();
        console.log('[Platform] Device Info:', info);
        return info;
    }
};

// Export to global scope
window.PlatformDetection = PlatformDetection;

// Log platform info on load
if (window.BuggyCall && window.BuggyCall.CONFIG && window.BuggyCall.CONFIG.DEBUG) {
    PlatformDetection.logPlatformInfo();
}
