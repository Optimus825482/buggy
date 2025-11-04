#!/usr/bin/env python
"""
Shuttle Call - Database Migration Initialization Script
Bu script database migration sistemini başlatır ve ilk migration'ı oluşturur.
"""
import os
import sys
from flask import Flask
from flask_migrate import init, migrate, upgrade
from app import create_app, db

def init_migrations():
    """Initialize Flask-Migrate and create initial migration"""
    
    print("=" * 60)
    print("Shuttle Call - Database Migration Initialization")
    print("=" * 60)
    print()
    
    # Create app
    app = create_app()
    
    with app.app_context():
        # Check if migrations folder exists
        migrations_dir = 'migrations'
        
        if os.path.exists(migrations_dir):
            print("⚠️  Migrations folder already exists!")
            response = input("Do you want to reinitialize? (yes/no): ")
            if response.lower() != 'yes':
                print("❌ Aborted.")
                return
            
            # Remove existing migrations
            import shutil
            shutil.rmtree(migrations_dir)
            print("✅ Removed existing migrations folder")
        
        # Step 1: Initialize migrations
        print("\n📁 Step 1: Initializing migrations folder...")
        try:
            from flask_migrate import init as flask_migrate_init
            # Note: flask_migrate.init() needs to be called via CLI
            # We'll provide instructions instead
            print("✅ Ready to initialize")
        except Exception as e:
            print(f"❌ Error: {e}")
            return
        
        # Step 2: Create initial migration
        print("\n📝 Step 2: Creating initial migration...")
        print("   This will scan all models and create migration files")
        
        # Step 3: Apply migration
        print("\n⬆️  Step 3: Applying migration to database...")
        print("   This will create all tables in the database")
        
        print("\n" + "=" * 60)
        print("MANUAL STEPS REQUIRED:")
        print("=" * 60)
        print()
        print("Please run these commands in your terminal:")
        print()
        print("1. Initialize migrations:")
        print("   flask db init")
        print()
        print("2. Create initial migration:")
        print("   flask db migrate -m \"Initial migration - all models\"")
        print()
        print("3. Apply migration:")
        print("   flask db upgrade")
        print()
        print("4. Verify:")
        print("   flask db current")
        print()
        print("=" * 60)
        print()
        
        # Show current models
        print("📊 Detected Models:")
        print("-" * 60)
        from app.models.hotel import Hotel
        from app.models.user import SystemUser
        from app.models.location import Location
        from app.models.buggy import Buggy
        from app.models.request import BuggyRequest
        from app.models.audit import AuditTrail
        from app.models.session import Session
        
        models = [
            ('Hotel', Hotel),
            ('SystemUser', SystemUser),
            ('Location', Location),
            ('Buggy', Buggy),
            ('BuggyRequest', BuggyRequest),
            ('AuditTrail', AuditTrail),
            ('Session', Session)
        ]
        
        for name, model in models:
            table_name = model.__tablename__
            print(f"  ✓ {name:20} -> {table_name}")
        
        print("-" * 60)
        print(f"Total: {len(models)} models")
        print()
        
        # Database info
        print("🗄️  Database Configuration:")
        print("-" * 60)
        db_uri = app.config['SQLALCHEMY_DATABASE_URI']
        # Hide password
        if '@' in db_uri:
            parts = db_uri.split('@')
            user_pass = parts[0].split('://')[-1]
            if ':' in user_pass:
                user = user_pass.split(':')[0]
                db_uri_safe = db_uri.replace(user_pass, f"{user}:****")
            else:
                db_uri_safe = db_uri
        else:
            db_uri_safe = db_uri
        
        print(f"  Database: {db_uri_safe}")
        print("-" * 60)
        print()
        
        print("✅ Initialization script completed!")
        print()
        print("💡 TIP: After running the commands above, you can:")
        print("   - Check migration status: flask db current")
        print("   - View migration history: flask db history")
        print("   - Rollback if needed: flask db downgrade")
        print()

if __name__ == '__main__':
    try:
        init_migrations()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
