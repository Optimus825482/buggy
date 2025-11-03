# Railway Deployment Troubleshooting Guide

## Common Deployment Errors and Solutions

### 1. Build Fails During Nix Package Installation

**Symptoms:**
```
copying path '/nix/store/...' from 'https://cache.nixos.org'...
Deploy failed
```

**Causes:**
- Incompatible Nix packages
- Network issues downloading packages
- Package version conflicts

**Solutions:**

1. **Check nixpacks.toml configuration:**
```toml
[phases.setup]
nixPkgs = ["python311", "python311Packages.pip", "gcc", "mysql80"]
```

2. **Verify Python version compatibility:**
```bash
# In build logs, look for:
python --version
# Should show: Python 3.11.x
```

3. **Check for package conflicts:**
- Remove unnecessary packages from nixPkgs
- Use pip for Python packages, not Nix

4. **Retry deployment:**
- Sometimes transient network issues cause failures
- Click "Redeploy" in Railway dashboard

### 2. Application Fails to Start

**Symptoms:**
```
Application error
Health check failed
```

**Causes:**
- Missing environment variables
- Database connection failure
- Import errors
- Migration failures

**Solutions:**

1. **Check Railway logs:**
```bash
railway logs
```

2. **Verify environment variables:**
```bash
# Required variables:
MYSQL_PUBLIC_URL=mysql://user:pass@host:port/database
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-key
FLASK_ENV=production
```

3. **Test database connection:**
- Go to MySQL service in Railway
- Check "Connect" tab
- Verify MYSQL_PUBLIC_URL is correct

4. **Check migration logs:**
```
Look for:
"Running database migrations..."
"✅ Database migrations completed successfully"
```

### 3. Database Connection Errors

**Symptoms:**
```
❌ Database health check failed
Could not connect to MySQL server
Access denied for user
```

**Causes:**
- Incorrect MYSQL_PUBLIC_URL
- MySQL service not running
- Network connectivity issues
- Wrong credentials

**Solutions:**

1. **Verify MYSQL_PUBLIC_URL format:**
```
Correct: mysql://root:password@host.railway.app:6543/railway
Wrong: mysql://root:password@:/railway (missing host)
```

2. **Get correct URL from Railway:**
- Click MySQL service
- Go to "Variables" tab
- Copy MYSQL_PUBLIC_URL
- Paste into Application service variables

3. **Check MySQL service status:**
- Ensure MySQL service is running (green indicator)
- Check MySQL logs for errors

4. **Test connection manually:**
```bash
# Use Railway CLI
railway run python scripts/verify_railway_deployment.py
```

### 4. Health Check Timeout

**Symptoms:**
```
Health check timeout
Application not responding
```

**Causes:**
- Application taking too long to start
- Migrations blocking startup
- Database connection slow

**Solutions:**

1. **Increase health check timeout:**
```json
// railway.json
{
  "deploy": {
    "healthcheckTimeout": 100
  }
}
```

2. **Check if migrations are running:**
```
Look for in logs:
"Running database migrations..."
```

3. **Verify health endpoint works:**
```bash
curl https://your-app.railway.app/health
```

### 5. Gevent/Eventlet Worker Errors

**Symptoms:**
```
ImportError: cannot import name 'eventlet'
Worker class 'eventlet' not found
```

**Causes:**
- Conflicting worker configurations
- Missing gevent dependency
- Wrong worker class specified

**Solutions:**

1. **Use gevent exclusively:**
```toml
# nixpacks.toml
[start]
cmd = "gunicorn --worker-class gevent -w 1 ..."
```

2. **Update requirements.txt:**
```
gevent==24.2.1
gevent-websocket==0.10.1
greenlet==3.0.3
# Remove: eventlet
```

3. **Verify worker in logs:**
```
Look for:
"Using worker: gevent"
```

### 6. Migration Failures

**Symptoms:**
```
❌ Migration failed
alembic.util.exc.CommandError
```

**Causes:**
- Missing migrations directory
- Database schema conflicts
- SQL syntax errors

**Solutions:**

1. **Check migrations directory exists:**
```bash
# Should exist: migrations/versions/
```

2. **Run migrations manually:**
```bash
railway run python scripts/run_migrations.py
```

3. **Check migration logs:**
```
Look for specific SQL errors
Check which migration file failed
```

4. **Reset database (CAUTION - loses data):**
```bash
# In Railway MySQL service
# Drop all tables and redeploy
```

### 7. WebSocket Connection Issues

**Symptoms:**
```
WebSocket connection failed
Real-time updates not working
```

**Causes:**
- Wrong worker class (not gevent)
- CORS configuration issues
- Proxy/load balancer issues

**Solutions:**

1. **Verify gevent worker:**
```bash
# In logs:
"Using worker: gevent"
```

2. **Check CORS configuration:**
```python
# app/config.py
CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'https://your-app.railway.app').split(',')
```

