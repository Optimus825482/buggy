# Eventlet Compatibility Fix for Python 3.12+

## Problem
The application was failing to start on Railway with the error:
```
AttributeError: module 'ssl' has no attribute 'wrap_socket'
```

This occurred because `eventlet==0.33.3` doesn't support Python 3.12+, where `ssl.wrap_socket()` was removed.

## Solution Applied
Switched from `eventlet` to `gevent` worker class, which is fully compatible with Python 3.12+.

### Changes Made:

1. **nixpacks.toml** - Updated worker class in start command:
   - Changed: `--worker-class eventlet` 
   - To: `--worker-class gevent`
   - Also downgraded Python from 3.13 to 3.11 for better stability

2. **Procfile** - Updated worker class:
   - Changed: `--worker-class eventlet`
   - To: `--worker-class gevent`

3. **app/config.py** - Made async mode configurable:
   - Changed: `SOCKETIO_ASYNC_MODE = 'threading'`
   - To: `SOCKETIO_ASYNC_MODE = os.getenv('SOCKETIO_ASYNC_MODE', 'gevent')`
   - This allows using `gevent` in production and `threading` in development

## Why Gevent?
- ✅ Fully compatible with Python 3.12+
- ✅ Already installed in requirements.txt
- ✅ Works seamlessly with Flask-SocketIO
- ✅ Better performance than threading mode
- ✅ Production-ready and well-maintained

## Deployment
After pushing these changes to Railway:
1. Railway will rebuild with Python 3.11
2. Gunicorn will use gevent worker class
3. Flask-SocketIO will use gevent async mode
4. Application should start successfully

## Alternative Options Considered
1. **Downgrade to Python 3.11** - Applied as additional safety measure
2. **Upgrade eventlet** - No stable version available for Python 3.12+
3. **Use threading mode** - Less performant for production WebSocket apps

## Testing
To test locally with gevent:
```bash
# Set environment variable
set SOCKETIO_ASYNC_MODE=gevent

# Run with gevent worker
gunicorn --worker-class gevent -w 1 --bind 0.0.0.0:5000 wsgi:app
```

## References
- [Eventlet Python 3.12 Issue](https://github.com/eventlet/eventlet/issues/868)
- [Flask-SocketIO Async Modes](https://flask-socketio.readthedocs.io/en/latest/deployment.html)
- [Gevent Documentation](http://www.gevent.org/)
