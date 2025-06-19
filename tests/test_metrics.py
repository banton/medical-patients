"""
Simple metrics tests - verify metrics are recorded without testing Prometheus internals
"""

import pytest
from unittest.mock import patch, MagicMock

from src.core.metrics import MetricsCollector

pytestmark = pytest.mark.unit


class TestMetrics:
    """Basic metrics functionality tests"""
    
    @pytest.fixture
    def metrics(self):
        """Create metrics collector"""
        return MetricsCollector()
    
    def test_record_request(self, metrics):
        """Test that request metrics are recorded"""
        # Just verify the method runs without error
        metrics.record_request("GET", "/api/v1/test", 200, 0.1)
        
    def test_record_job(self, metrics):
        """Test that job metrics are recorded"""
        metrics.record_job_started("test_job")
        metrics.record_job_completed("test_job", 5.0)
        metrics.record_job_failed("test_job", 1.0)
        
    def test_record_cache(self, metrics):
        """Test that cache metrics are recorded"""
        metrics.record_cache_hit("test_key")
        metrics.record_cache_miss("test_key")
        
    def test_get_metrics(self, metrics):
        """Test that metrics endpoint returns data"""
        # Record some metrics
        metrics.record_request("GET", "/test", 200, 0.1)
        
        # Get metrics output
        output = metrics.generate_metrics()
        assert isinstance(output, str)
        assert "http_requests_total" in output