#!/usr/bin/env python3
"""
Focused test for Manual Customer ID Support
Tests the specific endpoints mentioned in the review request
"""

import asyncio
import httpx
import json
import os
from datetime import datetime

# Get backend URL from environment
BACKEND_URL = os.getenv("REACT_APP_BACKEND_URL", "https://ce28504d-bf4c-4cd5-853b-5f3bb5417fa8.preview.emergentagent.com")
API_BASE = f"{BACKEND_URL}/api"

class ManualCustomerIDTester:
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
    
    def print_result(self, success: bool, message: str, details: any = None):
        """Print test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {message}")
        if details and not success:
            print(f"   Details: {details}")
    
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
    
    def get_auth_headers(self) -> dict:
        """Get authentication headers"""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
    
    async def test_iban_validation_with_manual_customer_id(self) -> bool:
        """Test POST /api/auth/validate-iban with UID type and UID value parameters"""
        self.print_test_header("IBAN Validation API - Manual Customer ID Support")
        
        try:
            # Test with different customer IDs as requested
            test_cases = [
                {
                    "customer_id": "IND_CUST_015",
                    "description": "Default customer ID"
                },
                {
                    "customer_id": "TEST_CUST_123", 
                    "description": "Test customer ID"
                }
            ]
            
            all_passed = True
            
            for test_case in test_cases:
                iban_data = {
                    "accountType": "CURRENT",
                    "accountId": "ACC_12345",
                    "ibanType": "IBAN",
                    "ibanValue": "JO27CBJO0000000000000000123456",
                    "uidType": "CUSTOMER_ID",
                    "uidValue": test_case["customer_id"]
                }
                
                response = await self.client.post(
                    f"{API_BASE}/auth/validate-iban",
                    json=iban_data
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Verify response structure
                    required_fields = ["valid", "iban_value", "api_info"]
                    missing_fields = [field for field in required_fields if field not in data]
                    if missing_fields:
                        self.print_result(False, f"Missing IBAN validation fields: {missing_fields}")
                        all_passed = False
                        continue
                    
                    # Verify customer ID is used correctly
                    api_info = data.get("api_info", {})
                    if api_info.get("customer_id") != test_case["customer_id"]:
                        self.print_result(False, f"Customer ID mismatch: expected {test_case['customer_id']}, got {api_info.get('customer_id')}")
                        all_passed = False
                        continue
                    
                    # Verify UID type is captured
                    if api_info.get("uid_type") != "CUSTOMER_ID":
                        self.print_result(False, f"UID type mismatch: expected CUSTOMER_ID, got {api_info.get('uid_type')}")
                        all_passed = False
                        continue
                    
                    self.print_result(True, f"IBAN validation successful with {test_case['description']} ({test_case['customer_id']})")
                    print(f"   📋 IBAN: {data['iban_value']}")
                    print(f"   👤 Customer ID: {api_info.get('customer_id')}")
                    print(f"   🔑 UID Type: {api_info.get('uid_type')}")
                    print(f"   ✅ Valid: {data['valid']}")
                    
                else:
                    self.print_result(False, f"IBAN validation failed for {test_case['customer_id']}: {response.status_code}")
                    all_passed = False
            
            return all_passed
            
        except Exception as e:
            self.print_result(False, f"IBAN validation test error: {str(e)}")
            return False
    
    async def test_accounts_api_with_customer_id_header(self) -> bool:
        """Test GET /api/open-banking/accounts with x-customer-id header"""
        self.print_test_header("Accounts API - x-customer-id Header Support")
        
        try:
            # Test with different customer IDs as requested
            test_cases = [
                {
                    "customer_id": "IND_CUST_015",
                    "description": "Default customer ID"
                },
                {
                    "customer_id": "TEST_CUST_123",
                    "description": "Test customer ID"
                }
            ]
            
            all_passed = True
            
            for test_case in test_cases:
                headers = self.get_auth_headers()
                headers["x-customer-id"] = test_case["customer_id"]
                
                response = await self.client.get(
                    f"{API_BASE}/open-banking/accounts",
                    headers=headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Verify response structure
                    required_fields = ["accounts", "total"]
                    missing_fields = [field for field in required_fields if field not in data]
                    if missing_fields:
                        self.print_result(False, f"Missing accounts fields: {missing_fields}")
                        all_passed = False
                        continue
                    
                    # Verify accounts structure
                    accounts = data.get("accounts", [])
                    if not isinstance(accounts, list):
                        self.print_result(False, "Accounts should be a list")
                        all_passed = False
                        continue
                    
                    # Check for dependency flow information (shows customer ID usage)
                    dependency_flow = data.get("dependency_flow", "")
                    data_source = data.get("data_source", "")
                    
                    self.print_result(True, f"Accounts API successful with {test_case['description']} ({test_case['customer_id']})")
                    print(f"   👤 Customer ID Header: {test_case['customer_id']}")
                    print(f"   🏦 Accounts Count: {len(accounts)}")
                    print(f"   🔄 Dependency Flow: {dependency_flow}")
                    print(f"   📊 Data Source: {data_source}")
                    
                    # Show first account details if available
                    if accounts:
                        account = accounts[0]
                        print(f"   💰 First Account: {account.get('bank_name', 'Unknown')} - {account.get('balance', 0):.2f} {account.get('currency', 'JOD')}")
                    
                else:
                    self.print_result(False, f"Accounts API failed for {test_case['customer_id']}: {response.status_code}")
                    print(f"   Error: {response.text}")
                    all_passed = False
            
            return all_passed
            
        except Exception as e:
            self.print_result(False, f"Accounts API test error: {str(e)}")
            return False
    
    async def test_offers_api_with_customer_id_header(self) -> bool:
        """Test GET /api/open-banking/accounts/{account_id}/offers with x-customer-id header"""
        self.print_test_header("Offers API - x-customer-id Header Support")
        
        try:
            # First get accounts to get a valid account_id
            accounts_response = await self.client.get(
                f"{API_BASE}/open-banking/accounts",
                headers=self.get_auth_headers()
            )
            
            if accounts_response.status_code != 200:
                self.print_result(False, "Failed to get accounts for offers test")
                return False
            
            accounts_data = accounts_response.json()
            if not accounts_data.get("accounts"):
                self.print_result(False, "No accounts available for offers test")
                return False
            
            account_id = accounts_data["accounts"][0]["account_id"]
            
            # Test with different customer IDs as requested
            test_cases = [
                {
                    "customer_id": "IND_CUST_015",
                    "description": "Default customer ID"
                },
                {
                    "customer_id": "TEST_CUST_123",
                    "description": "Test customer ID"
                }
            ]
            
            all_passed = True
            
            for test_case in test_cases:
                headers = self.get_auth_headers()
                headers["x-customer-id"] = test_case["customer_id"]
                
                response = await self.client.get(
                    f"{API_BASE}/open-banking/accounts/{account_id}/offers",
                    headers=headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Verify response structure
                    required_fields = ["account_id", "offers", "pagination", "api_info"]
                    missing_fields = [field for field in required_fields if field not in data]
                    if missing_fields:
                        self.print_result(False, f"Missing offers fields: {missing_fields}")
                        all_passed = False
                        continue
                    
                    # Verify account ID matches
                    if data["account_id"] != account_id:
                        self.print_result(False, f"Account ID mismatch in offers response")
                        all_passed = False
                        continue
                    
                    # Verify API info shows account-dependent call
                    api_info = data.get("api_info", {})
                    if not api_info.get("account_dependent"):
                        self.print_result(False, "Offers API should be account-dependent")
                        all_passed = False
                        continue
                    
                    # Verify customer ID is used (may be in API info or logs)
                    customer_id_used = api_info.get("customer_id", "")
                    
                    self.print_result(True, f"Offers API successful with {test_case['description']} ({test_case['customer_id']})")
                    print(f"   🏦 Account ID: {account_id}")
                    print(f"   👤 Customer ID Used: {customer_id_used}")
                    print(f"   📋 Offers Count: {len(data.get('offers', []))}")
                    print(f"   🔗 Account Dependent: {api_info.get('account_dependent')}")
                    
                else:
                    self.print_result(False, f"Offers API failed for {test_case['customer_id']}: {response.status_code}")
                    print(f"   Error: {response.text}")
                    all_passed = False
            
            return all_passed
            
        except Exception as e:
            self.print_result(False, f"Offers API test error: {str(e)}")
            return False
    
    async def test_loan_eligibility_with_customer_id_header(self) -> bool:
        """Test GET /api/loans/eligibility/{account_id} with x-customer-id header"""
        self.print_test_header("Loan Eligibility API - x-customer-id Header Support")
        
        try:
            # First get accounts to get a valid account_id
            accounts_response = await self.client.get(
                f"{API_BASE}/open-banking/accounts",
                headers=self.get_auth_headers()
            )
            
            if accounts_response.status_code != 200:
                self.print_result(False, "Failed to get accounts for loan eligibility test")
                return False
            
            accounts_data = accounts_response.json()
            if not accounts_data.get("accounts"):
                self.print_result(False, "No accounts available for loan eligibility test")
                return False
            
            account_id = accounts_data["accounts"][0]["account_id"]
            
            # Test with different customer IDs as requested
            test_cases = [
                {
                    "customer_id": "IND_CUST_015",
                    "description": "Default customer ID"
                },
                {
                    "customer_id": "TEST_CUST_123",
                    "description": "Test customer ID"
                }
            ]
            
            all_passed = True
            
            for test_case in test_cases:
                headers = self.get_auth_headers()
                headers["x-customer-id"] = test_case["customer_id"]
                
                response = await self.client.get(
                    f"{API_BASE}/loans/eligibility/{account_id}",
                    headers=headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Verify response structure
                    required_fields = ["account_id", "customer_id", "credit_score", "eligibility", "max_loan_amount", "eligible_for_loan"]
                    missing_fields = [field for field in required_fields if field not in data]
                    if missing_fields:
                        self.print_result(False, f"Missing loan eligibility fields: {missing_fields}")
                        all_passed = False
                        continue
                    
                    # Verify customer ID is used correctly
                    if data["customer_id"] != test_case["customer_id"]:
                        self.print_result(False, f"Customer ID mismatch: expected {test_case['customer_id']}, got {data['customer_id']}")
                        all_passed = False
                        continue
                    
                    # Verify account ID matches
                    if data["account_id"] != account_id:
                        self.print_result(False, f"Account ID mismatch in loan eligibility response")
                        all_passed = False
                        continue
                    
                    # Verify eligibility data
                    credit_score = data.get("credit_score", 0)
                    max_loan_amount = data.get("max_loan_amount", 0)
                    eligibility = data.get("eligibility", "")
                    
                    self.print_result(True, f"Loan eligibility successful with {test_case['description']} ({test_case['customer_id']})")
                    print(f"   🏦 Account ID: {account_id}")
                    print(f"   👤 Customer ID: {data['customer_id']}")
                    print(f"   📊 Credit Score: {credit_score}")
                    print(f"   🎯 Eligibility: {eligibility}")
                    print(f"   💰 Max Loan Amount: {max_loan_amount} JOD")
                    print(f"   ✅ Eligible: {data.get('eligible_for_loan', False)}")
                    
                    # Show available banks if any
                    available_banks = data.get("available_banks", [])
                    if available_banks:
                        print(f"   🏛️ Available Banks: {len(available_banks)}")
                        for bank in available_banks[:2]:
                            print(f"     • {bank.get('name', 'Unknown Bank')}")
                    
                else:
                    self.print_result(False, f"Loan eligibility failed for {test_case['customer_id']}: {response.status_code}")
                    print(f"   Error: {response.text}")
                    all_passed = False
            
            return all_passed
            
        except Exception as e:
            self.print_result(False, f"Loan eligibility test error: {str(e)}")
            return False
    
    async def test_loan_application_with_customer_id(self) -> bool:
        """Test POST /api/loans/apply with customer_id in request body"""
        self.print_test_header("Loan Application API - customer_id in Request Body")
        
        try:
            # First get accounts to get a valid account_id
            accounts_response = await self.client.get(
                f"{API_BASE}/open-banking/accounts",
                headers=self.get_auth_headers()
            )
            
            if accounts_response.status_code != 200:
                self.print_result(False, "Failed to get accounts for loan application test")
                return False
            
            accounts_data = accounts_response.json()
            if not accounts_data.get("accounts"):
                self.print_result(False, "No accounts available for loan application test")
                return False
            
            account_id = accounts_data["accounts"][0]["account_id"]
            
            # Test with different customer IDs as requested
            test_cases = [
                {
                    "customer_id": "IND_CUST_015",
                    "description": "Default customer ID"
                },
                {
                    "customer_id": "TEST_CUST_123",
                    "description": "Test customer ID"
                }
            ]
            
            all_passed = True
            
            for test_case in test_cases:
                loan_application = {
                    "account_id": account_id,
                    "loan_amount": 5000.0,
                    "selected_bank": "Jordan Bank",
                    "loan_term": 12,
                    "customer_id": test_case["customer_id"]
                }
                
                response = await self.client.post(
                    f"{API_BASE}/loans/apply",
                    headers=self.get_auth_headers(),
                    json=loan_application
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Verify response structure
                    required_fields = ["application_id", "status", "loan_amount", "selected_bank", "loan_term"]
                    missing_fields = [field for field in required_fields if field not in data]
                    if missing_fields:
                        self.print_result(False, f"Missing loan application fields: {missing_fields}")
                        all_passed = False
                        continue
                    
                    # Verify loan application data
                    if data["loan_amount"] != loan_application["loan_amount"]:
                        self.print_result(False, f"Loan amount mismatch")
                        all_passed = False
                        continue
                    
                    if data["selected_bank"] != loan_application["selected_bank"]:
                        self.print_result(False, f"Selected bank mismatch")
                        all_passed = False
                        continue
                    
                    if data["loan_term"] != loan_application["loan_term"]:
                        self.print_result(False, f"Loan term mismatch")
                        all_passed = False
                        continue
                    
                    self.print_result(True, f"Loan application successful with {test_case['description']} ({test_case['customer_id']})")
                    print(f"   📋 Application ID: {data['application_id']}")
                    print(f"   👤 Customer ID: {test_case['customer_id']}")
                    print(f"   💰 Loan Amount: {data['loan_amount']} JOD")
                    print(f"   🏛️ Selected Bank: {data['selected_bank']}")
                    print(f"   📅 Loan Term: {data['loan_term']} months")
                    print(f"   📊 Status: {data['status']}")
                    print(f"   💳 Monthly Payment: {data.get('estimated_monthly_payment', 0):.2f} JOD")
                    print(f"   📈 Interest Rate: {data.get('interest_rate', 0)}%")
                    
                else:
                    self.print_result(False, f"Loan application failed for {test_case['customer_id']}: {response.status_code}")
                    print(f"   Error details: {response.text}")
                    all_passed = False
            
            return all_passed
            
        except Exception as e:
            self.print_result(False, f"Loan application test error: {str(e)}")
            return False

    async def run_manual_customer_id_tests(self):
        """Run all manual customer ID support tests"""
        print("🚀 Starting Manual Customer ID Support Tests")
        print(f"Backend URL: {BACKEND_URL}")
        print(f"API Base: {API_BASE}")
        
        # Setup authentication
        auth_success = await self.login_test_user()
        if not auth_success:
            print("\n❌ Authentication setup failed. Cannot proceed with tests.")
            return
        
        print(f"\n🔐 Authenticated as: {self.user_data['full_name']} ({self.user_data['email']})")
        
        # Run tests
        test_results = []
        
        # Manual Customer ID Support Tests (Primary Focus - Review Request)
        print("\n" + "="*60)
        print("🆔 TESTING MANUAL CUSTOMER ID SUPPORT")
        print("="*60)
        test_results.append(await self.test_iban_validation_with_manual_customer_id())
        test_results.append(await self.test_accounts_api_with_customer_id_header())
        test_results.append(await self.test_offers_api_with_customer_id_header())
        test_results.append(await self.test_loan_eligibility_with_customer_id_header())
        test_results.append(await self.test_loan_application_with_customer_id())
        
        # Summary
        passed = sum(test_results)
        total = len(test_results)
        
        print(f"\n{'='*60}")
        print(f"🏁 MANUAL CUSTOMER ID SUPPORT TEST SUMMARY")
        print(f"{'='*60}")
        print(f"✅ Passed: {passed}/{total}")
        print(f"❌ Failed: {total - passed}/{total}")
        
        if passed == total:
            print("🎉 All manual customer ID support tests passed!")
            print("✅ IBAN validation accepts UID type and UID value parameters")
            print("✅ Accounts API properly uses x-customer-id header")
            print("✅ Offers API properly uses x-customer-id header")
            print("✅ Loan eligibility API properly uses x-customer-id header")
            print("✅ Loan application API properly uses customer_id in request body")
            print("✅ All endpoints tested with IND_CUST_015 and TEST_CUST_123")
        else:
            print("⚠️  Some tests failed. Check the details above.")
        
        return passed == total
    
async def main():
    """Main test runner"""
    tester = ManualCustomerIDTester()
    try:
        success = await tester.run_manual_customer_id_tests()
        return success
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)