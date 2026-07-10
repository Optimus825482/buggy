"""
Environment Check — Railway & Coolify compatible
Checks required DB/secret env vars for both naming conventions
"""
import os
import sys

def check_env():
    """Check required environment variables"""
    platform = "Railway" if os.getenv('RAILWAY_STATIC_URL') else "Coolify" if os.getenv('COOLIFY_RESOURCE_UUID') else "Generic"
    print("=" * 60)
    print(f"🔍 {platform} Environment Check")
    print("=" * 60)
    
    # DB vars: try Coolify names first, fall back to Railway names
    db_host = os.getenv('DB_HOST') or os.getenv('MYSQLHOST')
    db_port = os.getenv('DB_PORT') or os.getenv('MYSQLPORT')
    db_name = os.getenv('DB_NAME') or os.getenv('MYSQLDATABASE')
    db_user = os.getenv('DB_USER') or os.getenv('MYSQLUSER')
    db_pass = os.getenv('DB_PASSWORD') or os.getenv('MYSQLPASSWORD')
    mysql_url = os.getenv('MYSQL_PUBLIC_URL')
    
    required_vars = {
        'SECRET_KEY': os.getenv('SECRET_KEY'),
        'JWT_SECRET_KEY': os.getenv('JWT_SECRET_KEY'),
    }
    
    # DB connection — accept EITHER mysql_url OR individual vars
    db_ok = bool(mysql_url) or (bool(db_host) and bool(db_port) and bool(db_name) and bool(db_user) and db_pass is not None)
    
    missing = []
    present = []
    
    print("\n📋 Database Connection:")
    if mysql_url:
        host_part = mysql_url.split('@')[1].split('/')[0] if '@' in mysql_url else mysql_url[:20]
        print(f"  ✅ MYSQL_PUBLIC_URL: {host_part}")
    elif db_ok:
        print(f"  ✅ DB_HOST: {db_host}")
        print(f"  ✅ DB_PORT: {db_port}")
        print(f"  ✅ DB_NAME: {db_name}")
        print(f"  ✅ DB_USER: {db_user}")
        print(f"  ✅ DB_PASSWORD: {'*' * 8}")
    else:
        print(f"  ❌ DB_HOST / MYSQLHOST: {'OK' if db_host else 'MISSING'}")
        print(f"  ❌ DB_PORT / MYSQLPORT: {'OK' if db_port else 'MISSING'}")
        print(f"  ❌ DB_NAME / MYSQLDATABASE: {'OK' if db_name else 'MISSING'}")
        print(f"  ❌ DB_USER / MYSQLUSER: {'OK' if db_user else 'MISSING'}")
        print(f"  ❌ DB_PASSWORD / MYSQLPASSWORD: {'OK' if db_pass is not None else 'MISSING'}")
        print(f"  💡 Set EITHER MYSQL_PUBLIC_URL (Railway) OR DB_HOST/DB_PORT/DB_NAME/DB_USER/DB_PASSWORD (Coolify)")
        missing.append('DATABASE')
    
    print("\n📋 Required Variables:")
    for var, value in required_vars.items():
        if value:
            print(f"  ✅ {var}: {'*' * 8}")
            present.append(var)
        else:
            print(f"  ❌ {var}: MISSING")
            missing.append(var)
    
    print(f"\n📋 Optional: PORT={os.getenv('PORT', '5000')}, FLASK_ENV={os.getenv('FLASK_ENV', 'production')}")
    
    print("\n" + "=" * 60)
    if missing:
        print(f"❌ Missing {len(missing)} required variable(s):")
        for var in missing:
            print(f"   - {var}")
        print("\n💡 Set these in Coolify → Environment Variables:")
        print("   DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD")
        print("   SECRET_KEY, JWT_SECRET_KEY")
        print("=" * 60)
        return False
    else:
        print(f"✅ All required variables are set")
        print("=" * 60)
        return True

if __name__ == '__main__':
    success = check_env()
    sys.exit(0 if success else 1)
