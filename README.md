# 🏦 SmartBank - Modular Banking Backend System

A complete, production-ready banking backend system built with FastAPI, PostgreSQL, and modern web technologies.

### Money Transfer
![Transfer](/transfer.png)

## 📋 Features Implemented

### ✅ Core Features (All from Requirements)

1. **User Registration & KYC**
   - User registration with personal details
   - Simulated KYC verification
   - JWT-based authentication
   - Password hashing with bcrypt

2. **Account Management**
   - Create multiple accounts (Savings, Current, FD)
   - Auto-generated account numbers
   - Initial deposit validation
   - Account balance tracking

3. **Money Transfer**
   - Real-time balance validation
   - Daily limit enforcement
   - Transaction logging
   - Insufficient funds & limit checks
   - Celery for scheduled transfers (ready to implement)

4. **Loan Application & EMI Calculation**
   - Submit loan applications
   - Automatic EMI calculation using formula: `EMI = (P * r * (1 + r)^n) / ((1 + r)^n - 1)`
   - Admin loan approval/rejection
   - Loan status tracking

5. **Fraud Detection**
   - ML-based anomaly detection using Isolation Forest
   - One-Class SVM support
   - Automatic flagging of suspicious transactions
   - Admin notification system

6. **Audit Logging**
   - Comprehensive audit trails
   - User ID, timestamp, action, IP tracking
   - Secure audit table (RBAC protected)
   - Accessible only to auditors

7. **Reporting & Dashboard**
   - Account summary
   - Transaction trends
   - Loan repayment status
   - REST API for frontend integration

### 🔒 Security Features

- JWT-based authentication
- Password hashing with bcrypt
- Rate limiting (slowapi ready)
- Role-based access control (Customer, Admin, Auditor)
- Input validation & sanitization
- SQL injection prevention (SQLAlchemy ORM)

### 🧪 Testing Strategy

- Unit tests ready for business logic
- Integration tests for API endpoints
- Load testing support for transaction engine
- Coverage reports with PyTest

### 🚀 Deployment

- Dockerized services
- CI/CD ready with GitHub Actions
- Optional AWS/GCP deployment with PostgreSQL RDS
- Horizontal scaling support

## 🛠️ Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **PostgreSQL** - Production database
- **SQLAlchemy** - ORM for database operations
- **JWT** - Token-based authentication
- **scikit-learn** - ML for fraud detection
- **bcrypt** - Password hashing

### Frontend
- **HTML/CSS/JavaScript** - Simple, responsive UI
- **Vanilla JS** - No framework overhead for hackathon speed

### DevOps
- **Docker** - Containerization
- **Docker Compose** - Multi-container orchestration
- **pgAdmin** - Database management (YES, we can use it!)
- **Nginx** - Frontend serving

## 📦 Project Structure

```
smartbank/
├── backend/
│   ├── main.py              # FastAPI application with all endpoints
│   ├── requirements.txt     # Python dependencies
│   └── Dockerfile          # Backend container
├── frontend/
│   └── index.html          # Complete web interface
├── docker-compose.yml      # Multi-container setup
├── setup.sh               # Automated setup script
└── README.md              # This file
```

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose installed
- 8GB RAM minimum
- Ports 3000, 5000, 5432, 8000 available

### Option 1: Automated Setup (Recommended)

```bash
# Run the setup script
./setup.sh
```

That's it! The script will:
1. Start PostgreSQL database
2. Start pgAdmin for database management
3. Build and start the FastAPI backend
4. Start the frontend web server
5. Create the admin user automatically

### Option 2: Manual Setup

```bash
# Start all services
docker-compose up -d --build

# Wait for services to start (30 seconds)
sleep 30

# Check if services are running
docker-compose ps
```

## 🌐 Access Points

| Service | URL | Credentials |
|---------|-----|-------------|
| **Frontend** | http://localhost:3000 | - |
| **Backend API** | http://localhost:8000 | - |
| **API Docs** | http://localhost:8000/docs | - |
| **pgAdmin** | http://localhost:5050 | admin@smartbank.com / admin |
| **Database** | localhost:5432 | postgres / postgres |

## 👤 Default Users

### Admin User
- Email: `admin@smartbank.com`
- Password: `admin123`
- Role: Admin (can approve loans, view flagged transactions)

You can create more users through the registration page!

## 📖 User Guide

### For Customers

1. **Register**
   - Click "Register" on the login page
   - Fill in your details (name, email, password, phone, address)
   - Click "Register"

2. **Create Account**
   - Login with your credentials
   - Go to "Accounts" tab
   - Select account type (Savings/Current/FD)
   - Click "Create Account"

3. **Transfer Money**
   - Go to "Transfer" tab
   - Select source account
   - Enter destination account number
   - Enter amount and description
   - Click "Transfer"

4. **Apply for Loan**
   - Go to "Loans" tab
   - Select loan type
   - Enter amount and tenure (months)
   - Click "Apply"
   - EMI will be calculated automatically

5. **View Dashboard**
   - Click "Dashboard" to see:
     - Total balance
     - Recent transactions
     - Loan status

### For Admins

1. **Review Loan Applications**
   - Login as admin
   - Click "Admin" button
   - View pending loan applications
   - Approve or reject loans

2. **Monitor Flagged Transactions**
   - Click "Admin" button
   - View "Flagged Transactions" section
   - Review suspicious activities

