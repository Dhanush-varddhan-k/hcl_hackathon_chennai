#!/bin/bash

echo "🧪 SmartBank - Running Unit Tests"
echo "=================================="
echo ""

# Check if we're in the right directory
if [ ! -f "test_main.py" ]; then
    echo "❌ Error: test_main.py not found"
    echo "   Please run this from the backend directory"
    exit 1
fi

# Install test dependencies
echo "📦 Installing test dependencies..."
pip install -q pytest pytest-cov httpx

echo ""
echo "🚀 Running all tests..."
echo ""

# Run tests with coverage
pytest test_main.py -v --cov=main --cov-report=term-missing --cov-report=html

echo ""
echo "=================================="
echo "📊 Test Summary"
echo "=================================="
echo ""
echo "✅ Tests completed!"
echo ""
echo "Coverage report: htmlcov/index.html"
echo "Open with: open htmlcov/index.html"
echo ""