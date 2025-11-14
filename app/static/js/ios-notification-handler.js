/**
 * iOS Notification Handler
 * iOS Safari ve PWA için özel bildirim yönetimi
 * Powered by Erkan ERDEM
 */

class IOSNotificationHandler {
    constructor() {
        this.isIOS = /iPhone|iPad|iPod/i.test(navigator.userAgent);
        this.isSafari = /Safari/i.test(navigator.userAgent) && !/Chrome|CriOS|FxiOS/i.test(navigator.userAgent);
        this.isPWA = window.navigator.standalone === true;
        this.iosVersion = this.getIOSVersion();
        this.webPushSupported = this.checkWebPushSupport();
    }

    /**
     * iOS versiyonunu al
     */
    getIOSVersion() {
        if (!this.isIOS) return null;
        
        const match = navigator.userAgent.match(/OS (\d+)_(\d+)_?(\d+)?/);
        if (!match) return null;
        
        return {
            major: parseInt(match[1], 10),
            minor: parseInt(match[2], 10),
            patch: match[3] ? parseInt(match[3], 10) : 0,
            full: `${match[1]}.${match[2]}${match[3] ? '.' + match[3] : ''}`
        };
    }

    /**
     * Web Push desteğini kontrol et (iOS 16.4+)
     */
    checkWebPushSupport() {
        if (!this.iosVersion) return false;
        
        // iOS 16.4+ Web Push destekliyor
        return this.iosVersion.major > 16 || 
               (this.iosVersion.major === 16 && this.iosVersion.minor >= 4);
    }

    /**
     * iOS cihaz kontrolü
     */
    isIOSDevice() {
        return this.isIOS;
    }

    /**
     * iOS PWA kontrolü
     */
    isIOSPWA() {
        return this.isIOS && this.isPWA;
    }

    /**
     * Bildirim desteği kontrolü (gelişmiş)
     */
    isNotificationSupported() {
        // iOS değilse normal kontrol
        if (!this.isIOS) {
            return 'Notification' in window && 'serviceWorker' in navigator;
        }

        // iOS 16.4 altı - bildirim yok
        if (!this.webPushSupported) {
            console.log('[iOS] Web Push requires iOS 16.4+. Current:', this.iosVersion?.full || 'Unknown');
            return false;
        }

        // iOS 16.4+ - PWA modunda olmalı
        if (!this.isPWA) {
            console.log('[iOS] Notifications require PWA mode on iOS');
            return false;
        }

        // Tüm koşullar sağlandı
        return 'Notification' in window && 'serviceWorker' in navigator;
    }

    /**
     * iOS için detaylı durum bilgisi
     */
    getStatus() {
        if (!this.isIOS) {
            return {
                platform: 'not-ios',
                supported: true,
                message: 'Not an iOS device'
            };
        }

        const status = {
            platform: 'ios',
            version: this.iosVersion?.full || 'Unknown',
            isPWA: this.isPWA,
            webPushSupported: this.webPushSupported,
            notificationSupported: this.isNotificationSupported(),
            message: ''
        };

        // Durum mesajı oluştur
        if (!this.webPushSupported) {
            status.message = `iOS ${this.iosVersion?.full || 'Unknown'} - Web Push için iOS 16.4+ gerekli`;
        } else if (!this.isPWA) {
            status.message = 'PWA modunda değil - Ana ekrana ekleyin';
        } else {
            status.message = 'Bildirimler destekleniyor';
        }

        return status;
    }

    /**
     * Bildirim izni iste (iOS için özel - gelişmiş)
     */
    async requestPermission() {
        try {
            // iOS değilse normal akış
            if (!this.isIOS) {
                return await Notification.requestPermission();
            }

            // iOS 16.4 altı - desteklenmiyor
            if (!this.webPushSupported) {
                console.log('[iOS] Web Push not supported on iOS', this.iosVersion?.full);
                this.showVersionNotSupportedMessage();
                return 'denied';
            }

            // iOS Safari (PWA değil) - kullanıcıyı bilgilendir
            if (!this.isPWA) {
                console.log('[iOS] Not in PWA mode - showing install instructions');
                this.showPWARequiredMessage();
                return 'denied';
            }

            // iOS PWA + 16.4+ - bildirim izni iste
            console.log('[iOS PWA] Requesting notification permission');
            
            // iOS'ta bildirim izni için kullanıcı etkileşimi gerekli
            const permission = await Notification.requestPermission();
            console.log('[iOS PWA] Permission result:', permission);
            
            if (permission === 'granted') {
                this.showSuccessMessage();
                
                // FCM token al (eğer fcmManager varsa)
                if (window.fcmManager && typeof window.fcmManager.requestPermissionAndGetToken === 'function') {
                    console.log('[iOS PWA] Getting FCM token...');
                    await window.fcmManager.requestPermissionAndGetToken();
                }
            } else if (permission === 'denied') {
                this.showDeniedMessage();
            }
            
            return permission;

        } catch (error) {
            console.error('[iOS] Error requesting permission:', error);
            this.showErrorMessage(error.message);
            return 'denied';
        }
    }

