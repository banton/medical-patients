# Simplified Testing Strategy

## Philosophy
We're generating fake patients for military exercises. Our tests should ensure:
1. The API works and returns correct data
2. Patients are generated with valid data
3. Security (API keys) works
4. The system doesn't crash under normal use

We don't need to test every edge case or implementation detail.

## Core Test Categories

### 1. API Contract Tests (CRITICAL)
- **test_simple_api.py** - Basic happy path: generate patients, check job, download
- **test_api_standardization.py** - Verify API responses match documented schemas

### 2. Business Logic Tests (CRITICAL) 
- **test_evacuation_times.py** - Verify patient flow through facilities is realistic
- **test_simple_ui.py** - Basic UI functionality

### 3. Security Tests (CRITICAL)
- **test_api_key_management.py** - API key validation works
- **test_security.py** - Authentication and authorization

### 4. Integration Tests (IMPORTANT)
- **test_smoke.py** - Basic health checks for deployment
- **test_db_integration.py** - Database operations work

### 5. Performance Guards (NICE TO HAVE)
- Simple tests that generation doesn't use excessive memory
- Basic load test (100 patients, not 5000)

## Tests to Simplify or Remove

### Remove Completely
- **test_api_key_cli_*.py** - 2000+ lines testing a CLI tool extensively
- **test_connection_pool.py** OR **test_enhanced_pool.py** - Keep only one
- **test_metrics_helper.py** - Testing Prometheus internals
- **ubuntu_24_04_compatibility/** - Platform-specific tests

### Simplify Dramatically
- **test_e2e_flows.py** - Reduce to single happy path, remove 5000 patient tests
- **test_cache_*.py** - Consolidate to basic get/set/invalidate tests
- **test_metrics*.py** - Just verify metrics are recorded, not how

## Testing Guidelines

### DO:
- Test the API contract (request/response shapes)
- Test business rules (patient data validity)
- Test security (unauthorized access fails)
- Keep tests simple and readable
- Use realistic test data (10-100 patients, not 5000)

### DON'T:
- Test implementation details (how caching works internally)
- Test third-party libraries (Redis, Prometheus, psycopg2)
- Create complex mocks that are harder to maintain than the code
- Test every possible edge case for fake data generation

## Quick Test Commands

```bash
# Run only critical tests
pytest tests/test_simple_api.py tests/test_api_standardization.py tests/test_evacuation_times.py tests/test_security.py -v

# Run integration tests
pytest -m integration

# Run all tests (simplified suite)
pytest
```

## Test Maintenance

When adding new features:
1. Add API contract test if new endpoint
2. Add business logic test if new patient data
3. Skip unit tests for simple CRUD operations
4. Focus on user-visible behavior, not internals