from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
from typing import Optional, List
import jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
import enum
from sklearn.ensemble import IsolationForest
import numpy as np
import os

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/smartbank")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Security Configuration
SECRET_KEY = "your-secret-key-change-this-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# Enums
class UserRole(str, enum.Enum):
    CUSTOMER = "customer"
    ADMIN = "admin"
    AUDITOR = "auditor"

class AccountType(str, enum.Enum):
    SAVINGS = "savings"
    CURRENT = "current"
    FD = "fd"

class TransactionType(str, enum.Enum):
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    TRANSFER = "transfer"

class LoanStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

# Database Models
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    full_name = Column(String)
    phone = Column(String)
    address = Column(String)
    role = Column(SQLEnum(UserRole), default=UserRole.CUSTOMER)
    kyc_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    accounts = relationship("Account", back_populates="owner")
    loans = relationship("Loan", back_populates="customer")

class Account(Base):
    __tablename__ = "accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    account_number = Column(String, unique=True, index=True)
    account_type = Column(SQLEnum(AccountType))
    balance = Column(Float, default=0.0)
    daily_limit = Column(Float, default=50000.0)
    daily_used = Column(Float, default=0.0)
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    owner = relationship("User", back_populates="accounts")
    transactions_sent = relationship("Transaction", foreign_keys="Transaction.from_account_id", back_populates="from_account")
    transactions_received = relationship("Transaction", foreign_keys="Transaction.to_account_id", back_populates="to_account")

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    from_account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True)
    to_account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True)
    amount = Column(Float)
    transaction_type = Column(SQLEnum(TransactionType))
    description = Column(String)
    is_flagged = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    from_account = relationship("Account", foreign_keys=[from_account_id], back_populates="transactions_sent")
    to_account = relationship("Account", foreign_keys=[to_account_id], back_populates="transactions_received")

class Loan(Base):
    __tablename__ = "loans"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    loan_type = Column(String)
    amount = Column(Float)
    tenure = Column(Integer)  # in months
    interest_rate = Column(Float, default=8.5)
    emi = Column(Float)
    status = Column(SQLEnum(LoanStatus), default=LoanStatus.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    customer = relationship("User", back_populates="loans")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)
    action = Column(String)
    ip_address = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    details = Column(String)

# Create tables
Base.metadata.create_all(bind=engine)

# Pydantic Models
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    phone: str
    address: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class AccountCreate(BaseModel):
    account_type: AccountType

class TransferRequest(BaseModel):
    from_account_number: str
    to_account_number: str
    amount: float
    description: Optional[str] = ""

class LoanApplication(BaseModel):
    loan_type: str
    amount: float
    tenure: int

class LoanApproval(BaseModel):
    loan_id: int
    approved: bool

# FastAPI App
app = FastAPI(title="SmartBank API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Helper Functions
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    token = credentials.credentials
    payload = decode_token(token)
    user_id = payload.get("user_id")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

def generate_account_number():
    import random
    return f"ACC{random.randint(1000000000, 9999999999)}"

def calculate_emi(principal: float, rate: float, tenure: int) -> float:
    """Calculate EMI using the formula: EMI = (P * r * (1 + r)^n) / ((1 + r)^n - 1)"""
    r = rate / (12 * 100)  # Monthly interest rate
    n = tenure
    emi = (principal * r * pow(1 + r, n)) / (pow(1 + r, n) - 1)
    return round(emi, 2)

def check_fraud(amount: float, account_id: int, db: Session) -> bool:
    """Simple fraud detection using Isolation Forest"""
    # Get recent transactions for this account
    transactions = db.query(Transaction).filter(
        (Transaction.from_account_id == account_id) | (Transaction.to_account_id == account_id)
    ).order_by(Transaction.timestamp.desc()).limit(100).all()
    
    if len(transactions) < 10:
        # Not enough data, flag large transactions
        return amount > 100000
    
    amounts = np.array([[t.amount] for t in transactions])
    
    # Train Isolation Forest
    clf = IsolationForest(contamination=0.1, random_state=42)
    clf.fit(amounts)
    
    # Predict if current transaction is anomaly
    prediction = clf.predict([[amount]])
    
    return prediction[0] == -1  # -1 means anomaly

def log_audit(user_id: int, action: str, ip: str, details: str, db: Session):
    audit = AuditLog(user_id=user_id, action=action, ip_address=ip, details=details)
    db.add(audit)
    db.commit()

# API Endpoints

@app.get("/")
def root():
    return {"message": "SmartBank API - Modular Banking System", "version": "1.0.0"}

# 1. User Registration & KYC
@app.post("/api/register")
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    # Check if user exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    new_user = User(
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        full_name=user_data.full_name,
        phone=user_data.phone,
        address=user_data.address,
        kyc_verified=True  # Simulated KYC
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    log_audit(new_user.id, "USER_REGISTRATION", "0.0.0.0", "New user registered", db)
    
    return {"message": "User registered successfully", "user_id": new_user.id}

@app.post("/api/login")
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == credentials.email).first()
    
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_access_token({"user_id": user.id, "role": user.role.value})
    
    log_audit(user.id, "USER_LOGIN", "0.0.0.0", "User logged in", db)
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role.value
        }
    }

