# Ubuntu 24.04 LTS Compatibility Guide

## Overview
This document outlines the changes and configurations needed to ensure the Medical Patients Generator works seamlessly on Ubuntu 24.04 LTS (Noble Numbat).

## Key Changes in Ubuntu 24.04

### 1. Python Environment (PEP 668)
Ubuntu 24.04 enforces PEP 668, which prevents system-wide pip installations to protect the system Python environment.

**Solution**: Always use virtual environments
```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Default Python Version
- Ubuntu 24.04 ships with Python 3.12.3
- Our application targets Python 3.8-3.12 for maximum compatibility
- Docker images use Python 3.11 for consistency across platforms

### 3. PostgreSQL 16.2
Ubuntu 24.04 includes PostgreSQL 16.2 by default, which is fully compatible with our application.

### 4. System Dependencies
Required packages for Ubuntu 24.04:
```bash
sudo apt-get update
sudo apt-get install -y \
  python3.11 python3.11-venv python3.11-dev \
  build-essential libpq-dev libssl-dev libffi-dev \
  cargo pkg-config curl git
```

## Docker Support

### Available Dockerfiles

1. **Dockerfile** - Standard build (Python 3.11-slim)
   ```bash
   docker build -t medical-patients:latest .
   ```

2. **Dockerfile.unified** - Cross-platform unified build
   ```bash
   docker build -f Dockerfile.unified -t medical-patients:unified .
   ```

3. **Dockerfile.ubuntu2404** - Ubuntu 24.04 specific
   ```bash
   docker build -f Dockerfile.ubuntu2404 -t medical-patients:ubuntu2404 .
   ```

## Installation Steps for Ubuntu 24.04

### 1. System Setup
```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install dependencies
sudo apt-get install -y \
  python3.11 python3.11-venv python3.11-dev \
  build-essential libpq-dev libssl-dev libffi-dev \
  cargo pkg-config curl git \
  docker.io docker-compose

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

### 2. Project Setup
```bash
# Clone repository
git clone <repository-url>
cd medical-patients

# Create virtual environment (REQUIRED)
python3.11 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Install Task runner
curl -sL https://taskfile.dev/install.sh | sh

# Run setup
task setup
```

### 3. Database Setup
```bash
# Using Docker (recommended)
task db:start
task db:migrate

# Using system PostgreSQL 16
sudo -u postgres createdb medical_patients
sudo -u postgres createuser medical_patients_user
```

## Compatibility Testing

Run the Ubuntu 24.04 compatibility tests:
```bash
pytest tests/ubuntu_24_04_compatibility/ -v
```

## Known Issues and Solutions

### Issue 1: pip install fails globally
**Error**: `error: externally-managed-environment`
**Solution**: Always use virtual environments

### Issue 2: Cryptography build fails
**Error**: `error: Microsoft Visual C++ 14.0 or greater is required`
**Solution**: Install cargo and build tools
```bash
sudo apt-get install cargo build-essential
```

### Issue 3: psycopg2 installation fails
**Error**: `pg_config executable not found`
**Solution**: Install PostgreSQL development files
```bash
sudo apt-get install libpq-dev
```

## Performance Considerations

1. **PostgreSQL 16 Benefits**:
   - ~15% query performance improvement
   - Better parallel query execution
   - Enhanced JSON operations

2. **Python 3.11 in Docker**:
   - 10-60% faster than Python 3.10
   - Better error messages
   - Consistent across all deployments

## Migration Checklist

- [ ] Backup existing data
- [ ] Update system packages
- [ ] Install Python 3.11 and create virtual environment
- [ ] Install system dependencies (cargo, libpq-dev, etc.)
- [ ] Run compatibility tests
- [ ] Deploy using Ubuntu 24.04 compatible Docker image
- [ ] Verify PostgreSQL 16 connectivity
- [ ] Test application functionality

## Support

For Ubuntu 24.04 specific issues:
1. Check this guide first
2. Run compatibility tests
3. Check `/tests/ubuntu_24_04_compatibility/README.md`
4. Report issues with Ubuntu 24.04 tag