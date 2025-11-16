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
        /**
        console.log('Driver dashboard initializing...');
        **/
        
        // Get data from dashboard container or body
        const container = document.querySelector('.driver-dashboard') || document.body;
        this.hotelId = parseInt(container.dataset.hotelId) || 1;
        this.userId = parseInt(container.dataset.userId) || 0;
        this.buggyId = parseInt(container.dataset.buggyId) || 0;
        const needsLocationSetup = container.dataset.needsLocationSetup === 'true';
        
        // Initialize pending render flag
        this._pendingRenderUpdate = false;
        
        // Driver data loaded
        
        // Check if driver has buggy assigned
        if (!this.buggyId || this.buggyId === '0') {
            console.warn('⚠️ No buggy assigned to driver - limited functionality');
            // Don't return - still initialize dashboard for UI
        }
        
        // Location setup is now handled by separate page (select_location.html)
        // No need for modal anymore
        
        // Initialize WebSocket connection
        if (typeof io !== 'undefined') {
            this.initSocket();
        } else {
            console.error('❌ WebSocket not available');
        }
        
        // Load initial data (even if no buggy, show empty state)
        await this.loadDriverData();
        
        // Setup event listeners
        this.setupEventListeners();
        
        // Setup visibility change handler for deferred updates
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden && this._pendingRenderUpdate) {
                this._pendingRenderUpdate = false;
                this.renderPendingRequests();
            }
        });
        
        // FCM sistemi kullanılıyor, eski push notification devre dışı
        // this.requestPushNotificationPermission();
        
        // Driver dashboard initialized
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
            
            // Create location cards with images
            const locationCards = locations.map(loc => {
                // Prepare image URL
                let imageHtml = '';
                if (loc.location_image) {
                    let imageUrl = loc.location_image;
                    // Convert to full URL if needed
                    if (imageUrl.startsWith('/')) {
                        imageUrl = window.location.origin + imageUrl;
                    } else if (!imageUrl.startsWith('http')) {
                        imageUrl = window.location.origin + '/' + imageUrl;
                    }
                    
                    imageHtml = `
                        <img 
                            src="${imageUrl}" 
                            alt="${loc.name}"
                            style="
                                width: 48px;
                                height: 48px;
                                border-radius: 12px;
                                object-fit: cover;
                                flex-shrink: 0;
                            "
                            onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';"
                        />
                        <div style="
                            width: 48px;
                            height: 48px;
                            background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%);
                            border-radius: 12px;
                            display: none;
                            align-items: center;
                            justify-content: center;
                            flex-shrink: 0;
                        ">
                            <i class="fas fa-map-marker-alt" style="color: white; font-size: 1.25rem;"></i>
                        </div>
                    `;
                } else {
                    imageHtml = `
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
                    `;
                }
                
                return `
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
                        ${imageHtml}
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
                `;
            }).join('');
            
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
            // ✅ FALLBACK: Start polling if WebSocket not available
            this.startPollingFallback();
            return;
        }

        // Initialize Socket.IO with polling first to avoid WebSocket frame errors
        this.socket = io({
            transports: ['polling', 'websocket'],  // Polling önce, sonra WebSocket
            reconnection: true,
            reconnectionDelay: 1000,
            reconnectionAttempts: 5,
            timeout: 10000,
            withCredentials: true,  // ✅ Cookie'leri gönder (session için gerekli)
            autoConnect: true
        });

        // ✅ ERROR HANDLING: Connection error
        this.socket.on('connect_error', (error) => {
            console.error('❌ WebSocket connection error:', error.message);
            this.updateConnectionStatus('error');
            // Fallback to polling after 3 failed attempts
            if (!this._pollingFallbackStarted && this.socket.io.reconnectionAttempts >= 3) {
                console.warn('⚠️ Starting polling fallback after connection errors');
                this.startPollingFallback();
            }
        });

        // ✅ ERROR HANDLING: Reconnection failed
        this.socket.on('reconnect_failed', () => {
            console.error('❌ WebSocket reconnection failed - switching to polling');
            this.updateConnectionStatus('disconnected');
            this.startPollingFallback();
        });

        // Join hotel drivers room and user-specific room
        this.socket.on('connect', () => {
            console.log('✅ Socket connected');
            this.updateConnectionStatus('connected');
            // ✅ Stop polling if WebSocket connected
            this.stopPollingFallback();

            this.socket.emit('join_hotel', {
                hotel_id: this.hotelId,
                role: 'driver'
            });
            // Join user-specific room for session management
            this.socket.emit('join_user', {
                user_id: this.userId
            });
        });

        this.socket.on('disconnect', () => {
            console.log('❌ Socket disconnected');
            this.updateConnectionStatus('disconnected');
        });

        this.socket.on('reconnecting', (attemptNumber) => {
            console.log(`🔄 Reconnecting... (attempt ${attemptNumber})`);
            this.updateConnectionStatus('connecting');
        });
        
        this.socket.on('joined_hotel', (data) => {
            console.log('✅ Joined hotel room');
        });
        
        // Listen to guest connected (pre-alert)
        this.socket.on('guest_connected', (data) => {
            console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
            console.log('🚨 [GUEST_CONNECTED] Event received!');
            console.log('   Data:', data);
            console.log('   Location:', data.location_name || 'Bilinmeyen Lokasyon');
            console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
            
            // ✅ Show toast notification
            this.showGuestConnectedAlert(data);
            
            // ✅ Play notification sound
            this.playNotificationSound();
        });
        
        // Listen to new requests
        this.socket.on('new_request', (data) => {
            console.log('🎉 [DRIVER] Yeni talep:', data.request_id);
            
            // Add to pending list
            this.pendingRequests.unshift(data);
            this.renderPendingRequests();
            this.updatePendingCount();
            
            // Play notification sound
            this.playNotificationSound();
            
            // ✅ FOREGROUND DIALOG: Show dialog notification
            this.showNewRequestDialog(data);
            
            // Show push notification if available
            this.showPushNotification(data);
        });
        
        // Listen to request taken by another driver
        this.socket.on('request_taken', (data) => {
            this.removeRequest(data.request_id);
        });
        
        // Listen to request cancelled
        this.socket.on('request_cancelled', (data) => {
            if (this.currentRequest && this.currentRequest.id === data.request_id) {
                this.currentRequest = null;
            }
            this.removeRequest(data.request_id);
        });
        
        // Listen to force logout
        this.socket.on('force_logout', async (data) => {
            
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
            // Backend will handle setting buggy to offline
        });
    },

    /**
     * Load driver data
     */
    async loadDriverData() {
        try {
            // Load PENDING requests
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
            // Check if driver has buggy assigned
            if (!this.buggyId || this.buggyId === 0) {
            
                this.pendingRequests = [];
                this.renderPendingRequests();
                this.updatePendingCount();
                return;
            }
            
         
            const response = await fetch('/api/driver/pending-requests');
            const data = await response.json();
            
            if (!response.ok || !data.success) {
                console.warn('❌ Failed to load pending requests:', data.error);
                this.pendingRequests = [];
                this.renderPendingRequests();
                this.updatePendingCount();
                return;
            }
            
            this.pendingRequests = data.requests || [];
            this.renderPendingRequests();
            this.updatePendingCount();
        } catch (error) {
            console.error('❌ Error loading pending requests:', error);
            this.pendingRequests = [];
            this.renderPendingRequests();
            this.updatePendingCount();
        }
    },

    /**
     * Load current request
     */
    async loadCurrentRequest() {
        try {
            // Check if driver has buggy assigned
            if (!this.buggyId || this.buggyId === 0) {
                this.currentRequest = null;
                this.renderCurrentRequest();
                return;
            }
            
            const response = await fetch('/api/driver/active-request');
            const data = await response.json();
            
            if (!response.ok || !data.success) {
                console.warn('Failed to load current request:', data.error);
                this.currentRequest = null;
                this.renderCurrentRequest();
                return;
            }
            
            this.currentRequest = data.request;
            this.renderCurrentRequest();
        } catch (error) {
            console.error('Error loading current request:', error);
            this.currentRequest = null;
            this.renderCurrentRequest();
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
     * Render pending requests (optimized with RAF and diff-based updates)
     */
    renderPendingRequests() {
        const container = document.getElementById('pending-requests');
        const badge = document.getElementById('pending-badge');
        
        if (!container) return;
        
        // Defer updates if page is in background
        if (document.hidden) {
            this._pendingRenderUpdate = true;
            return;
        }
        
        // Use RequestAnimationFrame for smooth rendering
        requestAnimationFrame(() => {
            if (this.pendingRequests.length === 0) {
                // Only update if content changed
                if (!container.querySelector('.empty-state')) {
                    container.innerHTML = `
                        <div class="empty-state">
                            <i class="fas fa-check-circle"></i>
                            <p>Bekleyen talep yok</p>
                        </div>
                    `;
                }
                if (badge && badge.textContent !== '0') badge.textContent = '0';
                return;
            }
            
            // Update badge only if changed
            if (badge && badge.textContent !== String(this.pendingRequests.length)) {
                badge.textContent = this.pendingRequests.length;
            }
        
            // Get existing request IDs for diff
            const existingIds = new Set(
                Array.from(container.querySelectorAll('.request-card'))
                    .map(card => parseInt(card.dataset.id))
            );
            
            const currentIds = new Set(this.pendingRequests.map(r => r.id));
            
            // Remove deleted requests
            existingIds.forEach(id => {
                if (!currentIds.has(id)) {
                    const card = container.querySelector(`[data-id="${id}"]`);
                    if (card) card.remove();
                }
            });
            
            // Add or update requests
            this.pendingRequests.forEach((req, index) => {
                if (!req.id) {
                    console.error('❌ [DRIVER] Request missing ID:', req);
                    return;
                }
                
                let card = container.querySelector(`[data-id="${req.id}"]`);
                
                // Only update time if card exists (avoid full re-render)
                if (card) {
                    const timeElement = card.querySelector('.request-time');
                    if (timeElement) {
                        const newTimeAgo = this.getTimeAgo(req.requested_at);
                        const currentTime = timeElement.textContent.replace(/.*\s/, '');
                        if (currentTime !== newTimeAgo) {
                            timeElement.innerHTML = `<i class="fas fa-clock"></i> ${newTimeAgo}`;
                        }
                    }
                    return;
                }
                
                // Create new card
                const timeAgo = this.getTimeAgo(req.requested_at);
                const newCard = document.createElement('div');
                newCard.className = 'request-card';
                newCard.dataset.id = req.id;
                
                newCard.innerHTML = `
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
                `;
                
                // Insert at correct position
                if (index === 0) {
                    container.insertBefore(newCard, container.firstChild);
                } else {
                    const prevCard = container.querySelector(`[data-id="${this.pendingRequests[index - 1].id}"]`);
                    if (prevCard && prevCard.nextSibling) {
                        container.insertBefore(newCard, prevCard.nextSibling);
                    } else {
                        container.appendChild(newCard);
                    }
                }
            });
        });
    },

    /**
     * Render current request
     */
    renderCurrentRequest() {
        const container = document.getElementById('current-request');
        const section = document.getElementById('current-request-section');
        const pendingSection = document.getElementById('pending-requests-section');
        const activeCount = document.getElementById('active-request-count');
        
        if (!container) return;
        
        if (!this.currentRequest) {
            // Hide active request section, show pending requests section
            if (section) section.style.display = 'none';
            if (pendingSection) pendingSection.style.display = 'block';
            if (activeCount) activeCount.textContent = '0';
            return;
        }
        
        // Show active request section, hide pending requests section
        if (section) section.style.display = 'block';
        if (pendingSection) pendingSection.style.display = 'none';
        
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
     * Update PENDING count
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
            
            // Create location cards with images
            const locationCards = locations.map(loc => {
                // Prepare image URL
                let imageHtml = '';
                if (loc.location_image) {
                    let imageUrl = loc.location_image;
                    // Convert to full URL if needed
                    if (imageUrl.startsWith('/')) {
                        imageUrl = window.location.origin + imageUrl;
                    } else if (!imageUrl.startsWith('http')) {
                        imageUrl = window.location.origin + '/' + imageUrl;
                    }
                    
                    imageHtml = `
                        <img 
                            src="${imageUrl}" 
                            alt="${loc.name}"
                            style="
                                width: 48px;
                                height: 48px;
                                border-radius: 12px;
                                object-fit: cover;
                                flex-shrink: 0;
                            "
                            onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';"
                        />
                        <div style="
                            width: 48px;
                            height: 48px;
                            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
                            border-radius: 12px;
                            display: none;
                            align-items: center;
                            justify-content: center;
                            flex-shrink: 0;
                        ">
                            <i class="fas fa-map-marker-alt" style="color: white; font-size: 1.25rem;"></i>
                        </div>
                    `;
                } else {
                    imageHtml = `
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
                    `;
                }
                
                return `
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
                        ${imageHtml}
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
                `;
            }).join('');
            
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
        
        // Show browser push notification
        this.showPushNotification(data);
        
        // Show themed notification
        this.showNewRequestNotification(data);
    },

    /**
     * Show browser push notification for new request
     */
    async showPushNotification(data) {
        try {
            // Check if pushNotifications is available
            if (typeof pushNotifications === 'undefined') {
                console.warn('[DriverDashboard] pushNotifications not available');
                return;
            }

            const locationName = data.location?.name || 'Bilinmeyen Lokasyon';
            const guestInfo = data.guest_name || 'Misafir';
            const roomInfo = data.room_number ? ` - Oda ${data.room_number}` : '';
            
            // Show notification
            await pushNotifications.showNotification('🚗 Yeni Shuttle Talebi!', {
                body: `${locationName}\n${guestInfo}${roomInfo}`,
                icon: '/static/icons/Icon-192.png',
                badge: '/static/icons/Icon-96.png',
                tag: `request-${data.request_id}`,
                requireInteraction: true, // Keep notification visible
                vibrate: [200, 100, 200, 100, 200], // Vibration pattern
                data: {
                    type: 'new_request',
                    requestId: data.request_id,
                    url: '/driver/dashboard'
                },
                actions: [
                    {
                        action: 'view',
                        title: '👀 Görüntüle',
                        icon: '/static/icons/Icon-96.png'
                    }
                ]
            });
            
            console.log('🔔 [DRIVER] Bildirim gönderildi:', data.request_id);
        } catch (error) {
            console.error('❌ [DRIVER] Bildirim hatası:', error);
        }
    },

    /**
     * ✅ FOREGROUND DIALOG: Show new request dialog
     */
    showNewRequestDialog(data) {
        console.log('🔔 [DIALOG] Showing new request dialog:', data);

        // Remove existing dialog if any
        const existingDialog = document.getElementById('new-request-dialog');
        if (existingDialog) {
            console.log('⚠️ [DIALOG] Removing existing dialog');
            existingDialog.remove();
        }

        const locationName = data.location?.name || 'Bilinmeyen lokasyon';
        const roomNumber = data.room_number || 'Belirtilmemiş';
        const guestName = data.guest_name || '';
        const phone = data.phone_number || '';
        const notes = data.notes || '';

        console.log('📋 [DIALOG] Dialog data:', {locationName, roomNumber, guestName, phone, notes});

        const dialogHTML = `
            <div class="request-dialog-overlay" id="new-request-dialog" style="
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
            ">
                <div class="request-dialog" style="
                    background: white;
                    border-radius: 16px;
                    max-width: 500px;
                    width: 90%;
                    padding: 0;
                    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
                    animation: slideUp 0.3s ease;
                ">
                    <div class="request-dialog-header" style="
                        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
                        color: white;
                        padding: 1.5rem;
                        border-radius: 16px 16px 0 0;
                        text-align: center;
                        position: relative;
                    ">
                        <div class="request-dialog-icon" style="
                            width: 80px;
                            height: 80px;
                            margin: 0 auto 1rem;
                            background: rgba(255, 255, 255, 0.2);
                            border-radius: 50%;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            font-size: 2.5rem;
                            animation: pulse 2s infinite;
                        ">
                            <i class="fas fa-bell"></i>
                        </div>
                        <h3 style="margin: 0; font-size: 1.5rem; font-weight: 700;">🚗 YENİ SHUTTLE TALEBİ!</h3>
                        <button class="request-dialog-close" onclick="DriverDashboard.closeNewRequestDialog()" style="
                            position: absolute;
                            top: 1rem;
                            right: 1rem;
                            background: rgba(255, 255, 255, 0.2);
                            border: none;
                            color: white;
                            width: 32px;
                            height: 32px;
                            border-radius: 50%;
                            cursor: pointer;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            font-size: 1.25rem;
                        ">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                    <div class="request-dialog-body" style="padding: 1.5rem;">
                        <div style="
                            background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
                            border-radius: 12px;
                            padding: 1rem;
                            margin-bottom: 1rem;
                            border: 2px solid #0ea5e9;
                        ">
                            <div style="
                                font-size: 1.25rem;
                                font-weight: 600;
                                color: #0c4a6e;
                                margin-bottom: 0.75rem;
                                display: flex;
                                align-items: center;
                                gap: 0.5rem;
                            ">
                                <i class="fas fa-map-marker-alt" style="color: #0ea5e9;"></i>
                                ${this.escapeHtml(locationName)}
                            </div>
                            ${roomNumber !== 'Belirtilmemiş' ? `
                            <div style="display: flex; align-items: center; gap: 0.75rem; padding: 0.5rem 0; color: #334155;">
                                <i class="fas fa-door-open" style="width: 24px; color: #0ea5e9;"></i>
                                <div><strong>Oda:</strong> ${this.escapeHtml(roomNumber)}</div>
                            </div>
                            ` : ''}
                            ${guestName ? `
                            <div style="display: flex; align-items: center; gap: 0.75rem; padding: 0.5rem 0; color: #334155;">
                                <i class="fas fa-user" style="width: 24px; color: #0ea5e9;"></i>
                                <div><strong>Misafir:</strong> ${this.escapeHtml(guestName)}</div>
                            </div>
                            ` : ''}
                            ${phone ? `
                            <div style="display: flex; align-items: center; gap: 0.75rem; padding: 0.5rem 0; color: #334155;">
                                <i class="fas fa-phone" style="width: 24px; color: #0ea5e9;"></i>
                                <div><strong>Telefon:</strong> ${this.escapeHtml(phone)}</div>
                            </div>
                            ` : ''}
                            ${notes ? `
                            <div style="display: flex; align-items: center; gap: 0.75rem; padding: 0.5rem 0; color: #334155;">
                                <i class="fas fa-sticky-note" style="width: 24px; color: #0ea5e9;"></i>
                                <div><strong>Not:</strong> ${this.escapeHtml(notes)}</div>
                            </div>
                            ` : ''}
                        </div>
                        <div style="
                            background: #fef3c7;
                            border-left: 4px solid #f59e0b;
                            padding: 0.75rem;
                            border-radius: 8px;
                            margin-bottom: 1rem;
                        ">
                            <p style="margin: 0; color: #92400e; font-size: 0.875rem; font-weight: 500;">
                                <i class="fas fa-info-circle"></i> Bu talep 30 saniye sonra otomatik kapanacak
                            </p>
                        </div>
                    </div>
                    <div class="request-dialog-footer" style="
                        padding: 1rem 1.5rem;
                        border-top: 1px solid #e5e7eb;
                        display: flex;
                        gap: 0.75rem;
                    ">
                        <button onclick="DriverDashboard.closeNewRequestDialog()" style="
                            flex: 1;
                            padding: 0.75rem;
                            background: #f3f4f6;
                            border: none;
                            border-radius: 8px;
                            font-weight: 600;
                            cursor: pointer;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            gap: 0.5rem;
                        ">
                            <i class="fas fa-times"></i>
                            Kapat
                        </button>
                        <button onclick="DriverDashboard.acceptRequestFromDialog(${data.id || data.request_id})" style="
                            flex: 2;
                            padding: 0.75rem;
                            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
                            color: white;
                            border: none;
                            border-radius: 8px;
                            font-weight: 600;
                            cursor: pointer;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            gap: 0.5rem;
                        ">
                            <i class="fas fa-check"></i>
                            Kabul Et
                        </button>
                    </div>
                </div>
            </div>
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
                    0%, 100% { transform: scale(1); }
                    50% { transform: scale(1.1); }
                }
            </style>
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
     * Show themed new request notification (DEPRECATED - use showNewRequestDialog instead)
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
     * Request push notification permission
     * Uses notification-permission.js handler for consistent UX
     */
    async requestPushNotificationPermission() {
        // Check if push notifications are supported
        if (!('Notification' in window)) {
            console.warn('[Push] Notifications not supported');
            return;
        }

        // Check current permission
        if (Notification.permission === 'granted') {
            // Subscribe to push notifications
            await this.subscribeToPushNotifications();
            return;
        }

        // notification-permission.js handler will show dialog automatically
        // based on permission status (default/denied)
    },

    /**
     * Subscribe to push notifications
     */
    async subscribeToPushNotifications() {
        if (typeof pushNotifications !== 'undefined') {
            try {
                await pushNotifications.subscribe();
            } catch (error) {
                console.error('❌ [DRIVER] Push subscription error:', error);
            }
        }
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
     * Remove request (taken by another driver)
     */
    removeRequest(requestId) {
        // Find the request before removing
        const request = this.pendingRequests.find(r => r.id === requestId);
        
        // Remove from list
        this.pendingRequests = this.pendingRequests.filter(r => r.id !== requestId);
        this.renderPendingRequests();
        this.updatePendingCount();
        
        // Show notification that request was taken
        if (request) {
            this.showRequestTakenNotification(request);
        }
    },

    /**
     * Show notification when request is taken by another driver
     */
    showRequestTakenNotification(request) {
        const locationName = request.location?.name || 'Bilinmeyen Lokasyon';
        
        // Create toast notification
        const toast = document.createElement('div');
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: linear-gradient(135deg, #6b7280 0%, #4b5563 100%);
            color: white;
            padding: 16px 20px;
            border-radius: 12px;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
            z-index: 10001;
            animation: slideInRight 0.3s ease-out;
            max-width: 400px;
            display: flex;
            align-items: center;
            gap: 12px;
        `;
        
        toast.innerHTML = `
            <div style="
                width: 40px;
                height: 40px;
                background: rgba(255, 255, 255, 0.2);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                flex-shrink: 0;
            ">
                <i class="fas fa-info-circle" style="font-size: 1.25rem;"></i>
            </div>
            <div>
                <strong style="display: block; margin-bottom: 4px;">Talep Alındı</strong>
                <span style="font-size: 0.875rem; opacity: 0.9;">
                    ${locationName} talebi başka bir sürücü tarafından kabul edildi.
                </span>
            </div>
        `;
        
        document.body.appendChild(toast);
        
        // Auto remove after 4 seconds
        setTimeout(() => {
            toast.style.animation = 'slideInRight 0.3s ease-in reverse';
            setTimeout(() => {
                toast.remove();
            }, 300);
        }, 4000);
    },

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // WebSocket disconnect handler will automatically cleanup
        // No need for beforeunload - backend handles it via WebSocket disconnect
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

        try {
            const date = new Date(dateStr);
            const now = new Date();

            // Geçersiz tarih kontrolü
            if (isNaN(date.getTime())) {
                console.warn('[TimeAgo] Invalid date:', dateStr);
                return '';
            }

            const seconds = Math.floor((now - date) / 1000);

            // Gelecekteki tarihler için kontrol
            if (seconds < 0) {
                console.warn('[TimeAgo] Future date detected:', dateStr);
                return 'Az önce';
            }

            // Zaman dilimleri
            if (seconds < 10) return 'Şimdi';
            if (seconds < 60) return 'Az önce';

            const minutes = Math.floor(seconds / 60);
            if (minutes === 1) return '1 dakika önce';
            if (minutes < 60) return `${minutes} dakika önce`;

            const hours = Math.floor(minutes / 60);
            if (hours === 1) return '1 saat önce';
            if (hours < 24) return `${hours} saat önce`;

            const days = Math.floor(hours / 24);
            if (days === 1) return '1 gün önce';
            if (days < 7) return `${days} gün önce`;

            const weeks = Math.floor(days / 7);
            if (weeks === 1) return '1 hafta önce';
            if (weeks < 4) return `${weeks} hafta önce`;

            const months = Math.floor(days / 30);
            if (months === 1) return '1 ay önce';
            if (months < 12) return `${months} ay önce`;

            const years = Math.floor(days / 365);
            return `${years} yıl önce`;

        } catch (error) {
            console.error('[TimeAgo] Error:', error, 'Date:', dateStr);
            return '';
        }
    },

    /**
     * Update connection status indicator
     */
    updateConnectionStatus(status) {
        const statusElement = document.getElementById('connection-status');
        const textElement = document.getElementById('connection-text');

        if (!statusElement || !textElement) return;

        // ✅ ERROR HANDLING: Remove all status classes including new ones
        statusElement.classList.remove('connected', 'disconnected', 'connecting', 'error', 'polling');

        // Add new status class and update text
        switch(status) {
            case 'connected':
                statusElement.classList.add('connected');
                textElement.innerHTML = '<i class="fas fa-check-circle"></i> Sisteme Bağlı';
                break;
            case 'disconnected':
                statusElement.classList.add('disconnected');
                textElement.innerHTML = '<i class="fas fa-times-circle"></i> Bağlantı Kesildi';
                break;
            case 'connecting':
                statusElement.classList.add('connecting');
                textElement.innerHTML = '<i class="fas fa-sync fa-spin"></i> Bağlanıyor...';
                break;
            case 'error':
                statusElement.classList.add('error');
                textElement.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Bağlantı Hatası';
                break;
            case 'polling':
                statusElement.classList.add('polling');
                textElement.innerHTML = '<i class="fas fa-sync fa-spin"></i> Yedek Mod (Polling)';
                break;
        }
    },

    /**
     * Show guest connected alert (5 seconds blinking)
     */
    showGuestConnectedAlert(data) {
        // Create alert element
        const alertId = 'guest-alert-' + Date.now();
        const alert = document.createElement('div');
        alert.id = alertId;
        alert.className = 'guest-alert';
        
        alert.innerHTML = `
            <div class="guest-alert-icon">
                🚨
            </div>
            <div class="guest-alert-content">
                <div class="guest-alert-title">Yeni Misafir Bağlandı!</div>
                <div class="guest-alert-location">${data.location_name}</div>
            </div>
        `;
        
        // Add to page - prepend to body to ensure it's on top
        document.body.insertBefore(alert, document.body.firstChild);
        
        // Play sound
        this.playAlertSound();
        
        // Remove after 5 seconds
        setTimeout(() => {
            alert.style.animation = 'slideOutRight 0.3s ease';
            setTimeout(() => {
                if (document.getElementById(alertId)) {
                    document.body.removeChild(alert);
                }
            }, 300);
        }, 5000);
    },

    /**
     * Play alert sound
     */
    playAlertSound() {
        try {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            
            // Play two beeps
            [800, 1000].forEach((freq, index) => {
                setTimeout(() => {
                    const oscillator = audioContext.createOscillator();
                    const gainNode = audioContext.createGain();
                    
                    oscillator.connect(gainNode);
                    gainNode.connect(audioContext.destination);
                    
                    oscillator.frequency.value = freq;
                    oscillator.type = 'sine';
                    
                    gainNode.gain.setValueAtTime(0, audioContext.currentTime);
                    gainNode.gain.linearRampToValueAtTime(0.3, audioContext.currentTime + 0.01);
                    gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.2);
                    
                    oscillator.start(audioContext.currentTime);
                    oscillator.stop(audioContext.currentTime + 0.2);
                }, index * 250);
            });
        } catch (error) {
            console.error('Error playing alert sound:', error);
        }
    },

    /**
     * ✅ POLLING FALLBACK: Start polling when WebSocket fails
     */
    startPollingFallback() {
        if (this._pollingFallbackStarted) {
            return; // Already started
        }

        console.warn('🔄 Starting polling fallback (WebSocket unavailable)');
        this._pollingFallbackStarted = true;
        this.updateConnectionStatus('polling');

        // Poll for pending requests every 5 seconds
        this._pollingInterval = setInterval(async () => {
            try {
                await this.loadPendingRequests();
            } catch (error) {
                console.error('Polling error:', error);
            }
        }, 5000);

        console.log('✅ Polling fallback started (5s interval)');
    },

    /**
     * ✅ POLLING FALLBACK: Stop polling when WebSocket reconnects
     */
    stopPollingFallback() {
        if (!this._pollingFallbackStarted) {
            return;
        }

        console.log('⏹️ Stopping polling fallback (WebSocket connected)');
        this._pollingFallbackStarted = false;

        if (this._pollingInterval) {
            clearInterval(this._pollingInterval);
            this._pollingInterval = null;
        }
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
window.driverDashboard = DriverDashboard; // Lowercase alias for easy access
