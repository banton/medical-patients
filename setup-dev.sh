#!/bin/bash
# Developer Setup Script
# Sets up the development environment with all necessary tools

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
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

print_info "Setting up development environment..."

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
REQUIRED_VERSION="3.8"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    print_error "Python $REQUIRED_VERSION or higher is required. Found: Python $PYTHON_VERSION"
    exit 1
fi

# Check Node.js
if ! command -v node &> /dev/null; then
    print_error "Node.js is not installed. Please install Node.js 16 or higher."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    print_info "Creating Python virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
print_info "Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
print_info "Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
print_info "Installing Python dependencies..."
pip install -r requirements.txt

# Install development tools
print_info "Installing Python development tools..."
pip install ruff mypy types-requests pre-commit pytest-cov

# Install Node dependencies
print_info "Installing Node.js dependencies..."
npm install

# Install pre-commit hooks
print_info "Installing pre-commit hooks..."
pre-commit install

# Run initial checks
print_info "Running initial code quality checks..."

# Python linting
print_info "Checking Python code with Ruff..."
ruff check src/ patient_generator/ --fix || true

# Python formatting
print_info "Formatting Python code..."
ruff format src/ patient_generator/

# JavaScript linting
print_info "Checking JavaScript code..."
npm run lint || true

# Run pre-commit on all files (optional)
read -p "Run pre-commit on all files? This may take a while. (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_info "Running pre-commit on all files..."
    pre-commit run --all-files || true
fi

# Database setup reminder
print_warning "Don't forget to set up the database:"
echo "  1. Start PostgreSQL and Redis: docker compose up -d db redis"
echo "  2. Run migrations: alembic upgrade head"
echo "  3. Copy .env.example to .env and update values"

# Create .env if it doesn't exist
if [ ! -f ".env" ]; then
    print_info "Creating .env file from template..."
    cp .env.example .env
    print_warning "Please update .env with your local configuration"
fi

# Success message
print_info "Development environment setup complete!"
echo
echo "Next steps:"
echo "  1. Activate virtual environment: source .venv/bin/activate"
echo "  2. Start development server: make dev"
echo "  3. Run tests: make test"
echo "  4. Check code quality: make lint"
echo
echo "Available make commands:"
make help