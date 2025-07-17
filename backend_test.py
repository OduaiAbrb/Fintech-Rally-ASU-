#!/usr/bin/env python3
"""
Backend API Testing Suite for Stablecoin Fintech Platform
Tests Phase 4 Security & Risk Management System:
- AML (Anti-Money Laundering) System
- Biometric Authentication System  
- Risk Scoring System
- Security System Management
"""

import asyncio
import httpx
import json
import os
import base64
from datetime import datetime
from typing import Dict, Any, Optional

# Get backend URL from environment
BACKEND_URL = os.getenv("REACT_APP_BACKEND_URL", "https://fb2b8618-5ed0-42da-9035-50aa156b0e1e.preview.emergentagent.com")
API_BASE = f"{BACKEND_URL}/api"

class BackendTester:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.access_token = None
        self.user_data = None
        
    async def cleanup(self):
        """Clean up HTTP client"""
        await self.client.aclose()
    
    def print_test_header(self, test_name: str):
        """Print formatted test header"""
        print(f"\n{'='*60}")
        print(f"🧪 TESTING: {test_name}")
        print(f"{'='*60}")
    
    def print_result(self, success: bool, message: str, details: Any = None):
        """Print test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {message}")
        if details and not success:
            print(f"   Details: {details}")
    
    async def register_test_user(self) -> bool:
        """Register a test user for authentication"""
        try:
            user_data = {
                "email": "ahmed.hassan@example.com",
                "password": "SecurePass123!",
                "full_name": "Ahmed Hassan",
                "phone_number": "+962791234567"
            }
            
            response = await self.client.post(f"{API_BASE}/auth/register", json=user_data)
            
            if response.status_code in [200, 201]:
                data = response.json()
                self.access_token = data["access_token"]
                self.user_data = data["user"]
                self.print_result(True, f"User registered successfully: {self.user_data['full_name']}")
                return True
            elif response.status_code == 400 and "already registered" in response.text:
                # User exists, try to login
                return await self.login_test_user()
            else:
                self.print_result(False, f"Registration failed: {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.print_result(False, f"Registration error: {str(e)}")
            return False
    
    async def login_test_user(self) -> bool:
        """Login test user"""
        try:
            login_data = {
                "email": "ahmed.hassan@example.com",
                "password": "SecurePass123!"
            }
            
            response = await self.client.post(f"{API_BASE}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data["access_token"]
                self.user_data = data["user"]
                self.print_result(True, f"User logged in successfully: {self.user_data['full_name']}")
                return True
            else:
                self.print_result(False, f"Login failed: {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.print_result(False, f"Login error: {str(e)}")
            return False
    
    def get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers"""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
    
    async def test_connect_accounts_endpoint(self) -> bool:
        """Test POST /api/open-banking/connect-accounts endpoint"""
        self.print_test_header("POST /api/open-banking/connect-accounts")
        
        try:
            response = await self.client.post(
                f"{API_BASE}/open-banking/connect-accounts",
                headers=self.get_auth_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Validate response structure
                required_fields = ["has_linked_accounts", "total_balance", "accounts", "recent_transactions"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.print_result(False, f"Missing required fields: {missing_fields}")
                    return False
                
                # Validate accounts structure
                if not isinstance(data["accounts"], list):
                    self.print_result(False, "Accounts should be a list")
                    return False
                
                if len(data["accounts"]) == 0:
                    self.print_result(False, "No accounts returned")
                    return False
                
                # Validate account structure
                account = data["accounts"][0]
                account_fields = ["account_id", "account_name", "bank_name", "balance", "currency"]
                missing_account_fields = [field for field in account_fields if field not in account]
                
                if missing_account_fields:
                    self.print_result(False, f"Missing account fields: {missing_account_fields}")
                    return False
                
                # Validate data types and values
                if not isinstance(data["has_linked_accounts"], bool):
                    self.print_result(False, "has_linked_accounts should be boolean")
                    return False
                
                if not isinstance(data["total_balance"], (int, float)):
                    self.print_result(False, "total_balance should be numeric")
                    return False
                
                if data["total_balance"] <= 0:
                    self.print_result(False, "total_balance should be positive")
                    return False
                
                # Check if balance calculation is correct
                calculated_balance = sum(acc["balance"] for acc in data["accounts"])
                if abs(calculated_balance - data["total_balance"]) > 0.01:
                    self.print_result(False, f"Balance mismatch: calculated {calculated_balance}, returned {data['total_balance']}")
                    return False
                
                self.print_result(True, f"Connect accounts successful - {len(data['accounts'])} accounts, total balance: {data['total_balance']:.2f} JOD")
                
                # Print account details
                print("\n📋 Connected Accounts:")
                for i, account in enumerate(data["accounts"], 1):
                    print(f"   {i}. {account['bank_name']} - {account['account_name']}")
                    print(f"      Balance: {account['balance']:.2f} {account['currency']}")
                    print(f"      Account ID: {account['account_id']}")
                
                return True
            else:
                self.print_result(False, f"Request failed: {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.print_result(False, f"Connect accounts error: {str(e)}")
            return False
    
    async def test_get_accounts_endpoint(self) -> bool:
        """Test GET /api/open-banking/accounts endpoint"""
        self.print_test_header("GET /api/open-banking/accounts")
        
        try:
            response = await self.client.get(
                f"{API_BASE}/open-banking/accounts",
                headers=self.get_auth_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Validate response structure
                if "accounts" not in data:
                    self.print_result(False, "Missing 'accounts' field in response")
                    return False
                
                if "total" not in data:
                    self.print_result(False, "Missing 'total' field in response")
                    return False
                
                accounts = data["accounts"]
                if not isinstance(accounts, list):
                    self.print_result(False, "Accounts should be a list")
                    return False
                
                if len(accounts) == 0:
                    self.print_result(False, "No accounts returned")
                    return False
                
                # Validate account structure
                for i, account in enumerate(accounts):
                    required_fields = [
                        "account_id", "account_name", "account_number", "bank_name", 
                        "bank_code", "account_type", "currency", "balance", 
                        "available_balance", "status", "last_updated"
                    ]
                    
                    missing_fields = [field for field in required_fields if field not in account]
                    if missing_fields:
                        self.print_result(False, f"Account {i+1} missing fields: {missing_fields}")
                        return False
                    
                    # Validate data types
                    if not isinstance(account["balance"], (int, float)):
                        self.print_result(False, f"Account {i+1} balance should be numeric")
                        return False
                    
                    if not isinstance(account["available_balance"], (int, float)):
                        self.print_result(False, f"Account {i+1} available_balance should be numeric")
                        return False
                    
                    if account["currency"] != "JOD":
                        self.print_result(False, f"Account {i+1} currency should be JOD")
                        return False
                
                # Validate total count
                if data["total"] != len(accounts):
                    self.print_result(False, f"Total count mismatch: {data['total']} vs {len(accounts)}")
                    return False
                
                self.print_result(True, f"Get accounts successful - {len(accounts)} accounts returned")
                
                # Print account details
                print("\n📋 Account Details:")
                for i, account in enumerate(accounts, 1):
                    print(f"   {i}. {account['bank_name']} - {account['account_name']}")
                    print(f"      Account Number: {account['account_number']}")
                    print(f"      Type: {account['account_type']}")
                    print(f"      Balance: {account['balance']:.2f} {account['currency']}")
                    print(f"      Available: {account['available_balance']:.2f} {account['currency']}")
                    print(f"      Status: {account['status']}")
                
                return True
            else:
                self.print_result(False, f"Request failed: {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.print_result(False, f"Get accounts error: {str(e)}")
            return False
    
    async def test_get_dashboard_endpoint(self) -> bool:
        """Test GET /api/open-banking/dashboard endpoint"""
        self.print_test_header("GET /api/open-banking/dashboard")
        
        try:
            response = await self.client.get(
                f"{API_BASE}/open-banking/dashboard",
                headers=self.get_auth_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Validate response structure
                required_fields = ["has_linked_accounts", "total_balance", "accounts", "recent_transactions", "total_accounts"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.print_result(False, f"Missing required fields: {missing_fields}")
                    return False
                
                # Validate data types
                if not isinstance(data["has_linked_accounts"], bool):
                    self.print_result(False, "has_linked_accounts should be boolean")
                    return False
                
                if not isinstance(data["total_balance"], (int, float)):
                    self.print_result(False, "total_balance should be numeric")
                    return False
                
                if not isinstance(data["accounts"], list):
                    self.print_result(False, "accounts should be a list")
                    return False
                
                if not isinstance(data["recent_transactions"], list):
                    self.print_result(False, "recent_transactions should be a list")
                    return False
                
                if not isinstance(data["total_accounts"], int):
                    self.print_result(False, "total_accounts should be integer")
                    return False
                
                # Validate consistency
                if data["total_accounts"] != len(data["accounts"]):
                    self.print_result(False, f"Account count mismatch: {data['total_accounts']} vs {len(data['accounts'])}")
                    return False
                
                if data["has_linked_accounts"] and len(data["accounts"]) == 0:
                    self.print_result(False, "has_linked_accounts is true but no accounts present")
                    return False
                
                if not data["has_linked_accounts"] and len(data["accounts"]) > 0:
                    self.print_result(False, "has_linked_accounts is false but accounts present")
                    return False
                
                # Validate account structure in dashboard
                for i, account in enumerate(data["accounts"]):
                    required_fields = ["account_id", "account_name", "bank_name", "balance", "currency"]
                    missing_fields = [field for field in required_fields if field not in account]
                    
                    if missing_fields:
                        self.print_result(False, f"Dashboard account {i+1} missing fields: {missing_fields}")
                        return False
                
                # Check balance calculation
                if data["accounts"]:
                    calculated_balance = sum(acc["balance"] for acc in data["accounts"])
                    if abs(calculated_balance - data["total_balance"]) > 0.01:
                        self.print_result(False, f"Dashboard balance mismatch: calculated {calculated_balance}, returned {data['total_balance']}")
                        return False
                
                self.print_result(True, f"Dashboard successful - {data['total_accounts']} accounts, total: {data['total_balance']:.2f} JOD")
                
                # Print dashboard summary
                print(f"\n📊 Dashboard Summary:")
                print(f"   Has Linked Accounts: {data['has_linked_accounts']}")
                print(f"   Total Balance: {data['total_balance']:.2f} JOD")
                print(f"   Total Accounts: {data['total_accounts']}")
                print(f"   Recent Transactions: {len(data['recent_transactions'])}")
                
                if data["accounts"]:
                    print(f"\n💰 Account Balances:")
                    for account in data["accounts"]:
                        print(f"   • {account['bank_name']}: {account['balance']:.2f} {account['currency']}")
                
                return True
            else:
                self.print_result(False, f"Request failed: {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.print_result(False, f"Dashboard error: {str(e)}")
            return False
    
    async def test_authentication_required(self) -> bool:
        """Test that endpoints require authentication"""
        self.print_test_header("Authentication Requirements")
        
        endpoints = [
            "/open-banking/connect-accounts",
            "/open-banking/accounts", 
            "/open-banking/dashboard"
        ]
        
        all_passed = True
        
        for endpoint in endpoints:
            try:
                if endpoint == "/open-banking/connect-accounts":
                    response = await self.client.post(f"{API_BASE}{endpoint}")
                else:
                    response = await self.client.get(f"{API_BASE}{endpoint}")
                
                if response.status_code in [401, 403]:
                    self.print_result(True, f"{endpoint} properly requires authentication")
                else:
                    self.print_result(False, f"{endpoint} should return 401/403 without auth, got {response.status_code}")
                    all_passed = False
                    
            except Exception as e:
                self.print_result(False, f"Auth test error for {endpoint}: {str(e)}")
                all_passed = False
        
        return all_passed
    
    async def test_sandbox_mode_functionality(self) -> bool:
        """Test that sandbox mode returns proper mock data"""
        self.print_test_header("Sandbox Mode Functionality")
        
        try:
            # Test that we get consistent mock data
            response1 = await self.client.get(
                f"{API_BASE}/open-banking/accounts",
                headers=self.get_auth_headers()
            )
            
            response2 = await self.client.get(
                f"{API_BASE}/open-banking/accounts",
                headers=self.get_auth_headers()
            )
            
            if response1.status_code != 200 or response2.status_code != 200:
                self.print_result(False, "Failed to get accounts for sandbox test")
                return False
            
            data1 = response1.json()
            data2 = response2.json()
            
            # Check that we get the same accounts (sandbox should be consistent)
            if len(data1["accounts"]) != len(data2["accounts"]):
                self.print_result(False, "Inconsistent account count in sandbox mode")
                return False
            
            # Check for expected sandbox accounts
            expected_banks = ["Jordan Bank", "Arab Bank", "Housing Bank"]
            actual_banks = [acc["bank_name"] for acc in data1["accounts"]]
            
            for bank in expected_banks:
                if bank not in actual_banks:
                    self.print_result(False, f"Expected sandbox bank '{bank}' not found")
                    return False
            
            # Check that all accounts have positive balances
            for account in data1["accounts"]:
                if account["balance"] <= 0:
                    self.print_result(False, f"Account {account['account_name']} has non-positive balance")
                    return False
            
            self.print_result(True, f"Sandbox mode working correctly with {len(expected_banks)} mock banks")
            return True
            
        except Exception as e:
            self.print_result(False, f"Sandbox test error: {str(e)}")
            return False
    
    async def run_all_tests(self):
        """Run all Open Banking API tests"""
        print("🚀 Starting Open Banking API Tests")
        print(f"Backend URL: {BACKEND_URL}")
        print(f"API Base: {API_BASE}")
        
        # Setup authentication
        auth_success = await self.register_test_user()
        if not auth_success:
            print("\n❌ Authentication setup failed. Cannot proceed with tests.")
            return
        
        print(f"\n🔐 Authenticated as: {self.user_data['full_name']} ({self.user_data['email']})")
        
        # Run tests
        test_results = []
        
        # Test authentication requirements
        test_results.append(await self.test_authentication_required())
        
        # Test connect accounts endpoint
        test_results.append(await self.test_connect_accounts_endpoint())
        
        # Test get accounts endpoint  
        test_results.append(await self.test_get_accounts_endpoint())
        
        # Test dashboard endpoint
        test_results.append(await self.test_get_dashboard_endpoint())
        
        # Test sandbox functionality
        test_results.append(await self.test_sandbox_mode_functionality())
        
        # Summary
        passed = sum(test_results)
        total = len(test_results)
        
        print(f"\n{'='*60}")
        print(f"🏁 TEST SUMMARY")
        print(f"{'='*60}")
        print(f"✅ Passed: {passed}/{total}")
        print(f"❌ Failed: {total - passed}/{total}")
        
        if passed == total:
            print("🎉 All Open Banking API tests passed!")
        else:
            print("⚠️  Some tests failed. Check the details above.")
        
        return passed == total

async def main():
    """Main test runner"""
    tester = BackendTester()
    try:
        success = await tester.run_all_tests()
        return success
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)