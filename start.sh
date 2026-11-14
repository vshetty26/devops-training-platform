#!/bin/bash

# DevOps Arena Startup Script
# This script helps you start all components of DevOps Arena

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 DevOps Arena Startup${NC}"
echo "=================================="
echo ""

# Check Docker
echo -e "${YELLOW}Checking Docker...${NC}"
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed!${NC}"
    echo "Please install Docker Desktop from: https://www.docker.com/products/docker-desktop/"
    exit 1
fi

if ! docker ps &> /dev/null; then
    echo -e "${RED}❌ Docker is not running!${NC}"
    echo "Please start Docker Desktop and try again."
    exit 1
fi

echo -e "${GREEN}✅ Docker is running${NC}"
echo ""

# Check if challenge image exists
echo -e "${YELLOW}Checking challenge Docker image...${NC}"
if ! docker images | grep -q "devops-arena-nginx-502"; then
    echo -e "${YELLOW}⚠️  Challenge image not found. Building...${NC}"
    cd challenges/nginx-502
    docker build -t devops-arena-nginx-502:latest .
    cd ../..
    echo -e "${GREEN}✅ Challenge image built${NC}"
else
    echo -e "${GREEN}✅ Challenge image found${NC}"
fi
echo ""

# Initialize database
echo -e "${YELLOW}Initializing database...${NC}"
cd backend
if [ ! -f "devops_arena.db" ]; then
    source venv/bin/activate
    python -c "from app.database import Base, engine; Base.metadata.create_all(engine)" 2>/dev/null || true
    
    # Create demo user
    python -c "
from app.database import SessionLocal
from app.services.auth_service import create_user
db = SessionLocal()
try:
    create_user(db, 'demo', 'demo123')
    print('Created demo user: demo / demo123')
except:
    pass
finally:
    db.close()
" 2>/dev/null || true
    
    deactivate
    echo -e "${GREEN}✅ Database initialized${NC}"
else
    echo -e "${GREEN}✅ Database exists${NC}"
fi
cd ..
echo ""

# Check frontend dependencies
echo -e "${YELLOW}Checking frontend dependencies...${NC}"
cd frontend
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}Installing frontend dependencies...${NC}"
    npm install
fi
cd ..
echo -e "${GREEN}✅ Frontend ready${NC}"
echo ""

# Instructions
echo -e "${GREEN}=================================="
echo "✅ All checks passed!"
echo "==================================${NC}"
echo ""
echo "To start DevOps Arena, open 3 terminal windows:"
echo ""
echo -e "${YELLOW}Terminal 1 - Backend:${NC}"
echo "  cd $(pwd)/backend"
echo "  source venv/bin/activate"
echo "  uvicorn app.main:app --reload"
echo ""
echo -e "${YELLOW}Terminal 2 - Frontend:${NC}"
echo "  cd $(pwd)/frontend"
echo "  npm run dev"
echo ""
echo -e "${YELLOW}Terminal 3 - Open Browser:${NC}"
echo "  http://localhost:5173"
echo "  Login: demo / demo123"
echo ""
echo -e "${GREEN}Or use the helper scripts:${NC}"
echo "  ./start-backend.sh  (in Terminal 1)"
echo "  ./start-frontend.sh (in Terminal 2)"
echo ""
echo "See QUICKSTART.md for detailed instructions."