    /**
     * iOS versiyon desteklenmiyor mesajı
     */
    showVersionNotSupportedMessage() {
        const overlay = document.createElement('div');
        overlay.className = 'ios-notification-overlay';
        overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.85);
            z-index: 10001;
            display: flex;
            align-items: center;
            justify-content: center;
            animation: fadeIn 0.3s ease;
            padding: 20px;
        `;

        const modal = document.createElement('div');
        modal.style.cssText = `
            background: white;
            border-radius: 20px;
            width: 100%;
            max-width: 400px;
            padding: 24px;
            animation: scaleIn 0.3s ease;
        `;

        modal.innerHTML = `
            <style>
                @keyframes fadeIn {
                    from { opacity: 0; }
                    to { opacity: 1; }
                }
                @keyframes scaleIn {
                    from { transform: scale(0.9); opacity: 0; }
                    to { transform: scale(1); opacity: 1; }
                }
            </style>

            <div style="text-align: center;">
                <div style="
                    width: 80px;
                    height: 80px;
                    margin: 0 auto 16px;
                    background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    box-shadow: 0 8px 16px rgba(239, 68, 68, 0.3);
                ">
                    <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2">
                        <circle cx="12" cy="12" r="10"></circle>
                        <line x1="12" y1="8" x2="12" y2="12"></line>
                        <line x1="12" y1="16" x2="12.01" y2="16"></line>
                    </svg>
                </div>

                <h3 style="font-size: 20px; font-weight: 700; color: #1e293b; margin-bottom: 12px;">
                    iOS Versiyonu Eski
                </h3>

                <p style="font-size: 14px; color: #64748b; line-height: 1.6; margin-bottom: 20px;">
                    Bildirimler için <strong>iOS 16.4 veya üzeri</strong> gereklidir.<br>
                    Mevcut versiyon: <strong>${this.iosVersion?.full || 'Bilinmiyor'}</strong>
                </p>

                <div style="
                    background: #fef3c7;
                    border-left: 4px solid #f59e0b;
                    padding: 12px 16px;
                    border-radius: 8px;
                    text-align: left;
                    margin-bottom: 20px;
                ">
                    <div style="font-weight: 600; color: #92400e; margin-bottom: 4px;">
                        💡 Çözüm
                    </div>
                    <div style="font-size: 13px; color: #78350f; line-height: 1.6;">
                        Ayarlar → Genel → Yazılım Güncellemesi'nden iOS'u güncelleyin
                    </div>
                </div>

                <button onclick="this.closest('.ios-notification-overlay').remove()" style="
                    width: 100%;
                    padding: 14px;
                    background: #1BA5A8;
                    border: none;
                    border-radius: 12px;
                    font-size: 16px;
                    font-weight: 600;
                    color: white;
                    cursor: pointer;
                ">
                    Anladım
                </button>
            </div>
        `;

        overlay.appendChild(modal);
        document.body.appendChild(overlay);

        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) {
                overlay.remove();
            }
        });
    }

    /**
     * Hata mesajı göster
     */
    showErrorMessage(errorText) {
        this.showToast(`❌ Hata: ${errorText}`, 'error');
    }

    /**
     * PWA gerekli mesajı göster
     */
    showPWARequiredMessage() {
        const overlay = document.createElement('div');
        overlay.className = 'ios-notification-overlay';
        overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.85);
            z-index: 10001;
            display: flex;
            align-items: center;
            justify-content: center;
            animation: fadeIn 0.3s ease;
            padding: 20px;
        `;

