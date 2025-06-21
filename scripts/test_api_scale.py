#!/usr/bin/env python3
"""
API scale testing script to verify Task 2 optimizations.
Runs multiple generation requests and monitors Prometheus metrics.
"""

import asyncio
from datetime import datetime
import json
import os
import statistics
import sys
import time
from typing import Dict

import httpx
import psutil

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.ensure_demo_key import ensure_demo_key


class APIScaleTester:
    """Test API at scale and collect metrics."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.api_key = "DEMO_MILMED_2025_50_PATIENTS"
        self.headers = {"X-API-Key": self.api_key}
        self.results = []
        self.process = psutil.Process()

    async def wait_for_api(self, timeout: int = 30):
        """Wait for API to be ready."""
        print("⏳ Waiting for API to be ready...")
        start_time = time.time()

        async with httpx.AsyncClient() as client:
            while time.time() - start_time < timeout:
                try:
                    response = await client.get(f"{self.base_url}/api/v1/health")
                    if response.status_code == 200:
                        print("✅ API is ready!")
                        return True
                except Exception:
                    pass
                await asyncio.sleep(1)

        raise TimeoutError("API did not become ready in time")

    async def get_metrics(self) -> Dict:
        """Fetch Prometheus metrics."""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/metrics")
            if response.status_code == 200:
                return self._parse_prometheus_metrics(response.text)
            return {}

    def _parse_prometheus_metrics(self, text: str) -> Dict:
        """Parse Prometheus metrics text format."""
        metrics = {}
        for line in text.split("\n"):
            if line and not line.startswith("#"):
                parts = line.split(" ")
                if len(parts) == 2:
                    metric_name = parts[0].split("{")[0]
                    try:
                        value = float(parts[1])
                        if metric_name not in metrics:
                            metrics[metric_name] = []
                        metrics[metric_name].append(value)
                    except ValueError:
                        pass
        return metrics

    async def run_generation_test(
        self,
        patient_count: int,
        use_temporal: bool = False,
        concurrent_requests: int = 1
    ) -> Dict:
        """Run a generation test with metrics collection."""
        print(f"\n🧪 Testing: {patient_count} patients, "
              f"{'temporal' if use_temporal else 'standard'} generation, "
              f"{concurrent_requests} concurrent requests")

        # Get baseline metrics
        metrics_before = await self.get_metrics()
        memory_before = self.process.memory_info().rss / 1024 / 1024  # MB

        # Prepare request payload
        config = {
            "name": f"Scale Test {patient_count}",
            "description": "API scale testing",
            "count": patient_count,
            "injury_distribution": {
                "Disease": 0.52,
                "Non-Battle Injury": 0.33,
                "Battle Injury": 0.15
            },
            "front_configs": [],
            "facility_configs": [],
        }

        if use_temporal:
            config.update({
                "total_patients": patient_count,
                "days_of_fighting": 8,
                "base_date": "2025-06-01",
                "warfare_types": {
                    "conventional": True,
                    "urban": True,
                    "artillery": True
                },
                "intensity": "high",
                "tempo": "sustained",
                "environmental_conditions": {"night_operations": True},
                "special_events": {"mass_casualty": True}
            })

        request_payload = {
            "configuration": config,
            "output_formats": ["json"],
            "use_compression": False,
            "use_encryption": False
        }

        # Run concurrent requests
        start_time = time.time()
        tasks = []

        async with httpx.AsyncClient(timeout=300.0) as client:
            for i in range(concurrent_requests):
                task = self._run_single_generation(client, request_payload, i)
                tasks.append(task)

            results = await asyncio.gather(*tasks, return_exceptions=True)

        end_time = time.time()
        duration = end_time - start_time

        # Get final metrics
        metrics_after = await self.get_metrics()
        memory_after = self.process.memory_info().rss / 1024 / 1024  # MB

        # Analyze results
        successful = [r for r in results if isinstance(r, dict) and r.get("success")]
        failed = [r for r in results if not (isinstance(r, dict) and r.get("success"))]

        # Calculate metrics differences
        generation_times = []
        if "generation_duration_seconds_sum" in metrics_after:
            after_sum = sum(metrics_after.get("generation_duration_seconds_sum", [0]))
            before_sum = sum(metrics_before.get("generation_duration_seconds_sum", [0]))
            generation_times = [after_sum - before_sum]

        db_connections_used = 0
        if "db_connections_active" in metrics_after:
            max_after = max(metrics_after.get("db_connections_active", [0]))
            max_before = max(metrics_before.get("db_connections_active", [0]))
            db_connections_used = max_after - max_before

        return {
            "patient_count": patient_count,
            "use_temporal": use_temporal,
            "concurrent_requests": concurrent_requests,
            "total_duration": duration,
            "successful_requests": len(successful),
            "failed_requests": len(failed),
            "avg_time_per_request": duration / concurrent_requests if concurrent_requests > 0 else 0,
            "total_patients_per_second": (patient_count * len(successful)) / duration if duration > 0 else 0,
            "memory_before_mb": memory_before,
            "memory_after_mb": memory_after,
            "memory_increase_mb": memory_after - memory_before,
            "db_connections_peak": db_connections_used,
            "generation_times": generation_times,
            "chunked_generation": patient_count > 1000,
            "individual_results": results
        }

    async def _run_single_generation(self, client: httpx.AsyncClient, payload: Dict, request_id: int) -> Dict:
        """Run a single generation request."""
        try:
            # Start generation
            response = await client.post(
                f"{self.base_url}/api/v1/generation/",
                json=payload,
                headers=self.headers
            )

            if response.status_code != 201:
                return {"success": False, "error": f"Failed to start: {response.status_code}"}

            job_id = response.json()["job_id"]

            # Poll for completion
            start_time = time.time()
            max_wait = 300  # 5 minutes

            while time.time() - start_time < max_wait:
                job_response = await client.get(
                    f"{self.base_url}/api/v1/jobs/{job_id}",
                    headers=self.headers
                )

                if job_response.status_code != 200:
                    return {"success": False, "error": f"Failed to get job status: {job_response.status_code}"}

                job_data = job_response.json()
                status = job_data["status"].upper()

                if status == "COMPLETED":
                    duration = time.time() - start_time
                    return {
                        "success": True,
                        "request_id": request_id,
                        "job_id": job_id,
                        "duration": duration,
                        "patient_count": payload["configuration"]["count"]
                    }
                if status == "FAILED":
                    return {"success": False, "error": job_data.get("error", "Unknown error")}

                await asyncio.sleep(2)

            return {"success": False, "error": "Timeout waiting for completion"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def run_scale_tests(self):
        """Run comprehensive scale tests."""
        print("🚀 Starting API Scale Tests for Task 2 Optimizations")
        print("=" * 60)

        # Ensure demo key exists
        ensure_demo_key()

        # Wait for API
        await self.wait_for_api()

        # Test configurations
        test_configs = [
            # Single request tests - baseline
            {"patient_count": 100, "concurrent_requests": 1},
            {"patient_count": 1000, "concurrent_requests": 1},
            {"patient_count": 5000, "concurrent_requests": 1},  # Chunked
            {"patient_count": 10000, "concurrent_requests": 1},  # Chunked

            # Concurrent request tests
            {"patient_count": 1000, "concurrent_requests": 3},
            {"patient_count": 5000, "concurrent_requests": 2},

            # Temporal generation tests
            {"patient_count": 1000, "use_temporal": True, "concurrent_requests": 1},
            {"patient_count": 5000, "use_temporal": True, "concurrent_requests": 1},

            # Stress test
            {"patient_count": 2000, "concurrent_requests": 5},
        ]

        for config in test_configs:
            try:
                result = await self.run_generation_test(**config)
                self.results.append(result)

                # Print summary
                print("\n📊 Results:")
                print(f"  ✅ Success rate: {result['successful_requests']}/{result['concurrent_requests']}")
                print(f"  ⏱️  Total time: {result['total_duration']:.2f}s")
                print(f"  🚄 Speed: {result['total_patients_per_second']:.0f} patients/sec")
                print(f"  💾 Memory: {result['memory_before_mb']:.0f}MB → {result['memory_after_mb']:.0f}MB")
                print(f"  🔌 Peak DB connections: {result['db_connections_peak']}")

                if result["chunked_generation"]:
                    print("  📦 Used chunked generation")

                # Small delay between tests
                await asyncio.sleep(5)

            except Exception as e:
                print(f"  ❌ Test failed: {e}")

        # Print final summary
        self._print_summary()

    def _print_summary(self):
        """Print test summary with insights."""
        print("\n" + "=" * 60)
        print("📈 SCALE TEST SUMMARY")
        print("=" * 60)

        # Filter successful results
        successful_results = [r for r in self.results if r["successful_requests"] > 0]

        if not successful_results:
            print("❌ No successful tests")
            return

        # Analyze chunking effectiveness
        print("\n🔍 Chunking Effectiveness:")
        chunked = [r for r in successful_results if r["chunked_generation"]]
        non_chunked = [r for r in successful_results if not r["chunked_generation"]]

        if chunked and non_chunked:
            avg_memory_per_patient_chunked = statistics.mean([
                r["memory_increase_mb"] / (r["patient_count"] * r["successful_requests"])
                for r in chunked
            ])
            avg_memory_per_patient_non_chunked = statistics.mean([
                r["memory_increase_mb"] / (r["patient_count"] * r["successful_requests"])
                for r in non_chunked
            ])

            improvement = (1 - avg_memory_per_patient_chunked / avg_memory_per_patient_non_chunked) * 100
            print(f"  Memory efficiency improvement: {improvement:.0f}%")
            print(f"  Chunked: {avg_memory_per_patient_chunked:.4f} MB/patient")
            print(f"  Non-chunked: {avg_memory_per_patient_non_chunked:.4f} MB/patient")

        # Analyze concurrency
        print("\n🔄 Concurrency Performance:")
        by_concurrent = {}
        for r in successful_results:
            key = r["concurrent_requests"]
            if key not in by_concurrent:
                by_concurrent[key] = []
            by_concurrent[key].append(r["total_patients_per_second"])

        for concurrent, speeds in sorted(by_concurrent.items()):
            avg_speed = statistics.mean(speeds)
            print(f"  {concurrent} concurrent: {avg_speed:.0f} patients/sec average")

        # Temporal vs Standard
        print("\n⚔️ Temporal vs Standard Generation:")
        temporal = [r for r in successful_results if r["use_temporal"]]
        standard = [r for r in successful_results if not r["use_temporal"]]

        if temporal and standard:
            avg_speed_temporal = statistics.mean([r["total_patients_per_second"] for r in temporal])
            avg_speed_standard = statistics.mean([r["total_patients_per_second"] for r in standard])
            print(f"  Temporal: {avg_speed_temporal:.0f} patients/sec")
            print(f"  Standard: {avg_speed_standard:.0f} patients/sec")

        # Key insights
        print("\n🎯 Key Insights:")

        max_patients = max([r["patient_count"] * r["successful_requests"] for r in successful_results])
        print(f"  ✅ Successfully generated up to {max_patients:,} patients")

        max_concurrent = max([r["concurrent_requests"] for r in successful_results])
        print(f"  ✅ Handled up to {max_concurrent} concurrent requests")

        avg_db_connections = statistics.mean([r["db_connections_peak"] for r in successful_results])
        print(f"  ✅ Average peak DB connections: {avg_db_connections:.0f}")

        # Save detailed results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"scale_test_results_{timestamp}.json"
        with open(results_file, "w") as f:
            json.dump(self.results, f, indent=2)
        print(f"\n📄 Detailed results saved to: {results_file}")


async def main():
    """Run scale tests."""
    tester = APIScaleTester()

    print("⚠️  Make sure the API server is running with:")
    print("   python -m uvicorn src.main:app --reload")
    print("")

    try:
        await tester.run_scale_tests()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure:")
        print("1. The API server is running")
        print("2. Database is available")
        print("3. Demo API key exists")


if __name__ == "__main__":
    asyncio.run(main())
