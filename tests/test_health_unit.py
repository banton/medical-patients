"""
Unit tests for health check functionality.
Part of EPIC-003: Production Scalability Improvements
"""

from unittest.mock import MagicMock, Mock, patch

import pytest

from src.api.v1.routers.health import (
    check_api_health,
    check_database_health,
    check_disk_space,
    check_memory_usage,
)


class TestHealthCheckFunctions:
    """Test individual health check functions."""

    @patch("src.api.v1.routers.health.psutil")
    def test_check_disk_space_healthy(self, mock_psutil):
        """Test disk space check when healthy."""
        # Mock disk usage
        mock_disk = Mock()
        mock_disk.total = 100 * 1024**3  # 100GB
        mock_disk.used = 50 * 1024**3  # 50GB
        mock_disk.free = 50 * 1024**3  # 50GB
        mock_disk.percent = 50.0
        mock_psutil.disk_usage.return_value = mock_disk

        result = check_disk_space()

        assert result["status"] == "healthy"
        assert result["total_gb"] == 100.0
        assert result["used_gb"] == 50.0
        assert result["free_gb"] == 50.0
        assert result["percent_used"] == 50.0

    @patch("src.api.v1.routers.health.psutil")
    def test_check_disk_space_warning(self, mock_psutil):
        """Test disk space check when warning threshold reached."""
        # Mock high disk usage
        mock_disk = Mock()
        mock_disk.percent = 92.0  # Over 90% triggers warning
        mock_disk.total = 100 * 1024**3
        mock_disk.used = 92 * 1024**3
        mock_disk.free = 8 * 1024**3
        mock_psutil.disk_usage.return_value = mock_disk

        result = check_disk_space()

        assert result["status"] == "warning"
        assert result["percent_used"] == 92.0

    @patch("src.api.v1.routers.health.psutil")
    def test_check_disk_space_error(self, mock_psutil):
        """Test disk space check when error occurs."""
        # Mock exception
        mock_psutil.disk_usage.side_effect = Exception("Disk error")

        result = check_disk_space()

        assert result["status"] == "error"
        assert "Disk error" in result["error"]

    @patch("src.api.v1.routers.health.psutil")
    def test_check_memory_usage_healthy(self, mock_psutil):
        """Test memory usage check when healthy."""
        # Mock memory info
        mock_memory = Mock()
        mock_memory.total = 16 * 1024**3  # 16GB
        mock_memory.available = 8 * 1024**3  # 8GB
        mock_memory.used = 8 * 1024**3  # 8GB
        mock_memory.percent = 50.0
        mock_psutil.virtual_memory.return_value = mock_memory

        result = check_memory_usage()

        assert result["status"] == "healthy"
        assert result["total_gb"] == 16.0
        assert result["available_gb"] == 8.0
        assert result["used_gb"] == 8.0
        assert result["percent_used"] == 50.0

    @patch("src.api.v1.routers.health.psutil")
    def test_check_memory_usage_warning(self, mock_psutil):
        """Test memory usage check when warning threshold reached."""
        # Mock high memory usage
        mock_memory = Mock()
        mock_memory.percent = 88.0  # Over 85% triggers warning
        mock_memory.total = 16 * 1024**3
        mock_memory.available = 1.92 * 1024**3
        mock_memory.used = 14.08 * 1024**3
        mock_psutil.virtual_memory.return_value = mock_memory

        result = check_memory_usage()

        assert result["status"] == "warning"
        assert result["percent_used"] == 88.0

    @patch("src.api.v1.routers.health.get_pool")
    def test_check_database_health_success(self, mock_get_pool):
        """Test database health check when successful."""
        # Mock pool and cursor
        mock_pool = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = ["PostgreSQL 14.0 on x86_64"]
        mock_cursor.__enter__ = Mock(return_value=mock_cursor)
        mock_cursor.__exit__ = Mock(return_value=None)
        mock_pool.cursor.return_value = mock_cursor
        mock_pool.get_pool_status.return_value = {
            "pool": {"size": 20, "in_use": 5},
            "metrics": {"connections": {"created": 20}, "queries": {"total": 1000}},
        }
        mock_get_pool.return_value = mock_pool

        result = check_database_health()

        assert result["status"] == "healthy"
        assert "PostgreSQL" in result["version"]
        assert result["pool"]["size"] == 20
        assert result["pool"]["in_use"] == 5

    @patch("src.api.v1.routers.health.get_pool")
    def test_check_database_health_failure(self, mock_get_pool):
        """Test database health check when connection fails."""
        # Mock connection failure
        mock_get_pool.side_effect = Exception("Connection pool exhausted")

        result = check_database_health()

        assert result["status"] == "unhealthy"
        assert "Connection pool exhausted" in result["error"]

    @patch("src.api.v1.routers.health.platform")
    @patch("src.api.v1.routers.health.os")
    def test_check_api_health(self, mock_os, mock_platform):
        """Test API health check."""
        # Mock environment and platform
        mock_os.getenv.side_effect = lambda key, default: {"APP_VERSION": "2.0.0", "ENVIRONMENT": "production"}.get(
            key, default
        )
        mock_platform.python_version.return_value = "3.10.0"

        result = check_api_health()

        assert result["status"] == "healthy"
        assert result["version"] == "2.0.0"
        assert result["environment"] == "production"
        assert result["python_version"] == "3.10.0"


