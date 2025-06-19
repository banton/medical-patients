"""
Streaming patient generation endpoint for memory-efficient large-scale generation.
Part of EPIC-003: Production Scalability Improvements - Phase 3
"""

import asyncio
import gc
import json
from pathlib import Path
import tempfile
from typing import AsyncIterator, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBearer

from patient_generator.repository import ConfigurationRepository
from src.infrastructure.database_adapter import get_enhanced_database
from patient_generator.schemas_config import ConfigurationTemplateCreate
from src.api.v1.dependencies.services import get_patient_generation_service
from src.api.v1.models.responses import StreamingPatientResponse
from src.core.security_enhanced import verify_api_key
from src.domain.services.patient_generation_service import (
    AsyncPatientGenerationService,
    GenerationContext,
)

router = APIRouter(
    prefix="/streaming",
    tags=["streaming"],
)

security = HTTPBearer()


async def generate_patients_stream(
    config_id: str,
    patient_count: int,
    batch_size: int = 100,
    generation_service: AsyncPatientGenerationService = None,
) -> AsyncIterator[bytes]:
    """
    Generate patients as a streaming JSON response.

    This generator yields JSON data in chunks to minimize memory usage.
    Each batch of patients is generated, serialized, and yielded before
    moving to the next batch.

    Args:
        config_id: Configuration ID to use
        patient_count: Total number of patients to generate
        batch_size: Number of patients per batch
        generation_service: Patient generation service instance

    Yields:
        JSON bytes for streaming response
    """
    # Start JSON array
    yield b'{\n  "patients": [\n'

    # Get configuration from database
    db_instance = get_enhanced_database()
    config_repo = ConfigurationRepository(db_instance)

    config_template = config_repo.get_configuration(config_id)
    if not config_template:
        # Handle error in stream
        yield b']\n, "error": "Configuration not found"\n}'
        return

    # Override patient count if specified
    if patient_count:
        config_template.total_patients = patient_count

    # Create generation context
    output_dir = Path(tempfile.gettempdir()) / "medical_patients" / f"stream_{config_id}"
    output_dir.mkdir(parents=True, exist_ok=True)

    context = GenerationContext(
        config=config_template,
        job_id=f"stream_{config_id}",
        output_directory=str(output_dir),
        output_formats=["json"],  # Only JSON for streaming
        use_compression=False,  # No compression for streaming
    )

    # Initialize the generation pipeline
    assert generation_service is not None, "Generation service is required"
    generation_service._initialize_pipeline(config_id)

    # Track progress
    first_patient = True
    patients_generated = 0

    try:
        # Generate patients in batches
        if not hasattr(generation_service, "pipeline") or generation_service.pipeline is None:
            yield b']\n, "error": "Generation service not initialized"\n}'
            return
        async for _patient, patient_data in generation_service.pipeline.generate(context):
            # Add comma separator if not first patient
            if not first_patient:
                yield b",\n"
            else:
                first_patient = False

            # Serialize patient data
            patient_json = json.dumps(patient_data, indent=4)
            # Indent for array formatting
            indented_json = "\n".join(f"    {line}" for line in patient_json.split("\n"))
            yield indented_json.encode("utf-8")

            patients_generated += 1

            # Force garbage collection every batch_size patients
            if patients_generated % batch_size == 0:
                gc.collect()

                # Small delay to prevent overwhelming the system
                await asyncio.sleep(0.01)

            # Stop if we've generated enough patients
            if patients_generated >= patient_count:
                break

    except Exception as e:
        # Include error in response
        error_msg = f"Error during generation: {e!s}"
        yield f'\n  ],\n  "error": "{error_msg}",\n  "patients_generated": {patients_generated}\n}}'.encode()
        return

    # Close JSON array
    yield f'\n  ],\n  "total_patients": {patients_generated}\n}}'.encode()


