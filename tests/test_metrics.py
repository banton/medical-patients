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
        # Just verify the method runs without error
        metrics.track_request("GET", "/api/v1/test", 200, 0.1)
        
    def test_track_job(self, metrics):
        """Test that job metrics are recorded"""
        metrics.track_job_started("test_job")
        metrics.track_job_completed("test_job", 5.0)
        metrics.track_job_failed("test_job", 1.0)
        
    def test_track_cache(self, metrics):
        """Test that cache metrics are recorded"""
        metrics.track_cache_hit("test_key")
        metrics.track_cache_miss("test_key")
        
    def test_get_metrics(self, metrics):
        """Test that metrics endpoint returns data"""
        # Record some metrics
        metrics.track_request("GET", "/test", 200, 0.1)
        
        # Get metrics output
        output = metrics.generate_metrics()
        assert isinstance(output, str)
        assert "api_requests_total" in output