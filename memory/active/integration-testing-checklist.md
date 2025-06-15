# Integration Testing Checklist

## Pre-Flight Checks

### 1. Environment Setup
- [ ] Create fresh staging branch from main
- [ ] Set up isolated test database
- [ ] Configure environment variables for all EPICs
- [ ] Verify Docker Compose setup includes all services

### 2. Dependency Verification
```bash
# Commands to run:
pip install -r requirements.txt
pip check
python -m pytest --collect-only  # Verify all tests discoverable
```

## Integration Test Sequence

### Day 1: Individual EPIC Verification
- [ ] Run EPIC-001 cross-platform tests
- [ ] Run EPIC-002 API key management tests  
- [ ] Run EPIC-003 scalability tests
- [ ] Document any test failures

### Day 2: Paired Integration
- [ ] Test API Keys + Connection Pooling
  - [ ] Create API key via CLI
  - [ ] Validate key in async endpoint
  - [ ] Monitor pool metrics
  - [ ] Check for connection leaks

- [ ] Test Rate Limiting + Worker Pools
  - [ ] Set API key limits
  - [ ] Generate concurrent requests
  - [ ] Verify accurate limiting
  - [ ] Check worker resource usage

### Day 3: Full Stack Testing
- [ ] Start all services together
- [ ] Run migration chain
- [ ] Execute full test suite
- [ ] Monitor for:
  - [ ] Memory leaks
  - [ ] Connection pool exhaustion
  - [ ] Metric accuracy
  - [ ] Error rates

### Day 4: Load Testing
- [ ] Create load test scenarios:
  - [ ] 10 concurrent users
  - [ ] 50 concurrent users  
  - [ ] 100 concurrent users
- [ ] Monitor:
  - [ ] Response times
  - [ ] Error rates
  - [ ] Resource usage
  - [ ] Database connections

## Common Issues & Quick Fixes

### Issue: "Connection pool exhausted"
```python
# Fix: Increase pool size in config
DATABASE_POOL_SIZE = 30
DATABASE_POOL_MAX_OVERFLOW = 10
```

### Issue: "Async context error in API key validation"
```python
# Fix: Ensure proper async context
async with get_session() as session:
    repo = APIKeyRepository(session)
    # Don't pass session outside context
```

### Issue: "Rate limit not enforced correctly"
```python
# Fix: Use Redis for distributed rate limiting
RATE_LIMIT_BACKEND = "redis"
REDIS_URL = "redis://localhost:6379"
```

## Staging Environment Commands

```bash
# Start staging environment
docker-compose -f docker-compose.staging.yml up -d

# View logs
docker-compose -f docker-compose.staging.yml logs -f app

# Run integration tests
docker-compose -f docker-compose.staging.yml exec app pytest tests/integration/ -v

# Check metrics
curl http://localhost:9090/metrics

# Clean up
docker-compose -f docker-compose.staging.yml down -v
```

## Go/No-Go Decision Criteria

### Go (Ready for Production)
- All integration tests pass
- Load tests show <5% performance degradation
- No memory leaks detected
- Error rate <0.1%

### No-Go (Needs Fixes)
- Any critical test failures
- Performance degradation >10%
- Memory leaks detected
- Unhandled exceptions in logs

## Next Steps After Testing

1. **If Successful**:
   - Create PR for integration branch
   - Update documentation
   - Plan EPIC-004 (Production Deployment)

2. **If Issues Found**:
   - Document all issues in memory/fixes/
   - Create fix branches
   - Re-test after fixes
   - Consider EPIC-007 for integration improvements