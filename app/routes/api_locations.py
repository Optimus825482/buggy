"""
Buggy Call - Locations API Routes
Extracted from api.py for modularity
"""
from flask import Blueprint, jsonify, request, session, current_app, send_file
from app import db
from app.models.user import SystemUser
from app.models.location import Location
from app.services import LocationService
from app.utils import APIResponse, require_login
from app.utils.exceptions import BuggyCallException, ResourceNotFoundException, ValidationException
import qrcode
import io
import base64
import os
import uuid
import logging

api_locations_bp = Blueprint('api_locations', __name__)
logger = logging.getLogger(__name__)

# Upload configuration
UPLOAD_FOLDER = 'app/static/uploads/locations'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def save_location_image(file):
    try:
        if not file or file.filename == '':
            logger.warning("No file provided")
            return None

        if not allowed_file(file.filename):
            raise ValueError('Geçersiz dosya formatı. Sadece PNG, JPG, JPEG, GIF, WEBP desteklenir.')

        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)

        if file_size > MAX_FILE_SIZE:
            raise ValueError('Dosya boyutu 5MB\'dan büyük olamaz.')

        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{uuid.uuid4().hex}.{ext}"
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        return f"/static/uploads/locations/{filename}"
    except Exception as e:
        logger.error(f"Error saving location image: {str(e)}")
        raise


def delete_location_image(image_path):
    if not image_path or not image_path.startswith('/static/uploads/locations/'):
        return
    try:
        filepath = os.path.join('app', image_path.lstrip('/'))
        if os.path.exists(filepath):
            os.remove(filepath)
    except Exception as e:
        print(f"Error deleting image {image_path}: {e}")


@api_locations_bp.route('/api/locations', methods=['GET'])
def get_locations():
    """Get all locations (Public - no auth required for guests)"""
    try:
        hotel_id = request.args.get('hotel_id', type=int)
        if not hotel_id and 'user_id' in session:
            from app.utils.helpers import RequestContext
            hotel_id = RequestContext.get_current_hotel_id()
        hotel_id = hotel_id or 1

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)

        result = LocationService.get_all_locations(
            hotel_id=hotel_id, include_inactive=False,
            page=page, per_page=per_page
        )
        response_data = result.copy()
        response_data['locations'] = result['items']
        return APIResponse.success(response_data)
    except BuggyCallException as e:
        return jsonify(e.to_dict()), e.status_code
    except Exception as e:
        return APIResponse.error(str(e), 500)


@api_locations_bp.route('/api/locations/<int:location_id>', methods=['GET'])
def get_location(location_id):
    try:
        location = LocationService.get_location(location_id)
        return APIResponse.success({'location': location.to_dict()})
    except BuggyCallException as e:
        return jsonify(e.to_dict()), e.status_code
    except Exception as e:
        return APIResponse.error(str(e), 500)


