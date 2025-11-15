"""
Migration: Add guest_fcm_token and guest_fcm_token_expires_at fields to buggy_requests table
Date: 2025-01-15
Purpose: Move guest FCM token storage from in-memory to database for persistence
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db

app = create_app()

with app.app_context():
    print("=" * 60)
    print("ADD GUEST FCM TOKEN FIELDS MIGRATION")
    print("=" * 60)

    try:
        print("\n🔄 Adding guest_fcm_token field...")
        # Add guest_fcm_token column
        db.session.execute(db.text("""
            ALTER TABLE buggy_requests
            ADD COLUMN guest_fcm_token VARCHAR(500)
        """))

        print("🔄 Adding guest_fcm_token_expires_at field...")
        # Add guest_fcm_token_expires_at column
        db.session.execute(db.text("""
            ALTER TABLE buggy_requests
            ADD COLUMN guest_fcm_token_expires_at DATETIME
        """))

        db.session.commit()
        print("\n✅ Migration successful: Added guest_fcm_token fields")

        # Verify columns were added
        result = db.session.execute(db.text(
            "SHOW COLUMNS FROM buggy_requests WHERE Field IN ('guest_fcm_token', 'guest_fcm_token_expires_at')"
        )).fetchall()

        print(f"\n📊 New columns:")
        for row in result:
            print(f"   {row[0]}: {row[1]}")

        print("\n✅ Migration completed successfully!")

    except Exception as e:
        print(f"\n❌ Migration failed: {str(e)}")
        db.session.rollback()
        sys.exit(1)
