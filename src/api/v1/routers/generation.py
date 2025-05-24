"""
API router for patient generation.
"""
import os
import tempfile
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel

from patient_generator.database import Database, ConfigurationRepository
from patient_generator.schemas_config import ConfigurationTemplateCreate, ConfigurationTemplateDB
from patient_generator.config_manager import ConfigurationManager
from src.domain.services.job_service import JobService
from src.domain.services.patient_generation_service import (
    AsyncPatientGenerationService,
    GenerationContext
)
from src.domain.models.job import JobStatus, JobProgressDetails
from src.api.v1.dependencies.database import get_database
from src.api.v1.dependencies.services import get_job_service
from src.core.security import verify_api_key
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
    tags=["generation"],
    dependencies=[Depends(verify_api_key)]
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
    """Background task for patient generation using async pipeline."""
    settings = get_settings()
    
    try:
        # Update job status to running
        await job_service.update_job_status(job_id, JobStatus.RUNNING)
        
        # Create output directory
        output_dir = os.path.join(settings.OUTPUT_DIRECTORY, f"job_{job_id}")
        os.makedirs(output_dir, exist_ok=True)
        
        # Create progress callback
        async def update_progress(current: int, total: int):
            progress = int((current / total) * 100) if total > 0 else 0
            phase = "Generating patients" if current < total else "Finalizing output"
            
            await job_service.update_job_progress(
                job_id,
                progress,
                JobProgressDetails(
                    current_phase=phase,
                    phase_description=f"Processing patient {current} of {total}",
                    phase_progress=progress,
                    total_patients=total,
                    processed_patients=current,
                    time_estimates={"total": 0.0}
                )
            )
        
        # Get or create configuration
        db = Database()
        repo = ConfigurationRepository(db)
        
        if config_id:
            # Load existing configuration
            config = repo.get_configuration(config_id)
            if not config:
                raise ValueError(f"Configuration {config_id} not found")
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
            use_compression=use_compression
        )
        
        # For now, fall back to the synchronous approach wrapped in async
        # The full async refactoring requires deeper changes to patient_generator module
        from patient_generator.app import PatientGeneratorApp
        
        # Create configuration manager and load configuration
        config_manager = ConfigurationManager(database_instance=db)
        config_manager.load_configuration(config.id)
        
        # Run generation in thread pool to avoid blocking
        def run_sync_generation():
            generator = PatientGeneratorApp(config_manager)
            
            # Run with proper parameters
            patients, bundles, gen_output_files, gen_summary = generator.run(
                output_directory=output_dir,
                output_formats=output_formats,
                use_compression=use_compression,
                use_encryption=use_encryption,
                encryption_password=encryption_password,
                progress_callback=None  # Could add async callback wrapper here
            )
            return gen_output_files
        
        # Run in thread pool
        import asyncio
        gen_output_files = await asyncio.to_thread(run_sync_generation)
        
        # Update progress
        await update_progress(config.total_patients, config.total_patients)
        
        result = {
            "status": "completed",
            "output_files": gen_output_files,
            "patient_count": config.total_patients
        }
        
        # Extract output files from result
        output_files = []
        if "output_files" in result:
            for file_path in result["output_files"]:
                rel_path = os.path.relpath(file_path, output_dir)
                output_files.append(rel_path)
        
        # Create summary
        summary = {
            "total_patients": config.total_patients,
            "generation_time": datetime.now(timezone.utc).isoformat(),
            "output_formats": output_formats,
            "compressed": use_compression,
            "encrypted": use_encryption is True
        }
        
        # Set job results
        await job_service.set_job_results(
            job_id,
            output_dir,
            output_files,
            summary
        )
        
        # Mark job as completed
        await job_service.update_job_status(job_id, JobStatus.COMPLETED)
        
        # Clean up temporary configuration if created
        if not config_id:
            repo.delete_configuration(config.id)
        
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
        
        config_dict = config.model_dump() if config else {}
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