"""
Buggy Call - WSGI Entry Point for Production
"""
from app import create_app, socketio

app = create_app('production')

if __name__ == "__main__":
    socketio.run(app)
