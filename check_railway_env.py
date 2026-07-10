"""
Environment Check — warns only, never blocks startup
Coolify auto-sets DB_HOST/DB_PORT/DB_NAME/DB_USER/DB_PASSWORD via MySQL service.
SECRET_KEY and JWT_SECRET_KEY have defaults in config.py.
"""
import os
import sys

def check_env():
    """Check environment variables — warnings only, never fails"""
    platform = "Coolify" if os.getenv('COOLIFY_RESOURCE_UUID') else "Railway" if os.getenv('RAILWAY_STATIC_URL') else "Generic"
    print("=" * 60)
    print(f"🔍 {platform} Environment Check")
    print("=" * 60)
    
    db_host = os.getenv('DB_HOST') or os.getenv('MYSQLHOST') or 'localhost'
    db_port = os.getenv('DB_PORT') or os.getenv('MYSQLPORT') or '3306'
    db_name = os.getenv('DB_NAME') or os.getenv('MYSQLDATABASE') or 'buggycall'
    db_user = os.getenv('DB_USER') or os.getenv('MYSQLUSER') or 'root'
    db_pass = os.getenv('DB_PASSWORD') or os.getenv('MYSQLPASSWORD') or ''
    mysql_url = os.getenv('MYSQL_PUBLIC_URL')
    
    print(f"\n📋 Database:")
    if mysql_url:
        print(f"  ✅ MYSQL_PUBLIC_URL: {'*' * 8}")
    else:
        print(f"  ✅ DB_HOST={db_host}, DB_PORT={db_port}, DB_NAME={db_name}, DB_USER={db_user}")
    
    secret = os.getenv('SECRET_KEY')
    jwt = os.getenv('JWT_SECRET_KEY')
    print(f"  {'✅' if secret else '⚠️'} SECRET_KEY: {'*' * 8 if secret else 'default kullanilacak'}")
    print(f"  {'✅' if jwt else '⚠️'} JWT_SECRET_KEY: {'*' * 8 if jwt else 'default kullanilacak'}")
    print(f"\n📋 PORT={os.getenv('PORT', '5000')}, FLASK_ENV={os.getenv('FLASK_ENV', 'production')}")
    
    print("\n" + "=" * 60)
    print("✅ Environment check passed")
    print("=" * 60)
    return True

if __name__ == '__main__':
    sys.exit(0 if check_env() else 1)
