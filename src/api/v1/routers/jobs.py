"""
API router for job management.
"""
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from src.domain.services.job_service import JobService
from src.domain.models.job import Job
from src.core.exceptions import JobNotFoundError, StorageError
from src.api.v1.dependencies.services import get_job_service
from src.core.security import verify_api_key


# Router configuration
router = APIRouter(
    prefix="/api/jobs",
    tags=["jobs"],
    dependencies=[Depends(verify_api_key)]
)


@router.get("/", response_model=List[Dict[str, Any]])
async def list_jobs(
    job_service: JobService = Depends(get_job_service)
) -> List[Dict[str, Any]]:
    """List all jobs."""
    jobs = await job_service.list_jobs()
    return [job.to_dict() for job in jobs]


@router.get("/{job_id}", response_model=Dict[str, Any])
async def get_job_status(
    job_id: str,
    job_service: JobService = Depends(get_job_service)
) -> Dict[str, Any]:
    """Get job status and details."""
    try:
        job = await job_service.get_job(job_id)
        return job.to_dict()
    except JobNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )


@router.get("/{job_id}/results", response_model=Dict[str, Any])
async def get_job_results(
    job_id: str,
    job_service: JobService = Depends(get_job_service)
) -> Dict[str, Any]:
    """Get job results summary."""
    try:
        job = await job_service.get_job(job_id)
        
        if job.status.value != "completed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Job {job_id} is not completed yet"
            )
        
        return {
            "job_id": job.job_id,
            "status": job.status.value,
            "summary": job.summary,
            "output_files": job.result_files,
            "created_at": job.created_at.isoformat(),
            "completed_at": job.completed_at.isoformat() if job.completed_at else None
        }
        
    except JobNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(
    job_id: str,
    job_service: JobService = Depends(get_job_service)
) -> None:
    """Delete a job and its associated files."""
    try:
        await job_service.cleanup_job_files(job_id)
    except JobNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )