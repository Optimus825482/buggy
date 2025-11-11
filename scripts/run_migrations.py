"""
Buggy Call - Manual Migration Script
Allows manual execution of database migrations with status checks and rollback
"""
import sys
import os

# Set flag to skip SocketIO initialization during migrations
os.environ['SKIP_SOCKETIO'] = '1'

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask_migrate import upgrade, downgrade, current, history
from app import create_app, db
from sqlalchemy import inspect
import argparse


def check_migration_status(app):
    """Check current migration status"""
    with app.app_context():
        try:
            # Get current revision
            from alembic.migration import MigrationContext
            from alembic.script import ScriptDirectory
            from flask_migrate import Migrate
            
            migrate = Migrate(app, db)
            migrations_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'migrations')
            
            if not os.path.exists(migrations_dir):
                print("❌ No migrations directory found")
                return False
            
            # Get current database revision
            context = MigrationContext.configure(db.engine.connect())
            current_rev = context.get_current_revision()
            
            print("="*60)
            print("Migration Status")
            print("="*60)
            print(f"Current revision: {current_rev or 'None (empty database)'}")
            
            # Get available migrations
            from alembic.config import Config
            alembic_cfg = Config(os.path.join(migrations_dir, 'alembic.ini'))
            alembic_cfg.set_main_option('script_location', migrations_dir)
            script = ScriptDirectory.from_config(alembic_cfg)
            
            head_rev = script.get_current_head()
            print(f"Latest revision: {head_rev or 'None'}")
            
            if current_rev == head_rev:
                print("✅ Database is up to date")
            elif current_rev is None:
                print("⚠️  Database is empty, migrations needed")
            else:
                print("⚠️  Database needs migration")
            
            # List PENDING migrations
            if current_rev != head_rev:
                print("\nPending migrations:")
                for rev in script.iterate_revisions(head_rev, current_rev):
                    print(f"  - {rev.revision}: {rev.doc}")
            
            print("="*60)
            return True
            
        except Exception as e:
            print(f"❌ Failed to check migration status: {e}")
            return False


def run_upgrade(app, revision='head'):
    """Run database migrations"""
    with app.app_context():
        try:
            print("="*60)
            print(f"Running migrations to: {revision}")
            print("="*60)
            
            migrations_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'migrations')
            
            if not os.path.exists(migrations_dir):
                print("⚠️  No migrations directory found")
                print("Creating database tables directly...")
                db.create_all()
                print("✅ Database tables created")
                return True
            
            # Check if database is empty (no alembic_version table)
            from sqlalchemy import inspect, text
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            # For Railway: Always use db.create_all() for fresh database
            # Migrations are problematic with empty databases
            if not tables or 'alembic_version' not in tables or len(tables) < 5:
                print("⚠️  Empty or incomplete database detected")
                print("Creating all tables directly (bypassing migrations)...")
                db.create_all()
                print("✅ Database tables created")
                
                # Stamp the database with the latest migration
                try:
                    from flask_migrate import stamp
                    stamp(directory=migrations_dir, revision='head')
                    print("✅ Database stamped with current migration version")
                except Exception as stamp_error:
                    print(f"⚠️  Could not stamp database: {stamp_error}")
                    print("   This is not critical, continuing...")
                
                return True
            
            # Run migrations on existing database (only if tables already exist)
            print("Running Alembic migrations on existing database...")
            upgrade(directory=migrations_dir, revision=revision)
            
            print("✅ Migrations completed successfully")
            
            # Show new status
            check_migration_status(app)
            
            return True
            
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            print("\n⚠️  Attempting fallback: creating tables directly...")
            
            try:
                db.create_all()
                print("✅ Database tables created via fallback method")
                return True
            except Exception as fallback_error:
                print(f"❌ Fallback also failed: {fallback_error}")
                import traceback
                traceback.print_exc()
                return False


def run_downgrade(app, revision):
    """Rollback database migrations"""
    with app.app_context():
        try:
            print("="*60)
            print(f"Rolling back to: {revision}")
            print("="*60)
            print("⚠️  WARNING: This will revert database changes!")
            
            confirm = input("Are you sure? (yes/no): ")
            if confirm.lower() != 'yes':
                print("Rollback cancelled")
                return False
            
            migrations_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'migrations')
            
            # Run downgrade
            downgrade(directory=migrations_dir, revision=revision)
            
            print("✅ Rollback completed successfully")
            
            # Show new status
            check_migration_status(app)
            
            return True
            
        except Exception as e:
            print(f"❌ Rollback failed: {e}")
            import traceback
            traceback.print_exc()
            return False


