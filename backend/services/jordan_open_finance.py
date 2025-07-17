import httpx
import os
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
import uuid
from dotenv import load_dotenv

load_dotenv()

class JordanOpenFinanceService:
    """
    Service for integrating with Jordan Open Finance APIs (JoPACC)
    Supports AIS, PIS, FPS, and Extended Services
    Based on Jordan Open Finance Standards 2025
    """
    
    def __init__(self):
        # Production JoPACC API Configuration
        self.base_url = os.getenv("JORDAN_OPEN_FINANCE_BASE_URL", "https://api.jopacc.com")
        self.sandbox_url = os.getenv("JORDAN_OPEN_FINANCE_SANDBOX_URL", "https://jpcjofsdev.devportal-az-eu.webmethods.io")
        self.client_id = os.getenv("JORDAN_OPEN_FINANCE_CLIENT_ID")
        self.client_secret = os.getenv("JORDAN_OPEN_FINANCE_CLIENT_SECRET")
        self.api_key = os.getenv("JORDAN_OPEN_FINANCE_API_KEY")
        self.x_fapi_financial_id = os.getenv("JORDAN_OPEN_FINANCE_FINANCIAL_ID", "001")
        self.timeout = 30
        
        # Set sandbox mode to false for production deployment
        self.sandbox_mode = False
        self.api_base = self.base_url # Use production URL
        
    async def get_access_token(self) -> str:
        """Get OAuth2 access token for API authentication following JoPACC standards"""
        if self.sandbox_mode:
            return "sandbox_access_token_" + str(uuid.uuid4())[:8]
            
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            # JoPACC OAuth2 Token Endpoint
            response = await client.post(
                f"{self.api_base}/oauth2/token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "scope": "accounts payments funds-confirmation directory"
                },
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Accept": "application/json"
                }
            )
            response.raise_for_status()
            return response.json()["access_token"]
    
    async def get_headers(self) -> Dict[str, str]:
        """Get standard headers for JoPACC API requests"""
        access_token = await self.get_access_token()
        return {
            "Authorization": f"Bearer {access_token}",
            "x-fapi-financial-id": self.x_fapi_financial_id,
            "x-fapi-customer-ip-address": "127.0.0.1",
            "x-fapi-interaction-id": str(uuid.uuid4()),
            "Content-Type": "application/json",
            "Accept": "application/json",
            "x-jws-signature": "",  # Would need proper JWS implementation
            "x-idempotency-key": str(uuid.uuid4())
        }
    
    # Account Information Services (AIS) - Following JoPACC v1.0 Standards
    async def create_account_access_consent(self, permissions: List[str], user_id: str) -> Dict[str, Any]:
        """Create account access consent following JoPACC AIS standards"""
        if self.sandbox_mode:
            consent_id = f"urn:jopacc:consent:{str(uuid.uuid4())}"
            return {
                "Data": {
                    "ConsentId": consent_id,
                    "Status": "AwaitingAuthorisation",
                    "StatusUpdateDateTime": datetime.utcnow().isoformat() + "Z",
                    "CreationDateTime": datetime.utcnow().isoformat() + "Z",
                    "Permissions": permissions,
                    "ExpirationDateTime": (datetime.utcnow() + timedelta(days=90)).isoformat() + "Z"
                },
                "Links": {
                    "Self": f"/open-banking/v1.0/aisp/account-access-consents/{consent_id}"
                }
            }
        
        headers = await self.get_headers()
        consent_data = {
            "Data": {
                "Permissions": permissions,
                "ExpirationDateTime": (datetime.utcnow() + timedelta(days=90)).isoformat() + "Z",
                "TransactionFromDateTime": datetime.utcnow().isoformat() + "Z",
                "TransactionToDateTime": (datetime.utcnow() + timedelta(days=90)).isoformat() + "Z"
            },
            "Risk": {}
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.api_base}/open-banking/v1.0/aisp/account-access-consents",
                headers=headers,
                json=consent_data
            )
            response.raise_for_status()
            return response.json()
    
    async def get_accounts(self, consent_id: str) -> List[Dict[str, Any]]:
        """Get user accounts following JoPACC AIS v1.0 standards"""
        if self.sandbox_mode:
            return {
                "Data": {
                    "Account": [
                        {
                            "AccountId": "acc_001_jordan_bank",
                            "Status": "Enabled",
                            "StatusUpdateDateTime": datetime.utcnow().isoformat() + "Z",
                            "Currency": "JOD",
                            "AccountType": "Personal",
                            "AccountSubType": "CurrentAccount",
                            "Nickname": "Jordan Bank Current",
                            "OpeningDate": "2023-01-01T00:00:00Z",
                            "Account": [
                                {
                                    "SchemeName": "SortCodeAccountNumber",
                                    "Identification": "1234567890",
                                    "Name": "Jordan Bank - Current Account"
                                }
                            ],
                            "Servicer": {
                                "SchemeName": "BICFI",
                                "Identification": "JBANKJOA"
                            }
                        },
                        {
                            "AccountId": "acc_002_arab_bank",
                            "Status": "Enabled",
                            "StatusUpdateDateTime": datetime.utcnow().isoformat() + "Z",
                            "Currency": "JOD",
                            "AccountType": "Personal",
                            "AccountSubType": "Savings",
                            "Nickname": "Arab Bank Savings",
                            "OpeningDate": "2023-03-15T00:00:00Z",
                            "Account": [
                                {
                                    "SchemeName": "SortCodeAccountNumber",
                                    "Identification": "9876543210",
                                    "Name": "Arab Bank - Savings Account"
                                }
                            ],
                            "Servicer": {
                                "SchemeName": "BICFI",
                                "Identification": "ARABJOAM"
                            }
                        },
                        {
                            "AccountId": "acc_003_housing_bank",
                            "Status": "Enabled",
                            "StatusUpdateDateTime": datetime.utcnow().isoformat() + "Z",
                            "Currency": "JOD",
                            "AccountType": "Business",
                            "AccountSubType": "CurrentAccount",
                            "Nickname": "Housing Bank Business",
                            "OpeningDate": "2023-06-01T00:00:00Z",
                            "Account": [
                                {
                                    "SchemeName": "SortCodeAccountNumber",
                                    "Identification": "5555666677",
                                    "Name": "Housing Bank - Business Account"
                                }
                            ],
                            "Servicer": {
                                "SchemeName": "BICFI",
                                "Identification": "HBANKJOA"
                            }
                        }
                    ]
                },
                "Links": {
                    "Self": "/open-banking/v1.0/aisp/accounts"
                }
            }
        
        headers = await self.get_headers()
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.api_base}/open-banking/v1.0/aisp/accounts",
                headers=headers
            )
            response.raise_for_status()
            return response.json()
    
    async def get_account_balances(self, account_id: str) -> Dict[str, Any]:
        """Get account balances following JoPACC AIS v1.0 standards"""
        if self.sandbox_mode:
            # Mock balance data based on account_id
            mock_balances = {
                "acc_001_jordan_bank": {
                    "Amount": "2500.75",
                    "Currency": "JOD"
                },
                "acc_002_arab_bank": {
                    "Amount": "15000.00",
                    "Currency": "JOD"
                },
                "acc_003_housing_bank": {
                    "Amount": "8750.50",
                    "Currency": "JOD"
                }
            }
            
            balance_info = mock_balances.get(account_id, {"Amount": "0.00", "Currency": "JOD"})
            
            return {
                "Data": {
                    "Balance": [
                        {
                            "AccountId": account_id,
                            "Amount": balance_info,
                            "CreditDebitIndicator": "Credit",
                            "Type": "ClosingAvailable",
                            "DateTime": datetime.utcnow().isoformat() + "Z"
                        },
                        {
                            "AccountId": account_id,
                            "Amount": {
                                "Amount": str(float(balance_info["Amount"]) - 100),
                                "Currency": balance_info["Currency"]
                            },
                            "CreditDebitIndicator": "Credit",
                            "Type": "InterimAvailable",
                            "DateTime": datetime.utcnow().isoformat() + "Z"
                        }
                    ]
                },
                "Links": {
                    "Self": f"/open-banking/v1.0/aisp/accounts/{account_id}/balances"
                }
            }
        
        headers = await self.get_headers()
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.api_base}/open-banking/v1.0/aisp/accounts/{account_id}/balances",
                headers=headers
            )
            response.raise_for_status()
            return response.json()
    
    async def get_account_transactions(self, account_id: str, from_booking_date: Optional[datetime] = None,
                                     to_booking_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Get account transactions following JoPACC AIS v1.0 standards"""
        if self.sandbox_mode:
            # Generate mock transaction data in JoPACC format
            base_date = datetime.utcnow() - timedelta(days=30)
            transactions = []
            
            mock_transactions = [
                {"amount": "-250.00", "description": "ATM Cash Withdrawal", "merchant": "Jordan Bank ATM", "reference": "ATM001"},
                {"amount": "1500.00", "description": "Salary Payment", "merchant": "ABC Company Ltd", "reference": "SAL001"},
                {"amount": "-75.50", "description": "Grocery Purchase", "merchant": "Carrefour Jordan", "reference": "POS001"},
                {"amount": "-120.00", "description": "Fuel Purchase", "merchant": "Total Jordan", "reference": "POS002"},
                {"amount": "500.00", "description": "Money Transfer", "merchant": "Family Transfer", "reference": "TRF001"},
                {"amount": "-45.25", "description": "Restaurant Payment", "merchant": "Fakhr El-Din Restaurant", "reference": "POS003"},
                {"amount": "-200.00", "description": "Online Purchase", "merchant": "Amazon", "reference": "WEB001"},
                {"amount": "-35.00", "description": "Mobile Top-up", "merchant": "Zain Jordan", "reference": "BIL001"},
                {"amount": "2000.00", "description": "Investment Return", "merchant": "Jordan Investment Bank", "reference": "INV001"},
                {"amount": "-150.00", "description": "Electricity Bill", "merchant": "EDCO", "reference": "BIL002"}
            ]
            
            for i, tx in enumerate(mock_transactions):
                transaction_date = base_date + timedelta(days=i*3)
                amount = float(tx["amount"])
                
                transactions.append({
                    "AccountId": account_id,
                    "TransactionId": f"tx_{account_id}_{i+1}",
                    "TransactionReference": tx["reference"],
                    "Amount": {
                        "Amount": str(abs(amount)),
                        "Currency": "JOD"
                    },
                    "CreditDebitIndicator": "Credit" if amount > 0 else "Debit",
                    "Status": "Booked",
                    "BookingDateTime": transaction_date.isoformat() + "Z",
                    "ValueDateTime": transaction_date.isoformat() + "Z",
                    "TransactionInformation": tx["description"],
                    "MerchantDetails": {
                        "MerchantName": tx["merchant"],
                        "MerchantCategoryCode": "5411"
                    },
                    "ProprietaryBankTransactionCode": {
                        "Code": "Transfer",
                        "Issuer": "JoPACC"
                    }
                })
            
            return {
                "Data": {
                    "Transaction": transactions
                },
                "Links": {
                    "Self": f"/open-banking/v1.0/aisp/accounts/{account_id}/transactions"
                }
            }
        
        headers = await self.get_headers()
        params = {}
        if from_booking_date:
            params["fromBookingDateTime"] = from_booking_date.isoformat() + "Z"
        if to_booking_date:
            params["toBookingDateTime"] = to_booking_date.isoformat() + "Z"
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.api_base}/open-banking/v1.0/aisp/accounts/{account_id}/transactions",
                headers=headers,
                params=params
            )
            response.raise_for_status()
            return response.json()
    
    # Payment Initiation Services (PIS) - Following JoPACC v1.0 Standards
    async def create_payment_consent(self, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create payment consent following JoPACC PIS v1.0 standards"""
        if self.sandbox_mode:
            consent_id = f"urn:jopacc:payment-consent:{str(uuid.uuid4())}"
            return {
                "Data": {
                    "ConsentId": consent_id,
                    "Status": "AwaitingAuthorisation",
                    "StatusUpdateDateTime": datetime.utcnow().isoformat() + "Z",
                    "CreationDateTime": datetime.utcnow().isoformat() + "Z",
                    "Initiation": payment_data
                },
                "Links": {
                    "Self": f"/open-banking/v1.0/pisp/domestic-payment-consents/{consent_id}"
                }
            }
        
        headers = await self.get_headers()
        consent_data = {
            "Data": {
                "Initiation": payment_data
            },
            "Risk": {
                "PaymentContextCode": "Other"
            }
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.api_base}/open-banking/v1.0/pisp/domestic-payment-consents",
                headers=headers,
                json=consent_data
            )
            response.raise_for_status()
            return response.json()
    
    async def create_payment(self, consent_id: str, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create payment following JoPACC PIS v1.0 standards"""
        if self.sandbox_mode:
            payment_id = f"urn:jopacc:payment:{str(uuid.uuid4())}"
            return {
                "Data": {
                    "DomesticPaymentId": payment_id,
                    "ConsentId": consent_id,
                    "Status": "AcceptedSettlementInProcess",
                    "StatusUpdateDateTime": datetime.utcnow().isoformat() + "Z",
                    "CreationDateTime": datetime.utcnow().isoformat() + "Z",
                    "Initiation": payment_data
                },
                "Links": {
                    "Self": f"/open-banking/v1.0/pisp/domestic-payments/{payment_id}"
                }
            }
        
        headers = await self.get_headers()
        payment_request = {
            "Data": {
                "ConsentId": consent_id,
                "Initiation": payment_data
            }
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.api_base}/open-banking/v1.0/pisp/domestic-payments",
                headers=headers,
                json=payment_request
            )
            response.raise_for_status()
            return response.json()
    
    # Extended Services - FX and Additional Services
    async def get_exchange_rates(self, base_currency: str = "JOD") -> Dict[str, Any]:
        """Get exchange rates - Extended Service"""
        if self.sandbox_mode:
            return {
                "Data": {
                    "ExchangeRate": [
                        {
                            "UnitCurrency": "JOD",
                            "ExchangeRate": "1.41",
                            "RateType": "Actual",
                            "ContractIdentification": "FX001",
                            "QuotationDate": datetime.utcnow().isoformat() + "Z",
                            "TargetCurrency": "USD"
                        },
                        {
                            "UnitCurrency": "JOD",
                            "ExchangeRate": "1.29",
                            "RateType": "Actual",
                            "ContractIdentification": "FX002",
                            "QuotationDate": datetime.utcnow().isoformat() + "Z",
                            "TargetCurrency": "EUR"
                        },
                        {
                            "UnitCurrency": "JOD",
                            "ExchangeRate": "1.13",
                            "RateType": "Actual",
                            "ContractIdentification": "FX003",
                            "QuotationDate": datetime.utcnow().isoformat() + "Z",
                            "TargetCurrency": "GBP"
                        }
                    ]
                },
                "Links": {
                    "Self": "/open-banking/v1.0/fx/exchange-rates"
                }
            }
        
        headers = await self.get_headers()
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.api_base}/open-banking/v1.0/fx/exchange-rates",
                headers=headers,
                params={"baseCurrency": base_currency}
            )
            response.raise_for_status()
            return response.json()
    
    # Legacy methods for backward compatibility
    async def get_user_accounts(self, user_consent_id: str) -> List[Dict[str, Any]]:
        """Legacy method - converts new format to old format"""
        accounts_response = await self.get_accounts(user_consent_id)
        
        if self.sandbox_mode:
            # Convert new format to legacy format
            accounts = []
            for account in accounts_response["Data"]["Account"]:
                accounts.append({
                    "account_id": account["AccountId"],
                    "account_name": account["Nickname"],
                    "account_number": account["Account"][0]["Identification"],
                    "bank_name": account["Account"][0]["Name"].split(" - ")[0],
                    "bank_code": account["Servicer"]["Identification"],
                    "account_type": account["AccountSubType"].lower(),
                    "currency": account["Currency"],
                    "balance": 2500.75 if "001" in account["AccountId"] else 15000.00 if "002" in account["AccountId"] else 8750.50,
                    "available_balance": 2400.75 if "001" in account["AccountId"] else 15000.00 if "002" in account["AccountId"] else 8500.50,
                    "status": "active",
                    "last_updated": datetime.utcnow().isoformat()
                })
            return accounts
        
        # Production conversion would be more complex
        return []
    
    async def request_user_consent(self, user_id: str, permissions: List[str]) -> Dict[str, Any]:
        """Legacy method - creates account access consent"""
        consent_response = await self.create_account_access_consent(permissions, user_id)
        
        if self.sandbox_mode:
            return {
                "consent_id": consent_response["Data"]["ConsentId"],
                "user_id": user_id,
                "permissions": permissions,
                "status": "granted",
                "consent_url": f"https://sandbox.jopacc.com/consent/{consent_response["Data"]["ConsentId"]}",
                "expires_at": consent_response["Data"]["ExpirationDateTime"],
                "created_at": consent_response["Data"]["CreationDateTime"]
            }
        
        return consent_response
        
    # PIS (Payment Initiation Services)
    async def initiate_payment(self, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Initiate a payment using PIS"""
        if self.sandbox_mode:
            payment_id = f"pmt_{str(uuid.uuid4())[:8]}"
            return {
                "payment_id": payment_id,
                "status": "pending",
                "amount": payment_data["amount"],
                "currency": payment_data.get("currency", "JOD"),
                "recipient": payment_data["recipient"],
                "reference": payment_data.get("reference", ""),
                "created_at": datetime.utcnow().isoformat(),
                "estimated_completion": (datetime.utcnow() + timedelta(minutes=5)).isoformat()
            }
        
        headers = await self.get_headers()
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.api_base}/pis/v1/payments",
                headers=headers,
                json=payment_data
            )
            response.raise_for_status()
            return response.json()
    
    async def get_payment_status(self, payment_id: str) -> Dict[str, Any]:
        """Get payment status"""
        if self.sandbox_mode:
            return {
                "payment_id": payment_id,
                "status": "completed",
                "updated_at": datetime.utcnow().isoformat()
            }
        
        headers = await self.get_headers()
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.api_base}/pis/v1/payments/{payment_id}",
                headers=headers
            )
            response.raise_for_status()
            return response.json()
    
    # FX (Foreign Exchange)
    async def get_exchange_rates(self, base_currency: str = "JOD") -> Dict[str, Any]:
        """Get current exchange rates"""
        if self.sandbox_mode:
            return {
                "base_currency": base_currency,
                "rates": {
                    "USD": 1.41,
                    "EUR": 1.29,
                    "GBP": 1.13,
                    "SAR": 5.28,
                    "AED": 5.18,
                    "KWD": 0.43,
                    "QAR": 5.13
                },
                "last_updated": datetime.utcnow().isoformat()
            }
        
        headers = await self.get_headers()
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.api_base}/fx/v1/rates",
                headers=headers,
                params={"base_currency": base_currency}
            )
            response.raise_for_status()
            return response.json()
    
    async def convert_currency(self, from_currency: str, to_currency: str, amount: float) -> Dict[str, Any]:
        """Convert currency amount"""
        if self.sandbox_mode:
            # Mock conversion rates
            rates = {
                ("JOD", "USD"): 1.41,
                ("USD", "JOD"): 0.71,
                ("JOD", "EUR"): 1.29,
                ("EUR", "JOD"): 0.77,
                ("JOD", "STABLECOIN"): 1.0,  # 1:1 with our stablecoin
                ("STABLECOIN", "JOD"): 1.0
            }
            
            rate = rates.get((from_currency, to_currency), 1.0)
            converted_amount = amount * rate
            
            return {
                "from_currency": from_currency,
                "to_currency": to_currency,
                "original_amount": amount,
                "converted_amount": converted_amount,
                "exchange_rate": rate,
                "conversion_date": datetime.utcnow().isoformat()
            }
        
        headers = await self.get_headers()
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.api_base}/fx/v1/convert",
                headers=headers,
                json={
                    "from_currency": from_currency,
                    "to_currency": to_currency,
                    "amount": amount
                }
            )
            response.raise_for_status()
            return response.json()
    
    # FPS (Financial Products Services)
    async def get_financial_products(self, user_id: str) -> List[Dict[str, Any]]:
        """Get available financial products for user"""
        if self.sandbox_mode:
            return [
                {
                    "product_id": "loan_001",
                    "product_name": "Personal Loan",
                    "bank_name": "Jordan Bank",
                    "product_type": "loan",
                    "interest_rate": 8.5,
                    "max_amount": 50000,
                    "min_amount": 1000,
                    "term_months": 60,
                    "description": "Personal loan with competitive rates",
                    "eligibility": "Minimum income 500 JOD",
                    "status": "available"
                },
                {
                    "product_id": "cc_001",
                    "product_name": "Platinum Credit Card",
                    "bank_name": "Arab Bank",
                    "product_type": "credit_card",
                    "interest_rate": 18.0,
                    "credit_limit": 10000,
                    "annual_fee": 50,
                    "description": "Premium credit card with rewards",
                    "eligibility": "Minimum income 800 JOD",
                    "status": "available"
                },
                {
                    "product_id": "deposit_001",
                    "product_name": "High Yield Savings",
                    "bank_name": "Housing Bank",
                    "product_type": "deposit",
                    "interest_rate": 4.5,
                    "min_amount": 1000,
                    "term_months": 12,
                    "description": "Fixed deposit with guaranteed returns",
                    "eligibility": "Minimum deposit 1000 JOD",
                    "status": "available"
                }
            ]
        
        headers = await self.get_headers()
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.api_base}/fps/v1/products",
                headers=headers,
                params={"user_id": user_id}
            )
            response.raise_for_status()
            return response.json()["products"]
    
    async def apply_for_product(self, product_id: str, user_id: str, application_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply for a financial product"""
        if self.sandbox_mode:
            application_id = f"app_{str(uuid.uuid4())[:8]}"
            return {
                "application_id": application_id,
                "product_id": product_id,
                "user_id": user_id,
                "status": "pending",
                "submitted_at": datetime.utcnow().isoformat(),
                "estimated_decision_date": (datetime.utcnow() + timedelta(days=3)).isoformat()
            }
        
        headers = await self.get_headers()
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.api_base}/fps/v1/applications",
                headers=headers,
                json={
                    "product_id": product_id,
                    "user_id": user_id,
                    **application_data
                }
            )
            response.raise_for_status()
            return response.json()
    
    # Consent Management
    async def request_user_consent(self, user_id: str, permissions: List[str]) -> Dict[str, Any]:
        """Request user consent for accessing their banking data"""
        if self.sandbox_mode:
            consent_id = f"consent_{str(uuid.uuid4())[:8]}"
            return {
                "consent_id": consent_id,
                "user_id": user_id,
                "permissions": permissions,
                "status": "granted",
                "consent_url": f"https://sandbox.jopacc.com/consent/{consent_id}",
                "expires_at": (datetime.utcnow() + timedelta(days=90)).isoformat(),
                "created_at": datetime.utcnow().isoformat()
            }
        
        headers = await self.get_headers()
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.api_base}/consent/v1/requests",
                headers=headers,
                json={
                    "user_id": user_id,
                    "permissions": permissions,
                    "redirect_uri": "https://your-app.com/callback"
                }
            )
            response.raise_for_status()
            return response.json()
    
    async def get_consent_status(self, consent_id: str) -> Dict[str, Any]:
        """Get consent status"""
        if self.sandbox_mode:
            return {
                "consent_id": consent_id,
                "status": "granted",
                "permissions": ["ais", "pis", "fps", "fx"],
                "expires_at": (datetime.utcnow() + timedelta(days=90)).isoformat()
            }
        
        headers = await self.get_headers()
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.api_base}/consent/v1/status/{consent_id}",
                headers=headers
            )
            response.raise_for_status()
            return response.json()

