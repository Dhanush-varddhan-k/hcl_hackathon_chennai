# 🏗️ SmartBank - System Architecture

## 📊 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         SMARTBANK SYSTEM                         │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────┐
│   Frontend      │  Port 3000
│  (HTML/JS/CSS)  │  - User Interface
│                 │  - Dashboard
└────────┬────────┘  - Forms
         │
         │ HTTP/REST
         │
┌────────▼────────┐
│   FastAPI       │  Port 8000
│   Backend       │  - Authentication
│                 │  - Business Logic
│   ┌─────────┐   │  - API Endpoints
│   │ JWT Auth│   │  - Validation
│   └─────────┘   │
│   ┌─────────┐   │
│   │  RBAC   │   │
│   └─────────┘   │
└────────┬────────┘
         │
         │ SQLAlchemy ORM
         │
┌────────▼────────┐
│  PostgreSQL     │  Port 5432
│   Database      │  - User data
│                 │  - Accounts
│   Tables:       │  - Transactions
│   - users       │  - Loans
│   - accounts    │  - Audit logs
│   - transactions│
│   - loans       │
│   - audit_logs  │
└────────┬────────┘
         │
         │
┌────────▼────────┐
│    pgAdmin      │  Port 5050
│  DB Management  │  - Visual admin
│                 │  - Query tool
└─────────────────┘

┌─────────────────┐
│  ML Component   │
│  Fraud Detection│
│                 │
│  - Isolation    │
│    Forest       │
│  - One-Class    │
│    SVM          │
└─────────────────┘
```

## 🔄 Request Flow

### 1. User Registration Flow
```
User → Frontend → POST /api/register → Backend
                                         ├─ Validate input
                                         ├─ Hash password (bcrypt)
                                         ├─ Create user record
                                         ├─ Store in DB
                                         └─ Log audit event
                                         → Response → Frontend
```

### 2. Authentication Flow
```
User → Frontend → POST /api/login → Backend
                                      ├─ Validate credentials
                                      ├─ Verify password hash
                                      ├─ Generate JWT token
                                      └─ Log audit event
                                      → JWT Token → Frontend
                                      
All future requests include: Authorization: Bearer {JWT}
```

### 3. Money Transfer Flow
```
User → Frontend → POST /api/transfer → Backend (JWT validated)
                                         ├─ Verify account ownership
                                         ├─ Check balance
                                         ├─ Check daily limit
                                         ├─ Fraud detection (ML)
                                         ├─ Update balances
                                         ├─ Log transaction
                                         └─ Log audit event
                                         → Response → Frontend
```

### 4. Loan Application Flow
```
User → Frontend → POST /api/loans/apply → Backend (JWT validated)
                                            ├─ Validate input
                                            ├─ Calculate EMI
                                            ├─ Create loan record
                                            └─ Log audit event
                                            → Loan details → Frontend

Admin → Frontend → POST /api/admin/loans/approve → Backend
                                                     ├─ Verify admin role
                                                     ├─ Update loan status
                                                     └─ Log audit event
                                                     → Response → Frontend
```

## 🗄️ Database Schema

### Users Table
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR UNIQUE NOT NULL,
    password_hash VARCHAR NOT NULL,
    full_name VARCHAR NOT NULL,
    phone VARCHAR NOT NULL,
    address VARCHAR NOT NULL,
    role VARCHAR NOT NULL,  -- customer, admin, auditor
    kyc_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Accounts Table
```sql
CREATE TABLE accounts (
    id SERIAL PRIMARY KEY,
    account_number VARCHAR UNIQUE NOT NULL,
    account_type VARCHAR NOT NULL,  -- savings, current, fd
    balance DECIMAL(15,2) DEFAULT 0.00,
    daily_limit DECIMAL(15,2) DEFAULT 50000.00,
    daily_used DECIMAL(15,2) DEFAULT 0.00,
    user_id INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Transactions Table
```sql
CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    from_account_id INTEGER REFERENCES accounts(id),
    to_account_id INTEGER REFERENCES accounts(id),
    amount DECIMAL(15,2) NOT NULL,
    transaction_type VARCHAR NOT NULL,  -- deposit, withdrawal, transfer
    description VARCHAR,
    is_flagged BOOLEAN DEFAULT FALSE,
    timestamp TIMESTAMP DEFAULT NOW()
);
```

### Loans Table
```sql
CREATE TABLE loans (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    loan_type VARCHAR NOT NULL,
    amount DECIMAL(15,2) NOT NULL,
    tenure INTEGER NOT NULL,
    interest_rate DECIMAL(5,2) DEFAULT 8.5,
    emi DECIMAL(15,2) NOT NULL,
    status VARCHAR NOT NULL,  -- pending, approved, rejected
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Audit Logs Table
```sql
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    action VARCHAR NOT NULL,
    ip_address VARCHAR NOT NULL,
    timestamp TIMESTAMP DEFAULT NOW(),
    details VARCHAR
);
```

## 🔐 Security Architecture

### Authentication Layer
```
┌─────────────────────────────────────┐
│         Client Request              │
└──────────────┬──────────────────────┘
               │
               │ Authorization: Bearer {JWT}
               │
