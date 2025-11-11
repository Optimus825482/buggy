"""Check current database status"""
from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    print('Checking database status...\n')
    
    # Check if timeout_at column exists
    result = db.session.execute(text("""
        SELECT COLUMN_NAME 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = 'buggy_requests' 
        AND COLUMN_NAME = 'timeout_at'
    """))
    
    timeout_exists = result.fetchone() is not None
    print(f'✓ timeout_at column exists: {timeout_exists}')
    
    # Check current enum values
    result = db.session.execute(text("""
        SELECT COLUMN_TYPE 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = 'buggy_requests' 
        AND COLUMN_NAME = 'status'
    """))
    
    enum_type = result.fetchone()
    if enum_type:
        print(f'✓ Current status enum: {enum_type[0]}')
        has_unanswered = 'unanswered' in enum_type[0]
        print(f'✓ Has unanswered: {has_unanswered}')
    
    # Check if index exists
    result = db.session.execute(text("""
        SELECT INDEX_NAME 
        FROM INFORMATION_SCHEMA.STATISTICS 
        WHERE TABLE_NAME = 'buggy_requests' 
        AND INDEX_NAME = 'idx_requests_timeout_check'
    """))
    
    index_exists = result.fetchone() is not None
    print(f'✓ Index exists: {index_exists}')
    
    print('\n' + '='*50)
    if not timeout_exists or not has_unanswered or not index_exists:
        print('⚠️  Migration needed!')
        print('\nRun this command:')
        print('mysql -u root -p buggycall < migrations/add_unanswered_status_and_timeout.sql')
    else:
        print('✅ Database is up to date!')
