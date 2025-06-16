#!/bin/bash
# Ubuntu 24.04 LTS (Noble Numbat) Setup Script
# Handles PEP 668 externally-managed-environment requirements

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

echo "🐧 Medical Patients Generator - Ubuntu 24.04 LTS Setup"
echo "====================================================="
echo ""

# Check if running on Ubuntu 24.04
if [ -f /etc/os-release ]; then
    . /etc/os-release
    if [[ "$VERSION_ID" == "24.04" ]]; then
        print_info "Ubuntu 24.04 LTS detected"
    else
        print_warning "This script is optimized for Ubuntu 24.04 but may work on other versions"
    fi
fi

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
print_info "Python version: $PYTHON_VERSION"

if ! python3 -c "import sys; exit(0 if sys.version_info >= (3,8) else 1)" 2>/dev/null; then
    print_error "Python 3.8 or higher is required"
    exit 1
fi

# Install system dependencies
print_step "Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y \
    python3-pip \
    python3-venv \
    python3-dev \
    build-essential \
    postgresql-client \
    libpq-dev \
    redis-tools \
    git \
    curl \
    openssl

# Install Docker if not present
if ! command -v docker &> /dev/null; then
    print_step "Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    print_warning "You may need to log out and back in for Docker group changes to take effect"
else
    print_info "Docker is already installed"
fi

# Install Docker Compose if not present
if ! command -v docker &> /dev/null || ! docker compose version &> /dev/null; then
    print_step "Installing Docker Compose..."
    sudo apt-get install -y docker-compose-plugin
else
    print_info "Docker Compose is already installed"
fi

# Install Node.js if not present (for timeline viewer)
if ! command -v node &> /dev/null; then
    print_step "Installing Node.js..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    sudo apt-get install -y nodejs
else
    print_info "Node.js is already installed: $(node --version)"
fi

# Create project directory structure
print_step "Setting up project directory..."
mkdir -p output temp

# Create virtual environment (required on Ubuntu 24.04 due to PEP 668)
print_step "Creating Python virtual environment..."
if [ -d ".venv" ]; then
    print_warning "Virtual environment already exists. Removing old one..."
    rm -rf .venv
fi

python3 -m venv .venv
print_info "Virtual environment created"

# Activate virtual environment
print_step "Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip, setuptools, and wheel
print_step "Upgrading pip and build tools..."
pip install --upgrade pip setuptools wheel

# Install Python dependencies with proper error handling
print_step "Installing Python dependencies..."

# First install critical dependencies separately to handle potential conflicts
pip install --no-cache-dir "pydantic>=2.0.0"
pip install --no-cache-dir "alembic>=1.11.1"
pip install --no-cache-dir "psycopg2-binary>=2.9.5"
pip install --no-cache-dir "sqlalchemy>=2.0.0"

# Then install the rest
if ! pip install --no-cache-dir -r requirements.txt; then
    print_error "Failed to install all dependencies"
    print_info "Trying to install dependencies one by one..."
    
    while IFS= read -r line; do
        # Skip empty lines and comments
        if [[ -z "$line" ]] || [[ "$line" == \#* ]]; then
            continue
        fi
        
        # Extract package name for display
        package=$(echo "$line" | cut -d'=' -f1 | cut -d'>' -f1 | cut -d'<' -f1 | cut -d'[' -f1)
        
        print_info "Installing $package..."
        if ! pip install --no-cache-dir "$line"; then
            print_warning "Failed to install $line, skipping..."
        fi
    done < requirements.txt
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    print_step "Creating .env file..."
    API_KEY_VALUE="dev_secret_key_$(openssl rand -hex 16)"
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

# Setup Docker network and volumes
print_step "Setting up Docker resources..."
docker network create medical-patients_default 2>/dev/null || true

# Start database services
print_step "Starting database services..."
docker compose up -d db redis

# Wait for PostgreSQL to be ready
print_step "Waiting for PostgreSQL to be ready..."
for i in {1..30}; do
    if docker compose exec -T db pg_isready -U medgen_user &> /dev/null; then
        print_info "Database is ready!"
        break
    fi
    echo -n "."
    sleep 1
done
echo ""

# Run database migrations
print_step "Running database migrations..."
if ! alembic upgrade head; then
    print_warning "Failed to run migrations. This might be okay if the database already exists."
fi

# Install timeline viewer dependencies if Node.js is available
if command -v node &> /dev/null && [ -d "patient-timeline-viewer" ]; then
    print_step "Installing Timeline Viewer dependencies..."
    cd patient-timeline-viewer
    npm install
    cd ..
    print_info "Timeline Viewer ready!"
fi

# Create activation script
print_step "Creating activation helper script..."
cat > activate.sh << 'EOF'
#!/bin/bash
# Quick activation script for Ubuntu 24.04 virtual environment

if [ -f .venv/bin/activate ]; then
    source .venv/bin/activate
    echo "✅ Virtual environment activated"
    echo "   Python: $(which python3)"
    echo "   Pip: $(which pip)"
else
    echo "❌ Virtual environment not found. Run ./scripts/setup-ubuntu-24.sh first"
fi
EOF
chmod +x activate.sh

# Display final instructions
echo ""
echo "✨ Setup complete! Ubuntu 24.04 environment is ready."
echo ""
echo "📋 Quick Start Commands:"
echo "   1. Activate virtual environment: source .venv/bin/activate"
echo "      (or use the helper: ./activate.sh)"
echo "   2. Start development server: python3 -m uvicorn src.main:app --reload"
echo "   3. View API docs: http://localhost:8000/docs"
echo ""
echo "🐳 Docker Services:"
echo "   - PostgreSQL: localhost:5432"
echo "   - Redis: localhost:6379"
echo ""
echo "📊 Timeline Viewer (optional):"
echo "   cd patient-timeline-viewer && npm run dev"
echo ""
echo "⚠️  Ubuntu 24.04 Notes:"
echo "   - Always use virtual environment (PEP 668 requirement)"
echo "   - System Python packages are externally managed"
echo "   - Use 'pip install --user' only as last resort"
echo ""
echo "🔧 Troubleshooting:"
echo "   - If Alembic is missing: pip install alembic"
echo "   - If psycopg2 fails: sudo apt-get install libpq-dev"
echo "   - Database issues: docker compose logs db"
echo ""