3. **Test WebSocket endpoint:**
```javascript
// In browser console
const socket = io('https://your-app.railway.app');
socket.on('connect', () => console.log('Connected!'));
```

### 8. Import Errors

**Symptoms:**
```
ModuleNotFoundError: No module named 'flask'
ImportError: cannot import name 'X'
```

**Causes:**
- Missing dependencies in requirements.txt
- Incorrect Python version
- Build cache issues

**Solutions:**

1. **Verify requirements.txt:**
```bash
# Check all dependencies are listed
pip freeze > requirements.txt
```

2. **Clear build cache:**
- In Railway dashboard
- Settings → Clear Build Cache
- Redeploy

3. **Check Python version:**
```bash
# In build logs:
python --version
# Should be 3.11.x
```

## How to Read Railway Logs

### Accessing Logs

1. **Via Dashboard:**
   - Go to your Railway project
   - Click on your service
   - Click "Deployments" tab
   - Click on latest deployment
   - Click "View Logs"

2. **Via CLI:**
```bash
railway logs
railway logs --follow  # Real-time logs
```

### Log Sections

1. **Build Phase:**
```
Installing Nix packages...
Installing Python dependencies...
Running build commands...
```

2. **Migration Phase:**
```
Running database migrations...
✅ Database migrations completed successfully
```

3. **Startup Phase:**
```
✅ Application initialized successfully
[INFO] Listening at: http://0.0.0.0:PORT
[INFO] Using worker: gevent
```

4. **Runtime Phase:**
```
GET /health 200
POST /api/login 200
```

### Key Log Patterns

**Success Indicators:**
```
✅ Dependencies OK
✅ Database health check passed
✅ Database migrations completed successfully
✅ Application initialized successfully
```

**Error Indicators:**
```
❌ Database health check failed
❌ Migration failed
❌ Failed to parse MYSQL_PUBLIC_URL
Error: ...
Exception: ...
```

## Debug Checklist

When deployment fails, check in this order:

### 1. Environment Variables
- [ ] MYSQL_PUBLIC_URL is set and correct
- [ ] SECRET_KEY is set (not default)
- [ ] JWT_SECRET_KEY is set (not default)
- [ ] FLASK_ENV=production
- [ ] CORS_ORIGINS includes your Railway URL

### 2. MySQL Service
- [ ] MySQL service is running (green)
- [ ] Can connect to MySQL from Railway CLI
- [ ] MYSQL_PUBLIC_URL has correct format
- [ ] Database name is correct

### 3. Build Configuration
- [ ] nixpacks.toml has correct packages
- [ ] requirements.txt has all dependencies
- [ ] No conflicting packages (eventlet removed)
- [ ] Build logs show "Dependencies OK"

### 4. Start Command
- [ ] Same command in nixpacks.toml and railway.json
- [ ] Uses gevent worker (not eventlet)
- [ ] Runs migrations before gunicorn
- [ ] Binds to 0.0.0.0:$PORT

### 5. Application Code
- [ ] No syntax errors
- [ ] All imports work
- [ ] wsgi.py doesn't have background threads
- [ ] Health endpoint responds

### 6. Database
- [ ] Migrations run successfully
- [ ] Critical tables exist
- [ ] Initial data created
- [ ] Admin user exists

## Quick Fixes

### Force Redeploy
```bash
# Via CLI
railway up --force

# Via Dashboard
# Click "Redeploy" button
```

### Reset Database
```bash
# CAUTION: This deletes all data!
# In Railway MySQL service:
# 1. Click "Data" tab
# 2. Run: DROP DATABASE railway; CREATE DATABASE railway;
# 3. Redeploy application
```

### View Real-time Logs
```bash
railway logs --follow
```

### Test Locally with Railway Environment
```bash
railway run python wsgi.py
```

### Manual Migration
```bash
railway run python scripts/run_migrations.py
```

## Getting Help

### Railway Support
- Documentation: https://docs.railway.app
- Discord: https://discord.gg/railway
- Status: https://status.railway.app

### Application Logs
- Check Railway deployment logs
- Look for error messages with ❌
- Check stack traces for details

### Verification Script
```bash
# After deployment
railway run python scripts/verify_railway_deployment.py
```

## Prevention Tips

1. **Test locally first:**
```bash
# Install nixpacks
curl -sSL https://nixpacks.com/install.sh | bash

# Build locally
nixpacks build . --name buggycall

# Test
docker run -p 5000:5000 buggycall
```

2. **Use environment variables:**
- Never hardcode secrets
- Use Railway's variable management
- Reference variables in code with os.getenv()

3. **Monitor deployments:**
- Watch build logs
- Check health endpoint after deploy
- Run verification script

4. **Keep dependencies updated:**
- Regularly update requirements.txt
- Test compatibility locally
- Pin versions for stability

5. **Document changes:**
- Update RAILWAY_DEPLOYMENT.md
- Note any configuration changes
- Keep troubleshooting guide current
