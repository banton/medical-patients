# API Key Management System - Comprehensive Implementation Plan

## 🎯 Project Context
- **Project**: Medical Patients Generator API
- **Location**: `/Users/banton/Sites/medical-patients`
- **Live URL**: https://milmed.tech
- **Current State**: Single API key authentication via environment variable
- **Goal**: Implement multi-tenant API key system with public demo access

## 📋 Requirements Analysis

### Core Requirements
1. **Public Demo Key**: `DEMO_MILMED_2025_500_PATIENTS` with 500 patient limit (increased from 50)
2. **Personal API Keys**: Unlimited keys with custom limits
3. **Rate Limiting**: Per-key throttling to prevent spam
4. **CLI Management**: Create/manage keys via command line
5. **Backward Compatibility**: Keep existing `API_KEY` env var working
6. **Documentation**: Update all documentation to reflect new API access methods

### Current Authentication System Analysis
- **File**: `src/core/security.py`
- **Method**: Single API key from `settings.API_KEY` environment variable
- **Function**: `verify_api_key()` returns the key string if valid
- **Pattern**: Environment variable based, no database integration

### Database Architecture Requirements
- **ORM**: SQLAlchemy with Alembic migrations
- **Connection**: PostgreSQL via `settings.DATABASE_URL`
- **Pattern**: Custom `patient_generator.database.Database` class
- **Status**: No existing SQLAlchemy models - need to create proper models

## 🏗️ Implementation Architecture

### 1. Database Models (`src/domain/models/api_key.py`)
```python
# SQLAlchemy model for API keys with fields:
class APIKey(Base):
    __tablename__ = "api_keys"
    
    # Identity
    id: Primary key
    key: String(64), unique, indexed
    name: Human-readable name
    email: Optional contact email
    
    # Configuration
    is_demo: Boolean flag
    patient_limit: Max patients per generation (null = unlimited)
    daily_limit: Max requests per day
    rate_limit_per_minute: Default 60
    rate_limit_per_hour: Default 1000
    
    # Usage Tracking
    total_requests: Usage counter
    total_patients_generated: Usage counter
    last_used: Timestamp
    
    # Lifecycle
    created_at: Timestamp
    expires_at: Optional expiration
    is_active: Boolean
    notes: Internal notes
```

### 2. Repository Pattern (`src/domain/repositories/api_key_repository.py`)
```python
# CRUD operations interface:
- create(api_key) -> APIKey
- get_by_key(key: str) -> Optional[APIKey]
- get_by_id(id: int) -> Optional[APIKey]
- get_all(include_inactive=False) -> List[APIKey]
- update(api_key) -> APIKey
- delete(id: int) -> bool
- deactivate(id: int) -> bool
- increment_usage(key: str, patients: int)
- get_daily_usage(key: str) -> int
- search(query: str) -> List[APIKey]
```

### 3. Enhanced Security (`src/core/security_enhanced.py`)
```python
# New verify_api_key implementation:
1. Checks legacy env var first (backward compatibility)
2. Checks database for key
3. Auto-creates demo key if needed
4. Returns APIKeyContext object with:
   - key details
   - check_patient_limit(count)
   - check_daily_limit(usage)
```

### 4. Rate Limiter (`src/api/v1/middleware/rate_limiter.py`)
```python
# Per-key rate limiting:
- In-memory sliding window counter
- Enforces minute/hour limits from APIKey model
- Returns 429 with Retry-After header
```

### 5. CLI Tool (`scripts/manage_api_keys.py`)
```bash
# Command structure:
create --name "Name" [--demo] [--patient-limit 500] [--expires 30]
list [--all]
show <id>
deactivate <id>
delete <id>
```

### 6. Database Migration (`alembic_migrations/versions/XXX_create_api_keys.py`)
```sql
CREATE TABLE api_keys (
    id SERIAL PRIMARY KEY,
    key VARCHAR(64) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    -- ... all fields ...
);
CREATE INDEX ix_api_keys_key ON api_keys(key);

CREATE TABLE api_key_usage (
    id SERIAL PRIMARY KEY,
    api_key_id INTEGER REFERENCES api_keys(id),
    timestamp TIMESTAMP DEFAULT NOW(),
    endpoint VARCHAR(255),
    patients_generated INTEGER DEFAULT 0
);
```

## 🔧 Integration Changes Required

### Router Updates
```python
# Change from:
from src.core.security import verify_api_key
async def endpoint(current_user: str = Depends(verify_api_key)):

# To:
from src.core.security_enhanced import verify_api_key, APIKeyContext
from src.api.v1.middleware.rate_limiter import check_api_key_rate_limit

@router.post("/", dependencies=[Depends(check_api_key_rate_limit)])
async def endpoint(api_key_context: APIKeyContext = Depends(verify_api_key)):
    api_key_context.check_patient_limit(requested_count)
```

