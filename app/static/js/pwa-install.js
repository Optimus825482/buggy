/**
 * PWA Install Prompt Handler
 * Shuttle Call - Progressive Web App
 */

class PWAInstaller {
    constructor() {
        this.deferredPrompt = null;
        this.installButton = null;
        this.installBanner = null;
        this.init();
    }

    init() {
        // Check if we should show install prompt based on user role
        // Only show for admin and driver, NOT for guest
        if (!this.shouldShowInstallPrompt()) {
            console.log('[PWA] Install prompt disabled for guest users');
            return;
        }

        // Check if app is already installed
        if (window.matchMedia('(display-mode: standalone)').matches ||
            window.navigator.standalone === true) {
            console.log('[PWA] App is running in standalone mode');
            return;
        }

        // iOS Safari özel kontrolü
        const isIOS = /iPhone|iPad|iPod/i.test(navigator.userAgent);
        const isSafari = /Safari/i.test(navigator.userAgent) && !/Chrome|CriOS|FxiOS/i.test(navigator.userAgent);
        
        if (isIOS && isSafari) {
            console.log('[PWA] iOS Safari detected - showing iOS install instructions');
            // iOS için özel prompt göster (biraz gecikmeyle)
            setTimeout(() => {
                this.showIOSInstallPrompt();
            }, 3000);
            return;
        }

        // Android/Desktop için normal prompt
        // Listen for beforeinstallprompt event
        window.addEventListener('beforeinstallprompt', (e) => {
            console.log('[PWA] Install prompt available');
            e.preventDefault();
            this.deferredPrompt = e;
            this.showInstallPrompt();
        });

        // Listen for app installed event
        window.addEventListener('appinstalled', () => {
            console.log('[PWA] App installed successfully');
            this.hideInstallPrompt();
            this.showInstalledMessage();
        });

        // Create install UI
        this.createInstallUI();
    }

    /**
     * Check if install prompt should be shown
     * Only show for admin and driver pages, NOT for guest pages
     */
    shouldShowInstallPrompt() {
        // Check URL path to determine user type
        const path = window.location.pathname;

        // Show for admin and driver paths
        if (path.startsWith('/admin') || path.startsWith('/driver')) {
            return true;
        }

        // Don't show for guest paths
        if (path.startsWith('/guest')) {
            return false;
        }

        // Default: don't show for other paths (auth, api, etc.)
        return false;
    }

