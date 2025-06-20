# Medical Patients Generator - Performance Refactoring Plan

## Overview
This document outlines three critical refactoring tasks to improve the performance and scalability of the Medical Patients Generator application. Each task includes specific implementation details, test cases, and verification steps.

## Task 1: Database Connection Management Consolidation

### Objective
Remove the legacy database implementation and ensure all code uses the enhanced connection pool implementation for better performance and resource management.

### Current State
- Two database implementations exist: `patient_generator/database.py` (legacy) and `src/infrastructure/database_adapter.py` (enhanced)
- Legacy implementation creates individual connections without pooling
- Some modules directly import and use the legacy Database class

### Implementation Steps

1. **Identify all legacy database usage**
   - Search for all imports of `patient_generator.database.Database`
   - List all files that need updating

2. **Update imports and usage**
   - Replace `from patient_generator.database import Database` with `from src.infrastructure.database_adapter import get_enhanced_database`
   - Update instantiation from `Database()` or `Database.get_instance()` to `get_enhanced_database()`

3. **Remove legacy implementation**
   - Delete `patient_generator/database.py`
   - Update any remaining references

4. **Update connection usage patterns**
   - Ensure all database operations use the context manager pattern:
   ```python
   async with db.get_connection() as conn:
       # Use connection
   ```

### Test Cases

```python
# tests/test_database_consolidation.py

import pytest
from src.infrastructure.database_adapter import get_enhanced_database

class TestDatabaseConsolidation:
    """Verify database consolidation is complete and working"""
    
    def test_no_legacy_imports(self):
        """Ensure no files import the legacy database"""
        # Scan codebase for "from patient_generator.database import"
        # Should find zero occurrences
        
    async def test_connection_pool_working(self):
        """Verify connection pooling is active"""
        db = get_enhanced_database()
        
        # Get pool status before
        status_before = db.get_pool_status()
        
        # Create multiple connections
        async with db.get_connection() as conn1:
            async with db.get_connection() as conn2:
                # Both should work
                assert conn1 is not None
                assert conn2 is not None
        
        # Pool should show connections were reused
        status_after = db.get_pool_status()
        assert status_after['pool']['in_use'] == 0
        
    async def test_concurrent_operations(self):
        """Test multiple concurrent database operations"""
        db = get_enhanced_database()
        
        async def query_task(n):
            async with db.get_connection() as conn:
                result = await conn.fetchone("SELECT $1::int", n)
                return result[0]
        
        # Run 10 concurrent queries
        results = await asyncio.gather(*[query_task(i) for i in range(10)])
        assert results == list(range(10))
```

### Verification Steps
1. Run all existing tests - they should pass without modification
2. Monitor database connections during load test - should stay under max_connections
3. Check application logs - no connection exhaustion errors
4. Verify metrics endpoint shows proper pool statistics

---

## Task 2: Patient Generation Pipeline Optimization

### Objective
Optimize the patient generation pipeline to handle large datasets efficiently without memory issues or file I/O bottlenecks.

### Current State
- Temporal configuration requires writing/reading injuries.json file
- No true streaming - entire patient list kept in memory
- Inefficient batch processing
- Race conditions possible with concurrent temporal generations

### Implementation Steps

1. **Replace injuries.json manipulation with in-memory configuration**

```python
# src/domain/services/patient_generation_service.py

# Instead of writing to injuries.json:
async def _run_generation_task(job_id: str, config: Dict[str, Any], ...):
    # Pass temporal config directly to flow simulator
    if temporal_config_present:
        temporal_config = {
            "total_patients": inner_config.get("total_patients", 1440),
            "days_of_fighting": inner_config.get("days_of_fighting", 8),
            # ... rest of config
        }
        
        # Initialize flow simulator with temporal config
        flow_simulator = PatientFlowSimulator(
            self.config_manager,
            temporal_config=temporal_config
        )
```

2. **Implement true streaming generation**

