#!/usr/bin/env python3
"""
Performance monitoring scripts for refactoring validation
"""

import asyncio
from datetime import datetime
import json
import time
from typing import Any, Dict, List

import aiohttp
import asyncpg
import psutil


class PerformanceMonitor:
    """Monitor system performance during tests"""

    def __init__(self, db_url: str, redis_url: str = None):
        self.db_url = db_url
        self.redis_url = redis_url
        self.metrics = []
        self.monitoring = False

    async def start_monitoring(self, interval: float = 1.0):
        """Start monitoring system metrics"""
        self.monitoring = True

        while self.monitoring:
            metrics = await self._collect_metrics()
            self.metrics.append(metrics)
            await asyncio.sleep(interval)

    async def _collect_metrics(self) -> Dict[str, Any]:
        """Collect current system metrics"""
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk_io = psutil.disk_io_counters()

        # Database metrics
        db_metrics = await self._get_database_metrics()

        # Redis metrics if available
        redis_metrics = {}
        if self.redis_url:
            redis_metrics = await self._get_redis_metrics()

        return {
            "timestamp": datetime.now().isoformat(),
            "cpu_percent": cpu_percent,
            "memory": {
                "used_mb": memory.used / 1024 / 1024,
                "percent": memory.percent,
                "available_mb": memory.available / 1024 / 1024
            },
            "disk_io": {
                "read_mb": disk_io.read_bytes / 1024 / 1024,
                "write_mb": disk_io.write_bytes / 1024 / 1024
            },
            "database": db_metrics,
            "redis": redis_metrics
        }

    async def _get_database_metrics(self) -> Dict[str, Any]:
        """Get PostgreSQL metrics"""
        try:
            conn = await asyncpg.connect(self.db_url)

            # Active connections
            active_query = """
                SELECT count(*) as active_connections
                FROM pg_stat_activity
                WHERE state = 'active'
            """
            active_count = await conn.fetchval(active_query)

            # Connection pool stats
            pool_query = """
                SELECT count(*) as total_connections,
                       count(*) FILTER (WHERE state = 'idle') as idle_connections,
                       count(*) FILTER (WHERE state = 'idle in transaction') as idle_in_transaction
                FROM pg_stat_activity
                WHERE datname = current_database()
            """
            pool_stats = await conn.fetchone(pool_query)

            await conn.close()

            return {
                "active_connections": active_count,
                "total_connections": pool_stats["total_connections"],
                "idle_connections": pool_stats["idle_connections"],
                "idle_in_transaction": pool_stats["idle_in_transaction"]
            }
        except Exception as e:
            return {"error": str(e)}

    async def _get_redis_metrics(self) -> Dict[str, Any]:
        """Get Redis metrics"""
        try:
            import aioredis

            redis = await aioredis.from_url(self.redis_url)
            info = await redis.info()

            metrics = {
                "used_memory_mb": info.get("used_memory", 0) / 1024 / 1024,
                "connected_clients": info.get("connected_clients", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": 0
            }

            # Calculate hit rate
            total_ops = metrics["keyspace_hits"] + metrics["keyspace_misses"]
            if total_ops > 0:
                metrics["hit_rate"] = metrics["keyspace_hits"] / total_ops

            await redis.close()
            return metrics

        except Exception as e:
            return {"error": str(e)}

    def stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring = False

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of collected metrics"""
        if not self.metrics:
            return {}

        # Calculate averages and peaks
        cpu_values = [m["cpu_percent"] for m in self.metrics]
        memory_values = [m["memory"]["used_mb"] for m in self.metrics]
        db_connections = [m["database"].get("active_connections", 0) for m in self.metrics]

        summary = {
            "duration_seconds": len(self.metrics),
            "cpu": {
                "avg_percent": sum(cpu_values) / len(cpu_values),
                "max_percent": max(cpu_values),
                "min_percent": min(cpu_values)
            },
            "memory": {
                "avg_mb": sum(memory_values) / len(memory_values),
                "max_mb": max(memory_values),
                "min_mb": min(memory_values)
            },
            "database": {
                "avg_connections": sum(db_connections) / len(db_connections),
                "max_connections": max(db_connections),
                "min_connections": min(db_connections)
            }
        }

        # Add Redis summary if available
        if self.redis_url and self.metrics[0].get("redis"):
            hit_rates = [m["redis"].get("hit_rate", 0) for m in self.metrics if "redis" in m]
            if hit_rates:
                summary["redis"] = {
                    "avg_hit_rate": sum(hit_rates) / len(hit_rates),
                    "final_hit_rate": self.metrics[-1]["redis"].get("hit_rate", 0)
                }

        return summary

    def save_metrics(self, filename: str):
        """Save metrics to file"""
        with open(filename, "w") as f:
            json.dump({
                "metrics": self.metrics,
                "summary": self.get_summary()
            }, f, indent=2)


async def benchmark_generation(
    api_url: str,
    api_key: str,
    patient_counts: List[int],
    monitor: PerformanceMonitor
) -> Dict[int, Dict[str, Any]]:
    """Benchmark patient generation with different sizes"""

    results = {}

    async with aiohttp.ClientSession() as session:
        headers = {"Authorization": f"Bearer {api_key}"}

        for count in patient_counts:
            print(f"\nBenchmarking {count} patients...")

            # Start monitoring
            monitor_task = asyncio.create_task(monitor.start_monitoring())

            # Create generation job
            start_time = time.time()

            config = {
                "name": f"Benchmark {count}",
                "total_patients": count,
                "injury_distribution": {
                    "Disease": 0.52,
                    "Non-Battle Injury": 0.33,
                    "Battle Injury": 0.15
                }
            }

            async with session.post(
                f"{api_url}/api/v1/generation/",
                json={"configuration": config},
                headers=headers
            ) as resp:
                job_data = await resp.json()
                job_id = job_data["job_id"]

            # Wait for completion
            while True:
                async with session.get(
                    f"{api_url}/api/v1/jobs/{job_id}",
                    headers=headers
                ) as resp:
                    job = await resp.json()

                    if job["status"] in ["completed", "failed"]:
                        break

                await asyncio.sleep(2)

            duration = time.time() - start_time

            # Stop monitoring
            monitor.stop_monitoring()
            await monitor_task

            # Collect results
            results[count] = {
                "duration_seconds": duration,
                "status": job["status"],
                "patients_per_second": count / duration if duration > 0 else 0,
                "metrics_summary": monitor.get_summary()
            }

            # Reset metrics for next run
            monitor.metrics = []

            print(f"  Duration: {duration:.2f}s")
            print(f"  Rate: {results[count]['patients_per_second']:.0f} patients/second")
            print(f"  Peak Memory: {results[count]['metrics_summary']['memory']['max_mb']:.0f}MB")
            print(f"  Peak DB Connections: {results[count]['metrics_summary']['database']['max_connections']}")

    return results


async def test_concurrent_load(
    api_url: str,
    api_key: str,
    num_jobs: int,
    patients_per_job: int,
    monitor: PerformanceMonitor
) -> Dict[str, Any]:
    """Test concurrent job handling"""

    print(f"\nTesting {num_jobs} concurrent jobs with {patients_per_job} patients each...")

    # Start monitoring
    monitor_task = asyncio.create_task(monitor.start_monitoring())
    start_time = time.time()

    async with aiohttp.ClientSession() as session:
        headers = {"Authorization": f"Bearer {api_key}"}

        # Create all jobs concurrently
        async def create_job(job_num: int):
            config = {
                "name": f"Concurrent Test {job_num}",
                "total_patients": patients_per_job,
                "injury_distribution": {
                    "Disease": 0.52,
                    "Non-Battle Injury": 0.33,
                    "Battle Injury": 0.15
                }
            }

            # Add temporal config to some jobs
            if job_num % 3 == 0:
                config["warfare_types"] = {"conventional": True}
                config["base_date"] = "2025-06-01"

            async with session.post(
                f"{api_url}/api/v1/generation/",
                json={"configuration": config},
                headers=headers
            ) as resp:
                return await resp.json()

        # Create jobs
        job_responses = await asyncio.gather(*[
            create_job(i) for i in range(num_jobs)
        ])

        job_ids = [j["job_id"] for j in job_responses]

        # Monitor all jobs until completion
        completed = set()
        while len(completed) < num_jobs:
            for job_id in job_ids:
                if job_id in completed:
                    continue

                async with session.get(
                    f"{api_url}/api/v1/jobs/{job_id}",
                    headers=headers
                ) as resp:
                    job = await resp.json()

                    if job["status"] in ["completed", "failed"]:
                        completed.add(job_id)

            await asyncio.sleep(2)

    duration = time.time() - start_time

    # Stop monitoring
    monitor.stop_monitoring()
    await monitor_task

    return {
        "total_duration_seconds": duration,
        "jobs_completed": len(completed),
        "total_patients": num_jobs * patients_per_job,
        "patients_per_second": (num_jobs * patients_per_job) / duration,
        "metrics_summary": monitor.get_summary()
    }


async def main():
    """Run performance tests"""

    # Configuration
    API_URL = "http://localhost:8000"
    API_KEY = "your-api-key"
    DB_URL = "postgresql://user:pass@localhost:5432/dbname"
    REDIS_URL = "redis://localhost:6379/0"

    # Create monitor
    monitor = PerformanceMonitor(DB_URL, REDIS_URL)

    # Test 1: Generation scaling
    print("=== Generation Scaling Test ===")
    scaling_results = await benchmark_generation(
        API_URL, API_KEY,
        patient_counts=[1000, 5000, 10000, 50000],
        monitor=monitor
    )

    # Save results
    monitor.save_metrics("generation_scaling_metrics.json")

    # Test 2: Concurrent load
    print("\n=== Concurrent Load Test ===")
    concurrent_results = await test_concurrent_load(
        API_URL, API_KEY,
        num_jobs=10,
        patients_per_job=5000,
        monitor=monitor
    )

    # Save results
    monitor.save_metrics("concurrent_load_metrics.json")

    # Print summary
    print("\n=== Test Summary ===")
    print("\nGeneration Scaling:")
    for count, result in scaling_results.items():
        print(f"  {count:,} patients: {result['duration_seconds']:.1f}s "
              f"({result['patients_per_second']:.0f} patients/s)")

    print("\nConcurrent Load:")
    print(f"  Total Duration: {concurrent_results['total_duration_seconds']:.1f}s")
    print(f"  Total Patients: {concurrent_results['total_patients']:,}")
    print(f"  Rate: {concurrent_results['patients_per_second']:.0f} patients/s")
    print(f"  Peak DB Connections: {concurrent_results['metrics_summary']['database']['max_connections']}")
    print(f"  Peak Memory: {concurrent_results['metrics_summary']['memory']['max_mb']:.0f}MB")

    if "redis" in concurrent_results["metrics_summary"]:
        print(f"  Cache Hit Rate: {concurrent_results['metrics_summary']['redis']['final_hit_rate']:.1%}")


if __name__ == "__main__":
    asyncio.run(main())