┌──────────────▼──────────────────────┐
│      JWT Token Validation           │
│  - Verify signature                 │
│  - Check expiration                 │
│  - Extract user_id & role           │
└──────────────┬──────────────────────┘
               │
               │ Valid token
               │
┌──────────────▼──────────────────────┐
│    Role-Based Access Control        │
│  - Check user role                  │
│  - Verify endpoint permissions      │
└──────────────┬──────────────────────┘
               │
               │ Authorized
               │
┌──────────────▼──────────────────────┐
│      Business Logic Layer           │
└─────────────────────────────────────┘
```

### Data Protection
- **Passwords**: bcrypt hashing (irreversible)
- **Tokens**: JWT with expiration
- **Database**: ORM prevents SQL injection
- **Input**: Pydantic validation
- **Audit**: All actions logged

## 🤖 ML Fraud Detection

### Algorithm: Isolation Forest
```
┌─────────────────────────────────────┐
│    Transaction Initiated            │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│   Get Historical Transactions       │
│   (Last 100 from account)           │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│   Train Isolation Forest Model      │
│   - Contamination: 0.1              │
│   - Features: Transaction amount    │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│   Predict Current Transaction       │
│   - Normal: prediction = 1          │
│   - Anomaly: prediction = -1        │
└──────────────┬──────────────────────┘
               │
               ├─ Normal → Process
               │
               └─ Anomaly → Flag & Process
```

### Why Isolation Forest?
- Detects outliers without labeled data
- Works well with small datasets
- Fast training and prediction
- No assumptions about data distribution

## 🚀 Deployment Architecture

### Docker Compose Setup
```
┌─────────────────────────────────────────────────────────┐
│                    Docker Host                          │
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │   Frontend   │  │   Backend    │  │  PostgreSQL  │ │
│  │  Container   │  │  Container   │  │  Container   │ │
│  │  Port: 3000  │  │  Port: 8000  │  │  Port: 5432  │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│                                                         │
│  ┌──────────────┐                                      │
│  │   pgAdmin    │                                      │
│  │  Container   │                                      │
│  │  Port: 5050  │                                      │
│  └──────────────┘                                      │
│                                                         │
│  Network: smartbank_network                            │
│  Volume: postgres_data (persistent)                    │
└─────────────────────────────────────────────────────────┘
```

### Production Scaling (Future)
```
┌─────────────────────────────────────────────┐
│              Load Balancer                  │
└───────┬─────────────┬───────────────────────┘
        │             │
   ┌────▼────┐   ┌────▼────┐
   │ Backend │   │ Backend │   (Multiple instances)
   │   #1    │   │   #2    │
   └────┬────┘   └────┬────┘
        │             │
        └──────┬──────┘
               │
        ┌──────▼──────┐
        │ PostgreSQL  │
        │   (RDS)     │   (Managed service)
        └─────────────┘
```

## 📊 API Architecture

### RESTful Endpoints
```
BASE URL: http://localhost:8000/api

Authentication:
├── POST /register          (Public)
└── POST /login             (Public)

Customer Operations:
├── POST /accounts          (JWT required)
├── GET  /accounts          (JWT required)
├── POST /transfer          (JWT required)
├── GET  /transactions      (JWT required)
├── POST /loans/apply       (JWT required)
├── GET  /loans             (JWT required)
└── GET  /dashboard         (JWT required)

