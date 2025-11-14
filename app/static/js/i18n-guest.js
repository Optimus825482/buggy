/**
 * Guest Pages Multi-Language Support
 * Tarayıcı dilini otomatik algılar ve içeriği çevirir
 * Powered by Erkan ERDEM
 */

class GuestI18n {
    constructor() {
        this.currentLang = this.detectLanguage();
        this.translations = this.getTranslations();
        this.init();
    }

    /**
     * Tarayıcı dilini algıla
     */
    detectLanguage() {
        // URL parametresinden dil kontrolü (?lang=en)
        const urlParams = new URLSearchParams(window.location.search);
        const urlLang = urlParams.get('lang');
        if (urlLang && this.isSupported(urlLang)) {
            localStorage.setItem('guest_language', urlLang);
            return urlLang;
        }

        // LocalStorage'dan kayıtlı dil
        const savedLang = localStorage.getItem('guest_language');
        if (savedLang && this.isSupported(savedLang)) {
            return savedLang;
        }

        // Tarayıcı dilini algıla
        const browserLang = navigator.language || navigator.userLanguage;
        const langCode = browserLang.split('-')[0].toLowerCase();

        // Desteklenen diller: tr, en, de, ru, ar
        const supported = ['tr', 'en', 'de', 'ru', 'ar'];
        return supported.includes(langCode) ? langCode : 'en';
    }

    /**
     * Dil destekleniyor mu?
     */
    isSupported(lang) {
        return ['tr', 'en', 'de', 'ru', 'ar'].includes(lang.toLowerCase());
    }

