"""
Buggy Call - Driver Routes
"""
from flask import Blueprint, render_template, redirect, url_for, flash, session
from functools import wraps
from app.models.user import SystemUser

driver_bp = Blueprint('driver', __name__)


def driver_required(fn):
    """
    ✅ PERFORMANS OPTİMİZE: Cache'den user al
    Decorator to require driver role
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        # Check session first
        if 'user_id' not in session:
            flash('Lütfen giriş yapın', 'warning')
            return redirect(url_for('auth.login'))
        
        # ✅ Cache'den user al (DB sorgusu yerine)
        from app.utils.decorators import get_current_user_cached
        user = get_current_user_cached()
        
        if not user:
            session.clear()
            flash('Kullanıcı bulunamadı', 'danger')
            return redirect(url_for('auth.login'))
        
        # Check if user is driver (handle both enum name and value)
        from app.models.user import UserRole
        if user.role != UserRole.DRIVER:
            flash('Bu sayfaya erişim yetkiniz yok', 'danger')
            return redirect(url_for('auth.login'))
        return fn(*args, **kwargs)
    return wrapper


@driver_bp.route('/select-location')
@driver_required
def select_location():
    """Location selection page for drivers"""
    try:
        # Check if driver actually needs to select location
        if not session.get('needs_location_setup'):
            return redirect(url_for('driver.dashboard'))
        
        # Cache'den user al
        from app.utils.decorators import get_current_user_cached
        user = get_current_user_cached()
        
        # Sürücüye buggy atanmış mı kontrol et
        if not user or not user.buggy:
            flash('Size henüz bir buggy atanmamış. Lütfen yöneticinizle iletişime geçin.', 'warning')
            session.pop('needs_location_setup', None)
            return redirect(url_for('auth.login'))
        
        # Pass session data explicitly to avoid linter issues
        return render_template(
            'driver/select_location.html',
            hotel_id=session.get('hotel_id', 1),
            user_id=session.get('user_id', 0)
        )
    except Exception as e:
        import logging
        logging.error(f"Lokasyon seçim hatası: {str(e)}")
        flash('Bir hata oluştu. Lütfen tekrar deneyin.', 'danger')
        return redirect(url_for('auth.login'))


@driver_bp.route('/dashboard')
@driver_required
def dashboard():
    """Driver dashboard"""
    try:
        # ✅ Cache'den user al
        from app.utils.decorators import get_current_user_cached
        user = get_current_user_cached()
        
        if not user:
            flash('Kullanıcı bilgisi alınamadı', 'danger')
            return redirect(url_for('auth.login'))
        
        # CRITICAL: Ensure driver session is non-permanent
        # This forces session to expire when browser closes
        if session.permanent:
            print(f'[DRIVER_DASHBOARD] WARNING: Driver session was permanent, fixing...')
            session.permanent = False
        
        # Check if user must change password
        if user.must_change_password:
            return redirect(url_for('auth.change_password'))
        
        # Sürücüye buggy atanmış mı kontrol et
        if not user.buggy:
            flash('Size henüz bir buggy atanmamış. Lütfen yöneticinizle iletişime geçin.', 'warning')
            session.clear()
            return redirect(url_for('auth.login'))
        
        # Check if driver needs to set initial location (ALWAYS after login)
        if session.get('needs_location_setup', False):
            return redirect(url_for('driver.select_location'))
        
        # If somehow location is missing, redirect to location setup
        if not user.buggy.current_location_id:
            session['needs_location_setup'] = True
            return redirect(url_for('driver.select_location'))
        
        return render_template('driver/dashboard.html', 
                             user=user,
                             notification_permission_asked=session.get('notification_permission_asked', False),
                             notification_permission_status=session.get('notification_permission_status', 'default'))
    except Exception as e:
        import logging
        logging.error(f"Dashboard hatası: {str(e)}")
        flash('Dashboard yüklenirken bir hata oluştu', 'danger')
        return redirect(url_for('auth.login'))