### Specific Router Changes
- **`src/api/v1/routers/generation.py`**: Extract patient count, check limits, track usage
- **`src/main.py`**: Update FastAPI app with demo key documentation
- **All routers using `verify_api_key`**: Migrate to new security system

## 🔑 Public Demo Key Specification
- **Key**: `DEMO_MILMED_2025_500_PATIENTS`
- **Limits**:
  - 500 patients per generation
  - 100 requests per day
  - 10 requests per minute
  - 50 requests per hour
- **Auto-created**: First use creates DB entry

## 📚 Documentation Structure

### New Documentation Files
```
docs/
├── API_DOCUMENTATION.md      # Complete API reference with demo key
├── PUBLIC_DEMO_ACCESS.md      # Quick start for demo users
├── API_KEY_MANAGEMENT.md      # Internal key management guide
├── MIGRATION_GUIDE.md         # For existing users
└── examples/                  # Code examples
    ├── python_example.py
    ├── javascript_example.js
    └── curl_examples.sh
```

### README.md Updates
- **Live API Access** section with demo key
- **Example Usage** with curl examples
- **Production Access** instructions
- **API Documentation** links
- **Authentication** guide
- **Rate Limiting** information

### FastAPI App Description Update
```python
description="""
Military Medical Exercise Patient Generator API

## Demo Access
Try the API with our public demo key:
- **Key**: `DEMO_MILMED_2025_500_PATIENTS`
- **Limits**: 500 patients/generation, 100 requests/day

## Authentication
Include your API key in the `X-API-KEY` header for all requests.
"""
```

## 🔐 Security Considerations
- Use `secrets.token_hex(32)` for key generation
- Never log full API keys
- Implement key rotation recommendation
- Consider adding key scopes in future
- Add monitoring for suspicious usage patterns

## 🚀 Deployment Strategy
1. **Environment Variables**: Update production configs
2. **Database Migration**: Run on production database
3. **Documentation**: Deploy updated docs
4. **Monitoring**: Set up alerts for demo key abuse
5. **Support**: Prepare for user questions

## 📁 Files to Create/Modify

### Files to Create
```
src/domain/models/api_key.py
src/domain/repositories/api_key_repository.py
src/core/security_enhanced.py
src/api/v1/middleware/rate_limiter.py
scripts/manage_api_keys.py
alembic_migrations/versions/XXX_create_api_keys.py
docs/API_DOCUMENTATION.md
docs/PUBLIC_DEMO_ACCESS.md
docs/API_KEY_MANAGEMENT.md
docs/MIGRATION_GUIDE.md
docs/examples/ (directory with examples)
```

### Files to Modify
```
requirements.txt - Add tabulate>=0.9.0
src/main.py - Update API description
src/api/v1/routers/generation.py - Use new security
All other routers using verify_api_key
README.md - Add live API sections
```

## ⚠️ Critical Integration Notes

### Database Integration Challenge
- Project uses custom `patient_generator.database.Database` class
- Need to integrate SQLAlchemy models with existing system
- Must maintain backward compatibility with existing patterns

### Authentication Migration
- **Backward Compatibility**: Existing `API_KEY` env var must continue working
- **Demo Key**: Hardcoded `DEMO_MILMED_2025_500_PATIENTS` with auto-creation
- **Migration Path**: Seamless transition for existing users

### Testing Requirements
1. Run migration to create tables
2. Test CLI tool creates keys
3. Test demo key auto-creation and limits
4. Test rate limiting functionality
5. Test backward compatibility with env var
6. Test patient limit enforcement
7. Verify API documentation shows demo key
8. Test demo key in production environment

## 🎯 Success Criteria
- ✅ Demo key `DEMO_MILMED_2025_500_PATIENTS` works immediately on https://milmed.tech
- ✅ Existing API key authentication continues working
- ✅ Rate limiting prevents abuse
- ✅ CLI tool manages production keys
- ✅ Complete documentation for public and private use
- ✅ Production deployment without breaking changes

## 🔮 Future Enhancements
1. Web dashboard for key management
2. Self-service key registration
3. OAuth2 integration option
4. Detailed usage analytics dashboard
5. Webhook notifications for limits
6. Team/project associations
7. Usage-based billing integration

---

*Implementation Priority: High - Critical for public API access and scalability*
*Complexity Level: Medium-High - Database integration + authentication system*
*Estimated Effort: 2-3 development sessions with comprehensive testing*