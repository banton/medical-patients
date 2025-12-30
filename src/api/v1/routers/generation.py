"""
Patient generation API endpoints with proper versioning and standardized models.
Replaces the old /api/generate endpoint with /api/v1/generation/.
"""

import json
import logging
import os
from pathlib import Path
import shutil
import tempfile
import traceback
from typing import Any, Dict

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.security import HTTPBearer

from patient_generator.database import ConfigurationRepository, Database
from patient_generator.schemas_config import ConfigurationTemplateCreate
from src.api.v1.dependencies.database import get_database
from src.api.v1.dependencies.services import get_job_service, get_patient_generation_service
from src.api.v1.models import ErrorResponse, GenerationRequest, GenerationResponse
from src.core.security_enhanced import verify_api_key
from src.domain.models.job import JobStatus
from src.domain.services.job_service import JobService
from src.domain.services.patient_generation_service import AsyncPatientGenerationService, GenerationContext

logger = logging.getLogger(__name__)

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
    Start a new patient generation job with advanced medical simulation features.

    ## Configuration Options:
    - **configuration_id**: Use a saved configuration from the database
    - **configuration**: Provide inline configuration with full control

    ## Key Configuration Fields:
    - **total_patients**: Number of patients to generate (1-10000)
    - **injury_mix**: Distribution of Disease, Non-Battle, and Battle injuries
    - **warfare_types**: Active combat scenarios (conventional, artillery, urban, etc.)
    - **medical_simulation**: Enable advanced features (TUM, diagnostic uncertainty, Markov routing)
    - **advanced_overrides**: Fine-tune scenario intensity, tempo, and medical parameters

    ## Scenario Modifiers (in advanced_overrides):
    - **intensity**: Controls casualty severity (low/medium/high/extreme)
    - **tempo**: Controls distribution pattern (sustained/escalating/surge/declining)
    - **special_events**: Triggers mass casualty events
    - **environmental_conditions**: Applies weather and terrain effects

    The endpoint returns immediately with a job ID. Poll `/api/v1/jobs/{job_id}` for status.

    See full documentation at `/docs` or `API_DOCUMENTATION.md` for detailed parameter explanations.
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
        update_dict = {
            "output_formats": request.output_formats,
            "use_compression": request.use_compression,
            "use_encryption": request.use_encryption,
            "encryption_password": request.encryption_password,
            "priority": request.priority,
        }

        # Only add total_patients if it's provided as an override
        if request.total_patients is not None:
            update_dict["total_patients"] = request.total_patients

        config_dict.update(update_dict)

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
    # Initialize flag for temporal configuration tracking
    temporal_config_present = False

    try:
        # Update job status to running
        await job_service.update_job_status(job_id, JobStatus.RUNNING)

        # Create output directory
        output_dir = Path(tempfile.gettempdir()) / "medical_patients" / f"job_{job_id}"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Handle temporal configuration if present
        # Check both root level and nested configuration object
        inner_config = config.get("configuration", config)

        # Log configuration details for debugging
        logger.debug("Config type: %s", type(inner_config).__name__)
        logger.debug("total_patients value: %s", inner_config.get("total_patients"))

        temporal_config_present = any(
            key in inner_config for key in ["warfare_types", "environmental_conditions", "special_events", "base_date"]
        )

        logger.debug("Temporal config detected: %s", temporal_config_present)
        if temporal_config_present:
            temporal_keys = [k for k in ["warfare_types", "environmental_conditions", "special_events", "base_date"] if k in inner_config]
            logger.debug("Found temporal keys: %s", temporal_keys)

        if temporal_config_present:
            # Write temporal configuration to injuries.json for flow simulator
            # Use the path relative to current working directory (works in both dev and Docker)
            injuries_path = os.path.abspath("patient_generator/injuries.json")

            temporal_injuries_config = {
                "total_patients": inner_config.get("total_patients", 1440),
                "days_of_fighting": inner_config.get("days_of_fighting", 8),
                "base_date": inner_config.get("base_date", "2025-06-01"),
                "warfare_types": inner_config.get(
                    "warfare_types",
                    {
                        "conventional": True,
                        "artillery": True,
                        "urban": False,
                        "guerrilla": False,
                        "drone": True,
                        "naval": False,
                        "cbrn": False,
                        "peacekeeping": False,
                    },
                ),
                "intensity": inner_config.get("intensity", "medium"),
                "tempo": inner_config.get("tempo", "sustained"),
                "special_events": inner_config.get(
                    "special_events", {"major_offensive": False, "ambush": False, "mass_casualty": True}
                ),
                "environmental_conditions": inner_config.get("environmental_conditions", {"night_operations": True}),
                "injury_mix": inner_config.get(
                    "injury_mix",
                    inner_config.get(
                        "injury_distribution", {"Disease": 0.52, "Non-Battle Injury": 0.33, "Battle Injury": 0.15}
                    ),
                ),
            }

            # Backup existing injuries.json
            backup_path = injuries_path + ".backup"
            if os.path.exists(injuries_path):
                shutil.copy2(injuries_path, backup_path)

            # Write temporal config to injuries.json
            with open(injuries_path, "w") as f:
                json.dump(temporal_injuries_config, f, indent=2)

            active_warfare = [k for k, v in temporal_injuries_config["warfare_types"].items() if v]
            logger.info("Temporal config written - warfare: %s, base_date: %s", active_warfare, temporal_injuries_config["base_date"])

        # Handle configuration source
        db_instance = Database.get_instance()
        config_repo = ConfigurationRepository(db_instance)

        if "configuration_id" in config:
            # Use existing configuration from database
            config_template = config_repo.get_configuration(config["configuration_id"])
            if not config_template:
                error_msg = f"Configuration {config['configuration_id']} not found"
                raise ValueError(error_msg)
        else:
            # Create configuration template for database
            # Use injury_mix if available (temporal), otherwise injury_distribution (legacy)
            injury_dist = inner_config.get("injury_mix") or inner_config.get(
                "injury_distribution", {"Disease": 0.52, "Non-Battle Injury": 0.33, "Battle Injury": 0.15}
            )

            config_create = ConfigurationTemplateCreate(
                name=inner_config.get("name", "Generated Configuration"),
                description=inner_config.get("description", "Auto-generated configuration"),
                total_patients=inner_config.get("total_patients", inner_config.get("count", 10)),
                injury_distribution=injury_dist,
                front_configs=inner_config.get("front_configs", []),
                facility_configs=inner_config.get("facility_configs", []),
            )

            # Save to database
            config_template = config_repo.create_configuration(config_create)

        # Override total_patients if provided in request
        # Check both root level and inner_config for total_patients
        override_total = inner_config.get("total_patients") or config.get("total_patients")
        if override_total is not None:
            # Create a copy of the config template with overridden total_patients
            config_dict = (
                config_template.dict() if hasattr(config_template, "dict") else config_template.__dict__.copy()
            )
            config_dict["total_patients"] = override_total
            # Convert back to the same type as config_template
            config_template = type(config_template)(**config_dict)

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
            progress = progress_data.get("progress", 0)
            # Cap progress at 1.0 (100%) to prevent validation errors
            progress = min(progress, 1.0)
            progress_percent = int(progress * 100)
            await job_service.update_job_progress(job_id, progress_percent)

        # Run generation
        result = await generation_service.generate_patients(generation_context, progress_callback)

        # Clean up temporary configuration from database after generation (only if we created it)
        if "configuration_id" not in config:
            try:
                config_repo.delete_configuration(config_template.id)
            except Exception as e:
                logger.warning("Could not clean up temporary configuration %s: %s", config_template.id, e)

        # Restore original injuries.json if we modified it
        if temporal_config_present:
            # Get the project root directory and construct correct path
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
            injuries_path = os.path.join(project_root, "patient_generator", "injuries.json")
            backup_path = injuries_path + ".backup"

            if os.path.exists(backup_path):
                shutil.move(backup_path, injuries_path)
                logger.debug("Restored original injuries.json")
            else:
                logger.warning("No backup found to restore injuries.json")

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
        # Restore original injuries.json if we modified it (even on failure)
        if temporal_config_present:
            try:
                # Get the project root directory and construct correct path
                project_root = os.path.dirname(
                    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
                )
                injuries_path = os.path.join(project_root, "patient_generator", "injuries.json")
                backup_path = injuries_path + ".backup"

                if os.path.exists(backup_path):
                    shutil.move(backup_path, injuries_path)
                    logger.debug("Restored original injuries.json after failure")
            except Exception as cleanup_error:
                logger.error("Failed to restore injuries.json: %s", cleanup_error)

        # Mark job as failed
        await job_service.update_job_status(job_id, JobStatus.FAILED, error=str(e))
        logger.error("Generation task failed for job %s: %s", job_id, e)
        logger.debug("Traceback: %s", traceback.format_exc())


