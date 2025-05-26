# Application Architecture

This document describes the architecture of the Military Medical Exercise Patient Generator after the modularization refactoring.

## Overview

The application has been refactored from a monolithic `app.py` file into a clean, domain-driven architecture with clear separation of concerns. The new structure follows modern Python best practices and makes the codebase more maintainable, testable, and scalable.

## Directory Structure

```
military-patient-generator/
├── src/                          # New modular source code
│   ├── api/                      # API layer
│   │   └── v1/                   # API version 1
│   │       ├── dependencies/     # FastAPI dependencies
│   │       │   ├── database.py   # Database session management
│   │       │   └── services.py   # Service layer dependencies
│   │       └── routers/          # API endpoints
│   │           ├── configurations.py  # Configuration management
│   │           ├── generation.py      # Patient generation
│   │           ├── jobs.py           # Job management
│   │           ├── downloads.py      # File downloads
│   │           └── visualizations.py # Visualization data
│   ├── core/                     # Core utilities and shared code
│   │   ├── exceptions.py         # Custom exceptions
│   │   └── security.py           # Security utilities (API key validation)
│   ├── domain/                   # Business logic layer
│   │   ├── models/               # Domain models
│   │   │   └── job.py           # Job model and enums
│   │   ├── repositories/         # Data access interfaces
│   │   │   └── job_repository.py # Job repository interface and implementation
│   │   └── services/             # Business logic services
│   │       └── job_service.py    # Job management service
│   └── main.py                   # Application entry point
├── patient_generator/            # Existing patient generation logic
├── config.py                     # Environment configuration
└── tests/                        # Test files
    ├── test_job_service.py       # Job service tests
    └── test_security.py          # Security tests
```

## Architecture Layers

### 1. API Layer (`src/api/`)

The API layer handles HTTP requests and responses. It's organized by version (`v1/`) to support future API versions without breaking existing clients.

- **Routers**: Each router handles a specific domain (configurations, jobs, etc.)
- **Dependencies**: Shared dependencies for dependency injection
- **Middleware**: Cross-cutting concerns like rate limiting and CORS

### 2. Domain Layer (`src/domain/`)

The domain layer contains the business logic and is independent of the API layer.

- **Models**: Domain entities like `Job` with business logic
- **Services**: Business operations like `JobService`
- **Repositories**: Data access interfaces

### 3. Core Layer (`src/core/`)

Shared utilities and cross-cutting concerns.

- **Security**: API key validation
- **Exceptions**: Custom exception hierarchy
- **Configuration**: Environment variable management (via `config.py`)

### 4. Infrastructure Layer

Currently, the infrastructure layer is minimal:
- In-memory job repository (can be replaced with database implementation)
- File system for output storage

## Key Design Patterns

### 1. Dependency Injection

FastAPI's dependency injection is used throughout:

```python
async def generate_patients(
    request: GenerationRequest,
    job_service: JobService = Depends(get_job_service),
    db_session: Session = Depends(get_db_session)
):
    # Implementation
```

### 2. Repository Pattern

The repository pattern abstracts data access:

```python
class JobRepositoryInterface(ABC):
    @abstractmethod
    async def create(self, config: Dict[str, Any]) -> Job:
        pass
```

### 3. Service Layer

Business logic is encapsulated in services:

```python
class JobService:
    async def create_job(self, config: Dict[str, Any]) -> Job:
        # Business logic here
```

### 4. Factory Pattern

The main application is created via factory function:

```python
def create_app() -> FastAPI:
    app = FastAPI(...)
    # Configure app
    return app
```

## Data Flow

1. **Request Flow**:
   - Client → API Router → Service → Repository → Storage
   - Response flows back through the same layers

2. **Job Processing**:
   - Job creation → Background task → Patient generation → File storage
   - Progress updates via job service

3. **Configuration Management**:
   - Configurations stored in PostgreSQL
   - Accessed via `ConfigurationRepository`
   - Used by `PatientGeneratorApp`

## Security

- **API Key Authentication**: Required for configuration endpoints
- **Environment Variables**: Sensitive data like API keys
- **CORS**: Configurable allowed origins
- **Rate Limiting**: Via SlowAPI middleware

## Scalability Considerations

1. **Horizontal Scaling**: 
   - Stateless API can be scaled horizontally
   - Job storage needs distributed solution (Redis, database)

2. **Async Processing**:
   - Background tasks for long-running operations
   - Can be replaced with task queue (Celery, RQ)

3. **Database**:
   - Currently uses SQLAlchemy with PostgreSQL
   - Can be scaled with read replicas

## Future Improvements

1. **Async Patient Generation**: Replace threading with async/await
2. **Distributed Job Storage**: Replace in-memory with Redis/database
3. **Message Queue**: For job processing (RabbitMQ, Redis)
4. **Caching**: Add Redis for frequently accessed data
5. **Monitoring**: Add APM and logging infrastructure

## Testing Strategy

1. **Unit Tests**: Test individual components in isolation
2. **Integration Tests**: Test API endpoints with real database
3. **End-to-End Tests**: Test complete workflows

## Deployment

The application can be deployed using:
- Docker (see `Dockerfile`)
- Kubernetes (create manifests)
- Cloud platforms (AWS ECS, Google Cloud Run)

## Migration from Monolith

The migration preserved all functionality while improving:
- Code organization
- Testability
- Maintainability
- Scalability potential

The original `app.py` can be removed once all functionality is verified in the new structure.