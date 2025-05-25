"""
Repository interface and implementation for job management.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List
import uuid

from src.core.exceptions import JobNotFoundError
from src.domain.models.job import Job, JobStatus


class JobRepositoryInterface(ABC):
    """Abstract interface for job repository."""

    @abstractmethod
    async def create(self, config: Dict[str, Any]) -> Job:
        """Create a new job."""

    @abstractmethod
    async def get(self, job_id: str) -> Job:
        """Get a job by ID."""

    @abstractmethod
    async def update(self, job: Job) -> None:
        """Update a job."""

    @abstractmethod
    async def list_all(self) -> List[Job]:
        """List all jobs."""

    @abstractmethod
    async def delete(self, job_id: str) -> None:
        """Delete a job."""


class InMemoryJobRepository(JobRepositoryInterface):
    """In-memory implementation of job repository."""

    def __init__(self):
        self._jobs: Dict[str, Job] = {}

    async def create(self, config: Dict[str, Any]) -> Job:
        """Create a new job."""
        job_id = str(uuid.uuid4())
        job = Job(job_id=job_id, status=JobStatus.INITIALIZING, created_at=datetime.utcnow(), config=config, progress=0)
        self._jobs[job_id] = job
        return job

    async def get(self, job_id: str) -> Job:
        """Get a job by ID."""
        if job_id not in self._jobs:
            raise JobNotFoundError(job_id)
        return self._jobs[job_id]

    async def update(self, job: Job) -> None:
        """Update a job."""
        if job.job_id not in self._jobs:
            raise JobNotFoundError(job.job_id)
        self._jobs[job.job_id] = job

    async def list_all(self) -> List[Job]:
        """List all jobs."""
        return list(self._jobs.values())

    async def delete(self, job_id: str) -> None:
        """Delete a job."""
        if job_id not in self._jobs:
            raise JobNotFoundError(job_id)
        del self._jobs[job_id]
