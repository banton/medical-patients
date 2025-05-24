# Military Medical Exercise Patient Generator - Makefile
# Provides common development commands for easier workflow

.PHONY: help dev test lint format clean build-frontend api-test deps migrate

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
	@echo "  make api-test     - Run API integration tests"
	@echo "  make lint         - Run linting checks"
	@echo "  make format       - Format code automatically"
	@echo "  make clean        - Clean up generated files and cache"
	@echo "  make build-frontend - Build all frontend components"
	@echo "  make deps         - Install all dependencies"
	@echo "  make migrate      - Run database migrations"
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
test: test-unit api-test
	@echo "All tests completed!"

# Run unit tests
test-unit:
	@echo "Running unit tests..."
	python -m pytest tests/ -xvs

# Run API integration tests (requires running server)
api-test:
	@echo "Running API integration tests..."
	@echo "Ensure the server is running (make dev in another terminal)"
	python -m pytest tests_api.py -xvs

# Run linting
lint:
	@echo "Running linting checks..."
	@command -v ruff >/dev/null 2>&1 && ruff check src/ patient_generator/ || echo "Ruff not installed, skipping Python linting"
	@command -v mypy >/dev/null 2>&1 && mypy src/ patient_generator/ --ignore-missing-imports || echo "Mypy not installed, skipping type checking"
	@command -v npx >/dev/null 2>&1 && npx tsc --noEmit || echo "TypeScript not installed, skipping TS checking"

# Format code
format:
	@echo "Formatting code..."
	@command -v ruff >/dev/null 2>&1 && ruff format src/ patient_generator/ || echo "Ruff not installed, skipping Python formatting"
	@command -v npx >/dev/null 2>&1 && npx prettier --write "static/**/*.{js,jsx,ts,tsx,json,css,html}" || echo "Prettier not installed, skipping JS/TS formatting"

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
	@echo "Cleanup complete!"

# Build frontend components
build-frontend:
	@echo "Building frontend components..."
	npm run build:all-frontend

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
	curl -X POST http://localhost:8000/api/generate \
		-H "X-API-Key: your_secret_api_key_here" \
		-H "Content-Type: application/json" \
		-d '{"configuration_id": "test", "output_formats": ["json"], "use_compression": false}'

# Check code quality
quality: lint test
	@echo "Code quality checks passed!"

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