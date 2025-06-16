"""
Background job worker with resource optimization.
Part of EPIC-003: Production Scalability Improvements - Phase 4
"""

import asyncio
from contextlib import suppress
import gc
from typing import Any, Dict, List, Optional

from src.core.exceptions import ResourceLimitExceeded
from src.core.job_resource_manager import get_resource_manager
from src.core.metrics import get_metrics_collector
from src.domain.models.job import JobProgressDetails, JobStatus
from src.domain.services.job_service import JobService


class JobWorker:
    """
    Worker for processing background jobs with resource limits and optimization.

    Features:
    - Resource-limited job execution
    - Batch processing for large jobs
    - Automatic garbage collection
    - Job priority handling
    - Graceful shutdown
    """

    def __init__(self, job_service: JobService):
        """
        Initialize job worker.

        Args:
            job_service: Service for job management
        """
        self.job_service = job_service
        self.resource_manager = get_resource_manager()
        self.metrics = get_metrics_collector()
        self._running = False
        self._current_task: Optional[asyncio.Task] = None

    async def start(self):
        """Start the job worker."""
        self._running = True
        await self._worker_loop()

    async def stop(self):
        """Stop the job worker gracefully."""
        self._running = False

        # Cancel current task if any
        if self._current_task and not self._current_task.done():
            self._current_task.cancel()
            with suppress(asyncio.CancelledError):
                await self._current_task

    async def _worker_loop(self):
        """Main worker loop that processes jobs."""
        while self._running:
            try:
                # Wait for resources to be available
                if not await self.resource_manager.wait_for_resources(timeout=30):
                    await asyncio.sleep(5)
                    continue

                # Get next job from queue
                job = await self._get_next_job()
                if not job:
                    await asyncio.sleep(5)
                    continue

                # Process the job
                await self._process_job(job)

            except Exception as e:
                print(f"Worker error: {e}")
                self.metrics.track_generation_error(str(e))
                await asyncio.sleep(5)

    async def _get_next_job(self) -> Optional[Any]:
        """
        Get the next job to process.

        Returns:
            Job data or None if no jobs available
        """
        # Get all pending jobs
        jobs = await self.job_service.list_jobs()
        pending_jobs = [j for j in jobs if j.status == JobStatus.PENDING]

        if not pending_jobs:
            return None

        # Sort by priority and creation time
        pending_jobs.sort(key=lambda j: (j.config.get("priority", 0), j.created_at))

        # Return highest priority job
        return pending_jobs[0]

    async def _process_job(self, job: Any):
        """
        Process a single job with resource limits.

        Args:
            job: Job to process
        """
        job_id = job.job_id

        try:
            # Update status to running
            await self.job_service.update_job_status(job_id, JobStatus.RUNNING)

            # Process with resource tracking
            async with self.resource_manager.track_job(job_id):
                # Create task for job processing
                self._current_task = asyncio.create_task(self._execute_job_with_batching(job))
                await self._current_task

        except ResourceLimitExceeded as e:
            # Job exceeded resource limits
            await self.job_service.update_job_status(job_id, JobStatus.FAILED, error=f"Resource limit exceeded: {e}")
            self.metrics.track_job_failed(job_id, "resource_limit_exceeded")

        except asyncio.CancelledError:
            # Job was cancelled
            await self.job_service.update_job_status(job_id, JobStatus.FAILED, error="Job cancelled")
            raise

        except Exception as e:
            # Other errors
            await self.job_service.update_job_status(job_id, JobStatus.FAILED, error=str(e))
            self.metrics.track_job_failed(job_id, "execution_error")

    async def _execute_job_with_batching(self, job: Any):
        """
        Execute job with batch processing for memory efficiency.

        Args:
            job: Job to execute
        """
        from src.api.v1.routers.generation import _run_generation_task
        from src.domain.services.patient_generation_service import AsyncPatientGenerationService

        job_id = job.job_id
        config = job.config

        # Check if this is a large job that needs batching
        patient_count = config.get("count", 10)
        if isinstance(config.get("configuration"), dict):
            patient_count = config["configuration"].get("count", patient_count)

        # Use batching for large jobs
        if patient_count > self.resource_manager.batch_size:
            await self._execute_batched_generation(job, patient_count)
        else:
            # Regular execution for small jobs
            generation_service = AsyncPatientGenerationService()
            await _run_generation_task(job_id, config, generation_service, self.job_service)

    async def _execute_batched_generation(self, job: Any, total_patients: int):
        """
        Execute generation in batches to limit memory usage.

        Args:
            job: Job to execute
            total_patients: Total number of patients to generate
        """
        job_id = job.job_id
        config = job.config.copy()
        batch_size = self.resource_manager.batch_size

        # Update job with batching info
        progress_details = JobProgressDetails(
            current_phase="batching",
            phase_description=f"Processing in batches of {batch_size}",
            phase_progress=0,
            total_patients=total_patients,
            processed_patients=0,
        )
        await self.job_service.update_job_progress(job_id, 0, progress_details)

        # Process in batches
        patients_generated = 0
        batch_num = 0

        while patients_generated < total_patients:
            # Calculate batch size
            current_batch_size = min(batch_size, total_patients - patients_generated)

            # Update config for this batch
            batch_config = config.copy()
            if "configuration" in batch_config:
                batch_config["configuration"]["count"] = current_batch_size
            else:
                batch_config["count"] = current_batch_size

            # Generate batch
            from src.domain.services.patient_generation_service import AsyncPatientGenerationService

            generation_service = AsyncPatientGenerationService()

            # Create temporary job for batch
            batch_job_id = f"{job_id}_batch_{batch_num}"

            # Process batch
            await self._process_single_batch(
                batch_job_id, batch_config, generation_service, patients_generated, total_patients
            )

            # Update progress
            patients_generated += current_batch_size
            batch_num += 1
            progress = min(patients_generated / total_patients, 1.0)

            progress_details = JobProgressDetails(
                current_phase="generating",
                phase_description=f"Batch {batch_num} of {(total_patients + batch_size - 1) // batch_size}",
                phase_progress=int(progress * 100),
                total_patients=total_patients,
                processed_patients=patients_generated,
            )
            await self.job_service.update_job_progress(job_id, int(progress * 100), progress_details)

            # Garbage collection between batches
            gc.collect()

            # Small delay between batches
            await asyncio.sleep(self.resource_manager.batch_delay_ms / 1000.0)

        # Mark job as completed
        await self.job_service.update_job_status(job_id, JobStatus.COMPLETED)

    async def _process_single_batch(
        self, batch_job_id: str, batch_config: Dict[str, Any], generation_service: Any, offset: int, total: int
    ):
        """
        Process a single batch of patients.

        Args:
            batch_job_id: Unique ID for this batch
            batch_config: Configuration for the batch
            generation_service: Service to generate patients
            offset: Number of patients already generated
            total: Total patients to generate
        """
        # TODO: Implement actual batch processing logic
        # This would integrate with the patient generation service
        # to generate a subset of patients and append to output files


class JobWorkerPool:
    """
    Pool of job workers for concurrent processing.
    """

    def __init__(self, job_service: JobService, pool_size: int = 2):
        """
        Initialize worker pool.

        Args:
            job_service: Service for job management
            pool_size: Number of workers in pool
        """
        self.job_service = job_service
        self.pool_size = pool_size
        self.workers: List[JobWorker] = []
        self._running = False

    async def start(self):
        """Start all workers in the pool."""
        self._running = True

        # Create workers
        for _i in range(self.pool_size):
            worker = JobWorker(self.job_service)
            self.workers.append(worker)

        # Start workers concurrently
        tasks = [worker.start() for worker in self.workers]
        await asyncio.gather(*tasks)

    async def stop(self):
        """Stop all workers gracefully."""
        self._running = False

        # Stop all workers
        tasks = [worker.stop() for worker in self.workers]
        await asyncio.gather(*tasks)

        self.workers.clear()
