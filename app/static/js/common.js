/**
 * Buggy Call - Common JavaScript
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
            'pending': 'inline-flex items-center rounded-md bg-yellow-400/10 px-2 py-1 text-xs font-medium text-yellow-500 ring-1 ring-inset ring-yellow-400/20',
            'accepted': 'inline-flex items-center rounded-md bg-blue-400/10 px-2 py-1 text-xs font-medium text-blue-400 ring-1 ring-inset ring-blue-400/30',
            'completed': 'inline-flex items-center rounded-md bg-green-400/10 px-2 py-1 text-xs font-medium text-green-400 ring-1 ring-inset ring-green-500/20',
            'cancelled': 'inline-flex items-center rounded-md bg-red-400/10 px-2 py-1 text-xs font-medium text-red-400 ring-1 ring-inset ring-red-400/20',
            'available': 'inline-flex items-center rounded-md bg-green-400/10 px-2 py-1 text-xs font-medium text-green-400 ring-1 ring-inset ring-green-500/20',
            'busy': 'inline-flex items-center rounded-md bg-yellow-400/10 px-2 py-1 text-xs font-medium text-yellow-500 ring-1 ring-inset ring-yellow-400/20',
            'offline': 'inline-flex items-center rounded-md bg-gray-400/10 px-2 py-1 text-xs font-medium text-gray-400 ring-1 ring-inset ring-gray-400/20'
        };
        return statusMap[status] || 'inline-flex items-center rounded-md bg-gray-400/10 px-2 py-1 text-xs font-medium text-gray-400 ring-1 ring-inset ring-gray-400/20';
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

// Export globals
window.BuggyCall = {
    Utils,
    API,
    Socket,
    Form,
    CONFIG
};

console.log('Buggy Call initialized');
