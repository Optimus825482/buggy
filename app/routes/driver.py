"""
Buggy Call - Driver Routes
"""
from flask import Blueprint, render_template, redirect, url_for, flash, session
from functools import wraps
from app.models.user import SystemUser

driver_bp = Blueprint('driver', __name__)


def driver_required(fn):
    """Decorator to require driver role"""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        # Check session first
        if 'user_id' not in session:
            flash('Lütfen giriş yapın', 'warning')
            return redirect(url_for('auth.login'))
        
        user = SystemUser.query.get(session['user_id'])
        if not user:
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
    # Check if driver actually needs to select location
    if not session.get('needs_location_setup'):
        return redirect(url_for('driver.dashboard'))
    
    # Pass session data explicitly to avoid linter issues
    return render_template(
        'driver/select_location.html',
        hotel_id=session.get('hotel_id', 1),
        user_id=session.get('user_id', 0)
    )


@driver_bp.route('/dashboard')
@driver_required
def dashboard():
    """Driver dashboard"""
    user = SystemUser.query.get(session['user_id'])
    
    # CRITICAL: Ensure driver session is non-permanent
    # This forces session to expire when browser closes
    if session.permanent:
        print(f'[DRIVER_DASHBOARD] WARNING: Driver session was permanent, fixing...')
        session.permanent = False
    
    # Check if user must change password
    if user.must_change_password:
        return redirect(url_for('auth.change_password'))
    
    # Check if driver needs to set initial location (ALWAYS after login)
    if session.get('needs_location_setup', False):
        return redirect(url_for('driver.select_location'))
    
    # If somehow location is missing, redirect to location setup
    if user.buggy and not user.buggy.current_location_id:
        session['needs_location_setup'] = True
        return redirect(url_for('driver.select_location'))
    
    return render_template('driver/dashboard.html', 
                         user=user,
                         notification_permission_asked=session.get('notification_permission_asked', False),
                         notification_permission_status=session.get('notification_permission_status', 'default'))
