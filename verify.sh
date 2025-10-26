#!/bin/bash

echo "🏦 SmartBank - System Verification"
echo "===================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check functions
check_docker() {
    if command -v docker &> /dev/null; then
        echo -e "${GREEN}✓${NC} Docker installed"
        return 0
    else
        echo -e "${RED}✗${NC} Docker not installed"
        return 1
    fi
}

check_docker_compose() {
    if command -v docker-compose &> /dev/null; then
        echo -e "${GREEN}✓${NC} Docker Compose installed"
        return 0
    else
        echo -e "${RED}✗${NC} Docker Compose not installed"
        return 1
    fi
}

check_port() {
    local port=$1
    local service=$2
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${YELLOW}!${NC} Port $port ($service) is in use"
        return 1
    else
        echo -e "${GREEN}✓${NC} Port $port ($service) is available"
        return 0
    fi
}

check_container() {
    local container=$1
    if docker ps --format '{{.Names}}' | grep -q "^$container$"; then
        echo -e "${GREEN}✓${NC} Container $container is running"
        return 0
    else
        echo -e "${RED}✗${NC} Container $container is not running"
        return 1
    fi
}

check_service() {
    local url=$1
    local service=$2
    if curl -s -o /dev/null -w "%{http_code}" $url | grep -q "200\|302"; then
        echo -e "${GREEN}✓${NC} $service is accessible"
        return 0
    else
        echo -e "${RED}✗${NC} $service is not accessible"
        return 1
    fi
}

# Main verification
echo "1. Checking Prerequisites..."
echo "----------------------------"
check_docker
docker_ok=$?
check_docker_compose
compose_ok=$?

if [ $docker_ok -ne 0 ] || [ $compose_ok -ne 0 ]; then
    echo ""
    echo -e "${RED}ERROR: Docker and/or Docker Compose not installed${NC}"
    echo "Please install them first:"
    echo "  Docker: https://docs.docker.com/get-docker/"
    echo "  Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

echo ""
echo "2. Checking Port Availability..."
echo "--------------------------------"
check_port 3000 "Frontend"
check_port 5000 "Alt Frontend"
check_port 5432 "PostgreSQL"
check_port 5050 "pgAdmin"
check_port 8000 "Backend API"

echo ""
echo "3. Checking Docker Containers..."
echo "--------------------------------"
if docker ps >/dev/null 2>&1; then
    check_container "smartbank_frontend"
    frontend_ok=$?
    check_container "smartbank_backend"
    backend_ok=$?
    check_container "smartbank_db"
    db_ok=$?
    check_container "smartbank_pgadmin"
    pgadmin_ok=$?
    
    if [ $frontend_ok -ne 0 ] || [ $backend_ok -ne 0 ] || [ $db_ok -ne 0 ]; then
        echo ""
        echo -e "${YELLOW}Some containers are not running. Run './quick-start.sh' to start them.${NC}"
    fi
else
    echo -e "${YELLOW}Docker daemon is not running${NC}"
fi

echo ""
echo "4. Checking Service Accessibility..."
echo "------------------------------------"
if docker ps >/dev/null 2>&1; then
    sleep 2
    check_service "http://localhost:3000" "Frontend"
    check_service "http://localhost:8000" "Backend API"
    check_service "http://localhost:5050" "pgAdmin"
    check_service "http://localhost:8000/docs" "API Documentation"
else
    echo -e "${YELLOW}Skipping (Docker not running)${NC}"
fi

echo ""
echo "5. Checking Database Connection..."
echo "----------------------------------"
if docker ps --format '{{.Names}}' | grep -q "smartbank_db"; then
    if docker exec smartbank_db pg_isready -U postgres >/dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} PostgreSQL is ready"
        
        # Check if tables exist
        tables=$(docker exec smartbank_db psql -U postgres -d smartbank -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';" 2>/dev/null | tr -d ' ')
        if [ "$tables" -gt 0 ]; then
            echo -e "${GREEN}✓${NC} Database tables created ($tables tables)"
        else
            echo -e "${YELLOW}!${NC} Database tables not created yet"
        fi
    else
        echo -e "${RED}✗${NC} PostgreSQL is not ready"
    fi
else
    echo -e "${YELLOW}!${NC} PostgreSQL container not running"
fi

echo ""
echo "6. System Summary"
echo "=================="

all_ok=true

if [ $docker_ok -eq 0 ] && [ $compose_ok -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Prerequisites: OK"
else
    echo -e "${RED}✗${NC} Prerequisites: FAILED"
    all_ok=false
fi

if docker ps --format '{{.Names}}' | grep -q "smartbank"; then
    running=$(docker ps --filter "name=smartbank" --format "{{.Names}}" | wc -l)
    echo -e "${GREEN}✓${NC} Containers: $running/4 running"
    if [ $running -lt 4 ]; then
        all_ok=false
    fi
else
    echo -e "${RED}✗${NC} Containers: None running"
    all_ok=false
fi

echo ""
if [ "$all_ok" = true ]; then
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}✓ System is ready!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo "Access your application:"
    echo "  Frontend: http://localhost:3000"
    echo "  Backend API: http://localhost:8000"
    echo "  API Docs: http://localhost:8000/docs"
    echo "  pgAdmin: http://localhost:5050"
    echo ""
    echo "Default credentials:"
    echo "  Admin: admin@smartbank.com / admin123"
    echo "  Customer: john@example.com / password123"
    echo "  pgAdmin: admin@smartbank.com / admin"
    echo ""
else
    echo -e "${YELLOW}========================================${NC}"
    echo -e "${YELLOW}! System needs setup${NC}"
    echo -e "${YELLOW}========================================${NC}"
    echo ""
    echo "Run the following command to set up:"
    echo "  ./quick-start.sh"
    echo ""
    echo "Or manually:"
    echo "  docker-compose up -d --build"
    echo ""
fi

echo "For detailed logs, run:"
echo "  docker-compose logs -f"
echo ""