@router.get(
    "/generate",
    response_class=StreamingResponse,
    summary="Stream Patient Generation",
    description="""
    Generate patients with streaming JSON response for memory-efficient processing.

    This endpoint streams patients as they are generated, allowing clients to process
    large datasets without loading everything into memory at once.

    The response is a JSON object with a 'patients' array that is streamed incrementally.
    """,
    responses={
        200: {
            "description": "Streaming JSON response",
            "content": {
                "application/json": {
                    "schema": StreamingPatientResponse.schema(),
                    "example": {
                        "patients": [
                            {
                                "patient_id": "NATO-BEL-12345",
                                "name": "John Doe",
                                "injury_type": "Battle Injury"
                            }
                        ],
                        "total_patients": 100
                    }
                }
            },
        }
    },
)
async def stream_patients(
    configuration_id: str = Query(..., description="Configuration ID to use for generation"),
    count: Optional[int] = Query(None, description="Override patient count (uses config default if not specified)"),
    batch_size: int = Query(100, description="Number of patients per batch (affects memory usage)"),
    current_user: str = Depends(verify_api_key),
    generation_service: AsyncPatientGenerationService = Depends(get_patient_generation_service),
) -> StreamingResponse:
    """
    Stream patient generation with minimal memory footprint.

    Returns a streaming JSON response where patients are generated and sent
    in batches to minimize server memory usage.
    """
    try:
        # Validate batch size
        if batch_size < 1 or batch_size > 1000:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Batch size must be between 1 and 1000"
            )

        # Get configuration to determine patient count
        db_instance = get_enhanced_database()
        config_repo = ConfigurationRepository(db_instance)

        config_template = config_repo.get_configuration(configuration_id)
        if not config_template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Configuration '{configuration_id}' not found"
            )

        # Use provided count or configuration default
        patient_count = count if count is not None else config_template.total_patients

        # Validate patient count
        if patient_count < 1:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Patient count must be at least 1"
            )

        # Warm up caches before streaming
        await generation_service.cached_demographics.warm_cache()
        await generation_service.cached_medical.warm_cache()

        # Create streaming response
        return StreamingResponse(
            generate_patients_stream(
                config_id=configuration_id,
                patient_count=patient_count,
                batch_size=batch_size,
                generation_service=generation_service,
            ),
            media_type="application/json",
            headers={
                "Cache-Control": "no-cache",
                "X-Content-Type-Options": "nosniff",
                "X-Patient-Count": str(patient_count),
                "X-Batch-Size": str(batch_size),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to start streaming generation: {e!s}"
        )


@router.post(
    "/generate",
    response_class=StreamingResponse,
    summary="Stream Patient Generation with Configuration",
    description="""
    Generate patients with streaming JSON response using inline configuration.

    This endpoint accepts a configuration in the request body and streams patients
    as they are generated. Useful for one-off generations without saving configurations.
    """,
    responses={
        200: {
            "description": "Streaming JSON response",
            "content": {
                "application/json": {
                    "schema": StreamingPatientResponse.schema(),
                    "example": {
                        "patients": [
                            {
                                "patient_id": "NATO-BEL-12345",
                                "name": "John Doe",
                                "injury_type": "Battle Injury"
                            }
                        ],
                        "total_patients": 100
                    }
                }
            },
        }
    },
)
async def stream_patients_with_config(
    config: dict,
    batch_size: int = Query(100, description="Number of patients per batch"),
    current_user: str = Depends(verify_api_key),
    generation_service: AsyncPatientGenerationService = Depends(get_patient_generation_service),
) -> StreamingResponse:
    """
    Stream patient generation with inline configuration.
    """
    try:
        # Validate batch size
        if batch_size < 1 or batch_size > 1000:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Batch size must be between 1 and 1000"
            )

        # Create temporary configuration
        db_instance = get_enhanced_database()
        config_repo = ConfigurationRepository(db_instance)

        # Extract configuration data
        inner_config = config.get("configuration", config)
        injury_dist = inner_config.get("injury_mix") or inner_config.get(
            "injury_distribution", {"Disease": 0.52, "Non-Battle Injury": 0.33, "Battle Injury": 0.15}
        )

        config_create = ConfigurationTemplateCreate(
            name=inner_config.get("name", "Streaming Configuration"),
            description=inner_config.get("description", "Temporary configuration for streaming"),
            total_patients=inner_config.get("count", inner_config.get("total_patients", 10)),
            injury_distribution=injury_dist,
            front_configs=inner_config.get("front_configs", []),
            facility_configs=inner_config.get("facility_configs", []),
        )

        # Save temporary configuration
        config_template = config_repo.create_configuration(config_create)

        try:
            # Warm up caches
            await generation_service.cached_demographics.warm_cache()
            await generation_service.cached_medical.warm_cache()

            # Create streaming response
            return StreamingResponse(
                generate_patients_stream(
                    config_id=config_template.id,
                    patient_count=config_template.total_patients,
                    batch_size=batch_size,
                    generation_service=generation_service,
                ),
                media_type="application/json",
                headers={
                    "Cache-Control": "no-cache",
                    "X-Content-Type-Options": "nosniff",
                    "X-Patient-Count": str(config_template.total_patients),
                    "X-Batch-Size": str(batch_size),
                },
            )

        finally:
            # Schedule cleanup of temporary configuration
            # This will happen after response is sent
            async def cleanup():
                await asyncio.sleep(5)  # Give time for streaming to start
                try:
                    config_repo.delete_configuration(config_template.id)
                except Exception as e:
                    print(f"Warning: Could not clean up temporary configuration {config_template.id}: {e}")

            # Store reference to avoid task being garbage collected
            # The task will run independently and clean up after streaming
            asyncio.create_task(cleanup())  # noqa: RUF006

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to start streaming generation: {e!s}"
        )
