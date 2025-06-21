"""
Service layer for job management.
"""

from datetime import datetime
from io import BytesIO
import os
from pathlib import Path
import shutil
from typing import Any, Dict, List, Optional
import zipfile

from config import get_settings
from src.core.cache_utils import cache_job_status
from src.core.exceptions import InvalidOperationError, StorageError
from src.domain.models.job import Job, JobProgressDetails, JobStatus
from src.domain.repositories.job_repository import JobRepositoryInterface


class JobService:
    """Service for managing patient generation jobs."""

    def __init__(self, repository: JobRepositoryInterface):
        self.repository = repository
        self.settings = get_settings()

    async def create_job(self, config: Dict[str, Any]) -> Job:
        """Create a new generation job."""
        return await self.repository.create(config)

    async def get_job(self, job_id: str) -> Job:
        """Get a job by ID, checking cache first."""
        job = await self.repository.get(job_id)

        # Cache the job status for future requests
        await cache_job_status(job)

        return job

    async def list_jobs(self) -> List[Job]:
        """List all jobs."""
        return await self.repository.list_all()

    async def update_job_status(self, job_id: str, status: JobStatus, error: Optional[str] = None) -> None:
        """Update job status and cache."""
        job = await self.repository.get(job_id)
        job.status = status

        if error:
            job.error = error

        if status == JobStatus.COMPLETED:
            job.completed_at = datetime.utcnow()

        await self.repository.update(job)

        # Update cache with new status
        await cache_job_status(job)

    async def update_job_progress(
        self, job_id: str, progress: int, progress_details: Optional[JobProgressDetails] = None
    ) -> None:
        """Update job progress and cache."""
        job = await self.repository.get(job_id)
        job.progress = progress

        if progress_details:
            job.progress_details = progress_details

        await self.repository.update(job)

        # Update cache with new progress
        await cache_job_status(job)

    async def set_job_results(
        self, job_id: str, output_directory: str, result_files: List[str], summary: Optional[Dict[str, Any]] = None
    ) -> None:
        """Set job results."""
        job = await self.repository.get(job_id)
        job.output_directory = output_directory
        job.result_files = result_files

        if summary:
            job.summary = summary

        await self.repository.update(job)

    async def create_download_archive(self, job_id: str) -> BytesIO:
        """Create a ZIP archive of job results."""
        job = await self.repository.get(job_id)

        if job.status != JobStatus.COMPLETED:
            msg = f"Job {job_id} is not completed"
            raise StorageError(msg)

        # Reconstruct output directory path if not stored
        if not job.output_directory:
            import tempfile
            job.output_directory = os.path.join(tempfile.gettempdir(), "medical_patients", f"job_{job_id}")

        if not os.path.exists(job.output_directory):
            msg = f"Output directory not found for job {job_id}: {job.output_directory}"
            raise StorageError(msg)

        # Create in-memory ZIP
        zip_buffer = BytesIO()

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
            output_path = Path(job.output_directory)

            for file_path in output_path.rglob("*"):
                if file_path.is_file():
                    arcname = file_path.relative_to(output_path)
                    zipf.write(file_path, arcname)

        zip_buffer.seek(0)
        return zip_buffer

    async def cancel_job(self, job_id: str) -> Job:
        """Cancel a running or pending job."""
        job = await self.repository.get(job_id)

        # Only allow cancellation of pending or running jobs
        if job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
            error_msg = f"Cannot cancel job {job_id} with status {job.status.value}"
            raise InvalidOperationError(error_msg)

        job.status = JobStatus.CANCELLED
        job.completed_at = datetime.utcnow()
        job.error = "Job cancelled by user"

        await self.repository.update(job)
        return job

    async def cleanup_job_files(self, job_id: str) -> None:
        """Clean up job output files."""
        try:
            job = await self.repository.get(job_id)

            if job.output_directory and os.path.exists(job.output_directory):
                shutil.rmtree(job.output_directory)

            await self.repository.delete(job_id)

        except Exception as e:
            # Log error but don't raise - cleanup is best effort
            print(f"Error cleaning up job {job_id}: {e}")
