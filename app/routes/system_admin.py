"""
System Admin Setup Route
One-time admin creation endpoint for Railway deployment
"""
from flask import Blueprint, render_template, jsonify, request
from app import db
from app.models.hotel import Hotel
from app.models.user import SystemUser, UserRole

system_admin_bp = Blueprint('system_admin', __name__)


@system_admin_bp.route('/systemadmin', methods=['GET', 'POST'])
def system_admin():
    """System admin creation page"""
    
    if request.method == 'GET':
        # Check if admin already exists
        admin_exists = SystemUser.query.filter_by(username='admin').first() is not None
        
        return render_template('system_admin.html', admin_exists=admin_exists)
    
    # POST request - create admin
    try:
        # Check if admin already exists
        existing_admin = SystemUser.query.filter_by(username='admin').first()
        if existing_admin:
            return jsonify({
                'success': False,
                'message': 'Admin kullanıcısı zaten mevcut!'
            }), 400
        
        # Get or create hotel
        hotel = Hotel.query.first()
        if not hotel:
            hotel = Hotel(
                name='Buggy Call Hotel',
                code='HOTEL01'
            )
            db.session.add(hotel)
            db.session.flush()
        
        # Create admin user
        admin = SystemUser(
            hotel_id=hotel.id,
            username='admin',
            full_name='System Administrator',
            role=UserRole.ADMIN,
            email='admin@buggycall.com',
            is_active=True
        )
        admin.set_password('518518')
        
        db.session.add(admin)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Admin kullanıcısı başarıyla oluşturuldu!',
            'username': 'admin',
            'password': '518518'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Hata: {str(e)}'
        }), 500
