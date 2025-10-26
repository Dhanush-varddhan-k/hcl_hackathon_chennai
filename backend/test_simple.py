"""
SmartBank - Simple Working Tests
Only Account Management and Money Transfer
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import app, get_db, Base, Account
from main import hash_password

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_smartbank.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# Create tables
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

client = TestClient(app)


class TestAccountManagement:
    """Test Account Management"""
    
    def test_1_register_user(self):
        """Test user registration"""
        response = client.post("/api/register", json={
            "email": "testuser@example.com",
            "password": "password123",
            "full_name": "Test User",
            "phone": "9876543210",
            "address": "Test Address"
        })
        assert response.status_code == 200
        print("✓ User registration works")
    
    def test_2_login_user(self):
        """Test user login"""
        response = client.post("/api/login", json={
            "email": "testuser@example.com",
            "password": "password123"
        })
        assert response.status_code == 200
        assert "access_token" in response.json()
        print("✓ User login works")
    
    def test_3_create_savings_account(self):
        """Test creating savings account"""
        # Login first
        login_response = client.post("/api/login", json={
            "email": "testuser@example.com",
            "password": "password123"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create account
        response = client.post("/api/accounts",
            headers=headers,
            json={"account_type": "savings"}
        )
        assert response.status_code == 200
        assert "account_number" in response.json()
        print(f"✓ Created savings account: {response.json()['account_number']}")
    
    def test_4_create_current_account(self):
        """Test creating current account"""
        # Login
        login_response = client.post("/api/login", json={
            "email": "testuser@example.com",
            "password": "password123"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create account
        response = client.post("/api/accounts",
            headers=headers,
            json={"account_type": "current"}
        )
        assert response.status_code == 200
        assert "account_number" in response.json()
        print(f"✓ Created current account: {response.json()['account_number']}")
    
    def test_5_get_all_accounts(self):
        """Test getting user accounts"""
        # Login
        login_response = client.post("/api/login", json={
            "email": "testuser@example.com",
            "password": "password123"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get accounts
        response = client.get("/api/accounts", headers=headers)
        assert response.status_code == 200
        assert "accounts" in response.json()
        assert len(response.json()["accounts"]) >= 2
        print(f"✓ Found {len(response.json()['accounts'])} accounts")


class TestMoneyTransfer:
    """Test Money Transfer"""
    
    @classmethod
    def setup_class(cls):
        """Setup before all tests"""
        # Register new user for transfer tests
        client.post("/api/register", json={
            "email": "transferuser@example.com",
            "password": "password123",
            "full_name": "Transfer User",
            "phone": "1234567890",
            "address": "Test Address"
        })
        
        # Login and create two accounts
        login_response = client.post("/api/login", json={
            "email": "transferuser@example.com",
            "password": "password123"
        })
        cls.token = login_response.json()["access_token"]
        cls.headers = {"Authorization": f"Bearer {cls.token}"}
        
        # Create first account
        acc1_response = client.post("/api/accounts",
            headers=cls.headers,
            json={"account_type": "savings"}
        )
        cls.account1 = acc1_response.json()["account_number"]
        
        # Create second account
        acc2_response = client.post("/api/accounts",
            headers=cls.headers,
            json={"account_type": "current"}
        )
        cls.account2 = acc2_response.json()["account_number"]
        
        # Add balance to first account
        db = TestingSessionLocal()
        account = db.query(Account).filter(Account.account_number == cls.account1).first()
        account.balance = 50000.0
        db.commit()
        db.close()
        
        print(f"\n✓ Setup complete:")
        print(f"  Account 1: {cls.account1} (Balance: ₹50,000)")
        print(f"  Account 2: {cls.account2} (Balance: ₹0)")
    
    def test_1_successful_transfer(self):
        """Test successful money transfer"""
        response = client.post("/api/transfer",
            headers=self.headers,
            json={
                "from_account_number": self.account1,
                "to_account_number": self.account2,
                "amount": 5000.0,
                "description": "Test transfer"
            }
        )
        assert response.status_code == 200
        assert "transaction_id" in response.json()
        print(f"✓ Transfer successful: ₹5,000")
        print(f"  New balance: ₹{response.json()['new_balance']}")
    
    def test_2_insufficient_funds(self):
        """Test transfer with insufficient funds"""
        response = client.post("/api/transfer",
            headers=self.headers,
            json={
                "from_account_number": self.account1,
                "to_account_number": self.account2,
                "amount": 100000.0,
                "description": "Large transfer"
            }
        )
        assert response.status_code == 400
        assert "Insufficient" in response.json()["detail"]
        print("✓ Insufficient funds detected correctly")
    
    
    
    def test_4_view_transactions(self):
        """Test viewing transaction history"""
        response = client.get("/api/transactions", headers=self.headers)
        assert response.status_code == 200
        assert "transactions" in response.json()
        print(f"✓ Found {len(response.json()['transactions'])} transactions")
    
    def test_5_nonexistent_account(self):
        """Test transfer to non-existent account"""
        response = client.post("/api/transfer",
            headers=self.headers,
            json={
                "from_account_number": self.account1,
                "to_account_number": "ACC9999999999",
                "amount": 100.0,
                "description": "Test"
            }
        )
        assert response.status_code == 404
        print("✓ Non-existent account detected correctly")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("SmartBank - Account Management & Money Transfer Tests")
    print("="*60 + "\n")
    
    pytest.main([__file__, "-v", "-s"])
