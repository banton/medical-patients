"""
API router for visualization data with v1 standardization.
Provides endpoints for dashboard data and patient visualization information.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from patient_generator.visualization_data import transform_job_data_for_visualization
from src.api.v1.dependencies.services import get_job_service
from src.api.v1.models import ErrorResponse, VisualizationDataResponse
from src.core.security_enhanced import verify_api_key
from src.domain.models.job import JobStatus
from src.domain.services.job_service import JobService

logger = logging.getLogger(__name__)

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


def _find_patients_file(job) -> Optional[str]:
    """Find the patients.json file for a job."""
    # Check output_directory first
    if job.output_directory and Path(job.output_directory).is_dir():
        patients_path = Path(job.output_directory) / "patients.json"
        if patients_path.is_file():
            return str(patients_path)

    # Check result_files for JSON file
    if job.result_files:
        for file_path in job.result_files:
            if file_path.endswith(".json") and Path(file_path).is_file():
                return file_path

    # Try default output location
    default_path = Path("output") / job.job_id / "patients.json"
    if default_path.is_file():
        return str(default_path)

    return None


def _load_patients_from_file(file_path: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """Load patients from a JSON file."""
    try:
        with open(file_path) as f:
            patients = json.load(f)

        if not isinstance(patients, list):
            logger.warning("Patients file does not contain a list: %s", file_path)
            return []

        if limit and limit > 0:
            return patients[:limit]
        return patients

    except json.JSONDecodeError as e:
        logger.error("Error parsing patients file %s: %s", file_path, e)
        return []
    except Exception as e:
        logger.error("Error loading patients file %s: %s", file_path, e)
        return []


def _format_patient_summary(patient: Dict[str, Any]) -> Dict[str, Any]:
    """Format a patient record for API response."""
    # Extract patient ID - handle various formats
    patient_id = patient.get("id") or patient.get("patient_id") or patient.get("identifier", "unknown")
    if isinstance(patient_id, dict):
        patient_id = patient_id.get("value", str(patient_id))

    # Extract name - may be in different formats
    name = patient.get("name")
    if isinstance(name, dict):
        name = name.get("text") or f"{name.get('given', '')} {name.get('family', '')}".strip()
    elif isinstance(name, list) and name:
        name = name[0].get("text") if isinstance(name[0], dict) else str(name[0])
    name = name or f"Patient {patient_id}"

    return {
        "id": str(patient_id),
        "name": name,
        "nationality": patient.get("nationality", "Unknown"),
        "age": patient.get("age"),
        "gender": patient.get("gender", "unknown"),
        "injury_type": patient.get("injury_type", "Unknown"),
        "triage_category": patient.get("triage_category", "Unknown"),
        "final_status": patient.get("final_status") or patient.get("status", "Unknown"),
        "front": patient.get("front", "Unknown"),
        "day_of_injury": patient.get("day_of_injury"),
    }


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
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Job {job_id} not found or not completed"
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
                "summary": {
                    "total_patients": 0,
                    "rtd_count": 0,
                    "kia_count": 0,
                    "evacuated_count": 0
                },
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
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve dashboard data: {e!s}"
        )


@router.get(
    "/patient-detail/{patient_id}",
    response_model=VisualizationDataResponse,
    summary="Get Patient Detail",
    description="""
    Retrieve detailed information for a specific patient.

    Returns comprehensive patient data including demographics,
    medical conditions, treatment history, and final status.

    Requires a job_id to locate the patient data file.
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
        patient_data = None
        data_source = "not_found"

        if job_id:
            try:
                job = await job_service.get_job(job_id)
                patients_file = _find_patients_file(job)

                if patients_file:
                    patients = _load_patients_from_file(patients_file)
                    # Find the specific patient
                    for patient in patients:
                        pid = patient.get("id") or patient.get("patient_id")
                        if isinstance(pid, dict):
                            pid = pid.get("value")
                        if str(pid) == str(patient_id):
                            patient_data = patient
                            data_source = "generated_file"
                            break

            except Exception as e:
                logger.warning("Error loading patient from job %s: %s", job_id, e)

        if not patient_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Patient {patient_id} not found. Ensure job_id is provided."
            )

        return VisualizationDataResponse(
            data=patient_data,
            metadata={
                "patient_id": patient_id,
                "job_id": job_id,
                "data_source": data_source,
            },
        )

    except HTTPException:
        raise
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

    If job_id is provided, loads from that specific job.
    Otherwise, uses the most recently completed job.
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
        sample_patients: List[Dict[str, Any]] = []
        data_source = "no_data"
        source_job_id = job_id

        # Try to find job with patient data
        target_job = None

        if job_id:
            try:
                target_job = await job_service.get_job(job_id)
            except Exception:
                logger.warning("Job %s not found", job_id)
        else:
            # Get most recent completed job
            jobs = await job_service.list_jobs()
            completed_jobs = [j for j in jobs if j.status == JobStatus.COMPLETED]
            if completed_jobs:
                target_job = max(completed_jobs, key=lambda j: j.created_at)
                source_job_id = target_job.job_id

        # Load patients from job
        if target_job:
            patients_file = _find_patients_file(target_job)
            if patients_file:
                raw_patients = _load_patients_from_file(patients_file, limit=limit)
                sample_patients = [_format_patient_summary(p) for p in raw_patients]
                data_source = "generated_file"
                logger.debug(
                    "Loaded %d patients from %s",
                    len(sample_patients), patients_file
                )

        return VisualizationDataResponse(
            data={"patients": sample_patients},
            metadata={
                "job_id": source_job_id,
                "requested_limit": limit,
                "actual_count": len(sample_patients),
                "data_source": data_source,
            },
        )

    except Exception as e:
        logger.error("Failed to retrieve sample patients: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve sample patients: {e!s}"
        )
