"""
Buggy Call - Authentication Routes
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from app import db, csrf
from app.models.user import SystemUser
from datetime import datetime

auth_bp = Blueprint('auth', __name__)

# Note: CSRF protection strategy:
# - JSON API requests (Content-Type: application/json) are automatically exempt
# - HTML form submissions will require CSRF token
# We exempt the entire blueprint since login uses JSON
csrf.exempt(auth_bp)


@auth_bp.route('/login', methods=['GET'])
def login_page():
    """Render login page"""
    return render_template('auth/login.html')


@auth_bp.route('/login', methods=['POST'])
# Rate limiter disabled for high-traffic hotel environments
# @limiter.limit("5 per minute")  # Rate limit: 5 login attempts per minute
def login():
    """Handle login"""
    from app.services import AuthService
    from app.utils import APIResponse, validate_schema
    from app.schemas import UserLoginSchema
    from app.utils.exceptions import BuggyCallException
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
    
    try:
        # Get data
        data = request.get_json() if request.is_json else request.form
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return APIResponse.error('Kullanıcı adı ve şifre gerekli', 400)
        
        # Login via service
        user = AuthService.login(username, password)
        
        # Create tokens for API usage
        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)
        
        response_data = {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user.to_dict()
        }
        
        # Check if user must change password
        if user.must_change_password:
            if request.is_json:
                return jsonify({
                    'success': False,
                    'must_change_password': True,
                    'message': 'Şifrenizi değiştirmeniz gerekiyor',
                    'user_id': user.id
                }), 200
            else:
                # Redirect to change password page
                return redirect(url_for('auth.change_password'))
        
        if request.is_json:
            # Return success with data at root level for easier access
            return jsonify({
                'success': True,
                'message': 'Giriş başarılı',
                'access_token': access_token,
                'refresh_token': refresh_token,
                'user': user.to_dict()
            }), 200
        else:
            # Redirect based on role
            user_role = user.role.value if hasattr(user.role, 'value') else str(user.role)
            if user_role == 'admin':
                return redirect(url_for('admin.dashboard'))
            else:
                # Check if driver needs to select location
                if session.get('needs_location_setup'):
                    return redirect(url_for('driver.select_location'))
                else:
                    return redirect(url_for('driver.dashboard'))
                
    except BuggyCallException as e:
        return jsonify(e.to_dict()), e.status_code
    except Exception as e:
        return APIResponse.error(str(e), 500)


@auth_bp.route('/change-password', methods=['GET'])
def change_password():
    """Render change password page"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login_page'))
    return render_template('auth/change_password.html')


@auth_bp.route('/change-password', methods=['POST'])
# Rate limiter removed for high-traffic hotel environments
def change_password_submit():
    """Handle password change"""
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Oturum bulunamadı'}), 401
        
        data = request.get_json() if request.is_json else request.form
        old_password = data.get('old_password')
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')
        
        if not old_password or not new_password or not confirm_password:
            return jsonify({'error': 'Tüm alanlar gerekli'}), 400
        
        if new_password != confirm_password:
            return jsonify({'error': 'Yeni şifreler eşleşmiyor'}), 400
        
        if len(new_password) < 6:
            return jsonify({'error': 'Şifre en az 6 karakter olmalı'}), 400
        
        # Get user
        user = SystemUser.query.get(session['user_id'])
        if not user:
            return jsonify({'error': 'Kullanıcı bulunamadı'}), 404
        
        # Check old password
        if not user.check_password(old_password):
            return jsonify({'error': 'Mevcut şifre yanlış'}), 400
        
        # Set new password
        user.set_password(new_password)
        user.must_change_password = False
        db.session.commit()
        
        if request.is_json:
            return jsonify({
                'success': True,
                'message': 'Şifre başarıyla değiştirildi'
            }), 200
        else:
            # Redirect based on role
            user_role = user.role.value if hasattr(user.role, 'value') else str(user.role)
            if user_role == 'admin':
                return redirect(url_for('admin.dashboard'))
            else:
                return redirect(url_for('driver.dashboard'))
                
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/logout', methods=['POST', 'GET'])
def logout():
    """Handle logout"""
    from app.services import AuthService
    from app.utils import APIResponse
    
    try:
        # Logout via service
        AuthService.logout()
        
        if request.is_json or request.method == 'POST':
            response = APIResponse.success(message='Başarıyla çıkış yapıldı')
            # Clear session cookie explicitly
            response.set_cookie('buggycall_session', '', expires=0, httponly=True, samesite='Lax')
            return response
        else:
            flash('Başarıyla çıkış yaptınız', 'success')
            response = redirect(url_for('auth.login'))
            # Clear session cookie explicitly
            response.set_cookie('buggycall_session', '', expires=0, httponly=True, samesite='Lax')
            return response
    except Exception as e:
        return APIResponse.error(str(e), 500)


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token"""
    try:
        identity = get_jwt_identity()
        access_token = create_access_token(identity=identity)
        return jsonify({'access_token': access_token}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
