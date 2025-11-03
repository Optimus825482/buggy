"""
Setup Check Middleware
Checks if initial setup is completed
"""
from flask import request, jsonify, redirect, url_for
from functools import wraps
import os


def is_setup_completed():
    """Check if initial setup is completed"""
    # Check if setup marker file exists
    setup_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.setup_completed')
    return os.path.exists(setup_file)


def mark_setup_completed():
    """Mark setup as completed"""
    setup_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.setup_completed')
    with open(setup_file, 'w') as f:
        f.write('1')


def require_setup(fn):
    """Decorator to require setup completion"""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not is_setup_completed():
            # Allow setup endpoints
            if request.endpoint and 'setup' in request.endpoint:
                return fn(*args, **kwargs)
            
            # Redirect to setup
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({
                    'error': 'Setup required',
                    'message': 'Lütfen önce kurulum sihirbazını tamamlayın',
                    'setup_url': '/setup'
                }), 403
            else:
                return redirect('/setup')
        
        return fn(*args, **kwargs)
    return wrapper


def setup_middleware(app):
    """Register setup check middleware"""
    
    @app.before_request
    def check_setup():
        """Check if setup is completed before each request"""
        # Skip setup check for static files, setup endpoints, and system reset
        if request.endpoint in ['static', None] or \
           (request.endpoint and ('setup' in request.endpoint or 'system_reset' in request.endpoint)) or \
           request.path.startswith('/static/') or \
           request.path.startswith('/buggysystemreset') or \
           request.path.startswith('/api/system-reset'):
            return None
        
        # Check if setup is completed
        if not is_setup_completed():
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({
                    'error': 'Setup required',
                    'message': 'Lütfen önce kurulum sihirbazını tamamlayın',
                    'setup_url': '/setup'
                }), 403
            else:
                return redirect('/setup')
        
        return None
