"""
API router for job management with v1 standardization.
Provides endpoints for listing, retrieving, and managing patient generation jobs.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from src.api.v1.dependencies.services import get_job_service
from src.api.v1.models import DeleteResponse, ErrorResponse, JobResponse
from src.api.v1.models.responses import JobProgressDetails
from src.core.exceptions import JobNotFoundError
from src.core.security_enhanced import verify_api_key
from src.domain.services.job_service import JobService

# Router configuration with v1 prefix and standardized responses
router = APIRouter(
    prefix="/jobs",
    tags=["jobs"],
    dependencies=[Depends(verify_api_key)],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Job Not Found"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)


@router.get(
    "/",
    response_model=List[JobResponse],
    summary="List Jobs",
    description="Retrieve a list of all patient generation jobs",
    response_description="List of jobs with their current status and metadata",
)
async def list_jobs(job_service: JobService = Depends(get_job_service)) -> List[JobResponse]:
    """List all patient generation jobs with their current status."""
    try:
        jobs = await job_service.list_jobs()
        return [_job_to_response(job) for job in jobs]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to retrieve jobs: {e!s}")


@router.get(
    "/{job_id}",
    response_model=JobResponse,
    summary="Get Job Status",
    description="Retrieve detailed status and metadata for a specific job",
    response_description="Job details with current status and progress information",
)
async def get_job_status(job_id: str, job_service: JobService = Depends(get_job_service)) -> JobResponse:
    """Get detailed status and metadata for a specific job."""
    try:
        job = await job_service.get_job(job_id)
        return _job_to_response(job)
    except JobNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Job {job_id} not found")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to retrieve job {job_id}: {e!s}"
        )


@router.get(
    "/{job_id}/results",
    response_model=JobResponse,
    summary="Get Job Results",
    description="Retrieve results and output files for a completed job",
    response_description="Job results with output file information",
)
async def get_job_results(job_id: str, job_service: JobService = Depends(get_job_service)) -> JobResponse:
    """Get results and output files for a completed job."""
    try:
        job = await job_service.get_job(job_id)

        if job.status.value != "completed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Job {job_id} is not completed yet. Current status: {job.status.value}",
            )

        return _job_to_response(job)

    except JobNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Job {job_id} not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve job results for {job_id}: {e!s}",
        )


@router.delete(
    "/{job_id}",
    response_model=DeleteResponse,
    summary="Delete Job",
    description="Delete a job and all its associated files",
    response_description="Job successfully deleted",
)
async def delete_job(job_id: str, job_service: JobService = Depends(get_job_service)) -> DeleteResponse:
    """Delete a job and all its associated files."""
    try:
        await job_service.cleanup_job_files(job_id)
        return DeleteResponse(success=True, message="Job deleted successfully", deleted_id=job_id)
    except JobNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Job {job_id} not found")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to delete job {job_id}: {e!s}"
        )


@router.post(
    "/{job_id}/cancel",
    response_model=JobResponse,
    summary="Cancel Job",
    description="Cancel a running or pending job",
    response_description="Job cancellation status",
)
async def cancel_job(job_id: str, job_service: JobService = Depends(get_job_service)) -> JobResponse:
    """Cancel a running or pending job."""
    try:
        job = await job_service.cancel_job(job_id)
        return _job_to_response(job)
    except JobNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Job {job_id} not found")
    except Exception as e:
        # Check if it's an InvalidOperationError (job already completed/cancelled)
        error_msg = str(e)
        if "Cannot cancel job" in error_msg and "with status" in error_msg:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)

        # For other unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to cancel job {job_id}: {error_msg}"
        )


def _job_to_response(job) -> JobResponse:
    """Convert domain job object to JobResponse model."""
    # Create progress details if available
    progress_details = None
    if hasattr(job, "progress_details") and job.progress_details:
        # If it's already a JobProgressDetails object, use it directly
        if hasattr(job.progress_details, "current_phase"):
            progress_details = JobProgressDetails(
                current_step=job.progress_details.current_phase,
                total_steps=1,
                completed_steps=0,
                patients_generated=job.progress_details.processed_patients or 0,
                estimated_remaining_time=None,
                phase_description=job.progress_details.phase_description
                if hasattr(job.progress_details, "phase_description")
                else None,
            )
        # Handle legacy dictionary format
        elif isinstance(job.progress_details, dict):
            progress_details = JobProgressDetails(
                current_step=job.progress_details.get("current_step", "Unknown"),
                total_steps=job.progress_details.get("total_steps", 1),
                completed_steps=job.progress_details.get("completed_steps", 0),
                patients_generated=job.progress_details.get("patients_generated", 0),
                estimated_remaining_time=job.progress_details.get("estimated_remaining_time"),
            )

    return JobResponse(
        job_id=job.job_id,
        status=job.status,
        created_at=job.created_at,
        progress=getattr(job, "progress", 0),
        config=job.config if hasattr(job, "config") else {},
        completed_at=job.completed_at,
        error=job.error_message if hasattr(job, "error_message") else None,
        output_files=job.result_files if hasattr(job, "result_files") else [],
        progress_details=progress_details,
        summary=job.summary if hasattr(job, "summary") else None,
    )
