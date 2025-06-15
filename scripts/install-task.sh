#!/bin/bash
# Task Runner Installation Script for Cross-Platform Development
# Supports Linux, macOS, and Windows (via WSL/Git Bash)

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Detect OS
detect_os() {
    case "$(uname -s)" in
        Linux*)     OS="linux";;
        Darwin*)    OS="macos";;
        CYGWIN*|MINGW*|MSYS*) OS="windows";;
        *)          OS="unknown";;
    esac
}

# Check if Task is already installed
check_existing_task() {
    if command -v task >/dev/null 2>&1; then
        EXISTING_VERSION=$(task --version 2>/dev/null | grep -o 'v[0-9.]*' || echo "unknown")
        print_warning "Task is already installed (version: $EXISTING_VERSION)"
        read -p "Do you want to reinstall/update? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_status "Using existing Task installation"
            return 0
        fi
    fi
    return 1
}

# Install Task using the official installer
install_task_official() {
    print_status "Installing Task using official installer..."
    
    if [ "$OS" = "windows" ]; then
        print_error "Windows detected. Please install Task manually:"
        echo "  - PowerShell: irm https://taskfile.dev/install.ps1 | iex"
        echo "  - Scoop: scoop install task"
        echo "  - Chocolatey: choco install go-task"
        return 1
    fi
    
    # Download and run official installer
    curl -sL https://taskfile.dev/install.sh | sh
    
    # Move to PATH if needed
    if [ -f "./bin/task" ]; then
        print_status "Moving task to /usr/local/bin..."
        sudo mv ./bin/task /usr/local/bin/task
        sudo chmod +x /usr/local/bin/task
        rm -rf ./bin
    fi
}

# Install Task using package managers
install_task_package_manager() {
    case "$OS" in
        "macos")
            if command -v brew >/dev/null 2>&1; then
                print_status "Installing Task via Homebrew..."
                brew install go-task
                return 0
            fi
            ;;
        "linux")
            # Try different package managers
            if command -v apt >/dev/null 2>&1; then
                print_status "Installing Task via apt..."
                # Task might not be in default repos, so try snap first
                if command -v snap >/dev/null 2>&1; then
                    sudo snap install task --classic
                    return 0
                fi
            elif command -v yum >/dev/null 2>&1; then
                print_status "RedHat-based system detected. Using official installer..."
                install_task_official
                return 0
            elif command -v pacman >/dev/null 2>&1; then
                print_status "Installing Task via pacman..."
                sudo pacman -S go-task
                return 0
            fi
            ;;
    esac
    
    # Fallback to official installer
    install_task_official
}

# Verify installation
verify_installation() {
    if command -v task >/dev/null 2>&1; then
        TASK_VERSION=$(task --version)
        print_success "Task installed successfully!"
        print_status "Version: $TASK_VERSION"
        
        # Test basic functionality
        if echo "version: '3'" > /tmp/test-taskfile.yml && task -t /tmp/test-taskfile.yml --list >/dev/null 2>&1; then
            print_success "Task is working correctly"
            rm -f /tmp/test-taskfile.yml
        else
            print_warning "Task installed but may not be working correctly"
        fi
    else
        print_error "Task installation failed"
        return 1
    fi
}

# Show next steps
show_next_steps() {
    echo
    print_success "Task installation complete!"
    echo
    print_status "Next steps:"
    echo "  1. Restart your terminal or run: source ~/.bashrc"
    echo "  2. Verify installation: task --version"
    echo "  3. Create Taskfile.yml in your project"
    echo "  4. Run: task --list to see available tasks"
    echo
    print_status "For this project:"
    echo "  - Run: task setup (when Taskfile.yml is ready)"
    echo "  - Run: task dev (to start development environment)"
    echo
}

# Main installation process
main() {
    echo "================================="
    echo "Task Runner Installation Script"
    echo "Medical Patients Generator Project"
    echo "================================="
    echo
    
    detect_os
    print_status "Detected OS: $OS"
    
    # Check if already installed
    if check_existing_task; then
        verify_installation
        show_next_steps
        return 0
    fi
    
    # Install Task
    print_status "Installing Task runner..."
    
    if install_task_package_manager; then
        verify_installation && show_next_steps
    else
        print_error "Installation failed. Please install manually:"
        echo "  - Visit: https://taskfile.dev/installation/"
        echo "  - Or use package manager specific to your OS"
        return 1
    fi
}

# Run main function
main "$@"