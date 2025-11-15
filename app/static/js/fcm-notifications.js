/**
 * Firebase Cloud Messaging (FCM) - Push Notifications
 * Buggy Call - Sürücü Bildirim Sistemi
 * Powered by Erkan ERDEM
 */

class FCMNotificationManager {
    constructor() {
        this.messaging = null;
        this.currentToken = null;
        this.isSupported = false;

        // ✅ FCM CONFIG SIMPLIFY: Use global config from firebase-config.js
        this.firebaseConfig = window.firebaseConfig || {
            // Fallback if firebase-config.js not loaded
            apiKey: "AIzaSyD5brCkHqSPVCtt0XJmUMqZizrjK_HX9dc",
            authDomain: "shuttle-call-835d9.firebaseapp.com",
            projectId: "shuttle-call-835d9",
            storageBucket: "shuttle-call-835d9.firebasestorage.app",
            messagingSenderId: "1044072191950",
            appId: "1:1044072191950:web:dc780e1832d3a4ee5afd9f",
            measurementId: "G-DCP7FTRM9Q",
            vapidKey: "BBrNGl2-VPA-iuLasrj8jpS2Sj2FrYr-FQq57GET6ofRV4QOljRwyLg--HMI-bV7m-lmdBk5NJxSyy3nVpNLzA4"
        };
    }
    
    /**
     * FCM'i başlat (iOS kontrolü ile)
     */
    async initialize() {
        try {
            // iOS kontrolü
            if (window.iosNotificationHandler && window.iosNotificationHandler.isIOSDevice()) {
                const iosStatus = window.iosNotificationHandler.getStatus();
                console.log('📱 iOS Device Detected:', iosStatus);

                // iOS 16.4 altı - FCM desteklenmiyor
                if (!iosStatus.webPushSupported) {
                    console.warn('⚠️ iOS version does not support Web Push:', iosStatus.version);
                    this.isSupported = false;
                    return false;
                }

                // PWA modunda değil - FCM çalışmaz
                if (!iosStatus.isPWA) {
                    console.warn('⚠️ iOS requires PWA mode for FCM');
                    this.isSupported = false;
                    return false;
                }

                console.log('✅ iOS PWA mode - FCM supported');
            }

            // Firebase SDK kontrolü
            if (typeof firebase === 'undefined') {
                console.error('❌ Firebase SDK yüklenmemiş');
                return false;
            }
            
            // Messaging desteği kontrolü
            if (!firebase.messaging.isSupported()) {
                console.warn('⚠️ Bu tarayıcı FCM desteklemiyor');
                this.isSupported = false;
                return false;
            }
            
            this.isSupported = true;
            
            // Firebase'i başlat
            if (!firebase.apps.length) {
                firebase.initializeApp(this.firebaseConfig);
            }
            
            this.messaging = firebase.messaging();
            console.log('✅ FCM başlatıldı');
            
            // Foreground mesajları dinle
            this.setupForegroundListener();
            
            return true;
            
        } catch (error) {
            console.error('❌ FCM başlatma hatası:', error);
            return false;
        }
    }
    