    /**
     * Çevirileri getir
     */
    getTranslations() {
        return {
            // Türkçe
            tr: {
                // Brand
                'brand.name': 'Shuttle Call System',
                
                // Call Page
                'call.title': 'Shuttle Çağır',
                'call.scan_qr': 'QR Kod Okut',
                'call.or': 'veya',
                'call.select_location': 'Lokasyon Seç',
                'call.location_placeholder': 'Lokasyon seçin...',
                'call.room_number': 'Oda Numarası',
                'call.room_placeholder': 'Oda numaranızı girin',
                'call.notes': 'Notlar (Opsiyonel)',
                'call.notes_placeholder': 'Özel talepleriniz varsa yazın...',
                'call.call_shuttle': 'Shuttle Çağır',
                'call.calling': 'Çağrılıyor...',
                
                // Status Page
                'status.title': 'Talep Durumu',
                'status.request_id': 'Talep No',
                'status.status': 'Durum',
                'status.location': 'Lokasyon',
                'status.room': 'Oda',
                'status.time': 'Talep Zamanı',
                'status.shuttle': 'Shuttle',
                'status.driver': 'Sürücü',
                'status.eta': 'Tahmini Varış',
                
                // Status Messages
                'status.pending': 'Bekliyor',
                'status.pending_msg': 'Talebiniz alındı, sürücü bekleniyor...',
                'status.accepted': 'Kabul Edildi',
                'status.accepted_msg': 'Shuttle yolda! Sürücü konumunuza geliyor.',
                'status.in_progress': 'Yolda',
                'status.in_progress_msg': 'Shuttle size doğru geliyor.',
                'status.completed': 'Tamamlandı',
                'status.completed_msg': 'Shuttle ulaştı! İyi günler dileriz.',
                'status.cancelled': 'İptal Edildi',
                'status.cancelled_msg': 'Talebiniz iptal edildi.',
                
                // Notifications
                'notif.request_received': 'Talebiniz Alındı!',
                'notif.request_received_msg': 'Shuttle çağrınız başarıyla gönderildi. Durumunu takip edebilirsiniz.',
                'notif.shuttle_accepted': '🎉 Shuttle Kabul Edildi!',
                'notif.shuttle_accepted_msg': 'Shuttle size doğru geliyor.',
                'notif.shuttle_arrived': '✅ Shuttle Ulaştı!',
                'notif.shuttle_arrived_msg': 'İyi günler dileriz.',
                'notif.do_not_close': 'Bu pencereyi 5 saniye boyunca kapatmayın!',
                
                // Buttons
                'btn.confirm': 'Evet, Çağır',
                'btn.cancel': 'İptal',
                'btn.close': 'Kapat',
                'btn.understood': 'Anladım',
                'btn.refresh': 'Yenile',
                'btn.enable_notifications': 'İzin Ver',
                
                // Errors
                'error.no_location': 'Lütfen bir lokasyon seçin veya QR kod okutun.',
                'error.invalid_qr': 'Geçersiz QR kod formatı.',
                'error.request_failed': 'Shuttle çağrısı gönderilemedi.',
                'error.network': 'Bağlantı hatası. Lütfen tekrar deneyin.',
                
                // Notification Permission
                'notif.permission_denied': 'Bildirimler Kapalı',
                'notif.permission_denied_msg': 'Shuttle durumu hakkında bildirim almak için izin verin.',
                
                // QR Scanner
                'qr.title': 'QR Kod Tarayıcı',
                'qr.instruction': 'QR kodu kameranın önüne tutun',
                'qr.camera_error': 'Kamera erişimi reddedildi.',
                
                // Confirmation
                'confirm.title': 'Shuttle Çağırmak İstiyor musunuz?',
                'confirm.subtitle': 'Talebinizi onaylayın',
                'confirm.location': 'Lokasyon',
                'confirm.room': 'Oda',
                
                // Request Success
                'request.created': 'Talebiniz Alındı',
                'request.created_msg': 'Talebiniz başarıyla oluşturuldu. Yakındaki sürücüler bilgilendirildi.',
                'request.redirecting': 'Yönlendiriliyorsunuz...',
                
                // Status Labels
                'label.location': 'Lokasyon',
                'label.room': 'Oda No',
                'label.created': 'Talep Oluşturuldu',
                'label.processing': 'İşleme Alındı',
                'label.waiting': 'Bekleniyor...',
                'label.on_the_way': 'Shuttle Yolda',
                'label.arrived': 'Geldi'
            },

            // English
            en: {
                'brand.name': 'Shuttle Call System',
                
                'call.title': 'Call Shuttle',
                'call.scan_qr': 'Scan QR Code',
                'call.or': 'or',
                'call.select_location': 'Select Location',
                'call.location_placeholder': 'Select location...',
                'call.room_number': 'Room Number',
                'call.room_placeholder': 'Enter your room number',
                'call.notes': 'Notes (Optional)',
                'call.notes_placeholder': 'Write your special requests...',
                'call.call_shuttle': 'Call Shuttle',
                'call.calling': 'Calling...',
                
                'status.title': 'Request Status',
                'status.request_id': 'Request ID',
                'status.status': 'Status',
                'status.location': 'Location',
                'status.room': 'Room',
                'status.time': 'Request Time',
                'status.shuttle': 'Shuttle',
                'status.driver': 'Driver',
                'status.eta': 'Estimated Arrival',
                
                'status.pending': 'Pending',
                'status.pending_msg': 'Your request has been received, waiting for driver...',
                'status.accepted': 'Accepted',
                'status.accepted_msg': 'Shuttle is on the way! Driver is coming to your location.',
                'status.in_progress': 'In Progress',
                'status.in_progress_msg': 'Shuttle is heading towards you.',
                'status.completed': 'Completed',
                'status.completed_msg': 'Shuttle has arrived! Have a nice day.',
                'status.cancelled': 'Cancelled',
                'status.cancelled_msg': 'Your request has been cancelled.',
                
                'notif.request_received': 'Request Received!',
                'notif.request_received_msg': 'Your shuttle call has been sent successfully. You can track its status.',
                'notif.shuttle_accepted': '🎉 Shuttle Accepted!',
                'notif.shuttle_accepted_msg': 'Shuttle is coming to you.',
                'notif.shuttle_arrived': '✅ Shuttle Arrived!',
                'notif.shuttle_arrived_msg': 'Have a nice day.',
                'notif.do_not_close': 'Do not close this window for 5 seconds!',
                
                'btn.confirm': 'Yes, Call',
                'btn.cancel': 'Cancel',
                'btn.close': 'Close',
                'btn.understood': 'Understood',
                'btn.refresh': 'Refresh',
                'btn.enable_notifications': 'Enable',
                
                'notif.permission_denied': 'Notifications Disabled',
                'notif.permission_denied_msg': 'Enable notifications to receive shuttle status updates.',
                
                'error.no_location': 'Please select a location or scan QR code.',
                'error.invalid_qr': 'Invalid QR code format.',
                'error.request_failed': 'Failed to send shuttle call.',
                'error.network': 'Connection error. Please try again.',
                
                'qr.title': 'QR Code Scanner',
                'qr.instruction': 'Hold the QR code in front of the camera',
                'qr.camera_error': 'Camera access denied.',
                
                'confirm.title': 'Do You Want to Call Shuttle?',
                'confirm.subtitle': 'Confirm your request',
                'confirm.location': 'Location',
                'confirm.room': 'Room',
                
                'request.created': 'Request Received',
                'request.created_msg': 'Your request has been created successfully. Nearby drivers have been notified.',
                'request.redirecting': 'Redirecting...',
                
                'label.location': 'Location',
                'label.room': 'Room No',
                'label.created': 'Request Created',
                'label.processing': 'Processing',
                'label.waiting': 'Waiting...',
                'label.on_the_way': 'Shuttle On The Way',
                'label.arrived': 'Arrived'
            },

            // Deutsch (German)
            de: {
                'brand.name': 'Shuttle Call System',
                'call.title': 'Shuttle Rufen',
                'call.scan_qr': 'QR-Code Scannen',
                'call.or': 'oder',
                'call.select_location': 'Standort Wählen',
                'call.location_placeholder': 'Standort auswählen...',
                'call.room_number': 'Zimmernummer',
                'call.room_placeholder': 'Geben Sie Ihre Zimmernummer ein',
                'call.notes': 'Notizen (Optional)',
                'call.notes_placeholder': 'Schreiben Sie Ihre Sonderwünsche...',
                'call.call_shuttle': 'Shuttle Rufen',
                'call.calling': 'Wird Gerufen...',
                
                'status.title': 'Anfragestatus',
                'status.request_id': 'Anfrage-ID',
                'status.status': 'Status',
                'status.location': 'Standort',
                'status.room': 'Zimmer',
                'status.time': 'Anfragezeit',
                'status.shuttle': 'Shuttle',
                'status.driver': 'Fahrer',
                'status.eta': 'Geschätzte Ankunft',
                
                'status.pending': 'Ausstehend',
                'status.pending_msg': 'Ihre Anfrage wurde empfangen, warte auf Fahrer...',
                'status.accepted': 'Akzeptiert',
                'status.accepted_msg': 'Shuttle ist unterwegs! Fahrer kommt zu Ihrem Standort.',
                'status.in_progress': 'In Bearbeitung',
                'status.in_progress_msg': 'Shuttle fährt zu Ihnen.',
                'status.completed': 'Abgeschlossen',
                'status.completed_msg': 'Shuttle ist angekommen! Einen schönen Tag.',
                'status.cancelled': 'Storniert',
                'status.cancelled_msg': 'Ihre Anfrage wurde storniert.',
                
                'notif.request_received': 'Anfrage Erhalten!',
                'notif.request_received_msg': 'Ihr Shuttle-Ruf wurde erfolgreich gesendet.',
                'notif.shuttle_accepted': '🎉 Shuttle Akzeptiert!',
                'notif.shuttle_accepted_msg': 'Shuttle kommt zu Ihnen.',
                'notif.shuttle_arrived': '✅ Shuttle Angekommen!',
                'notif.shuttle_arrived_msg': 'Einen schönen Tag.',
                'notif.do_not_close': 'Schließen Sie dieses Fenster 5 Sekunden lang nicht!',
                
                'btn.confirm': 'Ja, Rufen',
                'btn.cancel': 'Abbrechen',
                'btn.close': 'Schließen',
                'btn.understood': 'Verstanden',
                'btn.refresh': 'Aktualisieren',
                'btn.enable_notifications': 'Aktivieren',
                
                'notif.permission_denied': 'Benachrichtigungen Deaktiviert',
                'notif.permission_denied_msg': 'Aktivieren Sie Benachrichtigungen für Shuttle-Updates.',
                
                'error.no_location': 'Bitte wählen Sie einen Standort oder scannen Sie den QR-Code.',
                'error.invalid_qr': 'Ungültiges QR-Code-Format.',
                'error.request_failed': 'Shuttle-Ruf konnte nicht gesendet werden.',
                'error.network': 'Verbindungsfehler. Bitte versuchen Sie es erneut.',
                
                'qr.title': 'QR-Code-Scanner',
                'qr.instruction': 'Halten Sie den QR-Code vor die Kamera',
                'qr.camera_error': 'Kamerazugriff verweigert.',
                
                'confirm.title': 'Möchten Sie Shuttle Rufen?',
                'confirm.subtitle': 'Bestätigen Sie Ihre Anfrage',
                'confirm.location': 'Standort',
                'confirm.room': 'Zimmer',
                
                'request.created': 'Anfrage Erhalten',
                'request.created_msg': 'Ihre Anfrage wurde erfolgreich erstellt. Fahrer in der Nähe wurden benachrichtigt.',
                'request.redirecting': 'Weiterleitung...',
                
                'label.location': 'Standort',
                'label.room': 'Zimmer Nr',
                'label.created': 'Anfrage Erstellt',
                'label.processing': 'In Bearbeitung',
                'label.waiting': 'Warten...',
                'label.on_the_way': 'Shuttle Unterwegs',
                'label.arrived': 'Angekommen'
            },

            // Русский (Russian)
            ru: {
                'brand.name': 'Shuttle Call System',
                'call.title': 'Вызвать Шаттл',
                'call.scan_qr': 'Сканировать QR-код',
                'call.or': 'или',
                'call.select_location': 'Выбрать Локацию',
                'call.location_placeholder': 'Выберите локацию...',
                'call.room_number': 'Номер Комнаты',
                'call.room_placeholder': 'Введите номер вашей комнаты',
                'call.notes': 'Примечания (Необязательно)',
                'call.notes_placeholder': 'Напишите ваши особые пожелания...',
                'call.call_shuttle': 'Вызвать Шаттл',
                'call.calling': 'Вызов...',
                
                'status.title': 'Статус Запроса',
                'status.request_id': 'ID Запроса',
                'status.status': 'Статус',
                'status.location': 'Локация',
                'status.room': 'Комната',
                'status.time': 'Время Запроса',
                'status.shuttle': 'Шаттл',
                'status.driver': 'Водитель',
                'status.eta': 'Ожидаемое Прибытие',
                
                'status.pending': 'Ожидание',
                'status.pending_msg': 'Ваш запрос получен, ожидаем водителя...',
                'status.accepted': 'Принято',
                'status.accepted_msg': 'Шаттл в пути! Водитель едет к вам.',
                'status.in_progress': 'В Процессе',
                'status.in_progress_msg': 'Шаттл направляется к вам.',
                'status.completed': 'Завершено',
                'status.completed_msg': 'Шаттл прибыл! Хорошего дня.',
                'status.cancelled': 'Отменено',
                'status.cancelled_msg': 'Ваш запрос был отменен.',
                
                'notif.request_received': 'Запрос Получен!',
                'notif.request_received_msg': 'Ваш вызов шаттла успешно отправлен.',
                'notif.shuttle_accepted': '🎉 Шаттл Принят!',
                'notif.shuttle_accepted_msg': 'Шаттл едет к вам.',
                'notif.shuttle_arrived': '✅ Шаттл Прибыл!',
                'notif.shuttle_arrived_msg': 'Хорошего дня.',
                'notif.do_not_close': 'Не закрывайте это окно в течение 5 секунд!',
                
                'btn.confirm': 'Да, Вызвать',
                'btn.cancel': 'Отмена',
                'btn.close': 'Закрыть',
                'btn.understood': 'Понятно',
                'btn.refresh': 'Обновить',
                'btn.enable_notifications': 'Разрешить',
                
                'notif.permission_denied': 'Уведомления Отключены',
                'notif.permission_denied_msg': 'Разрешите уведомления для получения обновлений.',
                
                'error.no_location': 'Пожалуйста, выберите локацию или отсканируйте QR-код.',
                'error.invalid_qr': 'Неверный формат QR-кода.',
                'error.request_failed': 'Не удалось отправить вызов шаттла.',
                'error.network': 'Ошибка соединения. Пожалуйста, попробуйте снова.',
                
                'qr.title': 'Сканер QR-кода',
                'qr.instruction': 'Держите QR-код перед камерой',
                'qr.camera_error': 'Доступ к камере запрещен.',
                
                'confirm.title': 'Вы Хотите Вызвать Шаттл?',
                'confirm.subtitle': 'Подтвердите ваш запрос',
                'confirm.location': 'Локация',
                'confirm.room': 'Комната',
                
                'request.created': 'Запрос Получен',
                'request.created_msg': 'Ваш запрос успешно создан. Ближайшие водители уведомлены.',
                'request.redirecting': 'Перенаправление...',
                
                'label.location': 'Локация',
                'label.room': 'Номер Комнаты',
                'label.created': 'Запрос Создан',
                'label.processing': 'Обработка',
                'label.waiting': 'Ожидание...',
                'label.on_the_way': 'Шаттл В Пути',
                'label.arrived': 'Прибыл'
            },

            // العربية (Arabic)
            ar: {
                'brand.name': 'Shuttle Call System',
                'call.title': 'استدعاء الحافلة',
                'call.scan_qr': 'مسح رمز QR',
                'call.or': 'أو',
                'call.select_location': 'اختر الموقع',
                'call.location_placeholder': 'اختر الموقع...',
                'call.room_number': 'رقم الغرفة',
                'call.room_placeholder': 'أدخل رقم غرفتك',
                'call.notes': 'ملاحظات (اختياري)',
                'call.notes_placeholder': 'اكتب طلباتك الخاصة...',
                'call.call_shuttle': 'استدعاء الحافلة',
                'call.calling': 'جاري الاستدعاء...',
                
                'status.title': 'حالة الطلب',
                'status.request_id': 'رقم الطلب',
                'status.status': 'الحالة',
                'status.location': 'الموقع',
                'status.room': 'الغرفة',
                'status.time': 'وقت الطلب',
                'status.shuttle': 'الحافلة',
                'status.driver': 'السائق',
                'status.eta': 'الوصول المتوقع',
                
                'status.pending': 'قيد الانتظار',
                'status.pending_msg': 'تم استلام طلبك، في انتظار السائق...',
                'status.accepted': 'تم القبول',
                'status.accepted_msg': 'الحافلة في الطريق! السائق قادم إلى موقعك.',
                'status.in_progress': 'قيد التنفيذ',
                'status.in_progress_msg': 'الحافلة متجهة نحوك.',
                'status.completed': 'مكتمل',
                'status.completed_msg': 'وصلت الحافلة! يوم سعيد.',
                'status.cancelled': 'ملغى',
                'status.cancelled_msg': 'تم إلغاء طلبك.',
                
                'notif.request_received': 'تم استلام الطلب!',
                'notif.request_received_msg': 'تم إرسال استدعاء الحافلة بنجاح.',
                'notif.shuttle_accepted': '🎉 تم قبول الحافلة!',
                'notif.shuttle_accepted_msg': 'الحافلة قادمة إليك.',
                'notif.shuttle_arrived': '✅ وصلت الحافلة!',
                'notif.shuttle_arrived_msg': 'يوم سعيد.',
                'notif.do_not_close': 'لا تغلق هذه النافذة لمدة 5 ثوان!',
                
                'btn.confirm': 'نعم، استدعاء',
                'btn.cancel': 'إلغاء',
                'btn.close': 'إغلاق',
                'btn.understood': 'فهمت',
                'btn.refresh': 'تحديث',
                'btn.enable_notifications': 'تفعيل',
                
                'notif.permission_denied': 'الإشعارات معطلة',
                'notif.permission_denied_msg': 'قم بتفعيل الإشعارات لتلقي تحديثات الحافلة.',
                
                'error.no_location': 'الرجاء اختيار موقع أو مسح رمز QR.',
                'error.invalid_qr': 'تنسيق رمز QR غير صالح.',
                'error.request_failed': 'فشل إرسال استدعاء الحافلة.',
                'error.network': 'خطأ في الاتصال. يرجى المحاولة مرة أخرى.',
                
                'qr.title': 'ماسح رمز QR',
                'qr.instruction': 'ضع رمز QR أمام الكاميرا',
                'qr.camera_error': 'تم رفض الوصول إلى الكاميرا.',
                
                'confirm.title': 'هل تريد استدعاء الحافلة؟',
                'confirm.subtitle': 'أكد طلبك',
                'confirm.location': 'الموقع',
                'confirm.room': 'الغرفة',
                
                'request.created': 'تم استلام الطلب',
                'request.created_msg': 'تم إنشاء طلبك بنجاح. تم إخطار السائقين القريبين.',
                'request.redirecting': 'إعادة التوجيه...',
                
                'label.location': 'الموقع',
                'label.room': 'رقم الغرفة',
                'label.created': 'تم إنشاء الطلب',
                'label.processing': 'قيد المعالجة',
                'label.waiting': 'في الانتظار...',
                'label.on_the_way': 'الحافلة في الطريق',
                'label.arrived': 'وصلت'
            }
        };
    }

