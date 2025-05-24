# Migration Guide: From Monolith to Modular Architecture

This guide explains the changes made during the modularization of `app.py` and how to migrate existing code.

## Overview of Changes

The monolithic `app.py` file (1000+ lines) has been refactored into a clean, modular architecture:

- **Before**: Single `app.py` with all routes, business logic, and utilities
- **After**: Organized modules under `src/` with clear separation of concerns

## Module Mapping

### API Endpoints

| Old Location (app.py) | New Location |
|----------------------|--------------|
| Configuration routes | `src/api/v1/routers/configurations.py` |
| Generation endpoint | `src/api/v1/routers/generation.py` |
| Job management | `src/api/v1/routers/jobs.py` |
| Download endpoint | `src/api/v1/routers/downloads.py` |
| Visualization API | `src/api/v1/routers/visualizations.py` |

### Core Functionality

| Functionality | Old Location | New Location |
|--------------|--------------|--------------|
| API key validation | `app.py` (inline) | `src/core/security.py` |
| Job storage | `jobs = {}` dict | `src/domain/repositories/job_repository.py` |
| Job management | Scattered in routes | `src/domain/services/job_service.py` |
| App configuration | Hardcoded | `config.py` + environment variables |

## Key Changes

### 1. Application Entry Point

**Before:**
```python
# app.py
app = FastAPI(title="Military Medical Exercise Patient Generator")
# ... all configuration and routes ...
```

**After:**
```python
# src/main.py
def create_app() -> FastAPI:
    app = FastAPI(...)
    # Configure middleware
    # Include routers
    return app

app = create_app()
```

### 2. Dependency Injection

**Before:**
```python
# Direct access to global variables
@app.post("/api/generate")
async def generate_patients(...):
    job_id = str(uuid.uuid4())
    jobs[job_id] = {...}  # Global dict
```

**After:**
```python
# Using dependency injection
@router.post("/generate")
async def generate_patients(
    job_service: JobService = Depends(get_job_service)
):
    job = await job_service.create_job(config)
```

### 3. Job Management

**Before:**
```python
# Global dictionary
jobs = {}

# Scattered update logic
jobs[job_id]["status"] = "running"
jobs[job_id]["progress"] = 50
```

**After:**
```python
# Service with clear interface
class JobService:
    async def create_job(self, config: Dict[str, Any]) -> Job:
        return await self.repository.create(config)
    
    async def update_job_progress(self, job_id: str, progress: int):
        # Centralized logic
```

### 4. Configuration

**Before:**
```python
EXPECTED_API_KEY = "your_secret_api_key_here"
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"]
)
```

**After:**
```python
# config.py
class Settings:
    API_KEY: str = os.getenv("API_KEY", "your_secret_api_key_here")
    CORS_ORIGINS: list[str] = os.getenv("CORS_ORIGINS", "...").split(",")

# Usage
settings = get_settings()
```

## Running the Application

### Development

**Before:**
```bash
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

**After:**
```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### Docker

The Dockerfile and docker-compose files have been updated:

```dockerfile
# Dockerfile
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Testing

New test structure:
```
tests/
├── test_job_service.py      # Unit tests for job service
├── test_security.py         # Security tests
└── test_api_integration.py  # API integration tests
```

Run tests:
```bash
pytest tests/
```

## Importing Modules

When adding new features or fixing bugs:

**Before:**
```python
# Everything was in app.py
from app import jobs, generate_patients_sync
```

**After:**
```python
# Import from appropriate modules
from src.domain.services.job_service import JobService
from src.core.security import verify_api_key
from src.api.v1.dependencies.services import get_job_service
```

## Environment Variables

See [ENVIRONMENT_CONFIG.md](ENVIRONMENT_CONFIG.md) for all available settings.

Key variables:
- `API_KEY`: API authentication key
- `DATABASE_URL`: PostgreSQL connection string
- `CORS_ORIGINS`: Allowed origins (comma-separated)

## Gradual Migration

The old `app.py` is still present but deprecated. To migrate gradually:

1. **Phase 1**: Run both old and new endpoints (current state)
2. **Phase 2**: Update clients to use new endpoints
3. **Phase 3**: Remove old `app.py`

## Common Issues

### Import Errors

If you see import errors, ensure:
1. `PYTHONPATH` includes the project root
2. Using `src.` prefix for new modules
3. Docker/virtualenv has latest code

### Missing Dependencies

The modular code uses the same dependencies. If something is missing:
```bash
pip install -r requirements.txt
```

### API Compatibility

The API endpoints remain compatible:
- Same paths (e.g., `/api/generate`)
- Same request/response formats
- Same authentication (API key)

## Benefits of New Architecture

1. **Testability**: Each component can be tested in isolation
2. **Maintainability**: Clear separation of concerns
3. **Scalability**: Easy to add new features without touching core
4. **Type Safety**: Better type hints and validation
5. **Dependency Management**: Clear dependencies via injection

## Next Steps

1. Update any scripts using `app:app` to use `src.main:app`
2. Review and update deployment configurations
3. Consider removing old `app.py` after verification
4. Implement additional improvements from [ARCHITECTURE.md](ARCHITECTURE.md)