#!/bin/bash

# Ubuntu 24.04 LTS Compatibility Test Runner
# This script performs comprehensive compatibility testing for the Medical Patients Generator

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test results
TESTS_PASSED=0
TESTS_FAILED=0
WARNINGS=()

echo -e "${BLUE}Ubuntu 24.04 LTS Compatibility Test Suite${NC}"
echo -e "${BLUE}==========================================${NC}"
echo ""

# Function to run a test
run_test() {
    local test_name=$1
    local test_command=$2
    
    echo -e "${YELLOW}Running: ${test_name}${NC}"
    if eval "$test_command"; then
        echo -e "${GREEN}✓ ${test_name} passed${NC}"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}✗ ${test_name} failed${NC}"
        ((TESTS_FAILED++))
    fi
    echo ""
}

# Function to check command availability
check_command() {
    local cmd=$1
    local package=$2
    
    if command -v "$cmd" &> /dev/null; then
        echo -e "${GREEN}✓ $cmd is installed${NC}"
        return 0
    else
        echo -e "${RED}✗ $cmd is not installed (install with: sudo apt-get install $package)${NC}"
        return 1
    fi
}

# 1. System Information
echo -e "${BLUE}=== System Information ===${NC}"
if [ -f /etc/os-release ]; then
    . /etc/os-release
    echo "OS: $NAME $VERSION"
    if [[ "$VERSION_ID" == "24.04" ]]; then
        echo -e "${GREEN}✓ Running on Ubuntu 24.04 LTS${NC}"
    else
        echo -e "${YELLOW}⚠ Not running on Ubuntu 24.04 (found $VERSION_ID)${NC}"
        WARNINGS+=("Not running on Ubuntu 24.04")
    fi
else
    echo -e "${RED}✗ Cannot determine OS version${NC}"
fi
echo ""

# 2. Python Version Check
echo -e "${BLUE}=== Python Compatibility ===${NC}"
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $PYTHON_VERSION"

if [[ "$PYTHON_VERSION" == 3.12.* ]]; then
    echo -e "${GREEN}✓ Python 3.12.x detected${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${YELLOW}⚠ Python $PYTHON_VERSION detected (Ubuntu 24.04 ships with 3.12.3)${NC}"
    WARNINGS+=("Python version mismatch")
fi

# Test PEP 668
echo -n "Testing PEP 668 (externally-managed-environment)... "
if python3 -m pip install --user requests 2>&1 | grep -q "externally-managed-environment"; then
    echo -e "${GREEN}✓ PEP 668 active${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${YELLOW}⚠ PEP 668 not enforced${NC}"
    WARNINGS+=("PEP 668 not active")
fi
echo ""

# 3. System Dependencies
echo -e "${BLUE}=== System Dependencies ===${NC}"
REQUIRED_PACKAGES=(
    "gcc:build-essential"
    "psql:postgresql-client"
    "cargo:cargo"
    "pkg-config:pkg-config"
)

for pkg_pair in "${REQUIRED_PACKAGES[@]}"; do
    IFS=':' read -r cmd package <<< "$pkg_pair"
    check_command "$cmd" "$package"
done

# Check specific library packages
echo -e "\n${YELLOW}Checking development libraries:${NC}"
REQUIRED_LIBS=(
    "libpq-dev"
    "libssl-dev"
    "libffi-dev"
    "python3-dev"
    "python3-venv"
)

for lib in "${REQUIRED_LIBS[@]}"; do
    if dpkg -l | grep -q "^ii  $lib"; then
        echo -e "${GREEN}✓ $lib is installed${NC}"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}✗ $lib is not installed${NC}"
        ((TESTS_FAILED++))
    fi
done
echo ""

# 4. Virtual Environment Test
echo -e "${BLUE}=== Virtual Environment Test ===${NC}"
TEMP_VENV=$(mktemp -d)
echo "Creating test virtual environment in $TEMP_VENV..."

if python3 -m venv "$TEMP_VENV/venv"; then
    echo -e "${GREEN}✓ Virtual environment created successfully${NC}"
    
    # Test activation and pip
    if source "$TEMP_VENV/venv/bin/activate"; then
        echo -e "${GREEN}✓ Virtual environment activated${NC}"
        
        # Test pip in venv
        if pip install --upgrade pip &> /dev/null; then
            echo -e "${GREEN}✓ pip upgrade successful in venv${NC}"
            ((TESTS_PASSED++))
        else
            echo -e "${RED}✗ pip upgrade failed in venv${NC}"
            ((TESTS_FAILED++))
        fi
        
        deactivate
    else
        echo -e "${RED}✗ Failed to activate virtual environment${NC}"
        ((TESTS_FAILED++))
    fi
