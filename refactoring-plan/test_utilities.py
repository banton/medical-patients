# Test Utilities for Refactoring

This file contains helper functions and utilities for testing the refactoring changes.

## Database Testing Utilities

```python
# tests/utils/database_helpers.py

import asyncio
from contextlib import asynccontextmanager
import psycopg2
from typing import List, Dict, Any

class DatabaseTestHelper:
    """Helper for database-related tests"""
    
    @staticmethod
    async def count_active_connections(db_url: str) -> int:
        """Count active database connections"""
        # Parse database name from URL
        db_name = db_url.split('/')[-1].split('?')[0]
        
        query = """
        SELECT count(*) 
        FROM pg_stat_activity 
        WHERE datname = %s 
        AND state = 'active'
        """
        
        # Use a separate connection to check
        conn = psycopg2.connect(db_url)
        try:
            cur = conn.cursor()
            cur.execute(query, (db_name,))
            return cur.fetchone()[0]
        finally:
            conn.close()
    
    @staticmethod
    async def simulate_concurrent_load(db, num_tasks: int = 50):
        """Simulate concurrent database load"""
        async def query_task(n):
            async with db.get_connection() as conn:
                result = await conn.fetchone(
                    "SELECT pg_sleep(0.1), $1::int", n
                )
                return result[1]
        
        # Run concurrent queries
        tasks = [query_task(i) for i in range(num_tasks)]
        results = await asyncio.gather(*tasks)
        return results
    
    @staticmethod
    @asynccontextmanager
    async def monitor_connections(db_url: str):
        """Context manager to monitor connection count changes"""
        before = await DatabaseTestHelper.count_active_connections(db_url)
        yield
        after = await DatabaseTestHelper.count_active_connections(db_url)
        
        # Connections should return to baseline
        assert after <= before + 1, f"Connection leak: {before} -> {after}"
```

## Memory Testing Utilities

```python
# tests/utils/memory_helpers.py

import tracemalloc
import psutil
import os
from typing import Callable, Tuple

class MemoryTestHelper:
    """Helper for memory usage tests"""
    
    @staticmethod
    def track_memory_usage(func: Callable) -> Tuple[Any, int, int]:
        """
        Track memory usage of a function.
        
        Returns:
            (result, peak_memory_mb, total_allocated_mb)
        """
        tracemalloc.start()
        
        # Get process memory before
        process = psutil.Process(os.getpid())
        mem_before = process.memory_info().rss / 1024 / 1024
        
        # Run function
        result = func()
        
        # Get memory stats
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        mem_after = process.memory_info().rss / 1024 / 1024
        
        return (
            result,
            peak / 1024 / 1024,  # Peak in MB
            mem_after - mem_before  # Total allocated in MB
        )
    
    @staticmethod
    async def monitor_memory_during_generation(
        generation_func: Callable,
        expected_max_mb: int = 500
    ):
        """Monitor memory usage during patient generation"""
        memory_samples = []
        
        async def sample_memory():
            process = psutil.Process(os.getpid())
            while True:
                mem_mb = process.memory_info().rss / 1024 / 1024
                memory_samples.append(mem_mb)
                await asyncio.sleep(0.1)
        
        # Start monitoring
        monitor_task = asyncio.create_task(sample_memory())
        
        try:
            # Run generation
            result = await generation_func()
            
            # Check peak memory
            peak_memory = max(memory_samples)
            assert peak_memory < expected_max_mb, \
                f"Memory usage too high: {peak_memory}MB > {expected_max_mb}MB"
            
            return result, memory_samples
            
        finally:
            monitor_task.cancel()
```

## Cache Testing Utilities

```python
# tests/utils/cache_helpers.py

from typing import Dict, List
import time

class CacheTestHelper:
    """Helper for cache-related tests"""
    
    @staticmethod
    async def measure_cache_performance(
        cache_service,
        operations: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """
        Measure cache operation performance.
        
        Args:
            operations: List of {'type': 'get'|'set', 'key': str, 'value': Any}
            
        Returns:
            Performance metrics
        """
        metrics = {
            'total_time': 0,
            'get_time': 0,
            'set_time': 0,
            'get_count': 0,
            'set_count': 0,
            'hit_count': 0,
            'miss_count': 0
        }
        
        start_time = time.time()
        
        for op in operations:
            op_start = time.time()
            
            if op['type'] == 'get':
                result = await cache_service.get(op['key'])
                op_time = time.time() - op_start
                
                metrics['get_time'] += op_time
                metrics['get_count'] += 1
                
                if result is not None:
                    metrics['hit_count'] += 1
                else:
                    metrics['miss_count'] += 1
                    
            elif op['type'] == 'set':
                await cache_service.set(op['key'], op['value'])
                op_time = time.time() - op_start
                
                metrics['set_time'] += op_time
                metrics['set_count'] += 1
        
        metrics['total_time'] = time.time() - start_time
        metrics['hit_rate'] = (
            metrics['hit_count'] / metrics['get_count'] 
            if metrics['get_count'] > 0 else 0
        )
        
        return metrics
    
    @staticmethod
    async def verify_cache_warmup(cache_service, expected_keys: List[str]):
        """Verify expected keys exist after cache warmup"""
        missing_keys = []
        
        for key in expected_keys:
            if not await cache_service.exists(key):
                missing_keys.append(key)
        
        assert not missing_keys, f"Missing cache keys: {missing_keys}"
        
        # Also check TTLs are set appropriately
        for key in expected_keys:
            ttl = await cache_service.get_ttl(key)
            assert ttl > 0, f"Key {key} has no TTL set"
```

## Generation Testing Utilities

