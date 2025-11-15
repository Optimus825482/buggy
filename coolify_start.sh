#!/bin/bash
# Coolify Startup Script
# Veritabanı migration'ını düzeltir ve uygulamayı başlatır

set -e  # Exit on error

echo "============================================================"
echo "🚀 Shuttle Call - Coolify Startup"
echo "============================================================"

# 1. Environment check
echo "⏳ Checking environment variables..."
python check_railway_env.py
if [ $? -ne 0 ]; then
    echo "❌ Environment check failed"
    exit 1
fi

# 2. Database connection check
echo ""
echo "⏳ Checking database connection..."
python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.session.execute('SELECT 1')" || {
    echo "❌ Database connection failed"
    exit 1
}
echo "✅ Database connection OK"

# 3. Create initial data (optional - skip if exists)
if [ -f "scripts/create_initial_data.py" ]; then
    echo ""
    echo "⏳ Creating initial data..."
    python scripts/create_initial_data.py || echo "⚠️  Initial data creation skipped"
fi

# 6. Start application
echo ""
echo "============================================================"
echo "🚀 Starting Gunicorn server..."
echo "============================================================"

# Port'u environment'tan al, yoksa 8000 kullan
PORT=${PORT:-8000}

exec gunicorn --worker-class gevent \
    -w 1 \
    --bind 0.0.0.0:$PORT \
    --timeout 120 \
    --keep-alive 5 \
    --log-level info \
    --access-logfile - \
    --error-logfile - \
    wsgi:app
