#!/usr/bin/env python3
"""
Performance Baseline Script for v1.2.0 EPIC-001 Refactoring
Captures metrics before optimization to measure improvement
"""

import asyncio
import time
import psutil
import os
from datetime import datetime
import json
from pathlib import Path
import sys

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.infrastructure.database_pool import get_pool


async def measure_database_connections():
    """Measure active database connections"""
    pool = get_pool()
    
    # Get pool stats
    stats = {
        "pool_size": pool.size(),
        "pool_checked_out": pool.checked_out_connections(),
        "pool_overflow": pool.overflow(),
        "pool_total": pool.size() + pool.overflow()
    }
    
    # Also check postgres directly
    async with pool.acquire() as conn:
        result = await conn.fetchone("""
            SELECT COUNT(*) 
            FROM pg_stat_activity 
            WHERE datname = current_database() 
            AND state = 'active'
        """)
        stats["postgres_active_connections"] = result[0]
    
    return stats


async def measure_generation_performance(patient_count: int):
    """Measure generation time and memory usage"""
    import httpx
    from config import API_BASE_URL, DEMO_API_KEY
    
    # Record start metrics
    process = psutil.Process()
    start_memory = process.memory_info().rss / 1024 / 1024  # MB
    start_time = time.time()
    
    # Generate patients
    async with httpx.AsyncClient(timeout=300.0) as client:
        response = await client.post(
            f"{API_BASE_URL}/api/v1/generation/",
            headers={"X-API-Key": DEMO_API_KEY},
            json={
                "config": {
                    "total_patients": patient_count,
                    "start_date": "2024-06-01T00:00:00",
                    "battle_rhythm": {
                        "A": {
                            "phase": "low"
                        }
                    }
                }
            }
        )
        
        if response.status_code != 200:
            raise Exception(f"Generation failed: {response.text}")
        
        job_id = response.json()["job_id"]
        
        # Wait for completion
        while True:
            status_response = await client.get(
                f"{API_BASE_URL}/api/v1/jobs/{job_id}",
                headers={"X-API-Key": DEMO_API_KEY}
            )
            job_status = status_response.json()
            
            if job_status["status"] in ["completed", "failed"]:
                break
            
            await asyncio.sleep(1)
    
    # Record end metrics
    end_time = time.time()
    peak_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    return {
        "patient_count": patient_count,
        "generation_time_seconds": end_time - start_time,
        "start_memory_mb": start_memory,
        "peak_memory_mb": peak_memory,
        "memory_growth_mb": peak_memory - start_memory,
        "patients_per_second": patient_count / (end_time - start_time)
    }


async def run_baseline_tests():
    """Run all baseline performance tests"""
    print("📊 Capturing Performance Baseline for v1.2.0 EPIC-001")
    print("=" * 60)
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "version": "pre-optimization",
        "tests": {}
    }
    
    # Test 1: Database Connections
    print("\n🔗 Testing Database Connections...")
    db_stats = await measure_database_connections()
    results["tests"]["database_connections"] = db_stats
    print(f"  Active connections: {db_stats['postgres_active_connections']}")
    print(f"  Pool total: {db_stats['pool_total']}")
    
    # Test 2: Small Generation (1K patients)
    print("\n⚡ Testing 1,000 patient generation...")
    small_gen = await measure_generation_performance(1000)
    results["tests"]["generation_1k"] = small_gen
    print(f"  Time: {small_gen['generation_time_seconds']:.2f}s")
    print(f"  Memory growth: {small_gen['memory_growth_mb']:.2f}MB")
    print(f"  Speed: {small_gen['patients_per_second']:.2f} patients/s")
    
    # Test 3: Medium Generation (10K patients)
    print("\n⚡ Testing 10,000 patient generation...")
    medium_gen = await measure_generation_performance(10000)
    results["tests"]["generation_10k"] = medium_gen
    print(f"  Time: {medium_gen['generation_time_seconds']:.2f}s")
    print(f"  Memory growth: {medium_gen['memory_growth_mb']:.2f}MB")
    print(f"  Speed: {medium_gen['patients_per_second']:.2f} patients/s")
    
    # Test 4: Large Generation (50K patients) - only if previous tests were fast
    if medium_gen['generation_time_seconds'] < 120:  # Less than 2 minutes
        print("\n⚡ Testing 50,000 patient generation...")
        large_gen = await measure_generation_performance(50000)
        results["tests"]["generation_50k"] = large_gen
        print(f"  Time: {large_gen['generation_time_seconds']:.2f}s")
        print(f"  Memory growth: {large_gen['memory_growth_mb']:.2f}MB")
        print(f"  Speed: {large_gen['patients_per_second']:.2f} patients/s")
    
    # Save results
    output_file = Path("baseline_metrics.json")
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✅ Baseline metrics saved to: {output_file}")
    print("\n📈 Summary:")
    print(f"  Database connections: {db_stats['postgres_active_connections']}")
    print(f"  1K generation speed: {small_gen['patients_per_second']:.2f} patients/s")
    print(f"  10K generation speed: {medium_gen['patients_per_second']:.2f} patients/s")
    if "generation_50k" in results["tests"]:
        print(f"  50K generation speed: {results['tests']['generation_50k']['patients_per_second']:.2f} patients/s")


if __name__ == "__main__":
    # Ensure we have API running
    print("⚠️  Make sure the API is running (task dev)")
    input("Press Enter to continue...")
    
    asyncio.run(run_baseline_tests())