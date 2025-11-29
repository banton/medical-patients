"""
Job resource management for background tasks.
Part of EPIC-003: Production Scalability Improvements - Phase 4
"""

import asyncio
from contextlib import asynccontextmanager, suppress
import os
import time
from typing import Any, Dict, Optional

import psutil

from src.core.exceptions import ResourceLimitExceeded
from src.core.metrics import get_metrics_collector


class JobResourceManager:
    """
    Manages resource limits and monitoring for background jobs.

    Features:
    - Memory limits per job
    - CPU time limits
    - Job timeout enforcement
    - Resource usage tracking
    - Automatic cleanup on limit exceeded
    """

    def __init__(self):
        """Initialize resource manager with configuration."""
        # Resource limits from settings or defaults
        self.max_memory_mb = int(os.environ.get("JOB_MAX_MEMORY_MB", "512"))  # 512MB default
        self.max_cpu_seconds = int(os.environ.get("JOB_MAX_CPU_SECONDS", "300"))  # 5 minutes
        self.max_runtime_seconds = int(os.environ.get("JOB_MAX_RUNTIME_SECONDS", "600"))  # 10 minutes
        self.check_interval_seconds = 5  # Check resources every 5 seconds

        # Batch processing configuration
        self.batch_size = int(os.environ.get("JOB_BATCH_SIZE", "100"))
        self.batch_delay_ms = int(os.environ.get("JOB_BATCH_DELAY_MS", "100"))

        # Worker configuration
        self.max_concurrent_jobs = int(os.environ.get("MAX_CONCURRENT_JOBS", "2"))
        self.job_queue_size = int(os.environ.get("JOB_QUEUE_SIZE", "10"))

        # Tracking
        self._active_jobs: Dict[str, Dict[str, Any]] = {}
        self._metrics = get_metrics_collector()

    @asynccontextmanager
    async def track_job(self, job_id: str):
        """
        Context manager to track and limit job resources.

        Args:
            job_id: Unique job identifier

        Raises:
            ResourceLimitExceeded: If job exceeds resource limits
        """
        # Initialize job tracking
        process = psutil.Process()
        start_time = time.time()
        start_cpu = process.cpu_times()

        self._active_jobs[job_id] = {
            "start_time": start_time,
            "start_cpu": start_cpu,
            "process": process,
            "cancelled": False,
            "exception": None,
        }

        # Start resource monitoring task
        monitor_task = asyncio.create_task(self._monitor_job_resources(job_id))

        try:
            # Track job start
            self._metrics.track_job_started(job_id)
            yield

        finally:
            # Cancel monitoring
            monitor_task.cancel()
            with suppress(asyncio.CancelledError):
                await monitor_task

            # Clean up tracking
            if job_id in self._active_jobs:
                job_info = self._active_jobs.pop(job_id)

                # Check if we need to raise an exception
                if job_info.get("exception"):
                    raise job_info["exception"]

                # Record final metrics
                runtime = time.time() - job_info["start_time"]
                self._metrics.track_job_completed(job_id, runtime)

    async def _monitor_job_resources(self, job_id: str):
        """
        Monitor job resource usage and enforce limits.

        Args:
            job_id: Job to monitor
        """
        while job_id in self._active_jobs:
            try:
                job_info = self._active_jobs[job_id]
                process = job_info["process"]

                # Check if job was cancelled
                if job_info.get("cancelled", False):
                    break

                # Check runtime limit
                runtime = time.time() - job_info["start_time"]
                if runtime > self.max_runtime_seconds:
                    error_message = f"Job {job_id} exceeded maximum runtime of {self.max_runtime_seconds} seconds"
                    raise ResourceLimitExceeded(error_message)

                # Check memory usage
                memory_info = process.memory_info()
                memory_mb = memory_info.rss / 1024 / 1024
                if memory_mb > self.max_memory_mb:
                    error_message = f"Job {job_id} exceeded memory limit: {memory_mb:.1f}MB > {self.max_memory_mb}MB"
                    raise ResourceLimitExceeded(error_message)

                # Check CPU time
                cpu_times = process.cpu_times()
                cpu_seconds = (cpu_times.user + cpu_times.system) - (
                    job_info["start_cpu"].user + job_info["start_cpu"].system
                )
                if cpu_seconds > self.max_cpu_seconds:
                    error_message = (
                        f"Job {job_id} exceeded CPU time limit: {cpu_seconds:.1f}s > {self.max_cpu_seconds}s"
                    )
                    raise ResourceLimitExceeded(error_message)

                # Record metrics
                self._metrics.track_resource_usage("job_memory_mb", memory_mb, {"job_id": job_id})
                self._metrics.track_resource_usage("job_cpu_seconds", cpu_seconds, {"job_id": job_id})

                # Wait before next check
                await asyncio.sleep(self.check_interval_seconds)

            except psutil.NoSuchProcess:
                # Process ended
                break
            except ResourceLimitExceeded as e:
                # Store exception to re-raise in context manager
                self._active_jobs[job_id]["exception"] = e
                print(f"Error monitoring job {job_id}: {e}")
                break
            except Exception as e:
                # Log error and stop monitoring
                print(f"Error monitoring job {job_id}: {e}")
                break

    def cancel_job(self, job_id: str):
        """
        Cancel a running job.

        Args:
            job_id: Job to cancel
        """
        if job_id in self._active_jobs:
            self._active_jobs[job_id]["cancelled"] = True

    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get current resource usage for a job.

        Args:
            job_id: Job to check

        Returns:
            Resource usage dict or None if job not found
        """
        if job_id not in self._active_jobs:
            return None

        job_info = self._active_jobs[job_id]
        process = job_info["process"]

        try:
            memory_info = process.memory_info()
            cpu_times = process.cpu_times()
            runtime = time.time() - job_info["start_time"]

            return {
                "runtime_seconds": runtime,
                "memory_mb": memory_info.rss / 1024 / 1024,
                "cpu_seconds": (cpu_times.user + cpu_times.system)
                - (job_info["start_cpu"].user + job_info["start_cpu"].system),
                "cancelled": job_info.get("cancelled", False),
            }
        except psutil.NoSuchProcess:
            return None

    def get_active_jobs(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all active jobs and their resource usage.

        Returns:
            Dict of job_id -> resource usage
        """
        active_jobs = {}
        for job_id in list(self._active_jobs.keys()):
            status = self.get_job_status(job_id)
            if status:
                active_jobs[job_id] = status
        return active_jobs

    def can_start_new_job(self) -> bool:
        """
        Check if a new job can be started based on resource limits.

        Returns:
            True if resources available for new job
        """
        # Check concurrent job limit
        active_count = len(self.get_active_jobs())
        if active_count >= self.max_concurrent_jobs:
            return False

        # Check system resources
        memory = psutil.virtual_memory()
        if memory.percent > 90:  # System memory > 90%
            return False

        cpu_percent = psutil.cpu_percent(interval=0.1)
        return cpu_percent <= 90  # CPU usage <= 90%

    async def wait_for_resources(self, timeout: float = 60.0) -> bool:
        """
        Wait for resources to become available.

        Args:
            timeout: Maximum time to wait in seconds

        Returns:
            True if resources available, False if timeout
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            if self.can_start_new_job():
                return True
            await asyncio.sleep(1)

        return False


# Global instance
_resource_manager: Optional[JobResourceManager] = None


def get_resource_manager() -> JobResourceManager:
    """Get or create the global resource manager instance."""
    global _resource_manager
    if _resource_manager is None:
        _resource_manager = JobResourceManager()
    return _resource_manager
