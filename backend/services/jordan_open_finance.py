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
    Service for integrating with Jordan Open Finance APIs
    Includes AIS, PIS, FPS, and FX services
    """
    
    def __init__(self):
        self.base_url = os.getenv("JORDAN_OPEN_FINANCE_BASE_URL", "https://sandbox.jopacc.com")
        self.client_id = os.getenv("JORDAN_OPEN_FINANCE_CLIENT_ID")
        self.client_secret = os.getenv("JORDAN_OPEN_FINANCE_CLIENT_SECRET")
        self.api_key = os.getenv("JORDAN_OPEN_FINANCE_API_KEY")
        self.timeout = 30
        
        # For sandbox/development, we'll use mock data
        self.sandbox_mode = os.getenv("JORDAN_OPEN_FINANCE_SANDBOX", "true").lower() == "true"
        
    async def get_access_token(self) -> str:
        """Get OAuth2 access token for API authentication"""
        if self.sandbox_mode:
            return "sandbox_access_token_" + str(uuid.uuid4())[:8]
            
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/oauth2/token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "scope": "ais pis fps fx"
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            response.raise_for_status()
            return response.json()["access_token"]
    
    async def get_headers(self) -> Dict[str, str]:
        """Get standard headers for API requests"""
        access_token = await self.get_access_token()
        return {
            "Authorization": f"Bearer {access_token}",
            "X-API-Key": self.api_key or "sandbox_api_key",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    # AIS (Account Information Services)
    async def get_user_accounts(self, user_consent_id: str) -> List[Dict[str, Any]]:
        """Get list of user's bank accounts"""
        if self.sandbox_mode:
            return [
                {
                    "account_id": "acc_001_jordan_bank",
                    "account_name": "Jordan Bank - Current Account",
                    "account_number": "1234567890",
                    "bank_name": "Jordan Bank",
                    "bank_code": "JB001",
                    "account_type": "current",
                    "currency": "JOD",
                    "balance": 2500.75,
                    "available_balance": 2400.75,
                    "status": "active",
                    "last_updated": datetime.utcnow().isoformat()
                },
                {
                    "account_id": "acc_002_arab_bank",
                    "account_name": "Arab Bank - Savings Account",
                    "account_number": "9876543210",
                    "bank_name": "Arab Bank",
                    "bank_code": "AB002",
                    "account_type": "savings",
                    "currency": "JOD",
                    "balance": 15000.00,
                    "available_balance": 15000.00,
                    "status": "active",
                    "last_updated": datetime.utcnow().isoformat()
                },
                {
                    "account_id": "acc_003_housing_bank",
                    "account_name": "Housing Bank - Business Account",
                    "account_number": "5555666677",
                    "bank_name": "Housing Bank",
                    "bank_code": "HB003",
                    "account_type": "business",
                    "currency": "JOD",
                    "balance": 8750.50,
                    "available_balance": 8500.50,
                    "status": "active",
                    "last_updated": datetime.utcnow().isoformat()
                }
            ]
        
        headers = await self.get_headers()
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/ais/v1/accounts",
                headers=headers,
                params={"consent_id": user_consent_id}
            )
            response.raise_for_status()
            return response.json()["accounts"]
    
    async def get_account_balance(self, account_id: str, user_consent_id: str) -> Dict[str, Any]:
        """Get specific account balance"""
        if self.sandbox_mode:
            # Mock balance data based on account_id
            mock_balances = {
                "acc_001_jordan_bank": {"balance": 2500.75, "available_balance": 2400.75},
                "acc_002_arab_bank": {"balance": 15000.00, "available_balance": 15000.00},
                "acc_003_housing_bank": {"balance": 8750.50, "available_balance": 8500.50}
            }
            return mock_balances.get(account_id, {"balance": 0.0, "available_balance": 0.0})
        
        headers = await self.get_headers()
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/ais/v1/accounts/{account_id}/balance",
                headers=headers,
                params={"consent_id": user_consent_id}
            )
            response.raise_for_status()
            return response.json()
    
    async def get_account_transactions(self, account_id: str, user_consent_id: str, 
                                     from_date: Optional[datetime] = None,
                                     to_date: Optional[datetime] = None,
                                     limit: int = 100) -> List[Dict[str, Any]]:
        """Get account transaction history"""
        if self.sandbox_mode:
            # Mock transaction data
            base_date = datetime.utcnow() - timedelta(days=30)
            transactions = []
            
            mock_transactions = [
                {"amount": -250.00, "description": "ATM Withdrawal", "merchant": "Jordan Bank ATM"},
                {"amount": 1500.00, "description": "Salary Credit", "merchant": "ABC Company"},
                {"amount": -75.50, "description": "Grocery Shopping", "merchant": "Carrefour"},
                {"amount": -120.00, "description": "Fuel Purchase", "merchant": "Total Station"},
                {"amount": 500.00, "description": "Bank Transfer", "merchant": "Family Transfer"},
                {"amount": -45.25, "description": "Restaurant", "merchant": "Fakhr El-Din"},
                {"amount": -200.00, "description": "Online Shopping", "merchant": "Amazon"},
                {"amount": -35.00, "description": "Mobile Recharge", "merchant": "Zain"},
                {"amount": 2000.00, "description": "Investment Return", "merchant": "Jordan Investment"},
                {"amount": -150.00, "description": "Utility Payment", "merchant": "EDCO"}
            ]
            
            for i, tx in enumerate(mock_transactions):
                transaction_date = base_date + timedelta(days=i*3)
                transactions.append({
                    "transaction_id": f"tx_{account_id}_{i+1}",
                    "account_id": account_id,
                    "amount": tx["amount"],
                    "currency": "JOD",
                    "description": tx["description"],
                    "merchant": tx["merchant"],
                    "transaction_date": transaction_date.isoformat(),
                    "value_date": transaction_date.isoformat(),
                    "transaction_type": "debit" if tx["amount"] < 0 else "credit",
                    "category": "general",
                    "status": "completed"
                })
            
            return transactions[:limit]
        
        headers = await self.get_headers()
        params = {"consent_id": user_consent_id, "limit": limit}
        if from_date:
            params["from_date"] = from_date.isoformat()
        if to_date:
            params["to_date"] = to_date.isoformat()
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/ais/v1/accounts/{account_id}/transactions",
                headers=headers,
                params=params
            )
            response.raise_for_status()
            return response.json()["transactions"]
    
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
                f"{self.base_url}/pis/v1/payments",
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
                f"{self.base_url}/pis/v1/payments/{payment_id}",
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
                f"{self.base_url}/fx/v1/rates",
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
                f"{self.base_url}/fx/v1/convert",
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
                f"{self.base_url}/fps/v1/products",
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
                f"{self.base_url}/fps/v1/applications",
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
                f"{self.base_url}/consent/v1/requests",
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
                f"{self.base_url}/consent/v1/status/{consent_id}",
                headers=headers
            )
            response.raise_for_status()
            return response.json()