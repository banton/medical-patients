#!/bin/bash
# Script to run different test suites

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if virtual environment is activated (skip in CI)
if [[ -z "${VIRTUAL_ENV}" ]] && [[ -z "${CI}" ]]; then
    print_warning "Virtual environment not activated. Activating .venv..."
    if [ -f .venv/bin/activate ]; then
        source .venv/bin/activate
    else
        print_error "Virtual environment not found. Please run: python -m venv .venv"
        exit 1
    fi
elif [[ -n "${CI}" ]]; then
    print_info "Running in CI environment, skipping virtual environment check"
fi

# Parse command line arguments
TEST_TYPE="${1:-all}"
EXTRA_ARGS="${@:2}"

# Function to check if server is running
check_server() {
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/docs | grep -q "200"; then
        return 0
    else
        return 1
    fi
}

# Function to check if Docker is running
check_docker() {
    if docker info >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

case "$TEST_TYPE" in
    unit)
        print_info "Running unit tests..."
        pytest tests/ -m "unit" ${EXTRA_ARGS}
        ;;
    
    integration)
        print_info "Running integration tests..."
        
        # Check if Docker is available for testcontainers
        if check_docker; then
            print_info "Docker is running. Running database integration tests..."
            pytest tests/test_db_integration.py -v ${EXTRA_ARGS}
        else
            print_warning "Docker not running. Skipping database integration tests."
        fi
        
        # Check if server is running for API tests
        if check_server; then
            print_info "Server is running. Running API integration tests..."
            pytest tests/test_simple_api.py tests/test_api_standardization.py -v ${EXTRA_ARGS}
        else
            print_warning "Server not running. Starting server for API tests..."
            # Start server in background
            PYTHONPATH=. python src/main.py &
            SERVER_PID=$!
            
            # Wait for server to start
            sleep 5
            
            if check_server; then
                pytest tests/test_simple_api.py tests/test_api_standardization.py -v ${EXTRA_ARGS}
                # Stop server
                kill $SERVER_PID 2>/dev/null || true
            else
                print_error "Failed to start server"
                kill $SERVER_PID 2>/dev/null || true
                exit 1
            fi
        fi
        ;;
    
    e2e)
        print_info "Running end-to-end tests..."
        
        # E2E tests require both server and Docker
        if ! check_server; then
            print_error "Server not running. Please start the server first: make dev"
            exit 1
        fi
        
        pytest tests/test_e2e_flows.py -v -m "e2e" ${EXTRA_ARGS}
        ;;
    
    db)
        print_info "Running database tests with testcontainers..."
        
        if ! check_docker; then
            print_error "Docker not running. Database tests require Docker."
            exit 1
        fi
        
        pytest tests/test_db_integration.py -v ${EXTRA_ARGS}
        ;;
    
    api)
        print_info "Running API tests..."
        
        if ! check_server; then
            print_error "Server not running. Please start the server first: make dev"
            exit 1
        fi
        
        pytest tests/test_simple_api.py tests/test_api_standardization.py -v ${EXTRA_ARGS}
        ;;
    
    timeline)
        print_info "Running timeline viewer tests..."
        
        # Check if timeline viewer dependencies are installed
        if [ ! -d "patient-timeline-viewer/node_modules" ]; then
            print_warning "Timeline viewer dependencies not found. Installing..."
            cd patient-timeline-viewer && npm install && cd ..
        fi
        
        # Build timeline viewer as a test
        print_info "Testing timeline viewer build..."
        cd patient-timeline-viewer && npm run build && cd ..
        print_info "Timeline viewer tests passed!"
        ;;
    
    frontend)
        print_info "Running all frontend tests..."
        
        # Run main frontend tests
        print_info "Running main frontend tests..."
        npm run test:ui || true
        
        # Run timeline viewer tests
        print_info "Running timeline viewer tests..."
        if [ ! -d "patient-timeline-viewer/node_modules" ]; then
            print_warning "Timeline viewer dependencies not found. Installing..."
            cd patient-timeline-viewer && npm install && cd ..
        fi
        cd patient-timeline-viewer && npm run build && cd ..
        print_info "All frontend tests completed!"
        ;;
    
    quick)
        print_info "Running quick tests (no Docker/server required)..."
        pytest tests/ -m "not requires_docker and not integration and not e2e" ${EXTRA_ARGS}
        ;;
    
    all)
        print_info "Running all tests..."
        
        # Run unit tests first
        print_info "Running unit tests..."
        pytest tests/ -m "unit" || true
        
        # Run integration tests if dependencies are available
        if check_docker; then
            print_info "Running database integration tests..."
            pytest tests/test_db_integration.py -v || true
        fi
        
        if check_server; then
            print_info "Running API and E2E tests..."
            pytest tests/test_simple_api.py tests/test_api_standardization.py tests/test_e2e_flows.py -v || true
        else
            print_warning "Server not running. Skipping API and E2E tests."
        fi
        
        # Run frontend tests
        print_info "Running frontend tests..."
        npm run test:ui || true
        
        # Test timeline viewer build
        print_info "Testing timeline viewer..."
        if [ ! -d "patient-timeline-viewer/node_modules" ]; then
            print_warning "Timeline viewer dependencies not found. Installing..."
            cd patient-timeline-viewer && npm install && cd ..
        fi
        cd patient-timeline-viewer && npm run build && cd .. || true
        ;;
    
    *)
        echo "Usage: $0 [unit|integration|e2e|db|api|timeline|frontend|quick|all] [pytest arguments]"
        echo ""
        echo "Test types:"
        echo "  unit        - Run unit tests only"
        echo "  integration - Run integration tests (database + API)"
        echo "  e2e         - Run end-to-end tests"
        echo "  db          - Run database tests with testcontainers"
        echo "  api         - Run API integration tests"
        echo "  timeline    - Run timeline viewer tests"
        echo "  frontend    - Run all frontend tests"
        echo "  quick       - Run tests that don't require external services"
        echo "  all         - Run all available tests"
        echo ""
        echo "Examples:"
        echo "  $0 unit                    # Run unit tests"
        echo "  $0 integration -k config   # Run integration tests matching 'config'"
        echo "  $0 e2e --maxfail=1        # Run E2E tests, stop on first failure"
        exit 1
        ;;
esac

print_info "Tests completed!"