@api_locations_bp.route('/api/locations', methods=['POST'])
@require_login
def create_location():
    try:
        user = SystemUser.query.get(session['user_id'])
        if request.files:
            data = request.form.to_dict()
            image_file = request.files.get('location_image')
        else:
            data = request.get_json()
            image_file = None

        if not data.get('name'):
            return jsonify({'error': 'Lokasyon adı gerekli'}), 400

        # Check duplicate name via LocationService
        from app.services.location_service import LocationService
        existing = db.session.query(Location.id).filter_by(
            hotel_id=user.hotel_id, name=data['name']
        ).first()
        if existing:
            return jsonify({'error': f'Lokasyon adı "{data["name"]}" bu otel için zaten kullanılıyor'}), 400

        if 'display_order' not in data or data['display_order'] is None or data['display_order'] == '' or int(data.get('display_order', 0)) == 0:
            max_order = db.session.query(db.func.max(Location.display_order)).filter_by(hotel_id=user.hotel_id).scalar() or 0
            data['display_order'] = max_order + 1

        location_image_path = None
        if image_file:
            try:
                location_image_path = save_location_image(image_file)
            except ValueError as e:
                return jsonify({'error': str(e)}), 400
        elif data.get('location_image'):
            location_image_path = data.get('location_image')

        location = Location(
            hotel_id=user.hotel_id, name=data['name'],
            description=data.get('description', ''), qr_code_data='',
            location_image=location_image_path,
            latitude=float(data['latitude']) if data.get('latitude') else None,
            longitude=float(data['longitude']) if data.get('longitude') else None,
            is_active=True, display_order=int(data['display_order'])
        )
        db.session.add(location)
        db.session.flush()

        # Generate QR code URL with location ID
        railway_domain = os.getenv('RAILWAY_PUBLIC_DOMAIN')
        railway_static_url = os.getenv('RAILWAY_STATIC_URL')
        if railway_domain:
            base_url = f"https://{railway_domain}"
        elif railway_static_url:
            base_url = railway_static_url.rstrip('/')
        elif request.host.startswith('localhost') or request.host.startswith('127.0.0.1'):
            base_url = "http://192.168.1.100:5000"
        elif current_app.config.get('BASE_URL') and current_app.config.get('BASE_URL') != 'http://localhost:5000':
            base_url = current_app.config.get('BASE_URL')
        else:
            base_url = request.host_url.rstrip('/')

        qr_code_data = f"{base_url}/guest/call?l={location.id}"
        location.qr_code_data = qr_code_data

        qr = qrcode.QRCode(version=1, box_size=2, border=0)
        qr.add_data(qr_code_data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        location.qr_code_image = f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"

        db.session.commit()
        return jsonify({'success': True, 'message': 'Lokasyon başarıyla oluşturuldu', 'location': location.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@api_locations_bp.route('/api/locations/<int:location_id>', methods=['PUT'])
@require_login
def update_location(location_id):
    try:
        user = SystemUser.query.get(session['user_id'])
        location = Location.query.filter_by(id=location_id, hotel_id=user.hotel_id).first()
        if not location:
            return jsonify({'error': 'Lokasyon bulunamadı'}), 404

        content_type = request.content_type or ''
        if 'multipart/form-data' in content_type:
            data = request.form.to_dict()
            image_file = request.files.get('location_image')
        elif 'application/json' in content_type:
            data = request.get_json() or {}
            image_file = None
        else:
            data = request.form.to_dict() if request.form else (request.get_json() or {})
            image_file = request.files.get('location_image') if request.files else None

        if 'name' in data:
            location.name = data['name']
        if 'description' in data:
            location.description = data['description']

        if image_file and image_file.filename:
            if location.location_image and location.location_image.startswith('/static/uploads/'):
                delete_location_image(location.location_image)
            try:
                new_image_path = save_location_image(image_file)
                if new_image_path:
                    location.location_image = new_image_path
            except ValueError as e:
                return jsonify({'error': str(e)}), 400
        elif 'location_image' in data:
            if data['location_image'] in ('', 'null', 'undefined'):
                if location.location_image and location.location_image.startswith('/static/uploads/'):
                    delete_location_image(location.location_image)
                location.location_image = None
            elif data['location_image'] and data['location_image'].startswith('data:image'):
                location.location_image = data['location_image']

        if 'latitude' in data:
            location.latitude = float(data['latitude']) if data['latitude'] else None
        if 'longitude' in data:
            location.longitude = float(data['longitude']) if data['longitude'] else None
        if 'is_active' in data:
            if isinstance(data['is_active'], bool):
                location.is_active = data['is_active']
            elif isinstance(data['is_active'], str):
                location.is_active = data['is_active'].lower() in ('true', '1', 'yes')
            else:
                location.is_active = bool(data['is_active'])
        if 'display_order' in data:
            location.display_order = int(data['display_order'])

        regenerate_qr = data.get('regenerate_qr', 'false').lower() == 'true' or 'name' in data
        if regenerate_qr:
            railway_domain = os.getenv('RAILWAY_PUBLIC_DOMAIN')
            railway_static_url = os.getenv('RAILWAY_STATIC_URL')
            if railway_domain:
                base_url = f"https://{railway_domain}"
            elif railway_static_url:
                base_url = railway_static_url.rstrip('/')
            elif request.host.startswith('localhost') or request.host.startswith('127.0.0.1'):
                base_url = "http://192.168.1.100:5000"
            elif current_app.config.get('BASE_URL') and current_app.config.get('BASE_URL') != 'http://localhost:5000':
                base_url = current_app.config.get('BASE_URL')
            else:
                base_url = request.host_url.rstrip('/')

            qr_code_data = f"{base_url}/guest/call?l={location.id}"
            location.qr_code_data = qr_code_data
            qr = qrcode.QRCode(version=1, box_size=2, border=0)
            qr.add_data(qr_code_data)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            location.qr_code_image = f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"

        db.session.commit()
        return jsonify({'success': True, 'message': 'Lokasyon başarıyla güncellendi', 'location': location.to_dict(), 'qr_regenerated': regenerate_qr}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Location update error: {str(e)}')
        return jsonify({'error': str(e)}), 500


@api_locations_bp.route('/api/locations/<int:location_id>/regenerate-qr', methods=['POST'])
@require_login
def regenerate_qr_code(location_id):
    try:
        user = SystemUser.query.get(session['user_id'])
        location = Location.query.filter_by(id=location_id, hotel_id=user.hotel_id).first()
        if not location:
            return jsonify({'error': 'Lokasyon bulunamadı'}), 404

        railway_domain = os.getenv('RAILWAY_PUBLIC_DOMAIN')
        railway_static_url = os.getenv('RAILWAY_STATIC_URL')
        if railway_domain:
            base_url = f"https://{railway_domain}"
        elif railway_static_url:
            base_url = railway_static_url.rstrip('/')
        elif request.host.startswith('localhost') or request.host.startswith('127.0.0.1'):
            base_url = "http://192.168.1.100:5000"
        elif current_app.config.get('BASE_URL') and current_app.config.get('BASE_URL') != 'http://localhost:5000':
            base_url = current_app.config.get('BASE_URL')
        else:
            base_url = request.host_url.rstrip('/')

        qr_code_data = f"{base_url}/guest/call?l={location.id}"
        location.qr_code_data = qr_code_data
        qr = qrcode.QRCode(version=1, box_size=2, border=0)
        qr.add_data(qr_code_data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        location.qr_code_image = f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"

        db.session.commit()
        return jsonify({'success': True, 'message': 'QR kod başarıyla yenilendi', 'location': location.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'QR regeneration error: {str(e)}')
        return jsonify({'error': str(e)}), 500


@api_locations_bp.route('/api/locations/<int:location_id>', methods=['DELETE'])
@require_login
def delete_location(location_id):
    try:
        user = SystemUser.query.get(session['user_id'])
        location = Location.query.filter_by(id=location_id, hotel_id=user.hotel_id).first()
        if not location:
            return jsonify({'error': 'Lokasyon bulunamadı'}), 404

        if location.location_image and location.location_image.startswith('/static/uploads/'):
            delete_location_image(location.location_image)

        LocationService.delete_location(location_id)
        return jsonify({'success': True, 'message': 'Lokasyon başarıyla silindi'}), 200
    except ResourceNotFoundException as e:
        return jsonify({'error': e.message}), 404
    except ValidationException as e:
        return jsonify({'error': e.message}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Lokasyon silinirken hata oluştu: {str(e)}'}), 500


@api_locations_bp.route('/api/locations/<int:location_id>/qr-code', methods=['GET'])
def download_qr_code(location_id):
    try:
        location = Location.query.get(location_id)
        if not location:
            return jsonify({'error': 'Lokasyon bulunamadı'}), 404

        qr = qrcode.QRCode(version=1, box_size=2, border=0, error_correction=qrcode.constants.ERROR_CORRECT_L)
        qr.add_data(location.qr_code_data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)

        return send_file(buffer, mimetype='image/png', as_attachment=True,
                        download_name=f'QR_{location.name.replace(" ", "_")}.png')
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_locations_bp.route('/api/locations/<int:location_id>/qr-svg', methods=['GET'])
def download_qr_svg(location_id):
    try:
        location = Location.query.get(location_id)
        if not location:
            return jsonify({'error': 'Lokasyon bulunamadı'}), 404

        from app.services.qr_service import QRCodeService
        import qrcode.constants
        svg_bytes, _ = QRCodeService.generate_qr_code(
            data=location.qr_code_data, box_size=2, border=0,
            error_correction=qrcode.constants.ERROR_CORRECT_L, format='svg'
        )
        buffer = io.BytesIO(svg_bytes)
        buffer.seek(0)
        return send_file(buffer, mimetype='image/svg+xml', as_attachment=True,
                        download_name=f'QR_{location.name.replace(" ", "_")}.svg')
    except Exception as e:
        logging.error(f"SVG QR kod oluşturma hatası: {str(e)}")
        return jsonify({'error': str(e)}), 500
