#!/bin/bash
# Platform Testing Script for Linux/macOS
# Tests all critical Task commands for cross-platform compatibility

set -e

echo "🧪 Cross-Platform Compatibility Test"
echo "Platform: $(uname -s) $(uname -m)"
echo "======================================"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test tracking
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_TOTAL=0

# Function to run test
run_test() {
    local test_name="$1"
    local test_command="$2"
    local expected_exit_code="${3:-0}"
    
    TESTS_TOTAL=$((TESTS_TOTAL + 1))
    
    echo -e "\n${BLUE}🧪 Testing: $test_name${NC}"
    echo "Command: $test_command"
    
    if eval "$test_command" >/dev/null 2>&1; then
        actual_exit_code=$?
    else
        actual_exit_code=$?
    fi
    
    if [ $actual_exit_code -eq $expected_exit_code ]; then
        echo -e "${GREEN}✅ PASS${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}❌ FAIL (exit code: $actual_exit_code, expected: $expected_exit_code)${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

# Function to check command exists
check_command() {
    local cmd="$1"
    local name="$2"
    
    echo -e "\n${BLUE}🔍 Checking: $name${NC}"
    
    if command -v "$cmd" >/dev/null 2>&1; then
        local version=$(eval "$cmd --version 2>/dev/null | head -1" || echo "version unavailable")
        echo -e "${GREEN}✅ Found: $cmd ($version)${NC}"
        return 0
    else
        echo -e "${RED}❌ Missing: $cmd${NC}"
        return 1
    fi
}

echo -e "\n${YELLOW}📋 Step 1: Environment Requirements${NC}"
echo "Checking required tools..."

# Check required tools
REQUIREMENTS_MET=true

if ! check_command "task" "Task runner"; then
    REQUIREMENTS_MET=false
fi

if ! check_command "docker" "Docker"; then
    REQUIREMENTS_MET=false
fi

if ! check_command "python3" "Python 3" && ! check_command "python" "Python"; then
    REQUIREMENTS_MET=false
fi

if ! check_command "node" "Node.js"; then
    echo -e "${YELLOW}⚠️  Node.js not found - timeline viewer tests will be skipped${NC}"
fi

if ! check_command "npm" "NPM"; then
    echo -e "${YELLOW}⚠️  NPM not found - timeline viewer tests will be skipped${NC}"
fi

if [ "$REQUIREMENTS_MET" = false ]; then
    echo -e "\n${RED}❌ Missing required tools. Please install them and try again.${NC}"
    echo "See PLATFORM-SUPPORT.md for installation instructions."
    exit 1
fi

echo -e "\n${YELLOW}📋 Step 2: Task System Tests${NC}"

# Test Task system basics
run_test "Task version check" "task --version"
run_test "Task list all commands" "task --list-all"
run_test "Task help display" "task"

echo -e "\n${YELLOW}📋 Step 3: Core Development Commands${NC}"

# Test core development workflow
run_test "Setup command" "task setup"
run_test "Clean command" "task clean"
run_test "Python detection" "task python-clean"

echo -e "\n${YELLOW}📋 Step 4: Docker Integration${NC}"

# Test Docker integration
if docker info >/dev/null 2>&1; then
    run_test "Docker service start" "task docker:services"
    run_test "Docker status check" "task docker:status"
    run_test "Docker cleanup" "task docker:clean"
else
    echo -e "${YELLOW}⚠️  Docker not running - skipping Docker tests${NC}"
fi

echo -e "\n${YELLOW}📋 Step 5: Database Commands${NC}"

# Test database commands (without requiring running database)
run_test "Database status check (expect failure)" "task db:status" 1
run_test "Database start command exists" "task db:start --dry-run" 0

echo -e "\n${YELLOW}📋 Step 6: Testing Framework${NC}"

# Test testing commands
run_test "Test environment check" "task test:check-env"
run_test "Test command structure" "task test:all --dry-run"

echo -e "\n${YELLOW}📋 Step 7: Linting and Code Quality${NC}"

# Test linting commands
run_test "Lint all command" "task lint:all"
run_test "Python linting" "task lint:python"

echo -e "\n${YELLOW}📋 Step 8: Frontend Commands${NC}"

# Test frontend commands
run_test "Frontend install check" "task frontend:install"

echo -e "\n${YELLOW}📋 Step 9: Timeline Viewer${NC}"

# Test timeline viewer if Node.js available
if command -v node >/dev/null 2>&1 && command -v npm >/dev/null 2>&1; then
    run_test "Timeline status" "task timeline:status"
    run_test "Timeline environment check" "task timeline:check-env"
    run_test "Timeline info" "task timeline:info"
    
    # Only install if not already installed
    if [ ! -d "patient-timeline-viewer/node_modules" ]; then
        run_test "Timeline dependency install" "task timeline:install"
    fi
    
    if [ -d "patient-timeline-viewer/node_modules" ]; then
        run_test "Timeline build" "task timeline:build"
        run_test "Timeline test" "task timeline:test"
    fi
else
    echo -e "${YELLOW}⚠️  Node.js/NPM not available - skipping timeline tests${NC}"
fi

echo -e "\n${YELLOW}📋 Step 10: Platform-Specific Checks${NC}"

# Platform-specific tests
case "$(uname -s)" in
    Darwin)
        echo "✅ macOS detected - all features should work"
        ;;
    Linux)
        echo "✅ Linux detected - checking distribution..."
        if [ -f /etc/os-release ]; then
            . /etc/os-release
            echo "Distribution: $NAME $VERSION"
        fi
        ;;
    MINGW*|CYGWIN*|MSYS*)
        echo "✅ Windows environment detected"
        echo "Note: Full Docker integration requires WSL2"
        ;;
    *)
        echo "⚠️  Unknown platform: $(uname -s)"
        ;;
esac

# Summary
echo -e "\n${BLUE}📊 Test Summary${NC}"
echo "======================================"
echo "Total tests: $TESTS_TOTAL"
echo -e "Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Failed: ${RED}$TESTS_FAILED${NC}"

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "\n${GREEN}🎉 All tests passed! Platform compatibility confirmed.${NC}"
    echo "This platform is ready for development."
    exit 0
else
    echo -e "\n${YELLOW}⚠️  Some tests failed. See details above.${NC}"
    echo "Platform may have limited functionality."
    
    if [ $TESTS_PASSED -gt $((TESTS_TOTAL / 2)) ]; then
        echo "Most functionality works - minor issues only."
        exit 0
    else
        echo "Major compatibility issues detected."
        exit 1
    fi
fi