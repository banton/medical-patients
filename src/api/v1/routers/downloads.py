"""
API router for file downloads with v1 standardization.
Provides endpoints for downloading patient generation results.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from src.api.v1.dependencies.services import get_job_service
from src.api.v1.models import ErrorResponse
from src.core.exceptions import JobNotFoundError, StorageError
from src.core.security import verify_api_key
from src.domain.services.job_service import JobService

# Router configuration with v1 prefix and standardized responses
router = APIRouter(
    prefix="/downloads",
    tags=["downloads"],
    dependencies=[Depends(verify_api_key)],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Job Not Found"},
        400: {"model": ErrorResponse, "description": "Bad Request"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)


@router.get(
    "/{job_id}",
    summary="Download Job Results",
    description="""
    Download patient generation results as a ZIP archive.

    The archive contains all generated files in the requested output formats
    (JSON, CSV, XLSX, XML, FHIR) along with any metadata files.

    If encryption was enabled during generation, the archive will be
    password-protected using the provided encryption password.
    """,
    response_description="ZIP archive containing all generated patient data files",
    responses={
        200: {
            "description": "ZIP archive download",
            "content": {"application/zip": {"schema": {"type": "string", "format": "binary"}}},
        }
    },
)
async def download_job_results(job_id: str, job_service: JobService = Depends(get_job_service)) -> StreamingResponse:
    """Download patient generation results as a ZIP archive."""
    try:
        # Verify job exists and is completed
        job = await job_service.get_job(job_id)

        if job.status.value != "completed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Job {job_id} is not completed yet. Current status: {job.status.value}",
            )

        # Create ZIP archive
        zip_buffer = await job_service.create_download_archive(job_id)

        # Determine filename based on job configuration
        filename = f"patient_data_{job_id}.zip"
        if hasattr(job, "config") and job.config:
            config_name = job.config.get("name", job.config.get("configuration_id", job_id))
            if config_name:
                # Sanitize filename
                safe_name = "".join(c for c in config_name if c.isalnum() or c in (" ", "-", "_")).strip()
                if safe_name:
                    filename = f"{safe_name}_{job_id}.zip"

        # Return as streaming response
        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={"Content-Disposition": f'attachment; filename="{filename}"', "Content-Type": "application/zip"},
        )

    except JobNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Job {job_id} not found")
    except StorageError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Storage error: {e!s}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create download archive for job {job_id}: {e!s}",
        )
