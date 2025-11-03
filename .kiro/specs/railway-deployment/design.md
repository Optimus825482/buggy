# Design Document - Railway Deployment

## Overview

Bu doküman, Buggy Call sisteminin Railway platformuna deploy edilmesi için teknik tasarımı açıklar. Sistem, Railway'in sağladığı MySQL veritabanı ile çalışacak ve production ortamında güvenli, ölçeklenebilir bir şekilde hizmet verecektir.

## Architecture

### Deployment Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Railway Platform                      │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │         Buggy Call Application Service           │  │
│  │                                                   │  │
│  │  ┌─────────────┐      ┌──────────────┐         │  │
│  │  │  Gunicorn   │──────│ Flask App    │         │  │
│  │  │  (WSGI)     │      │ + SocketIO   │         │  │
│  │  └─────────────┘      └──────────────┘         │  │
│  │                              │                   │  │
│  │                              │                   │  │
│  └──────────────────────────────┼───────────────────┘  │
│                                 │                       │
│  ┌──────────────────────────────┼───────────────────┐  │
│  │         MySQL Database Service                   │  │
│  │                              │                   │  │
│  │  ┌──────────────────────────▼────────────────┐  │  │
│  │  │  MySQL 8.0                                 │  │  │
│  │  │  - All application tables                  │  │  │
│  │  │  - Alembic migrations                      │  │  │
│  │  └────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────┘  │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### Application Flow

1. **Startup Sequence**:
   - Load environment variables from Railway
   - Parse MySQL connection URL
   - Initialize Flask application
   - Run database migrations
   - Create initial data if needed
   - Start Gunicorn with eventlet workers

2. **Request Handling**:
   - Gunicorn receives HTTP/WebSocket requests
   - Flask routes handle business logic
   - SQLAlchemy manages database operations
   - SocketIO handles real-time communications

## Components and Interfaces

### 1. Railway Configuration Files

#### Procfile
Railway kullanmıyor ama start command olarak kullanılacak:
```
web: gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:$PORT wsgi:app
```

#### railway.json (Optional)
```json
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:$PORT wsgi:app",
    "healthcheckPath": "/health",
    "healthcheckTimeout": 100,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

### 2. Environment Configuration Module

**File**: `app/config.py` (Güncellenecek)

Yeni özellikler:
- Railway MySQL URL parsing
- Production-specific settings
- Environment detection

```python
class ProductionConfig(Config):
    """Production configuration with Railway support"""
    
    @staticmethod
    def init_app(app):
        # Parse Railway MySQL URL if provided
        mysql_url = os.getenv('MYSQL_PUBLIC_URL')
        if mysql_url:
            # Parse: mysql://user:password@host:port/database
            from urllib.parse import urlparse
            parsed = urlparse(mysql_url)
            
            app.config['DB_HOST'] = parsed.hostname
            app.config['DB_PORT'] = parsed.port or 3306
            app.config['DB_NAME'] = parsed.path.lstrip('/')
            app.config['DB_USER'] = parsed.username
            app.config['DB_PASSWORD'] = parsed.password
            
            # Rebuild SQLAlchemy URI
            app.config['SQLALCHEMY_DATABASE_URI'] = (
                f"mysql+pymysql://{parsed.username}:{parsed.password}"
                f"@{parsed.hostname}:{parsed.port or 3306}"
                f"/{parsed.path.lstrip('/')}?charset=utf8mb4"
            )
```

### 3. Database Initialization Script

**File**: `scripts/railway_init.py` (Yeni)

Bu script Railway'de ilk deployment'ta çalışacak:

```python
def initialize_railway_database():
    """Initialize database for Railway deployment"""
    
    # 1. Run Alembic migrations
    run_migrations()
    
    # 2. Check if initial data exists
    if not Hotel.query.first():
        create_initial_data()
    
    # 3. Verify database health
    verify_database_health()
```

### 4. Health Check Endpoint

**File**: `app/routes/health.py` (Güncellenecek)

Railway'in health check'i için:

```python
@health_bp.route('/health')
def health_check():
    """Comprehensive health check for Railway"""
    
    health_status = {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'checks': {}
    }
    
    # Database check
    try:
        db.session.execute('SELECT 1')
        health_status['checks']['database'] = 'ok'
    except Exception as e:
        health_status['checks']['database'] = 'error'
        health_status['status'] = 'unhealthy'
    
    # Application check
    health_status['checks']['application'] = 'ok'
    
    status_code = 200 if health_status['status'] == 'healthy' else 503
    return jsonify(health_status), status_code
```

### 5. WSGI Entry Point

**File**: `wsgi.py` (Güncellenecek)

Production için optimize edilmiş entry point:

```python
import os
from app import create_app, socketio, db

# Create app with production config
app = create_app('production')

# Initialize database on startup
with app.app_context():
    from scripts.railway_init import initialize_railway_database
    initialize_railway_database()

if __name__ == "__main__":
    # This is for local testing only
    # Railway will use gunicorn
    socketio.run(app)