Admin Operations:
├── GET  /admin/loans                    (Admin role)
├── POST /admin/loans/approve            (Admin role)
└── GET  /admin/flagged-transactions     (Admin role)

Auditor Operations:
└── GET  /audit/logs                     (Auditor role)
```

### Request/Response Flow
```
Client Request
    ├── Headers: Authorization: Bearer {JWT}
    ├── Body: JSON payload
    └── Method: GET/POST/PUT/DELETE
         │
         ▼
    FastAPI Router
         ├── Validate JWT
         ├── Check RBAC
         ├── Validate input (Pydantic)
         └── Call business logic
              │
              ▼
    Business Logic Layer
         ├── Process request
         ├── Database operations
         ├── ML predictions (if needed)
         └── Audit logging
              │
              ▼
    Response
         ├── Status: 200, 400, 401, 403, 500
         ├── Body: JSON response
         └── Headers: Content-Type: application/json
```

## 🔄 Data Flow Diagram

### Complete Transaction Flow
```
┌─────────┐
│  User   │
└────┬────┘
     │ 1. Initiates transfer
     ▼
┌─────────────┐
│  Frontend   │
└──────┬──────┘
       │ 2. POST /api/transfer + JWT
       ▼
┌─────────────────┐
│  JWT Validation │
└──────┬──────────┘
       │ 3. Valid user
       ▼
┌─────────────────┐
│  Authorization  │
└──────┬──────────┘
       │ 4. Check ownership
       ▼
┌─────────────────┐
│   Validation    │
│  - Balance      │ ──→ Insufficient? → Error
│  - Daily limit  │ ──→ Exceeded? → Error
└──────┬──────────┘
       │ 5. Valid
       ▼
┌─────────────────┐
│ Fraud Detection │
│  (ML Model)     │
└──────┬──────────┘
       │ 6. Prediction
       ├─ Normal
       └─ Anomaly → Flag transaction
       │
       ▼
┌─────────────────┐
│  DB Transaction │
│  - Deduct from  │
│  - Add to       │
│  - Log txn      │
└──────┬──────────┘
       │ 7. Committed
       ▼
┌─────────────────┐
│  Audit Log      │
└──────┬──────────┘
       │ 8. Response
       ▼
┌─────────────┐
│  Frontend   │
└──────┬──────┘
       │ 9. Show result
       ▼
┌─────────┐
│  User   │
└─────────┘
```

## 🎯 System Capabilities

### Functional Requirements
✅ User management (register, login, KYC)
✅ Account management (create, view, types)
✅ Transaction processing (transfer, deposit, withdrawal)
✅ Loan management (apply, approve, EMI calculation)
✅ Fraud detection (ML-based, real-time)
✅ Audit logging (comprehensive, secure)
✅ Dashboard (summary, trends, insights)

### Non-Functional Requirements
✅ Security (JWT, bcrypt, RBAC, input validation)
✅ Performance (async operations, connection pooling)
✅ Scalability (containerized, horizontal scaling ready)
✅ Reliability (transaction integrity, error handling)
✅ Maintainability (clean code, documentation)
✅ Usability (intuitive UI, API documentation)

## 📈 Performance Considerations

### Database Optimization
- Indexes on frequently queried columns
- Foreign key constraints for integrity
- Connection pooling (SQLAlchemy)
- Query optimization with ORM

### API Performance
- Async operations with FastAPI
- Response caching (can be added)
- Database query optimization
- Pagination for large datasets

### Security Performance
- JWT token caching
- Password hash verification (bcrypt)
- Rate limiting (SlowAPI ready)

## 🔧 Maintenance & Monitoring

### Logging
- Application logs (FastAPI)
- Database logs (PostgreSQL)
- Container logs (Docker)
- Audit logs (Custom table)

### Monitoring Points
- API response times
- Database connection pool
- Transaction success rate
- Fraud detection accuracy
- System resource usage

### Backup Strategy
- Database backups (PostgreSQL dumps)
- Volume backups (Docker volumes)
- Code repository (Git)
- Configuration files

---

**This architecture is production-ready and scalable!** 🚀
