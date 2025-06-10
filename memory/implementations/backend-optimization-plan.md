# Backend Optimization Implementation Plan

## Priority 1: Immediate Optimizations (No Added Complexity)

### 1. Repository Structure Cleanup

#### Task: Move InMemoryJobRepository to infrastructure layer
```bash
# Create infrastructure repositories directory
mkdir -p src/infrastructure/repositories

# Move repository implementation
# Update imports across the codebase
```

**Files to Update:**
- Create: `src/infrastructure/repositories/__init__.py`
- Create: `src/infrastructure/repositories/job_repository.py`
- Update: `src/api/v1/dependencies/services.py`
- Keep: `src/domain/repositories/job_repository.py` (interface only)

### 2. Import Optimization

#### Task: Create clean module exports
```python
# src/domain/services/__init__.py
from .job_service import JobService
from .patient_generation_service import AsyncPatientGenerationService, GenerationContext
from .cached_demographics_service import CachedDemographicsService
from .cached_medical_service import CachedMedicalService

__all__ = [
    'JobService',
    'AsyncPatientGenerationService',
    'GenerationContext',
    'CachedDemographicsService',
    'CachedMedicalService'
]
```

**Files to Create/Update:**
- `src/domain/services/__init__.py`
- `src/domain/models/__init__.py`
- `src/api/v1/routers/__init__.py`

### 3. Logging Configuration

#### Task: Add structured logging
```python
# src/core/logging.py
import logging
import sys
from typing import Any, Dict

def setup_logging(debug: bool = False) -> None:
    """Configure application logging."""
    level = logging.DEBUG if debug else logging.INFO
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Silence noisy libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

def get_logger(name: str) -> logging.Logger:
    """Get a configured logger instance."""
    return logging.getLogger(name)
```

### 4. Error Standardization

#### Task: Create consistent error responses
```python
# src/core/errors.py
from enum import Enum
from typing import Any, Dict, Optional

class ErrorCode(str, Enum):
    """Standard error codes."""
    NOT_FOUND = "NOT_FOUND"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    GENERATION_ERROR = "GENERATION_ERROR"
    STORAGE_ERROR = "STORAGE_ERROR"
    UNAUTHORIZED = "UNAUTHORIZED"

class ErrorResponse:
    """Standard error response structure."""
    
    @staticmethod
    def create(
        code: ErrorCode,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create standard error response."""
        response = {
            "error": {
                "code": code.value,
                "message": message
            }
        }
        if details:
            response["error"]["details"] = details
        return response
```

### 5. Configuration Service

#### Task: Centralize configuration management
```python
# src/domain/services/configuration_service.py
from typing import Optional
from patient_generator.database import ConfigurationRepository, Database
from patient_generator.schemas_config import ConfigurationTemplateDB

class ConfigurationService:
    """Service for managing configurations."""
    
    def __init__(self):
        self._db = Database()
        self._repo = ConfigurationRepository(self._db)
    
    def get_configuration(self, config_id: str) -> Optional[ConfigurationTemplateDB]:
        """Get configuration by ID."""
        return self._repo.get_configuration(config_id)
    
    def get_default_configuration(self) -> ConfigurationTemplateDB:
        """Get or create default configuration."""
        # Implementation here
        pass
```

## Implementation Order

1. **Logging Setup** (30 min)
   - Create logging module
   - Update main.py to use logging
   - Add logger to key services

2. **Repository Restructure** (45 min)
   - Create infrastructure directories
   - Move repository implementation
   - Update all imports
   - Run tests to verify

3. **Import Cleanup** (30 min)
   - Create __init__.py exports
   - Update imports across codebase
   - Verify no circular imports

4. **Error Standardization** (45 min)
   - Create error module
   - Update API endpoints
   - Ensure consistent responses

5. **Configuration Service** (1 hour)
   - Create service
   - Update generation endpoint
   - Add tests

## Testing Checklist

After each optimization:
- [ ] Run existing tests: `pytest`
- [ ] Check API docs still work: `http://localhost:8000/docs`
- [ ] Verify generation still works
- [ ] Update relevant tests

## Rollback Plan

Each optimization is independent. If issues arise:
1. Revert the specific change
2. Run tests to ensure stability
3. Document the issue in memory/fixes/
4. Continue with next optimization

## Success Metrics

- [ ] All tests pass
- [ ] No new complexity added
- [ ] Code is more maintainable
- [ ] Clear separation of concerns
- [ ] Better error messages
- [ ] Structured logging in place

---

*Created: Current Session*
*Status: Ready for Implementation*
