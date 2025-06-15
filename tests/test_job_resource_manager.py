"""
Tests for job resource management.
Part of EPIC-003: Production Scalability Improvements - Phase 4
"""

import asyncio
import os
import time
from unittest.mock import MagicMock, patch

import pytest

from src.core.exceptions import ResourceLimitExceeded
from src.core.job_resource_manager import JobResourceManager, get_resource_manager


class TestJobResourceManager:
    """Test job resource management functionality."""

    @pytest.fixture()
    def resource_manager(self):
        """Create test resource manager."""
        manager = JobResourceManager()
        # Set test limits
        manager.max_memory_mb = 100
        manager.max_cpu_seconds = 10
        manager.max_runtime_seconds = 30
        manager.check_interval_seconds = 0.1
        return manager

    @pytest.mark.asyncio
    async def test_track_job_context_manager(self, resource_manager):
        """Test job tracking with context manager."""
        job_id = "test-job-123"

        # Track job execution
        async with resource_manager.track_job(job_id):
            # Job should be tracked
            assert job_id in resource_manager._active_jobs
            status = resource_manager.get_job_status(job_id)
            assert status is not None
            assert status["runtime_seconds"] >= 0
            assert status["memory_mb"] > 0

            # Simulate some work
            await asyncio.sleep(0.1)

        # Job should be cleaned up
        assert job_id not in resource_manager._active_jobs
        assert resource_manager.get_job_status(job_id) is None

    @pytest.mark.asyncio
    async def test_runtime_limit_exceeded(self, resource_manager):
        """Test runtime limit enforcement."""
        job_id = "test-job-timeout"
        resource_manager.max_runtime_seconds = 0.2  # 200ms limit

        with pytest.raises(ResourceLimitExceeded) as exc_info:
            async with resource_manager.track_job(job_id):
                # Exceed runtime limit
                await asyncio.sleep(0.3)

        assert "exceeded maximum runtime" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_memory_limit_exceeded(self, resource_manager):
        """Test memory limit enforcement."""
        job_id = "test-job-memory"
        resource_manager.max_memory_mb = 0.001  # Impossibly low limit

        with pytest.raises(ResourceLimitExceeded) as exc_info:
            async with resource_manager.track_job(job_id):
                # Any process will exceed this limit
                await asyncio.sleep(0.2)

        assert "exceeded memory limit" in str(exc_info.value)

    def test_cancel_job(self, resource_manager):
        """Test job cancellation."""
        job_id = "test-job-cancel"

        # Mock active job
        resource_manager._active_jobs[job_id] = {
            "start_time": time.time(),
            "cancelled": False,
        }

        # Cancel job
        resource_manager.cancel_job(job_id)
        assert resource_manager._active_jobs[job_id]["cancelled"] is True

        # Cancel non-existent job (should not error)
        resource_manager.cancel_job("non-existent")

    def test_get_active_jobs(self, resource_manager):
        """Test getting active jobs."""
        # Initially no jobs
        assert resource_manager.get_active_jobs() == {}

        # Mock some jobs
        mock_process = MagicMock()
        mock_process.memory_info.return_value.rss = 50 * 1024 * 1024  # 50MB
        mock_process.cpu_times.return_value.user = 1.0
        mock_process.cpu_times.return_value.system = 0.5

        resource_manager._active_jobs["job1"] = {
            "start_time": time.time(),
            "start_cpu": MagicMock(user=0.0, system=0.0),
            "process": mock_process,
            "cancelled": False,
        }

        resource_manager._active_jobs["job2"] = {
            "start_time": time.time() - 10,
            "start_cpu": MagicMock(user=0.0, system=0.0),
            "process": mock_process,
            "cancelled": True,
        }

        # Get active jobs
        active = resource_manager.get_active_jobs()
        assert len(active) == 2
        assert "job1" in active
        assert "job2" in active
        assert active["job1"]["memory_mb"] == 50.0
        assert active["job1"]["cpu_seconds"] == 1.5
        assert active["job2"]["cancelled"] is True

    @patch("psutil.virtual_memory")
    @patch("psutil.cpu_percent")
    def test_can_start_new_job(self, mock_cpu, mock_memory, resource_manager):
        """Test checking if new job can start."""
        resource_manager.max_concurrent_jobs = 2

        # System resources OK, no jobs running
        mock_memory.return_value.percent = 50
        mock_cpu.return_value = 40
        assert resource_manager.can_start_new_job() is True

        # Add jobs up to limit
        resource_manager._active_jobs["job1"] = {}
        resource_manager._active_jobs["job2"] = {}
        with patch.object(resource_manager, "get_active_jobs", return_value={"job1": {}, "job2": {}}):
            assert resource_manager.can_start_new_job() is False

        # High memory usage
        resource_manager._active_jobs.clear()
        mock_memory.return_value.percent = 95
        assert resource_manager.can_start_new_job() is False

        # High CPU usage
        mock_memory.return_value.percent = 50
        mock_cpu.return_value = 95
        assert resource_manager.can_start_new_job() is False

    @pytest.mark.asyncio
    @patch("psutil.virtual_memory")
    @patch("psutil.cpu_percent")
    async def test_wait_for_resources(self, mock_cpu, mock_memory, resource_manager):
        """Test waiting for resources to become available."""
        # Resources available immediately
        mock_memory.return_value.percent = 50
        mock_cpu.return_value = 40
        result = await resource_manager.wait_for_resources(timeout=1.0)
        assert result is True

        # Resources never available
        mock_memory.return_value.percent = 95
        start_time = time.time()
        result = await resource_manager.wait_for_resources(timeout=0.2)
        elapsed = time.time() - start_time
        assert result is False
        assert elapsed >= 0.2

    def test_singleton_instance(self):
        """Test that get_resource_manager returns singleton."""
        manager1 = get_resource_manager()
        manager2 = get_resource_manager()
        assert manager1 is manager2

    def test_environment_configuration(self):
        """Test configuration from environment variables."""
        with patch.dict(
            os.environ,
            {
                "JOB_MAX_MEMORY_MB": "1024",
                "JOB_MAX_CPU_SECONDS": "600",
                "JOB_MAX_RUNTIME_SECONDS": "1200",
                "JOB_BATCH_SIZE": "200",
                "MAX_CONCURRENT_JOBS": "4",
            },
        ):
            manager = JobResourceManager()
            assert manager.max_memory_mb == 1024
            assert manager.max_cpu_seconds == 600
            assert manager.max_runtime_seconds == 1200
            assert manager.batch_size == 200
            assert manager.max_concurrent_jobs == 4


class TestJobResourceMetrics:
    """Test metrics collection for job resources."""

    @pytest.fixture()
    def resource_manager(self):
        """Create test resource manager with mock metrics."""
        manager = JobResourceManager()
        manager._metrics = MagicMock()
        manager.check_interval_seconds = 0.05
        return manager

    @pytest.mark.asyncio
    async def test_metrics_tracking(self, resource_manager):
        """Test that metrics are tracked during job execution."""
        job_id = "test-metrics-job"

        async with resource_manager.track_job(job_id):
            # Wait for at least one monitoring cycle
            await asyncio.sleep(0.1)

        # Verify metrics were tracked
        resource_manager._metrics.track_job_started.assert_called_once_with(job_id)
        resource_manager._metrics.track_job_completed.assert_called_once()

        # Check resource usage metrics
        resource_manager._metrics.track_resource_usage.assert_called()
        calls = resource_manager._metrics.track_resource_usage.call_args_list
        assert any(call[0][0] == "job_memory_mb" for call in calls)
        assert any(call[0][0] == "job_cpu_seconds" for call in calls)