    /**
     * Sistemi başlat
     */
    init() {
    console.log(`
╔════════════════════════════════════════════════════════════╗
║  🌍 Guest i18n System Initializing                        ║
╠════════════════════════════════════════════════════════════╣
║  Detected Language: ${this.currentLang.toUpperCase().padEnd(37)} ║
║  Supported Languages: TR, EN, DE, RU, AR                  ║
╚════════════════════════════════════════════════════════════╝
        `);
        
        // Çevirileri doğrula (sadece development'ta)
        if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
            this.validateTranslations();
        }
        
        // Sayfa yüklendiğinde çevir
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                console.log('[i18n] 📄 DOM loaded, starting translation...');
                this.translatePage();
                this.setupMutationObserver();
            });
        } else {
            console.log('[i18n] 📄 DOM already loaded, starting translation...');
            this.translatePage();
            this.setupMutationObserver();
        }

        // Dil değiştirici butonları ekle
        this.addLanguageSwitcher();

        // RTL desteği (Arapça için)
        if (this.currentLang === 'ar') {
            document.documentElement.setAttribute('dir', 'rtl');
            document.documentElement.setAttribute('lang', 'ar');
            console.log('[i18n] 🔄 RTL mode enabled for Arabic');
        } else {
            document.documentElement.setAttribute('dir', 'ltr');
            document.documentElement.setAttribute('lang', this.currentLang);
        }
        
        console.log('[i18n] ✅ Initialization complete');
    }*

    /**
     * Dinamik içerik için MutationObserver kur
     */
    setupMutationObserver() {
        // MutationObserver ile yeni eklenen elementleri izle
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                mutation.addedNodes.forEach((node) => {
                    // Element node mu?
                    if (node.nodeType === Node.ELEMENT_NODE) {
                        // data-i18n attribute'u var mı?
                        if (node.hasAttribute && node.hasAttribute('data-i18n')) {
                            const key = node.getAttribute('data-i18n');
                            const translation = this.t(key);
                            node.textContent = translation;
                            console.log(`[i18n] 🆕 New element translated: ${key}`);
                        }
                        
                        // İçinde data-i18n elementleri var mı?
                        if (node.querySelectorAll) {
                            const i18nElements = node.querySelectorAll('[data-i18n]');
                            if (i18nElements.length > 0) {
                                console.log(`[i18n] 🆕 Found ${i18nElements.length} new i18n elements`);
                                i18nElements.forEach(el => {
                                    const key = el.getAttribute('data-i18n');
                                    const translation = this.t(key);
                                    el.textContent = translation;
                                });
                            }
                        }
                    }
                });
            });
        });

        // Body'yi izlemeye başla
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });

        console.log('[i18n] 👁️ MutationObserver active - watching for dynamic content');
    }

    /**
     * Çeviriyi getir
     */
    t(key) {
        // Key validation
        if (!key || typeof key !== 'string') {
            console.error(`[i18n] Invalid translation key:`, key);
            return key || '';
        }
        
        const translation = this.translations[this.currentLang]?.[key];
        
        if (!translation) {
            console.warn(`[i18n] ⚠️ Translation not found: "${key}" for language "${this.currentLang}"`);
            
            // Fallback to English
            const englishTranslation = this.translations['en']?.[key];
            if (englishTranslation) {
                console.log(`[i18n] 📝 Using English fallback for "${key}"`);
                return englishTranslation;
            }
            
            // Son çare: key'in kendisini döndür
            console.error(`[i18n] ❌ No translation found in any language for "${key}"`);
            return key;
        }
        
        return translation;
    }

    /**
     * Tüm çevirileri doğrula
     */
    validateTranslations() {
        console.log('[i18n] 🔍 Validating translations...');
        
        const languages = Object.keys(this.translations);
        const allKeys = new Set();
        const report = {};
        
        // Tüm key'leri topla
        languages.forEach(lang => {
            Object.keys(this.translations[lang]).forEach(key => allKeys.add(key));
        });
        
        // Her dil için eksik key'leri kontrol et
        languages.forEach(lang => {
            const missingKeys = [];
            allKeys.forEach(key => {
                if (!this.translations[lang][key]) {
                    missingKeys.push(key);
                }
            });
            
            report[lang] = {
                total: allKeys.size,
                translated: allKeys.size - missingKeys.length,
                missing: missingKeys.length,
                missingKeys: missingKeys,
                coverage: ((allKeys.size - missingKeys.length) / allKeys.size * 100).toFixed(1) + '%'
            };
        });
        
        console.table(report);
        
        // Eksik çeviriler varsa uyar
        Object.entries(report).forEach(([lang, data]) => {
            if (data.missing > 0) {
                console.warn(`[i18n] ⚠️ ${lang.toUpperCase()}: ${data.missing} missing translations`, data.missingKeys);
            } else {
                console.log(`[i18n] ✅ ${lang.toUpperCase()}: Complete (${data.total} translations)`);
            }
        });
        
        return report;
    }

    /**
     * Sayfayı çevir
     */
    translatePage() {
        try {
            // data-i18n attribute'u olan tüm elementleri bul
            const elements = document.querySelectorAll('[data-i18n]');
            
            let successCount = 0;
            let errorCount = 0;
            const errors = [];
            
            elements.forEach((element, index) => {
                try {
                    const key = element.getAttribute('data-i18n');
                    
                    // Key validation
                    if (!key || key.trim() === '') {
                        console.warn(`[i18n] Empty key at element ${index}:`, element);
                        errorCount++;
                        return;
                    }
                    
                    const translation = this.t(key);
                    
                    // Translation validation
                    if (!translation || translation === key) {
                        console.warn(`[i18n] Missing translation for key: ${key}`);
                        errors.push({ key, element });
                        errorCount++;
                        return;
                    }
                    
                    // Placeholder attribute
                    if (element.hasAttribute('placeholder')) {
                        const oldValue = element.getAttribute('placeholder');
                        element.setAttribute('placeholder', translation);
                        console.log(`[i18n] ✓ Placeholder: "${oldValue}" → "${translation}"`);
                        successCount++;
                    } 
                    // Value attribute (input fields)
                    else if (element.hasAttribute('value') && element.tagName === 'INPUT') {
                        const oldValue = element.getAttribute('value');
                        element.setAttribute('value', translation);
                        console.log(`[i18n] ✓ Input value: "${oldValue}" → "${translation}"`);
                        successCount++;
                    }
                    // Title attribute
                    else if (element.hasAttribute('title')) {
                        const oldValue = element.getAttribute('title');
                        element.setAttribute('title', translation);
                        console.log(`[i18n] ✓ Title: "${oldValue}" → "${translation}"`);
                        successCount++;
                    }
                    // Alt attribute (images)
                    else if (element.hasAttribute('alt') && element.tagName === 'IMG') {
                        const oldValue = element.getAttribute('alt');
                        element.setAttribute('alt', translation);
                        console.log(`[i18n] ✓ Alt text: "${oldValue}" → "${translation}"`);
                        successCount++;
                    }
                    // Aria-label attribute
                    else if (element.hasAttribute('aria-label')) {
                        const oldValue = element.getAttribute('aria-label');
                        element.setAttribute('aria-label', translation);
                        console.log(`[i18n] ✓ Aria-label: "${oldValue}" → "${translation}"`);
                        successCount++;
                    }
                    // Normal text content
                    else {
                        const oldText = element.textContent.trim();
                        
                        // Element içinde child elementler var mı?
                        if (element.children.length === 0) {
                            // Basit element - direkt textContent
                            element.textContent = translation;
                            
                            // DOM'u zorla güncelle
                            element.style.display = 'none';
                            element.offsetHeight; // Force reflow
                            element.style.display = '';
                            
                            console.log(`[i18n] ✓ Text: "${oldText}" → "${translation}"`);
                        } else {
                            // İçinde child elementler var
                            // innerHTML kullan (daha güvenilir)
                            const originalHTML = element.innerHTML;
                            element.innerHTML = translation;
                            
                            // DOM'u zorla güncelle
                            element.style.display = 'none';
                            element.offsetHeight; // Force reflow
                            element.style.display = '';
                            
                            console.log(`[i18n] ✓ innerHTML: "${oldText}" → "${translation}"`);
                        }
                        successCount++;
                    }
                    
                } catch (error) {
                    console.error(`[i18n] Error translating element ${index}:`, error, element);
                    errorCount++;
                    errors.push({ element, error: error.message });
                }
            });

            // Page title'ı güncelle
            this.updatePageTitle();

            // Özet rapor
            console.log(`
╔════════════════════════════════════════════════════════════╗
║  🌍 Translation Report - ${this.currentLang.toUpperCase()}                           ║
╠════════════════════════════════════════════════════════════╣
║  ✅ Success: ${successCount.toString().padEnd(3)} elements translated                  ║
║  ❌ Errors:  ${errorCount.toString().padEnd(3)} elements failed                       ║
║  📊 Total:   ${elements.length.toString().padEnd(3)} elements processed                   ║
╚════════════════════════════════════════════════════════════╝
            `);
            
            // Hata varsa detaylı göster
            if (errors.length > 0) {
                console.warn('[i18n] ⚠️ Translation errors:', errors);
            }
            
            // Başarı oranı
            const successRate = elements.length > 0 ? (successCount / elements.length * 100).toFixed(1) : 0;
            if (successRate < 100) {
                console.warn(`[i18n] ⚠️ Success rate: ${successRate}% - Some translations may be missing!`);
            } else {
                console.log(`[i18n] ✅ Perfect! 100% translation success rate`);
            }
            
        } catch (error) {
            console.error('[i18n] ❌ Critical error in translatePage:', error);
        }
    }

    /**
     * Page title'ı güncelle
     */
    updatePageTitle() {
        const path = window.location.pathname;
        
        // Call page
        if (path.includes('/guest/call')) {
            document.title = `${this.t('call.title')} - ${this.t('brand.name')}`;
        }
        // Status page
        else if (path.includes('/guest/status')) {
            document.title = `${this.t('status.title')} - ${this.t('brand.name')}`;
        }
        // Demo page
        else if (path.includes('/guest/language-demo')) {
            document.title = `Multi-Language Demo - ${this.t('brand.name')}`;
        }
    }

    /**
     * Dil değiştir
     */
    changeLanguage(lang) {
        if (!this.isSupported(lang)) {
            console.warn(`[i18n] Language not supported: ${lang}`);
            return;
        }

        this.currentLang = lang;
        localStorage.setItem('guest_language', lang);
        
        // RTL güncelle
        if (lang === 'ar') {
            document.documentElement.setAttribute('dir', 'rtl');
            document.documentElement.setAttribute('lang', 'ar');
        } else {
            document.documentElement.setAttribute('dir', 'ltr');
            document.documentElement.setAttribute('lang', lang);
        }

        // Sayfayı yeniden çevir (title dahil)
        this.translatePage();

        console.log(`[i18n] Language changed to: ${lang}`);
    }

    /**
     * Dil değiştirici ekle
     */
    addLanguageSwitcher() {
        const languages = [
            { code: 'tr', name: 'Türkçe', flag: '/static/flags/tr.svg' },
            { code: 'en', name: 'English', flag: '/static/flags/gb-eng.svg' },
            { code: 'de', name: 'Deutsch', flag: '/static/flags/de.svg' },
            { code: 'ru', name: 'Русский', flag: '/static/flags/ru.svg' },
            { code: 'ar', name: 'العربية', flag: '/static/flags/sa.svg' }
        ];

        // Font Awesome için CDN ekle (eğer yoksa)
        if (!document.querySelector('link[href*="font-awesome"]')) {
            const faLink = document.createElement('link');
            faLink.rel = 'stylesheet';
            faLink.href = 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css';
            document.head.appendChild(faLink);
        }

        const switcher = document.createElement('div');
        switcher.className = 'language-switcher';
        switcher.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
            padding: 8px;
        `;

        const currentLang = languages.find(l => l.code === this.currentLang);
        
        switcher.innerHTML = `
            <button class="lang-toggle" style="
                background: transparent;
                border: none;
                cursor: pointer;
                padding: 8px;
                display: flex;
                align-items: center;
                gap: 8px;
                border-radius: 8px;
                transition: background 0.2s;
            " onmouseover="this.style.background='#f0f9ff'" onmouseout="this.style.background='transparent'">
                <img src="${currentLang.flag}" alt="${currentLang.name}" style="
                    width: 32px;
                    height: 32px;
                    border-radius: 4px;
                    object-fit: cover;
                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                ">
            </button>
            <div class="lang-menu" style="
                display: none;
                position: absolute;
                top: 100%;
                right: 0;
                margin-top: 8px;
                background: white;
                border-radius: 12px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                padding: 8px;
                min-width: 180px;
            ">
                ${languages.map(lang => `
                    <button class="lang-option" data-lang="${lang.code}" style="
                        display: flex;
                        align-items: center;
                        gap: 12px;
                        width: 100%;
                        padding: 10px 12px;
                        border: none;
                        background: ${lang.code === this.currentLang ? '#f0f9ff' : 'transparent'};
                        border-radius: 8px;
                        cursor: pointer;
                        font-size: 14px;
                        text-align: left;
                        transition: all 0.2s;
                        ${lang.code === this.currentLang ? 'border: 2px solid #1BA5A8;' : 'border: 2px solid transparent;'}
                    " onmouseover="this.style.background='#f0f9ff'" onmouseout="this.style.background='${lang.code === this.currentLang ? '#f0f9ff' : 'transparent'}'">
                        <img src="${lang.flag}" alt="${lang.name}" style="
                            width: 24px;
                            height: 24px;
                            border-radius: 4px;
                            object-fit: cover;
                            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
                        ">
                        <span style="font-weight: ${lang.code === this.currentLang ? '600' : '400'};">${lang.name}</span>
                        ${lang.code === this.currentLang ? '<i class="fas fa-check" style="margin-left: auto; color: #1BA5A8;"></i>' : ''}
                    </button>
                `).join('')}
            </div>
        `;

        document.body.appendChild(switcher);

        // Toggle menu
        const toggle = switcher.querySelector('.lang-toggle');
        const menu = switcher.querySelector('.lang-menu');
        
        toggle.addEventListener('click', () => {
            menu.style.display = menu.style.display === 'none' ? 'block' : 'none';
        });

        // Close menu when clicking outside
        document.addEventListener('click', (e) => {
            if (!switcher.contains(e.target)) {
                menu.style.display = 'none';
            }
        });

        // Language selection
        switcher.querySelectorAll('.lang-option').forEach(option => {
            option.addEventListener('click', () => {
                const lang = option.getAttribute('data-lang');
                this.changeLanguage(lang);
                menu.style.display = 'none';
                
                // Update toggle button with new flag
                const newLang = languages.find(l => l.code === lang);
                toggle.innerHTML = `
                    <img src="${newLang.flag}" alt="${newLang.name}" style="
                        width: 32px;
                        height: 32px;
                        border-radius: 4px;
                        object-fit: cover;
                        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                    ">
                `;
                
                // Update menu items (highlight selected)
                switcher.querySelectorAll('.lang-option').forEach(opt => {
                    const optLang = opt.getAttribute('data-lang');
                    if (optLang === lang) {
                        opt.style.background = '#f0f9ff';
                        opt.style.border = '2px solid #1BA5A8';
                        opt.querySelector('span').style.fontWeight = '600';
                        if (!opt.querySelector('.fa-check')) {
                            opt.innerHTML += '<i class="fas fa-check" style="margin-left: auto; color: #1BA5A8;"></i>';
                        }
                    } else {
                        opt.style.background = 'transparent';
                        opt.style.border = '2px solid transparent';
                        opt.querySelector('span').style.fontWeight = '400';
                        const checkIcon = opt.querySelector('.fa-check');
                        if (checkIcon) {
                            checkIcon.remove();
                        }
                    }
                });
            });
        });
    }
}

// Global instance
window.guestI18n = new GuestI18n();

// Global test fonksiyonu
window.testI18n = function() {
 
    
    const languages = ['tr', 'en', 'de', 'ru', 'ar'];
    const testKeys = [
        'brand.name',
        'call.title',
        'call.call_shuttle',
        'status.pending',
        'confirm.title'
    ];
    
    
    languages.forEach(lang => {
        console.log(`\n📍 ${lang.toUpperCase()}:`);
        window.guestI18n.currentLang = lang;
        
        testKeys.forEach(key => {
            const translation = window.guestI18n.t(key);
            const status = translation !== key ? '✅' : '❌';
        });
    });
    
    const report = window.guestI18n.validateTranslations();
    

    return report;
};

// Force refresh fonksiyonu
window.forceTranslate = function() {
    window.guestI18n.translatePage();
};

// Dil değiştir ve zorla yenile
window.switchLanguage = function(lang) {
    console.log(`🌍 Switching to ${lang.toUpperCase()}...`);
    window.guestI18n.changeLanguage(lang);
    
    // Biraz bekle ve zorla yenile
    setTimeout(() => {
        window.forceTranslate();
    }, 100);
};

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = GuestI18n;
}
  
