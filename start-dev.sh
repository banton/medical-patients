#!/bin/bash

# Medical Patient Generator - Enhanced Development Environment Setup
# This script sets up the development environment with hardening and self-testing
# Compatible with the refactored domain-driven architecture

# Exit on any error and enable strict error handling
set -euo pipefail

# Logging and color support
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="docker-compose.dev.yml"
API_KEY="${API_KEY:-your_secret_api_key_here}"
MAX_HEALTH_RETRIES=30
HEALTH_CHECK_INTERVAL=5
TEST_TIMEOUT=60

# Utility functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

log_step() {
    echo -e "${PURPLE}🚀 $1${NC}"
    echo "$(printf '%.0s-' {1..70})"
}

# Check prerequisites
check_prerequisites() {
    log_step "Checking Prerequisites"
    
    local missing_deps=()
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        missing_deps+=("docker")
    fi
    
    # Check Docker Compose
    if ! command -v docker compose &> /dev/null && ! command -v docker-compose &> /dev/null; then
        missing_deps+=("docker-compose")
    fi
    
    # Check Node.js
    if ! command -v node &> /dev/null; then
        missing_deps+=("node")
    fi
    
    # Check npm
    if ! command -v npm &> /dev/null; then
        missing_deps+=("npm")
    fi
    
    # Check Python
    if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
        missing_deps+=("python")
    fi
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        log_error "Missing required dependencies: ${missing_deps[*]}"
        log_info "Please install the missing dependencies and try again"
        exit 1
    fi
    
    # Check Docker daemon
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running. Please start Docker and try again."
        exit 1
    fi
    
    log_success "All prerequisites are met"
}

# Environment validation
validate_environment() {
    log_step "Validating Environment"
    
    # Check if we're in the correct directory
    if [[ ! -f "package.json" ]] || [[ ! -f "requirements.txt" ]] || [[ ! -f "$COMPOSE_FILE" ]]; then
        log_error "This script must be run from the project root directory"
        log_info "Expected files: package.json, requirements.txt, $COMPOSE_FILE"
        exit 1
    fi
    
    # Check for critical configuration files
    if [[ ! -f "alembic.ini" ]]; then
        log_error "alembic.ini not found - database migrations may not work"
        exit 1
    fi
    
    if [[ ! -d "src" ]]; then
        log_error "src/ directory not found - new architecture not detected"
        exit 1
    fi
    
    # Validate API key
    if [[ "$API_KEY" == "your_secret_api_key_here" ]]; then
        log_warning "Using default API key - change API_KEY environment variable for production"
    fi
    
    log_success "Environment validation passed"
}