class TestHealthEndpointRoutes:
    """Test health endpoint route handlers."""

    @pytest.fixture()
    def mock_request(self):
        """Create a mock FastAPI request."""
        from fastapi import Request

        mock = MagicMock(spec=Request)
        return mock

    @pytest.mark.asyncio()
    @patch("src.api.v1.routers.health.check_api_health")
    @patch("src.api.v1.routers.health.check_database_health")
    @patch("src.api.v1.routers.health.check_disk_space")
    @patch("src.api.v1.routers.health.check_memory_usage")
    async def test_health_check_all_healthy(self, mock_memory, mock_disk, mock_db, mock_api):
        """Test comprehensive health check when all components are healthy."""
        # Mock all checks as healthy
        mock_api.return_value = {"status": "healthy"}
        mock_db.return_value = {"status": "healthy"}
        mock_disk.return_value = {"status": "healthy"}
        mock_memory.return_value = {"status": "healthy"}

        # Import and call the function
        from src.api.v1.routers.health import health_check

        result = await health_check()

        assert result["status"] == "healthy"
        assert "timestamp" in result
        assert result["checks"]["api"]["status"] == "healthy"
        assert result["checks"]["database"]["status"] == "healthy"
        assert result["checks"]["disk_space"]["status"] == "healthy"
        assert result["checks"]["memory"]["status"] == "healthy"

    @pytest.mark.asyncio()
    @patch("src.api.v1.routers.health.check_api_health")
    @patch("src.api.v1.routers.health.check_database_health")
    @patch("src.api.v1.routers.health.check_disk_space")
    @patch("src.api.v1.routers.health.check_memory_usage")
    async def test_health_check_with_unhealthy_component(self, mock_memory, mock_disk, mock_db, mock_api):
        """Test comprehensive health check when one component is unhealthy."""
        # Mock database as unhealthy
        mock_api.return_value = {"status": "healthy"}
        mock_db.return_value = {"status": "unhealthy", "error": "Connection failed"}
        mock_disk.return_value = {"status": "healthy"}
        mock_memory.return_value = {"status": "healthy"}

        from fastapi.responses import JSONResponse

        from src.api.v1.routers.health import health_check

        result = await health_check()

        # The function returns a JSONResponse when unhealthy
        if isinstance(result, JSONResponse):
            # Extract the content
            result = result.body.decode("utf-8")
            import json

            result = json.loads(result)

        assert result["status"] == "unhealthy"
        assert result["checks"]["database"]["status"] == "unhealthy"

    @pytest.mark.asyncio()
    @patch("src.api.v1.routers.health.get_pool")
    async def test_readiness_probe_ready(self, mock_get_pool):
        """Test readiness probe when system is ready."""
        # Mock successful database check
        mock_pool = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = (1,)
        mock_cursor.__enter__ = Mock(return_value=mock_cursor)
        mock_cursor.__exit__ = Mock(return_value=None)
        mock_pool.cursor.return_value = mock_cursor
        mock_get_pool.return_value = mock_pool

        from src.api.v1.routers.health import readiness_probe

        result = await readiness_probe()

        assert result == {"status": "ready"}

    @pytest.mark.asyncio()
    @patch("src.api.v1.routers.health.get_pool")
    async def test_readiness_probe_not_ready(self, mock_get_pool):
        """Test readiness probe when system is not ready."""
        # Mock database connection failure
        mock_pool = Mock()
        mock_pool.cursor.side_effect = Exception("Database unavailable")
        mock_get_pool.return_value = mock_pool

        from fastapi.responses import JSONResponse

        from src.api.v1.routers.health import readiness_probe

        result = await readiness_probe()

        assert isinstance(result, JSONResponse)
        assert result.status_code == 503
