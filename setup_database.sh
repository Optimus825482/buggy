#!/bin/bash
# Buggy Call - Database Setup Script
# Bu script database migration sistemini otomatik olarak kurar

echo "============================================================"
echo "Buggy Call - Database Migration Setup"
echo "============================================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if flask is available
if ! command -v flask &> /dev/null; then
    echo -e "${RED}❌ Flask command not found!${NC}"
    echo "Please activate your virtual environment first:"
    echo "  source venv/bin/activate  # Linux/Mac"
    echo "  venv\\Scripts\\activate     # Windows"
    exit 1
fi

echo -e "${GREEN}✅ Flask found${NC}"
echo ""

# Step 1: Initialize migrations
echo "📁 Step 1: Initializing migrations..."
if [ -d "migrations" ]; then
    echo -e "${YELLOW}⚠️  Migrations folder already exists${NC}"
    read -p "Do you want to reinitialize? (yes/no): " response
    if [ "$response" != "yes" ]; then
        echo -e "${RED}❌ Aborted${NC}"
        exit 0
    fi
    rm -rf migrations
    echo -e "${GREEN}✅ Removed existing migrations${NC}"
fi

flask db init
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Migrations initialized${NC}"
else
    echo -e "${RED}❌ Failed to initialize migrations${NC}"
    exit 1
fi
echo ""

# Step 2: Create initial migration
echo "📝 Step 2: Creating initial migration..."
flask db migrate -m "Initial migration - all models"
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Migration created${NC}"
else
    echo -e "${RED}❌ Failed to create migration${NC}"
    exit 1
fi
echo ""

# Step 3: Apply migration
echo "⬆️  Step 3: Applying migration to database..."
flask db upgrade
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Migration applied${NC}"
else
    echo -e "${RED}❌ Failed to apply migration${NC}"
    exit 1
fi
echo ""

# Step 4: Verify
echo "🔍 Step 4: Verifying migration..."
flask db current
echo ""

echo "============================================================"
echo -e "${GREEN}✅ Database migration setup completed!${NC}"
echo "============================================================"
echo ""
echo "📊 What was created:"
echo "  - migrations/ folder with Alembic configuration"
echo "  - Initial migration file in migrations/versions/"
echo "  - All database tables created"
echo ""
echo "💡 Useful commands:"
echo "  flask db current   - Show current migration"
echo "  flask db history   - Show migration history"
echo "  flask db upgrade   - Apply pending migrations"
echo "  flask db downgrade - Rollback last migration"
echo ""
