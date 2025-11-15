"""
Shuttle Call - Application Constants
✅ CODE REFACTORING: Centralized constants for better maintainability
"""

# ==================== REQUEST STATUS MESSAGES ====================
REQUEST_STATUS_MESSAGES = {
    'accepted': {
        'title': '🎉 Shuttle Kabul Edildi!',
        'body': 'Shuttle size doğru geliyor. Buggy: {buggy_code}',
        'guest_message': 'Talebiniz kabul edildi'
    },
    'in_progress': {
        'title': '🚗 Shuttle Yolda!',
        'body': 'Sürücü konumunuza yaklaşıyor',
        'guest_message': 'Shuttle yolda'
    },
    'completed': {
        'title': '✅ Shuttle Ulaştı!',
        'body': 'İyi günler dileriz',
        'guest_message': 'Shuttle tamamlandı'
    },
    'cancelled': {
        'title': '❌ Talep İptal Edildi',
        'body': 'Shuttle talebiniz iptal edildi',
        'guest_message': 'Talep iptal edildi'
    },
    'pending': {
        'title': '⏳ Talep Beklemede',
        'body': 'Bir sürücü tarafından kabul edilmeyi bekliyor',
        'guest_message': 'Talebiniz beklemede'
    },
    'unanswered': {
        'title': '⚠️ Talep Cevaplanmadı',
        'body': 'Süre doldu - lütfen tekrar deneyin',
        'guest_message': 'Talep zaman aşımına uğradı'
    }
}

# ==================== ERROR MESSAGES ====================
ERROR_MESSAGES = {
    # Validation Errors
    'MISSING_FIELD': '{field} gerekli',
    'INVALID_VALUE': 'Geçersiz {field} değeri',
    'NOT_FOUND': '{entity} bulunamadı',
    'ALREADY_EXISTS': '{entity} zaten mevcut',

    # Authentication Errors
    'UNAUTHORIZED': 'Yetkilendirme gerekli',
    'FORBIDDEN': 'Bu işlem için yetkiniz yok',
    'INVALID_CREDENTIALS': 'Geçersiz kullanıcı adı veya şifre',
    'SESSION_EXPIRED': 'Oturumunuz sonlandırıldı',

    # Business Logic Errors
    'BUGGY_NOT_AVAILABLE': 'Buggy müsait değil',
    'REQUEST_ALREADY_ACCEPTED': 'Talep başka bir sürücü tarafından kabul edildi',
    'DRIVER_NO_BUGGY': 'Aktif buggy ataması bulunamadı',
    'LOCATION_REQUIRED': 'Önce konumunuzu ayarlayın',

    # System Errors
    'DATABASE_ERROR': 'Veritabanı hatası oluştu',
    'INTERNAL_ERROR': 'Sunucu hatası oluştu',
    'FCM_ERROR': 'Bildirim gönderilemedi',
    'WEBSOCKET_ERROR': 'Bağlantı hatası oluştu'
}

# ==================== SUCCESS MESSAGES ====================
SUCCESS_MESSAGES = {
    'REQUEST_CREATED': 'Buggy çağrınız alındı',
    'REQUEST_ACCEPTED': 'Talep kabul edildi',
    'REQUEST_COMPLETED': 'Talep tamamlandı',
    'REQUEST_CANCELLED': 'Talep iptal edildi',
    'TOKEN_REGISTERED': 'Bildirimler aktif edildi',
    'LOCATION_UPDATED': 'Konum güncellendi',
    'PASSWORD_CHANGED': 'Şifre başarıyla değiştirildi',
    'USER_CREATED': 'Kullanıcı oluşturuldu',
    'LOGOUT_SUCCESS': 'Çıkış başarılı'
}

# ==================== REQUEST STATUS VALUES ====================
class RequestStatus:
    PENDING = 'PENDING'
    ACCEPTED = 'ACCEPTED'
    COMPLETED = 'COMPLETED'
    CANCELLED = 'CANCELLED'
    UNANSWERED = 'UNANSWERED'

# ==================== BUGGY STATUS VALUES ====================
class BuggyStatus:
    AVAILABLE = 'AVAILABLE'
    BUSY = 'BUSY'
    OFFLINE = 'OFFLINE'

# ==================== USER ROLES ====================
class UserRole:
    ADMIN = 'ADMIN'
    DRIVER = 'DRIVER'

# ==================== TIME CONSTANTS ====================
REQUEST_TIMEOUT_SECONDS = 3600  # 1 hour
GUEST_TOKEN_TTL_SECONDS = 3600  # 1 hour
SESSION_CLEANUP_INTERVAL_MINUTES = 5
INACTIVE_DRIVER_THRESHOLD_MINUTES = 5

# ==================== PAGINATION ====================
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# ==================== NOTIFICATION PRIORITIES ====================
class NotificationPriority:
    HIGH = 'high'
    NORMAL = 'normal'
    LOW = 'low'

# ==================== HTTP STATUS CODES ====================
# For consistency across API responses
class HttpStatus:
    OK = 200
    CREATED = 201
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    CONFLICT = 409
    INTERNAL_ERROR = 500
