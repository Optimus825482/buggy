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


@driver_bp.route('/dashboard')
@driver_required
def dashboard():
    """Driver dashboard"""
    user = SystemUser.query.get(session['user_id'])
    
    # Check if user must change password
    if user.must_change_password:
        return redirect(url_for('auth.change_password'))
    
    # Check if driver has buggy and needs to set initial location
    if user.buggy and not user.buggy.current_location_id:
        session['needs_location_setup'] = True
    
    return render_template('driver/dashboard.html', user=user)
