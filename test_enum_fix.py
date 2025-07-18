#!/usr/bin/env python3
"""
Test script to verify enum serialization fix
"""

import asyncio
import httpx
import json
import os

# Get backend URL from environment
BACKEND_URL = os.getenv("REACT_APP_BACKEND_URL", "https://0aa3f469-239e-4a70-bf25-a2009805653e.preview.emergentagent.com")
API_BASE = f"{BACKEND_URL}/api"

async def test_enhanced_login():
    """Test the enhanced login endpoint specifically"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        # First login normally to get a user
        login_data = {
            "email": "ahmed.hassan@example.com",
            "password": "SecurePass123!"
        }
        
        print("Testing enhanced login endpoint...")
        
        try:
            response = await client.post(f"{API_BASE}/auth/login-enhanced", json=login_data)
            
            print(f"Status Code: {response.status_code}")
            print(f"Response Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Enhanced login successful!")
                print(f"Risk Level: {data.get('risk_assessment', {}).get('risk_level', 'N/A')}")
                print(f"Risk Score: {data.get('risk_assessment', {}).get('risk_score', 'N/A')}")
                return True
            else:
                print(f"❌ Enhanced login failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Enhanced login error: {str(e)}")
            return False

async def test_security_apis():
    """Test all security APIs for enum serialization issues"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        # First login to get token
        login_data = {
            "email": "ahmed.hassan@example.com",
            "password": "SecurePass123!"
        }
        
        login_response = await client.post(f"{API_BASE}/auth/login", json=login_data)
        if login_response.status_code != 200:
            print("❌ Failed to login for security API tests")
            return False
        
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test security APIs
        security_endpoints = [
            ("GET", "/security/status"),
            ("GET", "/aml/dashboard"),
            ("GET", "/aml/alerts"),
            ("GET", "/risk/dashboard"),
            ("GET", f"/risk/assessment/{login_response.json()['user']['id']}"),
            ("GET", f"/biometric/user/{login_response.json()['user']['id']}"),
            ("GET", "/biometric/history")
        ]
        
        results = []
        
        for method, endpoint in security_endpoints:
            try:
                if method == "GET":
                    response = await client.get(f"{API_BASE}{endpoint}", headers=headers)
                else:
                    response = await client.post(f"{API_BASE}{endpoint}", headers=headers)
                
                if response.status_code == 200:
                    # Try to parse JSON to check for serialization issues
                    data = response.json()
                    print(f"✅ {endpoint}: OK")
                    results.append(True)
                else:
                    print(f"❌ {endpoint}: {response.status_code} - {response.text[:100]}")
                    results.append(False)
                    
            except Exception as e:
                print(f"❌ {endpoint}: Error - {str(e)}")
                results.append(False)
        
        return all(results)

async def main():
    print("🔍 Testing Security System APIs for Enum Serialization Issues")
    print("=" * 60)
    
    # Test enhanced login specifically
    enhanced_login_result = await test_enhanced_login()
    
    print("\n" + "=" * 60)
    
    # Test all security APIs
    security_apis_result = await test_security_apis()
    
    print("\n" + "=" * 60)
    print("📊 SUMMARY:")
    print(f"Enhanced Login: {'✅ PASS' if enhanced_login_result else '❌ FAIL'}")
    print(f"Security APIs: {'✅ PASS' if security_apis_result else '❌ FAIL'}")
    
    if enhanced_login_result and security_apis_result:
        print("🎉 All enum serialization issues resolved!")
        return True
    else:
        print("⚠️ Some enum serialization issues remain")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)