```python
# src/domain/services/patient_generation_service.py

class PatientGenerationPipeline:
    async def generate_streaming(
        self, 
        context: GenerationContext, 
        chunk_size: int = 1000
    ) -> AsyncIterator[List[Patient]]:
        """Generate patients in memory-efficient chunks"""
        
        total_patients = context.config.total_patients
        
        for start_idx in range(0, total_patients, chunk_size):
            end_idx = min(start_idx + chunk_size, total_patients)
            
            # Generate chunk
            chunk = await self._generate_patient_chunk(start_idx, end_idx)
            
            # Process chunk (demographics, medical conditions)
            processed_chunk = await self._process_chunk(chunk)
            
            # Yield for immediate writing
            yield processed_chunk
            
            # Let other tasks run
            await asyncio.sleep(0)
```

3. **Implement streaming file writers**

```python
# src/domain/services/output_writer.py

class StreamingOutputWriter:
    """Write patient data in streaming fashion"""
    
    async def write_json_streaming(
        self, 
        patient_chunks: AsyncIterator[List[Patient]], 
        output_path: str
    ):
        """Write JSON in streaming chunks"""
        async with aiofiles.open(output_path, 'w') as f:
            await f.write('[\n')
            
            first_chunk = True
            async for chunk in patient_chunks:
                for i, patient in enumerate(chunk):
                    if not first_chunk or i > 0:
                        await f.write(',\n')
                    
                    patient_json = json.dumps(patient.to_dict(), indent=2)
                    await f.write(patient_json)
                
                first_chunk = False
                
            await f.write('\n]')
```

### Test Cases

```python
# tests/test_generation_optimization.py

class TestGenerationOptimization:
    """Test optimized generation pipeline"""
    
    async def test_no_injuries_file_modification(self):
        """Ensure injuries.json is never modified during generation"""
        # Get original content
        original_content = Path("patient_generator/injuries.json").read_text()
        
        # Run temporal generation
        context = GenerationContext(
            config=create_temporal_config(),
            job_id="test-job",
            output_directory="/tmp/test"
        )
        
        service = AsyncPatientGenerationService()
        await service.generate_patients(context)
        
        # Verify file unchanged
        current_content = Path("patient_generator/injuries.json").read_text()
        assert original_content == current_content
        
    async def test_memory_efficient_generation(self):
        """Test generation doesn't load all patients in memory"""
        import tracemalloc
        
        tracemalloc.start()
        
        # Generate 10,000 patients
        context = GenerationContext(
            config=create_large_config(10000),
            job_id="test-job",
            output_directory="/tmp/test"
        )
        
        service = AsyncPatientGenerationService()
        
        # Track peak memory during generation
        peak_memory = 0
        async def monitor_memory():
            nonlocal peak_memory
            while True:
                current, peak = tracemalloc.get_traced_memory()
                peak_memory = max(peak_memory, peak)
                await asyncio.sleep(0.1)
        
        monitor_task = asyncio.create_task(monitor_memory())
        
        try:
            await service.generate_patients(context)
        finally:
            monitor_task.cancel()
        
        # Peak memory should be < 100MB (not holding all patients)
        assert peak_memory < 100 * 1024 * 1024
        
    async def test_concurrent_temporal_generation(self):
        """Test multiple temporal generations don't interfere"""
        # Run 3 concurrent temporal generations
        configs = [
            create_temporal_config(warfare_types={"conventional": True}),
            create_temporal_config(warfare_types={"urban": True}),
            create_temporal_config(warfare_types={"artillery": True})
        ]
        
        tasks = []
        for i, config in enumerate(configs):
            context = GenerationContext(
                config=config,
                job_id=f"test-job-{i}",
                output_directory=f"/tmp/test-{i}"
            )
            service = AsyncPatientGenerationService()
            tasks.append(service.generate_patients(context))
        
        results = await asyncio.gather(*tasks)
        
        # All should complete successfully
        assert all(r['status'] == 'completed' for r in results)
        
        # Verify each has correct warfare type
        for i, config in enumerate(configs):
            output_file = f"/tmp/test-{i}/patients.json"
            with open(output_file) as f:
                patients = json.load(f)
                # Check patients have expected characteristics
```