# Clean up previous runs
cleanup_previous_run() {
    log_step "Cleaning Up Previous Runs"
    
    # Stop and remove existing containers
    if docker compose -f "$COMPOSE_FILE" ps -q | grep -q .; then
        log_info "Stopping existing containers..."
        docker compose -f "$COMPOSE_FILE" down --remove-orphans
    fi
    
    # Clean up Docker build cache (optional)
    if [[ "${CLEAN_DOCKER_CACHE:-false}" == "true" ]]; then
        log_info "Cleaning Docker build cache..."
        docker builder prune -f || true
    fi
    
    # Clean up temporary files
    log_info "Cleaning temporary files..."
    rm -rf temp/* 2>/dev/null || true
    rm -rf output/job_* 2>/dev/null || true
    find . -name "*.pyc" -delete 2>/dev/null || true
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    
    log_success "Cleanup completed"
}

# Install and update dependencies
install_dependencies() {
    log_step "Installing Dependencies"
    
    # Frontend dependencies
    log_info "Installing/updating frontend dependencies..."
    npm ci --silent
    log_success "Frontend dependencies installed"
    
    # Check for Python dependencies (for local development)
    if [[ "${INSTALL_PYTHON_DEPS:-false}" == "true" ]]; then
        log_info "Installing Python dependencies locally..."
        if command -v pip &> /dev/null; then
            pip install -r requirements.txt --quiet
            log_success "Python dependencies installed"
        else
            log_warning "pip not found - skipping Python dependencies (will use Docker)"
        fi
    fi
}

# Build frontend assets
build_frontend() {
    log_step "Building Frontend Assets"
    
    log_info "Building all frontend components..."
    npm run build:all-frontend
    
    # Verify build outputs
    if [[ ! -d "static/dist" ]]; then
        log_error "Frontend build failed - static/dist directory not created"
        exit 1
    fi
    
    # Check for key build artifacts
    local expected_files=("static/dist/config-panel.js" "static/dist/visualization-dashboard.js")
    for file in "${expected_files[@]}"; do
        if [[ ! -f "$file" ]]; then
            log_warning "Expected build artifact not found: $file"
        fi
    done
    
    log_success "Frontend assets built successfully"
}

# Start Docker services
start_services() {
    log_step "Starting Docker Services"
    
    log_info "Starting PostgreSQL and Backend services..."
    docker compose -f "$COMPOSE_FILE" up --build -d
    
    log_info "Services started, waiting for health checks..."
    wait_for_services
}

# Wait for services to be healthy
wait_for_services() {
    local retry_count=0
    
    log_info "Waiting for services to become healthy (max ${MAX_HEALTH_RETRIES} attempts)..."
    
    while [[ $retry_count -lt $MAX_HEALTH_RETRIES ]]; do
        if docker compose -f "$COMPOSE_FILE" ps app | grep -Eiq 'healthy'; then
            log_success "Application service is healthy"
            return 0
        fi
        
        retry_count=$((retry_count + 1))
        log_info "Health check $retry_count/$MAX_HEALTH_RETRIES - waiting ${HEALTH_CHECK_INTERVAL}s..."
        sleep $HEALTH_CHECK_INTERVAL
    done
    
    # Health check failed
    log_error "Services failed to become healthy within timeout"
    log_info "Service status:"
    docker compose -f "$COMPOSE_FILE" ps
    
    log_info "Application logs:"
    docker compose -f "$COMPOSE_FILE" logs --tail=50 app
    
    log_info "Database logs:"
    docker compose -f "$COMPOSE_FILE" logs --tail=20 db
    
    exit 1
}

# Run database migrations
run_migrations() {
    log_step "Running Database Migrations"
    
    log_info "Applying Alembic migrations..."
    if ! docker compose -f "$COMPOSE_FILE" exec -T app alembic upgrade head; then
        log_error "Database migration failed"
        log_info "Database logs:"
        docker compose -f "$COMPOSE_FILE" logs db
        exit 1
    fi
    
    log_success "Database migrations completed"
}

# Self-testing functionality
run_self_tests() {
    log_step "Running Self-Tests"
    
    local base_url="http://localhost:8000"
    
    # Test 1: Health endpoint
    log_info "Testing health endpoint..."
    if timeout $TEST_TIMEOUT curl -sf "$base_url/health" &>/dev/null; then
        log_success "Health endpoint responsive"
    else
        log_error "Health endpoint failed"
        return 1
    fi
    
    # Test 2: API documentation
    log_info "Testing API documentation..."
    if timeout $TEST_TIMEOUT curl -sf "$base_url/docs" &>/dev/null; then
        log_success "API documentation accessible"
    else
        log_warning "API documentation not accessible"
    fi
    
    # Test 3: Static assets
    log_info "Testing static assets..."
    if timeout $TEST_TIMEOUT curl -sf "$base_url/static/index.html" &>/dev/null; then
        log_success "Main UI accessible"
    else
        log_error "Main UI not accessible"
        return 1
    fi
    
    # Test 4: API with authentication
    log_info "Testing authenticated API endpoint..."
    if timeout $TEST_TIMEOUT curl -sf -H "X-API-Key: $API_KEY" "$base_url/api/v1/configurations/reference/nationalities/" &>/dev/null; then
        log_success "Authenticated API endpoints working"
    else
        log_error "Authenticated API endpoints failed"
        return 1
    fi
    
    # Test 5: Database connectivity (via API)
    log_info "Testing database connectivity..."
    if timeout $TEST_TIMEOUT curl -sf -H "X-API-Key: $API_KEY" "$base_url/api/v1/configurations/" &>/dev/null; then
        log_success "Database connectivity confirmed"
    else
        log_error "Database connectivity failed"
        return 1
    fi
    
    log_success "All self-tests passed!"
    return 0
}

# Performance and security checks
run_hardening_checks() {
    log_step "Running Hardening Checks"
    
    # Check for default credentials
    if [[ "$API_KEY" == "your_secret_api_key_here" ]]; then
        log_warning "SECURITY: Default API key detected - change for production!"
    fi
    
    # Check Docker resource limits
    local memory_limit=$(docker compose -f "$COMPOSE_FILE" config | grep -A5 "deploy:" | grep "memory:" | head -1 || echo "")
    if [[ -z "$memory_limit" ]]; then
        log_warning "PERFORMANCE: No memory limits set for containers"
    fi
    
    # Check for development-only configurations
    if docker compose -f "$COMPOSE_FILE" config | grep -q "DEBUG.*true"; then
        log_info "DEBUG mode enabled (appropriate for development)"
    fi
    
    # Check database connection security
    if docker compose -f "$COMPOSE_FILE" config | grep -q "sslmode=disable"; then
        log_warning "SECURITY: Database SSL disabled (appropriate for development)"
    fi
    
    log_success "Hardening checks completed"
}

# Generate development data (optional)
generate_test_data() {
    if [[ "${GENERATE_TEST_DATA:-false}" == "true" ]]; then
        log_step "Generating Test Data"
        
        local base_url="http://localhost:8000"
        
        log_info "Creating test configuration..."
        local config_response
        config_response=$(curl -sf -X POST "$base_url/api/v1/configurations/" \
            -H "X-API-Key: $API_KEY" \
            -H "Content-Type: application/json" \
            -d '{
                "name": "Development Test Configuration",
                "description": "Auto-generated test configuration for development",
                "total_patients": 5,
                "front_configs": [{
                    "id": "dev-front",
                    "name": "Development Front",
                    "casualty_rate": 1.0,
                    "nationality_distribution": [{"nationality_code": "USA", "percentage": 100.0}]
                }],
                "facility_configs": [{
                    "id": "POI",
                    "name": "Point of Injury",
                    "kia_rate": 0.1,
                    "rtd_rate": 0.0
                }],
                "injury_distribution": {
                    "Disease": 50.0,
                    "Non-Battle Injury": 30.0,
                    "Battle Injury": 20.0
                }
            }' 2>/dev/null) || {
            log_warning "Failed to create test configuration"
            return 0
        }
        
        local config_id
        config_id=$(echo "$config_response" | grep -o '"id":"[^"]*"' | cut -d'"' -f4)
        
        if [[ -n "$config_id" ]]; then
            log_info "Generating test patients with configuration: $config_id"
            curl -sf -X POST "$base_url/api/generate" \
                -H "X-API-Key: $API_KEY" \
                -H "Content-Type: application/json" \
                -d "{\"configuration_id\": \"$config_id\", \"output_formats\": [\"json\"]}" &>/dev/null || {
                log_warning "Failed to generate test patients"
                return 0
            }
            log_success "Test data generation initiated"
        fi
    fi
}

# Print startup summary
print_summary() {
    log_step "Development Environment Ready!"
    
    echo -e "${CYAN}"
    echo "🔗 Application URLs:"
    echo "   • Main Application:      http://localhost:8000/static/index.html"
    echo "   • Visualization Dashboard: http://localhost:8000/static/visualizations.html"
    echo "   • API Documentation:     http://localhost:8000/docs"
    echo "   • Alternative API Docs:  http://localhost:8000/redoc"
    echo "   • Health Check:          http://localhost:8000/health"
    echo ""
    echo "🔑 Authentication:"
    echo "   • API Key: $API_KEY"
    echo ""
    echo "🛠️  Development Commands:"
    echo "   • View logs:            make logs"
    echo "   • Run tests:            make test"
    echo "   • Stop services:        make down"
    echo "   • Clean restart:        make clean && make dev"
    echo "   • Generate test data:   make generate-test"
    echo ""
    echo "📊 Service Status:"
    docker compose -f "$COMPOSE_FILE" ps --format="table {{.Service}}\\t{{.Status}}\\t{{.Ports}}"
    echo -e "${NC}"
}

# Cleanup function for script exit
cleanup_on_exit() {
    local exit_code=$?
    if [[ $exit_code -ne 0 ]]; then
        log_error "Setup failed with exit code $exit_code"
        log_info "Logs available via: docker compose -f $COMPOSE_FILE logs"
    fi
}

# Main execution
main() {
    trap cleanup_on_exit EXIT
    
    log_step "Medical Patient Generator - Development Environment Setup"
    log_info "Refactored architecture with hardening and self-testing"
    echo ""
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --clean)
                CLEAN_DOCKER_CACHE=true
                shift
                ;;
            --test-data)
                GENERATE_TEST_DATA=true
                shift
                ;;
            --skip-tests)
                SKIP_SELF_TESTS=true
                shift
                ;;
            --python-deps)
                INSTALL_PYTHON_DEPS=true
                shift
                ;;
            -h|--help)
                echo "Usage: $0 [OPTIONS]"
                echo "Options:"
                echo "  --clean        Clean Docker build cache"
                echo "  --test-data    Generate test data after setup"
                echo "  --skip-tests   Skip self-testing phase"
                echo "  --python-deps  Install Python dependencies locally"
                echo "  -h, --help     Show this help message"
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done
    
    # Execute setup steps
    check_prerequisites
    validate_environment
    cleanup_previous_run
    install_dependencies
    build_frontend
    start_services
    run_migrations
    run_hardening_checks
    
    # Run self-tests unless skipped
    if [[ "${SKIP_SELF_TESTS:-false}" != "true" ]]; then
        if ! run_self_tests; then
            log_error "Self-tests failed - environment may not be fully functional"
            exit 1
        fi
    fi
    
    # Generate test data if requested
    generate_test_data
    
    # Success!
    print_summary
    log_success "Development environment is ready and tested!"
}

# Execute main function with all arguments
main "$@"