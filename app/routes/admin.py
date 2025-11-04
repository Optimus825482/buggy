"""
Buggy Call - Admin Routes
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_jwt_extended import jwt_required, get_jwt_identity
from functools import wraps
from app import db
from app.models.user import SystemUser

admin_bp = Blueprint('admin', __name__)


def admin_required(fn):
    """Decorator to require admin role"""
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
        
        # Check if user is admin (handle both enum name and value)
        from app.models.user import UserRole
        if user.role != UserRole.ADMIN:
            flash('Bu sayfaya erişim yetkiniz yok', 'danger')
            return redirect(url_for('auth.login'))
        return fn(*args, **kwargs)
    return wrapper


@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    """Admin dashboard"""
    user = SystemUser.query.get(session['user_id'])
    return render_template('admin/dashboard.html', 
                         user=user,
                         notification_permission_asked=session.get('notification_permission_asked', False),
                         notification_permission_status=session.get('notification_permission_status', 'default'))


@admin_bp.route('/locations')
@admin_required
def locations():
    """Manage locations"""
    user = SystemUser.query.get(session['user_id'])
    return render_template('admin/locations.html', user=user)


@admin_bp.route('/buggies')
@admin_required
def buggies():
    """Manage buggies"""
    user = SystemUser.query.get(session['user_id'])
    return render_template('admin/buggies.html', user=user)


@admin_bp.route('/reports')
@admin_required
def reports():
    """View reports"""
    return render_template('admin/reports.html')


@admin_bp.route('/qr-print')
@admin_required
def qr_print():
    """QR codes print page"""
    user = SystemUser.query.get(session['user_id'])
    return render_template('admin/qr_print.html', user=user)
