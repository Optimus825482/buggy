"""
Authentication Endpoints Test
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_login():
    """Login endpoint test"""
    print("\n🔐 Testing LOGIN endpoint...")
    
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={
            "username": "admin1",
            "password": "admin123"
        }
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        data = response.json()
        return data["access_token"], data["refresh_token"]
    
    return None, None


def test_me(access_token):
    """Current user endpoint test"""
    print("\n👤 Testing ME endpoint...")
    
    response = requests.get(
        f"{BASE_URL}/auth/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")


def test_refresh(refresh_token):
    """Token refresh endpoint test"""
    print("\n🔄 Testing REFRESH endpoint...")
    
    response = requests.post(
        f"{BASE_URL}/auth/refresh",
        json={"refresh_token": refresh_token}
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")


def test_logout(access_token):
    """Logout endpoint test"""
    print("\n🚪 Testing LOGOUT endpoint...")
    
    response = requests.post(
        f"{BASE_URL}/auth/logout",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 Authentication Endpoints Test")
    print("=" * 60)
    
    try:
        # Login test
        access_token, refresh_token = test_login()
        
        if access_token:
            # Me endpoint test
            test_me(access_token)
            
            # Refresh token test
            test_refresh(refresh_token)
            
            # Logout test
            test_logout(access_token)
        
        print("\n" + "=" * 60)
        print("✅ Test tamamlandı!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Test hatası: {e}")
