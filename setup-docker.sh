#!/bin/bash

echo "🐳 DevOps Arena - Docker Setup Helper"
echo "======================================"
echo ""

# Check if Docker Desktop is installed
if [ ! -d "/Applications/Docker.app" ]; then
    echo "❌ Docker Desktop not found!"
    echo "📥 Please install Docker Desktop from: https://www.docker.com/products/docker-desktop/"
    exit 1
fi

echo "✅ Docker Desktop found"
echo ""

# Add Docker to PATH
echo "📝 Adding Docker to PATH..."
export PATH="/Applications/Docker.app/Contents/Resources/bin:$PATH"

# Check if docker command works
if command -v docker &> /dev/null; then
    echo "✅ Docker CLI is available"
    docker --version
else
    echo "⚠️  Docker CLI not in PATH yet"
    echo ""
    echo "To fix this permanently, run:"
    echo "  echo 'export PATH=\"/Applications/Docker.app/Contents/Resources/bin:\$PATH\"' >> ~/.zshrc"
    echo "  source ~/.zshrc"
fi

echo ""

# Check if Docker daemon is running
echo "🔍 Checking Docker daemon..."
if docker ps &> /dev/null; then
    echo "✅ Docker daemon is running"
    echo ""
    docker ps
else
    echo "⚠️  Docker daemon not running"
    echo ""
    echo "To start Docker:"
    echo "  1. Open Docker Desktop from Applications"
    echo "  2. Wait for the whale icon to stop animating in menu bar"
    echo "  3. Run this script again"
    exit 1
fi

echo ""
echo "✅ Docker setup complete!"
echo ""
echo "Next steps:"
echo "  1. Run: ./start-backend.sh"
echo "  2. Run: ./start-frontend.sh (in new terminal)"
echo "  3. Open: http://localhost:5173"
echo "  4. Login: demo / demo123"