    /**
     * Bildirim izni iste ve token al (iOS kontrolü ile)
     */
    async requestPermissionAndGetToken() {
        try {
            // iOS kontrolü
            if (window.iosNotificationHandler && window.iosNotificationHandler.isIOSDevice()) {
                const iosStatus = window.iosNotificationHandler.getStatus();
                
                // iOS desteklemiyor
                if (!iosStatus.notificationSupported) {
                    console.warn('⚠️ iOS notifications not supported:', iosStatus.message);
                    return null;
                }
                
                console.log('✅ iOS notifications supported, proceeding...');
            }

            // Önce mevcut izin durumunu kontrol et
            if (Notification.permission === 'denied') {
                console.warn('⚠️ Bildirim izni kalıcı olarak reddedilmiş');
                alert('⚠️ Bildirim izni engellenmiş!\n\nBildirimleri etkinleştirmek için:\n1. Adres çubuğundaki 🔒 simgesine tıklayın\n2. "Site ayarları" seçeneğine tıklayın\n3. "Bildirimler" bölümünde "İzin ver" seçeneğini işaretleyin\n4. Sayfayı yenileyin');
                return null;
            }
            
            // Bildirim izni iste
            let permission;
            if (window.iosNotificationHandler && window.iosNotificationHandler.isIOSDevice()) {
                // iOS için özel handler kullan
                permission = await window.iosNotificationHandler.requestPermission();
            } else {
                // Normal akış
                permission = await Notification.requestPermission();
            }
            
            if (permission !== 'granted') {
                console.warn('⚠️ Bildirim izni reddedildi');
                this.showPermissionDeniedMessage();
                return null;
            }
            
            console.log('✅ Bildirim izni verildi');
            
            // Service Worker kaydı
            const registration = await this.registerServiceWorker();
            
            if (!registration) {
                console.error('❌ Service Worker kaydedilemedi');
                return null;
            }
            
            // FCM token al
            const token = await this.messaging.getToken({
                vapidKey: this.firebaseConfig.vapidKey,
                serviceWorkerRegistration: registration
            });
            
            if (token) {
                console.log('✅ FCM Token alındı:', token.substring(0, 20) + '...');
                this.currentToken = token;
                
                // Token'ı backend'e kaydet
                await this.registerTokenToBackend(token);
                
                return token;
            } else {
                console.warn('⚠️ Token alınamadı');
                return null;
            }
            
        } catch (error) {
            console.error('❌ Token alma hatası:', error);
            
            // iOS için özel hata mesajı
            if (window.iosNotificationHandler && window.iosNotificationHandler.isIOSDevice()) {
                console.error('❌ iOS FCM Error:', error);
                const iosStatus = window.iosNotificationHandler.getStatus();
                console.log('📱 iOS Status:', iosStatus);
            }
            
            return null;
        }
    }
    
    /**
     * Service Worker kaydet
     */
    async registerServiceWorker() {
        try {
            if (!('serviceWorker' in navigator)) {
                console.error('❌ Service Worker desteklenmiyor');
                return null;
            }
            
            // Firebase Messaging Service Worker'ı kaydet
            const registration = await navigator.serviceWorker.register(
                '/firebase-messaging-sw.js'
                // Scope belirtme, default scope kullan
            );
            
            console.log('✅ Service Worker kaydedildi');
            
            // Service Worker'ın hazır olmasını bekle
            await navigator.serviceWorker.ready;
            
            return registration;
            
        } catch (error) {
            console.error('❌ Service Worker kayıt hatası:', error);
            return null;
        }
    }
    
