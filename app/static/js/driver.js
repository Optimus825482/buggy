/**
 * Shuttle Call - Driver Panel JavaScript
 * Real-time request management for drivers
 */

const Driver = {
    hotelId: null,
    buggyId: null,
    userId: null,
    socket: null,
    currentRequest: null,
    PENDINGRequests: [],

    /**
     * Initialize driver panel
     */
    async init() {
        console.log('Driver panel initializing...');
        
        // Get data from session
        this.hotelId = document.body.dataset.hotelId || 1;
        this.userId = document.body.dataset.userId;
        this.buggyId = document.body.dataset.buggyId;
        
        // Check if driver has buggy assigned
        if (!this.buggyId || this.buggyId === '0') {
            console.warn('No buggy assigned to driver');
            await BuggyCall.Utils.showWarning('Size henüz bir shuttle atanmamış. Lütfen yöneticinizle iletişime geçin.');
            return;
        }
        
        // Initialize Socket.IO
        this.initSocket();
        
        // Load initial data
        this.loadDriverData();
        
        // Setup event listeners
        this.setupEventListeners();
        
        // Play notification sound
        this.setupNotificationSound();
        
        console.log('Driver panel initialized');
    },

    /**
     * Initialize WebSocket connection
     */
    initSocket() {
        this.socket = BuggyCall.Socket.init();
        this.socket.connect();
        
        // Join hotel drivers room
        this.socket.on('connect', () => {
            this.socket.emit('join_hotel', {
                hotel_id: this.hotelId,
                role: 'driver'
            });
            this.updateStatus('available');
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
                this.updateStatus('available');
            }
            this.removeRequest(data.request_id);
        });
    },

    /**
     * Load driver data
     */
    async loadDriverData() {
        try {
            BuggyCall.Utils.showLoading();
            
            // Load PENDING requests
            await this.loadPendingRequests();
            
            // Load current request if any
            await this.loadCurrentRequest();
            
            // Load today's completed requests
            await this.loadCompletedToday();
            
            // Update UI
            this.updateDashboard();
            
            BuggyCall.Utils.hideLoading();
        } catch (error) {
            console.error('Error loading driver data:', error);
            await BuggyCall.Utils.showError('Veri yüklenirken hata oluştu: ' + error.message);
            BuggyCall.Utils.hideLoading();
        }
    },

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Accept request buttons (event delegation)
        document.addEventListener('click', (e) => {
            if (e.target.closest('[data-action="accept-request"]')) {
                const btn = e.target.closest('[data-action="accept-request"]');
                const requestId = btn.dataset.requestId;
                this.acceptRequest(requestId);
            }
        });
        
        // Complete request button
        const completeBtn = document.getElementById('complete-request-btn');
        if (completeBtn) {
            completeBtn.addEventListener('click', () => this.completeCurrentRequest());
        }
        
        // Location update
        const locationSelect = document.getElementById('driver-location');
        if (locationSelect) {
            locationSelect.addEventListener('change', (e) => {
                this.updateLocation(e.target.value);
            });
        }
        
        // Status toggle
        const statusToggle = document.getElementById('status-toggle');
        if (statusToggle) {
            statusToggle.addEventListener('change', (e) => {
                const status = e.target.checked ? 'available' : 'offline';
                this.updateStatus(status);
            });
        }
    },

    /**
     * Setup notification sound
     */
    setupNotificationSound() {
        // Create audio element for notification
        this.notificationSound = new Audio('data:audio/wav;base64,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');
    },

    /**
     * Load PENDING requests
     */
    async loadPendingRequests() {
        try {
            const response = await BuggyCall.API.get('/requests?status=PENDING');
            this.PENDINGRequests = response.requests || [];
            this.renderPendingRequests();
        } catch (error) {
            console.error('Error loading PENDING requests:', error);
        }
    },

    /**
     * Load current request
     */
    async loadCurrentRequest() {
        try {
            const response = await BuggyCall.API.get(`/requests?status=accepted&buggy_id=${this.buggyId}`);
            const requests = response.requests || [];
            if (requests.length > 0) {
                this.currentRequest = requests[0];
                this.renderCurrentRequest();
            }
        } catch (error) {
            console.error('Error loading current request:', error);
        }
    },

    /**
     * Load today's completed requests
     */
    async loadCompletedToday() {
        try {
            const response = await BuggyCall.API.get(`/requests?status=completed&buggy_id=${this.buggyId}`);
            const requests = response.requests || [];
            
            // Filter today's requests
            const today = new Date().toISOString().split('T')[0];
            const todayRequests = requests.filter(req => {
                if (req.completed_at) {
                    const completedDate = req.completed_at.split('T')[0];
                    return completedDate === today;
                }
                return false;
            });
            
            // Update counter
            const counter = document.getElementById('completed-today');
            if (counter) {
                counter.textContent = todayRequests.length;
            }
        } catch (error) {
            console.error('Error loading completed requests:', error);
        }
    },

    /**
     * Handle new request notification
     */
    handleNewRequest(data) {
        // Play notification sound
        if (this.notificationSound) {
            this.notificationSound.play().catch(e => console.log('Audio play failed:', e));
        }
        
        // Show toast notification
        BuggyCall.Utils.showToast(`Yeni talep: ${data.location.name}`, 'warning');
        
        // Add to PENDING requests
        this.PENDINGRequests.unshift(data);
        this.renderPendingRequests();
        
        // Update counter
        this.updateRequestCounter();
    },

    /**
     * Accept request
     */
    async acceptRequest(requestId) {
        try {
            BuggyCall.Utils.showLoading();
            
            const response = await BuggyCall.API.put(`/requests/${requestId}/accept`, {});
            
            if (response.success) {
                await BuggyCall.Utils.showSuccess('Talep başarıyla kabul edildi!');
                this.currentRequest = response.request;
                this.renderCurrentRequest();
                this.removeRequest(requestId);
                this.updateStatus('busy');
            }
            
            BuggyCall.Utils.hideLoading();
        } catch (error) {
            await BuggyCall.Utils.showError('Talep kabul edilirken hata oluştu: ' + error.message);
            BuggyCall.Utils.hideLoading();
        }
    },

    /**
     * Complete current request
     */
    async completeCurrentRequest() {
        if (!this.currentRequest) return;
        
        const confirmed = await BuggyCall.Utils.confirm(
            'Bu talebi tamamlamak istediğinizden emin misiniz?',
            'Talebi Tamamla'
        );
        
        if (!confirmed) {
            return;
        }
        
        try {
            // Show location selection modal
            const locationId = await this.showLocationSelectionModal();
            
            if (!locationId) {
                return; // User cancelled
            }
            
            BuggyCall.Utils.showLoading();
            
            await BuggyCall.API.put(`/requests/${this.currentRequest.id}/complete`, {
                current_location_id: locationId
            });
            
            await BuggyCall.Utils.showSuccess('Talep başarıyla tamamlandı!');
            this.currentRequest = null;
            this.renderCurrentRequest();
            this.updateStatus('available');
            
            BuggyCall.Utils.hideLoading();
        } catch (error) {
            await BuggyCall.Utils.showError('Talep tamamlanırken hata oluştu: ' + error.message);
            BuggyCall.Utils.hideLoading();
        }
    },

    /**
     * Show location selection modal
     */
    async showLocationSelectionModal() {
        return new Promise(async (resolve) => {
            try {
                // Load locations
                const response = await BuggyCall.API.get('/locations');
                const locations = response.locations || response.data?.items || [];
                
                if (locations.length === 0) {
                    await BuggyCall.Utils.showError('Lokasyon bulunamadı!');
                    resolve(null);
                    return;
                }
                
                // Create location cards HTML
                const locationCards = locations.map(loc => {
                    const imageOrIcon = loc.location_image 
                        ? `<img src="${loc.location_image}" alt="${this.escapeHtml(loc.name)}" style="width: 100%; height: 100%; object-fit: cover; border-radius: 11px;">`
                        : `<i class="fas fa-map-marker-alt" style="color: white; font-size: 1.5rem;"></i>`;
                    
                    return `
                        <button class="location-select-card" data-location-id="${loc.id}" style="
                            width: 100%;
                            padding: 1rem;
                            margin-bottom: 0.75rem;
                            background: white;
                            border: 2px solid #ddd;
                            border-radius: 12px;
                            cursor: pointer;
                            transition: all 0.2s ease;
                            display: flex;
                            align-items: center;
                            gap: 1rem;
                            text-align: left;
                        ">
                            <div style="
                                width: 60px;
                                height: 60px;
                                background: linear-gradient(135deg, #1BA5A8 0%, #158587 100%);
                                border-radius: 11px;
                                display: flex;
                                align-items: center;
                                justify-content: center;
                                flex-shrink: 0;
                                box-shadow: 0 4px 12px rgba(27, 165, 168, 0.25);
                            ">
                                ${imageOrIcon}
                            </div>
                            <div style="flex: 1; min-width: 0;">
                                <div style="font-weight: 600; color: #2C3E50; font-size: 1rem; margin-bottom: 0.25rem;">
                                    ${this.escapeHtml(loc.name)}
                                </div>
                                <div style="font-size: 0.875rem; color: #5A6C7D;">
                                    ${loc.description ? this.escapeHtml(loc.description) : 'Şu anda bu konumdasınız'}
                                </div>
                            </div>
                            <div style="flex-shrink: 0; color: #cbd5e1; font-size: 1.25rem;">
                                <i class="fas fa-chevron-right"></i>
                            </div>
                        </button>
                    `;
                }).join('');
                
                const modal = BuggyModal.showCustomModal({
                    title: 'Şu Anki Konumunuz',
                    type: 'info',
                    size: 'medium',
                    customContent: `
                        <div style="margin-bottom: 1rem;">
                            <p style="color: #5A6C7D; font-size: 0.875rem; margin-bottom: 1rem;">
                                Misafiri bıraktıktan sonra şu anda hangi konumdasınız?
                            </p>
                            <div id="location-cards-container" style="max-height: 400px; overflow-y: auto;">
                                ${locationCards}
                            </div>
                        </div>
                    `,
                    buttons: [
                        {
                            text: 'İptal',
                            class: 'btn-secondary',
                            onClick: () => {
                                BuggyModal.closeModal(modal);
                                resolve(null);
                            }
                        }
                    ]
                });
                
                // Add click handlers to location cards
                setTimeout(() => {
                    const cards = document.querySelectorAll('.location-select-card');
                    cards.forEach(card => {
                        card.addEventListener('click', () => {
                            const locationId = parseInt(card.dataset.locationId);
                            BuggyModal.closeModal(modal);
                            resolve(locationId);
                        });
                        
                        // Hover effect
                        card.addEventListener('mouseenter', () => {
                            card.style.borderColor = '#1BA5A8';
                            card.style.background = '#f0f9ff';
                            card.style.transform = 'translateY(-2px)';
                            card.style.boxShadow = '0 8px 20px rgba(27, 165, 168, 0.15)';
                        });
                        
                        card.addEventListener('mouseleave', () => {
                            card.style.borderColor = '#ddd';
                            card.style.background = 'white';
                            card.style.transform = 'translateY(0)';
                            card.style.boxShadow = 'none';
                        });
                    });
                }, 100);
                
            } catch (error) {
                console.error('Error loading locations:', error);
                await BuggyCall.Utils.showError('Lokasyonlar yüklenemedi!');
                resolve(null);
            }
        });
    },

    /**
     * Escape HTML to prevent XSS
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },

    /**
     * Remove request from PENDING list
     */
    removeRequest(requestId) {
        this.PENDINGRequests = this.PENDINGRequests.filter(r => r.request_id !== requestId && r.id !== requestId);
        this.renderPendingRequests();
        this.updateRequestCounter();
    },

    /**
     * Update driver status
     */
    updateStatus(status) {
        this.socket.emit('driver_status', {
            buggy_id: this.buggyId,
            status: status,
            hotel_id: this.hotelId
        });
        
        // Update UI
        const statusBadge = document.getElementById('driver-status-badge');
        if (statusBadge) {
            statusBadge.className = `badge ${BuggyCall.Utils.getBadgeClass(status)}`;
            statusBadge.textContent = this.getStatusText(status);
        }
    },

    /**
     * Update driver location
     */
    updateLocation(locationId) {
        this.socket.emit('driver_location', {
            buggy_id: this.buggyId,
            location_id: locationId,
            hotel_id: this.hotelId
        });
        
        BuggyCall.Utils.showToast('Lokasyon güncellendi', 'info');
    },

    /**
     * Render PENDING requests
     */
    renderPendingRequests() {
        const container = document.getElementById('PENDING-requests');
        if (!container) return;
        
        if (this.PENDINGRequests.length === 0) {
            container.innerHTML = '<div class="empty-state">Bekleyen talep yok</div>';
            return;
        }
        
        container.innerHTML = this.PENDINGRequests.map(req => `
            <div class="card request-card mb-2 hover-shadow" data-id="${req.request_id || req.id}">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-start">
                        <div class="flex-grow-1">
                            <h5 class="card-title">
                                <i class="fas fa-map-marker-alt text-primary"></i>
                                ${req.location?.name || 'Bilinmiyor'}
                            </h5>
                            ${req.room_number ? `<p class="mb-1"><i class="fas fa-door-open"></i> Oda: ${req.room_number}</p>` : ''}
                            <p class="text-muted mb-0">
                                <i class="fas fa-clock"></i>
                                ${BuggyCall.Utils.formatDate(req.requested_at)}
                            </p>
                        </div>
                        <button class="btn btn-success btn-lg" 
                                data-action="accept-request" 
                                data-request-id="${req.request_id || req.id}">
                            <i class="fas fa-check"></i> Kabul Et
                        </button>
                    </div>
                </div>
            </div>
        `).join('');
    },

    /**
     * Render current request
     */
    renderCurrentRequest() {
        const container = document.getElementById('current-request');
        if (!container) return;
        
        if (!this.currentRequest) {
            container.innerHTML = '<div class="empty-state">Aktif talep yok</div>';
            return;
        }
        
        const req = this.currentRequest;
        container.innerHTML = `
            <div class="card request-card-active">
                <div class="card-body">
                    <h4 class="card-title mb-3">
                        <i class="fas fa-route text-success"></i>
                        Aktif Talep
                    </h4>
                    <div class="mb-3">
                        <h5><i class="fas fa-map-marker-alt"></i> ${req.location?.name || 'Bilinmiyor'}</h5>
                        ${req.room_number ? `<p class="lead"><i class="fas fa-door-open"></i> Oda: ${req.room_number}</p>` : ''}
                    </div>
                    <div class="mb-3">
                        <p class="mb-1"><strong>Talep Zamanı:</strong> ${BuggyCall.Utils.formatDate(req.requested_at)}</p>
                        <p class="mb-1"><strong>Kabul Zamanı:</strong> ${BuggyCall.Utils.formatDate(req.accepted_at)}</p>
                        <p class="mb-0"><strong>Geçen Süre:</strong> <span id="elapsed-time">-</span></p>
                    </div>
                    <button id="complete-request-btn" class="btn btn-success btn-lg btn-block">
                        <i class="fas fa-check-circle"></i> Tamamla
                    </button>
                </div>
            </div>
        `;
        
        // Start elapsed time counter
        this.startElapsedTimeCounter();
    },

    /**
     * Start elapsed time counter
     */
    startElapsedTimeCounter() {
        if (this.elapsedTimeInterval) {
            clearInterval(this.elapsedTimeInterval);
        }
        
        if (!this.currentRequest) return;
        
        this.elapsedTimeInterval = setInterval(() => {
            const element = document.getElementById('elapsed-time');
            if (!element || !this.currentRequest) {
                clearInterval(this.elapsedTimeInterval);
                return;
            }
            
            const start = new Date(this.currentRequest.accepted_at);
            const now = new Date();
            const diffSeconds = Math.floor((now - start) / 1000);
            element.textContent = BuggyCall.Utils.formatDuration(diffSeconds);
        }, 1000);
    },

    /**
     * Update request counter
     */
    updateRequestCounter() {
        const counter = document.getElementById('PENDING-request-count');
        if (counter) {
            counter.textContent = this.PENDINGRequests.length;
        }
    },

    /**
     * Update dashboard
     */
    updateDashboard() {
        this.updateRequestCounter();
    },

    /**
     * Get status text in Turkish
     */
    getStatusText(status) {
        const statusMap = {
            'available': 'Müsait',
            'busy': 'Meşgul',
            'offline': 'Çevrimdışı'
        };
        return statusMap[status] || status;
    }
};

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => Driver.init());
} else {
    Driver.init();
}

// Export to global scope
window.Driver = Driver;
