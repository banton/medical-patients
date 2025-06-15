# CLI Tool Testing Strategy

## Overview

This document outlines the comprehensive testing strategy for the API Key Management CLI tool, covering unit tests, integration tests, and end-to-end tests following TDD principles.

## Testing Philosophy

### Test-Driven Development (TDD)
- **RED**: Write failing tests first
- **GREEN**: Implement minimal code to pass tests
- **REFACTOR**: Improve code while maintaining test coverage

### Test Pyramid Structure
```
     /\     E2E Tests (Few, High-Level)
    /  \    - Complete user workflows
   /____\   - Cross-system integration
  /      \  
 /        \  Integration Tests (Some, Medium-Level)
/          \ - Database operations
\          / - Component interactions
 \        /  
  \______/   Unit Tests (Many, Fast)
             - Individual functions
             - Input/output validation
             - Error handling
```

## Test Categories

### 1. Unit Tests (`tests/unit/test_api_key_cli_unit.py`)

**Purpose**: Test individual components in isolation with fast execution.

**Coverage Areas**:
- **Utility Methods**: Format functions, display helpers, data transformations
- **Input Validation**: Parameter parsing, type checking, boundary conditions
- **Output Formatting**: JSON/table/CSV formatting with edge cases
- **Error Handling**: Exception handling, error message formatting
- **Mock Dependencies**: Database and external service interactions

**Test Characteristics**:
- ⚡ Fast execution (< 1 second per test)
- 🔀 No external dependencies
- 🎯 Single responsibility testing
- 📊 High code coverage (>90%)

**Example Test Cases**:
```python
def test_format_key_display_edge_cases():
    """Test key display formatting with edge cases."""
    
def test_format_limits_with_unlimited_values():
    """Test limit formatting when values are None/unlimited."""
    
def test_usage_stats_with_missing_timestamps():
    """Test usage statistics when optional fields are None."""
```

### 2. Integration Tests (`tests/integration/test_api_key_cli_integration.py`)

**Purpose**: Test CLI commands with real database operations using testcontainers.

**Coverage Areas**:
- **Database Operations**: CRUD operations with real PostgreSQL
- **Transaction Behavior**: Commit/rollback scenarios
- **Command Workflows**: End-to-end command execution
- **Async Session Management**: Connection lifecycle, cleanup
- **Repository Integration**: Real APIKeyRepository operations

**Test Characteristics**:
- 🐘 Real PostgreSQL database via testcontainers
- ⏱️ Medium execution time (5-10 seconds per test)
- 🔄 Database isolation between tests
- 📈 Real data validation

**Example Test Cases**:
```python
async def test_create_command_real_database():
    """Test API key creation with real database."""
    
async def test_list_command_with_search_filter():
    """Test list command with search functionality."""
    
async def test_rotate_command_atomic_operation():
    """Test key rotation maintains data consistency."""
```

### 3. End-to-End Tests (`tests/e2e/test_api_key_cli_e2e.py`)

**Purpose**: Test complete user workflows and cross-system interactions.

**Coverage Areas**:
- **User Workflows**: Complete scenarios from start to finish
- **Data Consistency**: Cross-command data integrity
- **Performance**: Response times with realistic datasets
- **Error Recovery**: System behavior under failure conditions
- **Scalability**: Behavior with large datasets

**Test Characteristics**:
- 🌐 Full system integration
- ⏰ Slower execution (30+ seconds per test)
- 📊 Realistic data volumes
- 🔄 Complete workflows

**Example Test Cases**:
```python
async def test_complete_api_key_lifecycle():
    """Test: create → use → monitor → rotate → cleanup."""
    
async def test_bulk_operations_performance():
    """Test CLI performance with 1000+ API keys."""
    
async def test_error_recovery_workflow():
    """Test system recovery from database failures."""
```

## Test Implementation Plan

### Phase 1: Enhanced Unit Tests ✅
**Goal**: Expand unit test coverage to >95%