    createInstallUI() {
        // Create install banner
        this.installBanner = document.createElement('div');
        this.installBanner.id = 'pwa-install-banner';
        this.installBanner.className = 'pwa-install-banner';
        this.installBanner.innerHTML = `
            <div class="pwa-install-content">
                <div class="pwa-install-icon">
                    <img src="/static/icons/Icon-96.png" alt="Shuttle Call">
                </div>
                <div class="pwa-install-text">
                    <h3>Shuttle Call Uygulamasını Yükle</h3>
                    <p>Daha hızlı erişim ve offline kullanım için yükleyin</p>
                </div>
                <div class="pwa-install-actions">
                    <button class="pwa-install-btn" id="pwa-install-btn">
                        <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                            <path d="M10 1V15M10 15L5 10M10 15L15 10M3 19H17" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        </svg>
                        Yükle
                    </button>
                    <button class="pwa-close-btn" id="pwa-close-btn">
                        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                            <path d="M4 4L12 12M4 12L12 4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                        </svg>
                    </button>
                </div>
            </div>
        `;

        // Add styles
        const style = document.createElement('style');
        style.textContent = `
            .pwa-install-banner {
                position: fixed;
                bottom: 20px;
                left: 50%;
                transform: translateX(-50%);
                max-width: 500px;
                width: calc(100% - 40px);
                background: white;
                border-radius: 16px;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
                padding: 16px 20px;
                z-index: 9999;
                animation: slideUp 0.4s ease-out;
                display: none;
            }

            @keyframes slideUp {
                from {
                    transform: translate(-50%, 100px);
                    opacity: 0;
                }
                to {
                    transform: translate(-50%, 0);
                    opacity: 1;
                }
            }

            .pwa-install-banner.show {
                display: block;
            }

            .pwa-install-content {
                display: flex;
                align-items: center;
                gap: 16px;
            }

            .pwa-install-icon img {
                width: 56px;
                height: 56px;
                border-radius: 12px;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            }

            .pwa-install-text {
                flex: 1;
            }

            .pwa-install-text h3 {
                font-size: 16px;
                font-weight: 600;
                color: #1f2937;
                margin: 0 0 4px 0;
            }

            .pwa-install-text p {
                font-size: 13px;
                color: #6b7280;
                margin: 0;
            }

            .pwa-install-actions {
                display: flex;
                gap: 8px;
                align-items: center;
            }

            .pwa-install-btn {
                display: flex;
                align-items: center;
                gap: 8px;
                padding: 10px 20px;
                background: #1BA5A8;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.2s;
            }

            .pwa-install-btn:hover {
                background: #158B8E;
                transform: translateY(-1px);
            }

            .pwa-install-btn:active {
                transform: translateY(0);
            }

            .pwa-close-btn {
                padding: 8px;
                background: transparent;
                border: none;
                color: #9ca3af;
                cursor: pointer;
                border-radius: 8px;
                transition: all 0.2s;
            }

            .pwa-close-btn:hover {
                background: #f3f4f6;
                color: #6b7280;
            }

            @media (max-width: 768px) {
                .pwa-install-banner {
                    bottom: 10px;
                    width: calc(100% - 20px);
                    padding: 12px 16px;
                }

                .pwa-install-content {
                    gap: 12px;
                }

                .pwa-install-icon img {
                    width: 48px;
                    height: 48px;
                }

                .pwa-install-text h3 {
                    font-size: 14px;
                }

                .pwa-install-text p {
                    font-size: 12px;
                }

                .pwa-install-btn {
                    padding: 8px 16px;
                    font-size: 13px;
                }
            }

            /* Toast notification */
            .pwa-toast {
                position: fixed;
                top: 20px;
                right: 20px;
                background: #10b981;
                color: white;
                padding: 16px 20px;
                border-radius: 12px;
                box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
                z-index: 10000;
                animation: slideIn 0.3s ease-out;
                display: flex;
                align-items: center;
                gap: 12px;
            }

            @keyframes slideIn {
                from {
                    transform: translateX(400px);
                    opacity: 0;
                }
                to {
                    transform: translateX(0);
                    opacity: 1;
                }
            }

            .pwa-toast.hide {
                animation: slideOut 0.3s ease-in forwards;
            }

            @keyframes slideOut {
                to {
                    transform: translateX(400px);
                    opacity: 0;
                }
            }
        `;

        document.head.appendChild(style);

        // Add banner to body (hidden initially)
        document.body.appendChild(this.installBanner);

        // Add event listeners
        const installBtn = document.getElementById('pwa-install-btn');
        const closeBtn = document.getElementById('pwa-close-btn');

        if (installBtn) {
            installBtn.addEventListener('click', () => this.handleInstallClick());
        }

        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.hideInstallPrompt());
        }
    }

    showInstallPrompt() {
        if (this.installBanner && !this.isPromptDismissed()) {
            this.installBanner.classList.add('show');
        }
    }

    hideInstallPrompt() {
        if (this.installBanner) {
            this.installBanner.classList.remove('show');
            this.setPromptDismissed();
        }
    }

    async handleInstallClick() {
        if (!this.deferredPrompt) {
            console.log('[PWA] No install prompt available');
            return;
        }

        // Show the install prompt
        this.deferredPrompt.prompt();

        // Wait for the user to respond
        const { outcome } = await this.deferredPrompt.userChoice;
        console.log(`[PWA] User response: ${outcome}`);

        if (outcome === 'accepted') {
            console.log('[PWA] User accepted the install prompt');
        } else {
            console.log('[PWA] User dismissed the install prompt');
        }

        // Clear the deferred prompt
        this.deferredPrompt = null;
        this.hideInstallPrompt();
    }

    showInstalledMessage() {
        const toast = document.createElement('div');
        toast.className = 'pwa-toast';
        toast.innerHTML = `
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                <path d="M9 12L11 14L15 10M21 12C21 16.9706 16.9706 21 12 21C7.02944 21 3 16.9706 3 12C3 7.02944 7.02944 3 12 3C16.9706 3 21 7.02944 21 12Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <span>Uygulama başarıyla yüklendi!</span>
        `;

        document.body.appendChild(toast);

        setTimeout(() => {
            toast.classList.add('hide');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    /**
     * iOS için özel install promptu göster
     */
    showIOSInstallPrompt() {
        // Daha önce kapatıldıysa tekrar gösterme
        if (this.isPromptDismissed()) {
            return;
        }

        const overlay = document.createElement('div');
        overlay.className = 'ios-install-overlay';
        overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.85);
            z-index: 10000;
            display: flex;
            align-items: flex-end;
            justify-content: center;
            animation: fadeIn 0.3s ease;
        `;

        const modal = document.createElement('div');
        modal.style.cssText = `
            background: white;
            border-radius: 20px 20px 0 0;
            width: 100%;
            max-width: 500px;
            padding: 24px;
            animation: slideUpFromBottom 0.4s ease;
        `;

        modal.innerHTML = `
            <style>
                @keyframes fadeIn {
                    from { opacity: 0; }
                    to { opacity: 1; }
                }
                @keyframes slideUpFromBottom {
                    from { transform: translateY(100%); }
                    to { transform: translateY(0); }
                }
                .ios-install-step {
                    display: flex;
                    align-items: center;
                    gap: 16px;
                    padding: 16px;
                    background: #f8fafc;
                    border-radius: 12px;
                    margin-bottom: 12px;
                }
                .ios-install-step-number {
                    width: 32px;
                    height: 32px;
                    background: #1BA5A8;
                    color: white;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-weight: 700;
                    flex-shrink: 0;
                }
                .ios-install-icon {
                    font-size: 24px;
                    flex-shrink: 0;
                }
                .ios-close-btn {
                    width: 100%;
                    padding: 14px;
                    background: #e2e8f0;
                    border: none;
                    border-radius: 12px;
                    font-size: 16px;
                    font-weight: 600;
                    color: #64748b;
                    cursor: pointer;
                    margin-top: 16px;
                }
            </style>

            <div style="text-align: center; margin-bottom: 24px;">
                <div style="
                    width: 80px;
                    height: 80px;
                    margin: 0 auto 16px;
                    background: linear-gradient(135deg, #1BA5A8 0%, #158B8E 100%);
                    border-radius: 20px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    box-shadow: 0 8px 16px rgba(27, 165, 168, 0.3);
                ">
                    <img src="/static/icons/Icon-96.png" alt="Shuttle Call" style="width: 60px; height: 60px; border-radius: 12px;">
                </div>
                <h3 style="font-size: 20px; font-weight: 700; color: #1e293b; margin-bottom: 8px;">
                    Ana Ekrana Ekle
                </h3>
                <p style="font-size: 14px; color: #64748b;">
                    Daha hızlı erişim ve bildirimler için uygulamayı yükleyin
                </p>
            </div>

            <div class="ios-install-step">
                <div class="ios-install-step-number">1</div>
                <div class="ios-install-icon">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#1BA5A8" stroke-width="2">
                        <rect x="5" y="2" width="14" height="20" rx="2" ry="2"></rect>
                        <line x1="12" y1="18" x2="12" y2="18"></line>
                    </svg>
                </div>
                <div style="flex: 1;">
                    <div style="font-weight: 600; color: #1e293b; margin-bottom: 4px;">
                        Paylaş Butonuna Dokun
                    </div>
                    <div style="font-size: 13px; color: #64748b;">
                        Safari'nin alt kısmındaki paylaş ikonuna tıklayın
                    </div>
                </div>
            </div>

            <div class="ios-install-step">
                <div class="ios-install-step-number">2</div>
                <div class="ios-install-icon">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#1BA5A8" stroke-width="2">
                        <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                        <line x1="12" y1="8" x2="12" y2="16"></line>
                        <line x1="8" y1="12" x2="16" y2="12"></line>
                    </svg>
                </div>
                <div style="flex: 1;">
                    <div style="font-weight: 600; color: #1e293b; margin-bottom: 4px;">
                        "Ana Ekrana Ekle" Seçin
                    </div>
                    <div style="font-size: 13px; color: #64748b;">
                        Açılan menüden "Add to Home Screen" seçeneğini bulun
                    </div>
                </div>
            </div>

            <div class="ios-install-step">
                <div class="ios-install-step-number">3</div>
                <div class="ios-install-icon">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#1BA5A8" stroke-width="2">
                        <polyline points="20 6 9 17 4 12"></polyline>
                    </svg>
                </div>
                <div style="flex: 1;">
                    <div style="font-weight: 600; color: #1e293b; margin-bottom: 4px;">
                        Ekle'ye Basın
                    </div>
                    <div style="font-size: 13px; color: #64748b;">
                        Sağ üstteki "Ekle" butonuna tıklayın
                    </div>
                </div>
            </div>

            <button class="ios-close-btn" id="ios-close-btn">
                Anladım
            </button>
        `;

        overlay.appendChild(modal);
        document.body.appendChild(overlay);

        // Close button
        const closeBtn = modal.querySelector('#ios-close-btn');
        closeBtn.addEventListener('click', () => {
            overlay.style.animation = 'fadeOut 0.3s ease';
            setTimeout(() => {
                overlay.remove();
            }, 300);
            this.setPromptDismissed();
        });

        // Close on backdrop click
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) {
                closeBtn.click();
            }
        });
    }

    isPromptDismissed() {
        return localStorage.getItem('pwa-install-dismissed') === 'true';
    }

    setPromptDismissed() {
        localStorage.setItem('pwa-install-dismissed', 'true');
    }
}

// Initialize PWA Installer
if ('serviceWorker' in navigator) {
    new PWAInstaller();
}

// Handle service worker updates
if ('serviceWorker' in navigator) {
    let updateToastShown = false;
    
    navigator.serviceWorker.addEventListener('controllerchange', () => {
        // Sadece bir kez göster
        if (updateToastShown) {
            console.log('[PWA] Update toast already shown, skipping');
            return;
        }
        
        updateToastShown = true;
        console.log('[PWA] New service worker activated');

        // Mevcut toast'ı kaldır
        const existingToast = document.querySelector('.pwa-update-toast');
        if (existingToast) {
            existingToast.remove();
        }

        // Show update notification
        const updateToast = document.createElement('div');
        updateToast.className = 'pwa-toast pwa-update-toast';
        updateToast.innerHTML = `
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                <path d="M4 4V9H4.58152M19.9381 11C19.446 7.05369 16.0796 4 12 4C8.64262 4 5.76829 6.06817 4.58152 9M4.58152 9H9M20 20V15H19.4185M19.4185 15C18.2317 17.9318 15.3574 20 12 20C7.92038 20 4.55399 16.9463 4.06189 13M19.4185 15H15" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <span>Yeni sürüm yüklendi!</span>
            <button onclick="location.reload()" style="background: rgba(255,255,255,0.2); border: none; color: white; padding: 6px 12px; border-radius: 6px; cursor: pointer; font-weight: 600;">Yenile</button>
        `;

        document.body.appendChild(updateToast);
        
        // 10 saniye sonra otomatik kapat
        setTimeout(() => {
            updateToast.style.opacity = '0';
            setTimeout(() => {
                updateToast.remove();
            }, 300);
        }, 10000);
    });
}

// PWA Install handler loaded
