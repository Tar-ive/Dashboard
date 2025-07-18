#!/bin/bash

# OrbStack Setup Script for NSF Researcher Matching API
# This script sets up the complete containerized environment for testing

set -e

echo "🚀 Setting up NSF Researcher Matching API with OrbStack..."

# Check if OrbStack/Docker is available
if ! command -v docker &> /dev/null; then
    echo "❌ OrbStack/Docker is not available. Please install OrbStack first."
    echo "   Download from: https://orbstack.dev/"
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not available. OrbStack should include this."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.docker .env
    echo "⚠️  Please edit .env file and add your API keys:"
    echo "   - ANTHROPIC_API_KEY"
    echo "   - GROQ_API_KEY"
    echo ""
    read -p "Press Enter to continue after updating .env file..."
fi

# Create necessary directories
echo "📁 Creating data directories..."
mkdir -p data/uploads data/models data/outputs

# Build and start services
echo "🔨 Building Docker images..."
docker-compose build

echo "🚀 Starting services..."
docker-compose up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check service health
echo "🏥 Checking service health..."
if docker-compose ps | grep -q "Up (healthy)"; then
    echo "✅ Services are healthy!"
else
    echo "⚠️  Services may still be starting up. Check with: docker-compose ps"
fi

# Display service URLs
echo ""
echo "🎉 Setup complete! Services are running with OrbStack:"
echo "   📡 API Server: http://localhost:8000"
echo "   📊 API Docs: http://localhost:8000/docs"
echo "   🔍 Health Check: http://localhost:8000/health"
echo "   🗄️  Redis: localhost:6379"
echo ""
echo "🧪 To start Redis Commander for debugging:"
echo "   docker-compose --profile debug up -d redis-commander"
echo "   Then visit: http://localhost:8081"
echo ""
echo "📋 Useful OrbStack commands:"
echo "   docker-compose ps              # Check service status"
echo "   docker-compose logs api        # View API logs"
echo "   docker-compose logs redis      # View Redis logs"
echo "   docker-compose down            # Stop all services"
echo "   docker-compose down -v         # Stop and remove volumes"
echo "   orb                           # Open OrbStack dashboard"
echo ""
echo "🔧 Test the API with the Postman collection in ./postman/"
echo "💡 OrbStack provides better performance and resource usage than Docker Desktop!"