```

### 6. Migration Management

**Alembic Configuration**: Mevcut `migrations/` klasörü kullanılacak

Railway deployment sırasında:
```bash
flask db upgrade
```

## Data Models

Mevcut modeller değişmeyecek, sadece initialization stratejisi güncellenecek:

### Initial Data Structure

```python
INITIAL_DATA = {
    'hotel': {
        'name': 'Railway Demo Hotel',
        'address': 'Cloud Deployment',
        'timezone': 'Europe/Istanbul'
    },
    'admin': {
        'username': 'admin',
        'password': 'Admin123!',  # Güçlü default password
        'email': 'admin@buggycall.railway.app'
    },
    'locations': [
        'Reception', 'Beach', 'Restaurant', 
        'Spa', 'Pool', 'Tennis Court'
    ],
    'buggies': 3  # 3 buggy with drivers
}
```

## Error Handling

### Database Connection Errors

```python
def connect_with_retry(max_retries=5, delay=2):
    """Connect to database with exponential backoff"""
    
    for attempt in range(max_retries):
        try:
            db.session.execute('SELECT 1')
            return True
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = delay * (2 ** attempt)
                app.logger.warning(
                    f"Database connection failed (attempt {attempt + 1}), "
                    f"retrying in {wait_time}s..."
                )
                time.sleep(wait_time)
            else:
                app.logger.error("Database connection failed after all retries")
                raise
```

### Application Errors

- **500 Errors**: Log to Railway logs, return generic error to user
- **Database Errors**: Retry with backoff, fallback to maintenance mode
- **WebSocket Errors**: Graceful degradation, HTTP fallback

## Testing Strategy

### Pre-Deployment Testing

1. **Local Railway Simulation**:
   ```bash
   # Set Railway-like environment
   export FLASK_ENV=production
   export MYSQL_PUBLIC_URL=mysql://user:pass@localhost:3306/testdb
   
   # Test startup
   gunicorn --worker-class eventlet -w 1 wsgi:app
   ```

2. **Database Migration Testing**:
   ```bash
   # Test migrations
   flask db upgrade
   flask db downgrade
   flask db upgrade
   ```

3. **Health Check Testing**:
   ```bash
   curl http://localhost:8000/health
   ```

### Post-Deployment Verification

1. **Health Check**: Verify `/health` returns 200
2. **Database Check**: Verify tables exist and initial data loaded
3. **Authentication Check**: Test admin login
4. **WebSocket Check**: Test real-time features
5. **QR Code Check**: Test QR code generation and scanning

## Security Considerations

### Environment Variables

Railway'de şu environment variable'lar set edilecek:

```bash
# Flask
FLASK_ENV=production
SECRET_KEY=<strong-random-key>
DEBUG=False

# Database (Railway otomatik sağlar)
MYSQL_PUBLIC_URL=mysql://root:...@host:port/railway

# JWT
JWT_SECRET_KEY=<strong-random-key>
JWT_ACCESS_TOKEN_EXPIRES=3600
JWT_REFRESH_TOKEN_EXPIRES=2592000

# CORS
CORS_ORIGINS=https://your-app.railway.app

# Application
BASE_URL=https://your-app.railway.app
APP_NAME=Buggy Call

# Optional: Redis for scaling
REDIS_URL=redis://...
```

### Security Headers

Production'da otomatik eklenen header'lar:
- `Strict-Transport-Security`: HTTPS zorunlu
- `X-Content-Type-Options`: MIME sniffing engelleme
- `X-Frame-Options`: Clickjacking koruması
- `X-XSS-Protection`: XSS koruması

### Password Security

- Admin default password güçlü olacak
- İlk login'de password değişimi zorunlu (future enhancement)
- Bcrypt ile hash (cost factor: 12)

## Performance Optimization

### Database Connection Pooling

```python
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_size': 10,           # Railway free tier için uygun
    'pool_recycle': 3600,      # 1 saat
    'pool_pre_ping': True,     # Connection health check
    'max_overflow': 5          # Extra connections
}
```

### Gunicorn Configuration

```bash
# Single worker with eventlet for WebSocket support
gunicorn --worker-class eventlet \
         -w 1 \
         --bind 0.0.0.0:$PORT \
         --timeout 120 \
         --keep-alive 5 \
         --log-level info \
         wsgi:app
```

### Static Files

Railway'de static file'lar Flask üzerinden serve edilecek (CDN future enhancement).

## Deployment Process

### Step-by-Step Deployment

1. **Railway Project Setup**:
   - Create new project
   - Add MySQL database service
   - Connect GitHub repository

2. **Environment Configuration**:
   - Set all required environment variables
   - Copy MYSQL_PUBLIC_URL from database service

3. **Deploy**:
   - Push to main branch
   - Railway automatically builds and deploys
   - Migrations run automatically
   - Health check verifies deployment

4. **Verification**:
   - Check Railway logs
   - Test health endpoint
   - Login as admin
   - Test core features

### Rollback Strategy

Railway otomatik rollback sağlar:
- Health check fail olursa önceki version'a döner
- Manuel rollback: Railway dashboard'dan previous deployment seç

## Monitoring and Logging

### Railway Logs

Tüm application log'ları Railway'in log viewer'ında görünecek:

```python
# Structured logging
app.logger.info(f"Database initialized: {table_count} tables")
app.logger.error(f"Failed to connect: {error}", exc_info=True)
```

### Metrics to Monitor

- Response time
- Error rate
- Database connection pool usage
- WebSocket connection count
- Memory usage

## Future Enhancements

1. **Redis Integration**: Multi-instance scaling için
2. **CDN**: Static file serving için
3. **Backup Strategy**: Automated database backups
4. **Monitoring**: Sentry veya similar error tracking
5. **CI/CD**: Automated testing before deployment