# 2. Account Creation
@app.post("/api/accounts")
def create_account(
    account_data: AccountCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    account_number = generate_account_number()
    
    new_account = Account(
        account_number=account_number,
        account_type=account_data.account_type,
        user_id=current_user.id
    )
    
    db.add(new_account)
    db.commit()
    db.refresh(new_account)
    
    log_audit(current_user.id, "ACCOUNT_CREATION", "0.0.0.0", f"Account {account_number} created", db)
    
    return {
        "message": "Account created successfully",
        "account_number": account_number,
        "account_type": account_data.account_type.value
    }

@app.get("/api/accounts")
def get_accounts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    accounts = db.query(Account).filter(Account.user_id == current_user.id).all()
    
    return {
        "accounts": [
            {
                "id": acc.id,
                "account_number": acc.account_number,
                "account_type": acc.account_type.value,
                "balance": acc.balance,
                "daily_limit": acc.daily_limit,
                "created_at": acc.created_at
            }
            for acc in accounts
        ]
    }

# 3. Money Transfer
@app.post("/api/transfer")
def transfer_money(
    transfer: TransferRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Validate accounts
    from_account = db.query(Account).filter(Account.account_number == transfer.from_account_number).first()
    to_account = db.query(Account).filter(Account.account_number == transfer.to_account_number).first()
    
    if not from_account:
        raise HTTPException(status_code=404, detail="Source account not found")
    
    if not to_account:
        raise HTTPException(status_code=404, detail="Destination account not found")
    
    if from_account.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Unauthorized access to source account")
    
    # Validate balance
    if from_account.balance < transfer.amount:
        raise HTTPException(status_code=400, detail="Insufficient funds")
    
    # Check daily limit
    if from_account.daily_used + transfer.amount > from_account.daily_limit:
        raise HTTPException(status_code=400, detail="Exceeding daily limit")
    
    # Fraud detection
    is_fraudulent = check_fraud(transfer.amount, from_account.id, db)
    
    # Perform transaction
    from_account.balance -= transfer.amount
    to_account.balance += transfer.amount
    from_account.daily_used += transfer.amount
    
    # Log transaction
    transaction = Transaction(
        from_account_id=from_account.id,
        to_account_id=to_account.id,
        amount=transfer.amount,
        transaction_type=TransactionType.TRANSFER,
        description=transfer.description,
        is_flagged=is_fraudulent
    )
    
    db.add(transaction)
    db.commit()
    
    log_audit(current_user.id, "MONEY_TRANSFER", "0.0.0.0", 
              f"Transfer of {transfer.amount} from {transfer.from_account_number} to {transfer.to_account_number}", db)
    
    return {
        "message": "Transfer successful",
        "transaction_id": transaction.id,
        "is_flagged": is_fraudulent,
        "new_balance": from_account.balance
    }

@app.get("/api/transactions")
def get_transactions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Get all accounts of the user
    account_ids = [acc.id for acc in current_user.accounts]
    
    # Get transactions
    transactions = db.query(Transaction).filter(
        (Transaction.from_account_id.in_(account_ids)) | (Transaction.to_account_id.in_(account_ids))
    ).order_by(Transaction.timestamp.desc()).limit(50).all()
    
    return {
        "transactions": [
            {
                "id": t.id,
                "from_account": t.from_account.account_number if t.from_account else None,
                "to_account": t.to_account.account_number if t.to_account else None,
                "amount": t.amount,
                "type": t.transaction_type.value,
                "description": t.description,
                "is_flagged": t.is_flagged,
                "timestamp": t.timestamp
            }
            for t in transactions
        ]
    }

# 4. Loan Application & EMI Calculation
@app.post("/api/loans/apply")
def apply_loan(
    loan_data: LoanApplication,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Calculate EMI
    emi = calculate_emi(loan_data.amount, 8.5, loan_data.tenure)
    
    # Create loan application
    loan = Loan(
        user_id=current_user.id,
        loan_type=loan_data.loan_type,
        amount=loan_data.amount,
        tenure=loan_data.tenure,
        emi=emi
    )
    
    db.add(loan)
    db.commit()
    db.refresh(loan)
    
    log_audit(current_user.id, "LOAN_APPLICATION", "0.0.0.0", 
              f"Loan application for {loan_data.amount}", db)
    
    return {
        "message": "Loan application submitted",
        "loan_id": loan.id,
        "emi": emi,
        "status": loan.status.value
    }

@app.get("/api/loans")
def get_loans(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    loans = db.query(Loan).filter(Loan.user_id == current_user.id).all()
    
    return {
        "loans": [
            {
                "id": loan.id,
                "loan_type": loan.loan_type,
                "amount": loan.amount,
                "tenure": loan.tenure,
                "emi": loan.emi,
                "status": loan.status.value,
                "created_at": loan.created_at
            }
            for loan in loans
        ]
    }

# Admin Endpoints
@app.get("/api/admin/loans")
def get_all_loans(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    loans = db.query(Loan).all()
    
    return {
        "loans": [
            {
                "id": loan.id,
                "customer_name": loan.customer.full_name,
                "loan_type": loan.loan_type,
                "amount": loan.amount,
                "tenure": loan.tenure,
                "emi": loan.emi,
                "status": loan.status.value,
                "created_at": loan.created_at
            }
            for loan in loans
        ]
    }

@app.post("/api/admin/loans/approve")
def approve_loan(
    approval: LoanApproval,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    loan = db.query(Loan).filter(Loan.id == approval.loan_id).first()
    
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")
    
    loan.status = LoanStatus.APPROVED if approval.approved else LoanStatus.REJECTED
    db.commit()
    
    log_audit(current_user.id, "LOAN_APPROVAL", "0.0.0.0", 
              f"Loan {approval.loan_id} {'approved' if approval.approved else 'rejected'}", db)
    
    return {"message": f"Loan {'approved' if approval.approved else 'rejected'} successfully"}

@app.get("/api/admin/flagged-transactions")
def get_flagged_transactions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    flagged = db.query(Transaction).filter(Transaction.is_flagged == True).all()
    
    return {
        "flagged_transactions": [
            {
                "id": t.id,
                "from_account": t.from_account.account_number if t.from_account else None,
                "to_account": t.to_account.account_number if t.to_account else None,
                "amount": t.amount,
                "timestamp": t.timestamp
            }
            for t in flagged
        ]
    }

# Auditor Endpoints
@app.get("/api/audit/logs")
def get_audit_logs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != UserRole.AUDITOR:
        raise HTTPException(status_code=403, detail="Auditor access required")
    
    logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(100).all()
    
    return {
        "audit_logs": [
            {
                "id": log.id,
                "user_id": log.user_id,
                "action": log.action,
                "ip_address": log.ip_address,
                "timestamp": log.timestamp,
                "details": log.details
            }
            for log in logs
        ]
    }

# Dashboard & Reporting
@app.get("/api/dashboard")
def get_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Get account summary
    accounts = db.query(Account).filter(Account.user_id == current_user.id).all()
    total_balance = sum(acc.balance for acc in accounts)
    
    # Get recent transactions
    account_ids = [acc.id for acc in accounts]
    recent_transactions = db.query(Transaction).filter(
        (Transaction.from_account_id.in_(account_ids)) | (Transaction.to_account_id.in_(account_ids))
    ).order_by(Transaction.timestamp.desc()).limit(5).all()
    
    # Get loans
    loans = db.query(Loan).filter(Loan.user_id == current_user.id).all()
    
    return {
        "summary": {
            "total_accounts": len(accounts),
            "total_balance": total_balance,
            "active_loans": len([l for l in loans if l.status == LoanStatus.APPROVED])
        },
        "recent_transactions": [
            {
                "amount": t.amount,
                "type": t.transaction_type.value,
                "timestamp": t.timestamp
            }
            for t in recent_transactions
        ],
        "loan_status": [
            {
                "loan_type": l.loan_type,
                "emi": l.emi,
                "status": l.status.value
            }
            for l in loans
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
