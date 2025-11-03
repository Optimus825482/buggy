"""
Buggy Call - Deployment Verification Script
Performs comprehensive post-deployment checks
"""
import sys
import os
import requests
import json
from urllib.parse import urlparse
import argparse


class DeploymentVerifier:
    """Verify Railway deployment"""
    
    def __init__(self, base_url, admin_username='admin', admin_password='Admin123!Railway'):
        self.base_url = base_url.rstrip('/')
        self.admin_username = admin_username
        self.admin_password = admin_password
        self.session = requests.Session()
        self.results = {
            'passed': [],
            'failed': [],
            'warnings': []
        }
    
    def log_pass(self, test_name, message=''):
        """Log passed test"""
        self.results['passed'].append(test_name)
        print(f"✅ {test_name}")
        if message:
            print(f"   {message}")
    
    def log_fail(self, test_name, error):
        """Log failed test"""
        self.results['failed'].append(test_name)
        print(f"❌ {test_name}")
        print(f"   Error: {error}")
    
    def log_warning(self, test_name, message):
        """Log warning"""
        self.results['warnings'].append(test_name)
        print(f"⚠️  {test_name}")
        print(f"   {message}")
    
    def check_health_endpoint(self):
        """Check /health endpoint"""
        print("\n" + "="*60)
        print("1. Health Check Endpoint")
        print("="*60)
        
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('status') == 'healthy':
                    self.log_pass("Health endpoint", f"Status: {data.get('status')}")
                    
                    # Check database
                    db_check = data.get('checks', {}).get('database', {})
                    if db_check.get('status') == 'healthy':
                        self.log_pass("Database connection", 
                                    f"Tables: {db_check.get('table_count', 0)}")
                    else:
                        self.log_fail("Database connection", 
                                    db_check.get('message', 'Unknown error'))
                    
                    # Check application
                    app_check = data.get('checks', {}).get('application', {})
                    if app_check.get('status') == 'healthy':
                        self.log_pass("Application status")
                    else:
                        self.log_fail("Application status", 
                                    app_check.get('message', 'Unknown error'))
                else:
                    self.log_fail("Health endpoint", f"Status: {data.get('status')}")
            else:
                self.log_fail("Health endpoint", 
                            f"HTTP {response.status_code}: {response.text[:100]}")
                
        except requests.exceptions.RequestException as e:
            self.log_fail("Health endpoint", str(e))
    
    def check_database_tables(self):
        """Verify database tables exist"""
        print("\n" + "="*60)
        print("2. Database Tables")
        print("="*60)
        
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                db_check = data.get('checks', {}).get('database', {})
                
                table_count = db_check.get('table_count', 0)
                critical_ok = db_check.get('critical_tables_ok', False)
                
                if table_count > 0:
                    self.log_pass("Database tables", f"Found {table_count} tables")
                else:
                    self.log_fail("Database tables", "No tables found")
                
                if critical_ok:
                    self.log_pass("Critical tables", "All critical tables exist")
                else:
                    missing = db_check.get('missing_tables', [])
                    self.log_fail("Critical tables", f"Missing: {', '.join(missing)}")
            else:
                self.log_fail("Database tables", "Could not verify")
                
        except Exception as e:
            self.log_fail("Database tables", str(e))
    
    def check_admin_authentication(self):
        """Test admin authentication"""
        print("\n" + "="*60)
        print("3. Admin Authentication")
        print("="*60)
        
        try:
            # Try to login
            response = self.session.post(
                f"{self.base_url}/auth/login",
                json={
                    'username': self.admin_username,
                    'password': self.admin_password
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'access_token' in data or 'token' in data:
                    self.log_pass("Admin login", f"Username: {self.admin_username}")
                else:
                    self.log_fail("Admin login", "No token in response")
            elif response.status_code == 401:
                self.log_warning("Admin login", 
                               "Invalid credentials - password may have been changed")
            else:
                self.log_fail("Admin login", 
                            f"HTTP {response.status_code}: {response.text[:100]}")
                
        except requests.exceptions.RequestException as e:
            self.log_fail("Admin login", str(e))
    
    def check_static_files(self):
        """Check if static files are accessible"""
        print("\n" + "="*60)
        print("4. Static Files")
        print("="*60)
        
        # Check common static files
        static_files = [
            '/static/css/style.css',
            '/static/js/main.js',
        ]
        
        for file_path in static_files:
            try:
                response = self.session.get(f"{self.base_url}{file_path}", timeout=10)
                
                if response.status_code == 200:
                    self.log_pass(f"Static file: {file_path}")
                elif response.status_code == 404:
                    self.log_warning(f"Static file: {file_path}", "Not found (may not exist)")
                else:
                    self.log_fail(f"Static file: {file_path}", 
                                f"HTTP {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                self.log_fail(f"Static file: {file_path}", str(e))
    
    def check_websocket_support(self):
        """Check if WebSocket endpoint is accessible"""
        print("\n" + "="*60)
        print("5. WebSocket Support")
        print("="*60)
        
        try:
            # Check if socket.io endpoint responds
            response = self.session.get(
                f"{self.base_url}/socket.io/?EIO=4&transport=polling",
                timeout=10
            )
            
            if response.status_code == 200:
                self.log_pass("WebSocket endpoint", "Socket.IO accessible")
            else:
                self.log_warning("WebSocket endpoint", 
                               f"HTTP {response.status_code} - May need configuration")
                
        except requests.exceptions.RequestException as e:
            self.log_warning("WebSocket endpoint", str(e))
    
    def check_security_headers(self):
        """Check security headers"""
        print("\n" + "="*60)
        print("6. Security Headers")
        print("="*60)
        
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=10)
            headers = response.headers
            
            security_headers = {
                'X-Content-Type-Options': 'nosniff',
                'X-Frame-Options': 'SAMEORIGIN',
                'X-XSS-Protection': '1',
            }
            
            for header, expected in security_headers.items():
                if header in headers:
                    if expected in headers[header]:
                        self.log_pass(f"Security header: {header}")
                    else:
                        self.log_warning(f"Security header: {header}", 
                                       f"Value: {headers[header]}")
                else:
                    self.log_warning(f"Security header: {header}", "Not set")
            
            # Check HTTPS
            if self.base_url.startswith('https://'):
                self.log_pass("HTTPS", "Secure connection")
            else:
                self.log_warning("HTTPS", "Not using HTTPS")
                
        except Exception as e:
            self.log_fail("Security headers", str(e))
    
    def print_summary(self):
        """Print verification summary"""
        print("\n" + "="*60)
        print("VERIFICATION SUMMARY")
        print("="*60)
        
        total = len(self.results['passed']) + len(self.results['failed']) + len(self.results['warnings'])
        passed = len(self.results['passed'])
        failed = len(self.results['failed'])
        warnings = len(self.results['warnings'])
        
        print(f"\nTotal checks: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"⚠️  Warnings: {warnings}")
        
        if failed == 0:
            print("\n🎉 Deployment verification PASSED!")
            print("Your application is ready for use.")
        else:
            print("\n⚠️  Deployment verification FAILED!")
            print("Please fix the failed checks before using the application.")
        
        print("="*60)
        
        return failed == 0
    
    def run_all_checks(self):
        """Run all verification checks"""
        print("\n🚀 Buggy Call Deployment Verification")
        print(f"Target: {self.base_url}")
        print("="*60)
        
        self.check_health_endpoint()
        self.check_database_tables()
        self.check_admin_authentication()
        self.check_static_files()
        self.check_websocket_support()
        self.check_security_headers()
        
        return self.print_summary()


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Verify Buggy Call Railway Deployment')
    parser.add_argument('url', help='Base URL of the deployed application')
    parser.add_argument('--admin-username', default='admin',
                       help='Admin username (default: admin)')
    parser.add_argument('--admin-password', default='Admin123!Railway',
                       help='Admin password')
    parser.add_argument('--json', action='store_true',
                       help='Output results as JSON')
    
    args = parser.parse_args()
    
    # Validate URL
    try:
        parsed = urlparse(args.url)
        if not parsed.scheme or not parsed.netloc:
            print("❌ Invalid URL format")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Invalid URL: {e}")
        sys.exit(1)
    
    # Run verification
    verifier = DeploymentVerifier(
        args.url,
        args.admin_username,
        args.admin_password
    )
    
    success = verifier.run_all_checks()
    
    # Output JSON if requested
    if args.json:
        print("\nJSON Results:")
        print(json.dumps(verifier.results, indent=2))
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
