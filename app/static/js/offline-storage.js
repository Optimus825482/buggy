/**
 * Offline Storage Handler - IndexedDB for Background Sync
 * Shuttle Call - Progressive Web App
 */

class OfflineStorage {
    constructor() {
        this.dbName = 'ShuttleCallDB';
        this.dbVersion = 6; // Synced with sw.js version
        this.db = null;
        this.init();
    }

    async init() {
        try {
            this.db = await this.openDatabase();
            // IndexedDB initialized
        } catch (error) {
            console.error('[Storage] Failed to initialize IndexedDB:', error.message || error);
            // Fallback: Uygulama çalışmaya devam edebilir, sadece offline özellikler devre dışı kalır
            this.db = null;
        }
    }

    openDatabase() {
        return new Promise((resolve, reject) => {
            if (!window.indexedDB) {
                console.warn('[Storage] IndexedDB not supported in this browser');
                reject(new Error('IndexedDB not supported'));
                return;
            }

            try {
                const request = indexedDB.open(this.dbName, this.dbVersion);

                request.onerror = (event) => {
                    const error = event.target.error;
                    console.error('[Storage] Database error:', error?.message || 'Unknown error');
                    
                    // Daha detaylı hata mesajı
                    if (error?.name === 'VersionError') {
                        console.error('[Storage] Database version conflict detected');
                    } else if (error?.name === 'QuotaExceededError') {
                        console.error('[Storage] Storage quota exceeded');
                    }
                    
                    reject(error || new Error('Failed to open database'));
                };

                request.onsuccess = (event) => {
                    const db = event.target.result;
                    
                    // Database error handler
                    db.onerror = (event) => {
                        console.error('[Storage] Database error:', event.target.error);
                    };
                    
                    resolve(db);
                };

                request.onupgradeneeded = (event) => {
                    try {
                        const db = event.target.result;

                        // Create object stores if they don't exist
                        if (!db.objectStoreNames.contains('PENDINGRequests')) {
                            const requestStore = db.createObjectStore('PENDINGRequests', {
                                keyPath: 'id',
                                autoIncrement: true
                            });
                            requestStore.createIndex('timestamp', 'timestamp', { unique: false });
                            requestStore.createIndex('type', 'type', { unique: false });
                        }

                        if (!db.objectStoreNames.contains('cachedData')) {
                            const dataStore = db.createObjectStore('cachedData', {
                                keyPath: 'key'
                            });
                            dataStore.createIndex('timestamp', 'timestamp', { unique: false });
                        }

                        console.log('[Storage] Database schema created successfully');
                    } catch (error) {
                        console.error('[Storage] Error creating database schema:', error);
                        reject(error);
                    }
                };

                request.onblocked = () => {
                    console.warn('[Storage] Database upgrade blocked - close other tabs');
                };
                
            } catch (error) {
                console.error('[Storage] Exception opening database:', error);
                reject(error);
            }
        });
    }

    /**
     * Add a PENDING request to be synced when online
     */
    async addPendingRequest(requestData) {
        try {
            if (!this.db) {
                await this.init();
            }

            const transaction = this.db.transaction(['PENDINGRequests'], 'readwrite');
            const store = transaction.objectStore('PENDINGRequests');

            const request = {
                url: requestData.url,
                method: requestData.method,
                headers: requestData.headers,
                body: requestData.body,
                type: requestData.type || 'general',
                timestamp: Date.now(),
                retries: 0
            };

            return new Promise((resolve, reject) => {
                const addRequest = store.add(request);

                addRequest.onsuccess = () => {
                    console.log('[Storage] Pending request added:', request.url);
                    resolve(addRequest.result);
                };

                addRequest.onerror = () => {
                    console.error('[Storage] Failed to add PENDING request');
                    reject(addRequest.error);
                };
            });
        } catch (error) {
            console.error('[Storage] Error adding PENDING request:', error);
            throw error;
        }
    }

    /**
     * Get all PENDING requests
     */
    async getPendingRequests() {
        try {
            if (!this.db) {
                await this.init();
            }

            const transaction = this.db.transaction(['PENDINGRequests'], 'readonly');
            const store = transaction.objectStore('PENDINGRequests');

            return new Promise((resolve, reject) => {
                const request = store.getAll();

                request.onsuccess = () => {
                    console.log('[Storage] Retrieved PENDING requests:', request.result.length);
                    resolve(request.result);
                };

                request.onerror = () => {
                    console.error('[Storage] Failed to get PENDING requests');
                    reject(request.error);
                };
            });
        } catch (error) {
            console.error('[Storage] Error getting PENDING requests:', error);
            return [];
        }
    }

    /**
     * Remove a PENDING request after successful sync
     */
    async removePendingRequest(id) {
        try {
            if (!this.db) {
                await this.init();
            }

            const transaction = this.db.transaction(['PENDINGRequests'], 'readwrite');
            const store = transaction.objectStore('PENDINGRequests');

            return new Promise((resolve, reject) => {
                const request = store.delete(id);

                request.onsuccess = () => {
                    console.log('[Storage] Pending request removed:', id);
                    resolve(true);
                };

                request.onerror = () => {
                    console.error('[Storage] Failed to remove PENDING request');
                    reject(request.error);
                };
            });
        } catch (error) {
            console.error('[Storage] Error removing PENDING request:', error);
            return false;
        }
    }

