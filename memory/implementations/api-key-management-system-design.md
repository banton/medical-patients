# API Key Management System Design

## Overview

Claude Code designed a comprehensive API key management system for the Medical Patients Generator API. The system was designed but **NOT IMPLEMENTED** due to lack of user permission. This document preserves the design for future implementation.

## System Components

### 1. Database Models (`src/domain/models/api_key.py`)
- **APIKey Model**: SQLAlchemy model with comprehensive fields
- **Usage Tracking**: Built-in request and patient generation counters
- **Expiration Support**: Optional expiration dates
- **Rate Limiting**: Per-key minute/hour limits
- **Demo Keys**: Special flag for limited access keys

### 2. Repository Pattern (`src/domain/repositories/api_key_repository.py`)
- **CRUD Operations**: Create, read, update, delete API keys
- **Usage Tracking**: Increment request/patient counters
- **Search Functionality**: Find keys by name/email
- **Soft Delete**: Deactivate without losing history

### 3. Enhanced Security (`src/core/security_enhanced.py`)
- **APIKeyContext**: Rich context object with limits and validation
- **Patient Limit Checks**: Enforce per-key patient generation limits
- **Rate Limit Integration**: Works with middleware for enforcement
- **Legacy Compatibility**: Backward compatible with existing single API key
- **Public Demo Key**: Hardcoded demo key with 50-patient limit

### 4. Rate Limiting Middleware (`src/api/v1/middleware/rate_limiter.py`)
- **Per-Key Limits**: Individual rate limits per API key
- **Multiple Timeframes**: Minute and hour-based limiting
- **Redis Integration**: Fast rate limit tracking
- **Proper HTTP Responses**: 429 status with Retry-After headers

### 5. CLI Management Tool (`scripts/manage_api_keys.py`)
- **Key Creation**: Generate new API keys with custom limits
- **Key Listing**: Tabulated view of all keys with usage stats
- **Key Management**: Activate, deactivate, delete keys
- **Usage Reports**: View detailed usage statistics
- **Demo Key Support**: Create demo keys with restrictions

### 6. Database Migration (`alembic_migrations/versions/001_create_api_keys.py`)
- **API Keys Table**: Core table for key storage
- **Usage Tracking Table**: Detailed request logging (future enhancement)
- **Proper Indexes**: Optimized for key lookups

## Key Features

### Public Demo Key
- **Key**: `DEMO_MILMED_2025_50_PATIENTS`
- **Limits**: 50 patients/generation, 100 requests/day, 10/minute
- **Purpose**: Allow public testing without registration

### Individual Key Limits
- **Patient Limits**: Max patients per generation request
- **Daily Limits**: Max API requests per day
- **Rate Limits**: Per-minute and per-hour request limits
- **Expiration**: Optional key expiration dates

### Usage Tracking
- **Request Counting**: Total API requests per key
- **Patient Counting**: Total patients generated per key
- **Last Used**: Timestamp of most recent usage
- **Daily Usage**: Current day's request count

### CLI Commands
```bash
# Create keys
python scripts/manage_api_keys.py create --name "Client" --email "test@example.com"
python scripts/manage_api_keys.py create --demo --patient-limit 50

# Manage keys
python scripts/manage_api_keys.py list
python scripts/manage_api_keys.py show KEY_ID
python scripts/manage_api_keys.py deactivate KEY_ID

# Usage reports
python scripts/manage_api_keys.py show KEY_ID  # Includes usage stats
```

## Integration Points

### Router Updates Required
```python
# Replace single API key dependency
async def generate_patients(
    api_key_context: APIKeyContext = Depends(verify_api_key)
):
    # Check patient limits
    api_key_context.check_patient_limit(request.count)
    
    # Access key info
    if api_key_context.is_demo:
        # Handle demo key restrictions
        pass
```

### Rate Limiting Integration
```python
# Add to routes requiring rate limiting
@router.post("/generate", dependencies=[Depends(check_api_key_rate_limit)])
```

### Usage Tracking Integration
```python
# Track usage after successful operations
repo.increment_usage(api_key, patients_generated=count)
```

## Security Considerations

### Key Generation
- **Cryptographically Secure**: Uses `secrets.token_hex(32)` for 64-char keys
- **Uniqueness**: Database constraints prevent duplicates
- **Entropy**: 256 bits of randomness per key

### Rate Limiting
- **Per-Key Isolation**: Each key has independent limits
- **Redis Backend**: Fast, memory-based rate limit tracking
- **Graceful Degradation**: Falls back if Redis unavailable

### Demo Key Security
- **Limited Scope**: Restricted patient counts and request rates
- **Hardcoded Safety**: Public demo key is fixed, not user-configurable
- **Usage Monitoring**: Same tracking as regular keys

## Implementation Requirements

### Database Changes
1. Run Alembic migration to create `api_keys` table
2. Update existing security imports to use enhanced version
3. Add rate limiting middleware to critical endpoints

### Code Changes
1. Replace `verify_api_key` dependency with enhanced version
2. Add patient limit checks to generation endpoints
3. Integrate usage tracking after successful operations
4. Add rate limiting middleware to routes

### Deployment Steps
1. Apply database migration: `alembic upgrade head`
2. Create initial API keys: `python scripts/manage_api_keys.py create`
3. Update environment variables (backward compatible)
4. Monitor usage and adjust limits as needed

## Future Enhancements

### Web Dashboard
- GUI for key management instead of CLI only
- Usage analytics with charts and graphs
- Key lifecycle management interface

### Advanced Analytics
- Request pattern analysis
- Usage trend reporting
- Anomaly detection for suspicious usage

### Billing Integration
- Usage-based billing calculations
- Invoice generation based on patient counts
- Credit system for prepaid usage

## Files That Were Created (Now Deleted)

1. `src/domain/models/api_key.py` - SQLAlchemy model
2. `src/domain/repositories/api_key_repository.py` - Repository implementation
3. `src/core/security_enhanced.py` - Enhanced security with context
4. `src/api/v1/middleware/rate_limiter.py` - Rate limiting middleware
5. `src/api/v1/routers/generation_enhanced.py` - Example router updates
6. `scripts/manage_api_keys.py` - CLI management tool
7. `scripts/apikeys` - Bash wrapper for CLI
8. `alembic_migrations/versions/001_create_api_keys.py` - Database migration
9. `docs/API_KEY_MANAGEMENT.md` - Comprehensive documentation
10. `PUBLIC_API_ACCESS.md` - Public API usage guide
11. `IMPLEMENTATION_GUIDE.md` - Step-by-step implementation

## Status

**Design**: Complete and comprehensive
**Implementation**: NOT STARTED - requires user permission
**Testing**: NOT DONE - no code to test
**Documentation**: Complete design documentation available

This system would provide a production-ready API key management solution with individual limits, usage tracking, rate limiting, and comprehensive CLI tools for management.