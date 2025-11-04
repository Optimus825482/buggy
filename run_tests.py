"""
Test Runner for ShuttleCall Application
Runs all test suites and generates report
"""
import sys
import pytest
from datetime import datetime


def main():
    """Run all tests with detailed reporting"""
    
    print("=" * 80)
    print("ShuttleCall Application - Comprehensive Test Suite")
    print("=" * 80)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print()
    
    # Test configuration
    test_args = [
        'tests/',
        '-v',                          # Verbose output
        '--tb=short',                  # Short traceback format
        '--color=yes',                 # Colored output
        '-W', 'ignore::DeprecationWarning',  # Ignore deprecation warnings
        '--maxfail=5',                 # Stop after 5 failures
        '-p', 'no:warnings',           # Disable warnings plugin for cleaner output
    ]
    
    # Add coverage if requested
    if '--coverage' in sys.argv:
        test_args.extend([
            '--cov=app',
            '--cov-report=html',
            '--cov-report=term-missing',
        ])
        print("✓ Coverage reporting enabled")
        print()
    
    # Run specific test file if provided
    if len(sys.argv) > 1 and sys.argv[1].startswith('test_'):
        test_args[0] = f'tests/{sys.argv[1]}'
        print(f"Running specific test: {sys.argv[1]}")
        print()
    
    # Run tests
    exit_code = pytest.main(test_args)
    
    print()
    print("=" * 80)
    print(f"Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    if exit_code == 0:
        print("✅ All tests passed!")
    else:
        print(f"❌ Tests failed with exit code: {exit_code}")
    
    return exit_code


if __name__ == '__main__':
    sys.exit(main())