else
    echo -e "${RED}✗ Failed to create virtual environment${NC}"
    ((TESTS_FAILED++))
fi

rm -rf "$TEMP_VENV"
echo ""

# 5. PostgreSQL Check
echo -e "${BLUE}=== PostgreSQL Compatibility ===${NC}"
if command -v psql &> /dev/null; then
    PG_VERSION=$(psql --version | awk '{print $3}')
    echo "PostgreSQL client version: $PG_VERSION"
    
    if [[ "$PG_VERSION" == 16.* ]]; then
        echo -e "${GREEN}✓ PostgreSQL 16.x client detected${NC}"
        ((TESTS_PASSED++))
    else
        echo -e "${YELLOW}⚠ PostgreSQL $PG_VERSION detected (Ubuntu 24.04 ships with 16.2)${NC}"
        WARNINGS+=("PostgreSQL version mismatch")
    fi
else
    echo -e "${YELLOW}⚠ PostgreSQL client not installed${NC}"
    WARNINGS+=("PostgreSQL client missing")
fi
echo ""

# 6. OpenSSL Check
echo -e "${BLUE}=== OpenSSL Compatibility ===${NC}"
if command -v openssl &> /dev/null; then
    OPENSSL_VERSION=$(openssl version)
    echo "OpenSSL version: $OPENSSL_VERSION"
    
    if [[ "$OPENSSL_VERSION" == *"OpenSSL 3."* ]]; then
        echo -e "${GREEN}✓ OpenSSL 3.x detected${NC}"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}✗ OpenSSL 3.x not detected${NC}"
        ((TESTS_FAILED++))
    fi
else
    echo -e "${RED}✗ OpenSSL not installed${NC}"
    ((TESTS_FAILED++))
fi
echo ""

# 7. Docker Check (if available)
echo -e "${BLUE}=== Docker Compatibility ===${NC}"
if command -v docker &> /dev/null; then
    echo -e "${GREEN}✓ Docker is installed${NC}"
    
    # Check if we can run docker commands
    if docker info &> /dev/null; then
        echo -e "${GREEN}✓ Docker daemon is running${NC}"
        ((TESTS_PASSED++))
    else
        echo -e "${YELLOW}⚠ Docker daemon not running or permission denied${NC}"
        WARNINGS+=("Docker daemon issues")
    fi
else
    echo -e "${YELLOW}⚠ Docker not installed (optional)${NC}"
fi
echo ""

# 8. AppArmor Check
echo -e "${BLUE}=== Security Features ===${NC}"
if [ -f /sys/kernel/security/apparmor/profiles ]; then
    echo -e "${GREEN}✓ AppArmor is enabled${NC}"
    APPARMOR_PROFILES=$(cat /sys/kernel/security/apparmor/profiles | wc -l)
    echo "  Active profiles: $APPARMOR_PROFILES"
    ((TESTS_PASSED++))
else
    echo -e "${YELLOW}⚠ AppArmor not detected${NC}"
    WARNINGS+=("AppArmor not active")
fi
echo ""

# 9. Python Package Test (in venv)
echo -e "${BLUE}=== Python Package Installation Test ===${NC}"
TEMP_VENV=$(mktemp -d)
python3 -m venv "$TEMP_VENV/venv"
source "$TEMP_VENV/venv/bin/activate"

echo "Testing critical package installations..."
TEST_PACKAGES=(
    "fastapi"
    "psycopg2-binary"
    "cryptography"
)

for package in "${TEST_PACKAGES[@]}"; do
    echo -n "Installing $package... "
    if pip install "$package" &> /dev/null; then
        echo -e "${GREEN}✓${NC}"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}✗${NC}"
        ((TESTS_FAILED++))
    fi
done

deactivate
rm -rf "$TEMP_VENV"
echo ""

# 10. Summary
echo -e "${BLUE}=== Test Summary ===${NC}"
echo -e "Tests passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Tests failed: ${RED}$TESTS_FAILED${NC}"
echo -e "Warnings: ${YELLOW}${#WARNINGS[@]}${NC}"

if [ ${#WARNINGS[@]} -gt 0 ]; then
    echo -e "\n${YELLOW}Warnings:${NC}"
    for warning in "${WARNINGS[@]}"; do
        echo "  - $warning"
    done
fi

echo ""
if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All critical tests passed! System appears ready for Ubuntu 24.04.${NC}"
    exit 0
else
    echo -e "${RED}✗ Some tests failed. Please address the issues above.${NC}"
    exit 1
fi
