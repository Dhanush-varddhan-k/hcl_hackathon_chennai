#!/bin/bash

echo "🏦 SmartBank - Modular Banking System Setup"
echo "==========================================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✅ Docker and Docker Compose are installed"
echo ""

# Stop any existing containers
echo "🛑 Stopping existing containers..."
docker-compose down

# Build and start containers
echo "🚀 Building and starting containers..."
docker-compose up -d --build

echo ""
echo "⏳ Waiting for services to start..."
sleep 10

# Create admin user
echo "👤 Creating admin user..."
docker-compose exec -T backend python -c "
from main import SessionLocal, User, hash_password, UserRole
db = SessionLocal()
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
    db.commit()
    print('✅ Admin user created')
else:
    print('ℹ️  Admin user already exists')
db.close()
" 2>/dev/null || echo "Note: Admin user will be created on first backend start"

echo ""
echo "✅ SmartBank Setup Complete!"
echo ""
echo "📝 Access Information:"
echo "   Frontend: http://localhost:3000"
echo "   Backend API: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo "   pgAdmin: http://localhost:5050"
echo ""
echo "🔑 Default Credentials:"
echo "   Admin Login: admin@smartbank.com / admin123"
echo "   pgAdmin: admin@smartbank.com / admin"
echo ""
echo "📊 Database Connection (for pgAdmin):"
echo "   Host: postgres"
echo "   Port: 5432"
echo "   Database: smartbank"
echo "   Username: postgres"
echo "   Password: postgres"
echo ""
echo "🎉 You're all set! Open http://localhost:3000 to start!"
