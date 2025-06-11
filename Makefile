# Military Medical Exercise Patient Generator - Makefile
# Provides common development commands for easier workflow

.PHONY: help dev test lint format clean build-frontend api-test deps migrate timeline-viewer

# Default target - show help
help:
	@echo "Military Medical Exercise Patient Generator - Development Commands"
	@echo ""
	@echo "Available commands:"
	@echo "  make dev          - Start development environment (DB + App)"
	@echo "  make dev-with-data - Start development environment with test data"
	@echo "  make dev-clean    - Start development environment (clean build)"
	@echo "  make dev-fast     - Start development environment (skip tests)"
	@echo "  make test         - Run all tests"
	@echo "  make test-cache   - Run cache-specific tests"
	@echo "  make api-test     - Run API integration tests"
	@echo "  make lint         - Run linting checks"
	@echo "  make format       - Format code automatically"
	@echo "  make clean        - Clean up generated files and cache"
	@echo "  make build-frontend - Build all frontend components"
	@echo "  make timeline-viewer - Start React timeline viewer"
	@echo "  make timeline-dev   - Start timeline viewer in development mode"
	@echo "  make timeline-build - Build timeline viewer for production"
	@echo "  make timeline-test  - Test timeline viewer"
	@echo "  make deps         - Install all dependencies"
	@echo "  make migrate      - Run database migrations"
	@echo "  make services     - Start database and Redis services"
	@echo "  make cache-flush  - Flush Redis cache"
	@echo "  make cache-info   - Show Redis cache information"
	@echo "  make verify-redis - Verify Redis integration across all components"
	@echo ""
	@echo "Quick start: make deps && make dev"

# Start development environment
dev:
	@echo "Starting development environment..."
	@chmod +x start-dev.sh && ./start-dev.sh

# Start development environment with test data
dev-with-data:
	@echo "Starting development environment with test data..."
	@chmod +x start-dev.sh && ./start-dev.sh --test-data

# Start development environment (clean build)
dev-clean:
	@echo "Starting development environment (clean build)..."
	@chmod +x start-dev.sh && ./start-dev.sh --clean

# Start development environment (skip self-tests)
dev-fast:
	@echo "Starting development environment (skip tests)..."
	@chmod +x start-dev.sh && ./start-dev.sh --skip-tests

# Run all tests
test:
	@echo "Running all tests..."
	./run_tests.sh all

# Run unit tests only
test-unit:
	@echo "Running unit tests..."
	./run_tests.sh unit

# Run integration tests (database + API)
test-integration:
	@echo "Running integration tests..."
	./run_tests.sh integration

# Run end-to-end tests
test-e2e:
	@echo "Running end-to-end tests..."
	./run_tests.sh e2e

# Run database tests with testcontainers
test-db:
	@echo "Running database tests..."
	./run_tests.sh db

# Run API tests
test-api:
	@echo "Running API tests..."
	./run_tests.sh api

# Run UI integration tests
test-ui:
	@echo "Running UI integration tests..."
	npm run test:ui

# Run UI end-to-end tests (requires running server)
test-ui-e2e:
	@echo "Running UI end-to-end tests..."
	@echo "NOTE: Requires server running (make dev)"
	python -m pytest tests/test_ui_e2e.py -v

# Run quick tests (no external dependencies)
test-quick:
	@echo "Running quick tests..."
	./run_tests.sh quick

# Run cache-specific tests
test-cache:
	@echo "Running cache tests..."
	python -m pytest tests/test_cache_service.py tests/test_cached_services.py -xvs

# Run tests in Docker containers
test-docker:
	@echo "Running tests in Docker containers..."
	docker compose -f docker-compose.test.yml up --build --abort-on-container-exit --exit-code-from test-runner

# Run integration tests in Docker
test-docker-integration:
	@echo "Starting test environment..."
	docker compose -f docker-compose.test.yml up -d test-db test-redis test-integration
	@echo "Waiting for services to be ready..."
	@sleep 10
	@echo "Running integration tests..."
	python -m pytest tests/test_simple_api.py tests/test_api_standardization.py tests/test_e2e_flows.py -v --base-url=http://localhost:8001
	@echo "Cleaning up..."
	docker compose -f docker-compose.test.yml down

# Clean test containers and volumes
test-clean:
	@echo "Cleaning test containers and volumes..."
	docker compose -f docker-compose.test.yml down -v

# Run linting
lint:
	@echo "Running linting checks..."
	@echo "Python linting with Ruff..."
	@ruff check src/ patient_generator/ || true
	@echo "Python type checking with mypy..."
	@mypy src/ patient_generator/ --ignore-missing-imports || true
	@echo "JavaScript linting with ESLint..."
	@npm run lint:check || true

# Format code
format:
	@echo "Formatting code..."
	@echo "Python formatting with Ruff..."
	@ruff format src/ patient_generator/
	@echo "JavaScript/CSS/HTML formatting with Prettier..."
	@npm run format

# Run all linting and formatting checks (CI mode)
lint-ci:
	@echo "Running CI linting checks..."
	@ruff check src/ patient_generator/ --exit-non-zero-on-fix
	@mypy src/ patient_generator/ --ignore-missing-imports
	@npm run lint:check
	@npm run format:check

# Install linting and formatting tools
install-lint-tools:
	@echo "Installing Python linting tools..."
	@pip install ruff mypy types-requests
	@echo "Installing JavaScript linting tools..."
	@npm install
	@echo "Installing pre-commit hooks..."
	@pip install pre-commit
	@pre-commit install

# Run pre-commit on all files
pre-commit-all:
	@echo "Running pre-commit on all files..."
	@pre-commit run --all-files

