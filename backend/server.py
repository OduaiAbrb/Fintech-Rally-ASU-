from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
import os
from dotenv import load_dotenv
import uuid
from bson import ObjectId
import logging
from services.jordan_open_finance import JordanOpenFinanceService
from services.hey_dinar_ai import HeyDinarAI

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="Stablecoin Fintech Platform", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security configuration
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))

# MongoDB configuration
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017/stablecoin_db")
client = AsyncIOMotorClient(MONGO_URL)
database = client.get_database("stablecoin_db")

# Database collections
users_collection = database.get_collection("users")
wallets_collection = database.get_collection("wallets")
transactions_collection = database.get_collection("transactions")
accounts_collection = database.get_collection("accounts")
linked_accounts_collection = database.get_collection("linked_accounts")
consents_collection = database.get_collection("consents")
payments_collection = database.get_collection("payments")

# Initialize Jordan Open Finance service
jof_service = JordanOpenFinanceService()

# Pydantic models
class UserRegistration(BaseModel):
    email: str
    password: str
    full_name: str
    phone_number: Optional[str] = None

class UserLogin(BaseModel):
    email: str
    password: str

class UserProfile(BaseModel):
    id: str
    email: str
    full_name: str
    phone_number: Optional[str] = None
    created_at: datetime
    is_active: bool = True

class WalletBalance(BaseModel):
    id: str
    user_id: str
    jd_balance: float = 0.0
    stablecoin_balance: float = 0.0
    created_at: datetime
    updated_at: datetime

class Transaction(BaseModel):
    id: str
    user_id: str
    transaction_type: str  # 'deposit', 'withdrawal', 'transfer', 'exchange'
    amount: float
    currency: str  # 'JD' or 'STABLECOIN'
    status: str  # 'pending', 'completed', 'failed'
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class TransactionCreate(BaseModel):
    transaction_type: str
    amount: float
    currency: str
    description: Optional[str] = None

class ExchangeRequest(BaseModel):
    from_currency: str  # 'JD' or 'STABLECOIN'
    to_currency: str    # 'JD' or 'STABLECOIN'
    amount: float

class ConsentRequest(BaseModel):
    permissions: List[str]

class PaymentInitiation(BaseModel):
    recipient_account: str
    amount: float
    currency: str = "JOD"
    reference: Optional[str] = None
    description: Optional[str] = None

class LinkedAccount(BaseModel):
    account_id: str
    account_name: str
    account_number: str
    bank_name: str
    bank_code: str
    account_type: str
    currency: str
    balance: float
    available_balance: float
    status: str
    last_updated: datetime

# Utility functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = await users_collection.find_one({"_id": user_id})
    if user is None:
        raise credentials_exception
    return user

# API Routes
@app.get("/")
async def root():
    return {"message": "Stablecoin Fintech Platform API", "version": "1.0.0"}

@app.post("/api/auth/register")
async def register_user(user_data: UserRegistration):
    # Check if user already exists
    existing_user = await users_collection.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    user_id = str(uuid.uuid4())
    hashed_password = get_password_hash(user_data.password)
    
    user_doc = {
        "_id": user_id,
        "email": user_data.email,
        "full_name": user_data.full_name,
        "phone_number": user_data.phone_number,
        "hashed_password": hashed_password,
        "created_at": datetime.utcnow(),
        "is_active": True
    }
    
    await users_collection.insert_one(user_doc)
    
    # Create wallet for new user
    wallet_id = str(uuid.uuid4())
    wallet_doc = {
        "_id": wallet_id,
        "user_id": user_id,
        "jd_balance": 0.0,
        "stablecoin_balance": 0.0,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    await wallets_collection.insert_one(wallet_doc)
    
    # Create access token
    access_token = create_access_token(data={"sub": user_id})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user_id,
            "email": user_data.email,
            "full_name": user_data.full_name,
            "phone_number": user_data.phone_number
        }
    }

@app.post("/api/auth/login")
async def login_user(user_credentials: UserLogin):
    user = await users_collection.find_one({"email": user_credentials.email})
    
    if not user or not verify_password(user_credentials.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled"
        )
    
    access_token = create_access_token(data={"sub": user["_id"]})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user["_id"],
            "email": user["email"],
            "full_name": user["full_name"],
            "phone_number": user.get("phone_number")
        }
    }

@app.get("/api/auth/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    return {
        "id": current_user["_id"],
        "email": current_user["email"],
        "full_name": current_user["full_name"],
        "phone_number": current_user.get("phone_number"),
        "created_at": current_user["created_at"],
        "is_active": current_user["is_active"]
    }

