"""
Tests for the job service.
"""
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from src.domain.services.job_service import JobService
from src.domain.models.job import Job, JobStatus, JobProgressDetails
from src.domain.repositories.job_repository import InMemoryJobRepository
from src.core.exceptions import JobNotFoundError


@pytest.mark.asyncio
async def test_create_job():
    """Test creating a new job."""
    repository = InMemoryJobRepository()
    service = JobService(repository)
    
    config = {"total_patients": 100}
    job = await service.create_job(config)
    
    assert job.job_id is not None
    assert job.status == JobStatus.INITIALIZING
    assert job.config == config
    assert job.progress == 0


@pytest.mark.asyncio
async def test_get_job():
    """Test getting a job by ID."""
    repository = InMemoryJobRepository()
    service = JobService(repository)
    
    # Create a job
    config = {"total_patients": 100}
    created_job = await service.create_job(config)
    
    # Get the job
    retrieved_job = await service.get_job(created_job.job_id)
    
    assert retrieved_job.job_id == created_job.job_id
    assert retrieved_job.config == config


@pytest.mark.asyncio
async def test_get_nonexistent_job():
    """Test getting a job that doesn't exist."""
    repository = InMemoryJobRepository()
    service = JobService(repository)
    
    with pytest.raises(JobNotFoundError):
        await service.get_job("nonexistent-id")


@pytest.mark.asyncio
async def test_update_job_status():
    """Test updating job status."""
    repository = InMemoryJobRepository()
    service = JobService(repository)
    
    # Create a job
    job = await service.create_job({"total_patients": 100})
    
    # Update status to running
    await service.update_job_status(job.job_id, JobStatus.RUNNING)
    updated_job = await service.get_job(job.job_id)
    assert updated_job.status == JobStatus.RUNNING
    
    # Update status to completed
    await service.update_job_status(job.job_id, JobStatus.COMPLETED)
    completed_job = await service.get_job(job.job_id)
    assert completed_job.status == JobStatus.COMPLETED
    assert completed_job.completed_at is not None


@pytest.mark.asyncio
async def test_update_job_progress():
    """Test updating job progress."""
    repository = InMemoryJobRepository()
    service = JobService(repository)
    
    # Create a job
    job = await service.create_job({"total_patients": 100})
    
    # Update progress
    progress_details = JobProgressDetails(
        current_phase="Generating patients",
        phase_description="Processing batch 1",
        phase_progress=50,
        total_patients=100,
        processed_patients=50
    )
    
    await service.update_job_progress(job.job_id, 50, progress_details)
    
    updated_job = await service.get_job(job.job_id)
    assert updated_job.progress == 50
    assert updated_job.progress_details.processed_patients == 50


@pytest.mark.asyncio
async def test_set_job_results():
    """Test setting job results."""
    repository = InMemoryJobRepository()
    service = JobService(repository)
    
    # Create a job
    job = await service.create_job({"total_patients": 100})
    
    # Set results
    output_dir = "/tmp/job_123"
    result_files = ["patients.json", "summary.json"]
    summary = {"total_patients": 100, "rtd_count": 50, "kia_count": 10}
    
    await service.set_job_results(job.job_id, output_dir, result_files, summary)
    
    updated_job = await service.get_job(job.job_id)
    assert updated_job.output_directory == output_dir
    assert updated_job.result_files == result_files
    assert updated_job.summary == summary


@pytest.mark.asyncio
async def test_list_jobs():
    """Test listing all jobs."""
    repository = InMemoryJobRepository()
    service = JobService(repository)
    
    # Create multiple jobs
    jobs = []
    for i in range(3):
        job = await service.create_job({"total_patients": 100 + i})
        jobs.append(job)
    
    # List jobs
    all_jobs = await service.list_jobs()
    
    assert len(all_jobs) == 3
    for created_job in jobs:
        assert any(j.job_id == created_job.job_id for j in all_jobs)