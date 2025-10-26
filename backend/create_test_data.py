#!/usr/bin/env python3
"""
SmartBank - Test Data Generator
Creates sample users, accounts, and transactions for demo purposes
"""

from main import (
    SessionLocal, User, Account, Transaction, Loan,
    hash_password, UserRole, AccountType, TransactionType, LoanStatus,
    generate_account_number, calculate_emi
)
from datetime import datetime, timedelta
import random

def create_test_data():
    db = SessionLocal()
    
    print("🏦 SmartBank - Creating Test Data")
    print("=" * 50)
    
    try:
        # Create Admin User
        admin = db.query(User).filter(User.email == 'admin@smartbank.com').first()
        if not admin:
            admin = User(
                email='admin@smartbank.com',
                password_hash=hash_password('admin123'),
                full_name='System Admin',
                phone='1234567890',
                address='Admin Office',
                role=UserRole.ADMIN,
                kyc_verified=True
            )
            db.add(admin)
            print("✅ Admin user created")
        else:
            print("ℹ️  Admin user already exists")
        
        # Create Auditor User
        auditor = db.query(User).filter(User.email == 'auditor@smartbank.com').first()
        if not auditor:
            auditor = User(
                email='auditor@smartbank.com',
                password_hash=hash_password('auditor123'),
                full_name='System Auditor',
                phone='1234567891',
                address='Audit Office',
                role=UserRole.AUDITOR,
                kyc_verified=True
            )
            db.add(auditor)
            print("✅ Auditor user created")
        else:
            print("ℹ️  Auditor user already exists")
        
        # Create Sample Customers
        customers = []
        customer_data = [
            ('john@example.com', 'John Doe', '9876543210', 'Mumbai, Maharashtra'),
            ('jane@example.com', 'Jane Smith', '9876543211', 'Delhi, India'),
            ('bob@example.com', 'Bob Wilson', '9876543212', 'Bangalore, Karnataka'),
        ]
        
        for email, name, phone, address in customer_data:
            customer = db.query(User).filter(User.email == email).first()
            if not customer:
                customer = User(
                    email=email,
                    password_hash=hash_password('password123'),
                    full_name=name,
                    phone=phone,
                    address=address,
                    role=UserRole.CUSTOMER,
                    kyc_verified=True
                )
                db.add(customer)
                customers.append(customer)
                print(f"✅ Customer created: {name}")
            else:
                customers.append(customer)
                print(f"ℹ️  Customer already exists: {name}")
        
        db.commit()
        
        # Create Accounts for Customers
        print("\n📊 Creating Accounts...")
        for customer in customers:
            # Check if customer already has accounts
            existing_accounts = db.query(Account).filter(Account.user_id == customer.id).count()
            
            if existing_accounts == 0:
                # Savings Account
                savings = Account(
                    account_number=generate_account_number(),
                    account_type=AccountType.SAVINGS,
                    balance=random.uniform(10000, 100000),
                    user_id=customer.id
                )
                db.add(savings)
                
                # Current Account
                current = Account(
                    account_number=generate_account_number(),
                    account_type=AccountType.CURRENT,
                    balance=random.uniform(50000, 200000),
                    user_id=customer.id
                )
                db.add(current)
                
                print(f"✅ Accounts created for {customer.full_name}")
            else:
                print(f"ℹ️  Accounts already exist for {customer.full_name}")
        
        db.commit()
        
        # Create Sample Transactions
        print("\n💸 Creating Transactions...")
        accounts = db.query(Account).all()
        
        if len(accounts) >= 2:
            for i in range(5):
                from_acc = random.choice(accounts)
                to_acc = random.choice([a for a in accounts if a.id != from_acc.id])
                amount = random.uniform(100, 5000)
                
                transaction = Transaction(
                    from_account_id=from_acc.id,
                    to_account_id=to_acc.id,
                    amount=amount,
                    transaction_type=TransactionType.TRANSFER,
                    description=f"Transfer #{i+1}",
                    timestamp=datetime.utcnow() - timedelta(days=random.randint(1, 30))
                )
                db.add(transaction)
            
            print("✅ Sample transactions created")
        
        db.commit()
        
        # Create Sample Loan Applications
        print("\n💰 Creating Loan Applications...")
        loan_types = ['personal', 'home', 'car', 'education']
        
        for customer in customers[:2]:  # Only first 2 customers
            existing_loans = db.query(Loan).filter(Loan.user_id == customer.id).count()
            
            if existing_loans == 0:
                amount = random.choice([500000, 1000000, 2000000])
                tenure = random.choice([12, 24, 36, 60])
                
                loan = Loan(
                    user_id=customer.id,
                    loan_type=random.choice(loan_types),
                    amount=amount,
                    tenure=tenure,
                    emi=calculate_emi(amount, 8.5, tenure),
                    status=random.choice([LoanStatus.PENDING, LoanStatus.APPROVED])
                )
                db.add(loan)
                print(f"✅ Loan application created for {customer.full_name}")
            else:
                print(f"ℹ️  Loan already exists for {customer.full_name}")
        
        db.commit()
        
        print("\n" + "=" * 50)
        print("✅ Test data creation completed!")
        print("\n📝 Login Credentials:")
        print("   Admin: admin@smartbank.com / admin123")
        print("   Auditor: auditor@smartbank.com / auditor123")
        print("   Customer 1: john@example.com / password123")
        print("   Customer 2: jane@example.com / password123")
        print("   Customer 3: bob@example.com / password123")
        
    except Exception as e:
        print(f"\n❌ Error creating test data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_test_data()
