# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Essential Commands

### Development Setup

**Quick Start** (Recommended):
```bash
# Start development environment with Docker
make dev

# Check if services are running
curl http://localhost:8000/health

# View application at
# - UI: http://localhost:8000
# - API docs: http://localhost:8000/docs  
# - Advanced visualizations: http://localhost:8000/static/visualizations.html
```

**Manual setup** (if needed):
```bash
docker compose -f docker-compose.dev.yml up -d  # Start all services
docker compose -f docker-compose.dev.yml logs   # View logs
```

**Troubleshooting**:
```bash
# If startup fails, check logs
docker compose -f docker-compose.dev.yml logs app

# Restart services 
docker compose -f docker-compose.dev.yml restart

# Full cleanup and restart
make dev-clean
```

### Running Tests
```bash
# API integration tests (requires running server)
python -m pytest tests_api.py -xvs

# Single test
python -m pytest tests_api.py::TestAPIIntegration::test_05_config_create_valid -xvs

# Frontend tests
npm test

# Unit tests
python -m pytest tests/ -xvs
```

### Building Frontend
```bash
npm run build:all-frontend     # Build all React components
npm run build:viz-dashboard    # Build visualization dashboard only
npm run build:config-panel     # Build configuration panel only
npm run build:military-dashboard # Build military dashboard only
```

### Database Operations
```bash
# Create new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Database connection
postgresql://medgen_user:medgen_password@localhost:5432/medgen_db
```

### Cache Management
```bash
# Start Redis service only
make redis

# Start both database and Redis
make services

# Flush Redis cache
make cache-flush

# View Redis cache information
make cache-info

# Run cache-specific tests
make test-cache
```

### Docker Commands
```bash
docker compose up -d            # Start all services
docker compose down            # Stop all services
docker compose logs -f app     # View application logs
docker compose exec app bash   # Shell into app container
docker compose ps              # Check service status
```

### Linting and Type Checking
```bash
# Python linting (if configured)
ruff check src/ patient_generator/
mypy src/ patient_generator/

# TypeScript checking
npx tsc --noEmit
```

## Architecture Overview

The application follows a clean domain-driven architecture with clear separation of concerns:

### Layer Responsibilities

1. **API Layer (`src/api/v1/`)**
   - FastAPI routers handle HTTP requests
   - Each router corresponds to a domain area (configurations, generation, jobs)
   - Uses dependency injection for services and database access
   - All endpoints require API key authentication (except reference endpoints)

2. **Domain Layer (`src/domain/`)**
   - Contains business logic and domain models
   - Services orchestrate complex operations
   - Repository interfaces define data access contracts
   - Models represent business entities with behavior

3. **Core Layer (`src/core/`)**
   - Cross-cutting concerns like security and exceptions
   - API key validation middleware
   - Custom exception hierarchy for proper error handling

4. **Patient Generator (`patient_generator/`)**
   - Legacy module containing core generation logic
   - ConfigurationManager handles scenario configurations
   - Database class provides PostgreSQL connection pooling
   - Generators create demographics, medical conditions, and FHIR bundles

### Key Design Patterns

1. **Dependency Injection**
   - FastAPI's `Depends` mechanism for injecting services
   - Database connections managed through dependencies
   - Testability through interface injection

2. **Repository Pattern**
   - Data access abstracted behind repository interfaces
   - ConfigurationRepository handles configuration CRUD
   - Job repository manages job state persistence

3. **Service Layer**
   - JobService orchestrates job lifecycle
   - Handles background task coordination
   - Manages file storage and cleanup

4. **Background Tasks**
   - Patient generation runs as background tasks
   - Progress updates through job service
   - Async/await pattern for non-blocking operations

5. **Caching Layer**
   - Redis-based caching for improved performance
   - Demographics and medical conditions data cached
   - Automatic cache warming before patient generation
   - Graceful degradation when Redis is unavailable

### Critical Integration Points

1. **ConfigurationManager vs Direct Database Access**
   - PatientGeneratorApp requires ConfigurationManager with loaded config
   - Cannot pass configuration dict directly
   - For ad-hoc configs, must create temporary database entry

2. **Database Connection Management**
   - Database class uses singleton pattern with connection pooling
   - Always use Database() instance, not Database.get_instance()
   - Connection pool handles concurrent access

3. **File Output Management**
   - Output files stored in `output/job_{job_id}/` directories
   - Temporary files cleaned up automatically
   - ZIP archives created for download endpoints

4. **API Authentication**
   - API key passed via X-API-Key header
   - Default key: "your_secret_api_key_here" (change in production)
   - Reference endpoints don't require authentication

### Common Pitfalls to Avoid

1. **Import Paths**
   - Always set PYTHONPATH to project root
   - Use absolute imports from src/ and patient_generator/
   - Don't use relative imports between modules

2. **Type Annotations**
   - Time estimates in JobProgressDetails must be Dict[str, float]
   - Use Optional for nullable fields
   - Pydantic models use strict type validation

3. **Database Migrations**
   - Always create migrations for schema changes
   - Test rollback before applying to production
   - Use descriptive migration messages

4. **Frontend Builds**
   - Must rebuild after TypeScript changes
   - Bundle outputs to static/dist/
   - Clear browser cache after updates

## Environment Variables

### Core Application
- `API_KEY`: API authentication key (default: "your_secret_api_key_here")
- `DEBUG`: Enable debug mode (default: True in dev, False in prod)
- `CORS_ORIGINS`: Comma-separated list of allowed origins

### Database
- `DATABASE_URL`: PostgreSQL connection string (default: postgresql://medgen_user:medgen_password@localhost:5432/medgen_db)

### Redis Cache
- `REDIS_URL`: Redis connection string (default: redis://localhost:6379/0)
- `CACHE_TTL`: Default cache TTL in seconds (default: 3600)
- `CACHE_ENABLED`: Enable/disable caching (default: True)

### Patient Generation
- `PATIENT_GENERATOR_THREADS`: Number of worker threads (default: 4)
- `PATIENT_GENERATOR_MAX_MEMORY`: Maximum memory in MB (default: 2048)

## Git Workflow

- Feature branches: `feature/<epic>/<task>` or `feature/TICKET-ID-description`
- Commit format: `[TICKET-ID] Brief description`
- Always create PRs to `develop` branch
- Squash and merge for clean history
- Update ticket status in memory-bank after merge

## Testing Requirements

- All new endpoints need API integration tests
- Business logic requires unit tests
- Frontend components need Jest tests
- Maintain existing test patterns for consistency

## Feature Development Workflow

When deferring or hiding features for later development:
1. Comment out the UI element with a note: `<!-- Hidden for future development -->`
2. Add the feature to `memory-bank/backlog.md` with:
   - Current status (hidden, planned, partially implemented)
   - File locations where code exists
   - What functionality already exists
   - What needs to be specified before implementation
3. When ready to implement, create specification and move to tickets

This ensures unfinished features are tracked and not forgotten.

## Additional Memory Entries

- When changing HTML files, always confirm that no dependencies from API, JS or CSS, or other assets remain.