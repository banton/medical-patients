# Ubuntu 24.04 LTS Compatibility

This document outlines the compatibility improvements made to support Ubuntu 24.04 LTS (Noble Numbat).

## Key Changes Made

### 1. Task Runner Installation
- **Issue**: The default `install-task.sh` script attempted to install via snap, which could hang indefinitely
- **Solution**: Updated to use the official Task installer directly, bypassing snap
- **Files Updated**: 
  - `scripts/install-task.sh` - Added detection to avoid snap on Ubuntu
  - `scripts/init-setup.sh` - Added Task check before other prerequisites
  - `scripts/setup-ubuntu-24.sh` - Installs Task using official method

### 2. Python Virtual Environment (PEP 668)
- **Issue**: Ubuntu 24.04 enforces PEP 668, preventing system-wide pip installations
- **Solution**: All scripts now create and use virtual environments automatically
- **Files Updated**:
  - `scripts/init-setup.sh` - Auto-detects Ubuntu 24.04 and creates venv
  - `scripts/setup-ubuntu-24.sh` - Dedicated Ubuntu 24.04 setup script
  - Created `activate.sh` helper script for easy venv activation

### 3. Docker Installation
- **Issue**: Docker not installed by default on fresh Ubuntu 24.04
- **Solution**: Scripts now check for Docker and provide installation instructions
- **Improvements**:
  - Clear instructions for Docker installation
  - Automatic user addition to docker group
  - Guidance on group changes (logout/login or newgrp)

### 4. System Dependencies
- **Issue**: Missing system packages required for Python packages
- **Solution**: Scripts now install all required system dependencies:
  - `python3-venv` - Required for virtual environments
  - `python3-dev` - Python development headers
  - `libpq-dev` - PostgreSQL development headers
  - `build-essential` - Compilation tools
  - `lsof`, `net-tools` - Network utilities

## Quick Start for Ubuntu 24.04

```bash
# Clone the repository
git clone https://github.com/banton/medical-patients.git
cd medical-patients

# Option 1: Use the Ubuntu-specific setup script
chmod +x scripts/setup-ubuntu-24.sh
./scripts/setup-ubuntu-24.sh

# Option 2: Use Task (after installing it)
curl -sL https://taskfile.dev/install.sh | sudo sh -s -- -b /usr/local/bin
task init
```

## Testing Results

Successfully tested on Ubuntu 24.04 LTS (June 17, 2025):
- ✅ Task runner installation without hanging
- ✅ Python virtual environment creation and activation
- ✅ All Python dependencies installed
- ✅ Docker services started successfully
- ✅ Database migrations completed
- ✅ Application running and accessible
- ✅ Health endpoint responding correctly

## Known Issues & Workarounds

### 1. Docker Group Permissions
After adding user to docker group, you must either:
- Logout and login again
- Run `newgrp docker` in current session
- Use `sudo docker` commands until logout/login

### 2. Port Conflicts
If ports are in use, check with:
```bash
lsof -i :8000
lsof -i :5432
lsof -i :6379
```

### 3. Virtual Environment
Always activate the virtual environment:
```bash
source .venv/bin/activate
# or
./activate.sh
```

## Recommendations for CI/CD

1. Add Ubuntu 24.04 to GitHub Actions matrix
2. Use container images with pre-installed dependencies
3. Always use virtual environments in CI
4. Cache pip dependencies for faster builds

## Future Improvements

1. Create automated test for Ubuntu 24.04 compatibility
2. Add Ubuntu 24.04 specific Docker image
3. Create systemd service files for production deployment
4. Add automatic venv activation to shell profile