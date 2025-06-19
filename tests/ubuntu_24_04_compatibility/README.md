# Ubuntu 24.04 LTS Compatibility Testing Suite

This comprehensive testing suite ensures the Medical Patients Generator application is fully compatible with Ubuntu 24.04 LTS (Noble Numbat) and its default package versions.

## Overview

Ubuntu 24.04 LTS introduces significant changes that affect Python applications:

- **Python 3.12.3** as default (vs 3.10 in Ubuntu 22.04)
- **PEP 668** implementation (externally-managed-environment)
- **PostgreSQL 16.2** as default database
- **OpenSSL 3.x** with TLS 1.0/1.1 disabled
- **AppArmor 4.0** with stricter security policies

## Test Suite Structure

```
tests/ubuntu_24_04_compatibility/
├── test_ubuntu_compatibility.py      # Main compatibility test orchestrator
├── test_database_compatibility.py    # PostgreSQL 16.2 specific tests  
├── test_docker_compatibility.py      # Container and Docker tests
├── migration_helper.py              # Interactive migration assistant
└── README.md                        # This file
```

## Quick Start

### 1. Check Current Compatibility

```bash
# Check your current system
python tests/ubuntu_24_04_compatibility/migration_helper.py --check

# Run compatibility tests
pytest tests/ubuntu_24_04_compatibility/ -v
```

### 2. Prepare for Migration

```bash
# Backup current environment
python tests/ubuntu_24_04_compatibility/migration_helper.py --backup

# Start migration process
python tests/ubuntu_24_04_compatibility/migration_helper.py --migrate
```

### 3. Run Full Test Suite

```bash
# Create Ubuntu 24.04 compatible virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install pytest pytest-asyncio

# Run all compatibility tests
pytest tests/ubuntu_24_04_compatibility/ -v --tb=short
```

## Key Changes for Ubuntu 24.04

### 1. Virtual Environment Requirement (PEP 668)

Ubuntu 24.04 prevents system-wide pip installations:

```bash
# This will fail
pip install package-name

# This works
python3 -m venv .venv
source .venv/bin/activate
pip install package-name
```

### 2. Dockerfile Updates

Update your Dockerfile for Ubuntu 24.04:

```dockerfile
FROM ubuntu:24.04

# Install Python with venv support
RUN apt-get update && \
    apt-get install -y python3-full python3-venv

# Create virtual environment
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Now pip works
RUN pip install --upgrade pip
```

### 3. System Dependencies

Install required packages:

```bash
sudo apt-get update
sudo apt-get install -y \
  build-essential \
  libpq-dev \
  libssl-dev \
  libffi-dev \
  python3-dev \
  python3-venv \
  cargo \        # New: Required for cryptography
  pkg-config
```

## Running Tests

The test suite validates:
- System package compatibility
- Python environment setup
- Database connectivity and features
- Docker container builds
- Security configurations

For detailed testing instructions, run individual test modules or use the migration helper for guided assistance.
