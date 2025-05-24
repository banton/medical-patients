"""
Repository interface and implementation for job management.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid

from src.domain.models.job import Job, JobStatus, JobProgressDetails
from src.core.exceptions import JobNotFoundError


class JobRepositoryInterface(ABC):
    """Abstract interface for job repository."""
    
    @abstractmethod
    async def create(self, config: Dict[str, Any]) -> Job:
        """Create a new job."""
        pass
    
    @abstractmethod
    async def get(self, job_id: str) -> Job:
        """Get a job by ID."""
        pass
    
    @abstractmethod
    async def update(self, job: Job) -> None:
        """Update a job."""
        pass
    
    @abstractmethod
    async def list_all(self) -> List[Job]:
        """List all jobs."""
        pass
    
    @abstractmethod
    async def delete(self, job_id: str) -> None:
        """Delete a job."""
        pass


class InMemoryJobRepository(JobRepositoryInterface):
    """In-memory implementation of job repository."""
    
    def __init__(self):
        self._jobs: Dict[str, Job] = {}
    
    async def create(self, config: Dict[str, Any]) -> Job:
        """Create a new job."""
        job_id = str(uuid.uuid4())
        job = Job(
            job_id=job_id,
            status=JobStatus.INITIALIZING,
            created_at=datetime.utcnow(),
            config=config,
            progress=0
        )
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