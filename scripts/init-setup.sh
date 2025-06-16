#!/bin/bash
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

echo "🎉 Welcome to Medical Patients Generator Setup!"
echo "=============================================="
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

# Check Docker
print_step "Checking prerequisites..."
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed!"
    
    if [[ "$IS_UBUNTU_24_04" == true ]] || [[ "$OS_NAME" == "ubuntu" ]]; then
        echo "   Install Docker with:"
        echo "   curl -fsSL https://get.docker.com | sudo sh"
        echo "   sudo usermod -aG docker $USER"
    else
        echo "   Please install Docker Desktop from: https://www.docker.com/products/docker-desktop"
    fi
    exit 1
fi
print_info "Docker found"

# Check if Docker is running
if ! docker info &> /dev/null; then
    print_error "Docker is not running!"
    echo "   Please start Docker Desktop and try again."
    exit 1
fi
print_info "Docker is running"

# Check Docker Compose
if ! docker compose version &> /dev/null 2>&1; then
    print_warning "Docker Compose plugin not found"
    if [[ "$OS_NAME" == "ubuntu" ]]; then
        echo "   Install with: sudo apt-get install docker-compose-plugin"
    fi
fi

# Check Python
PYTHON=$(which python3 || which python || echo "")
PYTHON_VERSION=""
if [ -z "$PYTHON" ]; then
    print_warning "Python not found (required for local development)"
    echo "   Install Python 3.8+ from: https://www.python.org/downloads/"
else
    PYTHON_VERSION=$($PYTHON --version 2>&1 | awk '{print $2}')
    print_info "Python found: $PYTHON_VERSION"
    
    # Check if Python version is sufficient
    if ! $PYTHON -c "import sys; exit(0 if sys.version_info >= (3,8) else 1)" 2>/dev/null; then
        print_error "Python 3.8 or higher is required"
        exit 1
    fi
fi

# Check Node.js (for timeline viewer)
if ! command -v node &> /dev/null; then
    print_warning "Node.js not found (optional for timeline viewer)"
    echo "   Install Node.js 18+ from: https://nodejs.org/"
else
    print_info "Node.js found: $(node --version)"
fi

