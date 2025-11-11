// Admin Dashboard JavaScript

// Status badge mapping
const statusBadges = {
    'PENDING': '<span class="badge badge-warning">Bekliyor</span>',
    'assigned': '<span class="badge badge-info">Atandı</span>',
    'in_progress': '<span class="badge badge-primary">Yolda</span>',
    'completed': '<span class="badge badge-success">Tamamlandı</span>',
    'cancelled': '<span class="badge badge-danger">İptal</span>'
};

const buggyStatusBadges = {
    'available': '<span class="badge badge-success">Müsait</span>',
    'busy': '<span class="badge badge-warning">Meşgul</span>',
    'offline': '<span class="badge badge-secondary">Çevrimdışı</span>'
};

// Stats removed - no longer needed

async function loadActiveRequests() {
    try {
        const response = await fetch('/api/requests');
        const data = await response.json();
        
        console.log('Requests API response:', data);
        
        const requestsList = document.getElementById('requestsList');
        const requestsCount = document.getElementById('requestsCount');
        
        // Parse requests from different response formats
        let requests = [];
        if (data.requests) {
            requests = data.requests;
        } else if (data.data && data.data.requests) {
            requests = data.data.requests;
        }
        
        // Filter active requests (PENDING or accepted)
        const activeRequests = requests.filter(req => 
            req.status === 'PENDING' || req.status === 'accepted'
        );
        
        console.log('Active requests:', activeRequests);
        
        if (activeRequests && activeRequests.length > 0) {
            requestsCount.textContent = activeRequests.length;
            requestsList.innerHTML = activeRequests.map(req => `
                <tr style="cursor: pointer;" onclick="showRequestDetails(${req.id})">
                    <td>
                        <strong>${req.guest_name || 'Misafir'}</strong><br>
                        <small style="color: #6B7280;">Oda: ${req.room_number || '-'}</small>
                    </td>
                    <td>${req.location ? req.location.name : 'Bilinmiyor'}</td>
                    <td>${statusBadges[req.status] || req.status}</td>
                    <td>${req.driver ? req.driver.full_name : '<span class="badge badge-secondary">Atanmadı</span>'}</td>
                </tr>
            `).join('');
        } else {
            requestsCount.textContent = '0';
            requestsList.innerHTML = '<tr><td colspan="4" style="text-align: center; color: #6B7280; padding: 2rem;">Aktif çağrı yok</td></tr>';
        }
    } catch (error) {
        console.error('Failed to load requests:', error);
        document.getElementById('requestsList').innerHTML = '<tr><td colspan="4" style="text-align: center; color: #E74C3C;">Yüklenemedi</td></tr>';
    }
}

// Show request details in modal
async function showRequestDetails(requestId) {
    try {
        const response = await fetch(`/api/requests/${requestId}`);
        const data = await response.json();
        const req = data.request;
        
        if (!req) {
            alert('Talep bulunamadı');
            return;
        }
        
        const detailsHtml = `
            <div style="text-align: left;">
                <h3 style="color: #1BA5A8; margin-bottom: 1rem;">Talep Detayları</h3>
                <div style="background: #F9FAFB; padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">
                    <p><strong>Misafir:</strong> ${req.guest_name || '-'}</p>
                    <p><strong>Oda No:</strong> ${req.room_number || '-'}</p>
                    <p><strong>Telefon:</strong> ${req.phone || '-'}</p>
                    <p><strong>Lokasyon:</strong> ${req.location ? req.location.name : '-'}</p>
                    <p><strong>Durum:</strong> ${statusBadges[req.status] || req.status}</p>
                    <p><strong>Talep Zamanı:</strong> ${new Date(req.requested_at).toLocaleString('tr-TR')}</p>
                    ${req.driver ? `<p><strong>Sürücü:</strong> ${req.driver.full_name}</p>` : ''}
                    ${req.buggy ? `<p><strong>Shuttle:</strong> ${req.buggy.code}</p>` : ''}
                    ${req.notes ? `<p><strong>Notlar:</strong> ${req.notes}</p>` : ''}
                </div>
            </div>
        `;
        
        // You'll need to implement BuggyModal or use alert for now
        if (typeof BuggyModal !== 'undefined') {
            await BuggyModal.custom(detailsHtml, {
                title: 'Talep Detayları',
                confirmText: 'Kapat',
                showCancel: false
            });
        } else {
            alert('Talep ID: ' + requestId);
        }
    } catch (error) {
        console.error('Failed to load request details:', error);
        alert('Talep detayları yüklenemedi');
    }
}