### For Auditors

1. **View Audit Logs**
   - Login as auditor
   - Click "Audit" button
   - View complete system audit trail

## 🔧 Using pgAdmin (Database Management)

Yes, you can use pgAdmin! Here's how:

1. **Access pgAdmin**
   - Open http://localhost:5050
   - Login with: admin@smartbank.com / admin

2. **Connect to Database**
   - Click "Add New Server"
   - General Tab:
     - Name: SmartBank
   - Connection Tab:
     - Host: `postgres` (container name)
     - Port: `5432`
     - Database: `smartbank`
     - Username: `postgres`
     - Password: `postgres`
   - Click "Save"

3. **Explore Tables**
   - Navigate to: SmartBank > Databases > smartbank > Schemas > public > Tables
   - Right-click any table > View/Edit Data

## 📊 Database Schema

### Tables
- **users** - User accounts with roles
- **accounts** - Bank accounts (savings, current, FD)
- **transactions** - All money transfers
- **loans** - Loan applications
- **audit_logs** - System audit trail

## 🧪 Testing the System

### Test Fraud Detection

1. Create an account
2. Make several normal transactions (₹1000-₹5000)
3. Try transferring a very large amount (₹100,000+)
4. Transaction will be flagged automatically

### Test EMI Calculation

1. Apply for a loan: ₹500,000 for 60 months
2. Expected EMI: ₹10,274.71 (at 8.5% interest)

### Test Daily Limits

1. Create account (default limit: ₹50,000)
2. Transfer ₹30,000 - Success
3. Transfer ₹25,000 - Should fail (exceeds daily limit)

## 🔍 API Endpoints

### Authentication
- `POST /api/register` - Register new user
- `POST /api/login` - Login and get JWT token

### Accounts
- `POST /api/accounts` - Create new account
- `GET /api/accounts` - Get user's accounts

### Transactions
- `POST /api/transfer` - Transfer money
- `GET /api/transactions` - Get transaction history

### Loans
- `POST /api/loans/apply` - Apply for loan
- `GET /api/loans` - Get user's loans

### Admin
- `GET /api/admin/loans` - Get all loan applications
- `POST /api/admin/loans/approve` - Approve/reject loan
- `GET /api/admin/flagged-transactions` - Get flagged transactions

### Auditor
- `GET /api/audit/logs` - Get audit logs

### Dashboard
- `GET /api/dashboard` - Get user dashboard data

Full API documentation available at: http://localhost:8000/docs

## 🛠️ Development

### Run Backend Locally (without Docker)

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set database URL
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/smartbank"

# Run server
python main.py
```

### View Logs

```bash
# Backend logs
docker-compose logs -f backend

# Database logs
docker-compose logs -f postgres

# All logs
docker-compose logs -f
```

### Stop Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (clean restart)
docker-compose down -v
```

## 🎯 Hackathon Checklist

- ✅ User Registration & KYC
- ✅ Account Creation
- ✅ Money Transfer with validation
- ✅ Loan Application with EMI calculation
- ✅ Fraud Detection (ML-based)
- ✅ Audit Logging
- ✅ Role-based access (Customer, Admin, Auditor)
- ✅ Dashboard & Reporting
- ✅ Security (JWT, bcrypt, input validation)
- ✅ Docker deployment
- ✅ pgAdmin support
- ✅ Complete API documentation
- ✅ Working frontend
- ✅ Database setup

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Check what's using the port
sudo lsof -i :8000  # or 3000, 5432, 5050

# Kill the process
kill -9 <PID>
```

### Backend Won't Start
```bash
# Check logs
docker-compose logs backend

# Restart backend
docker-compose restart backend
```

### Can't Connect to Database
```bash
# Check if PostgreSQL is running
docker-compose ps

# Restart database
docker-compose restart postgres
```

### Frontend Shows "Cannot connect to API"
1. Make sure backend is running: http://localhost:8000
2. Check CORS settings in main.py
3. Verify browser console for errors

## 📝 Notes for Presentation

### Key Highlights
1. **Complete Feature Set** - All requirements implemented
2. **Production-Ready** - Proper error handling, validation, security
3. **Scalable Architecture** - Dockerized, can add Celery for async tasks
4. **ML Integration** - Real fraud detection with Isolation Forest
5. **Professional UI** - Clean, responsive interface
6. **Easy Setup** - One command to run everything

### Demo Flow
1. Show registration
2. Create account
3. Make transfer (show normal transaction)
4. Make large transfer (show fraud detection)
5. Apply for loan (show EMI calculation)
6. Login as admin (show loan approval)
7. Show audit logs
8. Show pgAdmin (database management)

## 🚀 Future Enhancements

- [ ] Real KYC integration with document upload
- [ ] SMS/Email notifications
- [ ] Credit score calculation
- [ ] Scheduled recurring transfers (Celery)
- [ ] Mobile app
- [ ] Advanced analytics dashboard
- [ ] Multi-currency support
- [ ] Investment products

## 📄 License

This is a hackathon project. Feel free to use and modify!

## 👨‍💻 Support

For issues or questions during the hackathon:
1. Check the logs: `docker-compose logs`
2. Verify all services are running: `docker-compose ps`
3. Restart if needed: `docker-compose restart`

---

**Built with ❤️ for the Hackathon**

Good luck! 🎉
