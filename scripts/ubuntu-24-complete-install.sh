#!/bin/bash
# Complete Ubuntu 24.04 Installation Script
# This script installs everything needed from a fresh Ubuntu 24.04 system
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

echo "🚀 Ubuntu 24.04 Complete Installation for Medical Patients Generator"
echo "=================================================================="
echo ""

# Step 1: Update system
print_step "Updating system packages..."
sudo apt-get update -qq
sudo apt-get upgrade -y -qq

# Step 2: Install basic tools
print_step "Installing basic tools..."
sudo apt-get install -y -qq \
    git \
    curl \
    wget \
    openssl \
    ca-certificates \
    gnupg \
    lsb-release

# Step 3: Install Docker
print_step "Installing Docker..."
if ! command -v docker &> /dev/null; then
    # Add Docker's official GPG key
    sudo mkdir -m 0755 -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    
    # Add the repository
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # Update and install Docker
    sudo apt-get update -qq
    sudo apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    
    # Add user to docker group
    sudo usermod -aG docker $USER
    print_info "Docker installed. Using sudo for this session."
else
    print_info "Docker already installed"
fi

# Step 4: Install Task runner
print_step "Installing Task runner..."
if ! command -v task &> /dev/null; then
    curl -sL https://taskfile.dev/install.sh | sudo sh -s -- -b /usr/local/bin
    print_info "Task installed: $(task --version)"
else
    print_info "Task already installed"
fi

# Step 5: Install Python dependencies
print_step "Installing Python system dependencies..."
sudo apt-get install -y -qq \
    python3-venv \
    python3-dev \
    python3-pip \
    libpq-dev \
    build-essential \
    libssl-dev \
    libffi-dev \
    lsof \
    net-tools

# Step 6: Clone repository
print_step "Cloning repository..."
if [ ! -d "medical-patients" ]; then
    git clone https://github.com/banton/medical-patients.git
    cd medical-patients
    git checkout feature/v1.1-consolidated
else
    cd medical-patients
    git pull
fi

# Step 7: Run non-interactive setup
print_step "Running project setup..."
export NONINTERACTIVE=true

# Create .env file
if [ ! -f .env ]; then
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
fi

# Pull Docker images
print_info "Pulling Docker images..."
sudo docker compose pull

# Start services
print_info "Starting database services..."
sudo docker compose up -d db redis

# Wait for database
print_info "Waiting for database..."
sleep 10

# Create virtual environment
print_info "Creating Python virtual environment..."
python3 -m venv .venv
source .venv/bin/activate

# Install Python packages
print_info "Installing Python packages..."
pip install --upgrade pip setuptools wheel -q
pip install --no-cache-dir -q -r requirements.txt

# Run migrations
print_info "Running database migrations..."
alembic upgrade head

# Step 8: Test installation
print_step "Testing installation..."

# Start the app
print_info "Starting application..."
nohup python3 -m uvicorn src.main:app --host 0.0.0.0 --port 8000 > app.log 2>&1 &
APP_PID=$!

# Wait for app to start
sleep 10

# Test health endpoint
if curl -s http://localhost:8000/health | grep -q "healthy"; then
    print_info "✅ Application is running successfully!"
    kill $APP_PID 2>/dev/null || true
else
    print_error "❌ Application failed to start"
    cat app.log
    kill $APP_PID 2>/dev/null || true
    exit 1
fi

# Create helper scripts
cat > start.sh << 'EOF'
#!/bin/bash
source .venv/bin/activate
task dev
EOF
chmod +x start.sh

cat > activate.sh << 'EOF'
#!/bin/bash
source .venv/bin/activate
echo "✅ Virtual environment activated"
EOF
chmod +x activate.sh

# Final message
echo ""
echo "✨ Installation complete!"
echo ""
echo "📋 Quick Start:"
echo "   1. Logout and login (or run: newgrp docker)"
echo "   2. cd medical-patients"
echo "   3. ./start.sh"
echo ""
echo "🌐 Access:"
echo "   - Application: http://localhost:8000"
echo "   - API Docs: http://localhost:8000/docs"
echo ""
echo "⚠️  Note: Docker group changes require logout/login to take effect"
echo ""