**Tasks**:
- [ ] Test all utility methods with edge cases
- [ ] Test command parameter validation
- [ ] Test output formatting for all formats (JSON, table, CSV)
- [ ] Test error message formatting
- [ ] Test interactive prompt scenarios

**Files**:
- `tests/unit/test_api_key_cli_unit.py`

### Phase 2: Integration Tests 🔄
**Goal**: Test real database operations

**Tasks**:
- [ ] Set up testcontainer fixtures for CLI testing
- [ ] Test each command with real database
- [ ] Test transaction behavior and rollbacks
- [ ] Test concurrent access scenarios
- [ ] Test search and filtering functionality

**Files**:
- `tests/integration/test_api_key_cli_integration.py`

### Phase 3: End-to-End Tests 📋
**Goal**: Test complete user workflows

**Tasks**:
- [ ] Test complete API key lifecycle workflows
- [ ] Test performance with large datasets
- [ ] Test error recovery scenarios
- [ ] Test cross-command data consistency
- [ ] Test CLI automation scenarios

**Files**:
- `tests/e2e/test_api_key_cli_e2e.py`

## Test Data Strategy

### Test Data Patterns

**Fixed Test Data**: Predictable, repeatable test scenarios
```python
SAMPLE_API_KEY = {
    "name": "Test API Key",
    "email": "test@example.com",
    "expires_at": datetime(2024, 12, 31),
    "max_patients_per_request": 1000,
    "max_requests_per_day": 500
}
```

**Generated Test Data**: Realistic volumes for performance testing
```python
def generate_test_keys(count: int) -> List[Dict]:
    """Generate test keys for bulk operations."""
```

**Edge Case Data**: Boundary conditions and error scenarios
```python
EDGE_CASES = {
    "empty_name": {"name": ""},
    "very_long_name": {"name": "x" * 1000},
    "invalid_email": {"email": "not-an-email"},
    "negative_limits": {"max_requests_per_day": -1}
}
```

## Testing Infrastructure

### Fixtures and Utilities

**Database Fixtures**:
```python
@pytest.fixture(scope="session")
def postgres_container():
    """PostgreSQL testcontainer for integration tests."""

@pytest.fixture
async def test_db_session(postgres_container):
    """Async database session for CLI testing."""

@pytest.fixture
async def sample_api_keys(test_db_session):
    """Pre-populated test data."""
```

**CLI Testing Utilities**:
```python
@pytest.fixture
def cli_runner():
    """Click test runner with proper isolation."""

@pytest.fixture
def mock_cli_environment():
    """Mock environment variables and configuration."""

async def run_cli_command(command: List[str]) -> CliResult:
    """Helper to run CLI commands with proper setup."""
```

### Test Organization

**Test File Structure**:
```
tests/
├── unit/
│   └── test_api_key_cli_unit.py          # Fast, isolated tests
├── integration/
│   └── test_api_key_cli_integration.py   # Database integration
├── e2e/
│   └── test_api_key_cli_e2e.py          # Complete workflows
└── fixtures/
    └── cli_fixtures.py                   # Shared test fixtures
```

**Test Naming Convention**:
```python
# Unit tests
def test_should_format_key_when_valid_input():
def test_should_raise_error_when_invalid_input():

# Integration tests  
async def test_create_command_should_persist_to_database():
async def test_delete_command_should_remove_from_database():

# E2E tests
async def test_complete_workflow_should_maintain_consistency():
async def test_bulk_operations_should_complete_within_timeout():
```

## Performance Testing

### Performance Benchmarks

**Response Time Targets**:
- Single operations: < 2 seconds
- Bulk operations (100 keys): < 30 seconds
- Large datasets (1000+ keys): < 5 minutes

**Memory Usage Targets**:
- Peak memory: < 100MB for normal operations
- Memory growth: < 10MB per 100 additional keys

