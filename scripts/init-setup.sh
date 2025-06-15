#!/bin/bash
set -e

echo "🎉 Welcome to Medical Patients Generator Setup!"
echo "=============================================="
echo ""

# Check Docker
echo "📋 Checking prerequisites..."
if ! command -v docker &> /dev/null; then
  echo "❌ Docker is not installed!"
  echo "   Please install Docker Desktop from: https://www.docker.com/products/docker-desktop"
  exit 1
fi
echo "✅ Docker found"

# Check if Docker is running
if ! docker info &> /dev/null; then
  echo "❌ Docker is not running!"
  echo "   Please start Docker Desktop and try again."
  exit 1
fi
echo "✅ Docker is running"

# Check Python
PYTHON=$(which python3 || which python || echo "")
if [ -z "$PYTHON" ]; then
  echo "⚠️  Python not found (optional for local development)"
  echo "   Install Python 3.8+ from: https://www.python.org/downloads/"
else
  echo "✅ Python found: $($PYTHON --version)"
fi

# Check Node.js (for timeline viewer)
if ! command -v node &> /dev/null; then
  echo "⚠️  Node.js not found (optional for timeline viewer)"
  echo "   Install Node.js 18+ from: https://nodejs.org/"
else
  echo "✅ Node.js found: $(node --version)"
fi

echo ""
echo "📦 Setting up environment files..."

# Create .env if it doesn't exist
if [ ! -f .env ]; then
  echo "Creating .env file..."
  API_KEY_VALUE="dev_secret_key_$(openssl rand -hex 16 2>/dev/null || echo 'please_change_me')"
  cat > .env << EOF
# Development Environment Variables
API_KEY=$API_KEY_VALUE
DEBUG=True
CORS_ORIGINS=http://localhost:8000,http://localhost:5174
CACHE_TTL=3600
EOF
  echo "✅ Created .env file"
else
  echo "✅ .env file already exists"
fi

# Check if ports are available
echo ""
echo "🔍 Checking port availability..."
for port in 8000 5432 6379; do
  if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1 || netstat -tuln 2>/dev/null | grep -q ":$port "; then
    echo "⚠️  Port $port is already in use"
    echo "   Run 'task stop' if you have services running"
  else
    echo "✅ Port $port is available"
  fi
done

echo ""
echo "🐳 Pulling Docker images..."
docker compose pull

echo ""
echo "🏗️  Creating Docker network and volumes..."
docker network create medical-patients_default 2>/dev/null || true

echo ""
echo "🚀 Starting database services..."
docker compose up -d db redis

echo ""
echo "⏳ Waiting for database to be ready..."
for i in {1..30}; do
  if docker compose exec -T db pg_isready -U medgen_user &> /dev/null; then
    echo "✅ Database is ready!"
    break
  fi
  echo -n "."
  sleep 1
done
echo ""

echo "📊 Running database migrations..."
docker compose run --rm app alembic upgrade head

# Install Python dependencies if running locally
if [ -n "$PYTHON" ] && [ ! -d ".venv" ]; then
  echo ""
  echo "🐍 Setting up Python virtual environment..."
  read -p "Create Python virtual environment? (y/N) " -n 1 -r
  echo
  if [[ $REPLY =~ ^[Yy]$ ]]; then
    $PYTHON -m venv .venv
    echo "✅ Created .venv"
    echo "   Activate with: source .venv/bin/activate"
    echo "   Then run: pip install -r requirements.txt"
  fi
fi

# Timeline viewer setup
if command -v node &> /dev/null && [ -d "patient-timeline-viewer" ]; then
  echo ""
  echo "📊 Setting up Timeline Viewer..."
  read -p "Install Timeline Viewer dependencies? (y/N) " -n 1 -r
  echo
  if [[ $REPLY =~ ^[Yy]$ ]]; then
    cd patient-timeline-viewer && npm install && cd ..
    echo "✅ Timeline Viewer ready!"
  fi
fi

echo ""
echo "✨ Setup complete! Here's what to do next:"
echo "   1. Run 'task dev' to start the development server"
echo "   2. Open http://localhost:8000 in your browser"
echo "   3. Check API docs at http://localhost:8000/docs"
echo ""
echo "Happy coding! 🎉"