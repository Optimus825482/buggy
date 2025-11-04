"""
Buggy Call - Map API Routes
Handles map thumbnail generation for notifications
"""
from flask import Blueprint, request, jsonify, send_file, current_app
from functools import lru_cache
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import os
import hashlib
from datetime import datetime, timedelta

map_api = Blueprint('map_api', __name__, url_prefix='/api/map')

# Cache directory for map thumbnails
CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'cache', 'maps')
os.makedirs(CACHE_DIR, exist_ok=True)

# Cache expiration (7 days)
CACHE_EXPIRATION_DAYS = 7

# Map configuration
MAP_CONFIG = {
    'width': 400,
    'height': 300,
    'zoom': 15,
    'max_file_size': 200 * 1024,  # 200KB
    'format': 'png',
    'quality': 85
}


def get_cache_key(lat, lng, width, height, zoom):
    """Generate cache key for map thumbnail"""
    key_string = f"{lat}_{lng}_{width}_{height}_{zoom}"
    return hashlib.md5(key_string.encode()).hexdigest()


def get_cached_thumbnail(cache_key):
    """Get cached thumbnail if exists and not expired"""
    cache_path = os.path.join(CACHE_DIR, f"{cache_key}.png")
    
    if os.path.exists(cache_path):
        # Check if cache is expired
        file_time = datetime.fromtimestamp(os.path.getmtime(cache_path))
        if datetime.now() - file_time < timedelta(days=CACHE_EXPIRATION_DAYS):
            return cache_path
        else:
            # Remove expired cache
            try:
                os.remove(cache_path)
            except:
                pass
    
    return None


def save_thumbnail_cache(cache_key, image_data):
    """Save thumbnail to cache"""
    try:
        cache_path = os.path.join(CACHE_DIR, f"{cache_key}.png")
        with open(cache_path, 'wb') as f:
            f.write(image_data)
        return cache_path
    except Exception as e:
        current_app.logger.error(f"Failed to save thumbnail cache: {e}")
        return None