@app.get("/api/wallet")
async def get_wallet_balance(current_user: dict = Depends(get_current_user)):
    wallet = await wallets_collection.find_one({"user_id": current_user["_id"]})
    
    if not wallet:
        # Create wallet if it doesn't exist
        wallet_id = str(uuid.uuid4())
        wallet_doc = {
            "_id": wallet_id,
            "user_id": current_user["_id"],
            "jd_balance": 0.0,
            "stablecoin_balance": 0.0,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        await wallets_collection.insert_one(wallet_doc)
        wallet = wallet_doc
    
    return {
        "id": wallet["_id"],
        "user_id": wallet["user_id"],
        "jd_balance": wallet["jd_balance"],
        "stablecoin_balance": wallet["stablecoin_balance"],
        "created_at": wallet["created_at"],
        "updated_at": wallet["updated_at"]
    }

@app.post("/api/wallet/exchange")
async def exchange_currency(
    exchange_request: ExchangeRequest,
    current_user: dict = Depends(get_current_user)
):
    wallet = await wallets_collection.find_one({"user_id": current_user["_id"]})
    
    if not wallet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wallet not found"
        )
    
    # Simple 1:1 exchange rate for MVP
    exchange_rate = 1.0
    
    # Validate exchange request
    if exchange_request.from_currency == exchange_request.to_currency:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot exchange same currency"
        )
    
    # Check sufficient balance
    if exchange_request.from_currency == "JD":
        if wallet["jd_balance"] < exchange_request.amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient JD balance"
            )
    else:
        if wallet["stablecoin_balance"] < exchange_request.amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient stablecoin balance"
            )
    
    # Perform exchange
    if exchange_request.from_currency == "JD":
        new_jd_balance = wallet["jd_balance"] - exchange_request.amount
        new_stablecoin_balance = wallet["stablecoin_balance"] + (exchange_request.amount * exchange_rate)
    else:
        new_jd_balance = wallet["jd_balance"] + (exchange_request.amount * exchange_rate)
        new_stablecoin_balance = wallet["stablecoin_balance"] - exchange_request.amount
    
    # Update wallet
    await wallets_collection.update_one(
        {"user_id": current_user["_id"]},
        {
            "$set": {
                "jd_balance": new_jd_balance,
                "stablecoin_balance": new_stablecoin_balance,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    # Create transaction record
    transaction_id = str(uuid.uuid4())
    transaction_doc = {
        "_id": transaction_id,
        "user_id": current_user["_id"],
        "transaction_type": "exchange",
        "amount": exchange_request.amount,
        "currency": exchange_request.from_currency,
        "to_currency": exchange_request.to_currency,
        "exchange_rate": exchange_rate,
        "status": "completed",
        "description": f"Exchange {exchange_request.amount} {exchange_request.from_currency} to {exchange_request.to_currency}",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    await transactions_collection.insert_one(transaction_doc)
    
    return {
        "message": "Exchange completed successfully",
        "transaction_id": transaction_id,
        "new_jd_balance": new_jd_balance,
        "new_stablecoin_balance": new_stablecoin_balance
    }

@app.get("/api/transactions")
async def get_transactions(
    limit: int = 10,
    offset: int = 0,
    current_user: dict = Depends(get_current_user)
):
    cursor = transactions_collection.find({"user_id": current_user["_id"]})
    cursor = cursor.sort("created_at", -1).skip(offset).limit(limit)
    
    transactions = []
    async for transaction in cursor:
        transactions.append({
            "id": transaction["_id"],
            "user_id": transaction["user_id"],
            "transaction_type": transaction["transaction_type"],
            "amount": transaction["amount"],
            "currency": transaction["currency"],
            "status": transaction["status"],
            "description": transaction.get("description"),
            "created_at": transaction["created_at"],
            "updated_at": transaction["updated_at"]
        })
    
    return {
        "transactions": transactions,
        "total": len(transactions),
        "limit": limit,
        "offset": offset
    }

@app.post("/api/wallet/deposit")
async def deposit_funds(
    transaction_request: TransactionCreate,
    current_user: dict = Depends(get_current_user)
):
    wallet = await wallets_collection.find_one({"user_id": current_user["_id"]})
    
    if not wallet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wallet not found"
        )
    
    # Update wallet balance
    if transaction_request.currency == "JD":
        new_balance = wallet["jd_balance"] + transaction_request.amount
        await wallets_collection.update_one(
            {"user_id": current_user["_id"]},
            {
                "$set": {
                    "jd_balance": new_balance,
                    "updated_at": datetime.utcnow()
                }
            }
        )
    else:
        new_balance = wallet["stablecoin_balance"] + transaction_request.amount
        await wallets_collection.update_one(
            {"user_id": current_user["_id"]},
            {
                "$set": {
                    "stablecoin_balance": new_balance,
                    "updated_at": datetime.utcnow()
                }
            }
        )
    
    # Create transaction record
    transaction_id = str(uuid.uuid4())
    transaction_doc = {
        "_id": transaction_id,
        "user_id": current_user["_id"],
        "transaction_type": "deposit",
        "amount": transaction_request.amount,
        "currency": transaction_request.currency,
        "status": "completed",
        "description": transaction_request.description or f"Deposit {transaction_request.amount} {transaction_request.currency}",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    await transactions_collection.insert_one(transaction_doc)
    
    return {
        "message": "Deposit completed successfully",
        "transaction_id": transaction_id,
        "new_balance": new_balance
    }

# Open Banking API Endpoints

@app.post("/api/open-banking/consent")
async def request_banking_consent(
    consent_request: ConsentRequest,
    current_user: dict = Depends(get_current_user)
):
    """Request user consent for accessing banking data"""
    try:
        consent_response = await jof_service.request_user_consent(
            user_id=current_user["_id"],
            permissions=consent_request.permissions
        )
        
        # Store consent in database
        consent_doc = {
            "_id": consent_response["consent_id"],
            "user_id": current_user["_id"],
            "permissions": consent_response["permissions"],
            "status": consent_response["status"],
            "expires_at": datetime.fromisoformat(consent_response["expires_at"].replace("Z", "+00:00")),
            "created_at": datetime.utcnow()
        }
        
        await consents_collection.insert_one(consent_doc)
        
        return consent_response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error requesting consent: {str(e)}"
        )

@app.get("/api/open-banking/accounts")
async def get_linked_accounts(current_user: dict = Depends(get_current_user)):
    """Get user's linked bank accounts"""
    try:
        # Get user's consent
        consent = await consents_collection.find_one({"user_id": current_user["_id"]})
        if not consent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No banking consent found. Please link your bank accounts first."
            )
        
        # Get accounts from Jordan Open Finance
        accounts = await jof_service.get_user_accounts(consent["_id"])
        
        # Store/update accounts in database
        for account in accounts:
            account_doc = {
                "_id": account["account_id"],
                "user_id": current_user["_id"],
                "consent_id": consent["_id"],
                "account_name": account["account_name"],
                "account_number": account["account_number"],
                "bank_name": account["bank_name"],
                "bank_code": account["bank_code"],
                "account_type": account["account_type"],
                "currency": account["currency"],
                "balance": account["balance"],
                "available_balance": account["available_balance"],
                "status": account["status"],
                "last_updated": datetime.utcnow()
            }
            
            await linked_accounts_collection.update_one(
                {"_id": account["account_id"]},
                {"$set": account_doc},
                upsert=True
            )
        
        return {
            "accounts": accounts,
            "total": len(accounts)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching accounts: {str(e)}"
        )

@app.get("/api/open-banking/accounts/{account_id}/balance")
async def get_account_balance(
    account_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get specific account balance"""
    try:
        # Get user's consent
        consent = await consents_collection.find_one({"user_id": current_user["_id"]})
        if not consent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No banking consent found"
            )
        
        # Verify account belongs to user
        linked_account = await linked_accounts_collection.find_one({
            "_id": account_id,
            "user_id": current_user["_id"]
        })
        if not linked_account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found or not linked to your profile"
            )
        
        balance = await jof_service.get_account_balance(account_id, consent["_id"])
        
        # Update stored balance
        await linked_accounts_collection.update_one(
            {"_id": account_id},
            {
                "$set": {
                    "balance": balance["balance"],
                    "available_balance": balance["available_balance"],
                    "last_updated": datetime.utcnow()
                }
            }
        )
        
        return balance
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching balance: {str(e)}"
        )

@app.get("/api/open-banking/accounts/{account_id}/transactions")
async def get_account_transactions(
    account_id: str,
    limit: int = 50,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get account transaction history"""
    try:
        # Get user's consent
        consent = await consents_collection.find_one({"user_id": current_user["_id"]})
        if not consent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No banking consent found"
            )
        
        # Verify account belongs to user
        linked_account = await linked_accounts_collection.find_one({
            "_id": account_id,
            "user_id": current_user["_id"]
        })
        if not linked_account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found or not linked to your profile"
            )
        
        # Parse dates if provided
        from_datetime = None
        to_datetime = None
        if from_date:
            from_datetime = datetime.fromisoformat(from_date)
        if to_date:
            to_datetime = datetime.fromisoformat(to_date)
        
        transactions = await jof_service.get_account_transactions(
            account_id, consent["_id"], from_datetime, to_datetime, limit
        )
        
        return {
            "transactions": transactions,
            "total": len(transactions),
            "account_id": account_id,
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching transactions: {str(e)}"
        )

@app.post("/api/open-banking/payments")
async def initiate_payment(
    payment_request: PaymentInitiation,
    current_user: dict = Depends(get_current_user)
):
    """Initiate payment using PIS"""
    try:
        # Prepare payment data
        payment_data = {
            "amount": payment_request.amount,
            "currency": payment_request.currency,
            "recipient": payment_request.recipient_account,
            "reference": payment_request.reference,
            "description": payment_request.description,
            "user_id": current_user["_id"]
        }
        
        # Initiate payment through Jordan Open Finance
        payment_response = await jof_service.initiate_payment(payment_data)
        
        # Store payment record
        payment_doc = {
            "_id": payment_response["payment_id"],
            "user_id": current_user["_id"],
            "amount": payment_request.amount,
            "currency": payment_request.currency,
            "recipient": payment_request.recipient_account,
            "reference": payment_request.reference,
            "description": payment_request.description,
            "status": payment_response["status"],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        await payments_collection.insert_one(payment_doc)
        
        return payment_response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error initiating payment: {str(e)}"
        )

@app.get("/api/open-banking/payments/{payment_id}")
async def get_payment_status(
    payment_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get payment status"""
    try:
        # Verify payment belongs to user
        payment = await payments_collection.find_one({
            "_id": payment_id,
            "user_id": current_user["_id"]
        })
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found"
            )
        
        # Get status from Jordan Open Finance
        status_response = await jof_service.get_payment_status(payment_id)
        
        # Update payment status
        await payments_collection.update_one(
            {"_id": payment_id},
            {
                "$set": {
                    "status": status_response["status"],
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        return status_response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching payment status: {str(e)}"
        )

@app.get("/api/open-banking/fx/rates")
async def get_exchange_rates(
    base_currency: str = "JOD",
    current_user: dict = Depends(get_current_user)
):
    """Get current exchange rates"""
    try:
        rates = await jof_service.get_exchange_rates(base_currency)
        return rates
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching exchange rates: {str(e)}"
        )

@app.post("/api/open-banking/fx/convert")
async def convert_currency_amount(
    from_currency: str,
    to_currency: str,
    amount: float,
    current_user: dict = Depends(get_current_user)
):
    """Convert currency amount"""
    try:
        conversion = await jof_service.convert_currency(from_currency, to_currency, amount)
        return conversion
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error converting currency: {str(e)}"
        )

@app.get("/api/open-banking/products")
async def get_financial_products(current_user: dict = Depends(get_current_user)):
    """Get available financial products"""
    try:
        products = await jof_service.get_financial_products(current_user["_id"])
        return {
            "products": products,
            "total": len(products)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching financial products: {str(e)}"
        )

@app.get("/api/open-banking/dashboard")
async def get_open_banking_dashboard(current_user: dict = Depends(get_current_user)):
    """Get aggregated dashboard data from all linked accounts"""
    try:
        # Get user's consent
        consent = await consents_collection.find_one({"user_id": current_user["_id"]})
        if not consent:
            return {
                "message": "No banking consent found",
                "has_linked_accounts": False,
                "total_balance": 0.0,
                "accounts": [],
                "recent_transactions": []
            }
        
        # Get all linked accounts
        accounts_cursor = linked_accounts_collection.find({"user_id": current_user["_id"]})
        accounts = []
        total_balance = 0.0
        
        async for account in accounts_cursor:
            account_data = {
                "account_id": account["_id"],
                "account_name": account["account_name"],
                "bank_name": account["bank_name"],
                "balance": account["balance"],
                "available_balance": account["available_balance"],
                "currency": account["currency"],
                "account_type": account["account_type"],
                "last_updated": account["last_updated"]
            }
            accounts.append(account_data)
            total_balance += account["balance"]
        
        # Get recent transactions from all accounts
        recent_transactions = []
        for account in accounts[:3]:  # Get transactions from first 3 accounts
            try:
                transactions = await jof_service.get_account_transactions(
                    account["account_id"], consent["_id"], limit=5
                )
                for tx in transactions:
                    tx["account_name"] = account["account_name"]
                    tx["bank_name"] = account["bank_name"]
                recent_transactions.extend(transactions)
            except:
                continue
        
        # Sort transactions by date
        recent_transactions.sort(key=lambda x: x["transaction_date"], reverse=True)
        recent_transactions = recent_transactions[:10]  # Top 10 recent transactions
        
        return {
            "has_linked_accounts": len(accounts) > 0,
            "total_balance": total_balance,
            "accounts": accounts,
            "recent_transactions": recent_transactions,
            "total_accounts": len(accounts)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching dashboard data: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)