```python
# tests/utils/generation_helpers.py

import json
import tempfile
from pathlib import Path
from typing import Dict, Any, List
import ijson

class GenerationTestHelper:
    """Helper for patient generation tests"""
    
    @staticmethod
    def create_test_config(
        total_patients: int = 100,
        temporal: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """Create test configuration"""
        config = {
            "name": f"Test Config {total_patients}",
            "total_patients": total_patients,
            "injury_distribution": {
                "Disease": 0.52,
                "Non-Battle Injury": 0.33,
                "Battle Injury": 0.15
            }
        }
        
        if temporal:
            config.update({
                "base_date": "2025-06-01",
                "days_of_fighting": 8,
                "warfare_types": {
                    "conventional": True,
                    "artillery": True,
                    "urban": False
                },
                "intensity": "medium",
                "tempo": "sustained"
            })
        
        config.update(kwargs)
        return config
    
    @staticmethod
    def validate_patient_file(file_path: str, expected_count: int):
        """Validate generated patient file"""
        path = Path(file_path)
        assert path.exists(), f"Output file not found: {file_path}"
        
        # Check file is valid JSON
        with open(path) as f:
            # Use streaming parser for large files
            parser = ijson.items(f, 'item')
            count = 0
            
            for patient in parser:
                # Validate patient structure
                assert 'id' in patient
                assert 'injury_type' in patient
                assert 'triage_category' in patient
                assert 'movement_timeline' in patient
                count += 1
        
        assert count == expected_count, \
            f"Wrong patient count: {count} != {expected_count}"
    
    @staticmethod
    async def run_generation_benchmark(
        service,
        patient_counts: List[int]
    ) -> Dict[int, float]:
        """Benchmark generation performance"""
        results = {}
        
        for count in patient_counts:
            config = GenerationTestHelper.create_test_config(count)
            
            with tempfile.TemporaryDirectory() as tmpdir:
                context = GenerationContext(
                    config=config,
                    job_id=f"bench-{count}",
                    output_directory=tmpdir
                )
                
                start_time = time.time()
                await service.generate_patients(context)
                duration = time.time() - start_time
                
                results[count] = duration
                
                # Verify output
                GenerationTestHelper.validate_patient_file(
                    f"{tmpdir}/patients.json", 
                    count
                )
        
        return results
```

## Load Testing Script

```python
# tests/load_test.py

import asyncio
import argparse
import json
from datetime import datetime
from typing import List, Dict, Any

async def run_load_test(
    base_url: str,
    api_key: str,
    num_jobs: int = 10,
    patients_per_job: int = 10000
):
    """Run load test against the API"""
    
    async def create_job(session, job_num: int) -> Dict[str, Any]:
        """Create a single generation job"""
        config = {
            "name": f"Load Test Job {job_num}",
            "total_patients": patients_per_job,
            "injury_distribution": {
                "Disease": 0.52,
                "Non-Battle Injury": 0.33,
                "Battle Injury": 0.15
            }
        }
        
        # Add temporal config for some jobs
        if job_num % 3 == 0:
            config.update({
                "warfare_types": {"conventional": True},
                "base_date": "2025-06-01",
                "days_of_fighting": 5
            })
        
        headers = {"Authorization": f"Bearer {api_key}"}
        
        async with session.post(
            f"{base_url}/api/v1/generation/",
            json={"configuration": config},
            headers=headers
        ) as resp:
            return await resp.json()
    
    async def monitor_job(session, job_id: str) -> Dict[str, Any]:
        """Monitor job until completion"""
        headers = {"Authorization": f"Bearer {api_key}"}
        
        while True:
            async with session.get(
                f"{base_url}/api/v1/jobs/{job_id}",
                headers=headers
            ) as resp:
                job = await resp.json()
                
                if job['status'] in ['completed', 'failed']:
                    return job
                
                await asyncio.sleep(2)
    
    # Run test
    import aiohttp
    
    results = {
        "start_time": datetime.now().isoformat(),
        "num_jobs": num_jobs,
        "patients_per_job": patients_per_job,
        "jobs": []
    }
    
    async with aiohttp.ClientSession() as session:
        # Create all jobs
        print(f"Creating {num_jobs} jobs...")
        create_tasks = [
            create_job(session, i) 
            for i in range(num_jobs)
        ]
        job_responses = await asyncio.gather(*create_tasks)
        
        # Monitor all jobs
        print("Monitoring job completion...")
        monitor_tasks = [
            monitor_job(session, resp['job_id']) 
            for resp in job_responses
        ]
        completed_jobs = await asyncio.gather(*monitor_tasks)
        
        # Collect results
        for job in completed_jobs:
            results["jobs"].append({
                "job_id": job['job_id'],
                "status": job['status'],
                "duration": job.get('duration'),
                "patient_count": job.get('summary', {}).get('total_patients')
            })
    
    results["end_time"] = datetime.now().isoformat()
    
    # Summary
    successful = sum(1 for j in results["jobs"] if j["status"] == "completed")
    print(f"\nLoad Test Complete:")
    print(f"  Total Jobs: {num_jobs}")
    print(f"  Successful: {successful}")
    print(f"  Failed: {num_jobs - successful}")
    
    return results

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://localhost:8000")
    parser.add_argument("--api-key", required=True)
    parser.add_argument("--jobs", type=int, default=10)
    parser.add_argument("--patients", type=int, default=10000)
    
    args = parser.parse_args()
    
    results = asyncio.run(run_load_test(
        args.url,
        args.api_key,
        args.jobs,
        args.patients
    ))
    
    # Save results
    with open(f"load_test_{datetime.now():%Y%m%d_%H%M%S}.json", "w") as f:
        json.dump(results, f, indent=2)
```