**Test Implementation**:
```python
@pytest.mark.performance
async def test_list_command_performance():
    """Test list command with 1000+ keys completes within 30s."""
    
@pytest.mark.performance  
async def test_memory_usage_large_dataset():
    """Test memory usage stays under 100MB with large datasets."""
```

## Error Testing Strategy

### Error Categories

**Database Errors**:
- Connection failures
- Transaction rollbacks
- Constraint violations
- Timeout scenarios

**Input Validation Errors**:
- Invalid command parameters
- Malformed data inputs
- Out-of-range values
- Missing required fields

**System Errors**:
- Out of memory conditions
- File system failures
- Permission denied
- Network timeouts

**Test Implementation**:
```python
async def test_handles_database_connection_failure():
    """Test graceful handling when database is unavailable."""
    
async def test_handles_invalid_key_id_format():
    """Test validation of UUID format for key IDs."""
    
async def test_recovers_from_transaction_failure():
    """Test proper cleanup when database operations fail."""
```

## Test Execution Strategy

### Continuous Integration

**Test Execution Matrix**:
```yaml
# .github/workflows/ci.yml
strategy:
  matrix:
    test-type: [unit, integration, e2e]
    python-version: [3.8, 3.9, 3.10, 3.11]
```

**Test Commands**:
```bash
# Unit tests (fast)
pytest tests/unit/ -v --cov=scripts/api_key_cli

# Integration tests (medium)  
pytest tests/integration/ -v --requires-docker

# E2E tests (slow)
pytest tests/e2e/ -v --requires-docker --timeout=300

# Performance tests
pytest -m performance --benchmark-only
```

### Local Development

**Pre-commit Testing**:
```bash
# Quick feedback loop
make test-cli-unit      # < 30 seconds

# Full validation
make test-cli-full      # < 5 minutes

# Performance validation
make test-cli-perf      # < 10 minutes
```

## Quality Gates

### Coverage Requirements

**Unit Tests**: 95% line coverage minimum
**Integration Tests**: 90% database operation coverage  
**E2E Tests**: 100% critical workflow coverage

### Performance Requirements

**Response Time**: 95th percentile under target thresholds
**Memory Usage**: No memory leaks in long-running operations
**Concurrency**: Support 10 concurrent CLI operations

### Test Quality Metrics

**Test Reliability**: 99.9% pass rate (< 0.1% flaky tests)
**Test Maintainability**: Max 5 minutes to update tests for feature changes
**Test Documentation**: All complex test scenarios documented

## Risk Mitigation

### Common Testing Risks

**Flaky Tests**: 
- Solution: Deterministic test data, proper cleanup, retry logic

**Slow Test Execution**:
- Solution: Parallel execution, selective test running, performance monitoring

**Test Environment Issues**:
- Solution: Containerized testing, infrastructure as code, environment validation

**Test Maintenance Burden**:
- Solution: Shared fixtures, helper utilities, automated test generation

### Monitoring and Alerting

**Test Performance Monitoring**:
- Track test execution times
- Alert on test time regressions
- Monitor test flakiness rates

**Coverage Monitoring**:
- Automated coverage reporting
- Coverage regression detection
- Missing coverage alerts

## Success Criteria

### Phase 1 Success (Unit Tests)
- ✅ >95% line coverage for CLI module
- ✅ All edge cases covered
- ✅ Test execution < 30 seconds
- ✅ Zero flaky tests

### Phase 2 Success (Integration Tests)  
- ✅ All CLI commands tested with real database
- ✅ Transaction behavior validated
- ✅ Concurrent operation support
- ✅ Test execution < 5 minutes

### Phase 3 Success (E2E Tests)
- ✅ Complete workflow coverage
- ✅ Performance benchmarks met
- ✅ Error recovery validated  
- ✅ Production-ready confidence

## Conclusion

This comprehensive testing strategy ensures the CLI tool is robust, reliable, and production-ready through systematic validation of all components, operations, and scenarios. The three-tier approach provides confidence at every level from individual functions to complete user workflows.