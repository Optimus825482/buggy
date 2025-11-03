"""
Buggy Call - Main Entry Point
"""
from app import create_app, socketio
import os

# Create Flask app
app = create_app()

if __name__ == '__main__':
    # Get configuration
    debug = app.config['DEBUG']
    port = int(os.getenv('PORT', 5000))
    host = os.getenv('HOST', '0.0.0.0')
    
    # Run with SocketIO
    socketio.run(app, 
                host=host, 
                port=port, 
                debug=debug,
                use_reloader=debug,
                log_output=debug)
