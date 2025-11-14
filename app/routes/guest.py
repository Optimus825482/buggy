"""
Buggy Call - Guest Routes
"""
from flask import Blueprint, render_template, request, current_app

guest_bp = Blueprint('guest', __name__)


@guest_bp.route('/call')
def call():
    """Guest buggy call page with premium features (QR scanner, manual location)"""
    # Kısa parametreleri destekle: l=location, h=hotel
    location_id = request.args.get('l') or request.args.get('location') or request.args.get('loc')
    hotel_id = request.args.get('h') or request.args.get('hotel', 1)  # Default hotel_id=1
    
    # VAPID public key'i gönder (push notifications için)
    vapid_public_key = current_app.config.get('VAPID_PUBLIC_KEY', '')
    firebase_vapid_key = current_app.config.get('FIREBASE_VAPID_KEY', '')
    
    return render_template('guest/call_premium.html', 
                         location_id=location_id, 
                         hotel_id=hotel_id,
                         vapid_public_key=vapid_public_key,
                         firebase_vapid_key=firebase_vapid_key)


@guest_bp.route('/status/<int:request_id>')
def status(request_id):
    """Track request status"""
    return render_template('guest/status_premium.html', request_id=request_id)


@guest_bp.route('/test-qr')
def test_qr():
    """Test QR code page - shows latest QR code for testing"""
    return render_template('test_qr.html')


@guest_bp.route('/language-demo')
def language_demo():
    """Multi-language support demo page"""
    return render_template('guest/language_demo.html')
