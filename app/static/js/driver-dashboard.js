/**
 * Shuttle Call - Driver Dashboard JavaScript
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
        
        // Location setup is now handled by separate page (select_location.html)
        // No need for modal anymore
        
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
            
            // Create location cards (mobile-friendly, better UX)
            // Click on card directly saves location
            const locationCards = locations.map(loc => `
                <button 
                    type="button"
                    class="location-card" 
                    data-location-id="${loc.id}"
                    style="
                        width: 100%;
                        padding: 1rem;
                        margin-bottom: 0.75rem;
                        background: white;
                        border: 2px solid #e2e8f0;
                        border-radius: 12px;
                        cursor: pointer;
                        transition: all 0.2s ease;
                        text-align: left;
                        display: flex;
                        align-items: center;
                        gap: 1rem;
                    "
                    onmouseover="this.style.borderColor='#0ea5e9'; this.style.backgroundColor='#f0f9ff'; this.style.transform='translateY(-2px)'; this.style.boxShadow='0 4px 12px rgba(14, 165, 233, 0.15)';"
                    onmouseout="this.style.borderColor='#e2e8f0'; this.style.backgroundColor='white'; this.style.transform='translateY(0)'; this.style.boxShadow='none';"
                    onclick="DriverDashboard.selectAndSaveLocation(${loc.id});"
                >
                    <div style="
                        width: 48px;
                        height: 48px;
                        background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%);
                        border-radius: 12px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        flex-shrink: 0;
                    ">
                        <i class="fas fa-map-marker-alt" style="color: white; font-size: 1.25rem;"></i>
                    </div>
                    <div style="flex: 1;">
                        <div style="font-weight: 600; color: #1e293b; font-size: 1rem; margin-bottom: 0.25rem;">
                            ${loc.name}
                        </div>
                        <div style="font-size: 0.875rem; color: #64748b;">
                            Konumu seç
                        </div>
                    </div>
                    <div style="flex-shrink: 0;">
                        <i class="fas fa-chevron-right" style="color: #cbd5e1; font-size: 1.25rem;"></i>
                    </div>
                </button>
            `).join('');
            
            const modalContent = `
                <div style="padding: 0;">
                    <p style="text-align: center; color: #64748b; margin-bottom: 1rem; font-size: 0.9rem;">
                        Lütfen başlangıç konumunuzu seçin
                    </p>
                    <div style="max-height: 400px; overflow-y: auto; padding: 0 0.25rem;">
                        ${locationCards}
                    </div>
                </div>
            `;
            
            // Show modal without buttons (click on location to select)
            BuggyModal.custom(modalContent, {
                title: '📍 Konum Seçin',
                confirmText: '',  // Empty string to hide
                cancelText: '',   // Empty string to hide
                size: 'medium'
            });
            
            // Customize modal after it's shown
            setTimeout(() => {
                // Remove ALL button containers
                document.querySelectorAll('.buggy-modal-actions, .buggy-modal-footer').forEach(el => {
                    el.remove();  // Remove actions and footer
                });
                
                // Remove ALL buttons
                document.querySelectorAll('.buggy-modal button').forEach(btn => {
                    if (!btn.classList.contains('location-card')) {
                        btn.remove();  // Remove all buttons except location cards
                    }
                });
                
                // Remove close button (X)
                const closeButton = document.querySelector('.buggy-modal-close');
                if (closeButton) {
                    closeButton.remove();
                }
                
                // Make header much more compact
                const modalHeader = document.querySelector('.buggy-modal-header');
                if (modalHeader) {
                    modalHeader.style.padding = '0.75rem 1.5rem';  // Even smaller padding
                    modalHeader.style.minHeight = 'auto';
                    modalHeader.style.background = 'transparent';  // Remove background
                    modalHeader.style.borderBottom = 'none';  // Remove border
                }
                
                // Remove icon from header
                const modalIcon = document.querySelector('.buggy-modal-icon');
                if (modalIcon) {
                    modalIcon.remove();  // Remove icon completely
                }
                
                // Make title smaller and centered
                const modalTitle = document.querySelector('.buggy-modal-title');
                if (modalTitle) {
                    modalTitle.style.fontSize = '1.1rem';  // Even smaller font
                    modalTitle.style.margin = '0';
                    modalTitle.style.fontWeight = '600';
                    modalTitle.style.textAlign = 'center';
                    modalTitle.style.width = '100%';
                }
                
                // Prevent modal from closing - MUST select location
                const backdrop = document.querySelector('.buggy-modal-backdrop');
                const modal = document.querySelector('.buggy-modal');
                
                if (backdrop) {
                    // Remove all click handlers
                    const newBackdrop = backdrop.cloneNode(true);
                    backdrop.parentNode.replaceChild(newBackdrop, backdrop);
                    
                    // Prevent any clicks
                    newBackdrop.addEventListener('click', (e) => {
                        e.stopPropagation();
                        e.stopImmediatePropagation();
                        e.preventDefault();
                        return false;
                    }, true);
                    
                    // Make backdrop unclickable
                    newBackdrop.style.pointerEvents = 'none';
                }
                
                if (modal) {
                    // Make modal clickable but prevent closing
                    modal.style.pointerEvents = 'auto';
                    
                    // Remove all click handlers from modal
                    const newModal = modal.cloneNode(true);
                    modal.parentNode.replaceChild(newModal, modal);
                    
                    // Prevent clicks from bubbling
                    newModal.addEventListener('click', (e) => {
                        e.stopPropagation();
                        e.stopImmediatePropagation();
                    }, true);
                }
                
                // Prevent ESC key globally
                const preventEscape = (e) => {
                    if (e.key === 'Escape') {
                        e.stopPropagation();
                        e.preventDefault();
                        return false;
                    }
                };
                document.addEventListener('keydown', preventEscape, true);
                
                // Remove bottom padding
                const modalContent = document.querySelector('.buggy-modal-content');
                if (modalContent) {
                    modalContent.style.paddingBottom = '1rem';
                }
            }, 150);
        } catch (error) {
            console.error('Error showing location setup modal:', error);
            await BuggyModal.alert('Lokasyonlar yüklenirken hata oluştu: ' + error.message);
        }
    },

    /**
     * Select and save location (called when clicking a location card)
     */
    async selectAndSaveLocation(locationId) {
        try {
            // Close the modal first
            const modalBackdrop = document.querySelector('.buggy-modal-backdrop');
            if (modalBackdrop) {
                modalBackdrop.remove();
            }
            
            // Set initial location
            await this.setInitialLocation(locationId);
        } catch (error) {
            console.error('Error selecting location:', error);
            await BuggyModal.alert('Lokasyon seçilirken hata oluştu: ' + error.message);
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
        
        // Join hotel drivers room and user-specific room
        this.socket.on('connect', () => {
            console.log('Socket connected');
            this.socket.emit('join_hotel', {
                hotel_id: this.hotelId,
                role: 'driver'
            });
            // Join user-specific room for session management
            this.socket.emit('join_user', {
                user_id: this.userId
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
        
        // Listen to force logout
        this.socket.on('force_logout', async (data) => {
            console.log('Force logout received:', data);
            
            // Create custom modal content with theme styling
            const modalContent = `
                <div style="text-align: center; padding: 1.5rem 0;">
                    <div style="
                        width: 80px;
                        height: 80px;
                        margin: 0 auto 1.5rem;
                        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
                        border-radius: 50%;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        box-shadow: 0 8px 16px rgba(239, 68, 68, 0.3);
                    ">
                        <i class="fas fa-sign-out-alt" style="font-size: 2.5rem; color: white;"></i>
                    </div>
                    
                    <h3 style="
                        font-size: 1.5rem;
                        font-weight: 700;
                        color: #1e293b;
                        margin-bottom: 1rem;
                    ">
                        Oturum Kapatıldı
                    </h3>
                    
                    <p style="
                        font-size: 1rem;
                        color: #64748b;
                        line-height: 1.6;
                        margin-bottom: 0;
                    ">
                        ${data.message || 'Oturumunuz yönetici tarafından kapatıldı. Lütfen tekrar giriş yapın.'}
                    </p>
                </div>
            `;
            
            // Show modal with custom content
            try {
                await BuggyModal.custom(modalContent, {
                    title: '',
                    confirmText: 'Giriş Sayfasına Git',
                    cancelText: null,
                    size: 'small'
                });
            } catch (error) {
                console.error('Error showing modal:', error);
            }
            
            // Redirect to logout
            window.location.href = '/auth/logout';
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
            
            if (locations.length === 0) {
                await BuggyModal.alert('Henüz lokasyon tanımlanmamış. Lütfen yöneticinizle iletişime geçin.');
                return;
            }
            
            // Store requestId for later use
            this.tempRequestId = requestId;
            
            // Create location cards (same style as initial setup)
            const locationCards = locations.map(loc => `
                <button 
                    type="button"
                    class="completion-location-card" 
                    data-location-id="${loc.id}"
                    style="
                        width: 100%;
                        padding: 1rem;
                        margin-bottom: 0.75rem;
                        background: white;
                        border: 2px solid #e2e8f0;
                        border-radius: 12px;
                        cursor: pointer;
                        transition: all 0.2s ease;
                        text-align: left;
                        display: flex;
                        align-items: center;
                        gap: 1rem;
                    "
                    onmouseover="this.style.borderColor='#10b981'; this.style.backgroundColor='#f0fdf4'; this.style.transform='translateY(-2px)'; this.style.boxShadow='0 4px 12px rgba(16, 185, 129, 0.15)';"
                    onmouseout="this.style.borderColor='#e2e8f0'; this.style.backgroundColor='white'; this.style.transform='translateY(0)'; this.style.boxShadow='none';"
                    onclick="DriverDashboard.selectCompletionLocation(${loc.id});"
                >
                    <div style="
                        width: 48px;
                        height: 48px;
                        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
                        border-radius: 12px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        flex-shrink: 0;
                    ">
                        <i class="fas fa-map-marker-alt" style="color: white; font-size: 1.25rem;"></i>
                    </div>
                    <div style="flex: 1;">
                        <div style="font-weight: 600; color: #1e293b; font-size: 1rem; margin-bottom: 0.25rem;">
                            ${loc.name}
                        </div>
                        <div style="font-size: 0.875rem; color: #64748b;">
                            Şu anki konumunuz
                        </div>
                    </div>
                    <div style="flex-shrink: 0;">
                        <i class="fas fa-check-circle" style="color: #cbd5e1; font-size: 1.25rem;"></i>
                    </div>
                </button>
            `).join('');
            
            const modalContent = `
                <div style="padding: 0;">
                    <p style="text-align: center; color: #64748b; margin-bottom: 1rem; font-size: 0.95rem;">
                        Talebi tamamladıktan sonra şu anki konumunuzu seçin
                    </p>
                    <div style="max-height: 400px; overflow-y: auto; padding: 0 0.25rem;">
                        ${locationCards}
                    </div>
                    
                    <div style="margin-top: 1.5rem; padding-top: 1rem; border-top: 1px solid #e2e8f0;">
                        <label style="display: block; font-size: 0.875rem; font-weight: 500; color: #64748b; margin-bottom: 0.5rem;">
                            <i class="fas fa-comment"></i> Notlar (Opsiyonel)
                        </label>
                        <textarea 
                            id="completion-notes" 
                            style="
                                width: 100%;
                                padding: 0.75rem;
                                border: 2px solid #e2e8f0;
                                border-radius: 8px;
                                font-size: 0.875rem;
                                resize: vertical;
                                min-height: 80px;
                                font-family: inherit;
                            "
                            placeholder="Varsa ek notlar yazabilirsiniz..."
                            onfocus="this.style.borderColor='#10b981'; this.style.outline='none';"
                            onblur="this.style.borderColor='#e2e8f0';"
                        ></textarea>
                    </div>
                </div>
            `;
            
            // Show modal without buttons (click on location to select)
            BuggyModal.custom(modalContent, {
                title: '✅ Talebi Tamamla',
                confirmText: '',
                cancelText: 'İptal',
                size: 'medium'
            });
            
            // Customize modal after it's shown
            setTimeout(() => {
                // Remove confirm button, keep cancel
                const confirmBtn = document.querySelector('.buggy-modal-footer .btn-primary');
                if (confirmBtn) {
                    confirmBtn.remove();
                }
                
                // Style cancel button
                const cancelBtn = document.querySelector('.buggy-modal-footer .btn-secondary');
                if (cancelBtn) {
                    cancelBtn.style.width = '100%';
                    cancelBtn.onclick = () => {
                        const overlay = document.querySelector('.buggy-modal-overlay');
                        if (overlay) {
                            BuggyModal.closeModal(overlay);
                        }
                    };
                }
                
                // Make header compact
                const modalHeader = document.querySelector('.buggy-modal-header');
                if (modalHeader) {
                    modalHeader.style.padding = '1rem 1.5rem';
                    modalHeader.style.background = 'linear-gradient(135deg, #10b981 0%, #059669 100%)';
                }
                
                // Style title
                const modalTitle = document.querySelector('.buggy-modal-title');
                if (modalTitle) {
                    modalTitle.style.fontSize = '1.25rem';
                    modalTitle.style.fontWeight = '600';
                    modalTitle.style.color = 'white';
                }
                
                // Change icon color
                const modalIcon = document.querySelector('.buggy-modal-icon i');
                if (modalIcon) {
                    modalIcon.style.color = 'white';
                }
            }, 100);
        } catch (error) {
            console.error('Error showing location selection modal:', error);
            await BuggyModal.alert('Lokasyonlar yüklenirken hata oluştu: ' + error.message);
        }
    },

    /**
     * Select completion location (called when clicking a location card)
     */
    async selectCompletionLocation(locationId) {
        try {
            // Get notes
            const notes = document.getElementById('completion-notes')?.value || '';
            
            // Close modal
            const overlay = document.querySelector('.buggy-modal-overlay');
            if (overlay) {
                BuggyModal.closeModal(overlay);
            }
            
            // Submit completion
            await this.submitCompletion(this.tempRequestId, locationId, notes);
        } catch (error) {
            console.error('Error selecting completion location:', error);
            await BuggyModal.alert('Lokasyon seçilirken hata oluştu: ' + error.message);
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
        
        // Show themed notification
        this.showNewRequestNotification(data);
    },

    /**
     * Show themed new request notification
     */
    showNewRequestNotification(data) {
        const locationName = data.location?.name || 'Bilinmeyen Lokasyon';
        const roomInfo = data.room_number ? `<div class="request-detail"><i class="fas fa-door-open"></i> Oda ${data.room_number}</div>` : '';
        const guestInfo = data.guest_name ? `<div class="request-detail"><i class="fas fa-user"></i> ${data.guest_name}</div>` : '';
        const phoneInfo = data.phone_number ? `<div class="request-detail"><i class="fas fa-phone"></i> ${data.phone_number}</div>` : '';
        
        // Create custom notification overlay
        const overlay = document.createElement('div');
        overlay.className = 'custom-notification-overlay';
        overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.7);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 10000;
            animation: fadeIn 0.3s ease;
        `;
        
        const modal = document.createElement('div');
        modal.style.cssText = `
            background: white;
            border-radius: 16px;
            max-width: 500px;
            width: 90%;
            padding: 2rem;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            animation: slideUp 0.3s ease;
        `;
        
        modal.innerHTML = `
            <style>
                @keyframes fadeIn {
                    from { opacity: 0; }
                    to { opacity: 1; }
                }
                @keyframes slideUp {
                    from { transform: translateY(50px); opacity: 0; }
                    to { transform: translateY(0); opacity: 1; }
                }
                @keyframes pulse {
                    0%, 100% {
                        transform: scale(1);
                        box-shadow: 0 8px 16px rgba(16, 185, 129, 0.3);
                    }
                    50% {
                        transform: scale(1.05);
                        box-shadow: 0 12px 24px rgba(16, 185, 129, 0.4);
                    }
                }
                .request-detail {
                    display: flex;
                    align-items: center;
                    gap: 0.75rem;
                    padding: 0.75rem;
                    background: white;
                    border-radius: 8px;
                    font-size: 1rem;
                    color: #334155;
                }
                .request-detail i {
                    width: 24px;
                    color: #0ea5e9;
                    font-size: 1.1rem;
                }
            </style>
            
            <div style="text-align: center;">
                <div style="
                    width: 100px;
                    height: 100px;
                    margin: 0 auto 1.5rem;
                    background: linear-gradient(135deg, #10b981 0%, #059669 100%);
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    box-shadow: 0 8px 16px rgba(16, 185, 129, 0.3);
                    animation: pulse 2s infinite;
                ">
                    <i class="fas fa-bell" style="font-size: 3rem; color: white;"></i>
                </div>
                
                <h3 style="
                    font-size: 1.75rem;
                    font-weight: 700;
                    color: #1e293b;
                    margin-bottom: 1.5rem;
                ">
                    🎉 Yeni Talep Geldi!
                </h3>
                
                <div style="
                    background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
                    border-radius: 12px;
                    padding: 1.5rem;
                    margin-bottom: 1rem;
                    border: 2px solid #0ea5e9;
                ">
                    <div style="
                        font-size: 1.25rem;
                        font-weight: 600;
                        color: #0c4a6e;
                        margin-bottom: 1rem;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        gap: 0.5rem;
                    ">
                        <i class="fas fa-map-marker-alt" style="color: #0ea5e9;"></i>
                        ${locationName}
                    </div>
                    
                    <div style="
                        display: flex;
                        flex-direction: column;
                        gap: 0.75rem;
                        text-align: left;
                    ">
                        ${guestInfo}
                        ${roomInfo}
                        ${phoneInfo}
                    </div>
                </div>
                
                <div style="
                    background: #fef3c7;
                    border-left: 4px solid #f59e0b;
                    padding: 1rem;
                    border-radius: 8px;
                    margin-top: 1rem;
                ">
                    <p style="
                        margin: 0;
                        color: #92400e;
                        font-size: 0.95rem;
                        font-weight: 500;
                    ">
                        <i class="fas fa-info-circle"></i> Bu pencereyi 5 saniye boyunca kapatmayın!
                    </p>
                </div>
            </div>
        `;
        
        overlay.appendChild(modal);
        document.body.appendChild(overlay);
        
        // Auto-close after 5 seconds
        setTimeout(() => {
            overlay.style.animation = 'fadeOut 0.3s ease';
            setTimeout(() => {
                if (overlay.parentNode) {
                    overlay.parentNode.removeChild(overlay);
                }
            }, 300);
        }, 5000);
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
        // WebSocket disconnect handler will automatically cleanup
        // No need for beforeunload - it's unreliable and causes issues
        console.log('Event listeners setup complete');
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
