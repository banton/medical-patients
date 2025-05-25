"""
API router for patient generation.
"""

from datetime import datetime, timezone
import os
from typing import Any, Dict, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel

from config import get_settings
from patient_generator.database import ConfigurationRepository, Database
from patient_generator.schemas_config import ConfigurationTemplateCreate
from src.api.v1.dependencies.database import get_database
from src.api.v1.dependencies.services import get_job_service
from src.core.security import verify_api_key
from src.domain.models.job import JobProgressDetails, JobStatus
from src.domain.services.job_service import JobService
from src.domain.services.patient_generation_service import AsyncPatientGenerationService, GenerationContext


# Request/Response models
class GenerationRequest(BaseModel):
    """Request model for patient generation."""

    configuration_id: Optional[str] = None
    configuration: Optional[ConfigurationTemplateCreate] = None
    output_formats: list[str] = ["json"]
    use_compression: bool = False
    use_encryption: bool = False
    encryption_password: Optional[str] = None


class GenerationResponse(BaseModel):
    """Response model for patient generation."""

    job_id: str
    status: str
    message: str


# Router configuration
router = APIRouter(prefix="/api", tags=["generation"], dependencies=[Depends(verify_api_key)])


async def run_patient_generation(
    job_id: str,
    job_service: JobService,
    config_dict: Dict[str, Any],
    output_formats: list[str],
    use_compression: bool,
    use_encryption: bool,
    encryption_password: Optional[str],
    config_id: Optional[str] = None,
) -> None:
    """Background task for patient generation using async pipeline."""
    settings = get_settings()

    try:
        # Update job status to running
        await job_service.update_job_status(job_id, JobStatus.RUNNING)

        # Create output directory
        output_dir = os.path.join(settings.OUTPUT_DIRECTORY, f"job_{job_id}")
        os.makedirs(output_dir, exist_ok=True)

        # Create progress callback
        async def update_progress(progress_data: Dict[str, Any]):
            # Extract progress information
            progress = progress_data.get("progress", 0)
            current = progress_data.get("processed_patients", 0)
            total = progress_data.get("total_patients", 0)
            phase_desc = progress_data.get("phase_description", f"Processing patient {current} of {total}")
            current_phase = progress_data.get("current_phase", "generating_patients")

            # Convert to percentage
            progress_percent = int(progress * 100) if progress <= 1 else int(progress)

            await job_service.update_job_progress(
                job_id,
                progress_percent,
                JobProgressDetails(
                    current_phase=current_phase,
                    phase_description=phase_desc,
                    phase_progress=progress_percent,
                    total_patients=total,
                    processed_patients=current,
                    time_estimates={"total": 0.0},
                ),
            )

        # Get or create configuration
        db = Database()
        repo = ConfigurationRepository(db)

        if config_id:
            # Load existing configuration
            config = repo.get_configuration(config_id)
            if not config:
                msg = f"Configuration {config_id} not found"
                raise ValueError(msg)
        else:
            # Create temporary configuration for ad-hoc generation
            temp_config_create = ConfigurationTemplateCreate(**config_dict)
            config = repo.create_configuration(temp_config_create)

        # Create generation context
        context = GenerationContext(
            config=config,
            job_id=job_id,
            output_directory=output_dir,
            encryption_password=encryption_password,
            output_formats=output_formats,
            use_compression=use_compression,
        )

        # Use async patient generation service
        generation_service = AsyncPatientGenerationService()
        result = await generation_service.generate_patients(context=context, progress_callback=update_progress)

        # Extract output files and summary
        gen_output_files = result.get("output_files", [])
        gen_summary = {
            "total_patients": result.get("patient_count", config.total_patients),
            "status": result.get("status", "completed"),
        }

        # Update final progress
        await update_progress(
            {
                "progress": 1.0,
                "processed_patients": config.total_patients,
                "total_patients": config.total_patients,
                "phase_description": f"Completed generating {config.total_patients} patients",
                "current_phase": "completed",
            }
        )

        result = {"status": "completed", "output_files": gen_output_files, "patient_count": config.total_patients}

        # Extract output files from result
        output_files = []
        if "output_files" in result:
            for file_path in result["output_files"]:
                rel_path = os.path.relpath(file_path, output_dir)
                output_files.append(rel_path)

        # Use summary from generator and add additional fields
        summary = gen_summary or {}
        summary.update(
            {
                "generation_time": datetime.now(timezone.utc).isoformat(),
                "output_formats": output_formats,
                "compressed": use_compression,
                "encrypted": use_encryption is True,
            }
        )

        # Set job results
        await job_service.set_job_results(job_id, output_dir, output_files, summary)

        # Mark job as completed
        await job_service.update_job_status(job_id, JobStatus.COMPLETED)

        # Clean up temporary configuration if created
        if not config_id:
            repo.delete_configuration(config.id)

    except Exception as e:
        # Mark job as failed
        await job_service.update_job_status(job_id, JobStatus.FAILED, error=str(e))
        raise


@router.post("/generate", response_model=GenerationResponse)
async def generate_patients(
    request: GenerationRequest,
    background_tasks: BackgroundTasks,
    job_service: JobService = Depends(get_job_service),
    db: Database = Depends(get_database),
) -> GenerationResponse:
    """Generate patients with specified configuration."""

    # Validate request
    if not request.configuration_id and not request.configuration:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Either configuration_id or configuration must be provided"
        )

    # Get configuration
    config_dict = None

    if request.configuration_id:
        # Load from database
        repo = ConfigurationRepository(db)
        config = repo.get_configuration(request.configuration_id)

        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Configuration {request.configuration_id} not found"
            )

        config_dict = config.model_dump() if config else {}
    else:
        # Use ad-hoc configuration
        config_dict = request.configuration.model_dump() if request.configuration else {}

    # Create job
    job = await job_service.create_job(
        {
            "configuration": config_dict,
            "output_formats": request.output_formats,
            "use_compression": request.use_compression,
            "use_encryption": request.use_encryption,
        }
    )

    # Queue background task
    background_tasks.add_task(
        run_patient_generation,
        job.job_id,
        job_service,
        config_dict,
        request.output_formats,
        request.use_compression,
        request.use_encryption,
        request.encryption_password,
        request.configuration_id,  # Pass the config_id if available
    )

    return GenerationResponse(job_id=job.job_id, status=job.status.value, message="Job queued for processing")