@router.post(
    "/debug-temporal",
    summary="Debug Temporal Configuration",
    description="Debug endpoint to test temporal configuration detection",
    include_in_schema=False,  # Hide from API docs
)
async def debug_temporal_configuration(
    request: GenerationRequest,
    current_user: str = Depends(verify_api_key),
) -> Dict[str, Any]:
    """
    Debug endpoint to check how temporal configuration is being received and processed.
    """
    # Get the raw configuration
    config_dict = {}
    if request.configuration:
        config_dict = request.configuration.copy()

    # Check both locations for temporal config
    direct_temporal_keys = [
        k for k in ["warfare_types", "environmental_conditions", "special_events", "base_date"] if k in config_dict
    ]

    configuration_data = config_dict.get("configuration", config_dict)
    nested_temporal_keys = [
        k
        for k in ["warfare_types", "environmental_conditions", "special_events", "base_date"]
        if k in configuration_data
    ]

    # Check current injuries.json
    project_root = Path(__file__).parent.parent.parent.parent.parent
    injuries_path = project_root / "patient_generator" / "injuries.json"

    current_injuries = None
    if injuries_path.exists():
        try:
            with open(injuries_path) as f:
                current_injuries = json.load(f)
        except Exception:
            current_injuries = {"error": "Could not read injuries.json"}

    # Build debug response
    debug_info: Dict[str, Any] = {
        "request_structure": {
            "has_configuration_field": hasattr(request, "configuration") and request.configuration is not None,
            "has_configuration_id": hasattr(request, "configuration_id") and request.configuration_id is not None,
            "configuration_keys": list(config_dict.keys()) if config_dict else [],
        },
        "temporal_detection": {
            "direct_temporal_keys": direct_temporal_keys,
            "direct_has_temporal": len(direct_temporal_keys) > 0,
            "nested_temporal_keys": nested_temporal_keys,
            "nested_has_temporal": len(nested_temporal_keys) > 0,
            "configuration_is_nested": config_dict.get("configuration") is not None,
        },
        "configuration_sample": {
            "total_patients": configuration_data.get("total_patients", "NOT FOUND"),
            "warfare_types": configuration_data.get("warfare_types", "NOT FOUND"),
            "base_date": configuration_data.get("base_date", "NOT FOUND"),
        },
        "current_injuries_json": {
            "exists": injuries_path.exists(),
            "has_warfare_types": "warfare_types" in current_injuries if current_injuries else False,
            "warfare_types": current_injuries.get("warfare_types") if current_injuries else None,
        },
        "recommendation": "",
    }

    # Add recommendation
    if debug_info["temporal_detection"]["direct_has_temporal"]:
        debug_info["recommendation"] = (
            "✅ Temporal configuration found directly in request. Backend should work correctly."
        )
    elif debug_info["temporal_detection"]["nested_has_temporal"]:
        debug_info["recommendation"] = (
            "⚠️ Temporal configuration found nested under 'configuration'. Backend needs to check config.get('configuration', config)."
        )
    else:
        debug_info["recommendation"] = (
            "❌ No temporal configuration found. Check frontend is sending warfare_types, etc."
        )

    return debug_info


