"""
Test script for Map API endpoint
"""
import requests
import sys

BASE_URL = "http://localhost:5000"

def test_map_thumbnail_with_coordinates():
    """Test map thumbnail generation with valid coordinates"""
    print("\n1. Testing map thumbnail with valid coordinates...")
    
    # Istanbul coordinates
    lat = 41.0082
    lng = 28.9784
    
    url = f"{BASE_URL}/api/map/thumbnail?lat={lat}&lng={lng}"
    
    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            print(f"✅ Success! Image size: {len(response.content)} bytes")
            print(f"   Content-Type: {response.headers.get('Content-Type')}")
            
            # Save image for inspection
            with open('test_map_thumbnail.png', 'wb') as f:
                f.write(response.content)
            print("   Saved as: test_map_thumbnail.png")
            
            return True
        else:
            print(f"❌ Failed with status code: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_map_thumbnail_without_coordinates():
    """Test map thumbnail generation without coordinates (fallback)"""
    print("\n2. Testing map thumbnail without coordinates (fallback)...")
    
    url = f"{BASE_URL}/api/map/thumbnail"
    
    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            print(f"✅ Success! Fallback image size: {len(response.content)} bytes")
            print(f"   Content-Type: {response.headers.get('Content-Type')}")
            
            # Save image for inspection
            with open('test_map_fallback.png', 'wb') as f:
                f.write(response.content)
            print("   Saved as: test_map_fallback.png")
            
            return True
        else:
            print(f"❌ Failed with status code: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_map_thumbnail_with_custom_size():
    """Test map thumbnail with custom dimensions"""
    print("\n3. Testing map thumbnail with custom size...")
    
    lat = 41.0082
    lng = 28.9784
    width = 600
    height = 400
    
    url = f"{BASE_URL}/api/map/thumbnail?lat={lat}&lng={lng}&width={width}&height={height}"
    
    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            print(f"✅ Success! Custom size image: {len(response.content)} bytes")
            
            # Save image for inspection
            with open('test_map_custom.png', 'wb') as f:
                f.write(response.content)
            print("   Saved as: test_map_custom.png")
            
            return True
        else:
            print(f"❌ Failed with status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_map_thumbnail_invalid_coordinates():
    """Test map thumbnail with invalid coordinates"""
    print("\n4. Testing map thumbnail with invalid coordinates...")
    
    lat = 999  # Invalid
    lng = 999  # Invalid
    
    url = f"{BASE_URL}/api/map/thumbnail?lat={lat}&lng={lng}"
    
    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            print(f"✅ Success! Fallback for invalid coords: {len(response.content)} bytes")
            
            # Save image for inspection
            with open('test_map_invalid.png', 'wb') as f:
                f.write(response.content)
            print("   Saved as: test_map_invalid.png")
            
            return True
        else:
            print(f"❌ Failed with status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_cache_functionality():
    """Test caching by making the same request twice"""
    print("\n5. Testing cache functionality...")
    
    lat = 41.0082
    lng = 28.9784
    url = f"{BASE_URL}/api/map/thumbnail?lat={lat}&lng={lng}"
    
    try:
        # First request
        import time
        start = time.time()
        response1 = requests.get(url, timeout=10)
        time1 = time.time() - start
        
        # Second request (should be cached)
        start = time.time()
        response2 = requests.get(url, timeout=10)
        time2 = time.time() - start
        
        if response1.status_code == 200 and response2.status_code == 200:
            print(f"✅ Success!")
            print(f"   First request: {time1:.3f}s")
            print(f"   Second request: {time2:.3f}s (cached)")
            
            if time2 < time1:
                print(f"   ✅ Cache is working! {((time1-time2)/time1*100):.1f}% faster")
            
            return True
        else:
            print(f"❌ Failed")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == '__main__':
    print("="*60)
    print("Map API Test Suite")
    print("="*60)
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print("❌ Server is not running or not healthy!")
            print("   Please start the server with: python run.py")
            sys.exit(1)
    except:
        print("❌ Cannot connect to server!")
        print("   Please start the server with: python run.py")
        sys.exit(1)
    
    print("✅ Server is running\n")
    
    # Run tests
    results = []
    results.append(test_map_thumbnail_with_coordinates())
    results.append(test_map_thumbnail_without_coordinates())
    results.append(test_map_thumbnail_with_custom_size())
    results.append(test_map_thumbnail_invalid_coordinates())
    results.append(test_cache_functionality())
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("✅ All tests passed!")
        sys.exit(0)
    else:
        print(f"❌ {total - passed} test(s) failed")
        sys.exit(1)