    /**
     * Update retry count for a PENDING request
     */
    async updateRetryCount(id, retries) {
        try {
            if (!this.db) {
                await this.init();
            }

            const transaction = this.db.transaction(['PENDINGRequests'], 'readwrite');
            const store = transaction.objectStore('PENDINGRequests');

            return new Promise((resolve, reject) => {
                const getRequest = store.get(id);

                getRequest.onsuccess = () => {
                    const data = getRequest.result;
                    if (data) {
                        data.retries = retries;
                        const updateRequest = store.put(data);

                        updateRequest.onsuccess = () => {
                            resolve(true);
                        };

                        updateRequest.onerror = () => {
                            reject(updateRequest.error);
                        };
                    } else {
                        reject(new Error('Request not found'));
                    }
                };

                getRequest.onerror = () => {
                    reject(getRequest.error);
                };
            });
        } catch (error) {
            console.error('[Storage] Error updating retry count:', error);
            return false;
        }
    }

    /**
     * Cache data for offline access
     */
    async cacheData(key, data, expiresIn = 3600000) {
        try {
            if (!this.db) {
                await this.init();
            }

            const transaction = this.db.transaction(['cachedData'], 'readwrite');
            const store = transaction.objectStore('cachedData');

            const cachedItem = {
                key: key,
                data: data,
                timestamp: Date.now(),
                expiresAt: Date.now() + expiresIn
            };

            return new Promise((resolve, reject) => {
                const request = store.put(cachedItem);

                request.onsuccess = () => {
                    console.log('[Storage] Data cached:', key);
                    resolve(true);
                };

                request.onerror = () => {
                    console.error('[Storage] Failed to cache data');
                    reject(request.error);
                };
            });
        } catch (error) {
            console.error('[Storage] Error caching data:', error);
            return false;
        }
    }

    /**
     * Get cached data
     */
    async getCachedData(key) {
        try {
            if (!this.db) {
                await this.init();
            }

            const transaction = this.db.transaction(['cachedData'], 'readonly');
            const store = transaction.objectStore('cachedData');

            return new Promise((resolve, reject) => {
                const request = store.get(key);

                request.onsuccess = () => {
                    const result = request.result;

                    if (!result) {
                        resolve(null);
                        return;
                    }

                    // Check if data has expired
                    if (result.expiresAt < Date.now()) {
                        console.log('[Storage] Cached data expired:', key);
                        this.removeCachedData(key);
                        resolve(null);
                        return;
                    }

                    console.log('[Storage] Retrieved cached data:', key);
                    resolve(result.data);
                };

                request.onerror = () => {
                    console.error('[Storage] Failed to get cached data');
                    reject(request.error);
                };
            });
        } catch (error) {
            console.error('[Storage] Error getting cached data:', error);
            return null;
        }
    }

    /**
     * Remove cached data
     */
    async removeCachedData(key) {
        try {
            if (!this.db) {
                await this.init();
            }

            const transaction = this.db.transaction(['cachedData'], 'readwrite');
            const store = transaction.objectStore('cachedData');

            return new Promise((resolve, reject) => {
                const request = store.delete(key);

                request.onsuccess = () => {
                    console.log('[Storage] Cached data removed:', key);
                    resolve(true);
                };

                request.onerror = () => {
                    reject(request.error);
                };
            });
        } catch (error) {
            console.error('[Storage] Error removing cached data:', error);
            return false;
        }
    }

    /**
     * Clear all expired cached data
     */
    async clearExpiredCache() {
        try {
            if (!this.db) {
                await this.init();
            }

            const transaction = this.db.transaction(['cachedData'], 'readwrite');
            const store = transaction.objectStore('cachedData');
            const index = store.index('timestamp');

            return new Promise((resolve, reject) => {
                const request = index.openCursor();
                let cleared = 0;

                request.onsuccess = (event) => {
                    const cursor = event.target.result;

                    if (cursor) {
                        if (cursor.value.expiresAt < Date.now()) {
                            cursor.delete();
                            cleared++;
                        }
                        cursor.continue();
                    } else {
                        console.log('[Storage] Cleared expired cache entries:', cleared);
                        resolve(cleared);
                    }
                };

                request.onerror = () => {
                    reject(request.error);
                };
            });
        } catch (error) {
            console.error('[Storage] Error clearing expired cache:', error);
            return 0;
        }
    }

    /**
     * Clear all data
     */
    async clearAll() {
        try {
            if (!this.db) {
                await this.init();
            }

            const transaction = this.db.transaction(['PENDINGRequests', 'cachedData'], 'readwrite');

            await Promise.all([
                new Promise((resolve) => {
                    transaction.objectStore('PENDINGRequests').clear().onsuccess = resolve;
                }),
                new Promise((resolve) => {
                    transaction.objectStore('cachedData').clear().onsuccess = resolve;
                })
            ]);

            console.log('[Storage] All data cleared');
            return true;
        } catch (error) {
            console.error('[Storage] Error clearing all data:', error);
            return false;
        }
    }

    /**
     * Get storage statistics
     */
    async getStats() {
        try {
            if (!this.db) {
                await this.init();
            }

            const transaction = this.db.transaction(['PENDINGRequests', 'cachedData'], 'readonly');

            const [PENDINGCount, cachedCount] = await Promise.all([
                new Promise((resolve) => {
                    transaction.objectStore('PENDINGRequests').count().onsuccess = (e) => {
                        resolve(e.target.result);
                    };
                }),
                new Promise((resolve) => {
                    transaction.objectStore('cachedData').count().onsuccess = (e) => {
                        resolve(e.target.result);
                    };
                })
            ]);

            return {
                PENDINGRequests: PENDINGCount,
                cachedItems: cachedCount
            };
        } catch (error) {
            console.error('[Storage] Error getting stats:', error);
            return {
                PENDINGRequests: 0,
                cachedItems: 0
            };
        }
    }
}

// Create global instance
const offlineStorage = new OfflineStorage();

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = offlineStorage;
}

// Offline storage handler loaded