# Install system dependencies on Ubuntu
if [[ "$OS_NAME" == "ubuntu" ]]; then
    print_step "Checking system dependencies..."
    
    MISSING_DEPS=()
    
    # Check for required packages
    if ! dpkg -s python3-venv &> /dev/null; then
        MISSING_DEPS+=("python3-venv")
    fi
    
    if ! dpkg -s python3-dev &> /dev/null; then
        MISSING_DEPS+=("python3-dev")
    fi
    
    if ! dpkg -s libpq-dev &> /dev/null; then
        MISSING_DEPS+=("libpq-dev")
    fi
    
    if ! dpkg -s build-essential &> /dev/null; then
        MISSING_DEPS+=("build-essential")
    fi
    
    if [ ${#MISSING_DEPS[@]} -ne 0 ]; then
        print_warning "Missing system dependencies: ${MISSING_DEPS[*]}"
        echo "   Install with: sudo apt-get install -y ${MISSING_DEPS[*]}"
        
        read -p "Install missing dependencies now? (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            sudo apt-get update
            sudo apt-get install -y "${MISSING_DEPS[@]}"
        else
            print_error "System dependencies are required. Please install them manually."
            exit 1
        fi
    else
        print_info "All system dependencies are installed"
    fi
fi

echo ""
print_step "Setting up environment files..."

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
DATABASE_URL=postgresql://medgen_user:medgen_pass@localhost:5432/medical_patients_db
REDIS_URL=redis://localhost:6379
EOF
    print_info "Created .env file"
else
    print_info ".env file already exists"
fi

# Check if ports are available
echo ""
print_step "Checking port availability..."
PORTS_IN_USE=false
for port in 8000 5432 6379; do
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1 || netstat -tuln 2>/dev/null | grep -q ":$port "; then
        print_warning "Port $port is already in use"
        echo "   Run 'task stop' if you have services running"
        PORTS_IN_USE=true
    else
        print_info "Port $port is available"
    fi
done

if [[ "$PORTS_IN_USE" == true ]]; then
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""
print_step "Pulling Docker images..."
docker compose pull

echo ""
print_step "Creating Docker network and volumes..."
docker network create medical-patients_default 2>/dev/null || true

echo ""
print_step "Starting database services..."
docker compose up -d db redis

echo ""
print_step "Waiting for database to be ready..."
for i in {1..30}; do
    if docker compose exec -T db pg_isready -U medgen_user &> /dev/null; then
        print_info "Database is ready!"
        break
    fi
    echo -n "."
    sleep 1
done
echo ""

# Install Python dependencies if running locally
if [ -n "$PYTHON" ]; then
    echo ""
    print_step "Setting up Python environment..."
    
    # For Ubuntu 24.04 or if .venv doesn't exist, we need to create it
    if [[ "$IS_UBUNTU_24_04" == true ]] || [ ! -d ".venv" ]; then
        if [ -d ".venv" ]; then
            print_warning "Virtual environment exists but may need updates"
        else
            print_info "Creating Python virtual environment (required for Ubuntu 24.04+)..."
            $PYTHON -m venv .venv
            print_info "Created .venv"
        fi
        
        # Activate virtual environment
        print_info "Activating virtual environment..."
        source .venv/bin/activate
        
        # Upgrade pip
        print_info "Upgrading pip..."
        pip install --upgrade pip setuptools wheel
        
        # Install dependencies
        print_info "Installing Python dependencies..."
        
        # Install critical dependencies first
        pip install --no-cache-dir "pydantic>=2.0.0" || print_warning "Failed to install pydantic"
        pip install --no-cache-dir "alembic>=1.11.1" || print_warning "Failed to install alembic"
        pip install --no-cache-dir "psycopg2-binary>=2.9.5" || print_warning "Failed to install psycopg2-binary"
        pip install --no-cache-dir "sqlalchemy>=2.0.0" || print_warning "Failed to install sqlalchemy"
        
        # Install all requirements
        if ! pip install --no-cache-dir -r requirements.txt; then
            print_warning "Some dependencies failed to install"
            echo "   You may need to install them manually"
        else
            print_info "All Python dependencies installed successfully"
        fi
        
        # Create activation helper
        if [[ "$IS_UBUNTU_24_04" == true ]]; then
            cat > activate.sh << 'EOF'
#!/bin/bash
# Quick activation script for virtual environment

if [ -f .venv/bin/activate ]; then
    source .venv/bin/activate
    echo "✅ Virtual environment activated"
    echo "   Python: $(which python3)"
    echo "   Pip: $(which pip)"
    
    # Check if alembic is available
    if command -v alembic &> /dev/null; then
        echo "   Alembic: $(which alembic)"
    else
        echo "⚠️  Alembic not found. Install with: pip install alembic"
    fi
else
    echo "❌ Virtual environment not found. Run 'task init' first"
fi
EOF
            chmod +x activate.sh
            print_info "Created activation helper script: ./activate.sh"
        fi
        
    else
        print_info "Virtual environment already exists"
        echo "   Activate with: source .venv/bin/activate"
        echo "   Then run: pip install -r requirements.txt"
    fi
fi

print_step "Running database migrations..."

# Check if we can run migrations
MIGRATION_SUCCESS=false

# First try with alembic in virtual environment if activated
if [ -n "$VIRTUAL_ENV" ] && command -v alembic &> /dev/null; then
    print_info "Running migrations with local alembic..."
    if alembic upgrade head; then
        MIGRATION_SUCCESS=true
    else
        print_warning "Local migration failed, trying Docker..."
    fi
fi

# If local migration failed or not available, use Docker
if [[ "$MIGRATION_SUCCESS" == false ]]; then
    print_info "Running migrations with Docker..."
    if docker compose run --rm app alembic upgrade head; then
        MIGRATION_SUCCESS=true
    else
        print_error "Migration failed"
        echo "   You may need to run migrations manually after setup"
    fi
fi

if [[ "$MIGRATION_SUCCESS" == true ]]; then
    print_info "Database migrations completed successfully"
fi

# Timeline viewer setup
if command -v node &> /dev/null && [ -d "patient-timeline-viewer" ]; then
    echo ""
    print_step "Setting up Timeline Viewer..."
    read -p "Install Timeline Viewer dependencies? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cd patient-timeline-viewer && npm install && cd ..
        print_info "Timeline Viewer ready!"
    fi
fi

echo ""
echo "✨ Setup complete! Here's what to do next:"
echo ""

if [[ "$IS_UBUNTU_24_04" == true ]] || [ -n "$VIRTUAL_ENV" ]; then
    echo "📋 For local development with Python:"
    echo "   1. Activate virtual environment:"
    echo "      source .venv/bin/activate"
    echo "      (or use: ./activate.sh)"
    echo "   2. Start development server:"
    echo "      task dev"
    echo ""
    echo "📋 For Docker-only development:"
    echo "   1. Start all services:"
    echo "      task start"
else
    echo "📋 Quick Start:"
    echo "   1. Run 'task dev' to start the development server"
fi

echo ""
echo "🌐 Access points:"
echo "   - Main Application: http://localhost:8000"
echo "   - API Documentation: http://localhost:8000/docs"
echo "   - Timeline Viewer: http://localhost:5174 (run 'task timeline')"
echo ""

if [[ "$IS_UBUNTU_24_04" == true ]]; then
    echo "⚠️  Ubuntu 24.04 Note:"
    echo "   Always use the virtual environment for Python commands"
    echo "   System Python packages are externally managed (PEP 668)"
fi

echo ""
echo "Happy coding! 🎉"