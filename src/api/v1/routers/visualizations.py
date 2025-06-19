"""
API router for visualization data with v1 standardization.
Provides endpoints for dashboard data and patient visualization information.
"""

import random
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from patient_generator.visualization_data import transform_job_data_for_visualization
from src.api.v1.dependencies.services import get_job_service
from src.api.v1.models import ErrorResponse, VisualizationDataResponse
from src.core.security_enhanced import verify_api_key
from src.domain.models.job import JobStatus
from src.domain.services.job_service import JobService

# Router configuration with v1 prefix and standardized responses
router = APIRouter(
    prefix="/visualizations",
    tags=["visualizations"],
    dependencies=[Depends(verify_api_key)],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Resource Not Found"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)


@router.get(
    "/dashboard-data",
    response_model=VisualizationDataResponse,
    summary="Get Dashboard Data",
    description="""
    Retrieve aggregated data for the visualization dashboard.

    If a job_id is provided, returns data specific to that job (if completed).
    Otherwise returns data from the most recently completed job.

    Dashboard data includes:
    - Patient summary statistics
    - Front and nationality distributions
    - Injury type distributions
    - Treatment flow data
    - Timeline data
    - Facility load information
    """,
    response_description="Dashboard visualization data with metadata",
)
async def get_dashboard_data(
    job_id: Optional[str] = Query(None, description="Specific job ID to get data for"),
    job_service: JobService = Depends(get_job_service),
) -> VisualizationDataResponse:
    """Get aggregated data for the visualization dashboard."""
    try:
        # Get all jobs
        jobs = await job_service.list_jobs()
        completed_jobs = [j for j in jobs if j.status == JobStatus.COMPLETED]

        # If specific job requested
        target_job_data = None
        if job_id:
            try:
                job = await job_service.get_job(job_id)
                if job.status == JobStatus.COMPLETED and job.summary:
                    target_job_data = transform_job_data_for_visualization(
                        {
                            "config": job.config,
                            "summary": job.summary,
                            "bundles": [],  # Bundles not stored in job
                        }
                    )
            except Exception:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail=f"Job {job_id} not found or not completed"
                )

        # If no specific job or job not found, use most recent
        if not target_job_data and completed_jobs:
            recent_job = max(completed_jobs, key=lambda j: j.created_at)
            if recent_job.summary:
                target_job_data = transform_job_data_for_visualization(
                    {"config": recent_job.config, "summary": recent_job.summary, "bundles": []}
                )

        # Return data or empty structure
        dashboard_data = (
            target_job_data
            if target_job_data
            else {
                "summary": {"total_patients": 0, "rtd_count": 0, "kia_count": 0, "evacuated_count": 0},
                "front_distribution": [],
                "nationality_distribution": [],
                "injury_distribution": [],
                "flow_data": {"nodes": [], "links": []},
                "timeline_data": [],
                "facility_load": [],
            }
        )

        return VisualizationDataResponse(
            data=dashboard_data,
            metadata={
                "job_id": job_id,
                "total_completed_jobs": len(completed_jobs),
                "data_source": "completed_job" if target_job_data else "empty",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to retrieve dashboard data: {e!s}"
        )


@router.get(
    "/patient-detail/{patient_id}",
    response_model=VisualizationDataResponse,
    summary="Get Patient Detail",
    description="""
    Retrieve detailed information for a specific patient.

    Returns comprehensive patient data including demographics,
    medical conditions, treatment history, and final status.

    Note: This endpoint currently returns mock data for demonstration.
    In production, it would load actual patient data from generated files.
    """,
    response_description="Detailed patient information",
)
async def get_patient_detail(
    patient_id: str,
    job_id: Optional[str] = Query(None, description="Job ID to load patient data from"),
    job_service: JobService = Depends(get_job_service),
) -> VisualizationDataResponse:
    """Get detailed information for a specific patient."""
    try:
        # TODO: In production, load actual patient data from generated files
        # For now, return mock data for demonstration
        patient_data = {
            "id": patient_id,
            "name": f"Patient {patient_id}",
            "nationality": "USA",
            "gender": "male",
            "age": 25,
            "injury_type": "Battle Injury",
            "conditions": ["Gunshot wound"],
            "treatment_history": [
                {
                    "facility": "POI",
                    "arrival_time": "2024-01-01T08:00:00Z",
                    "departure_time": "2024-01-01T08:30:00Z",
                    "treatments": ["First aid", "Stabilization"],
                }
            ],
            "final_status": "Evacuated",
        }

        return VisualizationDataResponse(
            data=patient_data,
            metadata={
                "patient_id": patient_id,
                "job_id": job_id,
                "data_source": "mock_data",
                "note": "This endpoint returns mock data for demonstration",
            },
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve patient detail for {patient_id}: {e!s}",
        )


@router.get(
    "/sample-patients",
    response_model=VisualizationDataResponse,
    summary="Get Sample Patients",
    description="""
    Retrieve a sample of patients from a generation job.

    Returns a limited number of patient records for visualization
    and preview purposes. Useful for dashboards and data exploration.

    Note: This endpoint currently returns mock data for demonstration.
    In production, it would load actual patient data from generated files.
    """,
    response_description="Sample patient data for visualization",
)
async def get_sample_patients(
    job_id: Optional[str] = Query(None, description="Job ID to load patient data from"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of patients to return"),
    job_service: JobService = Depends(get_job_service),
) -> VisualizationDataResponse:
    """Get a sample of patients from a generation job."""
    try:
        # TODO: In production, load actual patient data from generated files
        # For now, return mock data for demonstration
        sample_patients = []

        for i in range(limit):
            sample_patients.append(
                {
                    "id": f"patient_{i}",
                    "name": f"Patient {i}",
                    "nationality": random.choice(["USA", "POL", "EST", "FIN"]),
                    "age": random.randint(18, 45),
                    "gender": random.choice(["male", "female"]),
                    "injury_type": random.choice(["Battle Injury", "Disease", "Non-Battle Injury"]),
                    "final_status": random.choice(["RTD", "KIA", "Evacuated"]),
                }
            )

        return VisualizationDataResponse(
            data={"patients": sample_patients},
            metadata={
                "job_id": job_id,
                "requested_limit": limit,
                "actual_count": len(sample_patients),
                "data_source": "mock_data",
                "note": "This endpoint returns mock data for demonstration",
            },
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to retrieve sample patients: {e!s}"
        )