def generate_static_map(lat, lng, width, height, zoom):
    """
    Generate static map image using OpenStreetMap tiles
    
    Args:
        lat: Latitude
        lng: Longitude
        width: Image width
        height: Image height
        zoom: Zoom level
    
    Returns:
        BytesIO: Image data
    """
    try:
        # Calculate tile coordinates
        n = 2.0 ** zoom
        x_tile = int((lng + 180.0) / 360.0 * n)
        y_tile = int((1.0 - (lat * 3.14159265359 / 180.0).tan().asinh() / 3.14159265359) / 2.0 * n)
        
        # Create image
        img = Image.new('RGB', (width, height), color='#E5E5E5')
        draw = ImageDraw.Draw(img)
        
        # Download and composite tiles
        tile_size = 256
        tiles_x = (width // tile_size) + 2
        tiles_y = (height // tile_size) + 2
        
        for i in range(tiles_x):
            for j in range(tiles_y):
                tile_x = x_tile + i - tiles_x // 2
                tile_y = y_tile + j - tiles_y // 2
                
                # Download tile from OpenStreetMap
                tile_url = f"https://tile.openstreetmap.org/{zoom}/{tile_x}/{tile_y}.png"
                
                try:
                    response = requests.get(tile_url, timeout=5, headers={
                        'User-Agent': 'BuggyCall/1.0'
                    })
                    
                    if response.status_code == 200:
                        tile_img = Image.open(BytesIO(response.content))
                        
                        # Calculate position
                        pos_x = (i - tiles_x // 2) * tile_size + width // 2
                        pos_y = (j - tiles_y // 2) * tile_size + height // 2
                        
                        img.paste(tile_img, (pos_x, pos_y))
                except Exception as e:
                    current_app.logger.warning(f"Failed to download tile {tile_x},{tile_y}: {e}")
                    continue
        
        # Add marker at center
        center_x = width // 2
        center_y = height // 2
        
        # Draw marker (red pin)
        marker_size = 20
        draw.ellipse(
            [center_x - marker_size, center_y - marker_size, 
             center_x + marker_size, center_y + marker_size],
            fill='#E74C3C',
            outline='#FFFFFF',
            width=3
        )
        
        # Draw marker shadow
        draw.ellipse(
            [center_x - marker_size//2, center_y + marker_size,
             center_x + marker_size//2, center_y + marker_size + 10],
            fill='#00000040'
        )
        
        # Optimize image size
        output = BytesIO()
        img.save(output, format='PNG', optimize=True, quality=MAP_CONFIG['quality'])
        output.seek(0)
        
        return output
        
    except Exception as e:
        current_app.logger.error(f"Failed to generate static map: {e}")
        raise


def generate_fallback_image(width, height, message="Konum bilgisi mevcut değil"):
    """
    Generate fallback image when coordinates are not available
    
    Args:
        width: Image width
        height: Image height
        message: Message to display
    
    Returns:
        BytesIO: Image data
    """
    try:
        # Create image with gradient background
        img = Image.new('RGB', (width, height), color='#ECF0F1')
        draw = ImageDraw.Draw(img)
        
        # Draw gradient background
        for y in range(height):
            color_value = int(236 + (y / height) * 20)  # Gradient from #ECF0F1 to darker
            draw.line([(0, y), (width, y)], fill=(color_value, color_value, color_value + 10))
        
        # Draw icon (map pin)
        center_x = width // 2
        center_y = height // 2 - 20
        
        # Pin body
        pin_size = 30
        draw.ellipse(
            [center_x - pin_size, center_y - pin_size,
             center_x + pin_size, center_y + pin_size],
            fill='#95A5A6',
            outline='#7F8C8D',
            width=2
        )
        
        # Pin point
        draw.polygon(
            [
                (center_x, center_y + pin_size),
                (center_x - pin_size//2, center_y),
                (center_x + pin_size//2, center_y)
            ],
            fill='#95A5A6',
            outline='#7F8C8D'
        )
        
        # Draw text
        try:
            # Try to use a nice font
            font = ImageFont.truetype("arial.ttf", 16)
        except:
            # Fallback to default font
            font = ImageFont.load_default()
        
        # Calculate text position
        text_bbox = draw.textbbox((0, 0), message, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_x = (width - text_width) // 2
        text_y = center_y + pin_size + 20
        
        # Draw text with shadow
        draw.text((text_x + 1, text_y + 1), message, fill='#00000040', font=font)
        draw.text((text_x, text_y), message, fill='#2C3E50', font=font)
        
        # Save to BytesIO
        output = BytesIO()
        img.save(output, format='PNG', optimize=True)
        output.seek(0)
        
        return output
        
    except Exception as e:
        current_app.logger.error(f"Failed to generate fallback image: {e}")
        raise


@map_api.route('/thumbnail', methods=['GET'])
def get_map_thumbnail():
    """
    Generate map thumbnail for given coordinates
    
    Query Parameters:
        lat (float): Latitude
        lng (float): Longitude
        width (int, optional): Image width (default: 400)
        height (int, optional): Image height (default: 300)
        zoom (int, optional): Zoom level (default: 15)
    
    Returns:
        PNG image or fallback image if coordinates are invalid
    
    Requirements: 15.1, 15.2, 15.3, 15.4, 15.5
    """
    try:
        # Get parameters
        lat = request.args.get('lat', type=float)
        lng = request.args.get('lng', type=float)
        width = request.args.get('width', MAP_CONFIG['width'], type=int)
        height = request.args.get('height', MAP_CONFIG['height'], type=int)
        zoom = request.args.get('zoom', MAP_CONFIG['zoom'], type=int)
        
        # Validate dimensions
        width = min(max(width, 200), 800)  # Between 200-800px
        height = min(max(height, 150), 600)  # Between 150-600px
        zoom = min(max(zoom, 10), 18)  # Between 10-18
        
        # Check if coordinates are provided
        if lat is None or lng is None:
            # Return fallback image
            current_app.logger.info("No coordinates provided, returning fallback image")
            fallback = generate_fallback_image(width, height)
            return send_file(
                fallback,
                mimetype='image/png',
                as_attachment=False,
                download_name='map_fallback.png'
            )
        
        # Validate coordinates
        if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
            current_app.logger.warning(f"Invalid coordinates: lat={lat}, lng={lng}")
            fallback = generate_fallback_image(width, height, "Geçersiz konum")
            return send_file(
                fallback,
                mimetype='image/png',
                as_attachment=False,
                download_name='map_invalid.png'
            )
        
        # Generate cache key
        cache_key = get_cache_key(lat, lng, width, height, zoom)
        
        # Check cache
        cached_path = get_cached_thumbnail(cache_key)
        if cached_path:
            current_app.logger.info(f"Serving cached thumbnail: {cache_key}")
            return send_file(
                cached_path,
                mimetype='image/png',
                as_attachment=False,
                download_name='map_thumbnail.png'
            )
        
        # Generate new thumbnail
        current_app.logger.info(f"Generating new thumbnail: lat={lat}, lng={lng}")
        image_data = generate_static_map(lat, lng, width, height, zoom)
        
        # Save to cache
        image_bytes = image_data.getvalue()
        save_thumbnail_cache(cache_key, image_bytes)
        
        # Check file size
        file_size = len(image_bytes)
        if file_size > MAP_CONFIG['max_file_size']:
            current_app.logger.warning(
                f"Thumbnail size ({file_size} bytes) exceeds limit "
                f"({MAP_CONFIG['max_file_size']} bytes)"
            )
        
        # Return image
        image_data.seek(0)
        return send_file(
            image_data,
            mimetype='image/png',
            as_attachment=False,
            download_name='map_thumbnail.png'
        )
        
    except Exception as e:
        current_app.logger.error(f"Error generating map thumbnail: {e}")
        
        # Return fallback image on error
        try:
            fallback = generate_fallback_image(
                MAP_CONFIG['width'],
                MAP_CONFIG['height'],
                "Harita yüklenemedi"
            )
            return send_file(
                fallback,
                mimetype='image/png',
                as_attachment=False,
                download_name='map_error.png'
            )
        except:
            # Last resort: return error response
            return jsonify({
                'error': 'Failed to generate map thumbnail',
                'message': str(e)
            }), 500


@map_api.route('/clear-cache', methods=['POST'])
def clear_map_cache():
    """
    Clear map thumbnail cache
    
    Admin only endpoint to clear cached map thumbnails
    
    Returns:
        JSON response with number of files deleted
    """
    try:
        # TODO: Add admin authentication check
        
        deleted_count = 0
        for filename in os.listdir(CACHE_DIR):
            if filename.endswith('.png'):
                try:
                    os.remove(os.path.join(CACHE_DIR, filename))
                    deleted_count += 1
                except Exception as e:
                    current_app.logger.error(f"Failed to delete cache file {filename}: {e}")
        
        return jsonify({
            'success': True,
            'message': f'Cleared {deleted_count} cached thumbnails',
            'deleted_count': deleted_count
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error clearing map cache: {e}")
        return jsonify({
            'error': 'Failed to clear cache',
            'message': str(e)
        }), 500
