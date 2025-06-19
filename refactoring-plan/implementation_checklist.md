# Refactoring Implementation Checklist

## Pre-Implementation Setup
- [ ] Create development branch from main: `git checkout -b feature/performance-refactoring`
- [ ] Set up test database with production-like data (minimum 100K patient records)
- [ ] Install monitoring tools (htop, iotop, redis-cli monitor)
- [ ] Create baseline performance metrics:
  - [ ] Generate 50K patients - record time, memory, CPU
  - [ ] Run 10 concurrent jobs - record database connections
  - [ ] Measure cache hit rate (should be ~0% initially)

## Task 1: Database Consolidation ✓ when complete

### Phase 1: Analysis (30 min)
- [x] Search codebase for `from patient_generator.database import`
- [x] List all files that need updating in `db_migration_files.txt`
- [x] Count total occurrences: `grep -r "Database()" . | wc -l`

### Phase 2: Implementation (4 hours)
- [x] Update imports in patient_generator modules:
  - [x] config_manager.py
  - [ ] demographics.py (no Database usage found)
  - [ ] medical.py (no Database usage found)
  - [ ] flow_simulator.py (no Database usage found)
  - [ ] formatter.py (no Database usage found)
  - [ ] temporal_generator.py (no Database usage found)
- [x] Update imports in src modules:
  - [x] domain/services/patient_generation_service.py
  - [ ] domain/services/cached_demographics_service.py (no Database usage)
  - [ ] domain/services/cached_medical_service.py (no Database usage)
- [x] Update database instantiation patterns
- [x] Extract ConfigurationRepository to separate file
- [x] Remove patient_generator/database.py (legacy implementation)
- [ ] Update any SQL query patterns to use async

### Phase 3: Testing (2 hours)
- [x] Run unit tests: `pytest tests/test_db_integration.py -v`
- [ ] Run integration tests: `pytest tests/test_patient_generation.py -v`
- [ ] Monitor database connections during test
- [ ] Verify no connection leaks with load test

### Phase 4: Verification
- [ ] Database connections stay under 20 during load
- [ ] No "too many connections" errors in logs
- [ ] All existing tests pass
- [ ] Document any API changes

## Task 2: Generation Pipeline Optimization ✓ when complete

### Phase 1: Temporal Config Refactoring (2 hours)
- [ ] Update PatientFlowSimulator constructor
- [ ] Add temporal_config parameter
- [ ] Remove injuries.json file manipulation
- [ ] Update generation task to pass config in-memory
- [ ] Test temporal generation without file writes

### Phase 2: Streaming Implementation (4 hours)
- [ ] Create StreamingPatientWriter class
- [ ] Implement async file writing with aiofiles
- [ ] Update PatientGenerationPipeline for chunked generation
- [ ] Implement progress callbacks per chunk
- [ ] Add memory monitoring to tests

### Phase 3: Testing (3 hours)
- [ ] Test 100K patient generation:
  - [ ] Memory usage stays under 500MB
  - [ ] No memory growth over time
  - [ ] Output files are valid
- [ ] Test concurrent temporal generations:
  - [ ] No injuries.json conflicts
  - [ ] Each job gets correct config
  - [ ] Results match expected warfare patterns
- [ ] Benchmark generation speed:
  - [ ] 10K patients: target < 30s
  - [ ] 50K patients: target < 2 min
  - [ ] 100K patients: target < 5 min

### Phase 4: Verification
- [ ] Memory profile is flat during generation
- [ ] No file I/O race conditions
- [ ] Generation is 40-50% faster
- [ ] Output files are identical to old method

## Task 3: Smart Caching Implementation ✓ when complete

### Phase 1: Cache Warmup (2 hours)
- [ ] Create CacheWarmupService class
- [ ] Implement demographics cache warming
- [ ] Implement medical conditions cache warming
- [ ] Implement configuration cache warming
- [ ] Add warmup to application startup

### Phase 2: Computation Caching (3 hours)
- [ ] Create ComputationCache generic class
- [ ] Add caching to injury distribution calculations
- [ ] Add caching to triage weight calculations
- [ ] Add caching to transition matrix building
- [ ] Implement cache key generation

### Phase 3: Cache Invalidation (2 hours)
- [ ] Create CacheInvalidator class
- [ ] Add invalidation to configuration updates
- [ ] Add invalidation to job updates
- [ ] Add cache TTL strategy
- [ ] Test cache consistency

### Phase 4: Testing & Verification
- [ ] Measure cache hit rates:
  - [ ] Demographics: >95%
  - [ ] Medical: >95%
  - [ ] Configurations: >90%
  - [ ] Computations: >80%
- [ ] Verify cache memory usage < 100MB
- [ ] Test cache invalidation works correctly
- [ ] Benchmark API response times:
  - [ ] Config lookup: <10ms
  - [ ] Job status: <20ms

## Integration Testing

### Load Test Scenarios
- [ ] Scenario 1: 10 concurrent jobs, 10K patients each
  - [ ] All complete successfully
  - [ ] Memory usage stable
  - [ ] Database connections < 20
- [ ] Scenario 2: 5 temporal + 5 standard generations
  - [ ] No conflicts
  - [ ] Correct warfare patterns applied
- [ ] Scenario 3: Continuous generation for 1 hour
  - [ ] No memory leaks
  - [ ] No connection leaks
  - [ ] Cache hit rate stays high

### Performance Benchmarks
- [ ] Database connections reduced by 70%
- [ ] Generation time reduced by 50%
- [ ] Memory usage flat (no growth)
- [ ] Cache hit rate >90%
- [ ] API response <50ms

## Deployment Preparation

### Documentation
- [ ] Update API documentation
- [ ] Document new environment variables
- [ ] Create migration guide
- [ ] Update deployment scripts

### Staging Deployment
- [ ] Deploy to staging environment
- [ ] Run smoke tests
- [ ] Monitor for 24 hours
- [ ] Check error logs

### Rollback Plan
- [ ] Document rollback procedure
- [ ] Test rollback on staging
- [ ] Prepare rollback scripts
- [ ] Set monitoring alerts

## Post-Deployment

### Monitoring
- [ ] Set up Grafana dashboards:
  - [ ] Database connection pool
  - [ ] Cache hit rates
  - [ ] Memory usage
  - [ ] Generation performance
- [ ] Configure alerts:
  - [ ] High database connections
  - [ ] Low cache hit rate
  - [ ] Memory growth
  - [ ] Failed generations

### Performance Validation
- [ ] Compare metrics to baseline
- [ ] Document improvements
- [ ] Share results with team
- [ ] Plan next optimizations

## Sign-off

- [ ] Code review completed
- [ ] All tests passing
- [ ] Performance goals met
- [ ] Documentation updated
- [ ] Deployed to production
- [ ] Monitoring confirmed

**Implementation Start Date**: ___________
**Target Completion Date**: ___________
**Actual Completion Date**: ___________

## Notes Section

Use this space to track issues, decisions, and observations during implementation:

---
