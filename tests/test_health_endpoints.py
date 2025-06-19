"""
Integration tests for health check endpoints.
Part of EPIC-003: Production Scalability Improvements
"""

from unittest.mock import Mock, patch

import pytest

pytestmark = [pytest.mark.integration]


class TestHealthEndpoints:
    """Test health check endpoints."""

    @pytest.fixture()
    def base_url(self):
        """Base URL for tests."""
        return "http://localhost:8000"

    def test_liveness_probe(self, client):
        """Test liveness probe endpoint."""
        response = client.get("/api/v1/health/live")

        assert response.status_code == 200
        assert response.json() == {"status": "alive"}

    @patch("src.api.v1.routers.health.get_pool")
    def test_readiness_probe_success(self, mock_get_pool, client):
        """Test readiness probe when system is ready."""
        # Setup mock pool
        mock_pool = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = (1,)
        mock_cursor.__enter__ = Mock(return_value=mock_cursor)
        mock_cursor.__exit__ = Mock(return_value=None)
        mock_pool.cursor.return_value = mock_cursor
        mock_get_pool.return_value = mock_pool

        response = client.get("/api/v1/health/ready")

        assert response.status_code == 200
        assert response.json() == {"status": "ready"}

    @patch("src.api.v1.routers.health.get_pool")
    def test_readiness_probe_not_ready(self, mock_get_pool, client):
        """Test readiness probe when system is not ready."""
        # Setup mock pool to raise exception
        mock_get_pool.side_effect = Exception("Database not available")

        response = client.get("/api/v1/health/ready")

        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "not_ready"
        assert "error" in data

    @patch("src.api.v1.routers.health.psutil")
    @patch("src.api.v1.routers.health.get_pool")
    @patch("src.api.v1.routers.health.platform")
    def test_comprehensive_health_check(self, mock_platform, mock_get_pool, mock_psutil, client):
        """Test comprehensive health check endpoint."""
        # Setup mocks
        mock_platform.python_version.return_value = "3.10.0"

        # Mock disk usage
        mock_disk = Mock()
        mock_disk.total = 100 * 1024**3  # 100GB
        mock_disk.used = 50 * 1024**3  # 50GB
        mock_disk.free = 50 * 1024**3  # 50GB
        mock_disk.percent = 50.0
        mock_psutil.disk_usage.return_value = mock_disk

        # Mock memory
        mock_memory = Mock()
        mock_memory.total = 16 * 1024**3  # 16GB
        mock_memory.available = 8 * 1024**3  # 8GB
        mock_memory.used = 8 * 1024**3  # 8GB
        mock_memory.percent = 50.0
        mock_psutil.virtual_memory.return_value = mock_memory

        # Mock database pool
        mock_pool = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = ("PostgreSQL 14.0",)
        mock_cursor.__enter__ = Mock(return_value=mock_cursor)
        mock_cursor.__exit__ = Mock(return_value=None)
        mock_pool.cursor.return_value = mock_cursor
        mock_pool.get_pool_status.return_value = {
            "pool": {"size": 10, "in_use": 2, "available": 8},
            "metrics": {"connections": {"created": 10}, "queries": {"total": 100}},
        }
        mock_get_pool.return_value = mock_pool

        response = client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()

        # Check overall status
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "checks" in data

        # Check individual components
        checks = data["checks"]
        assert checks["api"]["status"] == "healthy"
        assert checks["database"]["status"] == "healthy"
        assert checks["disk_space"]["status"] == "healthy"
        assert checks["memory"]["status"] == "healthy"

        # Verify detailed data
        assert checks["disk_space"]["percent_used"] == 50.0
        assert checks["memory"]["percent_used"] == 50.0
        assert "PostgreSQL" in checks["database"]["version"]

    @patch("src.api.v1.routers.health.psutil")
    @patch("src.api.v1.routers.health.get_pool")
    def test_health_check_with_warnings(self, mock_get_pool, mock_psutil, client):
        """Test health check with warning conditions."""
        # Mock high disk usage (warning threshold)
        mock_disk = Mock()
        mock_disk.percent = 92.0  # Over 90% triggers warning
        mock_disk.total = 100 * 1024**3
        mock_disk.used = 92 * 1024**3
        mock_disk.free = 8 * 1024**3
        mock_psutil.disk_usage.return_value = mock_disk

        # Mock high memory usage (warning threshold)
        mock_memory = Mock()
        mock_memory.percent = 88.0  # Over 85% triggers warning
        mock_memory.total = 16 * 1024**3
        mock_memory.available = 2 * 1024**3
        mock_memory.used = 14 * 1024**3
        mock_psutil.virtual_memory.return_value = mock_memory

        # Mock database is healthy
        mock_pool = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = ("PostgreSQL 14.0",)
        mock_cursor.__enter__ = Mock(return_value=mock_cursor)
        mock_cursor.__exit__ = Mock(return_value=None)
        mock_pool.cursor.return_value = mock_cursor
        mock_pool.get_pool_status.return_value = {"pool": {"size": 10, "in_use": 2}, "metrics": {}}
        mock_get_pool.return_value = mock_pool

        response = client.get("/api/v1/health")

        # With warnings, status should still be 200 (but with warning status in response)
        assert response.status_code == 200
        data = response.json()

        # Overall status should be warning
        assert data["status"] == "warning"

        # Check individual statuses
        checks = data["checks"]
        assert checks["disk_space"]["status"] == "warning"
        assert checks["memory"]["status"] == "warning"
        assert checks["database"]["status"] == "healthy"

    @patch("src.api.v1.routers.health.get_pool")
    def test_database_health_endpoint(self, mock_get_pool, client):
        """Test database-specific health endpoint."""
        # Setup mock pool
        mock_pool = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = ("PostgreSQL 14.0 on x86_64-pc-linux-gnu", "medgen_db", "medgen_user")
        mock_cursor.__enter__ = Mock(return_value=mock_cursor)
        mock_cursor.__exit__ = Mock(return_value=None)
        mock_pool.cursor.return_value = mock_cursor
        mock_pool.get_pool_status.return_value = {
            "pool": {"size": 20, "minconn": 5, "available": 15, "in_use": 5},
            "metrics": {"connections": {"created": 20, "active": 5}, "queries": {"total": 1000, "avg_time_ms": 23.5}},
            "config": {"recycle_seconds": 3600, "timeout_seconds": 30, "query_timeout_ms": 30000, "pre_ping": True},
        }
        mock_get_pool.return_value = mock_pool

        response = client.get("/api/v1/health/database")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "healthy"
        assert "PostgreSQL" in data["database"]["version"]
        assert data["database"]["database"] == "medgen_db"
        assert data["database"]["user"] == "medgen_user"

        # Check pool information
        assert data["pool"]["size"] == 20
        assert data["pool"]["in_use"] == 5

        # Check metrics
        assert data["metrics"]["queries"]["total"] == 1000
        assert data["metrics"]["queries"]["avg_time_ms"] == 23.5

        # Check configuration
        assert data["config"]["pre_ping"] is True
        assert data["config"]["recycle_seconds"] == 3600

    @patch("src.api.v1.routers.health.get_pool")
    def test_database_health_unhealthy(self, mock_get_pool, client):
        """Test database health endpoint when database is unhealthy."""
        # Setup mock pool to raise exception
        mock_get_pool.side_effect = Exception("Connection pool exhausted")

        response = client.get("/api/v1/health/database")

        assert response.status_code == 503
        data = response.json()
        assert data["detail"]["status"] == "unhealthy"
        assert "Connection pool exhausted" in data["detail"]["error"]

    @patch("src.api.v1.routers.health.psutil")
    @patch("src.api.v1.routers.health.get_pool")
    def test_metrics_endpoint_health(self, mock_get_pool, mock_psutil, client):
        """Test metrics endpoint in health router."""
        # Setup mocks
        mock_psutil.virtual_memory.return_value = Mock(percent=75.0)
        mock_psutil.cpu_percent.return_value = 25.0
        mock_psutil.disk_usage.return_value = Mock(percent=60.0)

        mock_pool = Mock()
        mock_pool.get_pool_status.return_value = {
            "metrics": {
                "connections": {"created": 50, "active": 10},
                "queries": {"total": 5000, "slow_count": 50, "avg_time_ms": 15.5},
                "checkouts": {"avg_time_ms": 2.5, "failed": 5},
            }
        }
        mock_get_pool.return_value = mock_pool

        response = client.get("/api/v1/health/metrics")

        assert response.status_code == 200
        data = response.json()

        # Check database metrics
        assert data["database"]["connections_created_total"] == 50
        assert data["database"]["connections_active"] == 10
        assert data["database"]["queries_total"] == 5000
        assert data["database"]["queries_slow_total"] == 50
        assert data["database"]["query_duration_avg_ms"] == 15.5
        assert data["database"]["checkout_duration_avg_ms"] == 2.5
        assert data["database"]["checkout_failures_total"] == 5

        # Check system metrics
        assert data["system"]["memory_percent"] == 75.0
        assert data["system"]["cpu_percent"] == 25.0
        assert data["system"]["disk_percent"] == 60.0
