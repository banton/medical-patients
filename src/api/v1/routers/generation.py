"""
API router for patient generation.
"""
import os
import tempfile
from datetime import datetime
from typing import Optional, Dict, Any
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel

from patient_generator.app import PatientGeneratorApp
from patient_generator.config_manager import ConfigurationManager
from patient_generator.database import Database, ConfigurationRepository
from patient_generator.schemas_config import ConfigurationTemplateCreate
from src.domain.services.job_service import JobService
from src.domain.models.job import JobStatus, JobProgressDetails
from src.api.v1.dependencies.database import get_database
from src.api.v1.dependencies.services import get_job_service
from config import get_settings


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
router = APIRouter(
    prefix="/api",
    tags=["generation"]
)


async def run_patient_generation(
    job_id: str,
    job_service: JobService,
    config_dict: Dict[str, Any],
    output_formats: list[str],
    use_compression: bool,
    use_encryption: bool,
    encryption_password: Optional[str],
    config_id: Optional[str] = None
) -> None:
    """Background task for patient generation."""
    settings = get_settings()
    
    try:
        # Update job status to running
        await job_service.update_job_status(job_id, JobStatus.RUNNING)
        
        # Create output directory
        output_dir = os.path.join(settings.OUTPUT_DIRECTORY, f"job_{job_id}")
        os.makedirs(output_dir, exist_ok=True)
        
        # Create progress callback
        async def update_progress(current: int, total: int, phase: str = "Generating patients"):
            progress = int((current / total) * 100) if total > 0 else 0
            await job_service.update_job_progress(
                job_id,
                progress,
                JobProgressDetails(
                    current_phase=phase,
                    phase_description=f"Processing patient {current} of {total}",
                    phase_progress=progress,
                    total_patients=total,
                    processed_patients=current,
                    time_estimates={"total": 0.0}  # Set to 0.0 instead of None
                )
            )
        
        # Create configuration manager and load the configuration
        config_manager = ConfigurationManager()
        
        # If we have a configuration_id, use it. Otherwise create a temporary one
        if config_id:
            config_manager.load_configuration(config_id)
        else:
            # For ad-hoc configurations, we need to create a temporary config in the database
            # This is a limitation of the current design that expects configs to be in the database
            db = Database()
            repo = ConfigurationRepository(db)
            from patient_generator.schemas_config import ConfigurationTemplateCreate
            
            # Convert config_dict back to ConfigurationTemplateCreate
            temp_config_create = ConfigurationTemplateCreate(**config_dict)
            temp_config = repo.create_configuration(temp_config_create)
            config_manager.load_configuration(temp_config.id)
        
        # Initialize and run generator
        generator = PatientGeneratorApp(config_manager)
        
        # Note: This is still synchronous - we'll address async in a later task
        # The run method returns (patients, bundles, output_files, summary)
        patients, bundles, output_files_from_gen, summary = generator.run()
        
        # Update final progress
        await update_progress(
            config_dict.get("total_patients", 0),
            config_dict.get("total_patients", 0),
            "Finalizing output"
        )
        
        # Get list of output files
        output_files = []
        for root, _, files in os.walk(output_dir):
            for file in files:
                rel_path = os.path.relpath(os.path.join(root, file), output_dir)
                output_files.append(rel_path)
        
        # Set job results
        await job_service.set_job_results(
            job_id,
            output_dir,
            output_files,
            summary
        )
        
        # Mark job as completed
        await job_service.update_job_status(job_id, JobStatus.COMPLETED)
        
    except Exception as e:
        # Mark job as failed
        await job_service.update_job_status(
            job_id,
            JobStatus.FAILED,
            error=str(e)
        )
        raise


@router.post("/generate", response_model=GenerationResponse)
async def generate_patients(
    request: GenerationRequest,
    background_tasks: BackgroundTasks,
    job_service: JobService = Depends(get_job_service),
    db: Database = Depends(get_database)
) -> GenerationResponse:
    """Generate patients with specified configuration."""
    
    # Validate request
    if not request.configuration_id and not request.configuration:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either configuration_id or configuration must be provided"
        )
    
    # Get configuration
    config_dict = None
    
    if request.configuration_id:
        # Load from database
        repo = ConfigurationRepository(db)
        config = repo.get_configuration(request.configuration_id)
        
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Configuration {request.configuration_id} not found"
            )
        
        config_dict = config.model_dump()
    else:
        # Use ad-hoc configuration
        config_dict = request.configuration.model_dump()
    
    # Create job
    job = await job_service.create_job({
        "configuration": config_dict,
        "output_formats": request.output_formats,
        "use_compression": request.use_compression,
        "use_encryption": request.use_encryption
    })
    
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
        request.configuration_id  # Pass the config_id if available
    )
    
    return GenerationResponse(
        job_id=job.job_id,
        status=job.status.value,
        message="Job queued for processing"
    )