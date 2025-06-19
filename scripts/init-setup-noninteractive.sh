#!/bin/bash
# Non-interactive setup script for automated testing
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

echo "🎉 Non-Interactive Medical Patients Generator Setup"
echo "================================================="
echo ""

# Detect OS and version
OS_NAME=""
OS_VERSION=""
IS_UBUNTU_24_04=false

if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS_NAME="$ID"
    OS_VERSION="$VERSION_ID"
    
    if [[ "$ID" == "ubuntu" ]] && [[ "$VERSION_ID" == "24.04" ]]; then
        IS_UBUNTU_24_04=true
        print_warning "Ubuntu 24.04 LTS detected - will use virtual environment for Python packages"
    fi
fi

# Install Task runner if not present
print_step "Checking Task runner..."
if ! command -v task &> /dev/null; then
    print_info "Installing Task using official installer..."
    curl -sL https://taskfile.dev/install.sh | sudo sh -s -- -b /usr/local/bin
    if ! command -v task &> /dev/null; then
        print_error "Task installation failed"
        exit 1
    fi
fi
print_info "Task runner found: $(task --version)"

# Install Docker if not present
print_step "Checking Docker..."
if ! command -v docker &> /dev/null; then
    print_info "Installing Docker..."
    curl -fsSL https://get.docker.com | sudo sh
    sudo usermod -aG docker $USER
    print_warning "Docker installed. Using sudo for this session."
    DOCKER_CMD="sudo docker"
else
    print_info "Docker found"
    # Check if we can run docker without sudo
    if docker ps &> /dev/null; then
        DOCKER_CMD="docker"
    else
        DOCKER_CMD="sudo docker"
        print_warning "Using sudo for Docker commands"
    fi
fi

# Check Docker Compose
if ! $DOCKER_CMD compose version &> /dev/null 2>&1; then
    print_info "Installing Docker Compose plugin..."
    sudo apt-get update -qq
    sudo apt-get install -y -qq docker-compose-plugin
fi

# Check Python
PYTHON=$(which python3 || which python || echo "")
if [ -z "$PYTHON" ]; then
    print_error "Python not found"
    exit 1
fi
print_info "Python found: $($PYTHON --version)"

# Install system dependencies on Ubuntu
if [[ "$OS_NAME" == "ubuntu" ]]; then
    print_step "Installing system dependencies..."
    
    # Update package list
    sudo apt-get update -qq
    
    # Install all required packages
    sudo apt-get install -y -qq \
        python3-venv \
        python3-dev \
        libpq-dev \
        build-essential \
        git \
        curl \
        openssl \
        lsof \
        net-tools
    
    print_info "System dependencies installed"
fi

# Create .env file
print_step "Creating environment configuration..."
if [ ! -f .env ]; then
    API_KEY_VALUE="dev_secret_key_$(openssl rand -hex 16 2>/dev/null || echo 'please_change_me')"
    cat > .env << EOF
# Development Environment Variables
API_KEY=$API_KEY_VALUE
DEBUG=True
CORS_ORIGINS=http://localhost:8000,http://localhost:5174
CACHE_TTL=3600
DATABASE_URL=postgresql://medgen_user:medgen_pass@localhost:5432/medical_patients_db
REDIS_URL=redis://localhost:6379
EOF
    print_info "Created .env file"
fi

# Pull Docker images
print_step "Pulling Docker images..."
$DOCKER_CMD compose pull

# Create Docker network
print_step "Creating Docker network..."
$DOCKER_CMD network create medical-patients_default 2>/dev/null || true

# Start database services
print_step "Starting database services..."
$DOCKER_CMD compose up -d db redis

# Wait for database
print_step "Waiting for database to be ready..."
MAX_ATTEMPTS=30
ATTEMPT=0
while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    if $DOCKER_CMD compose exec -T db pg_isready -U medgen_user &> /dev/null; then
        print_info "Database is ready!"
        break
    fi
    ATTEMPT=$((ATTEMPT + 1))
    echo -n "."
    sleep 1
done
echo ""

if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
    print_error "Database failed to start"
    exit 1
fi

# Setup Python virtual environment
if [ -n "$PYTHON" ]; then
    print_step "Setting up Python virtual environment..."
    
    if [ ! -d ".venv" ]; then
        print_info "Creating virtual environment..."
        $PYTHON -m venv .venv
    fi
    
    # Activate virtual environment
    source .venv/bin/activate
    
    # Upgrade pip
    print_info "Upgrading pip..."
    pip install --upgrade pip setuptools wheel -q
    
    # Install dependencies
    print_info "Installing Python dependencies (this may take a few minutes)..."
    
    # Install critical dependencies first
    pip install --no-cache-dir -q "pydantic>=2.0.0"
    pip install --no-cache-dir -q "alembic>=1.11.1"
    pip install --no-cache-dir -q "psycopg2-binary>=2.9.5"
    pip install --no-cache-dir -q "sqlalchemy>=2.0.0"
    
    # Install all requirements
    if pip install --no-cache-dir -q -r requirements.txt; then
        print_info "All Python dependencies installed successfully"
    else
        print_warning "Some dependencies may have failed"
    fi
fi

# Run migrations
print_step "Running database migrations..."
if alembic upgrade head; then
    print_info "Database migrations completed"
else
    print_error "Migration failed"
    exit 1
fi

# Create activation helper
if [[ "$IS_UBUNTU_24_04" == true ]]; then
    cat > activate.sh << 'EOF'
#!/bin/bash
if [ -f .venv/bin/activate ]; then
    source .venv/bin/activate
    echo "✅ Virtual environment activated"
else
    echo "❌ Virtual environment not found"
fi
EOF
    chmod +x activate.sh
fi

# Test the installation
print_step "Testing installation..."

# Start the app in background
print_info "Starting application..."
nohup python3 -m uvicorn src.main:app --host 0.0.0.0 --port 8000 > app.log 2>&1 &
APP_PID=$!

# Wait for app to start
sleep 5

# Test health endpoint
if curl -s http://localhost:8000/health | grep -q "healthy"; then
    print_info "✅ Application is running successfully!"
    # Kill the test instance
    kill $APP_PID 2>/dev/null || true
else
    print_error "❌ Application failed to start"
    kill $APP_PID 2>/dev/null || true
    exit 1
fi

echo ""
echo "✨ Non-interactive setup complete!"
echo ""
echo "📋 To start using:"
echo "   1. source .venv/bin/activate"
echo "   2. task dev"
echo ""
echo "✅ All components installed and tested successfully!"