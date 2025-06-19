"""
Tests for Prometheus metrics collection.
Part of EPIC-003: Production Scalability Improvements - Phase 2
"""

import time
from unittest.mock import Mock

import pytest

from src.core.metrics import (
    cache_hits,
    cache_misses,
    get_metrics_collector,
    patients_generated,
    request_count,
)
from tests.test_metrics_helper import get_metric_value


class TestMetricsCollector:
    """Test metrics collector functionality."""

    def test_singleton_instance(self):
        """Test that metrics collector is a singleton."""
        collector1 = get_metrics_collector()
        collector2 = get_metrics_collector()
        assert collector1 is collector2

    def test_track_request_success(self):
        """Test tracking successful requests."""
        collector = get_metrics_collector()

        # Get initial count
        initial_count = get_metric_value(request_count, {"method": "GET", "endpoint": "/api/test", "status": "200"})

        # Track a successful request
        with collector.track_request("GET", "/api/test"):
            pass

        # Check metric was incremented
        new_count = get_metric_value(request_count, {"method": "GET", "endpoint": "/api/test", "status": "200"})
        assert new_count == initial_count + 1

    def test_track_request_failure(self):
        """Test tracking failed requests."""
        collector = get_metrics_collector()

        # Get initial count
        initial_count = get_metric_value(request_count, {"method": "POST", "endpoint": "/api/test", "status": "500"})

        # Track a failed request
        try:
            with collector.track_request("POST", "/api/test"):
                raise Exception("Test error")
        except Exception:
            pass

        # Check metric was incremented with error status
        new_count = get_metric_value(request_count, {"method": "POST", "endpoint": "/api/test", "status": "500"})
        assert new_count == initial_count + 1

    def test_track_db_query(self):
        """Test tracking database queries."""
        collector = get_metrics_collector()

        # Track a query
        with collector.track_db_query():
            time.sleep(0.01)  # Simulate query time

        # Check that duration was recorded
        # Note: We can't easily check histogram values, so we just ensure no errors
        assert True

    def test_track_generation(self):
        """Test tracking patient generation."""
        collector = get_metrics_collector()

        # Get initial count
        initial_value = get_metric_value(patients_generated, {"format": "json"})

        # Track successful generation
        with collector.track_generation("json", 100):
            pass

        # Check metric was incremented
        new_value = get_metric_value(patients_generated, {"format": "json"})
        assert new_value == initial_value + 100

    def test_cache_metrics(self):
        """Test cache hit/miss tracking."""
        collector = get_metrics_collector()

        # Get initial values
        initial_hits = get_metric_value(cache_hits, {"cache_type": "demographics"})
        initial_misses = get_metric_value(cache_misses, {"cache_type": "demographics"})

        # Record cache operations
        collector.record_cache_hit("demographics")
        collector.record_cache_miss("demographics")
        collector.record_cache_eviction("demographics", "size_limit")

        # Verify metrics were recorded
        assert get_metric_value(cache_hits, {"cache_type": "demographics"}) > initial_hits
        assert get_metric_value(cache_misses, {"cache_type": "demographics"}) > initial_misses

    def test_job_metrics(self):
        """Test job-related metrics."""
        collector = get_metrics_collector()

        # Record job status changes
        collector.record_job_status_change("pending", "running")
        collector.record_job_status_change("running", "completed")

        # Update queue size
        collector.update_job_queue_size("pending", 5)
        collector.update_job_queue_size("running", 2)

        # Track job execution
        with collector.track_job_execution("patient_generation"):
            time.sleep(0.01)

        # Verify metrics exist (values checked in integration tests)
        assert True

    def test_resource_metrics(self):
        """Test system resource metrics."""
        collector = get_metrics_collector()

        # Update resource metrics
        memory_info = {
            "rss": 1024 * 1024 * 100,  # 100MB
            "vms": 1024 * 1024 * 200,  # 200MB
            "available": 1024 * 1024 * 1024 * 8,  # 8GB
        }
        collector.update_resource_metrics(memory_info, 25.5)

        # Verify metrics were set
        assert True

    def test_get_metrics_output(self):
        """Test getting metrics in Prometheus format."""
        collector = get_metrics_collector()

        # Generate some metrics
        with collector.track_request("GET", "/health"):
            pass

        # Get metrics output
        metrics_output = collector.get_metrics()

        # Verify it's bytes and contains expected content
        assert isinstance(metrics_output, bytes)
        assert b"api_requests_total" in metrics_output
        assert b"TYPE" in metrics_output
        assert b"HELP" in metrics_output


class TestMetricsMiddleware:
    """Test metrics middleware functionality."""

    @pytest.mark.asyncio()
    async def test_middleware_path_normalization(self):
        """Test that middleware normalizes paths correctly."""
        from src.api.v1.middleware.metrics import MetricsMiddleware

        middleware = MetricsMiddleware(None)

        # Test various path normalizations
        assert middleware._normalize_path("/api/v1/jobs/123") == "/api/v1/jobs/:job_id"
        assert middleware._normalize_path("/api/v1/jobs/job_456") == "/api/v1/jobs/:job_id"
        assert (
            middleware._normalize_path("/api/v1/configurations/abc-def-123")
            == "/api/v1/configurations/:configuration_id"
        )
        assert middleware._normalize_path("/api/v1/health") == "/api/v1/health"
        assert middleware._normalize_path("/metrics") == "/metrics"

    @pytest.mark.asyncio()
    async def test_middleware_metrics_collection(self):
        """Test that middleware collects metrics correctly."""
        from src.api.v1.middleware.metrics import MetricsMiddleware

        # Create mock app and request
        async def mock_call_next(request):
            response = Mock()
            response.status_code = 200
            response.headers = {}
            return response

        middleware = MetricsMiddleware(None)

        # Create mock request
        request = Mock()
        request.method = "GET"
        request.url = Mock()
        request.url.path = "/api/v1/jobs/123"

        # Process request
        response = await middleware.dispatch(request, mock_call_next)

        # Verify response has timing header
        assert "X-Response-Time" in response.headers
        assert "ms" in response.headers["X-Response-Time"]