        const modal = document.createElement('div');
        modal.style.cssText = `
            background: white;
            border-radius: 20px;
            width: 100%;
            max-width: 400px;
            padding: 24px;
            animation: scaleIn 0.3s ease;
        `;

        modal.innerHTML = `
            <style>
                @keyframes fadeIn {
                    from { opacity: 0; }
                    to { opacity: 1; }
                }
                @keyframes scaleIn {
                    from { transform: scale(0.9); opacity: 0; }
                    to { transform: scale(1); opacity: 1; }
                }
            </style>

            <div style="text-align: center;">
                <div style="
                    width: 80px;
                    height: 80px;
                    margin: 0 auto 16px;
                    background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    box-shadow: 0 8px 16px rgba(245, 158, 11, 0.3);
                ">
                    <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2">
                        <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path>
                        <path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
                    </svg>
                </div>

                <h3 style="font-size: 20px; font-weight: 700; color: #1e293b; margin-bottom: 12px;">
                    Bildirimler İçin PWA Gerekli
                </h3>

                <p style="font-size: 14px; color: #64748b; line-height: 1.6; margin-bottom: 20px;">
                    iOS'ta bildirimler sadece uygulamayı <strong>Ana Ekrana Ekledikten</strong> sonra çalışır.
                </p>

                <div style="
                    background: #f0f9ff;
                    border-left: 4px solid #1BA5A8;
                    padding: 12px 16px;
                    border-radius: 8px;
                    text-align: left;
                    margin-bottom: 20px;
                ">
                    <div style="font-weight: 600; color: #1e293b; margin-bottom: 8px;">
                        📱 Nasıl Eklerim?
                    </div>
                    <ol style="margin: 0; padding-left: 20px; font-size: 13px; color: #64748b; line-height: 1.8;">
                        <li>Safari'de <strong>Paylaş</strong> butonuna tıklayın</li>
                        <li><strong>"Ana Ekrana Ekle"</strong> seçin</li>
                        <li><strong>"Ekle"</strong> butonuna basın</li>
                    </ol>
                </div>

                <button onclick="this.closest('.ios-notification-overlay').remove()" style="
                    width: 100%;
                    padding: 14px;
                    background: #1BA5A8;
                    border: none;
                    border-radius: 12px;
                    font-size: 16px;
                    font-weight: 600;
                    color: white;
                    cursor: pointer;
                ">
                    Anladım
                </button>
            </div>
        `;

        overlay.appendChild(modal);
        document.body.appendChild(overlay);

        // Close on backdrop click
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) {
                overlay.remove();
            }
        });
    }

    /**
     * Başarı mesajı
     */
    showSuccessMessage() {
        this.showToast('✅ Bildirimler Aktif!', 'success');
    }

    /**
     * Reddedildi mesajı
     */
    showDeniedMessage() {
        this.showToast('⚠️ Bildirim izni reddedildi', 'warning');
    }

    /**
     * Toast mesajı göster
     */
    showToast(message, type = 'info') {
        const colors = {
            success: '#10b981',
            warning: '#f59e0b',
            error: '#ef4444',
            info: '#3b82f6'
        };

        const toast = document.createElement('div');
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${colors[type]};
            color: white;
            padding: 16px 20px;
            border-radius: 12px;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
            z-index: 10002;
            animation: slideInRight 0.3s ease;
            font-weight: 600;
        `;
        toast.textContent = message;

        document.body.appendChild(toast);

        setTimeout(() => {
            toast.style.animation = 'slideOutRight 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    /**
     * Bildirim durumunu kontrol et ve kullanıcıyı bilgilendir
     */
    async checkAndPrompt() {
        // iOS değilse normal akış
        if (!this.isIOS) {
            return;
        }

        // PWA modunda değilse bilgilendir
        if (!this.isPWA) {
            console.log('[iOS] Not in PWA mode - user should install first');
            // Otomatik gösterme, sadece bildirim izni istendiğinde göster
            return;
        }

        // PWA modunda ve bildirim izni verilmemişse iste
        if (Notification.permission === 'default') {
            console.log('[iOS PWA] Notification permission not decided yet');
            // Kullanıcı etkileşimi bekle
        }
    }
}

// Global instance
window.iosNotificationHandler = new IOSNotificationHandler();

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = IOSNotificationHandler;
}

console.log('[iOS] Notification handler loaded');
