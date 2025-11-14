"""
Buggy Call - API Routes
Powered by Erkan ERDEM
Updated with Service Layer & Security
"""
from flask import Blueprint, jsonify, request, session, current_app
from app import db, csrf, socketio
from app.models.user import SystemUser, UserRole
from app.models.location import Location
from app.models.buggy import Buggy, BuggyStatus
from app.models.request import BuggyRequest, RequestStatus
from app.services import LocationService, BuggyService, RequestService, AuthService
from app.utils import APIResponse, require_login, require_role, validate_schema
from app.utils.exceptions import BuggyCallException
from app.utils.logger import logger, log_request_event, log_driver_event, log_websocket_event, log_api_call, log_error
from app.schemas import (
    LocationCreateSchema, LocationUpdateSchema,
    BuggyCreateSchema, BuggyUpdateSchema,
    BuggyRequestCreateSchema, BuggyRequestAcceptSchema,
    UserCreateSchema
)
from datetime import datetime
from werkzeug.utils import secure_filename
import qrcode
import io
import base64
import os
import uuid

api_bp = Blueprint('api', __name__)

# Exempt API endpoints from CSRF (using JWT/session instead)
csrf.exempt(api_bp)

# Upload configuration
UPLOAD_FOLDER = 'app/static/uploads/locations'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_location_image(file):
    """Save uploaded location image and return the file path"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        if not file or file.filename == '':
            logger.warning("No file provided")
            return None
        
        logger.info(f"Attempting to save file: {file.filename}")
        
        if not allowed_file(file.filename):
            logger.error(f"Invalid file format: {file.filename}")
            raise ValueError('Geçersiz dosya formatı. Sadece PNG, JPG, JPEG, GIF, WEBP desteklenir.')
        
        # Check file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        logger.info(f"File size: {file_size} bytes")
        
        if file_size > MAX_FILE_SIZE:
            logger.error(f"File too large: {file_size} bytes")
            raise ValueError('Dosya boyutu 5MB\'dan büyük olamaz.')
        
        # Generate unique filename
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{uuid.uuid4().hex}.{ext}"
        
        logger.info(f"Generated filename: {filename}")
        
        # Ensure upload directory exists
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        logger.info(f"Upload folder: {UPLOAD_FOLDER}")
        
        # Save file
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        logger.info(f"Saving to: {filepath}")
        
        file.save(filepath)
        
        # Verify file was saved
        if os.path.exists(filepath):
            logger.info(f"✅ File saved successfully: {filepath}")
        else:
            logger.error(f"❌ File not found after save: {filepath}")
            raise ValueError('Dosya kaydedilemedi')
        
        # Return relative path for database
        relative_path = f"/static/uploads/locations/{filename}"
        logger.info(f"Returning relative path: {relative_path}")
        return relative_path
        
    except Exception as e:
        logger.error(f"Error saving location image: {str(e)}")
        raise

def delete_location_image(image_path):
    """Delete location image file"""
    if not image_path or not image_path.startswith('/static/uploads/locations/'):
        return
    
    try:
        # Convert relative path to absolute
        filepath = os.path.join('app', image_path.lstrip('/'))
        if os.path.exists(filepath):
            os.remove(filepath)
    except Exception as e:
        print(f"Error deleting image {image_path}: {e}")


# ==================== Health & Info ====================
@api_bp.route('/health')
def health():
    """Basic health check endpoint - always returns 200"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'message': 'Buggy Call API is running'
    }), 200


@api_bp.route('/health/ready')
def health_ready():
    """Detailed readiness check with database validation"""
    try:
        from sqlalchemy import inspect
        
        # Test database connection
        db.session.execute('SELECT 1')
        
        # Get table information
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        
        # Check critical tables
        critical_tables = ['hotel', 'system_user', 'location', 'buggy', 'buggy_request']
        critical_tables_ok = all(table in tables for table in critical_tables)
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'checks': {
                'database': {
                    'status': 'healthy',
                    'table_count': len(tables),
                    'critical_tables_ok': critical_tables_ok
                },
                'application': {
                    'status': 'healthy'
                }
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(e),
            'checks': {
                'database': {
                    'status': 'unhealthy',
                    'error': str(e)
                }
            }
        }), 503


@api_bp.route('/version')
def version():
    """API version"""
    return jsonify({
        'version': '1.0.0',
        'name': 'Buggy Call API',
        'author': 'Erkan ERDEM'
    }), 200


# ==================== Locations API ====================
@api_bp.route('/locations', methods=['GET'])
# Rate limiter removed
def get_locations():
    """Get all locations (Public - no auth required for guests)"""
    try:
        # Get hotel_id from query params or session
        hotel_id = request.args.get('hotel_id', type=int)
        if not hotel_id and 'user_id' in session:
            from app.utils.helpers import RequestContext
            hotel_id = RequestContext.get_current_hotel_id()
        hotel_id = hotel_id or 1  # Default to hotel_id=1
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        result = LocationService.get_all_locations(
            hotel_id=hotel_id,
            include_inactive=False,
            page=page,
            per_page=per_page
        )
        
        # Return with both 'items' and 'locations' for backward compatibility
        response_data = result.copy()
        response_data['locations'] = result['items']
        
        return APIResponse.success(response_data)
    except BuggyCallException as e:
        return jsonify(e.to_dict()), e.status_code
    except Exception as e:
        return APIResponse.error(str(e), 500)


@api_bp.route('/locations/<int:location_id>', methods=['GET'])
# Rate limiter removed
def get_location(location_id):
    """Get single location (Public - no auth required for guests)"""
    try:
        location = LocationService.get_location(location_id)
        return APIResponse.success({'location': location.to_dict()})
    except BuggyCallException as e:
        return jsonify(e.to_dict()), e.status_code
    except Exception as e:
        return APIResponse.error(str(e), 500)


@api_bp.route('/locations', methods=['POST'])
@require_login
def create_location():
    """Create new location"""
    try:
        from app.config import Config
        
        user = SystemUser.query.get(session['user_id'])
        
        # Check if request has files (multipart/form-data)
        if request.files:
            # Form data with file upload
            data = request.form.to_dict()
            image_file = request.files.get('location_image')
        else:
            # JSON data (backward compatibility)
            data = request.get_json()
            image_file = None
        
        # Validate required fields
        if not data.get('name'):
            return jsonify({'error': 'Lokasyon adı gerekli'}), 400
        
        # Auto-assign display_order if not provided or is 0
        if 'display_order' not in data or data['display_order'] is None or data['display_order'] == '' or int(data.get('display_order', 0)) == 0:
            max_order = db.session.query(db.func.max(Location.display_order)).filter_by(hotel_id=user.hotel_id).scalar() or 0
            data['display_order'] = max_order + 1
        
        # Handle image upload
        location_image_path = None
        if image_file:
            try:
                location_image_path = save_location_image(image_file)
            except ValueError as e:
                return jsonify({'error': str(e)}), 400
        elif data.get('location_image'):
            # Backward compatibility: base64 image
            location_image_path = data.get('location_image')
        
        # Create location first to get the ID
        location = Location(
            hotel_id=user.hotel_id,
            name=data['name'],
            description=data.get('description', ''),
            qr_code_data='',  # Temporary, will be updated after we have the ID
            location_image=location_image_path,
            latitude=float(data['latitude']) if data.get('latitude') else None,
            longitude=float(data['longitude']) if data.get('longitude') else None,
            is_active=True,
            display_order=int(data['display_order'])
        )
        
        db.session.add(location)
        db.session.flush()  # Get the location ID without committing
        
        # Generate QR code data as URL with location ID
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
        
        # Kısa URL formatı kullan: l=location
        qr_code_data = f"{base_url}/guest/call?l={location.id}"
        location.qr_code_data = qr_code_data
        
        # Generate QR code image (optimize edilmiş parametreler)
        qr = qrcode.QRCode(version=1, box_size=2, border=0)
        qr.add_data(qr_code_data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_base64 = base64.b64encode(buffer.getvalue()).decode()
        location.qr_code_image = f"data:image/png;base64,{img_base64}"
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Lokasyon başarıyla oluşturuldu',
            'location': location.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@api_bp.route('/locations/<int:location_id>', methods=['PUT'])
@require_login
def update_location(location_id):
    """Update location"""
    try:
        user = SystemUser.query.get(session['user_id'])
        location = Location.query.filter_by(id=location_id, hotel_id=user.hotel_id).first()
        
        if not location:
            return jsonify({'error': 'Lokasyon bulunamadı'}), 404
        
        # Check content type and parse data accordingly
        content_type = request.content_type or ''
        
        if 'multipart/form-data' in content_type:
            # FormData request
            data = request.form.to_dict()
            image_file = request.files.get('location_image')
            current_app.logger.info(f"IMAGE FILE: {image_file}")
        elif 'application/json' in content_type:
            # JSON request
            data = request.get_json() or {}
            image_file = None
        else:
            # Try to handle both
            data = request.form.to_dict() if request.form else (request.get_json() or {})
            image_file = request.files.get('location_image') if request.files else None
        
        # Update fields
        if 'name' in data:
            location.name = data['name']
        if 'description' in data:
            location.description = data['description']
        
        # Handle image update
        if image_file and image_file.filename:
            # Delete old image if exists and is a file path
            current_app.logger.info(f"Old image path: {location.location_image}")
            current_app.logger.info(f"New image file: {image_file.filename}")
            if location.location_image and location.location_image.startswith('/static/uploads/'):
                delete_location_image(location.location_image)
            
            # Save new image
            try:
                new_image_path = save_location_image(image_file)
                if new_image_path:
                    location.location_image = new_image_path
                    import logging
                    logging.info(f"✅ Image updated for location {location_id}: {new_image_path}")
            except ValueError as e:
                return jsonify({'error': str(e)}), 400
        elif 'location_image' in data:
            # Sadece açıkça boş string gönderilirse sil
            if data['location_image'] == '' or data['location_image'] == 'null' or data['location_image'] == 'undefined':
                # Remove image
                if location.location_image and location.location_image.startswith('/static/uploads/'):
                    delete_location_image(location.location_image)
                location.location_image = None
            elif data['location_image'] and data['location_image'].startswith('data:image'):
                # Backward compatibility: base64 image
                location.location_image = data['location_image']
            # Eğer location_image field'ı var ama değeri None/boş değilse → mevcut görseli koru (hiçbir şey yapma)
        
        if 'latitude' in data:
            location.latitude = float(data['latitude']) if data['latitude'] else None
        if 'longitude' in data:
            location.longitude = float(data['longitude']) if data['longitude'] else None
        if 'is_active' in data:
            # Handle both boolean and string values
            if isinstance(data['is_active'], bool):
                location.is_active = data['is_active']
            elif isinstance(data['is_active'], str):
                location.is_active = data['is_active'].lower() in ('true', '1', 'yes')
            else:
                location.is_active = bool(data['is_active'])
        if 'display_order' in data:
            location.display_order = int(data['display_order'])
        
        # Regenerate QR code if requested or if name changed
        regenerate_qr = data.get('regenerate_qr', 'false').lower() == 'true' or 'name' in data
        
        if regenerate_qr:
            # Generate new QR code data URL
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
            
            # Kısa URL formatı kullan: l=location
            qr_code_data = f"{base_url}/guest/call?l={location.id}"
            location.qr_code_data = qr_code_data
            
            # Generate new QR code image (optimize edilmiş parametreler)
            qr = qrcode.QRCode(version=1, box_size=2, border=0)
            qr.add_data(qr_code_data)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            img_base64 = base64.b64encode(buffer.getvalue()).decode()
            location.qr_code_image = f"data:image/png;base64,{img_base64}"
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Lokasyon başarıyla güncellendi',
            'location': location.to_dict(),
            'qr_regenerated': regenerate_qr
        }), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Location update error: {str(e)}')
        return jsonify({'error': str(e)}), 500


