#!/bin/bash
set -e

# Simple init script - just the essentials

echo "🎉 Medical Patients Generator - Quick Setup"
echo "=========================================="
echo ""

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is required but not installed"
    echo "   Please install Docker Desktop from: https://www.docker.com"
    exit 1
fi

if ! docker info &> /dev/null; then
    echo "❌ Docker is installed but not running"
    echo "   Please start Docker Desktop and try again"
    exit 1
fi

echo "✅ Docker is ready"

# Create .env if missing
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cat > .env << EOF
# Development Environment Variables
API_KEY=dev_secret_key_$(openssl rand -hex 16 2>/dev/null || echo 'please_change_me')
DEBUG=True
CORS_ORIGINS=http://localhost:8000,http://localhost:5174
DATABASE_URL=postgresql://medgen_user:medgen_pass@localhost:5432/medical_patients_db
REDIS_URL=redis://localhost:6379
EOF
    echo "✅ Created .env file"
else
    echo "✅ Using existing .env file"
fi

# Start database
echo ""
echo "🚀 Starting database services..."
docker compose pull db redis
docker compose up -d db redis

# Wait for database
echo "⏳ Waiting for database..."
for i in {1..30}; do
    if docker compose exec -T db pg_isready -U medgen_user &> /dev/null; then
        break
    fi
    sleep 1
done

# Run migrations
echo "📊 Setting up database..."
docker compose run --rm app alembic upgrade head 2>/dev/null || echo "⚠️  Migration failed - run manually later"

echo ""
echo "✅ Setup complete!"
echo ""
echo "🎯 Next steps:"
echo "   1. Run: task dev"
echo "   2. Open: http://localhost:8000"
echo ""
echo "📚 Documentation: http://localhost:8000/docs"
echo "🎨 Timeline Viewer (optional): task timeline"
echo ""