@router.get(
    "/check-injuries-config",
    summary="Check Current Injuries Configuration",
    description="Check the current content of injuries.json",
    include_in_schema=False,
)
async def check_injuries_config(
    current_user: str = Depends(verify_api_key),
) -> Dict[str, Any]:
    """
    Check the current injuries.json configuration file.
    """
    project_root = Path(__file__).parent.parent.parent.parent.parent
    injuries_path = project_root / "patient_generator" / "injuries.json"
    backup_path = injuries_path.with_suffix(".json.backup")

    result = {
        "injuries_json": {
            "path": str(injuries_path),
            "exists": injuries_path.exists(),
            "content": None,
            "has_temporal_config": False,
        },
        "backup": {
            "exists": backup_path.exists(),
            "path": str(backup_path),
        },
    }

    if injuries_path.exists():
        try:
            with open(injuries_path) as f:
                content = json.load(f)
            result["injuries_json"]["content"] = content
            result["injuries_json"]["has_temporal_config"] = "warfare_types" in content

            # Add analysis
            if "warfare_types" in content:
                active_warfare = [k for k, v in content.get("warfare_types", {}).items() if v]
                result["injuries_json"]["active_warfare_types"] = active_warfare
                result["injuries_json"]["base_date"] = content.get("base_date", "NOT SET")
                result["injuries_json"]["days_of_fighting"] = content.get("days_of_fighting", "NOT SET")
        except Exception as e:
            result["injuries_json"]["error"] = str(e)

    return result