@api_bp.route('/locations/<int:location_id>/regenerate-qr', methods=['POST'])
@require_login
def regenerate_qr_code(location_id):
    """Regenerate QR code for a location"""
    try:
        user = SystemUser.query.get(session['user_id'])
        location = Location.query.filter_by(id=location_id, hotel_id=user.hotel_id).first()
        
        if not location:
            return jsonify({'error': 'Lokasyon bulunamadı'}), 404
        
        # Generate new QR code data URL
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
        
        # Kısa URL formatı kullan: l=location
        qr_code_data = f"{base_url}/guest/call?l={location.id}"
        location.qr_code_data = qr_code_data
        
        # Generate new QR code image (optimize edilmiş parametreler)
        qr = qrcode.QRCode(version=1, box_size=2, border=0)
        qr.add_data(qr_code_data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_base64 = base64.b64encode(buffer.getvalue()).decode()
        location.qr_code_image = f"data:image/png;base64,{img_base64}"
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'QR kod başarıyla yenilendi',
            'location': location.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'QR regeneration error: {str(e)}')
        return jsonify({'error': str(e)}), 500


@api_bp.route('/locations/<int:location_id>', methods=['DELETE'])
@require_login
def delete_location(location_id):
    """Delete location"""
    try:
        from app.utils.exceptions import ResourceNotFoundException, ValidationException
        
        user = SystemUser.query.get(session['user_id'])
        
        # Verify location belongs to user's hotel
        location = Location.query.filter_by(id=location_id, hotel_id=user.hotel_id).first()
        if not location:
            return jsonify({'error': 'Lokasyon bulunamadı'}), 404
        
        # Delete location image if exists
        if location.location_image and location.location_image.startswith('/static/uploads/'):
            delete_location_image(location.location_image)
        
        # Delegate to service layer for all validation and deletion logic
        LocationService.delete_location(location_id)
        
        return jsonify({
            'success': True,
            'message': 'Lokasyon başarıyla silindi'
        }), 200
        
    except ResourceNotFoundException as e:
        return jsonify({'error': e.message}), 404
    except ValidationException as e:
        return jsonify({'error': e.message}), 400
    except Exception as e:
        db.session.rollback()
        import traceback
        print(f"Error deleting location {location_id}: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': f'Lokasyon silinirken hata oluştu: {str(e)}'}), 500


@api_bp.route('/locations/<int:location_id>/qr-code', methods=['GET'])
def download_qr_code(location_id):
    """Download QR code image as PNG"""
    try:
        from flask import send_file

        location = Location.query.get(location_id)
        if not location:
            return jsonify({'error': 'Lokasyon bulunamadı'}), 404

        # Generate QR code (minimal yoğunluk)
        qr = qrcode.QRCode(version=1, box_size=2, border=0, error_correction=qrcode.constants.ERROR_CORRECT_L)
        qr.add_data(location.qr_code_data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        # Save to BytesIO
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)

        return send_file(
            buffer,
            mimetype='image/png',
            as_attachment=True,
            download_name=f'QR_{location.name.replace(" ", "_")}.png'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/locations/<int:location_id>/qr-svg', methods=['GET'])
def download_qr_svg(location_id):
    """Download QR code as SVG"""
    try:
        from flask import send_file
        import qrcode.image.svg

        location = Location.query.get(location_id)
        if not location:
            return jsonify({'error': 'Lokasyon bulunamadı'}), 404

        # QR kod verisi
        qr_data = location.qr_code_data
        
        # QRCodeService kullanarak SVG oluştur (800x800 boyut, minimal yoğunluk)
        from app.services.qr_service import QRCodeService
        svg_bytes, _ = QRCodeService.generate_qr_code(
            data=qr_data,
            box_size=2,  # Minimal yoğunluk
            border=0,    # Kenarsız
            error_correction=qrcode.constants.ERROR_CORRECT_L,  # %7 hata düzeltme
            format='svg'  # 800x800 boyutunda oluşturulacak
        )

        # BytesIO'ya yaz
        buffer = io.BytesIO(svg_bytes)
        buffer.seek(0)

        return send_file(
            buffer,
            mimetype='image/svg+xml',
            as_attachment=True,
            download_name=f'QR_{location.name.replace(" ", "_")}.svg'
        )
    except Exception as e:
        import logging
        logging.error(f"SVG QR kod oluşturma hatası: {str(e)}")
        return jsonify({'error': str(e)}), 500


# ==================== Buggies API ====================
@api_bp.route('/buggies', methods=['GET'])
@require_login
def get_buggies():
    """Get all buggies"""
    try:
        from sqlalchemy.orm import joinedload
        
        user = SystemUser.query.get(session['user_id'])
        
        # Eager loading ile tüm ilişkileri tek sorguda çek (N+1 problemi çözümü)
        buggies = Buggy.query.filter_by(hotel_id=user.hotel_id)\
            .options(
                joinedload(Buggy.current_location),
                joinedload(Buggy.driver_associations)
            ).all()
        
        result = []
        for buggy in buggies:
            buggy_dict = buggy.to_dict()
            result.append(buggy_dict)
        
        return jsonify({
            'success': True,
            'buggies': result
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/buggies', methods=['POST'])
@require_login
def create_buggy():
    """Create new buggy (driver assignment is optional)"""
    try:
        from app.models.user import UserRole
        from app.models.buggy_driver import BuggyDriver
        from app.utils.buggy_icons import assign_buggy_icon
        
        user = SystemUser.query.get(session['user_id'])
        data = request.get_json()
        
        if not data.get('code'):
            return jsonify({'error': 'Buggy kodu gerekli'}), 400
        
        buggy_code = data['code']
        driver_id = data.get('driver_id')  # Optional
        
        # Check if buggy code already exists
        existing_buggy = Buggy.query.filter_by(hotel_id=user.hotel_id, code=buggy_code).first()
        if existing_buggy:
            return jsonify({'error': 'Bu buggy kodu zaten kullanılıyor'}), 400
        
        # Use provided icon or assign unique icon for this buggy
        buggy_icon = data.get('icon') or assign_buggy_icon(user.hotel_id)
        
        # Create buggy without driver
        buggy = Buggy(
            hotel_id=user.hotel_id,
            code=buggy_code,
            license_plate=data.get('license_plate'),
            icon=buggy_icon,  # Assign icon
            status=BuggyStatus.OFFLINE,
            driver_id=None  # Will be managed through buggy_drivers table
        )
        
        db.session.add(buggy)
        db.session.flush()  # Get buggy ID
        
        # If driver_id provided, create association
        driver_info = None
        if driver_id:
            print(f'🔍 Looking for driver with ID: {driver_id}, hotel_id: {user.hotel_id}')
            
            # Verify driver exists
            driver = SystemUser.query.filter_by(
                id=driver_id,
                hotel_id=user.hotel_id,
                role=UserRole.DRIVER
            ).first()
            
            if driver:
                print(f'✅ Driver found: {driver.username} ({driver.full_name})')
                
                # Create buggy-driver association
                association = BuggyDriver(
                    buggy_id=buggy.id,
                    driver_id=driver_id,
                    is_active=False,  # Will be activated when driver logs in
                    is_primary=True,
                    assigned_at=get_current_timestamp()
                )
                db.session.add(association)
                print(f'✅ BuggyDriver association created: buggy_id={buggy.id}, driver_id={driver_id}')
                
                driver_info = {
                    'id': driver.id,
                    'username': driver.username,
                    'full_name': driver.full_name
                }
            else:
                print(f'❌ Driver not found with ID: {driver_id}')
        
        db.session.commit()
        print(f'✅ Buggy created successfully: {buggy.code} (ID: {buggy.id})')
        
        response = {
            'success': True,
            'message': 'Buggy başarıyla oluşturuldu',
            'buggy': buggy.to_dict()
        }
        
        if driver_info:
            response['driver'] = driver_info
            response['message'] = 'Buggy ve sürücü ataması başarıyla oluşturuldu'
            print(f'✅ Response includes driver info: {driver_info}')
        
        return jsonify(response), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@api_bp.route('/buggies/<int:buggy_id>', methods=['GET'])
@require_login
def get_buggy(buggy_id):
    """Get single buggy"""
    try:
        user = SystemUser.query.get(session['user_id'])
        buggy = Buggy.query.filter_by(id=buggy_id, hotel_id=user.hotel_id).first()
        
        if not buggy:
            return jsonify({'error': 'Buggy bulunamadı'}), 404
        
        buggy_dict = buggy.to_dict()
        # Add driver name
        if buggy.driver:
            # Use full_name if available, otherwise use username
            buggy_dict['driver_name'] = buggy.driver.full_name if buggy.driver.full_name else buggy.driver.username
        else:
            buggy_dict['driver_name'] = None
        
        return jsonify({
            'success': True,
            'buggy': buggy_dict
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/buggies/<int:buggy_id>', methods=['PUT'])
@require_login
def update_buggy(buggy_id):
    """Update buggy"""
    try:
        user = SystemUser.query.get(session['user_id'])
        buggy = Buggy.query.filter_by(id=buggy_id, hotel_id=user.hotel_id).first()
        
        if not buggy:
            return jsonify({'error': 'Buggy bulunamadı'}), 404
        
        data = request.get_json()
        
        if 'code' in data:
            buggy.code = data['code']
        if 'icon' in data:
            buggy.icon = data['icon']
        if 'model' in data:
            buggy.model = data['model']
        if 'license_plate' in data:
            buggy.license_plate = data['license_plate']
        if 'status' in data:
            buggy.status = BuggyStatus(data['status'])
        # Note: driver_id is now managed through buggy_drivers table, not directly on buggy
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Buggy başarıyla güncellendi',
            'buggy': buggy.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@api_bp.route('/buggies/<int:buggy_id>', methods=['DELETE'])
@require_login
def delete_buggy(buggy_id):
    """Delete buggy"""
    try:
        user = SystemUser.query.get(session['user_id'])
        buggy = Buggy.query.filter_by(id=buggy_id, hotel_id=user.hotel_id).first()
        
        if not buggy:
            return jsonify({'error': 'Buggy bulunamadı'}), 404
        
        db.session.delete(buggy)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Buggy başarıyla silindi'
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ==================== Drivers API ====================
@api_bp.route('/drivers', methods=['GET'])
@require_login
def get_drivers():
    """Get all drivers"""
    try:
        user = SystemUser.query.get(session['user_id'])
        from app.models.user import UserRole
        drivers = SystemUser.query.filter_by(hotel_id=user.hotel_id, role=UserRole.DRIVER, is_active=True).all()
        
        return jsonify({
            'success': True,
            'drivers': [{
                'id': d.id, 
                'username': d.username, 
                'full_name': d.full_name if d.full_name else d.username
            } for d in drivers]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/drivers/active', methods=['GET'])
def get_active_drivers():
    """Get active drivers with their buggies (No auth required for guest debugging)"""
    try:
        hotel_id = request.args.get('hotel_id', 1, type=int)
        notify_param = request.args.get('notify', 'false')
        notify = notify_param.lower() == 'true' if notify_param else False
        
        from app.models.buggy import Buggy, BuggyStatus
        from app.models.buggy_driver import BuggyDriver
        from app.models.location import Location
        
        # DEBUG: Tüm buggy'leri kontrol et
        all_buggies = Buggy.query.filter_by(hotel_id=hotel_id).all()
        print(f'\n🔍 [DEBUG] Hotel {hotel_id} - Total Buggies: {len(all_buggies)}')
        for b in all_buggies:
            print(f'   Buggy {b.code}: status={b.status.value}, location={b.current_location_id}')
        
        # Müsait buggy'leri bul
        available_buggies = Buggy.query.filter_by(
            hotel_id=hotel_id,
            status=BuggyStatus.AVAILABLE
        ).all()
        
        print(f'🟢 [DEBUG] Available Buggies: {len(available_buggies)}')
        
        active_drivers = []
        
        for buggy in available_buggies:
            # Aktif sürücü atamalarını bul
            print(f'   🔍 Checking Buggy {buggy.code} (ID: {buggy.id})')
            
            # Tüm assignment'ları kontrol et (debug için)
            all_assignments = BuggyDriver.query.filter_by(buggy_id=buggy.id).all()
            print(f'      Total assignments: {len(all_assignments)}')
            for a in all_assignments:
                print(f'         - Driver ID: {a.driver_id}, is_active: {a.is_active}')
            
            active_assignments = BuggyDriver.query.filter_by(
                buggy_id=buggy.id,
                is_active=True
            ).all()
            
            print(f'   ✅ Active assignments: {len(active_assignments)}')
            
            for assignment in active_assignments:
                driver = SystemUser.query.get(assignment.driver_id)
                if driver:
                    print(f'      ✅ Driver: {driver.full_name or driver.username}, FCM: {bool(driver.fcm_token)}')
                    active_drivers.append({
                        'driver_id': driver.id,
                        'driver_name': driver.full_name or driver.username,
                        'buggy_id': buggy.id,
                        'buggy_code': buggy.code,
                        'buggy_icon': buggy.icon,
                        'buggy_status': buggy.status.value,
                        'has_fcm_token': bool(driver.fcm_token),
                        'last_active': assignment.last_active_at.isoformat() if assignment.last_active_at else None
                    })
        
        print(f'👥 [DEBUG] Total Active Drivers: {len(active_drivers)}\n')
        
        # Eğer notify=true ise, sürücülere WebSocket ile bildirim gönder
        if notify and len(active_drivers) > 0:
            # Location bilgisini al (varsa)
            location_id = request.args.get('location_id', type=int)
            location_name = 'Bilinmeyen Lokasyon'
            if location_id:
                location = Location.query.get(location_id)
                if location:
                    location_name = location.name
            
            # WebSocket event data
            event_data = {
                'type': 'guest_connected',
                'message': '🚨 Yeni Misafir Bağlandı!',
                'location_name': location_name,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Hotel drivers room'a gönder
            drivers_room = f'hotel_{hotel_id}_drivers'
            socketio.emit('guest_connected', event_data, room=drivers_room, namespace='/')
            print(f'🚨 WebSocket: Guest connected notification sent to {drivers_room}')
        
        return jsonify({
            'success': True,
            'hotel_id': hotel_id,
            'active_drivers_count': len(active_drivers),
            'active_drivers': active_drivers,
            'notification_sent': notify and len(active_drivers) > 0
        }), 200
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f'❌ [ERROR] get_active_drivers failed: {str(e)}')
        print(error_details)
        return jsonify({
            'success': False,
            'error': str(e),
            'details': error_details if current_app.debug else None
        }), 500


# ==================== Requests API ====================
@api_bp.route('/requests', methods=['POST'])
def create_request():
    """Create new buggy request (Guest - no auth required)"""
    try:
        data = request.get_json()
        
        # Validate required fields
        location_id = data.get('location_id')
        if not location_id:
            log_error('CREATE_REQUEST', 'Location ID eksik', data)
            return jsonify({'error': 'Location ID gerekli'}), 400
        
        # Get location to verify and get hotel_id
        location = Location.query.get(location_id)
        if not location:
            log_error('CREATE_REQUEST', f'Geçersiz lokasyon: {location_id}')
            return jsonify({'error': 'Geçersiz lokasyon'}), 404
        
        # Create request (requested_at otomatik olarak get_current_timestamp ile ayarlanır)
        buggy_request = BuggyRequest(
            hotel_id=location.hotel_id,
            location_id=location_id,
            guest_name=data.get('guest_name'),
            room_number=data.get('room_number'),
            phone=data.get('phone'),
            notes=data.get('notes'),
            guest_device_id=request.remote_addr,  # Use IP as guest identifier
            status='PENDING'
        )
        
        db.session.add(buggy_request)
        db.session.commit()
        
        # Eager load relationships before session closes
        # Bu sayede to_dict() çağrısı güvenli olur
        db.session.refresh(buggy_request)
        _ = buggy_request.location  # Force load
        _ = buggy_request.buggy  # Force load (None olacak ama yüklensin)
        _ = buggy_request.accepted_by_driver  # Force load (None olacak)
        
        # Log request creation
        log_request_event('CREATED', {
            'request_id': buggy_request.id,
            'guest_name': buggy_request.guest_name,
            'location': location.name,
            'hotel_id': location.hotel_id,
            'room_number': buggy_request.room_number
        })
        
        # Emit WebSocket event for drivers and admins
        from app import socketio
        event_data = {
            'request_id': buggy_request.id,
            'guest_name': buggy_request.guest_name,
            'location': location.to_dict(),
            'room_number': buggy_request.room_number,
            'phone_number': buggy_request.phone,
            'notes': buggy_request.notes,
            'requested_at': buggy_request.requested_at.isoformat()
        }
        
        # Send via SSE (Server-Sent Events) - Simple and reliable!
        from app.routes.sse import send_to_all_drivers
        sent_count = send_to_all_drivers(location.hotel_id, 'new_request', event_data)
        log_websocket_event('SSE_NEW_REQUEST', {'request_id': buggy_request.id, 'drivers_notified': sent_count})
        
        # Also send via WebSocket for admin panel
        admin_room = f'hotel_{location.hotel_id}_admin'
        socketio.emit('new_request', event_data, room=admin_room, namespace='/')
        log_websocket_event('WS_NEW_REQUEST_ADMIN', {'request_id': buggy_request.id, 'room': admin_room})
        
        # Send push notifications to available drivers (FCM)
        try:
            from app.services.fcm_notification_service import FCMNotificationService
            notification_count = FCMNotificationService.notify_new_request(buggy_request)
            log_request_event('FCM_SENT', {'request_id': buggy_request.id, 'drivers_notified': notification_count})
        except Exception as e:
            log_error('FCM_NOTIFICATION', str(e), {'request_id': buggy_request.id})
            # Don't fail the request if notification fails
        
        return jsonify({
            'success': True,
            'message': 'Buggy çağrınız alındı',
            'request_id': buggy_request.id,
            'request': buggy_request.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@api_bp.route('/requests', methods=['GET'])
@require_login
def get_requests():
    """Get all requests (Admin/Driver)"""
    try:
        from sqlalchemy.orm import joinedload
        
        user = SystemUser.query.get(session['user_id'])
        
        # Get query parameters
        status_str = request.args.get('status')
        buggy_id = request.args.get('buggy_id')
        
        # Build query with eager loading (N+1 problemi çözümü)
        query = BuggyRequest.query.filter_by(hotel_id=user.hotel_id)\
            .options(
                joinedload(BuggyRequest.location),
                joinedload(BuggyRequest.buggy).joinedload(Buggy.current_location),
                joinedload(BuggyRequest.buggy).joinedload(Buggy.driver_associations)
            )
        
        # Handle status filter - convert string to enum
        if status_str:
            try:
                # Try to convert string to RequestStatus enum
                status_enum = RequestStatus(status_str.lower())
                query = query.filter_by(status=status_enum)
            except ValueError:
                # Invalid status value, ignore filter
                pass
        
        if buggy_id:
            query = query.filter_by(buggy_id=buggy_id)
        
        # Get requests
        requests = query.order_by(BuggyRequest.requested_at.desc()).all()
        
        result = []
        for req in requests:
            req_dict = req.to_dict()
            # Add location info
            if req.location:
                req_dict['location'] = req.location.to_dict()
            # Add buggy info
            if req.buggy:
                req_dict['buggy'] = req.buggy.to_dict()
            result.append(req_dict)
        
        return jsonify({
            'success': True,
            'requests': result
        }), 200
    except Exception as e:
        current_app.logger.error(f'Error in get_requests: {str(e)}')
        return jsonify({'error': str(e)}), 500


@api_bp.route('/requests/<int:request_id>', methods=['GET'])
def get_request(request_id):
    """Get single request (Guest - no auth required)"""
    try:
        buggy_request = BuggyRequest.query.get(request_id)
        
        if not buggy_request:
            return jsonify({'error': 'Talep bulunamadı'}), 404
        
        req_dict = buggy_request.to_dict()
        # Add location info
        if buggy_request.location:
            req_dict['location'] = buggy_request.location.to_dict()
        # Add buggy info
        if buggy_request.buggy:
            req_dict['buggy'] = {
                'id': buggy_request.buggy.id,
                'code': buggy_request.buggy.code,
                'icon': buggy_request.buggy.icon
            }
        
        return jsonify({
            'success': True,
            'request': req_dict
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/requests/<int:request_id>/accept', methods=['PUT', 'POST'])
@require_login
def accept_request(request_id):
    """Accept request (Driver)"""
    try:
        user = SystemUser.query.get(session['user_id'])
        
        # Get driver's buggy
        buggy = Buggy.query.filter_by(driver_id=user.id).first()
        if not buggy:
            log_error('ACCEPT_REQUEST', 'Buggy bulunamadı', {'user_id': user.id, 'request_id': request_id})
            return jsonify({'error': 'Bu kullanıcıya atanmış buggy bulunamadı'}), 404
        
        # Get request
        buggy_request = BuggyRequest.query.get(request_id)
        if not buggy_request:
            log_error('ACCEPT_REQUEST', 'Talep bulunamadı', {'request_id': request_id})
            return jsonify({'error': 'Talep bulunamadı'}), 404
        
        if buggy_request.status != 'PENDING':
            log_error('ACCEPT_REQUEST', 'Talep zaten işleme alınmış', {'request_id': request_id, 'status': buggy_request.status})
            return jsonify({'error': 'Bu talep zaten işleme alınmış'}), 400
        
        # Update request
        buggy_request.status = 'accepted'
        buggy_request.buggy_id = buggy.id
        buggy_request.accepted_at = datetime.utcnow()
        
        if buggy_request.requested_at:
            delta = buggy_request.accepted_at - buggy_request.requested_at
            buggy_request.response_time_seconds = int(delta.total_seconds())
        
        # Update buggy status
        buggy.status = BuggyStatus.BUSY
        
        db.session.commit()
        
        # Log acceptance
        log_request_event('ACCEPTED', {
            'request_id': request_id,
            'driver': user.full_name,
            'buggy': buggy.code,
            'response_time': buggy_request.response_time_seconds
        })
        
        # Emit WebSocket event for guest
        from app import socketio
        socketio.emit('request_accepted', {
            'request_id': buggy_request.id,
            'buggy': buggy.to_dict(),
            'accepted_at': buggy_request.accepted_at.isoformat()
        }, room=f'request_{request_id}')
        
        # Guest'e FCM bildirimi gönder
        try:
            from app.routes.guest_notification_api import GUEST_FCM_TOKENS
            import requests
            
            token_data = GUEST_FCM_TOKENS.get(request_id)
            if token_data:
                # FCM bildirimi gönder
                fcm_url = 'https://fcm.googleapis.com/fcm/send'
                fcm_headers = {
                    'Authorization': f'key={current_app.config.get("FCM_SERVER_KEY")}',
                    'Content-Type': 'application/json'
                }
                fcm_payload = {
                    'to': token_data['token'],
                    'notification': {
                        'title': '🚀 Shuttle Yola Çıktı!',
                        'body': f'Shuttle\'ınız {buggy.plate_number} yola çıktı. Yakında yanınızda!',
                        'icon': '/static/img/shuttle-icon.png',
                        'click_action': f'/guest/status/{request_id}'
                    },
                    'data': {
                        'request_id': str(request_id),
                        'status': 'accepted',
                        'buggy_plate': buggy.plate_number
                    }
                }
                
                response = requests.post(fcm_url, json=fcm_payload, headers=fcm_headers, timeout=5)
                if response.status_code == 200:
                    logger.info(f'✅ FCM notification sent to guest for request {request_id}')
                else:
                    logger.warning(f'⚠️ FCM notification failed: {response.text}')
            else:
                logger.info(f'ℹ️ No FCM token found for request {request_id}')
        except Exception as notif_error:
            logger.error(f'❌ Error sending FCM notification: {str(notif_error)}')
        
        # Emit to other drivers that this request is taken (via SSE)
        from app.routes.sse import send_to_all_drivers
        send_to_all_drivers(buggy_request.hotel_id, 'request_taken', {
            'request_id': buggy_request.id
        })
        
        # Also emit via WebSocket for backward compatibility
        socketio.emit('request_taken', {
            'request_id': buggy_request.id
        }, room=f'hotel_{buggy_request.hotel_id}_drivers')
        
        # Emit buggy status update for real-time dashboard
        try:
            from app.services.buggy_service import BuggyService
            BuggyService.emit_buggy_status_update(buggy.id, buggy_request.hotel_id)
        except:
            pass
        
        return jsonify({
            'success': True,
            'message': 'Talep kabul edildi',
            'request': buggy_request.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@api_bp.route('/requests/<int:request_id>/complete', methods=['PUT', 'POST'])
# Rate limiter removed
@require_login
@require_role('driver')
def complete_request(request_id):
    """Complete a buggy request and update buggy location"""
    try:
        user = SystemUser.query.get(session['user_id'])
        
        # Check if driver has assigned buggy
        if not user.buggy:
            return jsonify({'success': False, 'error': 'No buggy assigned'}), 400
        
        data = request.get_json() or {}
        current_location_id = data.get('current_location_id')
        notes = data.get('notes', '')
        
        # Validate current_location_id is provided
        if not current_location_id:
            return jsonify({'success': False, 'error': 'Current location is required'}), 400
        
        # Validate notes length
        if notes and len(notes) > 500:
            return jsonify({'success': False, 'error': 'Notes must be 500 characters or less'}), 400
        
        # Verify location exists and belongs to hotel
        location = Location.query.get(current_location_id)
        if not location:
            return jsonify({'success': False, 'error': 'Invalid location'}), 400
        
        if location.hotel_id != user.hotel_id:
            return jsonify({'success': False, 'error': 'Invalid location'}), 400
        
        # Get the request
        buggy_request = BuggyRequest.query.get(request_id)
        if not buggy_request:
            return jsonify({'success': False, 'error': 'Request not found'}), 404
        
        # Verify request is assigned to driver's buggy
        if buggy_request.buggy_id != user.buggy.id:
            return jsonify({'success': False, 'error': 'Request not assigned to your buggy'}), 403
        
        # Verify request status is ACCEPTED
        if buggy_request.status != RequestStatus.ACCEPTED:
            return jsonify({'success': False, 'error': 'Request is not in accepted status'}), 400
        
        # Use RequestService for completion (handles transaction, audit, websocket)
        from app.services.request_service import RequestService
        from app.utils.exceptions import BuggyCallException
        
        try:
            buggy_request = RequestService.complete_request(
                request_id=request_id,
                driver_id=user.id,
                current_location_id=current_location_id,
                notes=notes
            )
            
            # Return success response with buggy status and location
            return jsonify({
                'success': True,
                'message': 'Request completed successfully',
                'request': {
                    'id': buggy_request.id,
                    'status': buggy_request.status.value,
                    'completed_at': buggy_request.completed_at.isoformat() if buggy_request.completed_at else None
                },
                'buggy': {
                    'id': user.buggy.id,
                    'status': user.buggy.status.value,
                    'current_location': {
                        'id': location.id,
                        'name': location.name
                    }
                }
            }), 200
            
        except BuggyCallException as e:
            return jsonify({'success': False, 'error': str(e)}), e.status_code
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Completion failed'}), 500


@api_bp.route('/requests/<int:request_id>/cancel', methods=['PUT', 'POST'])
@require_login
def cancel_request(request_id):
    """Cancel request (Admin/System only - Guests cannot cancel)"""
    try:
        # Sadece admin ve sistem kullanıcıları iptal edebilir
        current_user = get_current_user()
        if not current_user or current_user.role not in ['admin', 'system']:
            return jsonify({
                'error': 'Yetkisiz işlem. Misafirler talep iptal edemez.',
                'message': 'Talebiniz 1 saat içinde yanıtlanmazsa otomatik olarak işaretlenecektir.'
            }), 403
        
        buggy_request = BuggyRequest.query.get(request_id)
        if not buggy_request:
            return jsonify({'error': 'Talep bulunamadı'}), 404
        
        if buggy_request.status == 'completed':
            return jsonify({'error': 'Tamamlanmış talep iptal edilemez'}), 400
        
        if buggy_request.status == 'cancelled':
            return jsonify({'error': 'Bu talep zaten iptal edilmiş'}), 400
        
        # Update request
        from app.models import get_current_timestamp
        old_status = buggy_request.status
        buggy_request.status = 'cancelled'
        buggy_request.cancelled_at = get_current_timestamp()
        buggy_request.cancelled_by = current_user.id
        
        # If was accepted, free up the buggy
        if old_status == 'accepted' and buggy_request.buggy:
            buggy_request.buggy.status = BuggyStatus.AVAILABLE
        
        db.session.commit()
        
        # Emit WebSocket event
        from app import socketio
        socketio.emit('request_cancelled', {
            'request_id': buggy_request.id
        }, room=f'request_{request_id}')
        
        if old_status == 'accepted':
            socketio.emit('request_cancelled', {
                'request_id': buggy_request.id
            }, room=f'hotel_{buggy_request.hotel_id}_drivers')
        
        return jsonify({
            'success': True,
            'message': 'Talep iptal edildi'
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ==================== Users API ====================
@api_bp.route('/users/<int:user_id>/reset-password', methods=['POST'])
@require_login
def reset_user_password(user_id):
    """Reset user password to temporary password (Admin only)"""
    try:
        # Check if user is admin
        admin = SystemUser.query.get(session['user_id'])
        if not admin or admin.role != UserRole.ADMIN:
            return jsonify({'error': 'Bu işlem için yetkiniz yok'}), 403
        
        # Get target user
        target_user = SystemUser.query.filter_by(id=user_id, hotel_id=admin.hotel_id).first()
        if not target_user:
            return jsonify({'error': 'Kullanıcı bulunamadı'}), 404
        
        # Generate temporary password: username + "123*"
        temp_password = f"{target_user.username}123*"
        
        # Reset password
        target_user.set_password(temp_password)
        target_user.must_change_password = True
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Şifre sıfırlandı',
            'username': target_user.username,
            'temp_password': temp_password
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@api_bp.route('/users', methods=['POST'])
@require_login
def create_user():
    """Create new user (Admin only)"""
    try:
        # Check if user is admin
        user = SystemUser.query.get(session['user_id'])
        if not user or user.role != UserRole.ADMIN:
            return jsonify({'error': 'Bu işlem için yetkiniz yok'}), 403
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['username', 'password', 'role']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'{field} alanı zorunludur'}), 400
        
        # Validate role
        valid_roles = ['admin', 'driver']
        if data['role'] not in valid_roles:
            return jsonify({'error': 'Geçersiz rol'}), 400
        
        # Convert string role to Enum
        role_enum = UserRole.ADMIN if data['role'] == 'admin' else UserRole.DRIVER
        
        # Check if username already exists
        existing_user = SystemUser.query.filter_by(username=data['username']).first()
        if existing_user:
            return jsonify({'error': 'Bu kullanıcı adı zaten kullanılıyor'}), 400
        
        # Create new user
        full_name = f"{data.get('first_name', '')} {data.get('last_name', '')}".strip() or data['username']
        print(f'🔄 Creating new user: username={data["username"]}, role={data["role"]}, full_name={full_name}')
        
        new_user = SystemUser(
            username=data['username'],
            role=role_enum,
            hotel_id=user.hotel_id,  # Same hotel as admin
            full_name=full_name,
            email=data.get('email'),
            phone=data.get('phone'),
            is_active=True
        )
        new_user.set_password(data['password'])
        
        db.session.add(new_user)
        db.session.commit()
        
        print(f'✅ User created successfully: ID={new_user.id}, username={new_user.username}, hotel_id={new_user.hotel_id}')
        
        return jsonify({
            'success': True,
            'message': 'Kullanıcı başarıyla oluşturuldu',
            'user': {
                'id': new_user.id,
                'username': new_user.username,
                'role': new_user.role.value,
                'full_name': new_user.full_name,
                'email': new_user.email,
                'phone': new_user.phone,
                'hotel_id': new_user.hotel_id
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ==================== Push Notifications ====================
@api_bp.route('/push/vapid-public-key', methods=['GET'])
def get_vapid_public_key():
    """
    LEGACY: Get VAPID public key for push notifications
    NOT USED - FCM kullanılıyor
    """
    # Eski sistem devre dışı, FCM kullanılıyor
    return jsonify({
        'error': 'Legacy endpoint - FCM kullanılıyor',
        'message': 'Bu endpoint artık kullanılmıyor. FCM sistemi aktif.'
    }), 410  # 410 Gone


# LEGACY ENDPOINTS - Kaldırıldı, FCM kullanılıyor
# /push/subscribe ve /push/unsubscribe endpoint'leri artık kullanılmıyor
# FCM için /api/fcm/register-token kullanılıyor


@api_bp.route('/notification-permission', methods=['POST'])
@require_login
def update_notification_permission():
    """
    Update notification permission status in session
    Only accessible by drivers and admins
    """
    try:
        # Get current user
        user_id = session.get('user_id')
        if not user_id:
            current_app.logger.warning('[NotificationPermission] Unauthorized access attempt - no user_id in session')
            return jsonify({
                'success': False,
                'error': 'Oturum bulunamadı'
            }), 401
        
        # Get user from database
        user = SystemUser.query.get(user_id)
        if not user:
            current_app.logger.warning(f'[NotificationPermission] User not found: {user_id}')
            return jsonify({
                'success': False,
                'error': 'Kullanıcı bulunamadı'
            }), 404
        
        # Role validation - only driver and admin
        user_role = session.get('role')
        if user_role not in ['driver', 'admin']:
            current_app.logger.warning(
                f'[NotificationPermission] Unauthorized role access attempt - '
                f'user_id: {user_id}, role: {user_role}'
            )
            return jsonify({
                'success': False,
                'error': 'Bu işlem için yetkiniz yok'
            }), 403
        
        # Get request data
        data = request.get_json()
        if not data:
            current_app.logger.warning(f'[NotificationPermission] Empty request body - user_id: {user_id}')
            return jsonify({
                'success': False,
                'error': 'Geçersiz istek'
            }), 400
        
        # Status validation
        status = data.get('status')
        valid_statuses = ['default', 'granted', 'denied']
        
        if not status:
            current_app.logger.warning(f'[NotificationPermission] Missing status - user_id: {user_id}')
            return jsonify({
                'success': False,
                'error': 'Bildirim izni durumu gerekli'
            }), 400
        
        if status not in valid_statuses:
            current_app.logger.warning(
                f'[NotificationPermission] Invalid status value - '
                f'user_id: {user_id}, status: {status}'
            )
            return jsonify({
                'success': False,
                'error': f'Geçersiz durum değeri. İzin verilen değerler: {", ".join(valid_statuses)}'
            }), 400
        
        # Update session
        try:
            session['notification_permission_asked'] = True
            session['notification_permission_status'] = status
            session.modified = True  # Ensure session is saved
            
            current_app.logger.info(
                f'[NotificationPermission] Permission updated - '
                f'user_id: {user_id}, role: {user_role}, status: {status}'
            )
            
            return jsonify({
                'success': True,
                'message': 'Bildirim izni durumu güncellendi',
                'data': {
                    'notification_permission_asked': True,
                    'notification_permission_status': status
                }
            }), 200
            
        except Exception as session_error:
            current_app.logger.error(
                f'[NotificationPermission] Session update failed - '
                f'user_id: {user_id}, error: {str(session_error)}'
            )
            return jsonify({
                'success': False,
                'error': 'Oturum güncellenirken hata oluştu'
            }), 500
    
    except Exception as e:
        current_app.logger.error(
            f'[NotificationPermission] Unexpected error - '
            f'user_id: {session.get("user_id")}, error: {str(e)}'
        )
        return jsonify({
            'success': False,
            'error': 'Bildirim izni güncellenirken beklenmeyen bir hata oluştu'
        }), 500


@api_bp.route('/push/test', methods=['POST'])
@require_login
# Rate limiter removed
def test_push_notification():
    """Test push notification - LEGACY"""
    try:
        # Eski sistem - artık kullanılmıyor
        return jsonify({'error': 'Legacy endpoint - FCM kullanılıyor'}), 410
        
        user = SystemUser.query.get(session['user_id'])
        if not user or not hasattr(user, 'push_subscription') or not user.push_subscription:
            return jsonify({'error': 'Push bildirimleri aktif değil'}), 400
        
        import json
        subscription_info = json.loads(user.push_subscription)
        
        success = NotificationService.send_notification(
            subscription_info=subscription_info,
            title="Test Bildirimi",
            body="Push bildirimleri başarıyla çalışıyor!",
            data={'type': 'test'}
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Test bildirimi gönderildi'
            })
        else:
            return jsonify({'error': 'Bildirim gönderilemedi'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500



# ==================== Buggy Location Tracking ====================
@api_bp.route('/buggies/locations', methods=['GET'])
# Rate limiter removed
@require_login
@require_role('admin')
def get_buggy_locations():
    """Get all buggies with their current locations (Admin only)"""
    try:
        from app.utils.helpers import RequestContext
        from sqlalchemy.orm import joinedload
        
        hotel_id = RequestContext.get_current_hotel_id()
        
        # Eager loading ile tüm ilişkileri tek sorguda çek (N+1 problemi çözümü)
        buggies = Buggy.query.filter_by(hotel_id=hotel_id)\
            .options(
                joinedload(Buggy.current_location),
                joinedload(Buggy.driver_associations)
            ).all()
        
        result = []
        for buggy in buggies:
            buggy_data = buggy.to_dict()
            result.append(buggy_data)
        
        return jsonify({
            'success': True,
            'buggies': result,
            'total': len(result)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/buggies/<int:buggy_id>/location', methods=['PUT'])
# Rate limiter removed
@require_login
def update_buggy_location(buggy_id):
    """Update buggy's current location (Driver or Admin)"""
    try:
        user = SystemUser.query.get(session['user_id'])
        data = request.get_json()
        
        if not data or 'location_id' not in data:
            return jsonify({'error': 'location_id gereklidir'}), 400
        
        location_id = data['location_id']
        
        # Get buggy
        buggy = Buggy.query.get(buggy_id)
        if not buggy:
            return jsonify({'error': 'Buggy bulunamadı'}), 404
        
        # Check authorization
        if user.role == 'driver' and buggy.driver_id != user.id:
            return jsonify({'error': 'Bu buggy size atanmamış'}), 403
        
        # Validate location
        location = Location.query.get(location_id)
        if not location:
            return jsonify({'error': 'Lokasyon bulunamadı'}), 404
        
        if location.hotel_id != buggy.hotel_id:
            return jsonify({'error': 'Lokasyon farklı bir otele ait'}), 400
        
        # Update location
        old_location_id = buggy.current_location_id
        buggy.current_location_id = location_id
        db.session.commit()
        
        # Log location change
        from app.services.audit_service import AuditService
        AuditService.log_action(
            action='buggy_location_changed',
            entity_type='buggy',
            entity_id=buggy_id,
            old_values={'location_id': old_location_id},
            new_values={'location_id': location_id},
            user_id=user.id,
            hotel_id=buggy.hotel_id
        )
        
        # Emit WebSocket event for real-time tracking
        from app import socketio
        socketio.emit('buggy_location_changed', {
            'buggy_id': buggy_id,
            'location_id': location_id,
            'location_name': location.name,
            'buggy_code': buggy.code
        }, room=f'hotel_{buggy.hotel_id}_admin')
        
        return jsonify({
            'success': True,
            'message': 'Lokasyon güncellendi',
            'buggy': buggy.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500



# ==================== Driver Initial Location Setup ====================
@api_bp.route('/driver/set-initial-location', methods=['POST'])
# Rate limiter removed
@require_login
def set_initial_location():
    """Set driver's initial location on first login"""
    try:
        user = SystemUser.query.get(session['user_id'])
        data = request.get_json()
        
        if not data or 'location_id' not in data:
            return jsonify({'error': 'location_id gereklidir'}), 400
        
        location_id = data['location_id']
        
        # Check if user is driver
        if user.role != UserRole.DRIVER:
            return jsonify({'error': 'Sadece sürücüler lokasyon ayarlayabilir'}), 403
        
        # Check if driver has buggy
        if not user.buggy:
            return jsonify({'error': 'Size atanmış buggy bulunamadı'}), 404
        
        # Validate location
        location = Location.query.get(location_id)
        if not location:
            return jsonify({'error': 'Lokasyon bulunamadı'}), 404
        
        if location.hotel_id != user.hotel_id:
            return jsonify({'error': 'Lokasyon farklı bir otele ait'}), 400
        
        # Set buggy location and status
        user.buggy.current_location_id = location_id
        user.buggy.status = BuggyStatus.AVAILABLE
        
        # Remove location setup flag
        session.pop('needs_location_setup', None)
        
        db.session.commit()
        
        # Log initial location setup
        from app.services.audit_service import AuditService
        AuditService.log_action(
            action='driver_initial_location_set',
            entity_type='buggy',
            entity_id=user.buggy.id,
            new_values={'location_id': location_id, 'location_name': location.name},
            user_id=user.id,
            hotel_id=user.hotel_id
        )
        
        # Emit WebSocket event to admin panel for real-time status update
        try:
            from app import socketio
            socketio.emit('buggy_status_changed', {
                'buggy_id': user.buggy.id,
                'buggy_code': user.buggy.code,
                'buggy_icon': user.buggy.icon,
                'driver_id': user.id,
                'driver_name': user.full_name if user.full_name else user.username,
                'location_id': location_id,
                'location_name': location.name,
                'status': 'available',
                'reason': 'initial_location_set'
            }, room=f'hotel_{user.hotel_id}_admin')
            print(f'[INITIAL_LOCATION] Emitted buggy_status_changed event to hotel_{user.hotel_id}_admin')
        except Exception as e:
            print(f'[INITIAL_LOCATION] Error emitting buggy_status_changed: {e}')
        
        # Emit buggy status update for real-time dashboard
        try:
            from app.services.buggy_service import BuggyService
            BuggyService.emit_buggy_status_update(user.buggy.id, user.hotel_id)
            print(f'[INITIAL_LOCATION] Emitted buggy status update')
        except Exception as e:
            print(f'[INITIAL_LOCATION] Error emitting buggy status: {e}')
        
        return jsonify({
            'success': True,
            'message': 'Lokasyon ayarlandı, sisteme hoş geldiniz!',
            'buggy': user.buggy.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500



# ==================== Admin Session Management ====================
@api_bp.route('/admin/close-driver-session/<int:driver_id>', methods=['POST'])
# Rate limiter removed
@require_login
@require_role('admin')
def close_driver_session(driver_id):
    """Admin closes driver session and sets buggy offline"""
    try:
        # Get driver
        driver = SystemUser.query.get(driver_id)
        if not driver:
            return jsonify({'error': 'Sürücü bulunamadı'}), 404
        
        if driver.role != UserRole.DRIVER:
            return jsonify({'error': 'Kullanıcı sürücü değil'}), 400
        
        # Close all active BuggyDriver associations and set buggies offline
        from app.models.buggy_driver import BuggyDriver
        from app.models.buggy import Buggy
        
        active_buggy_drivers = BuggyDriver.query.filter_by(
            driver_id=driver_id,
            is_active=True
        ).all()
        
        buggy_ids = []
        for assoc in active_buggy_drivers:
            # Deactivate driver association
            from app.models import get_current_timestamp
            assoc.is_active = False
            assoc.last_active_at = get_current_timestamp()
            
            # Set buggy to offline and clear location
            buggy = Buggy.query.get(assoc.buggy_id)
            if buggy:
                buggy.status = BuggyStatus.OFFLINE
                buggy.current_location_id = None  # Clear location when admin closes session
                buggy_ids.append({
                    'id': buggy.id,
                    'code': buggy.code,
                    'icon': buggy.icon
                })
        
        # Close all active sessions for this driver (if any exist)
        from app.models.session import Session as SessionModel
        active_sessions = SessionModel.query.filter_by(
            user_id=driver_id,
            is_active=True
        ).all()
        
        from app.models import get_current_timestamp
        for sess in active_sessions:
            sess.is_active = False
            sess.revoked_at = get_current_timestamp()
        
        db.session.commit()
        
        # Log admin action
        from app.services.audit_service import AuditService
        AuditService.log_action(
            action='admin_closed_driver_session',
            entity_type='session',
            entity_id=driver_id,
            new_values={'driver_name': driver.full_name, 'reason': 'admin_action'},
            user_id=session.get('user_id'),
            hotel_id=driver.hotel_id
        )
        
        # Emit WebSocket event to force driver logout
        from app import socketio
        socketio.emit('force_logout', {
            'reason': 'admin_terminated',
            'message': 'Oturumunuz yönetici tarafından kapatıldı. Lütfen tekrar giriş yapın.'
        }, room=f'user_{driver_id}')
        
        # Emit buggy status changed events to admin panel
        for buggy_info in buggy_ids:
            socketio.emit('buggy_status_changed', {
                'buggy_id': buggy_info['id'],
                'buggy_code': buggy_info['code'],
                'buggy_icon': buggy_info['icon'],
                'driver_id': None,
                'driver_name': None,
                'location_name': None,  # Clear location when admin closes session
                'status': 'offline',
                'reason': 'admin_closed_session'
            }, room=f'hotel_{driver.hotel_id}_admin')
        
        return jsonify({
            'success': True,
            'message': f'{driver.full_name} oturumu kapatıldı'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ==================== Driver Location Management ====================
@api_bp.route('/driver/set-location', methods=['POST'])
# Rate limiter removed
@require_login
def set_driver_location():
    """Set or update driver's current location"""
    try:
        user = SystemUser.query.get(session['user_id'])
        
        # User kontrolü
        if not user:
            return jsonify({'error': 'Kullanıcı bulunamadı'}), 404
        
        data = request.get_json()
        
        if not data or 'location_id' not in data:
            return jsonify({'error': 'location_id gereklidir'}), 400
        
        location_id = data['location_id']
        
        # Location ID validasyonu
        if not isinstance(location_id, int) or location_id <= 0:
            return jsonify({'error': 'Geçersiz location_id'}), 400
        
        # Check if user is driver
        if user.role != UserRole.DRIVER:
            return jsonify({'error': 'Sadece sürücüler lokasyon ayarlayabilir'}), 403
        
        # Check if driver has buggy
        if not user.buggy:
            return jsonify({'error': 'Size atanmış buggy bulunamadı. Lütfen yöneticinizle iletişime geçin.'}), 404
        
        # Validate location
        location = Location.query.get(location_id)
        if not location or not location.is_active:
            return jsonify({'error': 'Geçerli bir lokasyon bulunamadı'}), 404
        
        if location.hotel_id != user.hotel_id:
            return jsonify({'error': 'Lokasyon farklı bir otele ait'}), 400
        
        # Store old location for audit
        old_location_id = user.buggy.current_location_id
        old_location_name = user.buggy.current_location.name if user.buggy.current_location else None
        
        # Update buggy location and set to available
        user.buggy.current_location_id = location_id
        user.buggy.status = BuggyStatus.AVAILABLE
        
        db.session.commit()
        
        # Log location update
        from app.services.audit_service import AuditService
        AuditService.log_action(
            action='driver_location_updated',
            entity_type='buggy',
            entity_id=user.buggy.id,
            old_values={'location_id': old_location_id, 'location_name': old_location_name},
            new_values={'location_id': location_id, 'location_name': location.name},
            user_id=user.id,
            hotel_id=user.hotel_id
        )
        
        # Emit WebSocket events to admin
        from app.websocket import socketio
        
        # Emit location update event
        socketio.emit('driver_location_updated', {
            'buggy_id': user.buggy.id,
            'buggy_code': user.buggy.code,
            'driver_name': user.full_name,
            'location_id': location_id,
            'location_name': location.name,
            'status': user.buggy.status.value
        }, room=f'hotel_{user.hotel_id}_admin')
        
        # Emit buggy status changed event for full dashboard update
        socketio.emit('buggy_status_changed', {
            'buggy_id': user.buggy.id,
            'buggy_code': user.buggy.code,
            'buggy_icon': user.buggy.icon,
            'driver_id': user.id,
            'driver_name': user.full_name if user.full_name else user.username,
            'location_id': location_id,
            'location_name': location.name,
            'status': 'available',
            'reason': 'location_updated'
        }, room=f'hotel_{user.hotel_id}_admin')
        
        print(f'[LOCATION_UPDATE] Emitted events to hotel_{user.hotel_id}_admin')
        
        return jsonify({
            'success': True,
            'message': 'Konumunuz güncellendi',
            'buggy': user.buggy.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ==================== Driver Request Management ====================
@api_bp.route('/driver/accept-request/<int:request_id>', methods=['POST'])
# Rate limiter removed
@require_login
def driver_accept_request(request_id):
    """Accept a PENDING buggy request"""
    try:
        user = SystemUser.query.get(session['user_id'])
        
        # User kontrolü
        if not user:
            return jsonify({'error': 'Kullanıcı bulunamadı'}), 404
        
        # Check if user is driver
        if user.role != UserRole.DRIVER:
            return jsonify({'error': 'Sadece sürücüler talep kabul edebilir'}), 403
        
        # Check if driver has buggy
        if not user.buggy:
            return jsonify({'error': 'Size atanmış buggy bulunamadı. Lütfen yöneticinizle iletişime geçin.'}), 404
        
        # Check if buggy is available
        if user.buggy.status != BuggyStatus.AVAILABLE:
            return jsonify({'error': f'Buggy müsait değil. Mevcut durum: {user.buggy.status.value}'}), 400
        
        # Get request with row-level lock to prevent race conditions
        buggy_request = db.session.query(BuggyRequest).filter_by(
            id=request_id,
            hotel_id=user.hotel_id,
            status=RequestStatus.PENDING
        ).with_for_update().first()
        
        if not buggy_request:
            return jsonify({'error': 'Talep bulunamadı veya artık müsait değil'}), 404
        
        # Update request
        from app.models import get_current_timestamp
        buggy_request.status = RequestStatus.ACCEPTED
        buggy_request.buggy_id = user.buggy.id
        buggy_request.accepted_by_id = user.id
        buggy_request.accepted_at = get_current_timestamp()
        
        # Update buggy status
        user.buggy.status = BuggyStatus.BUSY
        
        db.session.commit()
        
        # Log acceptance
        from app.services.audit_service import AuditService
        AuditService.log_action(
            action='request_accepted',
            entity_type='request',
            entity_id=buggy_request.id,
            new_values={
                'buggy_id': user.buggy.id,
                'driver_id': user.id,
                'driver_name': user.full_name
            },
            user_id=user.id,
            hotel_id=user.hotel_id
        )
        
        # Send Web Push notification to guest
        if buggy_request.guest_push_subscription:
            from app.services.web_push_service import WebPushService
            try:
                location_name = buggy_request.location.name if buggy_request.location else "Lokasyon"
                driver_name = user.full_name or user.username
                
                WebPushService.send_shuttle_on_way_notification(
                    request_id=buggy_request.id,
                    location_name=location_name,
                    driver_name=driver_name
                )
                current_app.logger.info(f'✅ Web push notification gönderildi: request_id={buggy_request.id}')
            except Exception as e:
                current_app.logger.error(f'Web push notification hatası: {str(e)}')
                # Notification failure shouldn't break the flow
        
        # Send FCM notification to guest if subscribed (backward compatibility)
        if buggy_request.guest_device_id:
            from app.services.fcm_notification_service import FCMNotificationService
            try:
                # guest_device_id string veya JSON olabilir
                import json
                try:
                    device_data = json.loads(buggy_request.guest_device_id) if isinstance(buggy_request.guest_device_id, str) else buggy_request.guest_device_id
                    fcm_token = device_data.get('fcm_token') if isinstance(device_data, dict) else None
                except:
                    fcm_token = None
                
                if fcm_token:
                    FCMNotificationService.send_to_token(
                        token=fcm_token,
                        title="Buggy Kabul Edildi",
                        body=f"Buggy'niz yola çıktı. {user.buggy.code}",
                    data={'type': 'request_accepted', 'request_id': str(buggy_request.id)},
                    priority='high'
                )
            except:
                pass  # Notification failure shouldn't break the flow
        
        # Emit WebSocket events
        from app.websocket import socketio
        
        # Notify guest
        guest_room = f'request_{buggy_request.id}'
        socketio.emit('request_accepted', {
            'request_id': buggy_request.id,
            'buggy': user.buggy.to_dict(),
            'driver': user.to_dict()
        }, room=guest_room)
        print(f'✅ WebSocket emit: request_accepted to {guest_room}')
        
        # Notify admin
        admin_room = f'hotel_{user.hotel_id}_admin'
        socketio.emit('request_status_changed', {
            'request_id': buggy_request.id,
            'status': 'accepted',
            'buggy_code': user.buggy.code
        }, room=admin_room)
        print(f'✅ WebSocket emit: request_status_changed to {admin_room}')
        
        # Emit buggy status change
        socketio.emit('buggy_status_changed', {
            'buggy_id': user.buggy.id,
            'status': 'busy',
            'location_name': buggy_request.location.name if buggy_request.location else None
        }, room=f'hotel_{user.hotel_id}_admin')
        
        return jsonify({
            'success': True,
            'message': 'Talep kabul edildi',
            'request': {
                'id': buggy_request.id,
                'guest_name': buggy_request.guest_name,
                'room_number': buggy_request.room_number,
                'location': buggy_request.location.to_dict() if buggy_request.location else None,
                'status': buggy_request.status.value
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@api_bp.route('/driver/complete-request/<int:request_id>', methods=['POST'])
# Rate limiter removed
@require_login
def driver_complete_request(request_id):
    """Mark an accepted request as completed"""
    try:
        user = SystemUser.query.get(session['user_id'])
        
        # User kontrolü
        if not user:
            return jsonify({'error': 'Kullanıcı bulunamadı'}), 404
        
        # Check if user is driver
        if user.role != UserRole.DRIVER:
            return jsonify({'error': 'Sadece sürücüler talep tamamlayabilir'}), 403
        
        # Check if driver has buggy
        if not user.buggy:
            return jsonify({'error': 'Size atanmış buggy bulunamadı. Lütfen yöneticinizle iletişime geçin.'}), 404
        
        # Get request
        buggy_request = BuggyRequest.query.filter_by(
            id=request_id,
            buggy_id=user.buggy.id,
            accepted_by_id=user.id,
            status=RequestStatus.ACCEPTED
        ).first()
        
        if not buggy_request:
            return jsonify({'error': 'Talep bulunamadı veya size ait değil'}), 404
        
        # Update request
        from app.models import get_current_timestamp
        buggy_request.status = RequestStatus.COMPLETED
        buggy_request.completed_at = get_current_timestamp()
        
        # Keep buggy busy until driver sets new location
        # (Location modal will be shown on frontend)
        
        db.session.commit()
        
        # Log completion
        from app.services.audit_service import AuditService
        AuditService.log_action(
            action='request_completed',
            entity_type='request',
            entity_id=buggy_request.id,
            new_values={'completed_at': buggy_request.completed_at.isoformat()},
            user_id=user.id,
            hotel_id=user.hotel_id
        )
        
        # Send notification to guest if subscribed (FCM)
        # guest_device_id içinde FCM token olabilir (JSON parse gerekebilir)
        if buggy_request.guest_device_id:
            from app.services.fcm_notification_service import FCMNotificationService
            try:
                # guest_device_id string veya JSON olabilir
                import json
                try:
                    device_data = json.loads(buggy_request.guest_device_id) if isinstance(buggy_request.guest_device_id, str) else buggy_request.guest_device_id
                    fcm_token = device_data.get('fcm_token') if isinstance(device_data, dict) else None
                except:
                    fcm_token = None
                
                if fcm_token:
                    FCMNotificationService.send_to_token(
                        token=fcm_token,
                        title="Buggy Geldi!",
                        body="Buggy'niz konumunuza ulaştı. İyi yolculuklar!",
                    data={'type': 'request_completed', 'request_id': str(buggy_request.id)},
                    priority='high'
                )
            except:
                pass
        
        # Emit WebSocket events
        from app.websocket import socketio
        socketio.emit('request_completed', {
            'request_id': buggy_request.id
        }, room=f'request_{buggy_request.id}')
        
        socketio.emit('request_status_changed', {
            'request_id': buggy_request.id,
            'status': 'completed'
        }, room=f'hotel_{user.hotel_id}_admin')
        
        return jsonify({
            'success': True,
            'message': 'Talep tamamlandı! Lütfen yeni konumunuzu seçin.',
            'show_location_modal': True
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ==================== Admin Session Management ====================
@api_bp.route('/admin/sessions', methods=['GET'])
# Rate limiter removed
@require_login
def get_active_sessions():
    """Get all active sessions (admin only)"""
    try:
        user = SystemUser.query.get(session['user_id'])
        
        if user.role != UserRole.ADMIN:
            return jsonify({'error': 'Sadece adminler oturumları görüntüleyebilir'}), 403
        
        from app.models.session import Session as SessionModel
        
        # Get active sessions for this hotel
        sessions = SessionModel.query.filter_by(
            hotel_id=user.hotel_id,
            is_active=True
        ).order_by(SessionModel.created_at.desc()).all()
        
        return jsonify({
            'success': True,
            'sessions': [s.to_dict() for s in sessions]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/admin/sessions/<int:session_id>/terminate', methods=['POST'])
# Rate limiter removed
@require_login
def terminate_session(session_id):
    """Terminate a user session (admin only)"""
    try:
        user = SystemUser.query.get(session['user_id'])
        
        if user.role != UserRole.ADMIN:
            return jsonify({'error': 'Sadece adminler oturum sonlandırabilir'}), 403
        
        from app.models.session import Session as SessionModel
        
        # Get session
        user_session = SessionModel.query.filter_by(
            id=session_id,
            hotel_id=user.hotel_id
        ).first()
        
        if not user_session:
            return jsonify({'error': 'Oturum bulunamadı'}), 404
        
        if not user_session.is_active:
            return jsonify({'error': 'Oturum zaten sonlandırılmış'}), 400
        
        # Terminate session
        from app.models import get_current_timestamp
        user_session.is_active = False
        user_session.revoked_at = get_current_timestamp()
        
        # If driver, set buggy offline
        session_user = SystemUser.query.get(user_session.user_id)
        if session_user and session_user.role == UserRole.DRIVER and session_user.buggy:
            session_user.buggy.status = BuggyStatus.OFFLINE
        
        db.session.commit()
        
        # Log termination
        from app.services.audit_service import AuditService
        AuditService.log_action(
            action='session_terminated_by_admin',
            entity_type='session',
            entity_id=user_session.id,
            new_values={
                'terminated_user_id': user_session.user_id,
                'terminated_by_admin_id': user.id
            },
            user_id=user.id,
            hotel_id=user.hotel_id
        )
        
        # Emit WebSocket event to force logout
        from app.websocket import socketio
        socketio.emit('force_logout', {
            'reason': 'Session terminated by administrator',
            'message': 'Oturumunuz yönetici tarafından sonlandırıldı'
        }, room=f'user_{user_session.user_id}')
        
        return jsonify({
            'success': True,
            'message': 'Oturum başarıyla sonlandırıldı'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ==================== Driver Dashboard API ====================
@api_bp.route('/driver/pending-requests', methods=['GET'])
# Rate limiter removed
@require_login
@require_role('driver')
def get_pending_requests():
    """Get all pending requests for driver's hotel"""
    try:
        user = SystemUser.query.get(session['user_id'])
        
        # Check if driver has assigned buggy
        if not user.buggy:
            return jsonify({'success': False, 'error': 'No buggy assigned'}), 400
        
        # Query PENDING requests for the hotel with location eager loading
        from sqlalchemy.orm import joinedload
        from app.models.request import RequestStatus
        
        pending_requests = BuggyRequest.query\
            .options(joinedload(BuggyRequest.location))\
            .filter_by(
                hotel_id=user.hotel_id,
                status=RequestStatus.PENDING
            )\
            .order_by(BuggyRequest.requested_at.desc())\
            .all()
        
        print(f'📋 Found {len(pending_requests)} pending requests for hotel {user.hotel_id}')
        
        # Serialize with location and guest info
        requests_data = [{
            'id': req.id,
            'guest_name': req.guest_name,
            'room_number': req.room_number,
            'phone_number': req.phone,
            'location': {
                'id': req.location.id,
                'name': req.location.name
            } if req.location else None,
            'requested_at': req.requested_at.isoformat() if req.requested_at else None,
            'notes': req.notes
        } for req in pending_requests]
        
        # Log fetch action for debugging
        try:
            from app.services.audit_service import AuditService
            AuditService.log_action(
                action='driver_fetched_pending_requests',
                entity_type='request',
                entity_id=None,
                new_values={'count': len(pending_requests)},
                user_id=user.id,
                hotel_id=user.hotel_id
            )
        except Exception as log_error:
            # Logging failure should not break the API
            print(f"Audit log failed: {log_error}")
        
        print(f'✅ Returning {len(requests_data)} pending requests to driver {user.username}')
        
        return jsonify({
            'success': True,
            'requests': requests_data,
            'total': len(requests_data)
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/driver/active-request', methods=['GET'])
# Rate limiter removed
@require_login
@require_role('driver')
def get_active_request():
    """Get driver's currently active request"""
    try:
        user = SystemUser.query.get(session['user_id'])
        
        # Check if driver has assigned buggy
        if not user.buggy:
            return jsonify({'success': False, 'error': 'No buggy assigned'}), 400
        
        # Find accepted request assigned to this buggy
        from sqlalchemy.orm import joinedload
        from app.models.request import RequestStatus
        
        active_request = BuggyRequest.query\
            .options(joinedload(BuggyRequest.location))\
            .filter_by(
                buggy_id=user.buggy.id,
                status=RequestStatus.ACCEPTED
            )\
            .first()
        
        if not active_request:
            # Log fetch action
            try:
                from app.services.audit_service import AuditService
                AuditService.log_action(
                    action='driver_fetched_active_request',
                    entity_type='request',
                    entity_id=None,
                    new_values={'has_active': False},
                    user_id=user.id,
                    hotel_id=user.hotel_id
                )
            except Exception as log_error:
                print(f"Audit log failed: {log_error}")
            
            return jsonify({
                'success': True,
                'request': None
            }), 200
        
        # Serialize with full details
        request_data = {
            'id': active_request.id,
            'guest_name': active_request.guest_name,
            'room_number': active_request.room_number,
            'phone_number': active_request.phone,
            'location': {
                'id': active_request.location.id,
                'name': active_request.location.name
            } if active_request.location else None,
            'requested_at': active_request.requested_at.isoformat() if active_request.requested_at else None,
            'accepted_at': active_request.accepted_at.isoformat() if active_request.accepted_at else None,
            'notes': active_request.notes,
            'status': active_request.status.value
        }
        
        # Log fetch action
        try:
            from app.services.audit_service import AuditService
            AuditService.log_action(
                action='driver_fetched_active_request',
                entity_type='request',
                entity_id=active_request.id,
                new_values={'has_active': True, 'request_id': active_request.id},
                user_id=user.id,
                hotel_id=user.hotel_id
            )
        except Exception as log_error:
            print(f"Audit log failed: {log_error}")
        
        return jsonify({
            'success': True,
            'request': request_data
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/driver/shuttle-info', methods=['GET'])
@api_bp.route('/driver/buggy-info', methods=['GET'])  # Backward compatibility
@require_login
@require_role('driver')
def get_driver_shuttle_info():
    """Get driver's assigned shuttle information"""
    try:
        user = SystemUser.query.get(session['user_id'])
        
        # User kontrolü
        if not user:
            return jsonify({
                'success': False,
                'error': 'Kullanıcı bulunamadı'
            }), 404
        
        if not user.buggy:
            return jsonify({
                'success': False,
                'error': 'Size atanmış shuttle bulunamadı. Lütfen yöneticinizle iletişime geçin.'
            }), 404
        
        return jsonify({
            'success': True,
            'buggy': {  # Keep 'buggy' key for backward compatibility
                'id': user.buggy.id,
                'code': user.buggy.code,
                'model': user.buggy.model,
                'icon': user.buggy.icon,
                'status': user.buggy.status.value if hasattr(user.buggy.status, 'value') else str(user.buggy.status)
            }
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== Admin Driver Management ====================
@api_bp.route('/admin/assign-driver-to-buggy', methods=['POST'])
# Rate limiter removed
@require_login
@require_role('admin')
def assign_driver_to_buggy():
    """
    Assign a driver to a buggy (Admin only)
    
    Request Body:
    {
        "buggy_id": 1,
        "driver_id": 5
    }
    
    Response:
    {
        "success": true,
        "message": "Sürücü başarıyla atandı",
        "buggy": {...}
    }
    """
    try:
        admin = SystemUser.query.get(session['user_id'])
        data = request.get_json()
        
        # Validate required fields
        if not data or 'buggy_id' not in data or 'driver_id' not in data:
            return jsonify({'success': False, 'error': 'buggy_id ve driver_id gereklidir'}), 400
        
        buggy_id = data['buggy_id']
        driver_id = data['driver_id']
        
        # Get buggy
        buggy = Buggy.query.filter_by(id=buggy_id, hotel_id=admin.hotel_id).first()
        if not buggy:
            return jsonify({'success': False, 'error': 'Buggy bulunamadı'}), 404
        
        # Get driver
        driver = SystemUser.query.filter_by(
            id=driver_id,
            hotel_id=admin.hotel_id,
            role=UserRole.DRIVER
        ).first()
        if not driver:
            return jsonify({'success': False, 'error': 'Sürücü bulunamadı'}), 404
        
        # Store old driver for audit
        old_driver_id = buggy.get_active_driver()
        old_driver_name = buggy.get_active_driver_name()
        
        # Assign driver to buggy using association table
        from app.models.buggy_driver import BuggyDriver
        
        # Check if driver is already assigned to this buggy
        existing = BuggyDriver.query.filter_by(buggy_id=buggy_id, driver_id=driver_id).first()
        if not existing:
            # Create new association
            association = BuggyDriver(
                buggy_id=buggy_id,
                driver_id=driver_id,
                is_active=False,  # Will be set to True when driver logs in
                is_primary=True,  # Mark as primary driver
                assigned_at=get_current_timestamp()
            )
            db.session.add(association)
        
        db.session.commit()
        
        # Log driver assignment
        from app.services.audit_service import AuditService
        AuditService.log_action(
            action='driver_assigned_to_buggy',
            entity_type='buggy',
            entity_id=buggy_id,
            old_values={
                'driver_id': old_driver_id,
                'driver_name': old_driver_name
            },
            new_values={
                'driver_id': driver_id,
                'driver_name': driver.full_name,
                'buggy_code': buggy.code,
                'admin_name': admin.full_name
            },
            user_id=admin.id,
            hotel_id=admin.hotel_id
        )
        
        # Emit WebSocket event for real-time updates
        from app import socketio
        socketio.emit('driver_assigned', {
            'buggy_id': buggy_id,
            'buggy_code': buggy.code,
            'driver_id': driver_id,
            'driver_name': driver.full_name
        }, room=f'hotel_{admin.hotel_id}_admin')
        
        return jsonify({
            'success': True,
            'message': f'{driver.full_name} başarıyla {buggy.code} buggy\'sine atandı',
            'buggy': buggy.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/admin/transfer-driver', methods=['POST'])
# Rate limiter removed
@require_login
@require_role('admin')
def transfer_driver():
    """
    Transfer a driver from one buggy to another (Admin only)
    
    Request Body:
    {
        "driver_id": 5,
        "source_buggy_id": 1,
        "target_buggy_id": 2
    }
    
    Response:
    {
        "success": true,
        "message": "Sürücü başarıyla transfer edildi",
        "source_buggy": {...},
        "target_buggy": {...}
    }
    """
    try:
        admin = SystemUser.query.get(session['user_id'])
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['driver_id', 'source_buggy_id', 'target_buggy_id']
        for field in required_fields:
            if not data or field not in data:
                return jsonify({'success': False, 'error': f'{field} gereklidir'}), 400
        
        driver_id = data['driver_id']
        source_buggy_id = data['source_buggy_id']
        target_buggy_id = data['target_buggy_id']
        
        # Validate source and target are different
        if source_buggy_id == target_buggy_id:
            return jsonify({'success': False, 'error': 'Kaynak ve hedef buggy aynı olamaz'}), 400
        
        # Get driver
        driver = SystemUser.query.filter_by(
            id=driver_id,
            hotel_id=admin.hotel_id,
            role=UserRole.DRIVER
        ).first()
        if not driver:
            return jsonify({'success': False, 'error': 'Sürücü bulunamadı'}), 404
        
        # Get source buggy
        source_buggy = Buggy.query.filter_by(id=source_buggy_id, hotel_id=admin.hotel_id).first()
        if not source_buggy:
            return jsonify({'success': False, 'error': 'Kaynak buggy bulunamadı'}), 404
        
        # Get target buggy
        target_buggy = Buggy.query.filter_by(id=target_buggy_id, hotel_id=admin.hotel_id).first()
        if not target_buggy:
            return jsonify({'success': False, 'error': 'Hedef buggy bulunamadı'}), 404
        
        # Verify driver is assigned to source buggy using buggy_drivers table
        from app.models.buggy_driver import BuggyDriver
        source_association = BuggyDriver.query.filter_by(
            buggy_id=source_buggy_id,
            driver_id=driver_id
        ).first()
        
        if not source_association:
            return jsonify({'success': False, 'error': 'Sürücü kaynak buggy\'ye atanmamış'}), 400
        
        # Check if driver has active session
        from app.models.session import Session as SessionModel
        active_session = SessionModel.query.filter_by(
            user_id=driver_id,
            is_active=True
        ).first()
        
        session_was_active = active_session is not None
        
        # If active session exists, terminate it
        from app.models import get_current_timestamp
        if active_session:
            active_session.is_active = False
            active_session.revoked_at = get_current_timestamp()
            
            # Deactivate driver association from source buggy
            source_association.is_active = False
            
            # Set both buggies to OFFLINE
            source_buggy.status = BuggyStatus.OFFLINE
            target_buggy.status = BuggyStatus.OFFLINE
        else:
            # Just deactivate the association without changing buggy status
            source_association.is_active = False
        
        # Create or activate driver association with target buggy
        target_association = BuggyDriver.query.filter_by(
            buggy_id=target_buggy_id,
            driver_id=driver_id
        ).first()
        
        if target_association:
            # Reactivate existing association
            target_association.is_active = False  # Will be activated when driver logs in
            target_association.assigned_at = get_current_timestamp()
        else:
            # Create new association
            target_association = BuggyDriver(
                buggy_id=target_buggy_id,
                driver_id=driver_id,
                is_active=False,  # Will be activated when driver logs in
                is_primary=True,
                assigned_at=get_current_timestamp()
            )
            db.session.add(target_association)
        
        db.session.commit()
        
        # Log driver transfer
        from app.services.audit_service import AuditService
        AuditService.log_action(
            action='driver_transferred',
            entity_type='buggy',
            entity_id=target_buggy_id,
            old_values={
                'source_buggy_id': source_buggy_id,
                'source_buggy_code': source_buggy.code
            },
            new_values={
                'target_buggy_id': target_buggy_id,
                'target_buggy_code': target_buggy.code,
                'driver_id': driver_id,
                'driver_name': driver.full_name,
                'admin_name': admin.full_name,
                'session_terminated': session_was_active
            },
            user_id=admin.id,
            hotel_id=admin.hotel_id
        )
        
        # Emit WebSocket event for real-time updates
        from app import socketio
        socketio.emit('driver_transferred', {
            'driver_id': driver_id,
            'driver_name': driver.full_name,
            'source_buggy_id': source_buggy_id,
            'source_buggy_code': source_buggy.code,
            'target_buggy_id': target_buggy_id,
            'target_buggy_code': target_buggy.code,
            'session_terminated': session_was_active
        }, room=f'hotel_{admin.hotel_id}_admin')
        
        # If session was terminated, notify driver
        if session_was_active:
            socketio.emit('force_logout', {
                'reason': 'Driver transferred to another buggy',
                'message': f'Başka bir buggy\'ye transfer edildiniz: {target_buggy.code}'
            }, room=f'user_{driver_id}')
        
        return jsonify({
            'success': True,
            'message': f'{driver.full_name} başarıyla {source_buggy.code}\'dan {target_buggy.code}\'a transfer edildi',
            'source_buggy': source_buggy.to_dict(),
            'target_buggy': target_buggy.to_dict(),
            'session_terminated': session_was_active
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# HEALTH CHECK ENDPOINT (Coolify/Docker için)
# ============================================================================

@api_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint for Coolify/Docker
    Veritabanı bağlantısını ve uygulama durumunu kontrol eder
    """
    try:
        # Database bağlantısını test et
        db.session.execute(db.text('SELECT 1'))
        db_status = 'connected'
    except Exception as e:
        current_app.logger.error(f'Health check database error: {str(e)}')
        db_status = 'disconnected'
        return jsonify({
            'status': 'unhealthy',
            'database': db_status,
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 503
    
    return jsonify({
        'status': 'healthy',
        'database': db_status,
        'app_name': current_app.config.get('APP_NAME', 'Shuttle Call'),
        'timestamp': datetime.utcnow().isoformat()
    }), 200


# ==================== User Management API (CRUD) ====================
@api_bp.route('/users/<int:user_id>', methods=['GET'])
@require_login
def get_user(user_id):
    """
    Kullanıcı bilgilerini getir (Admin veya kendi bilgisi)
    """
    try:
        current_user = SystemUser.query.get(session['user_id'])
        
        # Admin değilse sadece kendi bilgisini görebilir
        if current_user.role != UserRole.ADMIN and current_user.id != user_id:
            return jsonify({'success': False, 'error': 'Bu işlem için yetkiniz yok'}), 403
        
        # Kullanıcıyı getir
        user = SystemUser.query.filter_by(id=user_id, hotel_id=current_user.hotel_id).first()
        if not user:
            return jsonify({'success': False, 'error': 'Kullanıcı bulunamadı'}), 404
        
        # Ad ve soyadı ayır
        full_name_parts = user.full_name.split(' ', 1) if user.full_name else ['', '']
        first_name = full_name_parts[0] if len(full_name_parts) > 0 else ''
        last_name = full_name_parts[1] if len(full_name_parts) > 1 else ''
        
        return jsonify({
            'success': True,
            'user': {
                'id': user.id,
                'username': user.username,
                'role': user.role.value,
                'full_name': user.full_name,
                'first_name': first_name,
                'last_name': last_name,
                'email': user.email,
                'phone': user.phone,
                'is_active': user.is_active,
                'created_at': user.created_at.isoformat() if user.created_at else None
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f'Error getting user {user_id}: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/users/<int:user_id>', methods=['PUT'])
@require_login
def update_user(user_id):
    """
    Kullanıcı bilgilerini güncelle (Admin veya kendi bilgisi)
    """
    try:
        current_user = SystemUser.query.get(session['user_id'])
        
        # Admin değilse sadece kendi bilgisini güncelleyebilir
        if current_user.role != UserRole.ADMIN and current_user.id != user_id:
            return jsonify({'success': False, 'error': 'Bu işlem için yetkiniz yok'}), 403
        
        # Kullanıcıyı getir
        user = SystemUser.query.filter_by(id=user_id, hotel_id=current_user.hotel_id).first()
        if not user:
            return jsonify({'success': False, 'error': 'Kullanıcı bulunamadı'}), 404
        
        data = request.get_json()
        
        # Güncellenebilir alanlar
        if 'first_name' in data or 'last_name' in data:
            first_name = data.get('first_name', '').strip()
            last_name = data.get('last_name', '').strip()
            user.full_name = f"{first_name} {last_name}".strip()
        
        if 'email' in data:
            user.email = data['email'].strip() if data['email'] else None
        
        if 'phone' in data:
            user.phone = data['phone'].strip() if data['phone'] else None
        
        # Şifre güncelleme (opsiyonel)
        if 'password' in data and data['password']:
            if len(data['password']) < 6:
                return jsonify({'success': False, 'error': 'Şifre en az 6 karakter olmalıdır'}), 400
            user.set_password(data['password'])
        
        # Admin sadece role ve is_active güncelleyebilir
        if current_user.role == UserRole.ADMIN:
            if 'is_active' in data:
                user.is_active = bool(data['is_active'])
            
            if 'role' in data and data['role'] in ['admin', 'driver']:
                user.role = UserRole.ADMIN if data['role'] == 'admin' else UserRole.DRIVER
        
        db.session.commit()
        
        # Audit log
        from app.services.audit_service import AuditService
        AuditService.log_action(
            action='user_updated',
            entity_type='user',
            entity_id=user_id,
            new_values={'updated_by': current_user.id},
            user_id=current_user.id,
            hotel_id=current_user.hotel_id
        )
        
        return jsonify({
            'success': True,
            'message': 'Kullanıcı bilgileri başarıyla güncellendi',
            'user': {
                'id': user.id,
                'username': user.username,
                'full_name': user.full_name,
                'email': user.email,
                'phone': user.phone,
                'is_active': user.is_active
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error updating user {user_id}: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/users/<int:user_id>', methods=['DELETE'])
@require_login
def delete_user(user_id):
    """
    Kullanıcıyı sil (Sadece Admin)
    """
    try:
        current_user = SystemUser.query.get(session['user_id'])
        
        # Sadece admin silebilir
        if current_user.role != UserRole.ADMIN:
            return jsonify({'success': False, 'error': 'Bu işlem için yetkiniz yok'}), 403
        
        # Kendini silemez
        if current_user.id == user_id:
            return jsonify({'success': False, 'error': 'Kendi hesabınızı silemezsiniz'}), 400
        
        # Kullanıcıyı getir
        user = SystemUser.query.filter_by(id=user_id, hotel_id=current_user.hotel_id).first()
        if not user:
            return jsonify({'success': False, 'error': 'Kullanıcı bulunamadı'}), 404
        
        # Eğer sürücü ise, buggy atamalarını kaldır
        if user.role == UserRole.DRIVER:
            from app.models.buggy_driver import BuggyDriver
            
            # Tüm buggy atamalarını sil
            BuggyDriver.query.filter_by(driver_id=user_id).delete()
            
            # Eğer aktif oturumu varsa, buggy'leri offline yap
            from app.models.buggy import Buggy
            assigned_buggies = Buggy.query.filter_by(driver_id=user_id).all()
            for buggy in assigned_buggies:
                buggy.driver_id = None
                buggy.status = BuggyStatus.OFFLINE
                buggy.current_location_id = None
        
        # Kullanıcıyı sil
        username = user.username
        full_name = user.full_name
        db.session.delete(user)
        db.session.commit()
        
        # Audit log
        from app.services.audit_service import AuditService
        AuditService.log_action(
            action='user_deleted',
            entity_type='user',
            entity_id=user_id,
            old_values={'username': username, 'full_name': full_name},
            user_id=current_user.id,
            hotel_id=current_user.hotel_id
        )
        
        # WebSocket ile bildir
        from app import socketio
        socketio.emit('user_deleted', {
            'user_id': user_id,
            'username': username
        }, room=f'hotel_{current_user.hotel_id}_admin')
        
        return jsonify({
            'success': True,
            'message': f'Kullanıcı "{full_name or username}" başarıyla silindi'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error deleting user {user_id}: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== Guest Push Notifications ====================
@api_bp.route('/guest/subscribe-push', methods=['POST'])
@csrf.exempt
def guest_subscribe_push():
    """
    Guest için push notification subscription kaydet
    
    Request Body:
        {
            "request_id": 123,
            "subscription": {
                "endpoint": "...",
                "keys": {...}
            }
        }
    """
    try:
        data = request.get_json()
        
        if not data or 'request_id' not in data or 'subscription' not in data:
            return jsonify({'error': 'request_id ve subscription gereklidir'}), 400
        
        request_id = data['request_id']
        subscription = data['subscription']
        
        # Request'i bul
        buggy_request = BuggyRequest.query.get(request_id)
        if not buggy_request:
            return jsonify({'error': 'Talep bulunamadı'}), 404
        
        # Subscription'ı kaydet (JSON olarak)
        import json
        buggy_request.guest_push_subscription = json.dumps(subscription)
        db.session.commit()
        
        current_app.logger.info(f'Guest push subscription kaydedildi: request_id={request_id}')
        
        return jsonify({
            'success': True,
            'message': 'Push subscription kaydedildi'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Guest push subscription hatası: {str(e)}')
        return jsonify({'error': str(e)}), 500


# ==================== FCM Push Notifications ====================
@api_bp.route('/fcm/register-token', methods=['POST'])
@require_login
def register_fcm_token():
    """
    FCM token kaydet (Sürücü/Admin)
    
    Request Body:
        {
            "token": "fcm_device_token_here"
        }
    """
    try:
        data = request.get_json()
        
        if not data or 'token' not in data:
            return APIResponse.error('Token gereklidir', 400)
        
        token = data['token']
        user_id = session.get('user_id')
        
        if not user_id:
            return APIResponse.error('Kullanıcı oturumu bulunamadı', 401)
        
        # Token'ı kaydet
        from app.services.fcm_notification_service import FCMNotificationService
        success = FCMNotificationService.register_token(user_id, token)
        
        if success:
            return APIResponse.success(
                message='FCM token başarıyla kaydedildi',
                data={'user_id': user_id}
            )
        else:
            return APIResponse.error('Token kaydedilemedi', 500)
            
    except Exception as e:
        current_app.logger.error(f"FCM token kayıt hatası: {str(e)}")
        return APIResponse.error(f'Token kayıt hatası: {str(e)}', 500)


@api_bp.route('/fcm/test-notification', methods=['POST'])
@require_login
def test_fcm_notification():
    """
    Test FCM bildirimi gönder (Development/Test için)
    
    Request Body:
        {
            "title": "Test Başlık",
            "body": "Test Mesaj"
        }
    """
    try:
        data = request.get_json()
        user_id = session.get('user_id')
        
        if not user_id:
            return APIResponse.error('Kullanıcı oturumu bulunamadı', 401)
        
        # Kullanıcının token'ını al
        user = SystemUser.query.get(user_id)
        if not user or not user.fcm_token:
            return APIResponse.error('FCM token bulunamadı. Önce token kaydedin.', 400)
        
        # Test bildirimi gönder
        from app.services.fcm_notification_service import FCMNotificationService
        
        title = data.get('title', '🧪 Test Bildirimi')
        body = data.get('body', 'Bu bir test bildirimidir.')
        
        success = FCMNotificationService.send_to_token(
            token=user.fcm_token,
            title=title,
            body=body,
            data={
                'type': 'test',
                'timestamp': datetime.utcnow().isoformat()
            },
            priority='high'
        )
        
        if success:
            return APIResponse.success(
                message='Test bildirimi gönderildi',
                data={'user_id': user_id, 'username': user.username}
            )
        else:
            return APIResponse.error('Bildirim gönderilemedi', 500)
            
    except Exception as e:
        current_app.logger.error(f"Test bildirim hatası: {str(e)}")
        return APIResponse.error(f'Test bildirim hatası: {str(e)}', 500)
