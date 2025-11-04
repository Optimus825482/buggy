#!/bin/bash
# Railway Startup Script
# Veritabanı migration'ını düzeltir ve uygulamayı başlatır

set -e  # Exit on error

echo "============================================================"
echo "🚀 Buggy Call - Railway Startup"
echo "============================================================"

# 1. Environment check
echo "⏳ Checking environment variables..."
python check_railway_env.py
if [ $? -ne 0 ]; then
    echo "❌ Environment check failed"
    exit 1
fi

# 2. Migration fix
echo ""
echo "⏳ Running migration fix..."
python fix_railway_migration.py
if [ $? -eq 0 ]; then
    echo "✅ Migration fix completed"
else
    echo "❌ Migration fix failed"
    exit 1
fi

# 3. Start application
echo ""
echo "============================================================"
echo "🚀 Starting Gunicorn server..."
echo "============================================================"
exec gunicorn --worker-class gevent -w 1 --bind 0.0.0.0:$PORT --timeout 120 --keep-alive 5 --log-level info wsgi:app