    /**
     * Token'ı backend'e kaydet
     */
    async registerTokenToBackend(token) {
        try {
            const response = await fetch('/api/fcm/register-token', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ token: token })
            });
            
            const data = await response.json();
            
            if (data.success) {
                console.log('✅ Token backend\'e kaydedildi');
                
                // Local storage'a kaydet
                localStorage.setItem('fcm_token', token);
                localStorage.setItem('fcm_token_date', new Date().toISOString());
                
                return true;
            } else {
                console.error('❌ Token kayıt hatası:', data.message);
                return false;
            }
            
        } catch (error) {
            console.error('❌ Backend kayıt hatası:', error);
            return false;
        }
    }
    
    /**
     * Foreground mesajları dinle (uygulama açıkken)
     */
    setupForegroundListener() {
        if (!this.messaging) return;
        
        this.messaging.onMessage((payload) => {
            console.log('📨 Foreground mesaj alındı:', payload);
            
            // Bildirim göster
            this.showForegroundNotification(payload);
            
            // Özel event tetikle (dashboard güncellemesi için)
            const event = new CustomEvent('fcm-message', { detail: payload });
            window.dispatchEvent(event);
        });
        
        // Token refresh artık otomatik - manuel kontrol için periyodik check
        this.startTokenRefreshCheck();
    }
    
    /**
     * Token'ı periyodik olarak kontrol et ve gerekirse yenile
     */
    startTokenRefreshCheck() {
        // Her 24 saatte bir token'ı kontrol et
        setInterval(async () => {
            try {
                console.log('🔄 FCM token kontrolü yapılıyor...');
                
                const registration = await navigator.serviceWorker.ready;
                const newToken = await this.messaging.getToken({
                    vapidKey: this.firebaseConfig.vapidKey,
                    serviceWorkerRegistration: registration
                });
                
                // Token değiştiyse güncelle
                if (newToken && newToken !== this.currentToken) {
                    console.log('✅ Token değişti, güncelleniyor...');
                    const oldToken = this.currentToken;
                    this.currentToken = newToken;
                    await this.refreshTokenOnBackend(oldToken, newToken);
                }
            } catch (error) {
                console.error('❌ Token kontrol hatası:', error);
            }
        }, 24 * 60 * 60 * 1000); // 24 saat
    }
    
    /**
     * Token'ı backend'de yenile
     */
    async refreshTokenOnBackend(oldToken, newToken) {
        try {
            const response = await fetch('/api/fcm/refresh-token', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ 
                    old_token: oldToken,
                    new_token: newToken 
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                console.log('✅ Token backend\'de yenilendi');
                localStorage.setItem('fcm_token', newToken);
                localStorage.setItem('fcm_token_date', new Date().toISOString());
                return true;
            } else {
                console.error('❌ Token yenileme hatası:', data.message);
                return false;
            }
            
        } catch (error) {
            console.error('❌ Backend token yenileme hatası:', error);
            return false;
        }
    }
    
    /**
     * Foreground bildirim göster
     */
    showForegroundNotification(payload) {
        const title = payload.notification?.title || 'Buggy Call';
        const options = {
            body: payload.notification?.body || 'Yeni bildirim',
            icon: payload.notification?.icon || '/static/icons/Icon-192.png',
            badge: '/static/icons/Icon-96.png',
            tag: payload.data?.type || 'notification',
            data: payload.data || {},
            requireInteraction: payload.data?.priority === 'high',
            vibrate: [200, 100, 200]
        };
        
        // Tarayıcı bildirimi göster
        if (Notification.permission === 'granted') {
            new Notification(title, options);
        }
        
        // Ses çal (yeni talep için)
        if (payload.data?.type === 'new_request') {
            this.playNotificationSound();
        }
    }
    
    /**
     * Bildirim sesi çal
     */
    playNotificationSound() {
        try {
            const audio = new Audio('/static/sounds/notification.mp3');
            audio.volume = 0.5;
            audio.play().catch(err => {
                console.warn('⚠️ Ses çalınamadı:', err);
            });
        } catch (error) {
            console.warn('⚠️ Ses hatası:', error);
        }
    }
    
    /**
     * İzin reddedildi mesajı
     */
    showPermissionDeniedMessage() {
        // Eğer mesaj zaten varsa tekrar ekleme
        if (document.getElementById('fcm-permission-alert')) {
            console.log('⚠️ İzin mesajı zaten gösteriliyor');
            return;
        }
        
        const message = `
            <div class="alert alert-warning" id="fcm-permission-alert" style="margin: 20px; padding: 20px; background: #fff3cd; border: 1px solid #ffc107; border-radius: 8px;">
                <strong style="display: block; margin-bottom: 10px;">⚠️ Bildirim İzni Gerekli</strong>
                <p style="margin-bottom: 15px;">Yeni talepleri anında almak için bildirim iznini açmanız gerekiyor.</p>
                <button id="fcm-request-permission-btn" style="
                    background: #1BA5A8;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 6px;
                    cursor: pointer;
                    font-size: 14px;
                    font-weight: 600;
                    margin-right: 10px;
                ">
                    🔔 İzin Ver
                </button>
                <small style="color: #666; display: block; margin-top: 10px;">
                    <strong>Not:</strong> Eğer tarayıcı izin penceresi açılmazsa, adres çubuğundaki 🔒 simgesine tıklayıp "Site ayarları" → "Bildirimler" → "İzin ver" seçeneğini işaretleyin.
                </small>
            </div>
        `;
        
        // Dashboard'a mesaj ekle
        const container = document.querySelector('.dashboard-container') || document.body;
        const div = document.createElement('div');
        div.innerHTML = message;
        container.insertBefore(div, container.firstChild);
        
        // Butona tıklama eventi ekle
        const button = document.getElementById('fcm-request-permission-btn');
        if (button) {
            button.addEventListener('click', async () => {
                button.disabled = true;
                button.textContent = '⏳ İzin isteniyor...';
                
                try {
                    const token = await this.requestPermissionAndGetToken();
                    
                    if (token) {
                        // Başarılı - Mesajı kaldır
                        const alert = document.getElementById('fcm-permission-alert');
                        if (alert) {
                            alert.style.background = '#d4edda';
                            alert.style.borderColor = '#28a745';
                            alert.innerHTML = `
                                <strong style="color: #155724;">✅ Bildirimler Etkinleştirildi!</strong>
                                <p style="color: #155724; margin-top: 10px;">Artık yeni talepleri anında alacaksınız.</p>
                            `;
                            
                            // 3 saniye sonra kaldır
                            setTimeout(() => {
                                alert.remove();
                            }, 3000);
                        }
                    } else {
                        // Başarısız
                        button.disabled = false;
                        button.textContent = '🔔 Tekrar Dene';
                        button.style.background = '#dc3545';
                    }
                } catch (error) {
                    console.error('❌ İzin hatası:', error);
                    button.disabled = false;
                    button.textContent = '🔔 Tekrar Dene';
                    button.style.background = '#dc3545';
                }
            });
        }
    }
    
    /**
     * Test bildirimi gönder
     */
    async sendTestNotification() {
        try {
            const response = await fetch('/api/fcm/test-notification', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    title: '🧪 Test Bildirimi',
                    body: 'FCM sistemi çalışıyor!'
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                console.log('✅ Test bildirimi gönderildi');
                return true;
            } else {
                console.error('❌ Test bildirimi hatası:', data.message);
                return false;
            }
            
        } catch (error) {
            console.error('❌ Test hatası:', error);
            return false;
        }
    }
    
    /**
     * Token'ı yenile
     */
    async refreshToken() {
        try {
            // Mevcut token'ı sil
            if (this.currentToken) {
                await this.messaging.deleteToken(this.currentToken);
            }
            
            // Yeni token al
            const newToken = await this.requestPermissionAndGetToken();
            
            return newToken;
            
        } catch (error) {
            console.error('❌ Token yenileme hatası:', error);
            return null;
        }
    }
}

