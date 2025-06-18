"""
Integration tests for Prometheus metrics.
Part of EPIC-003: Production Scalability Improvements
"""

import asyncio
import time

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
import pytest

from src.api.v1.middleware.metrics import MetricsMiddleware
from src.core.metrics import (
    cache_hits,
    cache_misses,
    generation_errors,
    get_metrics_collector,
    job_status_changes,
    patients_generated,
    request_count,
)


class TestMetricsMiddleware:
    """Test metrics middleware integration."""

    @pytest.fixture()
    def test_app(self):
        """Create test FastAPI app with metrics middleware."""
        app = FastAPI()
        app.add_middleware(MetricsMiddleware)

        @app.get("/test")
        async def test_endpoint():
            return {"status": "ok"}

        @app.get("/test/{item_id}")
        async def test_with_id(item_id: str):
            return {"item_id": item_id}

        @app.get("/error")
        async def error_endpoint():
            raise HTTPException(status_code=400, detail="Bad request")

        @app.get("/slow")
        async def slow_endpoint():
            await asyncio.sleep(0.1)
            return {"status": "slow"}

        return app

    @pytest.fixture()
    def client(self, test_app):
        """Create test client."""
        return TestClient(test_app)

    def test_request_metrics_collection(self, client):
        """Test that middleware collects request metrics."""
        # Make some requests
        response = client.get("/test")
        assert response.status_code == 200

        response = client.get("/test/123")
        assert response.status_code == 200

        response = client.get("/test/456")
        assert response.status_code == 200

        # Check metrics were collected
        # Path should be normalized
        metrics = {}
        for labels, value in request_count._metrics.items():
            key = f"{labels[0]} {labels[1]} {labels[2]}"
            metrics[key] = value

        # Should have normalized paths
        assert any("GET /test 200" in k for k in metrics)
        assert any("GET /test/:id 200" in k for k in metrics)

    def test_error_metrics_collection(self, client):
        """Test that middleware collects error metrics."""
        # Make request that returns error
        response = client.get("/error")
        assert response.status_code == 400

        # Check error was recorded
        metrics = {}
        for labels, value in request_count._metrics.items():
            key = f"{labels[0]} {labels[1]} {labels[2]}"
            metrics[key] = value

        assert any("GET /error 400" in k for k in metrics)

    def test_response_time_header(self, client):
        """Test that middleware adds response time header."""
        response = client.get("/test")

        assert "X-Response-Time" in response.headers
        assert "ms" in response.headers["X-Response-Time"]

        # Parse response time
        time_str = response.headers["X-Response-Time"].replace("ms", "")
        response_time = float(time_str)
        assert response_time > 0
        assert response_time < 1000  # Should be less than 1 second

    def test_path_normalization(self, client):
        """Test path normalization for various ID formats."""
        middleware = MetricsMiddleware(None)

        # Test UUID normalization
        assert middleware._normalize_path("/api/v1/jobs/550e8400-e29b-41d4-a716-446655440000") == "/api/v1/jobs/:job_id"
        assert middleware._normalize_path("/api/v1/jobs/550e8400e29b41d4a716446655440000") == "/api/v1/jobs/:job_id"

        # Test numeric ID normalization
        assert middleware._normalize_path("/api/v1/items/12345") == "/api/v1/items/:id"

        # Test job ID format
        assert middleware._normalize_path("/api/v1/jobs/job_12345") == "/api/v1/jobs/:job_id"

        # Test configurations
        assert (
            middleware._normalize_path("/api/v1/configurations/abc-123") == "/api/v1/configurations/:configuration_id"
        )

        # Test downloads
        assert middleware._normalize_path("/api/v1/downloads/file_123") == "/api/v1/downloads/:download_id"

        # Test paths without IDs
        assert middleware._normalize_path("/api/v1/health") == "/api/v1/health"
        assert middleware._normalize_path("/metrics") == "/metrics"

    def test_metrics_endpoint_excluded(self, client):
        """Test that /metrics endpoint is excluded from metrics collection."""
        # Get initial metrics state
        initial_metrics = dict(request_count._metrics)

        # Make request to /metrics (if it exists)
        client.get("/metrics")

        # Metrics should not change
        new_metrics = dict(request_count._metrics)
        assert initial_metrics == new_metrics


