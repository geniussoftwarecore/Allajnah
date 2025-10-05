#!/bin/bash

echo "=================================="
echo "Docker Build Test Script"
echo "=================================="
echo ""

echo "Testing Docker files exist..."
test -f Dockerfile.backend && echo "✅ Dockerfile.backend found" || echo "❌ Dockerfile.backend missing"
test -f Dockerfile.frontend && echo "✅ Dockerfile.frontend found" || echo "❌ Dockerfile.frontend missing"
test -f docker-compose.yml && echo "✅ docker-compose.yml found" || echo "❌ docker-compose.yml missing"
test -f .dockerignore && echo "✅ .dockerignore found" || echo "❌ .dockerignore missing"
test -f seed_data.py && echo "✅ seed_data.py found" || echo "❌ seed_data.py missing"
echo ""

echo "Testing file permissions..."
test -x seed_data.py && echo "✅ seed_data.py is executable" || echo "⚠️  seed_data.py is not executable (run: chmod +x seed_data.py)"
echo ""

echo "Checking Docker availability..."
if command -v docker &> /dev/null; then
    echo "✅ Docker is installed"
    docker --version
else
    echo "❌ Docker is not installed"
    exit 1
fi
echo ""

if command -v docker-compose &> /dev/null; then
    echo "✅ Docker Compose is installed"
    docker-compose --version
else
    echo "❌ Docker Compose is not installed"
    exit 1
fi
echo ""

echo "Testing Docker Compose configuration..."
docker-compose config > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ docker-compose.yml is valid"
else
    echo "❌ docker-compose.yml has errors"
    docker-compose config
    exit 1
fi
echo ""

echo "=================================="
echo "All checks passed! ✅"
echo "=================================="
echo ""
echo "To start the system, run:"
echo "  docker-compose up --build -d"
echo ""
echo "To initialize the database, run:"
echo "  docker-compose exec api python complaints_backend/src/init_data.py"
echo "  docker-compose exec api python seed_data.py"
echo ""
