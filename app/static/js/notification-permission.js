/**
 * Notification Permission Handler
 * Shuttle Call - Progressive Web App
 * 
 * Handles notification permission requests for driver and admin users
 * after login to enable real-time guest request notifications.
 */

class NotificationPermissionHandler {
    constructor() {
        this.userRole = null;
        this.alreadyAsked = false;
        this.currentStatus = 'default';
        this.dialog = null;
        this.previousFocusElement = null; // Store previous focus for restoration
    }

    /**
     * Initialize the handler
     * @param {string} userRole - User role ('driver' or 'admin')
     * @param {boolean} alreadyAsked - Whether permission was already asked in this session
     * @param {string} currentStatus - Current permission status ('default', 'granted', 'denied')
     */
    init(userRole, alreadyAsked, currentStatus) {
        try {
            this.userRole = userRole;
            this.alreadyAsked = alreadyAsked;
            this.currentStatus = currentStatus;

            console.log('[NotificationPermission] Initializing...', {
                userRole,
                alreadyAsked,
                currentStatus
            });

            // Browser support check
            if (!('Notification' in window)) {
                console.warn('[NotificationPermission] Notifications not supported in this browser');
                return;
            }

            // Only for driver and admin
            if (this.userRole !== 'driver' && this.userRole !== 'admin') {
                console.log('[NotificationPermission] Not a driver or admin, skipping');
                return;
            }

            // Check if we should show dialog (with delay for better UX)
            setTimeout(() => {
                this.checkAndShowDialog().catch(error => {
                    console.error('[NotificationPermission] Error in checkAndShowDialog:', error);
                });
            }, 2000); // 2 second delay after page load
        } catch (error) {
            console.error('[NotificationPermission] Error in init:', error);
        }
    }

    /**
     * Check conditions and show dialog if needed
     */
    async checkAndShowDialog() {
        try {
            // Check browser permission status first
            const browserStatus = await this.getBrowserPermissionStatus();
            console.log('[NotificationPermission] Browser status:', browserStatus);

            // Show dialog if permission is 'default' (not decided yet)
            if (browserStatus === 'default') {
                console.log('[NotificationPermission] Permission is default, showing dialog');
                this.showDialog();
            } else if (browserStatus === 'granted') {
                console.log('[NotificationPermission] Permission already granted');
                // Update session with current status
                await this.updateSessionStatus(browserStatus);
            } else if (browserStatus === 'denied') {
                console.log('[NotificationPermission] Permission denied by browser');
                // Show info message about how to enable notifications
                this.showDeniedInfo();
                // Update session with current status
                await this.updateSessionStatus(browserStatus);
            }
        } catch (error) {
            console.error('[NotificationPermission] Error in checkAndShowDialog:', error);
        }
    }

