"""
API router for file downloads.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from src.api.v1.dependencies.services import get_job_service
from src.core.exceptions import JobNotFoundError, StorageError
from src.core.security import verify_api_key
from src.domain.services.job_service import JobService

# Router configuration
router = APIRouter(prefix="/api", tags=["downloads"], dependencies=[Depends(verify_api_key)])


@router.get("/download/{job_id}")
async def download_job_results(job_id: str, job_service: JobService = Depends(get_job_service)) -> StreamingResponse:
    """Download job results as ZIP archive."""
    try:
        # Create ZIP archive
        zip_buffer = await job_service.create_download_archive(job_id)

        # Return as streaming response
        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename=patient_data_{job_id}.zip"},
        )

    except JobNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Job {job_id} not found")
    except StorageError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
