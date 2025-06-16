# Ubuntu 24.04 LTS Installation Guide

This guide provides detailed instructions for installing and running the Medical Patients Generator on Ubuntu 24.04 LTS (Noble Numbat).

## Overview

Ubuntu 24.04 LTS introduces PEP 668 (externally-managed-environment) which prevents installing Python packages system-wide using pip. This is a security feature to prevent conflicts between system packages and pip-installed packages. All Python packages must be installed in a virtual environment.

## Prerequisites

### System Requirements
- Ubuntu 24.04 LTS (Noble Numbat)
- 4GB RAM minimum (8GB recommended)
- 10GB free disk space
- Internet connection for downloading dependencies

### Required Software
- Python 3.12 (included in Ubuntu 24.04)
- Docker and Docker Compose
- Git
- Node.js 18+ (optional, for timeline viewer)

## Quick Installation

We provide an automated setup script specifically for Ubuntu 24.04:

```bash
# Clone the repository
git clone <repository_url>
cd medical-patients

# Run the Ubuntu 24.04 setup script
chmod +x scripts/setup-ubuntu-24.sh
./scripts/setup-ubuntu-24.sh
```

This script will:
1. Install all system dependencies
2. Set up Docker and Docker Compose (if needed)
3. Create a Python virtual environment
4. Install all Python packages including Alembic
5. Configure the database
6. Run initial migrations
7. Create helper scripts for easy activation

## Manual Installation Steps

If you prefer manual installation or the script fails:

### 1. Update System and Install Dependencies

```bash
# Update package list
sudo apt update

# Install Python development tools
sudo apt install -y python3-pip python3-venv python3-dev

# Install build essentials
sudo apt install -y build-essential

# Install PostgreSQL client libraries
sudo apt install -y postgresql-client libpq-dev

# Install other utilities
sudo apt install -y redis-tools git curl openssl
```

### 2. Install Docker

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Log out and back in for group changes to take effect
# Or use: newgrp docker

# Install Docker Compose plugin
sudo apt install -y docker-compose-plugin

# Verify installation
docker --version
docker compose version
```

### 3. Install Node.js (Optional - for Timeline Viewer)

```bash
# Install Node.js 20.x
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Verify installation
node --version
npm --version
```

### 4. Set Up Python Virtual Environment

**IMPORTANT**: Always use a virtual environment on Ubuntu 24.04!

```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel
```

### 5. Install Python Dependencies

```bash
# With virtual environment activated
pip install -r requirements.txt

# If you get errors, install dependencies one by one:
pip install alembic>=1.11.1
pip install psycopg2-binary>=2.9.5
pip install fastapi==0.100.0
# ... continue with other packages
```

### 6. Configure Environment

```bash
# Create .env file
cp .env.example .env

# Or create manually
cat > .env << EOF
API_KEY=dev_secret_key_$(openssl rand -hex 16)
DEBUG=True
CORS_ORIGINS=http://localhost:8000,http://localhost:5174
CACHE_TTL=3600
DATABASE_URL=postgresql://medgen_user:medgen_pass@localhost:5432/medical_patients_db
REDIS_URL=redis://localhost:6379
EOF
```

### 7. Start Services

```bash
# Start database services
docker compose up -d db redis

# Wait for database to be ready
sleep 10

# Run migrations
alembic upgrade head

# Start the application
python3 -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

## Common Issues and Solutions

### Issue: "command not found: alembic"

**Solution**: Ensure you've activated the virtual environment:
```bash
source .venv/bin/activate
which alembic  # Should show path in .venv
```

### Issue: "error: externally-managed-environment"

**Solution**: Never use `pip install` without a virtual environment on Ubuntu 24.04:
```bash
# Wrong
pip install package-name

# Correct
source .venv/bin/activate
pip install package-name
```

### Issue: "psycopg2 installation fails"

**Solution**: Install PostgreSQL development headers:
```bash
sudo apt install libpq-dev
pip install psycopg2-binary
```

### Issue: "Permission denied" when running Docker

**Solution**: Add your user to the docker group:
```bash
sudo usermod -aG docker $USER
# Log out and back in, or run:
newgrp docker
```

### Issue: "Port 8000 already in use"

**Solution**: Check what's using the port:
```bash
sudo lsof -i :8000
# Kill the process or use a different port
```

## Running the Application

### Development Mode

Always activate the virtual environment first:

```bash
# Using the helper script (created by setup)
./activate.sh

# Or manually
source .venv/bin/activate

# Start with Task
task dev

# Or manually
python3 -m uvicorn src.main:app --reload
```

### Using Task Commands

The project uses Task for command automation:

```bash
# First time setup
task init

# Start development
task dev

# Run tests
task test

# View all commands
task --list
```

### Docker Mode

To run everything in Docker:

```bash
# Build and start all services
docker compose up --build

# Run in background
docker compose up -d

# View logs
docker compose logs -f
```

## Timeline Viewer Setup

If you want to use the React timeline viewer:

```bash
# Install dependencies
cd patient-timeline-viewer
npm install

# Start development server
npm run dev

# Or use Task from project root
task timeline
```

## Production Deployment on Ubuntu 24.04

For production deployments:

1. Use a production virtual environment:
   ```bash
   python3 -m venv /opt/medical-patients/venv
   source /opt/medical-patients/venv/bin/activate
   ```

2. Install with production dependencies only:
   ```bash
   pip install --no-cache-dir -r requirements.txt
   ```

3. Use systemd service files for process management
4. Configure nginx as reverse proxy
5. Use environment variables for secrets

## Getting Help

If you encounter issues:

1. Check the virtual environment is activated: `which python3`
2. Verify all dependencies: `pip list`
3. Check Docker services: `docker compose ps`
4. Review logs: `docker compose logs`
5. Check system logs: `journalctl -xe`

## Additional Resources

- [Ubuntu 24.04 Release Notes](https://discourse.ubuntu.com/t/noble-numbat-release-notes/39890)
- [PEP 668 Documentation](https://peps.python.org/pep-0668/)
- [Python venv Documentation](https://docs.python.org/3/library/venv.html)
- [Docker Installation Guide](https://docs.docker.com/engine/install/ubuntu/)