async function loadBuggiesStatus() {
    try {
        console.log('📡 [ADMIN] Fetching buggies from API...');
        const response = await fetch('/api/buggies');
        const data = await response.json();
        console.log('📊 [ADMIN] Buggies data received:', data);
        
        const buggiesList = document.getElementById('buggiesList');
        const availableCount = document.getElementById('availableBuggiesCount');
        
        if (data.buggies && data.buggies.length > 0) {
            const available = data.buggies.filter(b => b.status === 'available').length;
            console.log(`✅ [ADMIN] Found ${data.buggies.length} buggies, ${available} available`);
            availableCount.textContent = available;
            
            buggiesList.innerHTML = data.buggies.map(buggy => `
                <tr>
                    <td><strong>${buggy.code || buggy.license_plate}</strong><br><small>${buggy.license_plate || ''}</small></td>
                    <td>${buggy.driver_name || '<span class="badge badge-secondary">Atanmadı</span>'}</td>
                    <td>${buggy.current_location?.name || buggy.current_location_name || '<span class="badge badge-secondary">-</span>'}</td>
                    <td>${buggyStatusBadges[buggy.status] || buggy.status}</td>
                </tr>
            `).join('');
        } else {
            availableCount.textContent = '0';
            buggiesList.innerHTML = '<tr><td colspan="4" style="text-align: center; color: #6B7280;">Buggy yok</td></tr>';
        }
    } catch (error) {
        console.error('Failed to load buggies:', error);
        document.getElementById('buggiesList').innerHTML = '<tr><td colspan="4" style="text-align: center; color: #E74C3C;">Yüklenemedi</td></tr>';
    }
}

// Locations status removed - no longer needed

// WebSocket connection for real-time updates
let socket = null;

function initWebSocket() {
    // Check if Socket.IO is available
    if (typeof io === 'undefined') {
        console.warn('Socket.IO not loaded, using polling instead');
        return;
    }
    
    try {
        socket = io();
        
        socket.on('connect', () => {
            console.log('✅ Admin WebSocket connected - SID:', socket.id);
            // Join hotel admin room
            const hotelId = document.body.dataset.hotelId || 1;
            console.log('📡 Admin joining hotel room:', hotelId);
            socket.emit('join_hotel', { 
                hotel_id: parseInt(hotelId),
                role: 'admin'
            });
        });
        
        socket.on('joined_hotel', (data) => {
            console.log('✅ Admin successfully joined hotel room:', data);
        });
        
        socket.on('disconnect', () => {
            console.log('WebSocket disconnected');
        });
        
        // Listen for new requests
        socket.on('new_request', (data) => {
            console.log('🎉 ADMIN - NEW REQUEST RECEIVED:', data);
            console.log('   Request ID:', data.request_id);
            console.log('   Location:', data.location?.name);
            
            // Show browser notification
            showNotification('Yeni Shuttle Talebi!', {
                body: `${data.location?.name || 'Lokasyon'} - ${data.guest_name || 'Misafir'}`,
                icon: '/static/images/logo.png',
                tag: 'new-request-' + data.request_id
            });
            
            // Play notification sound
            playNotificationSound();
            
            // Reload requests list
            loadActiveRequests();
        });
        
        // Listen for request updates
        socket.on('request_accepted', (data) => {
            console.log('Request accepted:', data);
            loadActiveRequests();
        });
        
        socket.on('request_completed', (data) => {
            console.log('Request completed:', data);
            loadActiveRequests();
        });
        
        // Listen for buggy status changes (CRITICAL for logout/disconnect)
        socket.on('buggy_status_changed', (data) => {
            console.log('🔔 [ADMIN] Buggy status changed event received:', data);
            console.log('🔄 [ADMIN] Reloading buggies list...');
            // Reload buggies list to reflect new status
            loadBuggiesStatus();
        });
        
        // Listen for driver location updates
        socket.on('driver_location_updated', (data) => {
            console.log('Driver location updated:', data);
            // Reload buggies list to reflect new location
            loadBuggiesStatus();
        });
        
    } catch (error) {
        console.error('WebSocket initialization failed:', error);
    }
}

// Show browser notification
function showNotification(title, options) {
    // Check if browser supports notifications
    if (!('Notification' in window)) {
        console.warn('Browser does not support notifications');
        return;
    }
    
    // Check permission
    if (Notification.permission === 'granted') {
        new Notification(title, options);
    } else if (Notification.permission !== 'denied') {
        Notification.requestPermission().then(permission => {
            if (permission === 'granted') {
                new Notification(title, options);
            }
        });
    }
}

// Play notification sound
function playNotificationSound() {
    try {
        // Create a simple beep sound using Web Audio API
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);
        
        oscillator.frequency.value = 800; // Frequency in Hz
        oscillator.type = 'sine';
        
        gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
        
        oscillator.start(audioContext.currentTime);
        oscillator.stop(audioContext.currentTime + 0.5);
    } catch (error) {
        console.warn('Notification sound failed:', error);
    }
}

// Request notification permission (must be called from user gesture)
function requestNotificationPermission() {
    if ('Notification' in window && Notification.permission === 'default') {
        // Note: This must be called from a user gesture (click, touch, etc.)
        // Edge/Chrome will block if called without user interaction
        Notification.requestPermission().then(permission => {
            console.log('[Dashboard] Notification permission:', permission);
        }).catch(error => {
            console.error('[Dashboard] Permission request failed:', error);
        });
    }
}

// Load all data on page load
function loadAllData() {
    loadActiveRequests();
    loadBuggiesStatus();
}

// Initial load
loadAllData();
initWebSocket();
requestNotificationPermission();

// Refresh every 30 seconds (WebSocket handles real-time updates)
setInterval(loadAllData, 30000);