### Verification Steps
1. Generate 100K patients - should complete without memory errors
2. Run 5 concurrent generation jobs - no file conflicts
3. Monitor memory usage during generation - should stay flat
4. Verify output files are valid and complete

---

## Task 3: Smart Caching Strategy Implementation

### Objective
Implement intelligent caching to reduce database queries and improve response times.

### Current State
- Cache used only for demographics and medical data
- Cache warming happens per job (inefficient)
- No caching of computed values
- No cache invalidation strategy

### Implementation Steps

1. **Implement startup cache warming**

```python
# src/core/cache_warmup.py

class CacheWarmupService:
    """Warm critical caches on application startup"""
    
    def __init__(self, cache_service: CacheService, db: Database):
        self.cache = cache_service
        self.db = db
        
    async def warm_all_caches(self):
        """Warm all critical caches"""
        await asyncio.gather(
            self._warm_demographics_cache(),
            self._warm_medical_cache(),
            self._warm_configuration_cache(),
            self._warm_computation_cache()
        )
        
    async def _warm_configuration_cache(self):
        """Cache frequently used configurations"""
        # Get top 10 most used configs from last 30 days
        configs = await self.db.fetch_all("""
            SELECT DISTINCT c.* 
            FROM configurations c
            JOIN jobs j ON j.config_id = c.id
            WHERE j.created_at > NOW() - INTERVAL '30 days'
            GROUP BY c.id
            ORDER BY COUNT(j.id) DESC
            LIMIT 10
        """)
        
        for config in configs:
            cache_key = f"config:{config['id']}:v2"
            await self.cache.set(cache_key, dict(config), ttl=86400)

# In src/main.py lifespan:
async def lifespan(app: FastAPI):
    # Startup
    if settings.CACHE_ENABLED:
        warmup_service = CacheWarmupService(cache_service, db)
        await warmup_service.warm_all_caches()
```

2. **Add computation caching layer**

```python
# src/core/computation_cache.py

class ComputationCache:
    """Cache expensive computations"""
    
    def __init__(self, cache_service: CacheService):
        self.cache = cache_service
        
    async def get_or_compute(
        self, 
        cache_key: str, 
        compute_func: Callable, 
        ttl: int = 3600
    ):
        """Get from cache or compute and cache"""
        # Try cache first
        cached = await self.cache.get(cache_key)
        if cached is not None:
            return cached
            
        # Compute
        result = await compute_func()
        
        # Cache result
        await self.cache.set(cache_key, result, ttl=ttl)
        
        return result

# Usage in FlowSimulator:
async def _get_warfare_injury_distribution(self, warfare_type: str, base_mix: Dict):
    cache_key = f"injury_dist:{warfare_type}:{hash(str(sorted(base_mix.items())))}"
    
    return await self.comp_cache.get_or_compute(
        cache_key,
        lambda: self._compute_injury_distribution(warfare_type, base_mix),
        ttl=7200  # 2 hours
    )
```

3. **Implement cache invalidation**

```python
# src/api/v1/routers/configurations.py

@router.put("/configurations/{config_id}")
async def update_configuration(config_id: str, ...):
    # Update in database
    result = await config_repo.update(config_id, updates)
    
    # Invalidate related caches
    await cache_service.delete(f"config:{config_id}:v2")
    await cache_service.invalidate_pattern(f"computation:*:{config_id}:*")
    
    return result
```

### Test Cases

