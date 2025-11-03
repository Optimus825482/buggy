/**
 * Buggy Call - Admin Panel JavaScript
 * Powered by Erkan ERDEM
 */

const Admin = {
    hotelId: null,
    socket: null,
    locations: [],
    buggies: [],
    drivers: [],
    requests: [],

    /**
     * Initialize admin panel
     */
    init() {
        console.log('Admin panel initializing...');
        
        // Get hotel ID from session (passed from backend)
        this.hotelId = parseInt(document.body.dataset.hotelId) || 1;
        
        // Initialize Socket.IO
        this.initSocket();
        
        // Load initial data
        this.loadDashboardData();
        
        // Setup event listeners
        this.setupEventListeners();
        
        console.log('Admin panel initialized');
    },

    /**
     * Initialize WebSocket connection
     */
    initSocket() {
        this.socket = BuggyCall.Socket.init();
        this.socket.connect();
        
        // Join hotel room
        this.socket.on('connect', () => {
            this.socket.emit('join_hotel', {
                hotel_id: this.hotelId,
                role: 'admin'
            });
        });
        
        // Listen to real-time events
        this.socket.on('new_request', (data) => {
            console.log('New request:', data);
            BuggyCall.Utils.showToast('Yeni buggy talebi geldi!', 'info');
            this.refreshRequests();
        });
        
        this.socket.on('request_accepted', (data) => {
            console.log('Request accepted:', data);
            this.refreshRequests();
        });
        
        this.socket.on('request_completed', (data) => {
            console.log('Request completed:', data);
            this.refreshRequests();
        });
        
        this.socket.on('buggy_status_changed', (data) => {
            console.log('Buggy status changed:', data);
            this.updateBuggyStatus(data);
        });
        
        this.socket.on('buggy_location_changed', (data) => {
            console.log('Buggy location changed:', data);
            this.updateBuggyStatus(data);
        });
        
        // Listen for driver login/logout events
        this.socket.on('driver_logged_in', (data) => {
            console.log('Driver logged in:', data);
            this.refreshBuggies(); // Refresh buggy list to show active driver
        });
        
        this.socket.on('driver_logged_out', (data) => {
            console.log('Driver logged out:', data);
            this.refreshBuggies(); // Refresh buggy list to hide driver
        });
    },

    /**
     * Load dashboard data
     */
    async loadDashboardData() {
        try {
            BuggyCall.Utils.showLoading();
            
            // Load locations
            await this.loadLocations();
            
            // Load buggies
            await this.loadBuggies();
            
            // Load drivers
            await this.loadDrivers();
            
            // Load requests
            await this.loadRequests();
            
            // Update stats
            this.updateStats();
            
            BuggyCall.Utils.hideLoading();
        } catch (error) {
            console.error('Error loading dashboard data:', error);
            await BuggyCall.Utils.showError('Veri yüklenirken hata oluştu: ' + error.message);
            BuggyCall.Utils.hideLoading();
        }
    },

    /**
     * Update dashboard stats
     */
    updateStats() {
        // Count active buggies (available or busy)
        const activeBuggies = this.buggies.filter(b => 
            b.status === 'available' || b.status === 'busy'
        ).length;
        
        // Count pending requests
        const pendingRequests = this.requests.filter(r => r.status === 'pending').length;
        
        // Count completed today
        const today = new Date().toISOString().split('T')[0];
        const completedToday = this.requests.filter(r => {
            if (r.status === 'completed' && r.completed_at) {
                const completedDate = r.completed_at.split('T')[0];
                return completedDate === today;
            }
            return false;
        }).length;
        
        // Total locations
        const totalLocations = this.locations.length;
        
        // Update DOM
        const activeBuggiesEl = document.getElementById('active-buggies');
        if (activeBuggiesEl) activeBuggiesEl.textContent = activeBuggies;
        
        const pendingRequestsEl = document.getElementById('pending-requests');
        if (pendingRequestsEl) pendingRequestsEl.textContent = pendingRequests;
        
        const completedTodayEl = document.getElementById('completed-today');
        if (completedTodayEl) completedTodayEl.textContent = completedToday;
        
        const totalLocationsEl = document.getElementById('total-locations');
        if (totalLocationsEl) totalLocationsEl.textContent = totalLocations;
        
        // Update lists on dashboard
        this.updateBuggyStatusList();
        this.updateActiveRequestsList();
    },

    /**
     * Update active requests list on dashboard
     */
    updateActiveRequestsList() {
        const container = document.getElementById('active-requests-list');
        if (!container) return;
        
        // Get active requests (pending and accepted)
        const activeRequests = this.requests.filter(r => 
            r.status === 'pending' || r.status === 'accepted'
        ).slice(0, 10); // Show max 10
        
        if (activeRequests.length === 0) {
            container.innerHTML = '<p class="text-center text-muted" style="padding: 2rem;">Henüz talep yok</p>';
            return;
        }
        
        container.innerHTML = activeRequests.map(req => `
            <div class="list-item" data-id="${req.id}" style="
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 1rem 1.5rem;
                border-bottom: 1px solid #f1f5f9;
                transition: background 0.2s ease;
                cursor: pointer;
            " onmouseover="this.style.background='#f8fafc'" onmouseout="this.style.background='white'">
                <div style="display: flex; align-items: center; gap: 1rem; flex: 1;">
                    <div style="
                        width: 40px;
                        height: 40px;
                        border-radius: 50%;
                        background: linear-gradient(135deg, #f59e0b, #d97706);
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        color: white;
                        font-size: 1.25rem;
                    ">
                        <i class="fas fa-map-marker-alt"></i>
                    </div>
                    <div style="flex: 1;">
                        <div style="font-weight: 600; color: #1e293b; margin-bottom: 0.25rem;">
                            ${req.location?.name || 'Bilinmiyor'}
                            ${req.room_number ? `<span style="color: #64748b; font-weight: 400; font-size: 0.875rem;"> • Oda ${req.room_number}</span>` : ''}
                        </div>
                        <div style="font-size: 0.875rem; color: #64748b;">
                            <i class="fas fa-clock" style="margin-right: 0.25rem;"></i>
                            ${BuggyCall.Utils.formatDate(req.requested_at)}
                        </div>
                    </div>
                </div>
                <span class="${BuggyCall.Utils.getBadgeClass(req.status)}" style="font-weight: 600;">
                    ${this.getStatusText(req.status)}
                </span>
            </div>
        `).join('');
    },

    /**
     * Update buggy status list on dashboard
     */
    updateBuggyStatusList() {
        const container = document.getElementById('buggy-status-list');
        if (!container) return;
        
        if (this.buggies.length === 0) {
            container.innerHTML = '<p class="text-center text-muted" style="padding: 2rem;">Henüz buggy eklenmemiş</p>';
            return;
        }
        
        container.innerHTML = this.buggies.map(buggy => {
            // Get location name if available
            const locationName = buggy.current_location?.name || buggy.current_location_name || '-';
            const hasLocation = locationName !== '-';
            
            return `
            <div class="list-item buggy-item" data-buggy-id="${buggy.id}" style="
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 1rem 1.5rem;
                border-bottom: 1px solid #f1f5f9;
                transition: background 0.2s ease;
            " onmouseover="this.style.background='#f8fafc'" onmouseout="this.style.background='white'">
                <div style="display: flex; align-items: center; gap: 1rem; flex: 1;">
                    <div style="
                        width: 40px;
                        height: 40px;
                        border-radius: 50%;
                        background: linear-gradient(135deg, var(--primary-color), var(--accent-color));
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        color: white;
                        font-weight: bold;
                        font-size: 0.875rem;
                    ">${buggy.code}</div>
                    <div style="flex: 1;">
                        <div style="font-weight: 600; color: #1e293b; margin-bottom: 0.25rem;">
                            ${buggy.code}
                            ${buggy.driver_name ? `<span style="color: #64748b; font-weight: 400; font-size: 0.875rem;"> • ${buggy.driver_name}</span>` : ''}
                        </div>
                        <div style="font-size: 0.875rem; color: #64748b;">
                            <i class="fas fa-map-marker-alt" style="margin-right: 0.25rem; color: ${hasLocation ? '#10b981' : '#94a3b8'};"></i>
                            <span class="buggy-location">${locationName}</span>
                        </div>
                    </div>
                </div>
                <span class="badge buggy-status ${BuggyCall.Utils.getBadgeClass(buggy.status)}" style="font-weight: 600;">
                    ${this.getStatusText(buggy.status)}
                </span>
            </div>
        `;
        }).join('');
    },

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Location form
        const locationForm = document.getElementById('location-form');
        if (locationForm) {
            locationForm.addEventListener('submit', (e) => this.handleLocationSubmit(e));
        }
        
        // Buggy form
        const buggyForm = document.getElementById('buggy-form');
        if (buggyForm) {
            buggyForm.addEventListener('submit', (e) => this.handleBuggySubmit(e));
        }
        
        // New location button
        const newLocationBtn = document.getElementById('new-location-btn');
        if (newLocationBtn) {
            newLocationBtn.addEventListener('click', () => this.showLocationModal());
        }
        
        // New buggy button
        const newBuggyBtn = document.getElementById('new-buggy-btn');
        if (newBuggyBtn) {
            newBuggyBtn.addEventListener('click', () => this.showBuggyModal());
        }
        
        // Refresh buttons
        document.querySelectorAll('[data-action="refresh"]').forEach(btn => {
            btn.addEventListener('click', () => {
                const target = btn.dataset.target;
                this.refreshData(target);
            });
        });
    },

    /**
     * Load locations
     */
    async loadLocations() {
        try {
            const response = await BuggyCall.API.get('/locations');
            // Handle both formats: {locations: [...]} or {data: {items: [...]}}
            this.locations = response.locations || response.data?.items || response.items || [];
            
            const container = document.getElementById('locations-list');
            if (!container) return;
            
            const locations = this.locations;
            
            if (locations.length === 0) {
                container.innerHTML = '<div class="empty-state">Henüz lokasyon eklenmemiş</div>';
                return;
            }
            
            container.innerHTML = locations.map(loc => `
                <div class="card location-card" data-id="${loc.id}">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-start">
                            <div>
                                <h5 class="card-title">${loc.name}</h5>
                                <p class="card-text text-muted">${loc.description || ''}</p>
                                <span class="badge ${loc.is_active ? 'badge-success' : 'badge-secondary'}">
                                    ${loc.is_active ? 'Aktif' : 'Pasif'}
                                </span>
                            </div>
                            <div class="btn-group">
                                <button class="btn btn-sm btn-outline-primary" onclick="Admin.showQRCode('${loc.id}', '${loc.qr_code_data}')">
                                    <i class="fas fa-qrcode"></i> QR
                                </button>
                                <button class="btn btn-sm btn-outline-secondary" onclick="Admin.editLocation('${loc.id}')">
                                    <i class="fas fa-edit"></i>
                                </button>
                                <button class="btn btn-sm btn-outline-danger" onclick="Admin.deleteLocation('${loc.id}')">
                                    <i class="fas fa-trash"></i>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            `).join('');
        } catch (error) {
            console.error('Error loading locations:', error);
            throw error;
        }
    },

    /**
     * Load buggies
     */
    async loadBuggies() {
        try {
            const response = await BuggyCall.API.get('/buggies');
            // Handle both formats: {buggies: [...]} or {data: {items: [...]}}
            this.buggies = response.buggies || response.data?.items || response.items || [];
            
            const container = document.getElementById('buggies-list');
            if (!container) return;
            
            const buggies = this.buggies;
            
            if (buggies.length === 0) {
                container.innerHTML = '<div class="empty-state">Henüz buggy eklenmemiş</div>';
                return;
            }
            
            container.innerHTML = buggies.map(buggy => `
                <div class="card buggy-card" data-id="${buggy.id}">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-start">
                            <div>
                                <h5 class="card-title">${buggy.code}</h5>
                                <p class="card-text">
                                    <small class="text-muted">${buggy.license_plate || 'Plaka yok'}</small><br>
                                    <small>Model: ${buggy.model || '-'}</small><br>
                                    <small>Sürücü: ${buggy.driver_name || 'Atanmamış'}</small>
                                </p>
                                <span class="badge ${BuggyCall.Utils.getBadgeClass(buggy.status)}">
                                    ${this.getStatusText(buggy.status)}
                                </span>
                            </div>
                            <div class="btn-group">
                                <button class="btn btn-sm btn-outline-secondary" onclick="Admin.editBuggy('${buggy.id}')">
                                    <i class="fas fa-edit"></i>
                                </button>
                                <button class="btn btn-sm btn-outline-danger" onclick="Admin.deleteBuggy('${buggy.id}')">
                                    <i class="fas fa-trash"></i>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            `).join('');
        } catch (error) {
            console.error('Error loading buggies:', error);
            throw error;
        }
    },

    /**
     * Load drivers
     */
    async loadDrivers() {
        try {
            const response = await BuggyCall.API.get('/drivers');
            // Handle both formats: {drivers: [...]} or {data: {items: [...]}}
            this.drivers = response.drivers || response.data?.items || response.items || [];
            
            // Populate driver select in buggy form
            const driverSelect = document.getElementById('buggy-driver');
            if (driverSelect) {
                driverSelect.innerHTML = '<option value="">Sürücü Seç</option>' +
                    this.drivers.map(d => `<option value="${d.id}">${d.full_name || d.username}</option>`).join('');
            }
        } catch (error) {
            console.error('Error loading drivers:', error);
        }
    },

    /**
     * Load requests
     */
    async loadRequests() {
        try {
            const response = await BuggyCall.API.get('/requests');
            // Handle both formats: {requests: [...]} or {data: {items: [...]}}
            this.requests = response.requests || response.data?.items || response.items || [];
            
            // Try dashboard container first, fallback to requests page
            const container = document.getElementById('active-requests-list') || document.getElementById('requests-list');
            if (!container) return;
            
            const requests = this.requests;
            
            if (requests.length === 0) {
                container.innerHTML = '<div class="empty-state">Henüz talep yok</div>';
                return;
            }
            
            // Group by status
            const pending = requests.filter(r => r.status === 'pending');
            const accepted = requests.filter(r => r.status === 'accepted');
            const completed = requests.filter(r => r.status === 'completed');
            
            container.innerHTML = `
                <div class="requests-section">
                    <h6 class="text-warning"><i class="fas fa-clock"></i> Bekleyen (${pending.length})</h6>
                    ${this.renderRequests(pending)}
                </div>
                <div class="requests-section mt-3">
                    <h6 class="text-info"><i class="fas fa-check-circle"></i> Kabul Edildi (${accepted.length})</h6>
                    ${this.renderRequests(accepted)}
                </div>
                <div class="requests-section mt-3">
                    <h6 class="text-success"><i class="fas fa-check-double"></i> Tamamlandı (${completed.length})</h6>
                    ${this.renderRequests(completed.slice(0, 5))}
                </div>
            `;
        } catch (error) {
            console.error('Error loading requests:', error);
        }
    },

    /**
     * Render requests list
     */
    renderRequests(requests) {
        if (requests.length === 0) {
            return '<p class="text-muted" style="padding: 1rem; text-align: center;">Talep yok</p>';
        }
        
        return requests.map(req => `
            <div class="list-item" data-id="${req.id}" style="
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 1rem 1.5rem;
                border-bottom: 1px solid #f1f5f9;
                transition: background 0.2s ease;
                cursor: pointer;
            " onmouseover="this.style.background='#f8fafc'" onmouseout="this.style.background='white'">
                <div style="display: flex; align-items: center; gap: 1rem; flex: 1;">
                    <div style="
                        width: 40px;
                        height: 40px;
                        border-radius: 50%;
                        background: linear-gradient(135deg, #f59e0b, #d97706);
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        color: white;
                        font-size: 1.25rem;
                    ">
                        <i class="fas fa-map-marker-alt"></i>
                    </div>
                    <div style="flex: 1;">
                        <div style="font-weight: 600; color: #1e293b; margin-bottom: 0.25rem;">
                            ${req.location?.name || 'Bilinmiyor'}
                            ${req.room_number ? `<span style="color: #64748b; font-weight: 400; font-size: 0.875rem;"> • Oda ${req.room_number}</span>` : ''}
                        </div>
                        <div style="font-size: 0.875rem; color: #64748b;">
                            <i class="fas fa-clock" style="margin-right: 0.25rem;"></i>
                            ${BuggyCall.Utils.formatDate(req.requested_at)}
                            ${req.buggy ? `<span style="margin-left: 0.5rem;"><i class="fas fa-car-side"></i> ${req.buggy.code}</span>` : ''}
                        </div>
                    </div>
                </div>
                <span class="${BuggyCall.Utils.getBadgeClass(req.status)}" style="font-weight: 600;">
                    ${this.getStatusText(req.status)}
                </span>
            </div>
        `).join('');
    },

    /**
     * Handle location form submit
     */
    async handleLocationSubmit(e) {
        e.preventDefault();
        
        const form = e.target;
        const data = BuggyCall.Form.getData(form);
        
        try {
            BuggyCall.Utils.showLoading();
            
            const locationId = form.dataset.locationId;
            if (locationId) {
                // Update
                await BuggyCall.API.put(`/locations/${locationId}`, data);
                await BuggyCall.Utils.showSuccess('Lokasyon başarıyla güncellendi!');
            } else {
                // Create
                await BuggyCall.API.post('/locations', data);
                await BuggyCall.Utils.showSuccess('Yeni lokasyon başarıyla oluşturuldu!');
            }
            
            // Reload locations
            await this.loadLocations();
            
            // Close modal
            this.closeModal('locationModal');
            form.reset();
            
            BuggyCall.Utils.hideLoading();
        } catch (error) {
            await BuggyCall.Utils.showError('İşlem sırasında hata oluştu: ' + error.message);
            BuggyCall.Utils.hideLoading();
        }
    },

    /**
     * Handle buggy form submit
     */
    async handleBuggySubmit(e) {
        e.preventDefault();
        
        const form = e.target;
        const data = BuggyCall.Form.getData(form);
        
        try {
            BuggyCall.Utils.showLoading();
            
            const buggyId = form.dataset.buggyId;
            if (buggyId) {
                // Update
                await BuggyCall.API.put(`/buggies/${buggyId}`, data);
                await BuggyCall.Utils.showSuccess('Buggy başarıyla güncellendi!');
            } else {
                // Create
                await BuggyCall.API.post('/buggies', data);
                await BuggyCall.Utils.showSuccess('Yeni buggy başarıyla oluşturuldu!');
            }
            
            // Reload buggies
            await this.loadBuggies();
            
            // Close modal
            this.closeModal('buggyModal');
            form.reset();
            
            BuggyCall.Utils.hideLoading();
        } catch (error) {
            await BuggyCall.Utils.showError('İşlem sırasında hata oluştu: ' + error.message);
            BuggyCall.Utils.hideLoading();
        }
    },

    /**
     * Show location modal
     */
    showLocationModal(locationId = null) {
        const modal = document.getElementById('locationModal');
        const form = document.getElementById('location-form');
        
        if (locationId) {
            // Load location data
            // TODO: Fetch and populate form
            form.dataset.locationId = locationId;
        } else {
            form.reset();
            delete form.dataset.locationId;
        }
        
        if (modal) {
            modal.style.display = 'block';
        }
    },

    /**
     * Show buggy modal
     */
    showBuggyModal(buggyId = null) {
        const modal = document.getElementById('buggyModal');
        const form = document.getElementById('buggy-form');
        
        if (buggyId) {
            form.dataset.buggyId = buggyId;
        } else {
            form.reset();
            delete form.dataset.buggyId;
        }
        
        if (modal) {
            modal.style.display = 'block';
        }
    },

    /**
     * Close modal
     */
    closeModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.style.display = 'none';
        }
    },

    /**
     * Show QR code
     */
    showQRCode(locationId, qrData) {
        // Generate QR code using external library or show data
        BuggyCall.Utils.showToast(`QR Kod: ${qrData}`, 'info');
        // TODO: Show QR code in modal
    },

    /**
     * Edit location
     */
    editLocation(locationId) {
        this.showLocationModal(locationId);
    },

    /**
     * Delete location
     */
    async deleteLocation(locationId) {
        const confirmed = await BuggyCall.Utils.confirm(
            'Bu lokasyonu silmek istediğinizden emin misiniz? Bu işlem geri alınamaz.',
            'Lokasyon Sil'
        );
        
        if (!confirmed) {
            return;
        }
        
        try {
            BuggyCall.Utils.showLoading();
            await BuggyCall.API.delete(`/locations/${locationId}`);
            await BuggyCall.Utils.showSuccess('Lokasyon başarıyla silindi!');
            await this.loadLocations();
            BuggyCall.Utils.hideLoading();
        } catch (error) {
            await BuggyCall.Utils.showError('Silme işlemi sırasında hata oluştu: ' + error.message);
            BuggyCall.Utils.hideLoading();
        }
    },

    /**
     * Edit buggy
     */
    editBuggy(buggyId) {
        this.showBuggyModal(buggyId);
    },

    /**
     * Delete buggy
     */
    async deleteBuggy(buggyId) {
        const confirmed = await BuggyCall.Utils.confirm(
            'Bu buggy\'yi silmek istediğinizden emin misiniz? Bu işlem geri alınamaz.',
            'Buggy Sil'
        );
        
        if (!confirmed) {
            return;
        }
        
        try {
            BuggyCall.Utils.showLoading();
            await BuggyCall.API.delete(`/buggies/${buggyId}`);
            await BuggyCall.Utils.showSuccess('Buggy başarıyla silindi!');
            await this.loadBuggies();
            BuggyCall.Utils.hideLoading();
        } catch (error) {
            await BuggyCall.Utils.showError('Silme işlemi sırasında hata oluştu: ' + error.message);
            BuggyCall.Utils.hideLoading();
        }
    },

    /**
     * Refresh data
     */
    async refreshData(target) {
        switch (target) {
            case 'locations':
                await this.loadLocations();
                break;
            case 'buggies':
                await this.loadBuggies();
                break;
            case 'requests':
                await this.loadRequests();
                break;
            default:
                await this.loadDashboardData();
        }
    },

    /**
     * Refresh requests
     */
    async refreshRequests() {
        await this.loadRequests();
    },
    
    /**
     * Refresh buggies
     */
    async refreshBuggies() {
        await this.loadBuggies();
    },

    /**
     * Update buggy status
     */
    updateBuggyStatus(data) {
        // Update in buggies array
        const buggyIndex = this.buggies.findIndex(b => b.id === data.buggy_id);
        if (buggyIndex !== -1) {
            this.buggies[buggyIndex].status = data.status;
            if (data.location_name) {
                this.buggies[buggyIndex].current_location_name = data.location_name;
            }
        }
        
        // Update buggy card on buggies page
        const buggyCard = document.querySelector(`.buggy-card[data-id="${data.buggy_id}"]`);
        if (buggyCard) {
            const badge = buggyCard.querySelector('.badge');
            if (badge) {
                badge.className = `badge ${BuggyCall.Utils.getBadgeClass(data.status)}`;
                badge.textContent = this.getStatusText(data.status);
            }
        }
        
        // Update buggy item on dashboard
        const buggyItem = document.querySelector(`.buggy-item[data-buggy-id="${data.buggy_id}"]`);
        if (buggyItem) {
            const statusBadge = buggyItem.querySelector('.buggy-status');
            if (statusBadge) {
                statusBadge.className = `badge buggy-status ${BuggyCall.Utils.getBadgeClass(data.status)}`;
                statusBadge.textContent = this.getStatusText(data.status);
            }
            
            // Update location if provided
            if (data.location_name) {
                const locationSpan = buggyItem.querySelector('.buggy-location');
                if (locationSpan) {
                    locationSpan.textContent = data.location_name;
                    // Update icon color
                    const locationIcon = buggyItem.querySelector('.fa-map-marker-alt');
                    if (locationIcon) {
                        locationIcon.style.color = '#10b981';
                    }
                }
            }
        }
        
        // Update stats
        this.updateStats();
    },

    /**
     * Get status text in Turkish
     */
    getStatusText(status) {
        const statusMap = {
            'pending': 'Bekliyor',
            'accepted': 'Kabul Edildi',
            'completed': 'Tamamlandı',
            'cancelled': 'İptal Edildi',
            'available': 'Müsait',
            'busy': 'Meşgul',
            'offline': 'Çevrimdışı'
        };
        return statusMap[status] || status;
    }
};

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => Admin.init());
} else {
    Admin.init();
}

// Export to global scope
window.Admin = Admin;
