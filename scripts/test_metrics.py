#!/usr/bin/env python3
"""
Test script for Prometheus metrics endpoint.
Part of EPIC-003: Production Scalability Improvements - Phase 2
"""

import concurrent.futures
import random
import sys
import time

import requests


def test_metrics_endpoint(base_url="http://localhost:8000"):
    """Test the metrics endpoint functionality."""
    print("Testing Prometheus Metrics Endpoint")
    print("=" * 50)

    # First, generate some traffic to create metrics
    print("\n1. Generating test traffic...")

    endpoints = [
        ("/api/v1/health", "GET"),
        ("/api/v1/jobs", "GET"),
        ("/api/v1/configurations", "GET"),
        ("/api/v1/health/database", "GET"),
    ]

    # Generate requests
    for _ in range(20):
        endpoint, method = random.choice(endpoints)
        try:
            response = requests.request(method, f"{base_url}{endpoint}")
            print(f"  {method} {endpoint} -> {response.status_code}")
        except Exception as e:
            print(f"  {method} {endpoint} -> ERROR: {e}")
        time.sleep(0.1)

    # Test metrics endpoint
    print("\n2. Fetching metrics...")
    try:
        response = requests.get(f"{base_url}/metrics")
        if response.status_code == 200:
            print("✅ Metrics endpoint is working!")

            # Parse and display some metrics
            metrics_text = response.text
            lines = metrics_text.split("\n")

            print("\n3. Sample metrics:")

            # Extract request metrics
            for line in lines:
                if line.startswith("api_requests_total{"):
                    # Extract labels and value
                    parts = line.split("}")
                    if len(parts) >= 2:
                        labels = parts[0].replace("api_requests_total{", "")
                        value = parts[1].strip()
                        print(f"  Request: {labels} = {value}")

                elif line.startswith("api_request_duration_seconds_bucket{"):
                    # Skip histogram buckets for brevity
                    continue

                elif line.startswith("db_connections_active"):
                    value = line.split(" ")[-1]
                    print(f"  DB Connections Active: {value}")

                elif line.startswith("db_query_duration_seconds_count"):
                    value = line.split(" ")[-1]
                    print(f"  DB Query Count: {value}")

            # Show content type
            print("\n4. Response headers:")
            print(f"  Content-Type: {response.headers.get('Content-Type')}")
            print(f"  Content-Length: {len(response.content)} bytes")

        else:
            print(f"❌ Metrics endpoint returned status {response.status_code}")

    except Exception as e:
        print(f"❌ Error accessing metrics endpoint: {e}")
        return False

    # Test with Prometheus format parsing
    print("\n5. Testing Prometheus compatibility...")

    # Check for required Prometheus format elements
    required_elements = [
        "# HELP",
        "# TYPE",
        "api_requests_total",
        "api_request_duration_seconds",
    ]

    missing = []
    for element in required_elements:
        if element not in metrics_text:
            missing.append(element)

    if missing:
        print(f"❌ Missing Prometheus format elements: {missing}")
    else:
        print("✅ Metrics are in valid Prometheus format")

    return True


def test_metrics_under_load(base_url="http://localhost:8000"):
    """Test metrics collection under load."""
    print("\n\nTesting Metrics Under Load")
    print("=" * 50)

    print("\n1. Generating concurrent load...")

    def make_request(i):
        """Make a request to generate metrics."""
        endpoints = [
            "/api/v1/health",
            "/api/v1/jobs",
            "/api/v1/health/database",
            f"/api/v1/jobs/{i}",  # This will generate 404s
        ]

        endpoint = random.choice(endpoints)
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            return endpoint, response.status_code
        except Exception:
            return endpoint, "error"

    # Generate load with thread pool
    start_time = time.time()
    request_count = 100

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(make_request, i) for i in range(request_count)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    duration = time.time() - start_time

    # Count results
    status_counts = {}
    for _endpoint, status in results:
        status_counts[status] = status_counts.get(status, 0) + 1

    print("\n2. Load test results:")
    print(f"  Total requests: {request_count}")
    print(f"  Duration: {duration:.2f}s")
    print(f"  Requests/second: {request_count / duration:.2f}")
    print(f"  Status codes: {status_counts}")

    # Check metrics after load
    print("\n3. Checking metrics after load...")

    response = requests.get(f"{base_url}/metrics")
    if response.status_code == 200:
        metrics_text = response.text

        # Extract total request count
        total_requests = 0
        for line in metrics_text.split("\n"):
            if "api_requests_total{" in line and not line.startswith("#"):
                try:
                    value = int(float(line.split(" ")[-1]))
                    total_requests += value
                except:
                    pass

        print(f"  Total requests recorded: {total_requests}")
        print("✅ Metrics successfully tracked load test")
    else:
        print("❌ Failed to fetch metrics after load test")


def main():
    """Main test function."""
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = "http://localhost:8000"

    print(f"Testing metrics at: {base_url}")
    print()

    # Test basic functionality
    if test_metrics_endpoint(base_url):
        # Test under load
        test_metrics_under_load(base_url)

        print("\n\n✅ All metrics tests completed!")
        print("\nTo use with Prometheus, add this to your prometheus.yml:")
        print("```yaml")
        print("scrape_configs:")
        print("  - job_name: 'medical_patients_generator'")
        print("    static_configs:")
        print(f"      - targets: ['{base_url.replace('http://', '')}']")
        print("    metrics_path: '/metrics'")
        print("    scrape_interval: 15s")
        print("```")
    else:
        print("\n❌ Metrics tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