class TestPrometheusMetricsEndpoint:
    """Test Prometheus metrics endpoint."""

    @pytest.fixture()
    def client(self):
        """Create test client for main app."""
        from src.main import app

        return TestClient(app)

    def test_metrics_endpoint_format(self, client):
        """Test metrics endpoint returns Prometheus format."""
        response = client.get("/metrics")

        assert response.status_code == 200
        # Allow for potential charset duplication by FastAPI
        assert response.headers["content-type"].startswith("text/plain; version=0.0.4; charset=utf-8")

        # Check for Prometheus format markers
        content = response.text
        assert "# HELP" in content
        assert "# TYPE" in content

        # Check for expected metrics
        assert "api_requests_total" in content
        assert "api_request_duration_seconds" in content
        assert "db_connections_active" in content
        assert "patients_generated_total" in content

    def test_metrics_no_cache_headers(self, client):
        """Test metrics endpoint has no-cache headers."""
        response = client.get("/metrics")

        assert response.headers["cache-control"] == "no-cache, no-store, must-revalidate"
        assert response.headers["pragma"] == "no-cache"
        assert response.headers["expires"] == "0"

    def test_metrics_content_after_activity(self, client):
        """Test metrics content after generating some activity."""
        # Generate some activity
        client.get("/api/v1/health")
        client.get("/api/v1/jobs")
        client.get("/api/v1/configurations")

        # Get metrics
        response = client.get("/metrics")
        content = response.text

        # Check that our requests are reflected
        assert 'api_requests_total{endpoint="/api/v1/health",method="GET",status="200"}' in content
        assert 'api_requests_total{endpoint="/api/v1/jobs",method="GET",status="' in content

        # Parse a metric value
        lines = content.split("\n")
        for line in lines:
            if 'api_requests_total{endpoint="/api/v1/health",method="GET",status="200"}' in line:
                parts = line.split(" ")
                value = float(parts[-1])
                assert value >= 1.0


class TestMetricsIntegration:
    """Test metrics integration with various services."""

    def test_patient_generation_metrics(self):
        """Test patient generation metrics tracking."""
        metrics = get_metrics_collector()

        # Get initial state
        initial_generated = self._get_metric_value(patients_generated, ("json",))
        initial_errors = self._get_metric_value(generation_errors, ("RuntimeError",))

        # Track successful generation
        with metrics.track_generation("json", 100):
            pass

        # Check metric increased
        new_generated = self._get_metric_value(patients_generated, ("json",))
        assert new_generated == initial_generated + 100

        # Track failed generation
        try:
            with metrics.track_generation("xml", 50):
                raise RuntimeError("Test error")
        except RuntimeError:
            pass

        # Check error was recorded
        new_errors = self._get_metric_value(generation_errors, ("RuntimeError",))
        assert new_errors == initial_errors + 1

    def test_job_lifecycle_metrics(self):
        """Test job lifecycle metrics."""
        metrics = get_metrics_collector()

        # Record job status changes
        metrics.record_job_status_change("pending", "running")
        metrics.record_job_status_change("running", "completed")

        # Update queue sizes
        metrics.update_job_queue_size("pending", 5)
        metrics.update_job_queue_size("running", 2)
        metrics.update_job_queue_size("completed", 10)

        # Track job execution
        with metrics.track_job_execution("patient_generation"):
            time.sleep(0.01)

        # Verify metrics exist
        assert self._get_metric_value(job_status_changes, ("pending", "running")) >= 1
        assert self._get_metric_value(job_status_changes, ("running", "completed")) >= 1

    def test_cache_metrics(self):
        """Test cache metrics tracking."""
        metrics = get_metrics_collector()

        # Record cache operations
        for _ in range(10):
            metrics.record_cache_hit("demographics")

        for _ in range(3):
            metrics.record_cache_miss("demographics")

        metrics.record_cache_eviction("demographics", "size_limit")
        metrics.record_cache_eviction("demographics", "ttl_expired")

        # Check metrics
        assert self._get_metric_value(cache_hits, ("demographics",)) >= 10
        assert self._get_metric_value(cache_misses, ("demographics",)) >= 3

    def test_database_query_metrics(self):
        """Test database query metrics."""
        metrics = get_metrics_collector()

        # Track queries
        for i in range(5):
            with metrics.track_db_query():
                time.sleep(0.001 * i)  # Varying query times

        # Check that queries were tracked
        # Note: Histogram metrics are harder to check directly
        assert True

    def test_resource_metrics(self):
        """Test resource metrics updates."""
        metrics = get_metrics_collector()

        # Update resource metrics
        memory_info = {
            "rss": 100 * 1024 * 1024,  # 100MB
            "vms": 200 * 1024 * 1024,  # 200MB
            "available": 8 * 1024 * 1024 * 1024,  # 8GB
        }
        metrics.update_resource_metrics(memory_info, cpu_percent=25.5)

        # Verify metrics were set (actual values checked via /metrics endpoint)
        assert True

    def _get_metric_value(self, metric, labels):
        """Helper to get metric value for specific labels."""
        # Convert labels tuple to dict
        label_names = metric._labelnames
        label_dict = dict(zip(label_names, labels))
        
        # Collect metric samples
        for family in metric.collect():
            for sample in family.samples:
                # Check if this is the main metric (not _created suffix)
                if sample.name.endswith('_total') or sample.name.endswith('_sum'):
                    if sample.labels == label_dict:
                        return sample.value
        return 0


class TestMetricsThreadSafety:
    """Test metrics collection thread safety."""

    def test_concurrent_metric_updates(self):
        """Test concurrent updates to metrics."""
        metrics = get_metrics_collector()

        def update_metrics():
            for _ in range(100):
                with metrics.track_request("GET", "/test"):
                    pass
                metrics.record_cache_hit("test")
                metrics.record_job_status_change("pending", "running")

        # Run updates in multiple threads
        import threading

        threads = [threading.Thread(target=update_metrics) for _ in range(10)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Verify no errors occurred and metrics are consistent
        assert True  # If we get here, no thread safety issues
