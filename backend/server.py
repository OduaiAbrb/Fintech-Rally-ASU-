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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)