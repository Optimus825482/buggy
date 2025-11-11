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
        
        // Firebase Config (Firebase Console'dan alınmalı)
        this.firebaseConfig = {
            

            apiKey: "AIzaSyDyjVSgW8j4wY-wF0G9uUJpY_Iv-5uQx1I",
            authDomain: "buggy-call-a5785.firebaseapp.com",
            projectId: "buggy-call-a5785",
            storageBucket: "buggy-call-a5785.firebasestorage.app",
            messagingSenderId: "141355725901",
            appId: "1:141355725901:web:a2c08a67a489ba82ca1804",
            measurementId: "G-7HZ1RNDNX5"

        };
    }
    
    /**
     * FCM'i başlat
     */
    async initialize() {
        try {
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
     * Bildirim izni iste ve token al
     */
    async requestPermissionAndGetToken() {
        try {
            // Bildirim izni kontrolü
            const permission = await Notification.requestPermission();
            
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
                vapidKey: 'BB2-xRCo75G7j3UVqhbeUjv5G55uTN11XCnMt2iZD0w718faVYUZpsGxfAGzqM5Eftw8xN_PVee6X7jRAgoFeAY',
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
        const message = `
            <div class="alert alert-warning" style="margin: 20px;">
                <strong>⚠️ Bildirim İzni Gerekli</strong>
                <p>Yeni talepleri anında almak için bildirim iznini açmanız gerekiyor.</p>
                <p>Tarayıcı ayarlarından bildirimleri etkinleştirin.</p>
            </div>
        `;
        
        // Dashboard'a mesaj ekle
        const container = document.querySelector('.dashboard-container') || document.body;
        const div = document.createElement('div');
        div.innerHTML = message;
        container.insertBefore(div, container.firstChild);
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
            }
        }
    }
});

// FCM mesajlarını dinle ve dashboard'ı güncelle
window.addEventListener('fcm-message', (event) => {
    const payload = event.detail;
    
    console.log('📬 FCM mesajı alındı:', payload);
    
    // Yeni talep geldiğinde listeyi güncelle
    if (payload.data?.type === 'new_request') {
        console.log('🆕 Yeni talep - Dashboard güncelleniyor...');
        
        // Dashboard'ı yenile (eğer loadPendingRequests fonksiyonu varsa)
        if (typeof loadPendingRequests === 'function') {
            loadPendingRequests();
        }
        
        // Veya sayfayı yenile
        // window.location.reload();
    }
});

console.log('✅ FCM Notification Manager yüklendi');
