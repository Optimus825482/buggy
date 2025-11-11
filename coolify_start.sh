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

# 2. Database reset (if RESET_DB=true)
if [ "$RESET_DB" = "true" ]; then
    echo ""
    echo "🔥 RESETTING DATABASE..."
    python reset_database.py
    if [ $? -eq 0 ]; then
        echo "✅ Database reset completed"
    else
        echo "❌ Database reset failed"
        exit 1
    fi
fi

# 3. Column fix (add missing push notification columns)
echo ""
echo "⏳ Fixing missing columns..."
python railway_fix_columns.py
if [ $? -eq 0 ]; then
    echo "✅ Column fix completed"
else
    echo "⚠️  Column fix failed, continuing..."
fi

# 4. Migration fix
echo ""
echo "⏳ Running migration fix..."
python fix_railway_migration.py
if [ $? -eq 0 ]; then
    echo "✅ Migration fix completed"
else
    echo "❌ Migration fix failed"
    exit 1
fi

# 5. Create initial data
echo ""
echo "⏳ Creating initial data..."
python scripts/create_initial_data.py || echo "⚠️  Initial data creation failed, continuing..."

# 6. Start application
echo ""
echo "============================================================"
echo "🚀 Starting Gunicorn server..."
echo "============================================================"

# Port'u environment'tan al, yoksa 5000 kullan
PORT=${PORT:-5000}

exec gunicorn --worker-class gevent \
    -w 1 \
    --bind 0.0.0.0:$PORT \
    --timeout 120 \
    --keep-alive 5 \
    --log-level info \
    --access-logfile - \
    --error-logfile - \
    wsgi:app
