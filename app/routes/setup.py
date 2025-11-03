"""
Buggy Call - Setup Wizard Routes
Initial setup for new installations
"""
from flask import Blueprint, jsonify, request, render_template
from app import db
from app.models.hotel import Hotel
from app.models.user import SystemUser, UserRole
from app.middleware.setup_check import is_setup_completed, mark_setup_completed
from app.utils.exceptions import BuggyCallException

setup_bp = Blueprint('setup', __name__)


@setup_bp.route('/setup', methods=['GET'])
def setup_page():
    """Setup wizard page"""
    if is_setup_completed():
        return render_template('error.html', 
            error='Setup already completed',
            message='Kurulum zaten tamamlanmış. Giriş sayfasına yönlendiriliyorsunuz...',
            redirect='/auth/login'
        ), 400
    
    return render_template('setup/index.html')


@setup_bp.route('/api/setup/check', methods=['GET'])
def check_setup():
    """Check if setup is completed"""
    return jsonify({
        'setup_completed': is_setup_completed()
    })


@setup_bp.route('/api/setup/hotel', methods=['POST'])
def setup_hotel():
    """Create hotel during setup"""
    try:
        if is_setup_completed():
            return jsonify({'error': 'Setup already completed'}), 400
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'code']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        # Check if hotel already exists
        existing_hotel = Hotel.query.filter_by(code=data['code']).first()
        if existing_hotel:
            return jsonify({'error': 'Hotel code already exists'}), 400
        
        # Create hotel
        hotel = Hotel(
            name=data['name'],
            code=data['code'],
            address=data.get('address'),
            phone=data.get('phone'),
            email=data.get('email'),
            timezone=data.get('timezone', 'Europe/Istanbul')
        )
        
        db.session.add(hotel)
        db.session.commit()
        
        # Log hotel creation
        from app.services.audit_service import AuditService
        AuditService.log_action(
            action='hotel_created',
            entity_type='hotel',
            entity_id=hotel.id,
            new_values=hotel.to_dict(),
            hotel_id=hotel.id
        )
        
        return jsonify({
            'success': True,
            'message': 'Hotel created successfully',
            'hotel': hotel.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@setup_bp.route('/api/setup/admin', methods=['POST'])
def setup_admin():
    """Create admin account during setup"""
    try:
        if is_setup_completed():
            return jsonify({'error': 'Setup already completed'}), 400
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['hotel_id', 'username', 'password', 'full_name']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        # Check if hotel exists
        hotel = Hotel.query.get(data['hotel_id'])
        if not hotel:
            return jsonify({'error': 'Hotel not found'}), 404
        
        # Check if username already exists
        existing_user = SystemUser.query.filter_by(username=data['username']).first()
        if existing_user:
            return jsonify({'error': 'Username already exists'}), 400
        
        # Create admin user
        admin = SystemUser(
            hotel_id=data['hotel_id'],
            username=data['username'],
            role=UserRole.ADMIN,
            full_name=data['full_name'],
            email=data.get('email'),
            phone=data.get('phone'),
            is_active=True
        )
        admin.set_password(data['password'])
        
        db.session.add(admin)
        db.session.commit()
        
        # Log admin creation
        from app.services.audit_service import AuditService
        AuditService.log_action(
            action='admin_created_during_setup',
            entity_type='user',
            entity_id=admin.id,
            new_values=admin.to_dict(),
            user_id=admin.id,
            hotel_id=admin.hotel_id
        )
        
        return jsonify({
            'success': True,
            'message': 'Admin account created successfully',
            'user': admin.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@setup_bp.route('/api/setup/complete', methods=['POST'])
def complete_setup():
    """Mark setup as completed"""
    try:
        if is_setup_completed():
            return jsonify({'error': 'Setup already completed'}), 400
        
        # Verify that at least one hotel and one admin exist
        hotel_count = Hotel.query.count()
        admin_count = SystemUser.query.filter_by(role=UserRole.ADMIN).count()
        
        if hotel_count == 0:
            return jsonify({'error': 'No hotel created. Please create a hotel first.'}), 400
        
        if admin_count == 0:
            return jsonify({'error': 'No admin account created. Please create an admin account first.'}), 400
        
        # Mark setup as completed
        mark_setup_completed()
        
        # Log setup completion
        from app.services.audit_service import AuditService
        AuditService.log_action(
            action='system_setup_completed',
            entity_type='system',
            new_values={
                'hotel_count': hotel_count,
                'admin_count': admin_count,
                'ip_address': request.remote_addr
            }
        )
        
        return jsonify({
            'success': True,
            'message': 'Setup completed successfully',
            'redirect': '/login'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@setup_bp.route('/api/setup/reset', methods=['POST'])
def reset_setup():
    """Reset setup (for development only)"""
    try:
        import os
        
        # Only allow in development mode
        if os.getenv('FLASK_ENV') != 'development':
            return jsonify({'error': 'Only available in development mode'}), 403
        
        # Remove setup marker
        setup_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.setup_completed')
        if os.path.exists(setup_file):
            os.remove(setup_file)
        
        return jsonify({
            'success': True,
            'message': 'Setup reset successfully'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
