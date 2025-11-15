"""
Railway Environment Check
Gerekli environment variable'ları kontrol eder
"""
import os
import sys

def check_env():
    """Check required environment variables"""
    print("=" * 60)
    print("🔍 Railway Environment Check")
    print("=" * 60)
    
    required_vars = {
        'MYSQL_PUBLIC_URL': 'MySQL connection URL',
        'MYSQLHOST': 'MySQL host',
        'MYSQLPORT': 'MySQL port',
        'MYSQLUSER': 'MySQL user',
        'MYSQLPASSWORD': 'MySQL password',
        'MYSQLDATABASE': 'MySQL database name',
        'SECRET_KEY': 'Flask secret key',
        'JWT_SECRET_KEY': 'JWT secret key'
    }
    
    optional_vars = {
        'PORT': 'Application port (default: 5000)',
        'FLASK_ENV': 'Flask environment (default: production)'
    }
    
    missing = []
    present = []
    
    print("\n📋 Required Variables:")
    for var, desc in required_vars.items():
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            if 'PASSWORD' in var or 'SECRET' in var or 'KEY' in var:
                display_value = '*' * 8
            elif 'URL' in var:
                # Show only host part
                display_value = value.split('@')[1].split('/')[0] if '@' in value else value[:20] + '...'
            else:
                display_value = value[:30] + '...' if len(value) > 30 else value
            
            print(f"  ✅ {var}: {display_value}")
            present.append(var)
        else:
            print(f"  ❌ {var}: MISSING - {desc}")
            missing.append(var)
    
    print("\n📋 Optional Variables:")
    for var, desc in optional_vars.items():
        value = os.getenv(var)
        if value:
            if 'KEY' in var:
                display_value = '*' * 8
            else:
                display_value = value[:30] + '...' if len(value) > 30 else value
            print(f"  ✅ {var}: {display_value}")
        else:
            print(f"  ⚠️  {var}: Not set - {desc}")
    
    print("\n" + "=" * 60)
    if missing:
        print(f"❌ Missing {len(missing)} required variable(s):")
        for var in missing:
            print(f"   - {var}")
        print("\n💡 Set these in Railway project settings:")
        print("   railway.app → Project → Variables")
        print("=" * 60)
        return False
    else:
        print(f"✅ All {len(present)} required variables are set")
        print("=" * 60)
        return True

if __name__ == '__main__':
    success = check_env()
    sys.exit(0 if success else 1)
