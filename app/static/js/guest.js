/**
 * Shuttle Call - Guest Panel JavaScript
 * QR code scanning and real-time request tracking
 */

const Guest = {
    hotelId: null,
    locationId: null,
    requestId: null,
    socket: null,
    html5QrCode: null,

    /**
     * Initialize guest panel
     */
    init() {
        console.log('Guest panel initializing...');
        
        // Get hotel ID from session
        this.hotelId = document.body.dataset.hotelId || 1;
        
        // Check if we have a location from URL
        const urlParams = new URLSearchParams(window.location.search);
        this.locationId = urlParams.get('location');
        
        // Initialize Socket.IO
        this.initSocket();
        
        // Load available locations
        this.loadLocations();
        
        // Setup event listeners
        this.setupEventListeners();
        
        // Auto-fill if location is provided
        if (this.locationId) {
            this.loadLocationData();
        }
        
        console.log('Guest panel initialized');
    },

    /**
     * Initialize WebSocket connection
     */
    initSocket() {
        this.socket = BuggyCall.Socket.init();
        this.socket.connect();
        
        this.socket.on('connect', () => {
            console.log('Socket connected');
        });
    },

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // QR Scanner button
        const scanBtn = document.getElementById('scan-qr-btn');
        if (scanBtn) {
            scanBtn.addEventListener('click', () => this.startQRScanner());
        }
        
        // Call buggy form
        const callForm = document.getElementById('call-buggy-form');
        if (callForm) {
            callForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                // Direkt submit et (confirmation modal'ı atla)
                await this.submitRequest();
            });
        }
        
        // Location select
        const locationSelect = document.getElementById('location-select');
        if (locationSelect) {
            locationSelect.addEventListener('change', (e) => {
                this.locationId = e.target.value;
            });
        }
    },

    /**
     * Start QR code scanner
     */
    async startQRScanner() {
        const modal = document.getElementById('qr-scanner-modal');
        if (!modal) {
            console.error('QR scanner modal not found');
            return;
        }
        
        // Show modal (Tailwind - remove hidden class, add flex)
        modal.classList.remove('hidden');
        modal.classList.add('flex');
        
        // Initialize scanner
        const readerElement = document.getElementById('qr-reader');
        if (!readerElement) {
            console.error('QR reader element not found');
            return;
        }
        
        // Use html5-qrcode library
        if (typeof Html5Qrcode === 'undefined') {
            await BuggyCall.Utils.showError('QR kod tarayıcı yüklenemedi. Lütfen sayfayı yenileyin.');
            return;
        }
        
        this.html5QrCode = new Html5Qrcode("qr-reader");
        
        const config = { 
            fps: 10, 
            qrbox: { width: 250, height: 250 },
            aspectRatio: 1.0
        };
        
        this.html5QrCode.start(
            { facingMode: "environment" },
            config,
            (decodedText, decodedResult) => {
                console.log('QR Code detected:', decodedText);
                this.handleQRCodeScan(decodedText);
                this.stopQRScanner();
                modal.classList.add('hidden');
                modal.classList.remove('flex');
            },
            (errorMessage) => {
                // Scanning errors are common, don't spam console
            }
        ).catch(async (err) => {
            console.error('Failed to start scanner:', err);
            await BuggyCall.Utils.showError('Kamera erişimi reddedildi. Lütfen tarayıcı ayarlarından kamera iznini kontrol edin.');
        });
        
        // Stop scanner when modal is closed (Tailwind modal close)
        const closeButtons = modal.querySelectorAll('.modal-close, .modal-backdrop');
        closeButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                modal.classList.add('hidden');
                modal.classList.remove('flex');
                this.stopQRScanner();
            });
        });
    },

    /**
     * Stop QR code scanner
     */
    stopQRScanner() {
        if (this.html5QrCode) {
            this.html5QrCode.stop().then(() => {
                console.log('QR scanner stopped');
                this.html5QrCode.clear();
                this.html5QrCode = null;
            }).catch(err => {
                console.error('Failed to stop scanner:', err);
            });
        }
    },

    /**
     * Handle QR code scan
     */
    async handleQRCodeScan(qrData) {
        try {
            // Check if QR code contains a URL format (new format)
            if (qrData.startsWith('http://') || qrData.startsWith('https://')) {
                console.log('URL format detected, redirecting to:', qrData);
                // URL format - redirect directly
                window.location.href = qrData;
                return;
            }
            
            // Parse QR data - legacy formats: LOC1001 or {"hotel_id": 1, "location_id": 3}
            let locationId = null;
            let hotelId = this.hotelId;
            
            // Check if it's LOC format (legacy)
            if (qrData.startsWith('LOC')) {
                console.log('Legacy LOC format detected:', qrData);
                
                // Find location by QR code data
                try {
                    const response = await fetch('/api/locations');
                    const data = await response.json();
                    
                    if (data.success && data.locations) {
                        const location = data.locations.find(loc => loc.qr_code_data === qrData);
                        
                        if (location) {
                            locationId = location.id;
                            hotelId = location.hotel_id || this.hotelId;
                        }
                    }
                } catch (e) {
                    console.error('Error fetching locations:', e);
                }
            } else {
                // Try to parse as JSON (legacy format)
                try {
                    const data = JSON.parse(qrData);
                    locationId = data.location_id;
                    hotelId = data.hotel_id || this.hotelId;
                } catch (e) {
                    console.error('Failed to parse QR data as JSON:', e);
                }
            }
            
            if (!locationId) {
                await BuggyCall.Utils.showError('Geçersiz QR kod formatı. Lütfen geçerli bir lokasyon QR kodu tarayın.');
                return;
            }
            
            this.locationId = locationId;
            this.hotelId = hotelId;
            
            // Load location data
            await this.loadLocationData();
            
            await BuggyCall.Utils.showSuccess('Lokasyon başarıyla tanımlandı!');
        } catch (error) {
            console.error('QR code parse error:', error);
            await BuggyCall.Utils.showError('QR kod okunamadı. Lütfen tekrar deneyin.');
        }
    },

    /**
     * Load available locations
     */
    async loadLocations() {
        try {
            const response = await fetch('/api/locations');
            const data = await response.json();
            
            if (data.success && data.locations) {
                this.allLocations = data.locations; // Store for search
                const locationSelect = document.getElementById('location-select');
                if (locationSelect) {
                    // Add locations to dropdown
                    data.locations.forEach(loc => {
                        const option = document.createElement('option');
                        option.value = loc.id;
                        option.textContent = loc.name;
                        locationSelect.appendChild(option);
                    });
                }
                
                // Setup search functionality
                this.setupLocationSearch();
            }
        } catch (error) {
            console.error('Error loading locations:', error);
        }
    },

    /**
     * Setup location search functionality
     */
    setupLocationSearch() {
        const searchInput = document.getElementById('location-search');
        if (!searchInput) return;
        
        searchInput.addEventListener('input', (e) => {
            this.searchLocations(e.target.value);
        });
    },

    /**
     * Search locations by name or description
     */
    searchLocations(query) {
        if (!this.allLocations) return;
        
        const locationSelect = document.getElementById('location-select');
        if (!locationSelect) return;
        
        const searchTerm = query.toLowerCase().trim();
        
        // Clear existing options except first (placeholder)
        const placeholder = locationSelect.options[0];
        locationSelect.innerHTML = '';
        if (placeholder) {
            locationSelect.appendChild(placeholder);
        }
        
        // Filter and display matching locations
        const filteredLocations = this.allLocations.filter(loc => {
            return loc.name.toLowerCase().includes(searchTerm) ||
                   (loc.description && loc.description.toLowerCase().includes(searchTerm));
        });
        
        filteredLocations.forEach(loc => {
            const option = document.createElement('option');
            option.value = loc.id;
            option.textContent = loc.name;
            locationSelect.appendChild(option);
        });
        
        // Show count
        const resultCount = document.getElementById('search-result-count');
        if (resultCount) {
            resultCount.textContent = `${filteredLocations.length} lokasyon bulundu`;
        }
    },

    /**
     * Load location data
     */
    async loadLocationData() {
        if (!this.locationId) return;
        
        try {
            const response = await BuggyCall.API.get(`/locations/${this.locationId}`);
            const location = response.location;
            
            // Update UI
            const locationNameEl = document.getElementById('location-name');
            const locationNameContainer = document.getElementById('location-name-container');
            if (locationNameEl && locationNameContainer) {
                locationNameEl.textContent = location.name;
                locationNameContainer.classList.remove('d-none');
            }
            
            // Update select
            const locationSelect = document.getElementById('location-select');
            if (locationSelect) {
                locationSelect.value = this.locationId;
            }
            
            // Show call form
            const callFormContainer = document.getElementById('call-form-container');
            if (callFormContainer) {
                callFormContainer.classList.remove('d-none');
            }
        } catch (error) {
            console.error('Error loading location:', error);
            await BuggyCall.Utils.showError('Lokasyon bilgisi alınamadı: ' + error.message);
        }
    },

    /**
     * Show call confirmation modal
     */
    async showCallConfirmation() {
        const i18n = window.guestI18n || { t: (key) => key };
        const formData = BuggyCall.Form.getData('call-buggy-form');
        
        // Validation
        if (!this.locationId) {
            await BuggyCall.Utils.showWarning(i18n.t('error.no_location'));
            return;
        }
        
        // Get location name
        const locationSelect = document.getElementById('location-select');
        const locationName = locationSelect?.options[locationSelect.selectedIndex]?.text || 'Seçili Lokasyon';
        
        // Build confirmation details
        const roomInfo = formData.room_number ? `<div class="confirm-detail"><i class="fas fa-door-open"></i> ${i18n.t('confirm.room')}: ${formData.room_number}</div>` : '';
        const notesInfo = formData.notes ? `<div class="confirm-detail"><i class="fas fa-comment"></i> ${i18n.t('call.notes')}: ${formData.notes}</div>` : '';
        
        // Create custom confirmation overlay
        const overlay = document.createElement('div');
        overlay.className = 'custom-confirmation-overlay';
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
                @keyframes questionPulse {
                    0%, 100% {
                        transform: scale(1);
                        box-shadow: 0 8px 16px rgba(249, 115, 22, 0.3);
                    }
                    50% {
                        transform: scale(1.05);
                        box-shadow: 0 12px 24px rgba(249, 115, 22, 0.4);
                    }
                }
                .confirm-detail {
                    display: flex;
                    align-items: center;
                    gap: 0.75rem;
                    padding: 0.75rem;
                    background: #f8fafc;
                    border-radius: 8px;
                    font-size: 1rem;
                    color: #334155;
                    margin-bottom: 0.5rem;
                }
                .confirm-detail i {
                    width: 24px;
                    color: #1BA5A8;
                    font-size: 1.1rem;
                }
                .confirm-btn {
                    padding: 1rem 2rem;
                    border: none;
                    border-radius: 12px;
                    font-size: 1.1rem;
                    font-weight: 600;
                    cursor: pointer;
                    transition: all 0.2s ease;
                    flex: 1;
                }
                .confirm-btn-yes {
                    background: linear-gradient(135deg, #10b981 0%, #059669 100%);
                    color: white;
                }
                .confirm-btn-yes:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 8px 16px rgba(16, 185, 129, 0.3);
                }
                .confirm-btn-no {
                    background: #e2e8f0;
                    color: #64748b;
                }
                .confirm-btn-no:hover {
                    background: #cbd5e1;
                }
            </style>
            
            <div style="text-align: center;">
                <div style="
                    width: 100px;
                    height: 100px;
                    margin: 0 auto 1.5rem;
                    background: linear-gradient(135deg, #f97316 0%, #ea580c 100%);
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    box-shadow: 0 8px 16px rgba(249, 115, 22, 0.3);
                    animation: questionPulse 2s infinite;
                ">
                    <i class="fas fa-question" style="font-size: 3rem; color: white;"></i>
                </div>
                
                <h3 style="
                    font-size: 1.75rem;
                    font-weight: 700;
                    color: #1e293b;
                    margin-bottom: 1rem;
                ">
                    ${i18n.t('confirm.title')}
                </h3>
                
                <p style="
                    font-size: 1rem;
                    color: #64748b;
                    margin-bottom: 1.5rem;
                ">
                    ${i18n.t('confirm.subtitle')}
                </p>
                
                <div style="
                    background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
                    border-radius: 12px;
                    padding: 1.5rem;
                    margin-bottom: 1.5rem;
                    border: 2px solid #1BA5A8;
                    text-align: left;
                ">
                    <div class="confirm-detail">
                        <i class="fas fa-map-marker-alt"></i>
                        <span><strong>${i18n.t('confirm.location')}:</strong> ${locationName}</span>
                    </div>
                    ${roomInfo}
                    ${notesInfo}
                </div>
                
                <div style="display: flex; gap: 1rem;">
                    <button class="confirm-btn confirm-btn-no" id="cancel-btn">
                        <i class="fas fa-times"></i> ${i18n.t('btn.cancel')}
                    </button>
                    <button class="confirm-btn confirm-btn-yes" id="confirm-btn">
                        <i class="fas fa-check"></i> ${i18n.t('btn.confirm')}
                    </button>
                </div>
            </div>
        `;
        
        overlay.appendChild(modal);
        document.body.appendChild(overlay);
        
        // Manuel olarak çevir (MutationObserver innerHTML'i yakalamıyor)
        setTimeout(() => {
            if (window.guestI18n) {
                const i18nElements = modal.querySelectorAll('[data-i18n]');
                i18nElements.forEach(el => {
                    const key = el.getAttribute('data-i18n');
                    const translation = window.guestI18n.t(key);
                    el.textContent = translation;
                });
                console.log('[Guest] Confirmation modal translated:', i18nElements.length, 'elements');
            }
        }, 50);
        
        // Handle button clicks
        return new Promise((resolve) => {
            const confirmBtn = modal.querySelector('#confirm-btn');
            const cancelBtn = modal.querySelector('#cancel-btn');
            
            const cleanup = () => {
                overlay.style.animation = 'fadeOut 0.3s ease';
                setTimeout(() => {
                    if (overlay.parentNode) {
                        overlay.parentNode.removeChild(overlay);
                    }
                }, 300);
            };
            
            confirmBtn.onclick = () => {
                cleanup();
                this.submitRequest();
                resolve(true);
            };
            
            cancelBtn.onclick = () => {
                cleanup();
                resolve(false);
            };
            
            // Close on backdrop click
            overlay.onclick = (e) => {
                if (e.target === overlay) {
                    cleanup();
                    resolve(false);
                }
            };
        });
    },

    /**
     * Submit shuttle request
     */
    async submitRequest() {
        try {
            // Get location ID from global state or this object
            const locationId = window.state?.selectedLocationId || this.locationId;
            
            // Validation
            if (!locationId) {
                console.error('❌ Location ID bulunamadı');
                if (typeof showToast === 'function') {
                    showToast('Lütfen önce QR kod okutun', 'error');
                } else {
                    alert('Lütfen önce QR kod okutun');
                }
                return;
            }
            
            // Get room number from input
            const roomNumberInput = document.getElementById('room-number');
            const roomNumber = roomNumberInput?.value?.trim() || null;
            
            console.log('🚀 Submitting request:', { locationId, roomNumber });
            
            // Show loading
            if (typeof showLoadingOverlay === 'function') {
                showLoadingOverlay('Shuttle çağrılıyor...');
            }
            
            // Submit request
            const response = await fetch('/api/requests', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    location_id: locationId,
                    room_number: roomNumber
                })
            });
            
            const data = await response.json();
            
            // Hide loading
            if (typeof hideLoadingOverlay === 'function') {
                hideLoadingOverlay();
            }
            
            if (data.success && data.request) {
                this.requestId = data.request.id;
                
                console.log('✅ Request created:', this.requestId);
                
                // Trigger request-created event for notification system
                const requestCreatedEvent = new CustomEvent('request-created', {
                    detail: { requestId: this.requestId }
                });
                window.dispatchEvent(requestCreatedEvent);
                
                // Show success toast
                if (typeof showToast === 'function') {
                    showToast('Talebiniz oluşturuldu! Yönlendiriliyorsunuz...', 'success');
                }
                
                // Redirect to status page
                setTimeout(() => {
                    window.location.href = `/guest/status/${this.requestId}`;
                }, 500);
            } else {
                console.error('❌ Request failed:', data);
                if (typeof showToast === 'function') {
                    showToast(data.error || 'Talep oluşturulamadı', 'error');
                } else {
                    alert(data.error || 'Talep oluşturulamadı');
                }
            }
        } catch (error) {
            console.error('❌ Request submission error:', error);
            
            // Hide loading
            if (typeof hideLoadingOverlay === 'function') {
                hideLoadingOverlay();
            }
            
            if (typeof showToast === 'function') {
                showToast('Bağlantı hatası. Lütfen tekrar deneyin.', 'error');
            } else {
                alert('Bağlantı hatası. Lütfen tekrar deneyin.');
            }
        }
    },

    /**
     * Show themed request success notification
     */
    showRequestSuccessNotification() {
        // Get translations
        const i18n = window.guestI18n || { t: (key) => key };
        
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
                @keyframes successPulse {
                    0%, 100% {
                        transform: scale(1);
                        box-shadow: 0 8px 16px rgba(16, 185, 129, 0.3);
                    }
                    50% {
                        transform: scale(1.05);
                        box-shadow: 0 12px 24px rgba(16, 185, 129, 0.4);
                    }
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
                    animation: successPulse 2s infinite;
                ">
                    <i class="fas fa-check" style="font-size: 3.5rem; color: white;"></i>
                </div>
                
                <h3 style="
                    font-size: 1.75rem;
                    font-weight: 700;
                    color: #1e293b;
                    margin-bottom: 1rem;
                ">
                    ${i18n.t('notif.request_received')}
                </h3>
                
                <p style="
                    font-size: 1.1rem;
                    color: #64748b;
                    line-height: 1.6;
                    margin-bottom: 1.5rem;
                ">
                    ${i18n.t('notif.request_received_msg')}
                </p>
                
                <div style="
                    background: #fef3c7;
                    border-left: 4px solid #f59e0b;
                    padding: 1rem 1.25rem;
                    border-radius: 8px;
                    margin-top: 1.5rem;
                ">
                    <p style="
                        margin: 0;
                        color: #92400e;
                        font-size: 1rem;
                        font-weight: 600;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        gap: 0.5rem;
                    ">
                        <i class="fas fa-exclamation-triangle"></i>
                        ${i18n.t('notif.do_not_close')}
                    </p>
                </div>
            </div>
        `;
        
        overlay.appendChild(modal);
        document.body.appendChild(overlay);
        
        // Manuel olarak çevir (MutationObserver innerHTML'i yakalamıyor)
        setTimeout(() => {
            if (window.guestI18n) {
                const i18nElements = modal.querySelectorAll('[data-i18n]');
                i18nElements.forEach(el => {
                    const key = el.getAttribute('data-i18n');
                    const translation = window.guestI18n.t(key);
                    el.textContent = translation;
                });
                console.log('[Guest] Success modal translated:', i18nElements.length, 'elements');
            }
        }, 50);
        
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
     * Setup status tracking
     */
    setupStatusTracking() {
        // Listen to request accepted
        this.socket.on('request_accepted', (data) => {
            if (data.request_id === this.requestId) {
                console.log('Request accepted:', data);
                this.updateStatus('accepted', data);
            }
        });
        
        // Listen to request completed
        this.socket.on('request_completed', (data) => {
            if (data.request_id === this.requestId) {
                console.log('Request completed:', data);
                this.updateStatus('completed', data);
            }
        });
        
        // Listen to request cancelled
        this.socket.on('request_cancelled', (data) => {
            if (data.request_id === this.requestId) {
                console.log('Request cancelled:', data);
                this.updateStatus('cancelled', data);
            }
        });
        
        // Start status polling as backup
        this.startStatusPolling();
    },

    /**
     * Start status polling (backup for WebSocket)
     */
    startStatusPolling() {
        if (this.statusPollInterval) {
            clearInterval(this.statusPollInterval);
        }
        
        this.statusPollInterval = setInterval(async () => {
            if (!this.requestId) {
                clearInterval(this.statusPollInterval);
                return;
            }
            
            try {
                const response = await BuggyCall.API.get(`/requests/${this.requestId}`);
                const request = response.request;
                
                // Update UI if status changed
                this.updateStatusUI(request);
                
                // Stop polling if completed or cancelled
                if (['completed', 'cancelled'].includes(request.status)) {
                    clearInterval(this.statusPollInterval);
                }
            } catch (error) {
                console.error('Status polling error:', error);
            }
        }, 10000); // Poll every 10 seconds
    },

    /**
     * Update status
     */
    updateStatus(status, data) {
        BuggyCall.Utils.showToast(this.getStatusMessage(status), 'info');
        
        // Play notification sound for accepted status
        if (status === 'accepted') {
            this.playAcceptedNotificationSound();
            this.showAcceptedNotification(data);
        }
        
        // Update progress indicator
        this.updateStatusUI({ status, ...data });
        
        // Stop polling if completed
        if (['completed', 'cancelled'].includes(status)) {
            if (this.statusPollInterval) {
                clearInterval(this.statusPollInterval);
            }
        }
    },

    /**
     * Play notification sound when request is accepted
     */
    playAcceptedNotificationSound() {
        try {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            
            // Play success melody (C-E-G chord)
            const frequencies = [523.25, 659.25, 783.99]; // C, E, G
            
            frequencies.forEach((freq, index) => {
                setTimeout(() => {
                    const oscillator = audioContext.createOscillator();
                    const gainNode = audioContext.createGain();
                    
                    oscillator.connect(gainNode);
                    gainNode.connect(audioContext.destination);
                    
                    oscillator.frequency.value = freq;
                    oscillator.type = 'sine';
                    
                    gainNode.gain.setValueAtTime(0, audioContext.currentTime);
                    gainNode.gain.linearRampToValueAtTime(0.3, audioContext.currentTime + 0.01);
                    gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.4);
                    
                    oscillator.start(audioContext.currentTime);
                    oscillator.stop(audioContext.currentTime + 0.4);
                }, index * 150);
            });
            
            // Vibrate if supported
            if (window.navigator && window.navigator.vibrate) {
                window.navigator.vibrate([200, 100, 200, 100, 200]);
            }
        } catch (error) {
            console.error('Error playing notification sound:', error);
        }
    },

    /**
     * Show accepted notification
     */
    showAcceptedNotification(data) {
        const shuttleCode = data.buggy?.code || 'Shuttle';
        const driverName = data.driver?.full_name || data.driver?.name || '';
        
        // Show browser notification if permitted
        if ('Notification' in window && Notification.permission === 'granted') {
            new Notification('🎉 Shuttle Kabul Edildi!', {
                body: `${shuttleCode} size doğru geliyor${driverName ? `\nSürücü: ${driverName}` : ''}`,
                icon: '/static/icons/icon-192x192.png',
                badge: '/static/icons/icon-96x96.png',
                vibrate: [200, 100, 200, 100, 200]
            });
        } else if ('Notification' in window && Notification.permission === 'default') {
            // İzin verilmemişse uyarı göster
            this.showNotificationPermissionPrompt();
        }
    },

    /**
     * Bildirim izni isteme prompt'u göster
     */
    showNotificationPermissionPrompt() {
        const i18n = window.guestI18n || { t: (key) => key };
        
        // Zaten gösteriliyorsa tekrar gösterme
        if (document.querySelector('.notification-permission-prompt')) {
            return;
        }
        
        const prompt = document.createElement('div');
        prompt.className = 'notification-permission-prompt';
        prompt.style.cssText = `
            position: fixed;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            max-width: 500px;
            width: calc(100% - 40px);
            background: white;
            border-radius: 16px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
            padding: 20px;
            z-index: 9999;
            animation: slideUpFade 0.4s ease-out;
        `;
        
        prompt.innerHTML = `
            <style>
                @keyframes slideUpFade {
                    from {
                        transform: translate(-50%, 100px);
                        opacity: 0;
                    }
                    to {
                        transform: translate(-50%, 0);
                        opacity: 1;
                    }
                }
            </style>
            <div style="display: flex; align-items: start; gap: 16px;">
                <div style="
                    width: 48px;
                    height: 48px;
                    background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
                    border-radius: 12px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    flex-shrink: 0;
                ">
                    <i class="fas fa-bell" style="color: white; font-size: 24px;"></i>
                </div>
                <div style="flex: 1;">
                    <h3 style="
                        font-size: 16px;
                        font-weight: 700;
                        color: #1e293b;
                        margin: 0 0 8px 0;
                    ">${i18n.t('notif.permission_denied')}</h3>
                    <p style="
                        font-size: 14px;
                        color: #64748b;
                        margin: 0 0 16px 0;
                        line-height: 1.5;
                    ">${i18n.t('notif.permission_denied_msg')}</p>
                    <div style="display: flex; gap: 12px;">
                        <button onclick="Guest.requestNotificationPermission()" style="
                            flex: 1;
                            padding: 12px 20px;
                            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
                            color: white;
                            border: none;
                            border-radius: 10px;
                            font-size: 14px;
                            font-weight: 600;
                            cursor: pointer;
                            transition: transform 0.2s;
                        " onmouseover="this.style.transform='translateY(-2px)'" onmouseout="this.style.transform='translateY(0)'">
                            <i class="fas fa-check"></i> ${i18n.t('btn.enable_notifications')}
                        </button>
                        <button onclick="this.closest('.notification-permission-prompt').remove()" style="
                            padding: 12px 20px;
                            background: #e2e8f0;
                            color: #64748b;
                            border: none;
                            border-radius: 10px;
                            font-size: 14px;
                            font-weight: 600;
                            cursor: pointer;
                            transition: background 0.2s;
                        " onmouseover="this.style.background='#cbd5e1'" onmouseout="this.style.background='#e2e8f0'">
                            ${i18n.t('btn.close')}
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(prompt);
        
        // 10 saniye sonra otomatik kapat
        setTimeout(() => {
            if (prompt.parentNode) {
                prompt.style.animation = 'slideUpFade 0.3s ease-in reverse';
                setTimeout(() => prompt.remove(), 300);
            }
        }, 10000);
    },

    /**
     * Bildirim izni iste
     */
    async requestNotificationPermission() {
        try {
            // Prompt'u kapat
            const prompt = document.querySelector('.notification-permission-prompt');
            if (prompt) {
                prompt.remove();
            }
            
            // iOS kontrolü
            if (window.iosNotificationHandler && window.iosNotificationHandler.isIOSDevice()) {
                const permission = await window.iosNotificationHandler.requestPermission();
                if (permission === 'granted') {
                    BuggyCall.Utils.showSuccess('Bildirimler aktif edildi! 🔔');
                }
            } else {
                // Normal tarayıcılar
                const permission = await Notification.requestPermission();
                if (permission === 'granted') {
                    BuggyCall.Utils.showSuccess('Bildirimler aktif edildi! 🔔');
                    
                    // Guest notification manager varsa token al
                    if (window.guestNotificationManager && this.requestId) {
                        await window.guestNotificationManager.requestPermissionAndGetToken(this.requestId);
                    }
                } else {
                    BuggyCall.Utils.showWarning('Bildirim izni reddedildi');
                }
            }
        } catch (error) {
            console.error('Notification permission error:', error);
            BuggyCall.Utils.showError('Bildirim izni alınamadı');
        }
    },

    /**
     * Update status UI
     */
    updateStatusUI(request) {
        const statusBadge = document.getElementById('request-status-badge');
        const statusText = document.getElementById('request-status-text');
        const progressBar = document.getElementById('status-progress');
        const driverInfo = document.getElementById('driver-info');
        const etaInfo = document.getElementById('eta-info');
        
        if (statusBadge) {
            statusBadge.className = `badge ${BuggyCall.Utils.getBadgeClass(request.status)}`;
            statusBadge.textContent = this.getStatusText(request.status);
        }
        
        if (statusText) {
            statusText.textContent = this.getStatusMessage(request.status);
        }
        
        if (progressBar) {
            const progressMap = {
                'PENDING': 33,
                'accepted': 66,
                'completed': 100,
                'cancelled': 0
            };
            const progress = progressMap[request.status] || 0;
            progressBar.style.width = progress + '%';
            progressBar.setAttribute('aria-valuenow', progress);
        }
        
        // Show driver info if accepted
        if (driverInfo && request.status === 'accepted' && request.buggy) {
            driverInfo.innerHTML = `
                <div class="alert alert-info">
                    <i class="fas fa-golf-ball"></i>
                    <strong>Shuttle:</strong> ${request.buggy.code || 'N/A'}
                    ${request.driver ? `<br><i class="fas fa-user"></i> <strong>Sürücü:</strong> ${request.driver.name}` : ''}
                </div>
            `;
            driverInfo.classList.remove('d-none');
        }
        
        // Show ETA if available
        if (etaInfo && request.response_time) {
            const responseTime = Math.round(request.response_time / 60);
            etaInfo.innerHTML = `
                <div class="alert alert-success">
                    <i class="fas fa-clock"></i>
                    <strong>Yanıt Süresi:</strong> ${responseTime} dakika
                </div>
            `;
            etaInfo.classList.remove('d-none');
        }
    },

    /**
     * Show status view
     */
    showStatusView() {
        const callView = document.getElementById('call-view');
        const statusView = document.getElementById('status-view');
        
        if (callView) callView.classList.add('d-none');
        if (statusView) statusView.classList.remove('d-none');
    },

    /**
     * Get status message
     */
    getStatusMessage(status) {
        const i18n = window.guestI18n || { t: (key) => key };
        const messages = {
            'PENDING': i18n.t('status.pending_msg'),
            'accepted': i18n.t('status.accepted_msg'),
            'in_progress': i18n.t('status.in_progress_msg'),
            'completed': i18n.t('status.completed_msg'),
            'cancelled': i18n.t('status.cancelled_msg')
        };
        return messages[status] || 'Durum güncelleniyor...';
    },

    /**
     * Get status text
     */
    getStatusText(status) {
        const i18n = window.guestI18n || { t: (key) => key };
        const statusMap = {
            'PENDING': i18n.t('status.pending'),
            'accepted': i18n.t('status.accepted'),
            'in_progress': i18n.t('status.in_progress'),
            'completed': i18n.t('status.completed'),
            'cancelled': i18n.t('status.cancelled')
        };
        return statusMap[status] || status;
    }
};

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => Guest.init());
} else {
    Guest.init();
}

// Export to global scope
window.Guest = Guest;
