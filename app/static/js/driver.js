/**
 * ========================================
 * SHUTTLE CALL - DRIVER DASHBOARD v3.0
 * Modern, Real-time, Production-Ready
 * ========================================
 */

const DriverDashboard = {
    // ==================== STATE ====================
    state: {
        hotelId: null,
        userId: null,
        buggyId: null,
        currentRequest: null,
        pendingRequests: [],
        completedToday: 0,
        isOnline: false,
        lastSync: null
    },

    // ==================== WEBSOCKET ====================
    socket: null,
    reconnectAttempts: 0,
    maxReconnectAttempts: 5,

    // ==================== TIMERS ====================
    timers: {
        elapsed: null,
        sync: null,
        heartbeat: null
    },

    // ==================== AUDIO ====================
    audio: {
        notification: null,
        enabled: true
    },

    /**
     * ========================================
     * INITIALIZATION
     * ========================================
     */
    async init() {
        console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
        console.log('🚀 Driver Dashboard v3.0 Initializing...');
        console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');

        try {
            // Load state from DOM
            console.log('📊 [INIT] Loading state from DOM...');
            this.loadStateFromDOM();

            // Validate buggy assignment
            if (!this.state.buggyId || this.state.buggyId === '0') {
                console.warn('⚠️ [INIT] No buggy assigned to driver');
                await this.showNoBuggyWarning();
                return;
            }

            // Initialize components
            console.log('🔧 [INIT] Initializing components...');
            await this.initializeComponents();

            // Load initial data
            console.log('📥 [INIT] Loading initial data...');
            await this.loadInitialData();

            // Setup event listeners
            console.log('👂 [INIT] Setting up event listeners...');
            this.setupEventListeners();

            // Start background tasks
            console.log('⏰ [INIT] Starting background tasks...');
            this.startBackgroundTasks();

            console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
            console.log('✅ Driver Dashboard Initialized Successfully');
            console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
        } catch (error) {
            console.error('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
            console.error('❌ Initialization Error:', error);
            console.error('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
            await BuggyCall.Utils.showError('Dashboard başlatılamadı: ' + error.message);
        }
    },

    /**
     * Load state from DOM data attributes
     */
    loadStateFromDOM() {
        const body = document.body;
        this.state.hotelId = parseInt(body.dataset.hotelId) || 1;
        this.state.userId = parseInt(body.dataset.userId) || 0;
        this.state.buggyId = parseInt(body.dataset.buggyId) || 0;

        console.log('📊 State loaded:', this.state);
    },

    /**
     * Initialize all components
     */
    async initializeComponents() {
        // Initialize WebSocket
        this.initWebSocket();

        // Initialize audio
        this.initAudio();

        // Initialize UI components
        this.initUI();
    },

    /**
     * ========================================
     * WEBSOCKET CONNECTION
     * ========================================
     */
    initWebSocket() {
        console.log('🔌 Initializing WebSocket...');

        try {
            this.socket = io({
                transports: ['websocket', 'polling'],
                reconnection: true,
                reconnectionDelay: 1000,
                reconnectionDelayMax: 5000,
                reconnectionAttempts: this.maxReconnectAttempts
            });

            // Connection events
            this.socket.on('connect', () => this.onSocketConnect());
            this.socket.on('disconnect', () => this.onSocketDisconnect());
            this.socket.on('connect_error', (error) => this.onSocketError(error));
            this.socket.on('joined_hotel', (data) => this.onJoinedHotel(data));

            // Request events
            this.socket.on('new_request', (data) => this.onNewRequest(data));
            this.socket.on('request_taken', (data) => this.onRequestTaken(data));
            this.socket.on('request_cancelled', (data) => this.onRequestCancelled(data));
            this.socket.on('request_completed', (data) => this.onRequestCompleted(data));

            // ✅ Guest events
            this.socket.on('guest_connected', (data) => this.onGuestConnected(data));

            console.log('✅ WebSocket initialized');
        } catch (error) {
            console.error('❌ WebSocket initialization failed:', error);
        }
    },

    /**
     * Socket connected
     */
    onSocketConnect() {
        console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
        console.log('✅ [WEBSOCKET] Socket Connected!');
        console.log('   - Socket ID:', this.socket.id);
        console.log('   - Transport:', this.socket.io.engine.transport.name);
        console.log('   - Hotel ID:', this.state.hotelId);
        console.log('   - User ID:', this.state.userId);
        console.log('   - Buggy ID:', this.state.buggyId);
        console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
        
        this.state.isOnline = true;
        this.reconnectAttempts = 0;

        // Join hotel drivers room
        console.log('📤 [WEBSOCKET] Emitting join_hotel event...');
        this.socket.emit('join_hotel', {
            hotel_id: this.state.hotelId,
            role: 'driver'
        });

        // Update UI
        this.updateConnectionStatus('connected');
    },

    /**
     * Successfully joined hotel room
     */
    onJoinedHotel(data) {
        console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
        console.log('✅ [WEBSOCKET] Successfully joined hotel room!');
        console.log('   - Hotel ID:', data.hotel_id);
        console.log('   - Role:', data.role);
        console.log('   - Room:', data.room);
        console.log('   - Socket ID:', this.socket.id);
        console.log('   - Now listening for guest_connected events...');
        console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
        
        // Test: Emit a test event to verify connection
        console.log('🧪 [TEST] Testing socket connection...');
        this.socket.emit('test_connection', { message: 'Driver dashboard connected' });
    },

    /**
     * Socket disconnected
     */
    onSocketDisconnect() {
        console.log('⚠️ WebSocket Disconnected');
        this.state.isOnline = false;
        this.updateConnectionStatus('disconnected');
    },

    /**
     * Socket error
     */
    onSocketError(error) {
        console.error('❌ WebSocket Error:', error);
        this.reconnectAttempts++;

        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            this.updateConnectionStatus('failed');
            BuggyCall.Utils.showError('Bağlantı kurulamadı. Lütfen sayfayı yenileyin.');
        } else {
            this.updateConnectionStatus('reconnecting');
        }
    },

    /**
     * ========================================
     * WEBSOCKET EVENT HANDLERS
     * ========================================
     */

    /**
     * New request received
     */
    async onNewRequest(data) {
        console.log('🔔 New Request:', data);

        // Play notification sound
        this.playNotificationSound();

        // Add to pending requests
        this.state.pendingRequests.unshift(data);

        // Update UI
        this.renderPendingRequests();
        this.updateCounters();

        // Show toast notification
        BuggyCall.Utils.showToast(`🔔 Yeni talep: ${data.location?.name || 'Bilinmeyen lokasyon'}`, 'info');

        // ✅ Show request dialog/modal
        this.showNewRequestDialog(data);
    },

    /**
     * Request taken by another driver
     */
    onRequestTaken(data) {
        console.log('👤 Request Taken:', data);

        // Remove from pending
        this.removeRequestFromPending(data.request_id);

        // Update UI
        this.renderPendingRequests();
        this.updateCounters();
    },

    /**
     * Request cancelled
     */
    onRequestCancelled(data) {
        console.log('❌ Request Cancelled:', data);

        // Remove from pending
        this.removeRequestFromPending(data.request_id);

        // If it's current request, clear it
        if (this.state.currentRequest && this.state.currentRequest.id === data.request_id) {
            this.state.currentRequest = null;
            this.renderCurrentRequest();
        }

        // Update UI
        this.renderPendingRequests();
        this.updateCounters();
    },

    /**
     * Request completed
     */
    async onRequestCompleted(data) {
        console.log('✅ Request Completed:', data);

        // Remove from pending
        this.removeRequestFromPending(data.request_id);

        // If it's current request, clear it
        if (this.state.currentRequest && this.state.currentRequest.id === data.request_id) {
            this.state.currentRequest = null;
            this.renderCurrentRequest();
        }

        // Reload data
        await this.loadPendingRequests();
        await this.loadCompletedToday();

        // Update UI
        this.updateCounters();
    },

    /**
     * Guest connected notification
     */
    onGuestConnected(data) {
        console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
        console.log('🚨 [GUEST_CONNECTED] Event received!');
        console.log('   Data:', data);
        console.log('   Location:', data.location_name || 'Bilinmeyen Lokasyon');
        console.log('   Hotel ID:', data.hotel_id);
        console.log('   Guest Count:', data.guest_count);
        console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');

        try {
            // ✅ Show animated toast alert (not simple toast)
            console.log('📢 [GUEST_CONNECTED] Calling showGuestConnectedAlert...');
            this.showGuestConnectedAlert(data);
            console.log('✅ [GUEST_CONNECTED] Alert shown successfully');
        } catch (error) {
            console.error('❌ [GUEST_CONNECTED] Error showing alert:', error);
        }

        try {
            // Play notification sound
            console.log('🔊 [GUEST_CONNECTED] Playing notification sound...');
            this.playNotificationSound();
        } catch (error) {
            console.error('❌ [GUEST_CONNECTED] Error playing sound:', error);
        }

        try {
            // Optionally refresh pending requests
            console.log('🔄 [GUEST_CONNECTED] Refreshing pending requests...');
            this.loadPendingRequests();
        } catch (error) {
            console.error('❌ [GUEST_CONNECTED] Error refreshing requests:', error);
        }
    },

    /**
     * Show guest connected alert with animation
     */
    showGuestConnectedAlert(data) {
        console.log('🎨 [ALERT] Creating guest connected alert...');
        console.log('🎨 [ALERT] Data:', data);
        
        try {
            // Create alert element
            const alertId = 'guest-alert-' + Date.now();
            console.log('🎨 [ALERT] Alert ID:', alertId);
            
            const alert = document.createElement('div');
            alert.id = alertId;
            alert.className = 'guest-alert';
            console.log('🎨 [ALERT] Alert element created');
            
            alert.innerHTML = `
                <div class="guest-alert-icon">
                    🚨
                </div>
                <div class="guest-alert-content">
                    <div class="guest-alert-title">Yeni Misafir Bağlandı!</div>
                    <div class="guest-alert-location">${data.location_name || 'Bilinmeyen Lokasyon'}</div>
                </div>
            `;
        
            console.log('🎨 [ALERT] Alert HTML set');
            
            // Add to page - prepend to body to ensure it's on top
            document.body.insertBefore(alert, document.body.firstChild);
            console.log('🎨 [ALERT] Alert added to DOM');
            console.log('🎨 [ALERT] Alert position:', alert.getBoundingClientRect());
            
            // Remove after 5 seconds
            setTimeout(() => {
                console.log('🎨 [ALERT] Starting fadeout animation');
                alert.style.animation = 'slideOutRight 0.3s ease';
                setTimeout(() => {
                    if (document.getElementById(alertId)) {
                        document.body.removeChild(alert);
                        console.log('🎨 [ALERT] Alert removed from DOM');
                    }
                }, 300);
            }, 5000);
            
            console.log('✅ [ALERT] Guest connected alert created successfully');
        } catch (error) {
            console.error('❌ [ALERT] Error creating alert:', error);
            console.error('❌ [ALERT] Stack:', error.stack);
        }
    },

    /**
     * ========================================
     * DATA LOADING
     * ========================================
     */

    /**
     * Load all initial data
     */
    async loadInitialData() {
        console.log('📥 Loading initial data...');

        try {
            await Promise.all([
                this.loadPendingRequests(),
                this.loadCurrentRequest(),
                this.loadCompletedToday()
            ]);

            this.state.lastSync = new Date();
            console.log('✅ Initial data loaded');
        } catch (error) {
            console.error('❌ Failed to load initial data:', error);
            throw error;
        }
    },

    /**
     * Load pending requests
     */
    async loadPendingRequests() {
        try {
            const response = await BuggyCall.API.get('/requests?status=PENDING');
            this.state.pendingRequests = response.requests || [];
            this.renderPendingRequests();
            this.updateCounters();
        } catch (error) {
            console.error('❌ Failed to load pending requests:', error);
        }
    },

    /**
     * Load current request
     */
    async loadCurrentRequest() {
        try {
            const response = await BuggyCall.API.get(`/requests?status=ACCEPTED&buggy_id=${this.state.buggyId}`);
            const requests = response.requests || [];

            if (requests.length > 0) {
                this.state.currentRequest = requests[0];
            } else {
                this.state.currentRequest = null;
            }

            this.renderCurrentRequest();
        } catch (error) {
            console.error('❌ Failed to load current request:', error);
        }
    },

    /**
     * Load completed today count
     */
    async loadCompletedToday() {
        try {
            const response = await BuggyCall.API.get(`/requests?status=COMPLETED&buggy_id=${this.state.buggyId}`);
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

            this.state.completedToday = todayRequests.length;
            this.updateCounters();
        } catch (error) {
            console.error('❌ Failed to load completed count:', error);
        }
    },

    /**
     * ========================================
     * REQUEST ACTIONS
     * ========================================
     */

    /**
     * Accept a request
     */
    async acceptRequest(requestId) {
        console.log('✅ Accepting request:', requestId);

        try {
            BuggyCall.Utils.showLoading();

            const response = await BuggyCall.API.put(`/requests/${requestId}/accept`, {});

            if (response.success) {
                // Update state
                this.state.currentRequest = response.request;

                // Remove from pending
                this.removeRequestFromPending(requestId);

                // Update UI
                this.renderCurrentRequest();
                this.renderPendingRequests();
                this.updateCounters();

                await BuggyCall.Utils.showSuccess('✅ Talep başarıyla kabul edildi!');
            }

            BuggyCall.Utils.hideLoading();
        } catch (error) {
            BuggyCall.Utils.hideLoading();
            await BuggyCall.Utils.showError('Talep kabul edilemedi: ' + error.message);
        }
    },

    /**
     * Complete current request
     */
    async completeRequest() {
        if (!this.state.currentRequest) {
            await BuggyCall.Utils.showWarning('Aktif talep yok!');
            return;
        }

        const confirmed = await BuggyCall.Utils.confirm(
            'Bu talebi tamamlamak istediğinizden emin misiniz?',
            'Talebi Tamamla'
        );

        if (!confirmed) return;

        try {
            // Show location selection modal
            const locationId = await this.showLocationSelectionModal();

            if (!locationId) return; // User cancelled

            BuggyCall.Utils.showLoading();

            await BuggyCall.API.put(`/requests/${this.state.currentRequest.id}/complete`, {
                current_location_id: locationId
            });

            // Clear current request
            this.state.currentRequest = null;

            // ✅ CRITICAL: Refresh FCM token after completing request
            console.log('🔄 [DRIVER] Task completed, refreshing FCM token...');
            if (window.driverFCM) {
                try {
                    const savedToken = localStorage.getItem('fcm_token');
                    if (savedToken) {
                        await window.driverFCM.registerTokenWithBackend(savedToken);
                        console.log('✅ [DRIVER] FCM token refreshed after task completion');
                    } else {
                        console.warn('⚠️ [DRIVER] No token found, triggering full setup...');
                        await window.driverFCM.setupComplete();
                    }
                } catch (error) {
                    console.error('❌ [DRIVER] FCM token refresh failed:', error);
                }
            }

            // Reload data
            await this.loadPendingRequests();
            await this.loadCompletedToday();

            // Update UI
            this.renderCurrentRequest();
            this.updateCounters();

            await BuggyCall.Utils.showSuccess('✅ Talep başarıyla tamamlandı!');

            BuggyCall.Utils.hideLoading();
        } catch (error) {
            BuggyCall.Utils.hideLoading();
            await BuggyCall.Utils.showError('Talep tamamlanamadı: ' + error.message);
        }
    },

    /**
     * ========================================
     * UI RENDERING
     * ========================================
     */

    /**
     * Render pending requests
     */
    renderPendingRequests() {
        const container = document.getElementById('pending-requests');
        if (!container) return;

        if (this.state.pendingRequests.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-check-circle"></i>
                    <p>Bekleyen talep yok</p>
                </div>
            `;
            return;
        }

        container.innerHTML = this.state.pendingRequests.map(req => this.createRequestCard(req)).join('');
    },

    /**
     * Create request card HTML
     */
    createRequestCard(req) {
        const requestId = req.request_id || req.id;
        const locationName = req.location?.name || 'Bilinmeyen Lokasyon';
        const roomNumber = req.room_number || '';
        const requestedAt = this.formatDateTime(req.requested_at);

        return `
            <div class="request-card" data-request-id="${requestId}">
                <div class="request-card-header">
                    <div class="request-location">
                        <i class="fas fa-map-marker-alt"></i>
                        <span>${this.escapeHtml(locationName)}</span>
                    </div>
                    <div class="request-time">
                        <i class="fas fa-clock"></i>
                        <span>${requestedAt}</span>
                    </div>
                </div>
                ${roomNumber ? `
                <div class="request-room">
                    <i class="fas fa-door-open"></i>
                    <span>Oda: ${this.escapeHtml(roomNumber)}</span>
                </div>
                ` : ''}
                <div class="request-actions">
                    <button class="btn btn-accept" onclick="DriverDashboard.acceptRequest(${requestId})">
                        <i class="fas fa-check"></i>
                        Kabul Et
                    </button>
                </div>
            </div>
        `;
    },

    /**
     * Render current request
     */
    renderCurrentRequest() {
        const container = document.getElementById('current-request');
        const section = document.getElementById('current-request-section');

        if (!container || !section) return;

        if (!this.state.currentRequest) {
            section.style.display = 'none';
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-inbox"></i>
                    <p>Aktif görev yok</p>
                </div>
            `;
            this.stopElapsedTimer();
            return;
        }

        section.style.display = 'block';

        const req = this.state.currentRequest;
        const locationName = req.location?.name || 'Bilinmeyen Lokasyon';
        const roomNumber = req.room_number || '';
        const requestedAt = this.formatDateTime(req.requested_at);
        const acceptedAt = this.formatDateTime(req.accepted_at);

        container.innerHTML = `
            <div class="active-request-card">
                <div class="active-request-header">
                    <i class="fas fa-route"></i>
                    <h3>Aktif Görev</h3>
                </div>
                <div class="active-request-body">
                    <div class="active-request-location">
                        <i class="fas fa-map-marker-alt"></i>
                        <span>${this.escapeHtml(locationName)}</span>
                    </div>
                    ${roomNumber ? `
                    <div class="active-request-room">
                        <i class="fas fa-door-open"></i>
                        <span>Oda: ${this.escapeHtml(roomNumber)}</span>
                    </div>
                    ` : ''}
                    <div class="active-request-info">
                        <div class="info-row">
                            <span class="info-label">Talep Zamanı:</span>
                            <span class="info-value">${requestedAt}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">Kabul Zamanı:</span>
                            <span class="info-value">${acceptedAt}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">Geçen Süre:</span>
                            <span class="info-value" id="elapsed-time">-</span>
                        </div>
                    </div>
                </div>
                <div class="active-request-actions">
                    <button class="btn btn-complete" onclick="DriverDashboard.completeRequest()">
                        <i class="fas fa-check-circle"></i>
                        Tamamla
                    </button>
                </div>
            </div>
        `;

        this.startElapsedTimer();
    },

    /**
     * ========================================
     * LOCATION SELECTION MODAL
     * ========================================
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

                // Create modal HTML
                const modalHTML = `
                    <div class="location-modal-overlay" id="location-modal">
                        <div class="location-modal">
                            <div class="location-modal-header">
                                <h3>Mevcut Lokasyonunuzu Seçin</h3>
                                <button class="location-modal-close" onclick="DriverDashboard.closeLocationModal()">
                                    <i class="fas fa-times"></i>
                                </button>
                            </div>
                            <div class="location-modal-body">
                                ${locations.map(loc => `
                                    <div class="location-card" data-location-id="${loc.id}" onclick="DriverDashboard.selectLocation(${loc.id})">
                                        <div class="location-image">
                                            ${loc.location_image 
                                                ? `<img src="${loc.location_image}" alt="${this.escapeHtml(loc.name)}">`
                                                : `<i class="fas fa-map-marker-alt"></i>`
                                            }
                                        </div>
                                        <div class="location-name">${this.escapeHtml(loc.name)}</div>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    </div>
                `;

                // Add to body
                document.body.insertAdjacentHTML('beforeend', modalHTML);

                // Store resolve function
                this._locationModalResolve = resolve;

            } catch (error) {
                console.error('❌ Failed to show location modal:', error);
                resolve(null);
            }
        });
    },

    /**
     * Select location from modal
     */
    selectLocation(locationId) {
        if (this._locationModalResolve) {
            this._locationModalResolve(locationId);
            this._locationModalResolve = null;
        }
        this.closeLocationModal();
    },

    /**
     * Close location modal
     */
    closeLocationModal() {
        const modal = document.getElementById('location-modal');
        if (modal) {
            modal.remove();
        }
        if (this._locationModalResolve) {
            this._locationModalResolve(null);
            this._locationModalResolve = null;
        }
    },

    /**
     * ========================================
     * NEW REQUEST DIALOG
     * ========================================
     */

    /**
     * Show new request dialog with accept/reject options
     */
    showNewRequestDialog(requestData) {
        console.log('🔔 [DIALOG] Showing new request dialog:', requestData);

        // Remove existing dialog if any
        const existingDialog = document.getElementById('new-request-dialog');
        if (existingDialog) {
            console.log('⚠️ [DIALOG] Removing existing dialog');
            existingDialog.remove();
        }

        const locationName = requestData.location?.name || 'Bilinmeyen lokasyon';
        const roomNumber = requestData.room_number || 'Belirtilmemiş';
        const guestName = requestData.guest_name || '';
        const phone = requestData.phone || '';
        const notes = requestData.notes || '';

        console.log('📋 [DIALOG] Dialog data:', {locationName, roomNumber, guestName, phone, notes});

        const dialogHTML = `
            <div class="request-dialog-overlay" id="new-request-dialog">
                <div class="request-dialog">
                    <div class="request-dialog-header">
                        <div class="request-dialog-icon">
                            <i class="fas fa-bell"></i>
                        </div>
                        <h3>🚗 YENİ SHUTTLE TALEBİ!</h3>
                        <button class="request-dialog-close" onclick="DriverDashboard.closeNewRequestDialog()">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                    <div class="request-dialog-body">
                        <div class="request-detail">
                            <i class="fas fa-map-marker-alt"></i>
                            <div>
                                <strong>Lokasyon:</strong>
                                <span>${this.escapeHtml(locationName)}</span>
                            </div>
                        </div>
                        <div class="request-detail">
                            <i class="fas fa-door-open"></i>
                            <div>
                                <strong>Oda:</strong>
                                <span>${this.escapeHtml(roomNumber)}</span>
                            </div>
                        </div>
                        ${guestName ? `
                        <div class="request-detail">
                            <i class="fas fa-user"></i>
                            <div>
                                <strong>Misafir:</strong>
                                <span>${this.escapeHtml(guestName)}</span>
                            </div>
                        </div>
                        ` : ''}
                        ${phone ? `
                        <div class="request-detail">
                            <i class="fas fa-phone"></i>
                            <div>
                                <strong>Telefon:</strong>
                                <span>${this.escapeHtml(phone)}</span>
                            </div>
                        </div>
                        ` : ''}
                        ${notes ? `
                        <div class="request-detail">
                            <i class="fas fa-sticky-note"></i>
                            <div>
                                <strong>Not:</strong>
                                <span>${this.escapeHtml(notes)}</span>
                            </div>
                        </div>
                        ` : ''}
                    </div>
                    <div class="request-dialog-footer">
                        <button class="btn btn-secondary" onclick="DriverDashboard.closeNewRequestDialog()">
                            <i class="fas fa-times"></i>
                            Kapat
                        </button>
                        <button class="btn btn-primary" onclick="DriverDashboard.acceptRequestFromDialog(${requestData.id})">
                            <i class="fas fa-check"></i>
                            Kabul Et
                        </button>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', dialogHTML);

        // Auto-close after 30 seconds
        setTimeout(() => {
            this.closeNewRequestDialog();
        }, 30000);
    },

    /**
     * Accept request from dialog
     */
    async acceptRequestFromDialog(requestId) {
        this.closeNewRequestDialog();
        await this.acceptRequest(requestId);
    },

    /**
     * Close new request dialog
     */
    closeNewRequestDialog() {
        const dialog = document.getElementById('new-request-dialog');
        if (dialog) {
            dialog.style.animation = 'fadeOut 0.3s ease';
            setTimeout(() => dialog.remove(), 300);
        }
    },

    /**
     * ========================================
     * TIMERS & COUNTERS
     * ========================================
     */

    /**
     * Start elapsed time timer
     */
    startElapsedTimer() {
        this.stopElapsedTimer();

        if (!this.state.currentRequest || !this.state.currentRequest.accepted_at) return;

        this.timers.elapsed = setInterval(() => {
            const element = document.getElementById('elapsed-time');
            if (!element || !this.state.currentRequest) {
                this.stopElapsedTimer();
                return;
            }

            const start = new Date(this.state.currentRequest.accepted_at);
            const now = new Date();
            const diffSeconds = Math.floor((now - start) / 1000);
            element.textContent = this.formatDuration(diffSeconds);
        }, 1000);
    },

    /**
     * Stop elapsed time timer
     */
    stopElapsedTimer() {
        if (this.timers.elapsed) {
            clearInterval(this.timers.elapsed);
            this.timers.elapsed = null;
        }
    },

    /**
     * Update all counters
     */
    updateCounters() {
        // Pending requests counter
        const pendingBadge = document.getElementById('pending-badge');
        if (pendingBadge) {
            pendingBadge.textContent = this.state.pendingRequests.length;
        }

        // Completed today counter
        const completedCounter = document.getElementById('completed-today');
        if (completedCounter) {
            completedCounter.textContent = this.state.completedToday;
        }
    },

    /**
     * ========================================
     * BACKGROUND TASKS
     * ========================================
     */

    /**
     * Start background tasks
     */
    startBackgroundTasks() {
        // Sync data every 30 seconds
        this.timers.sync = setInterval(() => {
            this.syncData();
        }, 30000);

        // Heartbeat every 10 seconds
        this.timers.heartbeat = setInterval(() => {
            this.sendHeartbeat();
        }, 10000);
    },

    /**
     * Sync data with server
     */
    async syncData() {
        if (!this.state.isOnline) return;

        try {
            await this.loadPendingRequests();
            await this.loadCompletedToday();
            this.state.lastSync = new Date();
        } catch (error) {
            console.error('❌ Sync failed:', error);
        }
    },

    /**
     * Send heartbeat to server
     */
    sendHeartbeat() {
        if (this.socket && this.socket.connected) {
            this.socket.emit('driver_heartbeat', {
                driver_id: this.state.userId,
                buggy_id: this.state.buggyId,
                timestamp: new Date().toISOString()
            });
        }
    },

    /**
     * ========================================
     * EVENT LISTENERS
     * ========================================
     */

    /**
     * Setup all event listeners
     */
    setupEventListeners() {
        // Page visibility change
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) {
                this.syncData();
            }
        });

        // Online/offline events
        window.addEventListener('online', () => {
            console.log('🌐 Back online');
            this.updateConnectionStatus('connected');
            this.syncData();
        });

        window.addEventListener('offline', () => {
            console.log('📡 Offline');
            this.updateConnectionStatus('disconnected');
        });

        // Before unload
        window.addEventListener('beforeunload', () => {
            this.cleanup();
        });
    },

    /**
     * ========================================
     * AUDIO
     * ========================================
     */

    /**
     * Initialize audio
     */
    initAudio() {
        try {
            this.audio.notification = new Audio('/static/sounds/notification.mp3');
            this.audio.notification.volume = 0.5;
        } catch (error) {
            console.warn('⚠️ Audio initialization failed:', error);
        }
    },

    /**
     * Play notification sound
     */
    playNotificationSound() {
        if (this.audio.enabled && this.audio.notification) {
            this.audio.notification.play().catch(e => {
                console.warn('⚠️ Audio play failed:', e);
            });
        }
    },

    /**
     * ========================================
     * UI HELPERS
     * ========================================
     */

    /**
     * Initialize UI components
     */
    initUI() {
        // Set initial connection status
        this.updateConnectionStatus('connecting');
    },

    /**
     * Update connection status indicator
     */
    updateConnectionStatus(status) {
        const statusElement = document.getElementById('connection-status');
        const textElement = document.getElementById('connection-text');

        if (!statusElement || !textElement) return;

        statusElement.className = 'connection-status ' + status;

        const statusTexts = {
            connecting: 'Bağlanıyor...',
            connected: 'Bağlı',
            disconnected: 'Bağlantı Kesildi',
            reconnecting: 'Yeniden Bağlanıyor...',
            failed: 'Bağlantı Başarısız'
        };

        textElement.textContent = statusTexts[status] || 'Bilinmiyor';
    },

    /**
     * Show no buggy warning
     */
    async showNoBuggyWarning() {
        await BuggyCall.Utils.showWarning(
            'Size henüz bir shuttle atanmamış. Lütfen yöneticinizle iletişime geçin.'
        );
    },

    /**
     * ========================================
     * UTILITY FUNCTIONS
     * ========================================
     */

    /**
     * Remove request from pending list
     */
    removeRequestFromPending(requestId) {
        this.state.pendingRequests = this.state.pendingRequests.filter(
            r => (r.request_id || r.id) !== requestId
        );
    },

    /**
     * Format date time
     */
    formatDateTime(dateString) {
        if (!dateString) return '-';

        try {
            const date = new Date(dateString);
            return date.toLocaleString('tr-TR', {
                day: '2-digit',
                month: '2-digit',
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
        } catch (error) {
            return dateString;
        }
    },

    /**
     * Format duration in seconds
     */
    formatDuration(seconds) {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = seconds % 60;

        if (hours > 0) {
            return `${hours}sa ${minutes}dk ${secs}sn`;
        } else if (minutes > 0) {
            return `${minutes}dk ${secs}sn`;
        } else {
            return `${secs}sn`;
        }
    },

    /**
     * Escape HTML
     */
    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },

    /**
     * ========================================
     * CLEANUP
     * ========================================
     */

    /**
     * Cleanup resources
     */
    cleanup() {
        console.log('🧹 Cleaning up...');

        // Stop all timers
        Object.values(this.timers).forEach(timer => {
            if (timer) clearInterval(timer);
        });

        // Disconnect socket
        if (this.socket) {
            this.socket.disconnect();
        }
    }
};

/**
 * ========================================
 * AUTO-INITIALIZE ON DOM READY
 * ========================================
 */
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        DriverDashboard.init();
    });
} else {
    DriverDashboard.init();
}

// Export for global access
window.DriverDashboard = DriverDashboard;
