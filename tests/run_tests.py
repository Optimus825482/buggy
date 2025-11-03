#!/usr/bin/env python3
"""
Test runner script for Buggy Call system

Usage:
    python tests/run_tests.py                    # Run all tests
    python tests/run_tests.py --driver          # Run only driver tests
    python tests/run_tests.py --guest           # Run only guest tests
    python tests/run_tests.py --session         # Run only session tests
    python tests/run_tests.py --integration     # Run only integration tests
    python tests/run_tests.py --verbose         # Run with verbose output
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def run_tests(test_type=None, verbose=False):
    """Run tests with pytest"""
    
    # Base pytest command
    cmd = ['python', '-m', 'pytest']
    
    # Add test file based on type
    if test_type == 'driver':
        cmd.append('tests/test_driver_workflow.py')
    elif test_type == 'guest':
        cmd.append('tests/test_guest_workflow.py')
    elif test_type == 'session':
        cmd.append('tests/test_session_management.py')
    elif test_type == 'integration':
        cmd.append('tests/test_integration.py')
    else:
        cmd.append('tests/')  # Run all tests
    
    # Add verbose flag
    if verbose:
        cmd.append('-v')
    
    # Add other useful flags
    cmd.extend([
        '--tb=short',  # Shorter traceback format
        '--strict-markers',  # Strict marker checking
        '--disable-warnings'  # Disable warnings for cleaner output
    ])
    
    print(f"Running command: {' '.join(cmd)}")
    print("=" * 60)
    
    # Run tests
    try:
        result = subprocess.run(cmd, cwd=project_root)
        return result.returncode
    except KeyboardInterrupt:
        print("\nTests interrupted by user")
        return 1
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1


def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import pytest
        import flask
        import sqlalchemy
        print("✓ All required dependencies found")
        return True
    except ImportError as e:
        print(f"✗ Missing dependency: {e}")
        print("Please install dependencies with: pip install -r requirements.txt")
        return False


def setup_test_environment():
    """Setup test environment"""
    # Set environment variables for testing
    os.environ['FLASK_ENV'] = 'testing'
    os.environ['TESTING'] = 'true'
    
    # Ensure test database directory exists
    test_db_dir = project_root / 'tests' / 'data'
    test_db_dir.mkdir(exist_ok=True)
    
    print("✓ Test environment configured")


def print_test_summary():
    """Print test summary and instructions"""
    print("\n" + "=" * 60)
    print("BUGGY CALL SYSTEM - TEST SUITE")
    print("=" * 60)
    print("\nTest Categories:")
    print("  • Driver Workflow Tests - Login, location, accept/complete requests")
    print("  • Guest Workflow Tests - QR codes, requests, status tracking")
    print("  • Session Management Tests - Admin session control, single device")
    print("  • Integration Tests - Complete end-to-end workflows")
    print("\nTest Coverage:")
    print("  • API Endpoints - All new driver and admin endpoints")
    print("  • Business Logic - Request acceptance, completion, race conditions")
    print("  • Security - Session management, authorization")
    print("  • User Experience - QR workflow, real-time updates")
    print("\n" + "=" * 60)


def main():
    parser = argparse.ArgumentParser(description='Run Buggy Call system tests')
    parser.add_argument('--driver', action='store_true', help='Run driver workflow tests')
    parser.add_argument('--guest', action='store_true', help='Run guest workflow tests')
    parser.add_argument('--session', action='store_true', help='Run session management tests')
    parser.add_argument('--integration', action='store_true', help='Run integration tests')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--summary', action='store_true', help='Show test summary only')
    
    args = parser.parse_args()
    
    if args.summary:
        print_test_summary()
        return 0
    
    # Print summary first
    print_test_summary()
    
    # Check dependencies
    if not check_dependencies():\
        return 1
    
    # Setup test environment
    setup_test_environment()
    
    # Determine test type
    test_type = None
    if args.driver:
        test_type = 'driver'
    elif args.guest:
        test_type = 'guest'
    elif args.session:
        test_type = 'session'
    elif args.integration:
        test_type = 'integration'
    
    # Run tests
    return run_tests(test_type, args.verbose)


if __name__ == '__main__':
    sys.exit(main())
