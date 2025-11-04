/**
 * Shuttle Call - Custom Modal System
 * Modern, tema uyumlu alert, confirm ve modal gösterimler
 */

const BuggyModal = {
    /**
     * Show alert modal
     */
    alert(message, type = 'info', title = '') {
        return new Promise((resolve) => {
            const modal = this.createModal({
                title: title || this.getDefaultTitle(type),
                message: message,
                type: type,
                buttons: [
                    {
                        text: 'Tamam',
                        class: `btn-${type}`,
                        onClick: () => {
                            this.closeModal(modal);
                            resolve(true);
                        }
                    }
                ]
            });
            this.showModal(modal);
        });
    },

    /**
     * Show confirm modal
     */
    confirm(message, title = 'Onay Gerekli', confirmText = 'Evet', cancelText = 'Hayır') {
        return new Promise((resolve) => {
            const modal = this.createModal({
                title: title,
                message: message,
                type: 'warning',
                buttons: [
                    {
                        text: cancelText,
                        class: 'btn-secondary',
                        onClick: () => {
                            this.closeModal(modal);
                            resolve(false);
                        }
                    },
                    {
                        text: confirmText,
                        class: 'btn-primary',
                        onClick: () => {
                            this.closeModal(modal);
                            resolve(true);
                        }
                    }
                ]
            });
            this.showModal(modal);
        });
    },

    /**
     * Show success message
     */
    success(message, title = 'Başarılı!') {
        return this.alert(message, 'success', title);
    },

    /**
     * Show error message
     */
    error(message, title = 'Hata!') {
        return this.alert(message, 'danger', title);
    },

    /**
     * Show warning message
     */
    warning(message, title = 'Uyarı!') {
        return this.alert(message, 'warning', title);
    },

    /**
     * Show info message
     */
    info(message, title = 'Bilgi') {
        return this.alert(message, 'info', title);
    },

    /**
     * Show custom modal with HTML content and get user confirmation
     * @param {string} htmlContent - HTML content to display in modal body
     * @param {object} options - Modal options (title, confirmText, cancelText, size)
     * @returns {Promise<boolean>} - Resolves to true if confirmed, false if cancelled
     */
    custom(htmlContent, options = {}) {
        const {
            title = 'Form',
            confirmText = 'Tamam',
            cancelText = 'İptal',
            size = 'medium',
            type = 'info'
        } = options;

        return new Promise((resolve) => {
            const modal = this.createModal({
                title: title,
                message: '',
                type: type,
                customContent: htmlContent,
                size: size,
                buttons: [
                    {
                        text: cancelText,
                        class: 'btn-secondary',
                        onClick: () => {
                            this.closeModal(modal);
                            resolve(false);
                        }
                    },
                    {
                        text: confirmText,
                        class: 'btn-primary',
                        onClick: () => {
                            this.closeModal(modal);
                            resolve(true);
                        }
                    }
                ]
            });
            this.showModal(modal);
        });
    },

    /**
     * Show custom modal with form
     */
    showCustomModal(options) {
        const modal = this.createModal(options);
        this.showModal(modal);
        return modal;
    },

    /**
     * Create modal element
     */
    createModal(options) {
        const {
            title = '',
            message = '',
            type = 'info',
            buttons = [],
            customContent = null,
            size = 'medium' // small, medium, large
        } = options;

        // Create overlay
        const overlay = document.createElement('div');
        overlay.className = 'buggy-modal-overlay';
        overlay.onclick = (e) => {
            if (e.target === overlay) {
                this.closeModal(overlay);
            }
        };

        // Create modal
        const modal = document.createElement('div');
        modal.className = `buggy-modal buggy-modal-${size}`;

        // Icon based on type
        const icon = this.getIcon(type);

        // Build modal HTML
        modal.innerHTML = `
            <div class="buggy-modal-header ${type}">
                <div class="buggy-modal-icon">
                    <i class="${icon}"></i>
                </div>
                <button class="buggy-modal-close" onclick="BuggyModal.closeCurrentModal()">&times;</button>
            </div>
            <div class="buggy-modal-body">
                ${title ? `<h3 class="buggy-modal-title">${title}</h3>` : ''}
                ${message ? `<p class="buggy-modal-message">${message}</p>` : ''}
                ${customContent || ''}
            </div>
            <div class="buggy-modal-footer">
                ${buttons.map(btn => `
                    <button class="btn ${btn.class || 'btn-secondary'}" data-action="${btn.text}">
                        ${btn.icon ? `<i class="${btn.icon}"></i> ` : ''}${btn.text}
                    </button>
                `).join('')}
            </div>
        `;

        // Attach button handlers
        const btnElements = modal.querySelectorAll('.buggy-modal-footer button');
        btnElements.forEach((btnEl, index) => {
            if (buttons[index] && buttons[index].onClick) {
                btnEl.onclick = buttons[index].onClick;
            }
        });

        overlay.appendChild(modal);
        return overlay;
    },

    /**
     * Show modal
     */
    showModal(overlay) {
        document.body.appendChild(overlay);
        // Trigger animation
        setTimeout(() => {
            overlay.classList.add('show');
        }, 10);
    },

    /**
     * Close modal
     */
    closeModal(overlay) {
        overlay.classList.remove('show');
        setTimeout(() => {
            if (overlay.parentNode) {
                overlay.parentNode.removeChild(overlay);
            }
        }, 300);
    },

    /**
     * Close current modal (for inline onclick)
     */
    closeCurrentModal() {
        const overlay = document.querySelector('.buggy-modal-overlay.show');
        if (overlay) {
            this.closeModal(overlay);
        }
    },

    /**
     * Get icon based on type
     */
    getIcon(type) {
        const icons = {
            'success': 'fas fa-check-circle',
            'danger': 'fas fa-exclamation-circle',
            'warning': 'fas fa-exclamation-triangle',
            'info': 'fas fa-info-circle',
            'question': 'fas fa-question-circle'
        };
        return icons[type] || icons['info'];
    },

    /**
     * Get default title based on type
     */
    getDefaultTitle(type) {
        const titles = {
            'success': 'Başarılı!',
            'danger': 'Hata!',
            'warning': 'Uyarı!',
            'info': 'Bilgi'
        };
        return titles[type] || 'Bildirim';
    }
};

// Make BuggyModal globally accessible
window.BuggyModal = BuggyModal;

// Global shortcuts
window.showAlert = (msg, type, title) => BuggyModal.alert(msg, type, title);
window.showConfirm = (msg, title, yes, no) => BuggyModal.confirm(msg, title, yes, no);
window.showSuccess = (msg, title) => BuggyModal.success(msg, title);
window.showError = (msg, title) => BuggyModal.error(msg, title);
window.showWarning = (msg, title) => BuggyModal.warning(msg, title);

// Debug info
console.log('BuggyModal loaded successfully with custom() method:', typeof BuggyModal.custom);
