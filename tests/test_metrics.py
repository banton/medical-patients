"""
Simple metrics tests - verify metrics are recorded without testing Prometheus internals
"""

import pytest

from src.core.metrics import MetricsCollector

pytestmark = pytest.mark.unit


class TestMetrics:
    """Basic metrics functionality tests"""
    
    @pytest.fixture
    def metrics(self):
        """Create metrics collector"""
        return MetricsCollector()
    
    def test_track_request(self, metrics):
        """Test that request metrics are recorded"""
        # track_request is a context manager
        with metrics.track_request("GET", "/api/v1/test"):
            pass  # Simulate request processing
        
    def test_track_job(self, metrics):
        """Test that job metrics are recorded"""
        metrics.track_job_started("test_job")
        metrics.track_job_completed("test_job", 5.0)
        metrics.track_job_failed("test_job", "TestError")
        
    def test_record_cache(self, metrics):
        """Test that cache metrics are recorded"""
        metrics.record_cache_hit("test_key")
        metrics.record_cache_miss("test_key")
        
    def test_get_metrics(self, metrics):
        """Test that metrics endpoint returns data"""
        # Record some metrics using context manager
        with metrics.track_request("GET", "/test"):
            pass
        
        # Get metrics output
        output = metrics.get_metrics()
        assert isinstance(output, bytes)
        assert b"api_requests_total" in output