/**
 * Timezone Helper for Cyprus (Kıbrıs)
 * Converts UTC timestamps to Cyprus local time
 * 
 * Cyprus Timezone: Europe/Nicosia (UTC+2 winter, UTC+3 summer with DST)
 */

const TimezoneHelper = {
    // Cyprus timezone
    TIMEZONE: 'Europe/Nicosia',
    
    /**
     * Convert UTC timestamp to Cyprus local time
     * @param {string|Date} utcTimestamp - UTC timestamp (ISO string or Date object)
     * @returns {Date} - Date object in Cyprus timezone
     */
    toLocalTime(utcTimestamp) {
        if (!utcTimestamp) return null;
        
        const date = typeof utcTimestamp === 'string' ? new Date(utcTimestamp) : utcTimestamp;
        return new Date(date.toLocaleString('en-US', { timeZone: this.TIMEZONE }));
    },
    
    /**
     * Format UTC timestamp to Cyprus local time string
     * @param {string|Date} utcTimestamp - UTC timestamp
     * @param {object} options - Intl.DateTimeFormat options
     * @returns {string} - Formatted date string
     */
    formatLocal(utcTimestamp, options = {}) {
        if (!utcTimestamp) return '';
        
        const date = typeof utcTimestamp === 'string' ? new Date(utcTimestamp) : utcTimestamp;
        
        const defaultOptions = {
            timeZone: this.TIMEZONE,
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: false
        };
        
        return date.toLocaleString('tr-TR', { ...defaultOptions, ...options });
    },
    
    /**
     * Format as "14 Kasım 2025 21:13"
     * @param {string|Date} utcTimestamp - UTC timestamp
     * @returns {string} - Formatted date string
     */
    formatFriendly(utcTimestamp) {
        if (!utcTimestamp) return '';
        
        const date = typeof utcTimestamp === 'string' ? new Date(utcTimestamp) : utcTimestamp;
        
        return date.toLocaleString('tr-TR', {
            timeZone: this.TIMEZONE,
            day: 'numeric',
            month: 'long',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            hour12: false
        });
    },
    
    /**
     * Format as "21:13:33"
     * @param {string|Date} utcTimestamp - UTC timestamp
     * @returns {string} - Time string
     */
    formatTime(utcTimestamp) {
        if (!utcTimestamp) return '';
        
        const date = typeof utcTimestamp === 'string' ? new Date(utcTimestamp) : utcTimestamp;
        
        return date.toLocaleString('tr-TR', {
            timeZone: this.TIMEZONE,
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: false
        });
    },
    
    /**
     * Format as "14.11.2025"
     * @param {string|Date} utcTimestamp - UTC timestamp
     * @returns {string} - Date string
     */
    formatDate(utcTimestamp) {
        if (!utcTimestamp) return '';
        
        const date = typeof utcTimestamp === 'string' ? new Date(utcTimestamp) : utcTimestamp;
        
        return date.toLocaleString('tr-TR', {
            timeZone: this.TIMEZONE,
            day: '2-digit',
            month: '2-digit',
            year: 'numeric'
        });
    },
    
    /**
     * Get elapsed time from UTC timestamp (e.g., "2 dakika önce")
     * @param {string|Date} utcTimestamp - UTC timestamp
     * @returns {string} - Elapsed time string
     */
    getElapsedTime(utcTimestamp) {
        if (!utcTimestamp) return '';
        
        const date = typeof utcTimestamp === 'string' ? new Date(utcTimestamp) : utcTimestamp;
        const now = new Date();
        const diffMs = now - date;
        const diffSeconds = Math.floor(diffMs / 1000);
        
        if (diffSeconds < 60) {
            return `${diffSeconds} saniye önce`;
        } else if (diffSeconds < 3600) {
            const minutes = Math.floor(diffSeconds / 60);
            return `${minutes} dakika önce`;
        } else if (diffSeconds < 86400) {
            const hours = Math.floor(diffSeconds / 3600);
            return `${hours} saat önce`;
        } else {
            const days = Math.floor(diffSeconds / 86400);
            return `${days} gün önce`;
        }
    },
    
    /**
     * Get current Cyprus local time
     * @returns {Date} - Current date in Cyprus timezone
     */
    now() {
        return new Date(new Date().toLocaleString('en-US', { timeZone: this.TIMEZONE }));
    },
    
    /**
     * Convert local Cyprus time to UTC
     * @param {Date} localDate - Local date in Cyprus timezone
     * @returns {Date} - UTC date
     */
    toUTC(localDate) {
        if (!localDate) return null;
        
        // Get the offset for Cyprus timezone
        const localString = localDate.toLocaleString('en-US', { timeZone: this.TIMEZONE });
        const localTime = new Date(localString);
        const offset = localDate - localTime;
        
        return new Date(localDate.getTime() - offset);
    }
};

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TimezoneHelper;
}

console.log('✅ Timezone Helper loaded (Cyprus/Nicosia - UTC+2/+3)');
