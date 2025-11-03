/**
 * Buggy Call - Driver Dashboard JavaScript
 * Real-time request management for drivers
 */

const DriverDashboard = {
    hotelId: null,
    buggyId: null,
    userId: null,
    socket: null,
    currentRequest: null,
    pendingRequests: [],

    /**
     * Initialize driver dashboard
     */
    async init() {
        console.log('Driver dashboard initializing...');
        
        // Get data from session
        this.hotelId = parseInt(document.body.dataset.hotelId) || 1;
        this.userId = parseInt(document.body.dataset.userId) || 0;
        this.buggyId = parseInt(document.body.dataset.buggyId) || 0;
        const needsLocationSetup = document.body.dataset.needsLocationSetup === 'true';
        
        // Check if driver has buggy assigned
        if (!this.buggyId || this.buggyId === '0') {
            console.warn('No buggy assigned to driver');
            return;
        }
        
        // Show location setup modal if needed
        if (needsLocationSetup) {
            await this.showLocationSetupModal();
            return;
        }
        
        // Initialize Socket.IO if available
        if (typeof io !== 'undefined') {
            this.initSocket();
        } else {
            console.warn('Socket.IO not available');
        }
        
        // Load initial data
        await this.loadDriverData();
        
        // Setup event listeners
        this.setupEventListeners();
        
        console.log('Driver dashboard initialized');
    },

    /**
     * Show location setup modal
     */
    async showLocationSetupModal() {
        try {
            // Load locations
            const response = await fetch(`/api/locations?hotel_id=${this.hotelId}`);
            const data = await response.json();
            
            if (!response.ok || !data.success) {
                throw new Error(data.error || 'Lokasyonlar yüklenemedi');
            }
            
            const locations = data.locations || data.data?.items || [];
            
            if (locations.length === 0) {
                await BuggyModal.alert('Henüz lokasyon tanımlanmamış. Lütfen yöneticinizle iletişime geçin.');
                return;
            }
            
            const locationOptions = locations.map(loc => 
                `<option value="${loc.id}">${loc.name}</option>`
            ).join('');
            
            const modalContent = `
                <div class="space-y-4">
                    <p class="text-center text-muted">Lütfen başlangıç konumunuzu seçin:</p>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Lokasyon *</label>
                        <select id="initial-location" 
                                class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
                                required>
                            <option value="">Lokasyon Seçin</option>
                            ${locationOptions}
                        </select>
                    </div>
                </div>
            `;
            
            const result = await BuggyModal.custom(modalContent, {
                title: '📍 Başlangıç Konumu',
                confirmText: 'Devam Et',
                cancelText: 'İptal',
                size: 'medium'
            });
            
            if (result) {
                const locationId = document.getElementById('initial-location').value;
                
                if (!locationId) {
                    await BuggyModal.alert('Lütfen bir lokasyon seçin!');
                    return this.showLocationSetupModal(); // Show again
                }
                
                // Set initial location
                await this.setInitialLocation(locationId);
            }
        } catch (error) {
            console.error('Error showing location setup modal:', error);
            await BuggyModal.alert('Lokasyonlar yüklenirken hata oluştu: ' + error.message);
        }
    },

    /**
     * Set initial location
     */
    async setInitialLocation(locationId) {
        try {
            const response = await fetch('/api/driver/set-initial-location', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ location_id: parseInt(locationId) })
            });
            
            const data = await response.json();
            
            if (!response.ok || !data.success) {
                throw new Error(data.error || 'Lokasyon ayarlanamadı');
            }
            
            await BuggyModal.alert('Lokasyon başarıyla ayarlandı! Sisteme hoş geldiniz.');
            
            // Reload page to initialize dashboard
            window.location.reload();
        } catch (error) {
            console.error('Error setting initial location:', error);
            await BuggyModal.alert('Lokasyon ayarlanırken hata oluştu: ' + error.message);
        }
    },

    /**
     * Initialize WebSocket connection
     */
    initSocket() {
        if (typeof io === 'undefined') {
            console.error('Socket.IO not loaded');
            return;
        }
        
        // Connect to Socket.IO server
        this.socket = io({
            transports: ['polling', 'websocket'],
            reconnection: true,
            reconnectionDelay: 1000,
            reconnectionAttempts: 5
        });
        
        // Join hotel drivers room
        this.socket.on('connect', () => {
            console.log('Socket connected');
            this.socket.emit('join_hotel', {
                hotel_id: this.hotelId,
                role: 'driver'
            });
        });
        
        // Listen to new requests
        this.socket.on('new_request', (data) => {
            console.log('New request received:', data);
            this.handleNewRequest(data);
        });
        
        // Listen to request taken by another driver
        this.socket.on('request_taken', (data) => {
            console.log('Request taken:', data);
            this.removeRequest(data.request_id);
        });
        
        // Listen to request cancelled
        this.socket.on('request_cancelled', (data) => {
            console.log('Request cancelled:', data);
            if (this.currentRequest && this.currentRequest.id === data.request_id) {
                this.currentRequest = null;
            }
            this.removeRequest(data.request_id);
        });
        
        this.socket.on('disconnect', () => {
            console.log('Socket disconnected');
        });
    },

    /**
     * Load driver data
     */
    async loadDriverData() {
        try {
            // Load pending requests
            await this.loadPendingRequests();
            
            // Load current request if any
            await this.loadCurrentRequest();
            
            // Load today's completed requests
            await this.loadCompletedToday();
        } catch (error) {
            console.error('Error loading driver data:', error);
        }
    },

    /**
     * Load pending requests
     */
    async loadPendingRequests() {
        try {
            const response = await fetch('/api/driver/pending-requests');
            const data = await response.json();
            
            if (!response.ok || !data.success) {
                throw new Error(data.error || 'Talepler yüklenemedi');
            }
            
            this.pendingRequests = data.requests || [];
            console.log('Pending requests loaded:', this.pendingRequests);
            this.renderPendingRequests();
            this.updatePendingCount();
        } catch (error) {
            console.error('Error loading pending requests:', error);
        }
    },

    /**
     * Load current request
     */
    async loadCurrentRequest() {
        try {
            const response = await fetch('/api/driver/active-request');
            const data = await response.json();
            
            if (!response.ok || !data.success) {
                throw new Error(data.error || 'Aktif talep yüklenemedi');
            }
            
            this.currentRequest = data.request;
            this.renderCurrentRequest();
        } catch (error) {
            console.error('Error loading current request:', error);
        }
    },

    /**
     * Load completed today
     */
    async loadCompletedToday() {
        try {
            const response = await fetch('/api/requests?status=completed');
            const data = await response.json();
            
            if (!response.ok || !data.success) {
                return;
            }
            
            const requests = data.requests || [];
            const today = new Date().toISOString().split('T')[0];
            const completedToday = requests.filter(r => {
                if (r.completed_at) {
                    const completedDate = r.completed_at.split('T')[0];
                    return completedDate === today;
                }
                return false;
            }).length;
            
            const el = document.getElementById('completed-today');
            if (el) el.textContent = completedToday;
        } catch (error) {
            console.error('Error loading completed today:', error);
        }
    },

    /**
     * Render pending requests
     */
    renderPendingRequests() {
        const container = document.getElementById('pending-requests');
        const badge = document.getElementById('pending-badge');
        
        if (!container) return;
        
        if (this.pendingRequests.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-check-circle"></i>
                    <p>Bekleyen talep yok</p>
                </div>
            `;
            if (badge) badge.textContent = '0';
            return;
        }
        
        if (badge) badge.textContent = this.pendingRequests.length;
        
        container.innerHTML = this.pendingRequests.map(req => {
            console.log('Rendering request:', req);
            if (!req.id) {
                console.error('Request missing ID:', req);
                return '';
            }
            
            const timeAgo = this.getTimeAgo(req.requested_at);
            
            return `
            <div class="request-card" data-id="${req.id}">
                <div class="request-header">
                    <div class="request-location">
                        <i class="fas fa-map-marker-alt"></i>
                        ${req.location?.name || 'Bilinmiyor'}
                    </div>
                    <div class="request-time">
                        <i class="fas fa-clock"></i> ${timeAgo}
                    </div>
                </div>
                <div class="request-details">
                    ${req.guest_name ? `
                        <div class="request-detail">
                            <i class="fas fa-user"></i>
                            <span>${req.guest_name}</span>
                        </div>
                    ` : ''}
                    ${req.room_number ? `
                        <div class="request-detail">
                            <i class="fas fa-door-open"></i>
                            <span>Oda ${req.room_number}</span>
                        </div>
                    ` : ''}
                    ${req.phone_number ? `
                        <div class="request-detail">
                            <i class="fas fa-phone"></i>
                            <span>${req.phone_number}</span>
                        </div>
                    ` : ''}
                </div>
                ${req.notes ? `
                    <div class="request-detail" style="margin-top: 0.5rem; color: #6c757d;">
                        <i class="fas fa-comment"></i>
                        <span>${req.notes}</span>
                    </div>
                ` : ''}
                <div class="request-actions">
                    <button class="btn-accept" onclick="DriverDashboard.acceptRequest(${req.id})">
                        <i class="fas fa-check"></i> Kabul Et
                    </button>
                </div>
            </div>
        `;
        }).join('');
    },

    /**
     * Render current request
     */
    renderCurrentRequest() {
        const container = document.getElementById('current-request');
        const section = document.getElementById('current-request-section');
        const activeCount = document.getElementById('active-request-count');
        
        if (!container) return;
        
        if (!this.currentRequest) {
            // Hide the entire section when no active request
            if (section) section.style.display = 'none';
            if (activeCount) activeCount.textContent = '0';
            return;
        }
        
        // Show the section when there's an active request
        if (section) section.style.display = 'block';
        
        if (activeCount) activeCount.textContent = '1';
        
        const req = this.currentRequest;
        const timeAgo = this.getTimeAgo(req.accepted_at);
        
        container.innerHTML = `
            <div class="request-card active">
                <div class="request-header">
                    <div class="request-location">
                        <i class="fas fa-map-marker-alt"></i>
                        ${req.location?.name || 'Bilinmiyor'}
                    </div>
                    <div class="request-time">
                        <i class="fas fa-check-circle"></i> ${timeAgo}
                    </div>
                </div>
                <div class="request-details">
                    ${req.guest_name ? `
                        <div class="request-detail">
                            <i class="fas fa-user"></i>
                            <span>${req.guest_name}</span>
                        </div>
                    ` : ''}
                    ${req.room_number ? `
                        <div class="request-detail">
                            <i class="fas fa-door-open"></i>
                            <span>Oda ${req.room_number}</span>
                        </div>
                    ` : ''}
                    ${req.phone_number ? `
                        <div class="request-detail">
                            <i class="fas fa-phone"></i>
                            <span>${req.phone_number}</span>
                        </div>
                    ` : ''}
                </div>
                ${req.notes ? `
                    <div class="request-detail" style="margin-top: 0.5rem; color: #6c757d;">
                        <i class="fas fa-comment"></i>
                        <span>${req.notes}</span>
                    </div>
                ` : ''}
                <div class="request-actions">
                    <button class="btn-complete" onclick="DriverDashboard.completeRequest(${req.id})">
                        <i class="fas fa-check-double"></i> Tamamla
                    </button>
                </div>
            </div>
        `;
    },

    /**
     * Update pending count
     */
    updatePendingCount() {
        const el = document.getElementById('pending-request-count');
        if (el) el.textContent = this.pendingRequests.length;
    },

    /**
     * Accept request
     */
    async acceptRequest(requestId) {
        try {
            const response = await fetch(`/api/driver/accept-request/${requestId}`, {
                method: 'POST'
            });
            
            const data = await response.json();
            
            if (!response.ok || !data.success) {
                throw new Error(data.error || 'Talep kabul edilemedi');
            }
            
            await BuggyModal.alert('Talep başarıyla kabul edildi!');
            
            // Reload data
            await this.loadDriverData();
        } catch (error) {
            console.error('Error accepting request:', error);
            await BuggyModal.alert('Talep kabul edilirken hata oluştu: ' + error.message);
        }
    },

    /**
     * Complete request
     */
    async completeRequest(requestId) {
        // Show location selection modal
        await this.showLocationSelectionModal(requestId);
    },

    /**
     * Show location selection modal
     */
    async showLocationSelectionModal(requestId) {
        try {
            // Load locations
            const response = await fetch(`/api/locations?hotel_id=${this.hotelId}`);
            const data = await response.json();
            
            if (!response.ok || !data.success) {
                throw new Error(data.error || 'Lokasyonlar yüklenemedi');
            }
            
            const locations = data.locations || data.data?.items || [];
            
            const locationOptions = locations.map(loc => 
                `<option value="${loc.id}">${loc.name}</option>`
            ).join('');
            
            const modalContent = `
                <div class="space-y-4">
                    <p class="text-center text-muted">Talebi tamamladıktan sonra şu anki konumunuzu seçin:</p>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Şu Anki Konumunuz *</label>
                        <select id="current-location" 
                                class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
                                required>
                            <option value="">Lokasyon Seçin</option>
                            ${locationOptions}
                        </select>
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Notlar (Opsiyonel)</label>
                        <textarea id="completion-notes" 
                                  class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
                                  rows="3"
                                  placeholder="Varsa ek notlar..."></textarea>
                    </div>
                </div>
            `;
            
            const result = await BuggyModal.custom(modalContent, {
                title: '✅ Talebi Tamamla',
                confirmText: 'Tamamla',
                cancelText: 'İptal',
                size: 'medium'
            });
            
            if (result) {
                const locationId = document.getElementById('current-location').value;
                const notes = document.getElementById('completion-notes').value;
                
                if (!locationId) {
                    await BuggyModal.alert('Lütfen şu anki konumunuzu seçin!');
                    return this.showLocationSelectionModal(requestId); // Show again
                }
                
                // Complete request
                await this.submitCompletion(requestId, locationId, notes);
            }
        } catch (error) {
            console.error('Error showing location selection modal:', error);
            await BuggyModal.alert('Lokasyonlar yüklenirken hata oluştu: ' + error.message);
        }
    },

    /**
     * Submit completion
     */
    async submitCompletion(requestId, locationId, notes) {
        try {
            const response = await fetch(`/api/requests/${requestId}/complete`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    current_location_id: parseInt(locationId),
                    notes: notes || ''
                })
            });
            
            const data = await response.json();
            
            if (!response.ok || !data.success) {
                throw new Error(data.error || 'Talep tamamlanamadı');
            }
            
            await BuggyModal.alert('Talep başarıyla tamamlandı!');
            
            // Reload data
            await this.loadDriverData();
        } catch (error) {
            console.error('Error completing request:', error);
            await BuggyModal.alert('Talep tamamlanırken hata oluştu: ' + error.message);
        }
    },

    /**
     * Handle new request
     */
    handleNewRequest(data) {
        // Check if request already exists
        const exists = this.pendingRequests.some(r => r.id === data.request_id);
        if (exists) {
            console.log('Request already in list, skipping');
            return;
        }
        
        // Format the request data properly
        const formattedRequest = {
            id: data.request_id,
            guest_name: data.guest_name,
            room_number: data.room_number,
            phone_number: data.phone_number,
            location: data.location,
            requested_at: data.requested_at,
            notes: data.notes
        };
        
        // Add to pending requests
        this.pendingRequests.unshift(formattedRequest);
        this.renderPendingRequests();
        this.updatePendingCount();
        
        // Play notification sound
        this.playNotificationSound();
        
        // Show notification with location
        const locationName = data.location?.name || 'Bilinmeyen Lokasyon';
        const roomInfo = data.room_number ? ` - Oda: ${data.room_number}` : '';
        const guestInfo = data.guest_name ? `\nMisafir: ${data.guest_name}` : '';
        const message = `📍 ${locationName}${roomInfo}${guestInfo}\n\nYeni talep geldi!`;
        
        alert(message);
    },

    /**
     * Play notification sound
     */
    playNotificationSound() {
        try {
            // Use Web Audio API to generate notification sound
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            
            // Create oscillator for beep sound
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            // Configure sound - pleasant notification tone
            oscillator.frequency.value = 800; // Hz
            oscillator.type = 'sine';
            
            // Volume envelope
            gainNode.gain.setValueAtTime(0, audioContext.currentTime);
            gainNode.gain.linearRampToValueAtTime(0.3, audioContext.currentTime + 0.01);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
            
            // Play sound
            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + 0.5);
            
            // Play second beep
            setTimeout(() => {
                const osc2 = audioContext.createOscillator();
                const gain2 = audioContext.createGain();
                
                osc2.connect(gain2);
                gain2.connect(audioContext.destination);
                
                osc2.frequency.value = 1000;
                osc2.type = 'sine';
                
                gain2.gain.setValueAtTime(0, audioContext.currentTime);
                gain2.gain.linearRampToValueAtTime(0.3, audioContext.currentTime + 0.01);
                gain2.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
                
                osc2.start(audioContext.currentTime);
                osc2.stop(audioContext.currentTime + 0.5);
            }, 200);
            
            // Vibrate if supported
            if (window.navigator && window.navigator.vibrate) {
                window.navigator.vibrate([200, 100, 200]);
            }
        } catch (error) {
            console.error('Error playing notification sound:', error);
            // Fallback to vibration only
            if (window.navigator && window.navigator.vibrate) {
                window.navigator.vibrate([200, 100, 200, 100, 200]);
            }
        }
    },

    /**
     * Remove request
     */
    removeRequest(requestId) {
        this.pendingRequests = this.pendingRequests.filter(r => r.id !== requestId);
        this.renderPendingRequests();
        this.updatePendingCount();
    },

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Event listeners can be added here if needed in the future
    },

    /**
     * Format date
     */
    formatDate(dateStr) {
        if (!dateStr) return '';
        const date = new Date(dateStr);
        return date.toLocaleString('tr-TR', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    },

    /**
     * Get time ago
     */
    getTimeAgo(dateStr) {
        if (!dateStr) return '';
        
        const date = new Date(dateStr);
        const now = new Date();
        const seconds = Math.floor((now - date) / 1000);
        
        if (seconds < 60) return 'Az önce';
        
        const minutes = Math.floor(seconds / 60);
        if (minutes < 60) return `${minutes} dakika önce`;
        
        const hours = Math.floor(minutes / 60);
        if (hours < 24) return `${hours} saat önce`;
        
        const days = Math.floor(hours / 24);
        return `${days} gün önce`;
    }
};

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => DriverDashboard.init());
} else {
    DriverDashboard.init();
}

// Export to global scope
window.DriverDashboard = DriverDashboard;
