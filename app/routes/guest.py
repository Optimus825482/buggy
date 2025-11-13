"""
Buggy Call - Guest Routes
"""
from flask import Blueprint, render_template, request

guest_bp = Blueprint('guest', __name__)


@guest_bp.route('/call')
def call():
    """Guest buggy call page with premium features (QR scanner, manual location)"""
    # Kısa parametreleri destekle: l=location, h=hotel
    location_id = request.args.get('l') or request.args.get('location') or request.args.get('loc')
    hotel_id = request.args.get('h') or request.args.get('hotel', 1)  # Default hotel_id=1
    return render_template('guest/call_premium.html', location_id=location_id, hotel_id=hotel_id)


@guest_bp.route('/status/<int:request_id>')
def status(request_id):
    """Track request status"""
    return render_template('guest/status_premium.html', request_id=request_id)


@guest_bp.route('/test-qr')
def test_qr():
    """Test QR code page - shows latest QR code for testing"""
    return render_template('test_qr.html')