# Clean up generated files
clean:
	@echo "Cleaning up..."
	docker compose down -v 2>/dev/null || true
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf output/job_* 2>/dev/null || true
	rm -rf temp/* 2>/dev/null || true
	rm -rf .pytest_cache 2>/dev/null || true
	rm -rf .mypy_cache 2>/dev/null || true
	rm -rf node_modules/.cache 2>/dev/null || true
	rm -rf patient-timeline-viewer/dist 2>/dev/null || true
	rm -rf patient-timeline-viewer/node_modules/.cache 2>/dev/null || true
	@echo "Cleanup complete!"

# Build frontend components
build-frontend:
	@echo "Building frontend components..."
	npm run build:all-frontend
	@echo "Building timeline viewer..."
	@cd patient-timeline-viewer && npm run build

# Build individual frontend components
build-viz:
	npm run build:viz-dashboard

build-config:
	npm run build:config-panel

build-military:
	npm run build:military-dashboard

# Install dependencies
deps:
	@echo "Installing dependencies..."
	pip install -r requirements.txt
	npm install
	@echo "Installing timeline viewer dependencies..."
	@cd patient-timeline-viewer && npm install
	@echo "Dependencies installed!"

# Run database migrations
migrate:
	@echo "Running database migrations..."
	alembic upgrade head

# Create a new migration
migrate-create:
	@echo "Creating new migration..."
	@read -p "Enter migration message: " msg; \
	alembic revision --autogenerate -m "$$msg"

# Database shell
db-shell:
	@echo "Connecting to database..."
	docker compose exec db psql -U medgen_user -d medgen_db

# Start only the database
db:
	@echo "Starting database..."
	docker compose up -d db
	@echo "Database started on localhost:5432"

# Start only Redis
redis:
	@echo "Starting Redis..."
	docker compose up -d redis
	@echo "Redis started on localhost:6379"

# Start database and Redis
services:
	@echo "Starting database and Redis..."
	docker compose up -d db redis
	@echo "Services started: database (5432), Redis (6379)"

# Run the application without docker
run:
	@echo "Starting application..."
	PYTHONPATH=. python src/main.py

# Watch for changes and restart (requires watchdog)
watch:
	@command -v watchmedo >/dev/null 2>&1 || (echo "Installing watchdog..." && pip install watchdog)
	watchmedo auto-restart -d src -d patient_generator -p "*.py" -- python src/main.py

# Generate test data
generate-test:
	@echo "Generating test patients..."
	curl -X POST http://localhost:8000/api/v1/generation/ \
		-H "X-API-Key: your_secret_api_key_here" \
		-H "Content-Type: application/json" \
		-d '{"configuration": {"count": 10}, "output_formats": ["json"], "use_compression": false}'

# Check code quality
quality: lint test
	@echo "Code quality checks passed!"

# Redis cache management
cache-flush:
	@echo "Flushing Redis cache..."
	docker compose exec redis redis-cli FLUSHDB
	@echo "Cache flushed!"

cache-info:
	@echo "Redis cache information:"
	docker compose exec redis redis-cli INFO memory
	docker compose exec redis redis-cli DBSIZE

# Docker compose shortcuts
up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f app

ps:
	docker compose ps

# Development database operations
db-reset: down
	@echo "Resetting database..."
	docker volume rm medical-patients_postgres_data 2>/dev/null || true
	docker compose up -d db
	sleep 5
	alembic upgrade head
	@echo "Database reset complete!"

# Production build
build-prod:
	@echo "Building for production..."
	docker build -t medical-patient-generator:latest .
	npm run build:all-frontend
	@echo "Production build complete!"

# Environment setup check
check-env:
	@echo "Checking environment setup..."
	@command -v python3 >/dev/null 2>&1 && echo "✓ Python installed" || echo "✗ Python not found"
	@command -v node >/dev/null 2>&1 && echo "✓ Node.js installed" || echo "✗ Node.js not found"
	@command -v docker >/dev/null 2>&1 && echo "✓ Docker installed" || echo "✗ Docker not found"
	@command -v alembic >/dev/null 2>&1 && echo "✓ Alembic installed" || echo "✗ Alembic not found"
	@test -f .env && echo "✓ .env file exists" || echo "✗ .env file not found (using defaults)"
	@echo ""
	@echo "Database URL: postgresql://medgen_user:medgen_password@localhost:5432/medgen_db"
	@echo "API Key: your_secret_api_key_here"

# Verify Redis integration
verify-redis:
	@echo "Verifying Redis integration..."
	python verify-redis-integration.py

# React Timeline Viewer Commands
timeline-viewer:
	@echo "Starting React timeline viewer..."
	@cd patient-timeline-viewer && npm run dev

timeline-dev:
	@echo "Starting timeline viewer in development mode..."
	@cd patient-timeline-viewer && npm run dev

timeline-build:
	@echo "Building timeline viewer for production..."
	@cd patient-timeline-viewer && npm run build

timeline-test:
	@echo "Testing timeline viewer..."
	@cd patient-timeline-viewer && npm run build
	@echo "Timeline viewer build successful!"

timeline-deps:
	@echo "Installing timeline viewer dependencies..."
	@cd patient-timeline-viewer && npm install
	@echo "Timeline viewer dependencies installed!"

timeline-clean:
	@echo "Cleaning timeline viewer build files..."
	@cd patient-timeline-viewer && rm -rf dist node_modules/.cache
	@echo "Timeline viewer cleaned!"

# Start both backend and timeline viewer
dev-full:
	@echo "Starting full development environment (backend + timeline viewer)..."
	@echo "Starting backend on port 8000..."
	@chmod +x start-dev.sh && ./start-dev.sh --skip-tests &
	@echo "Waiting for backend to start..."
	@sleep 10
	@echo "Starting timeline viewer on port 5174..."
	@cd patient-timeline-viewer && npm run dev