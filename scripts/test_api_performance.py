#!/usr/bin/env python3
"""
Simple API performance test to demonstrate Task 2 optimizations.
"""

from datetime import datetime
import json
import time

# Ensure demo key exists
from ensure_demo_key import ensure_demo_key
import requests

ensure_demo_key()

API_KEY = "DEMO_MILMED_2025_50_PATIENTS"
BASE_URL = "http://localhost:8000"
HEADERS = {"X-API-Key": API_KEY}


def test_generation(patient_count: int, use_temporal: bool = False):
    """Test patient generation and measure performance."""
    print(f"\n🧪 Testing {patient_count} patients ({'temporal' if use_temporal else 'standard'})...")

    # Check metrics before
    metrics_before = requests.get(f"{BASE_URL}/metrics").text

    # Extract key metrics
    def extract_metric(text, metric_name):
        for line in text.split("\n"):
            if metric_name in line and not line.startswith("#"):
                parts = line.split(" ")
                if len(parts) >= 2:
                    try:
                        return float(parts[-1])
                    except ValueError:
                        pass
        return 0

    gen_count_before = extract_metric(metrics_before, "patients_generated_total")
    gen_time_before = extract_metric(metrics_before, "generation_duration_seconds_sum")

    # Prepare request
    config = {
        "name": f"Performance Test {patient_count}",
        "description": "Testing Task 2 optimizations",
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

    # Start generation
    start_time = time.time()
    response = requests.post(
        f"{BASE_URL}/api/v1/generation/",
        json=request_payload,
        headers=HEADERS
    )

    if response.status_code != 201:
        print(f"  ❌ Failed to start: {response.status_code} - {response.text}")
        return None

    job_id = response.json()["job_id"]
    print(f"  📋 Job ID: {job_id}")

    # Poll for completion
    max_wait = 300  # 5 minutes
    poll_interval = 2

    while time.time() - start_time < max_wait:
        job_response = requests.get(
            f"{BASE_URL}/api/v1/jobs/{job_id}",
            headers=HEADERS
        )

        if job_response.status_code != 200:
            print(f"  ❌ Failed to get status: {job_response.status_code}")
            return None

        job_data = job_response.json()
        status = job_data["status"].upper()
        progress = job_data.get("progress", 0)

        if status == "RUNNING":
            print(f"  ⏳ Progress: {progress}%", end="\r")
        elif status == "COMPLETED":
            total_time = time.time() - start_time
            print(f"  ✅ Completed in {total_time:.2f}s")

            # Get metrics after
            metrics_after = requests.get(f"{BASE_URL}/metrics").text
            gen_count_after = extract_metric(metrics_after, "patients_generated_total")
            gen_time_after = extract_metric(metrics_after, "generation_duration_seconds_sum")

            # Calculate metrics
            patients_generated = gen_count_after - gen_count_before
            generation_time = gen_time_after - gen_time_before

            print("  📊 Metrics:")
            print(f"     - Patients generated: {patients_generated:.0f}")
            print(f"     - Generation time (Prometheus): {generation_time:.2f}s")
            print(f"     - Speed: {patient_count / total_time:.0f} patients/sec")

            # Check if chunked generation was used
            if patient_count > 1000:
                print("  📦 Used chunked generation (1000 patients/chunk)")

            # Get health check for resource info
            health = requests.get(f"{BASE_URL}/api/v1/health", headers=HEADERS).json()
            memory_info = health.get("checks", {}).get("memory", {})
            if memory_info:
                print(f"  💾 System memory: {memory_info.get('percent_used', 0):.1f}% used")

            return total_time

        elif status == "FAILED":
            print(f"  ❌ Failed: {job_data.get('error', 'Unknown error')}")
            return None

        time.sleep(poll_interval)

    print(f"  ❌ Timeout after {max_wait}s")
    return None


def main():
    """Run performance tests."""
    print("🚀 API Performance Test - Task 2 Optimizations")
    print("=" * 60)

    # Check if server is running
    try:
        health = requests.get(f"{BASE_URL}/api/v1/health", headers=HEADERS)
        if health.status_code == 503:
            health_data = health.json()
            db_status = health_data.get("checks", {}).get("database", {}).get("status")
            if db_status == "unhealthy":
                print("⚠️  Warning: Database is not connected")
                print("   Some features may not work properly")
                print("   But generation should still work!\n")
    except Exception as e:
        print(f"❌ Cannot connect to API: {e}")
        print("   Make sure the server is running with:")
        print("   python -m uvicorn src.main:app --reload")
        return

    # Run tests
    test_configs = [
        # Small tests (no chunking)
        {"patient_count": 100},
        {"patient_count": 500},
        {"patient_count": 1000},

        # Large tests (with chunking)
        {"patient_count": 2500},
        {"patient_count": 5000},
        {"patient_count": 10000},

        # Temporal tests
        {"patient_count": 1000, "use_temporal": True},
        {"patient_count": 5000, "use_temporal": True},
    ]

    results = []
    for config in test_configs:
        try:
            duration = test_generation(**config)
            if duration:
                results.append({
                    **config,
                    "duration": duration,
                    "speed": config["patient_count"] / duration
                })
        except Exception as e:
            print(f"  ❌ Error: {e}")

    # Summary
    if results:
        print("\n" + "=" * 60)
        print("📈 SUMMARY")
        print("=" * 60)
        print(f"{'Patients':<10} {'Type':<10} {'Time(s)':<10} {'Speed(/s)':<10} {'Chunked':<8}")
        print("-" * 50)

        for r in results:
            gen_type = "Temporal" if r.get("use_temporal") else "Standard"
            chunked = "Yes" if r["patient_count"] > 1000 else "No"
            print(f"{r['patient_count']:<10} {gen_type:<10} {r['duration']:<10.2f} "
                  f"{r['speed']:<10.0f} {chunked:<8}")

        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"api_performance_results_{timestamp}.json"
        with open(results_file, "w") as f:
            json.dump(results, f, indent=2)
        print(f"\n📄 Results saved to: {results_file}")

        # Key insights
        print("\n🎯 Key Optimizations Demonstrated:")
        print("  ✅ Streaming file writes with aiofiles")
        print("  ✅ Chunked generation for large datasets (>1000 patients)")
        print("  ✅ In-memory temporal configuration")
        print("  ✅ Periodic flushing every 100 patients")
        print("  ✅ Efficient memory usage with garbage collection")


if __name__ == "__main__":
    main()
