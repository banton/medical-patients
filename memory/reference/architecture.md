# Architecture Reference

## System Structure
```
src/
├── api/v1/        # REST endpoints
├── domain/        # Business logic
├── infrastructure/# Data access
└── core/          # Shared utilities
```

## Key Components
- FastAPI for REST API
- SQLAlchemy for ORM
- Alembic for migrations
- Redis for caching
- pytest for testing

## Design Patterns
- Repository pattern for data access
- Service layer for business logic
- Dependency injection
- Async/await throughout
