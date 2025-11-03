"""
Buggy Call - Railway Deployment Verification Script
Verifies that Railway deployment is successful and all components are working
"""
import os
import sys
import requests
import time
from urllib.parse import urlparse

def print_header(text):
    """Print formatted header"""
    print("\n" + "="*60)
    print(text)
    print("="*60)

def print_success(text):
    """Print success message"""
    print(f"✅ {text}")

def print_error(text):
    """Print error message"""
    print(f"❌ {text}")

def print_warning(text):
    """Print warning message"""
    print(f"⚠️  {text}")

def check_environment_variables():
    """Check required environment variables"""
    print_header("Checking Environment Variables")
    
    required_vars = [
        'MYSQL_PUBLIC_URL',
        'SECRET_KEY',
        'JWT_SECRET_KEY',
        'FLASK_ENV'
    ]
    
    optional_vars = [
        'CORS_ORIGINS',
        'BASE_URL',
        'INITIAL_ADMIN_PASSWORD'
    ]
    
    all_ok = True
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            if 'PASSWORD' in var or 'SECRET' in var or 'KEY' in var:
                print_success(f"{var}: ****** (set)")
            else:
                print_success(f"{var}: {value[:50]}...")
        else:
            print_error(f"{var}: NOT SET")
            all_ok = False
    
    print("\nOptional variables:")
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            if 'PASSWORD' in var:
                print_success(f"{var}: ****** (set)")
            else:
                print_success(f"{var}: {value}")
        else:
            print_warning(f"{var}: not set (using default)")
    
    return all_ok

def check_database_connection():
    """Check database connection"""
    print_header("Checking Database Connection")
    
    mysql_url = os.getenv('MYSQL_PUBLIC_URL')
    if not mysql_url:
        print_error("MYSQL_PUBLIC_URL not set")
        return False
    
    try:
        parsed = urlparse(mysql_url)
        print_success(f"Host: {parsed.hostname}")
        print_success(f"Port: {parsed.port or 3306}")
        print_success(f"Database: {parsed.path.lstrip('/')}")
        print_success(f"User: {parsed.username}")
        
        # Try to connect
        import pymysql
        connection = pymysql.connect(
            host=parsed.hostname,
            port=parsed.port or 3306,
            user=parsed.username,
            password=parsed.password,
            database=parsed.path.lstrip('/'),
            connect_timeout=10
        )
        
        cursor = connection.cursor()
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()
        print_success(f"MySQL Version: {version[0]}")
        
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        print_success(f"Tables found: {len(tables)}")
        
        critical_tables = ['hotel', 'system_user', 'location', 'buggy', 'buggy_request']
        table_names = [table[0] for table in tables]
        
        for table in critical_tables:
            if table in table_names:
                print_success(f"  - {table}: ✓")
            else:
                print_error(f"  - {table}: ✗ (missing)")
        
        connection.close()
        return True
        
    except Exception as e:
        print_error(f"Database connection failed: {e}")
        return False

def check_health_endpoint(base_url):
    """Check health endpoint"""
    print_header("Checking Health Endpoint")
    
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        
        if response.status_code == 200:
            print_success(f"Health check: {response.status_code}")
            data = response.json()
            print_success(f"Status: {data.get('status')}")
            print_success(f"Timestamp: {data.get('timestamp')}")
            return True
        else:
            print_error(f"Health check failed: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Health check failed: {e}")
        return False

def check_ready_endpoint(base_url):
    """Check readiness endpoint"""
    print_header("Checking Readiness Endpoint")
    
    try:
        response = requests.get(f"{base_url}/health/ready", timeout=10)
        
        if response.status_code == 200:
            print_success(f"Readiness check: {response.status_code}")
            data = response.json()
            
            if 'checks' in data:
                db_check = data['checks'].get('database', {})
                print_success(f"Database status: {db_check.get('status')}")
                print_success(f"Table count: {db_check.get('table_count')}")
                print_success(f"Critical tables OK: {db_check.get('critical_tables_ok')}")
            
            return True
        else:
            print_warning(f"Readiness check: {response.status_code}")
            print_warning("Application may still be initializing")
            return False
            
    except Exception as e:
        print_warning(f"Readiness check failed: {e}")
        return False

def main():
    """Main verification function"""
    print_header("🚀 Railway Deployment Verification")
    
    # Get base URL
    base_url = os.getenv('BASE_URL')
    if not base_url:
        base_url = input("Enter your Railway app URL (e.g., https://your-app.railway.app): ").strip()
    
    if not base_url:
        print_error("BASE_URL is required")
        sys.exit(1)
    
    # Remove trailing slash
    base_url = base_url.rstrip('/')
    
    print(f"\nVerifying deployment at: {base_url}\n")
    
    # Run checks
    checks = {
        'Environment Variables': check_environment_variables(),
        'Database Connection': check_database_connection(),
        'Health Endpoint': check_health_endpoint(base_url),
        'Readiness Endpoint': check_ready_endpoint(base_url)
    }
    
    # Summary
    print_header("Verification Summary")
    
    for check_name, result in checks.items():
        if result:
            print_success(f"{check_name}: PASSED")
        else:
            print_error(f"{check_name}: FAILED")
    
    all_passed = all(checks.values())
    
    if all_passed:
        print_header("✅ All Checks Passed!")
        print("\nYour Railway deployment is successful!")
        print(f"\nNext steps:")
        print(f"1. Visit {base_url} to access the application")
        print(f"2. Log in with admin credentials")
        print(f"3. Generate QR codes for locations")
        print(f"4. Test buggy request flow")
        sys.exit(0)
    else:
        print_header("❌ Some Checks Failed")
        print("\nPlease review the errors above and:")
        print("1. Check Railway logs for detailed errors")
        print("2. Verify environment variables are set correctly")
        print("3. Ensure MySQL service is running")
        print("4. Check application logs for startup issues")
        sys.exit(1)

if __name__ == "__main__":
    main()