// Global instance
window.fcmManager = new FCMNotificationManager();

// Sayfa yüklendiğinde otomatik başlat (sadece driver sayfalarında)
document.addEventListener('DOMContentLoaded', async () => {
    // Sadece driver dashboard'da çalıştır
    if (window.location.pathname.includes('/driver')) {
        console.log('🚀 FCM Manager başlatılıyor...');
        
        const initialized = await window.fcmManager.initialize();
        
        if (initialized) {
            // Token al (eğer yoksa)
            const savedToken = localStorage.getItem('fcm_token');
            
            if (!savedToken) {
                console.log('📱 FCM token alınıyor...');
                await window.fcmManager.requestPermissionAndGetToken();
            } else {
                console.log('✅ Kayıtlı FCM token bulundu');
                window.fcmManager.currentToken = savedToken;
                
                // Backend'e sync et (token validation)
                console.log('🔄 Token backend ile senkronize ediliyor...');
                await window.fcmManager.registerTokenToBackend(savedToken);
            }
        }
    }
});

// FCM mesajlarını dinle ve dashboard'ı güncelle
window.addEventListener('fcm-message', (event) => {
    const payload = event.detail;
    
    console.log('📬 FCM mesajı alındı:', payload);
    
    // Yeni talep geldiğinde AJAX ile ekle
    if (payload.data?.type === 'new_request') {
        console.log('🆕 Yeni talep - AJAX ile ekleniyor...');
        
        // driverDashboard varsa handleNewRequest çağır
        if (window.driverDashboard && typeof window.driverDashboard.handleNewRequest === 'function') {
            const requestData = {
                request_id: parseInt(payload.data.request_id),
                guest_name: payload.data.guest_name || null,
                room_number: payload.data.room_number || null,
                phone_number: payload.data.phone || null,
                location: {
                    name: payload.data.location_name || 'Bilinmeyen Lokasyon'
                },
                requested_at: new Date().toISOString(),
                notes: payload.data.notes || null
            };
            
            window.driverDashboard.handleNewRequest(requestData);
            console.log('✅ Talep AJAX ile eklendi');
        } else {
            console.warn('⚠️ driverDashboard bulunamadı, sayfa yenileniyor...');
            setTimeout(() => window.location.reload(), 1000);
        }
    }
});

console.log('✅ FCM Notification Manager yüklendi');