```python
# tests/test_smart_caching.py

class TestSmartCaching:
    """Test smart caching implementation"""
    
    async def test_cache_warmup_on_startup(self):
        """Verify caches are warmed on startup"""
        cache = CacheService(settings.REDIS_URL)
        await cache.initialize()
        
        # Clear all caches
        await cache.invalidate_pattern("*")
        
        # Run warmup
        warmup = CacheWarmupService(cache, db)
        await warmup.warm_all_caches()
        
        # Check expected keys exist
        assert await cache.exists("demographics:USA:male")
        assert await cache.exists("medical:conditions:BATTLE_TRAUMA")
        
    async def test_computation_caching(self):
        """Test expensive computations are cached"""
        cache = CacheService(settings.REDIS_URL)
        comp_cache = ComputationCache(cache)
        
        call_count = 0
        async def expensive_computation():
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.1)  # Simulate expensive work
            return {"result": "computed"}
        
        # First call - should compute
        result1 = await comp_cache.get_or_compute(
            "test:key", 
            expensive_computation
        )
        assert call_count == 1
        
        # Second call - should use cache
        result2 = await comp_cache.get_or_compute(
            "test:key", 
            expensive_computation
        )
        assert call_count == 1  # Not called again
        assert result1 == result2
        
    async def test_cache_invalidation(self):
        """Test cache invalidation on updates"""
        # Cache a configuration
        await cache.set("config:123:v2", {"name": "test"})
        
        # Update configuration
        await update_configuration("123", {"name": "updated"})
        
        # Cache should be invalidated
        assert await cache.get("config:123:v2") is None
        
    async def test_no_repeated_cache_warming(self):
        """Ensure cache warming doesn't happen per job"""
        # Monitor cache warming calls
        warm_cache_calls = 0
        
        original_warm = CachedDemographicsService.warm_cache
        async def counting_warm(self):
            nonlocal warm_cache_calls
            warm_cache_calls += 1
            return await original_warm(self)
        
        CachedDemographicsService.warm_cache = counting_warm
        
        # Generate multiple jobs
        for i in range(3):
            context = GenerationContext(...)
            await service.generate_patients(context)
        
        # Should not warm cache (already warm from startup)
        assert warm_cache_calls == 0
```

### Verification Steps
1. Monitor Redis memory usage - should stabilize after warmup
2. Check cache hit rate - should be >90% for repeated operations  
3. Measure API response times - configuration lookups <10ms
4. Run load test - database query count should be minimal

---

## Implementation Order & Testing Strategy

### Phase 1: Database Consolidation (Day 1-2)
1. Create feature branch `refactor/database-consolidation`
2. Update all imports and usage
3. Run existing test suite
4. Remove legacy implementation
5. Run load tests to verify connection pooling

### Phase 2: Generation Pipeline (Day 3-5)  
1. Create feature branch `refactor/generation-pipeline`
2. Implement in-memory temporal config
3. Add streaming generation
4. Test with 100K patient generation
5. Verify memory usage stays flat

### Phase 3: Smart Caching (Day 6-7)
1. Create feature branch `refactor/smart-caching`
2. Implement startup cache warming
3. Add computation caching
4. Test cache hit rates
5. Verify performance improvements

### Integration Testing (Day 8)
1. Merge all branches to `develop`
2. Run full test suite
3. Perform load testing:
   - 10 concurrent jobs
   - 50K patients each
   - Monitor: memory, CPU, database connections, cache hit rate
4. Deploy to staging for real-world testing

## Success Metrics

- **Database connections**: Peak connections reduced by 70%
- **Generation time**: 50K patients in <2 minutes (from ~5 minutes)
- **Memory usage**: Flat memory profile during generation
- **Cache hit rate**: >90% for configuration lookups
- **API response time**: <50ms for job status checks
- **Concurrent jobs**: Support 10+ concurrent generations

## Rollback Plan

Each refactoring is isolated and can be rolled back independently:
1. Database: Revert to legacy implementation (1-hour rollback)
2. Generation: Revert to file-based temporal config (30-min rollback)
3. Caching: Disable cache warming (instant via feature flag)