    /**
     * Show info about enabling notifications when denied
     */
    showDeniedInfo() {
        console.log('[NotificationPermission] Showing denied info');
        
        // Show a small toast with instructions
        const toast = document.createElement('div');
        toast.className = 'notification-permission-toast';
        toast.innerHTML = `
            <div style="display: flex; align-items: start; gap: 12px;">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" style="flex-shrink: 0; margin-top: 2px;">
                    <path d="M12 9V11M12 15H12.01M5.07183 19H18.9282C20.4678 19 21.4301 17.3333 20.6603 16L13.7321 4C12.9623 2.66667 11.0377 2.66667 10.2679 4L3.33975 16C2.56995 17.3333 3.53223 19 5.07183 19Z" 
                          stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                <div>
                    <strong>Bildirimler Kapalı</strong>
                    <p style="margin: 4px 0 0 0; font-size: 0.875rem; opacity: 0.9;">
                        Tarayıcı ayarlarından bildirimleri açabilirsiniz.
                    </p>
                </div>
            </div>
        `;
        
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #f59e0b;
            color: white;
            padding: 16px 20px;
            border-radius: 12px;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
            z-index: 10001;
            animation: slideInRight 0.3s ease-out;
            max-width: 400px;
        `;

        document.body.appendChild(toast);

        setTimeout(() => {
            try {
                toast.style.animation = 'slideInRight 0.3s ease-in reverse';
                setTimeout(() => {
                    try {
                        toast.remove();
                    } catch (error) {
                        console.error('[NotificationPermission] Error removing toast:', error);
                    }
                }, 300);
            } catch (error) {
                console.error('[NotificationPermission] Error animating toast:', error);
            }
        }, 5000);
    }

    /**
     * Get browser notification permission status
     * @returns {Promise<string>} Permission status
     */
    async getBrowserPermissionStatus() {
        try {
            // Browser support check
            if (!('Notification' in window)) {
                console.warn('[NotificationPermission] Notifications not supported');
                return 'denied';
            }
            
            return Notification.permission;
        } catch (error) {
            console.error('[NotificationPermission] Error getting browser permission status:', error);
            return 'denied';
        }
    }

    /**
     * Show permission request dialog
     */
    showDialog() {
        try {
            console.log('[NotificationPermission] Showing dialog');
            
            // Store current focus element for restoration
            this.previousFocusElement = document.activeElement;
            
            // Create and show custom dialog
            this.dialog = this.createDialog();
            document.body.appendChild(this.dialog);

            // Animate in
            setTimeout(() => {
                try {
                    this.dialog.classList.add('show');
                    
                    // Focus first button for accessibility
                    const firstButton = this.dialog.querySelector('.btn-allow');
                    if (firstButton) {
                        firstButton.focus();
                    }
                } catch (error) {
                    console.error('[NotificationPermission] Error animating dialog:', error);
                }
            }, 100);

            // Add keyboard event listeners
            this.dialog.addEventListener('keydown', (e) => {
                // Escape key to close
                if (e.key === 'Escape') {
                    this.handleLater();
                    return;
                }
                
                // Tab key navigation (trap focus within dialog)
                if (e.key === 'Tab') {
                    this.handleTabNavigation(e);
                }
            });
        } catch (error) {
            console.error('[NotificationPermission] Error showing dialog:', error);
        }
    }

    /**
     * Handle Tab key navigation within dialog (focus trap)
     * @param {KeyboardEvent} e - Keyboard event
     */
    handleTabNavigation(e) {
        try {
            if (!this.dialog) return;

            // Get all focusable elements in dialog
            const focusableElements = this.dialog.querySelectorAll(
                'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
            );
            
            if (focusableElements.length === 0) return;

            const firstElement = focusableElements[0];
            const lastElement = focusableElements[focusableElements.length - 1];

            // Shift + Tab on first element -> focus last element
            if (e.shiftKey && document.activeElement === firstElement) {
                e.preventDefault();
                lastElement.focus();
            }
            // Tab on last element -> focus first element
            else if (!e.shiftKey && document.activeElement === lastElement) {
                e.preventDefault();
                firstElement.focus();
            }
        } catch (error) {
            console.error('[NotificationPermission] Error in handleTabNavigation:', error);
        }
    }

    /**
     * Create dialog HTML element
     * @returns {HTMLElement} Dialog element
     */
    createDialog() {
        const dialog = document.createElement('div');
        dialog.className = 'notification-permission-dialog';
        dialog.setAttribute('role', 'dialog');
        dialog.setAttribute('aria-modal', 'true');
        dialog.setAttribute('aria-labelledby', 'notification-dialog-title');
        dialog.setAttribute('aria-describedby', 'notification-dialog-description');
        
        dialog.innerHTML = `
            <div class="notification-permission-overlay" aria-hidden="true"></div>
            <div class="notification-permission-content">
                <div class="notification-permission-icon" aria-hidden="true">
                    <i class="fas fa-bell"></i>
                </div>
                <h3 id="notification-dialog-title">Bildirimler</h3>
                <p id="notification-dialog-description">
                    Misafirlerden gelen shuttle taleplerini anında almak için bildirim izni verin.
                </p>
                <div class="notification-permission-actions">
                    <button class="btn-allow" 
                            aria-label="Bildirim izni ver ve bildirimleri aktif et"
                            type="button">
                        <i class="fas fa-check" aria-hidden="true"></i> İzin Ver
                    </button>
                    <button class="btn-later" 
                            aria-label="Şimdi bildirim izni verme, daha sonra sor"
                            type="button">
                        Şimdi Değil
                    </button>
                </div>
            </div>
        `;
        
        // Event listener'ları ekle - daha güvenli ve debug edilebilir
        const allowBtn = dialog.querySelector('.btn-allow');
        const laterBtn = dialog.querySelector('.btn-later');
        
        console.log('[NotificationPermission] Buttons found:', { allowBtn: !!allowBtn, laterBtn: !!laterBtn });
        
        if (allowBtn) {
            // Multiple event types for better compatibility
            const handleAllowClick = (e) => {
                console.log('[NotificationPermission] Allow button clicked!', e);
                e.preventDefault();
                e.stopPropagation();
                this.handleAllow();
            };
            
            allowBtn.addEventListener('click', handleAllowClick, { once: true });
            allowBtn.addEventListener('touchend', handleAllowClick, { once: true });
            
            // Test button accessibility
            console.log('[NotificationPermission] Allow button style:', {
                pointerEvents: window.getComputedStyle(allowBtn).pointerEvents,
                display: window.getComputedStyle(allowBtn).display,
                visibility: window.getComputedStyle(allowBtn).visibility
            });
        } else {
            console.error('[NotificationPermission] Allow button not found!');
        }
        
        if (laterBtn) {
            const handleLaterClick = (e) => {
                console.log('[NotificationPermission] Later button clicked!', e);
                e.preventDefault();
                e.stopPropagation();
                this.handleLater();
            };
            
            laterBtn.addEventListener('click', handleLaterClick, { once: true });
            laterBtn.addEventListener('touchend', handleLaterClick, { once: true });
        } else {
            console.error('[NotificationPermission] Later button not found!');
        }
        
        return dialog;
    }

    /**
     * Handle "Allow" button click
     */
    async handleAllow() {
        console.log('[NotificationPermission] User clicked Allow');
        
        // Close dialog immediately for better UX
        this.closeDialog();
        
        try {
            // Browser support check
            if (!('Notification' in window)) {
                console.error('[NotificationPermission] Notifications not supported');
                return;
            }

            // Check if pushNotifications is available
            if (typeof pushNotifications === 'undefined' || !pushNotifications.requestPermission) {
                console.error('[NotificationPermission] PushNotificationManager not available');
                // Try direct browser API
                const permission = await Notification.requestPermission();
                console.log('[NotificationPermission] Direct permission result:', permission);
                await this.updateSessionStatus(permission);
                
                if (permission === 'granted') {
                    this.showSuccessToast('Bildirimler aktif edildi! 🔔');
                }
                return;
            }

            // Request browser permission via PushNotificationManager
            const permission = await pushNotifications.requestPermission();
            console.log('[NotificationPermission] Permission result:', permission);

            // Update session
            await this.updateSessionStatus(permission);

            // Show success message if granted
            if (permission === 'granted') {
                this.showSuccessToast('Bildirimler aktif edildi! 🔔');
            }
        } catch (error) {
            console.error('[NotificationPermission] Error requesting permission:', error);
            
            // Update session anyway
            try {
                await this.updateSessionStatus('denied');
            } catch (updateError) {
                console.error('[NotificationPermission] Error updating session after permission error:', updateError);
            }
        }
    }

    /**
     * Handle "Later" button click
     */
    async handleLater() {
        try {
            console.log('[NotificationPermission] User clicked Later');
            
            // Update session (asked but not granted)
            await this.updateSessionStatus('default');

            // Close dialog
            this.closeDialog();
        } catch (error) {
            console.error('[NotificationPermission] Error in handleLater:', error);
            // Still close dialog even if update fails
            this.closeDialog();
        }
    }

    /**
     * Update session status via API
     * @param {string} status - Permission status
     */
    async updateSessionStatus(status) {
        try {
            // Validate status value
            const validStatuses = ['default', 'granted', 'denied'];
            if (!validStatuses.includes(status)) {
                console.warn('[NotificationPermission] Invalid status value:', status);
                status = 'default';
            }

            const response = await fetch('/api/notification-permission', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                },
                body: JSON.stringify({ status })
            });

            if (response.ok) {
                console.log('[NotificationPermission] Session updated:', status);
            } else {
                const errorText = await response.text().catch(() => 'Unknown error');
                console.error('[NotificationPermission] Failed to update session:', response.status, errorText);
            }
        } catch (error) {
            // Network error handling
            if (error instanceof TypeError && error.message.includes('fetch')) {
                console.error('[NotificationPermission] Network error - unable to reach server:', error);
            } else {
                console.error('[NotificationPermission] Error updating session:', error);
            }
            // Don't block user flow on network errors
        }
    }

    /**
     * Close dialog with animation
     */
    closeDialog() {
        try {
            if (this.dialog) {
                this.dialog.classList.remove('show');
                setTimeout(() => {
                    try {
                        if (this.dialog && this.dialog.parentNode) {
                            this.dialog.remove();
                        }
                        this.dialog = null;
                        
                        // Restore focus to previous element
                        if (this.previousFocusElement && typeof this.previousFocusElement.focus === 'function') {
                            try {
                                this.previousFocusElement.focus();
                            } catch (focusError) {
                                console.warn('[NotificationPermission] Could not restore focus:', focusError);
                            }
                        }
                        this.previousFocusElement = null;
                    } catch (error) {
                        console.error('[NotificationPermission] Error removing dialog:', error);
                        this.dialog = null;
                        this.previousFocusElement = null;
                    }
                }, 300);
            }
        } catch (error) {
            console.error('[NotificationPermission] Error closing dialog:', error);
            this.dialog = null;
            this.previousFocusElement = null;
        }
    }

    /**
     * Show success toast message
     * @param {string} message - Message to display
     */
    showSuccessToast(message) {
        try {
            const toast = document.createElement('div');
            toast.className = 'notification-permission-toast';
            toast.innerHTML = `
                <div style="display: flex; align-items: center; gap: 12px;">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" style="flex-shrink: 0;">
                        <path d="M9 12L11 14L15 10M21 12C21 16.9706 16.9706 21 12 21C7.02944 21 3 16.9706 3 12C3 7.02944 7.02944 3 12 3C16.9706 3 21 7.02944 21 12Z" 
                              stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                    <span>${message}</span>
                </div>
            `;
            
            toast.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                background: #10b981;
                color: white;
                padding: 16px 20px;
                border-radius: 12px;
                box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
                z-index: 10001;
                animation: slideInRight 0.3s ease-out;
            `;

            document.body.appendChild(toast);

            setTimeout(() => {
                try {
                    toast.style.animation = 'slideInRight 0.3s ease-in reverse';
                    setTimeout(() => {
                        try {
                            toast.remove();
                        } catch (error) {
                            console.error('[NotificationPermission] Error removing toast:', error);
                        }
                    }, 300);
                } catch (error) {
                    console.error('[NotificationPermission] Error animating toast:', error);
                }
            }, 3000);
        } catch (error) {
            console.error('[NotificationPermission] Error showing success toast:', error);
        }
    }
}

/**
 * Get CSRF token from meta tag
 * @returns {string} CSRF token
 */
function getCSRFToken() {
    try {
        const meta = document.querySelector('meta[name="csrf-token"]');
        return meta ? meta.getAttribute('content') : '';
    } catch (error) {
        console.error('[NotificationPermission] Error getting CSRF token:', error);
        return '';
    }
}

// Create global instance
const notificationPermissionHandler = new NotificationPermissionHandler();

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = notificationPermissionHandler;
}

console.log('[NotificationPermission] Handler loaded');