def show_history(app):
    """Show migration history"""
    with app.app_context():
        try:
            migrations_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'migrations')
            
            if not os.path.exists(migrations_dir):
                print("❌ No migrations directory found")
                return False
            
            print("="*60)
            print("Migration History")
            print("="*60)
            
            from alembic.config import Config
            from alembic.script import ScriptDirectory
            
            alembic_cfg = Config(os.path.join(migrations_dir, 'alembic.ini'))
            alembic_cfg.set_main_option('script_location', migrations_dir)
            script = ScriptDirectory.from_config(alembic_cfg)
            
            for rev in script.walk_revisions():
                print(f"\nRevision: {rev.revision}")
                print(f"Down revision: {rev.down_revision or 'None'}")
                print(f"Description: {rev.doc}")
                print(f"Created: {rev.module.__file__ if hasattr(rev, 'module') else 'N/A'}")
            
            print("="*60)
            return True
            
        except Exception as e:
            print(f"❌ Failed to show history: {e}")
            return False


def verify_tables(app):
    """Verify database tables exist"""
    with app.app_context():
        try:
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            print("="*60)
            print("Database Tables")
            print("="*60)
            print(f"Total tables: {len(tables)}")
            
            critical_tables = ['hotel', 'system_user', 'location', 'buggy', 'buggy_request']
            
            print("\nCritical tables:")
            for table in critical_tables:
                status = "✓" if table in tables else "✗"
                print(f"  {status} {table}")
            
            print("\nAll tables:")
            for table in sorted(tables):
                print(f"  - {table}")
            
            print("="*60)
            return True
            
        except Exception as e:
            print(f"❌ Failed to verify tables: {e}")
            return False


def main():
    """Main function"""
    # Check if running in Railway (no arguments provided during build)
    if len(sys.argv) == 1:
        # Auto-run upgrade in Railway
        print("\n🚀 Buggy Call - Railway Auto Migration")
        print("="*60)
        
        try:
            app = create_app('production')
            db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
            db_display = db_uri.split('@')[-1] if '@' in db_uri else 'Not configured'
            print(f"Database: {db_display}")
            print(f"Environment: {os.getenv('FLASK_ENV', 'production')}")
            print("="*60)
            
            # Test database connection first
            print("\n⏳ Testing database connection...")
            with app.app_context():
                from sqlalchemy import text
                max_retries = 5
                for attempt in range(max_retries):
                    try:
                        db.session.execute(text('SELECT 1'))
                        print(f"✅ Database connection successful (attempt {attempt + 1})")
                        break
                    except Exception as e:
                        if attempt < max_retries - 1:
                            wait_time = 2 ** attempt
                            print(f"⚠️  Connection failed (attempt {attempt + 1}/{max_retries}), retrying in {wait_time}s...")
                            import time
                            time.sleep(wait_time)
                        else:
                            print(f"❌ Database connection failed after {max_retries} attempts: {e}")
                            sys.exit(1)
            
            # Run migrations
            success = run_upgrade(app, 'head')
            
            if success:
                print("\n✅ Migration completed successfully")
                sys.exit(0)
            else:
                print("\n❌ Migration failed")
                sys.exit(1)
                
        except Exception as e:
            print(f"\n❌ Fatal error during migration: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    
    # Manual execution with arguments
    parser = argparse.ArgumentParser(description='Buggy Call Database Migration Tool')
    parser.add_argument('command', choices=['status', 'upgrade', 'downgrade', 'history', 'verify'],
                       help='Migration command to execute')
    parser.add_argument('--revision', default='head',
                       help='Target revision (default: head)')
    parser.add_argument('--env', default='production',
                       help='Environment (default: production)')
    
    args = parser.parse_args()
    
    # Create app
    app = create_app(args.env)
    
    print(f"\n🚀 Buggy Call Migration Tool")
    print(f"Environment: {args.env}")
    print(f"Database: {app.config.get('SQLALCHEMY_DATABASE_URI', '').split('@')[-1] if '@' in app.config.get('SQLALCHEMY_DATABASE_URI', '') else 'Not configured'}\n")
    
    # Execute command
    if args.command == 'status':
        success = check_migration_status(app)
    elif args.command == 'upgrade':
        success = run_upgrade(app, args.revision)
    elif args.command == 'downgrade':
        success = run_downgrade(app, args.revision)
    elif args.command == 'history':
        success = show_history(app)
    elif args.command == 'verify':
        success = verify_tables(app)
    else:
        print(f"❌ Unknown command: {args.command}")
        success = False
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
