"""
Patient generation API endpoints with proper versioning and standardized models.
Replaces the old /api/generate endpoint with /api/v1/generation/.
"""

from typing import Any, Dict

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.security import HTTPBearer

from src.api.v1.dependencies.database import get_database
from src.api.v1.dependencies.services import get_job_service, get_patient_generation_service
from src.api.v1.models import ErrorResponse, GenerationRequest, GenerationResponse
from src.core.security import verify_api_key
from src.domain.services.job_service import JobService
from src.domain.services.patient_generation_service import AsyncPatientGenerationService

router = APIRouter(
    prefix="/generation",
    tags=["generation"],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        422: {"model": ErrorResponse, "description": "Validation Error"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)

security = HTTPBearer()


@router.post(
    "/",
    response_model=GenerationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate Patients",
    description="""
    Start a new patient generation job with the specified configuration.

    You can either:
    - Use an existing configuration by providing `configuration_id`
    - Provide an inline configuration using the `configuration` field

    The endpoint returns immediately with a job ID for tracking progress.
    Use the job endpoints to monitor generation status and download results.
    """,
    response_description="Generation job created successfully",
)
async def generate_patients(
    request: GenerationRequest,
    background_tasks: BackgroundTasks,
    current_user: str = Depends(verify_api_key),
    job_service: JobService = Depends(get_job_service),
    generation_service: AsyncPatientGenerationService = Depends(get_patient_generation_service),
    db_session=Depends(get_database),
) -> GenerationResponse:
    """
    Generate patients based on the provided configuration.

    This endpoint creates a background job for patient generation and returns
    immediately with job tracking information.
    """
    try:
        # Validate configuration source
        config_dict: Dict[str, Any] = {}
        if request.configuration_id:
            # TODO: Validate configuration_id exists in database
            config_dict = {"configuration_id": request.configuration_id}
        elif request.configuration:
            # Use inline configuration
            config_dict = request.configuration.copy()

        # Add generation parameters to config
        config_dict.update(
            {
                "output_formats": request.output_formats,
                "use_compression": request.use_compression,
                "use_encryption": request.use_encryption,
                "encryption_password": request.encryption_password,
                "priority": request.priority,
            }
        )

        # Create job
        job = await job_service.create_job(config=config_dict)

        # Start background generation
        background_tasks.add_task(_run_generation_task, job.job_id, config_dict, generation_service, job_service)

        # Estimate duration based on configuration
        estimated_duration = _estimate_generation_duration(config_dict)

        return GenerationResponse(
            job_id=job.job_id,
            status=job.status,
            message=f"Patient generation job '{job.job_id}' created successfully",
            estimated_duration=estimated_duration,
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to create generation job: {e!s}"
        )


def _estimate_generation_duration(config: Dict[str, Any]) -> int:
    """
    Estimate generation duration based on configuration parameters.

    Args:
        config: Job configuration dictionary

    Returns:
        Estimated duration in seconds
    """
    # Extract patient count from various possible config structures
    patient_count = config.get("count", 10)
    if isinstance(config.get("configuration"), dict):
        patient_count = config["configuration"].get("count", patient_count)

    # Base time: 0.5 seconds per patient
    base_time = patient_count * 0.5

    # Add time for multiple output formats
    format_multiplier = len(config.get("output_formats", ["json"]))
    base_time *= format_multiplier

    # Add time for compression
    if config.get("use_compression", False):
        base_time *= 1.2

    # Add time for encryption
    if config.get("use_encryption", False):
        base_time *= 1.3

    # Minimum 5 seconds, maximum 300 seconds (5 minutes)
    return max(5, min(int(base_time), 300))


async def _run_generation_task(
    job_id: str, config: Dict[str, Any], generation_service: AsyncPatientGenerationService, job_service: JobService
) -> None:
    """
    Background task to run patient generation.

    Args:
        job_id: Unique job identifier
        config: Generation configuration
        generation_service: Patient generation service
        job_service: Job management service
    """
    from pathlib import Path
    import tempfile

    from src.domain.models.job import JobStatus
    from src.domain.services.patient_generation_service import GenerationContext

    try:
        # Update job status to running
        await job_service.update_job_status(job_id, JobStatus.RUNNING)

        # Create output directory
        output_dir = Path(tempfile.gettempdir()) / "medical_patients" / f"job_{job_id}"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Handle configuration source
        from patient_generator.database import ConfigurationRepository, Database
        from patient_generator.schemas_config import ConfigurationTemplateCreate

        db_instance = Database.get_instance()
        config_repo = ConfigurationRepository(db_instance)

        if "configuration_id" in config:
            # Use existing configuration from database
            config_template = config_repo.get_configuration(config["configuration_id"])
            if not config_template:
                raise ValueError(f"Configuration {config['configuration_id']} not found")
        else:
            # Create configuration template for database
            config_create = ConfigurationTemplateCreate(
                name=config.get("name", "Generated Configuration"),
                description=config.get("description", "Auto-generated configuration"),
                total_patients=config.get("count", config.get("total_patients", 10)),
                injury_distribution=config.get(
                    "injury_distribution", {"Disease": 0.52, "Non-Battle Injury": 0.33, "Battle Injury": 0.15}
                ),
                front_configs=config.get("front_configs", []),
                facility_configs=config.get("facility_configs", []),
            )

            # Save to database
            config_template = config_repo.create_configuration(config_create)

        # Create generation context
        generation_context = GenerationContext(
            config=config_template,
            job_id=job_id,
            output_directory=str(output_dir),
            encryption_password=config.get("encryption_password"),
            output_formats=config.get("output_formats", ["json"]),
            use_compression=config.get("use_compression", False),
        )

        # Progress callback
        async def progress_callback(progress_data: Dict[str, Any]) -> None:
            progress_percent = int(progress_data.get("progress", 0) * 100)
            await job_service.update_job_progress(job_id, progress_percent)

        # Run generation
        result = await generation_service.generate_patients(generation_context, progress_callback)

        # Clean up temporary configuration from database after generation (only if we created it)
        if "configuration_id" not in config:
            try:
                config_repo.delete_configuration(config_template.id)
            except Exception as e:
                print(f"Warning: Could not clean up temporary configuration {config_template.id}: {e}")

        # Update job with results
        await job_service.set_job_results(
            job_id=job_id,
            output_directory=str(output_dir),
            result_files=result.get("output_files", []),
            summary={"total_patients": result.get("patient_count", 0)},
        )

        # Mark job as completed
        await job_service.update_job_status(job_id, JobStatus.COMPLETED)

    except Exception as e:
        # Mark job as failed
        await job_service.update_job_status(job_id, JobStatus.FAILED, error=str(e))
        print(f"Generation task failed for job {job_id}: {e}")
        import traceback

        traceback.print_exc()
