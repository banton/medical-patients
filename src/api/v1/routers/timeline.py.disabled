"""
Timeline and evacuation statistics API endpoints.
Provides access to patient timeline data and evacuation metrics.
"""

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from src.api.v1.dependencies.services import get_job_service
from src.api.v1.models.responses import ErrorResponse
from src.core.security import verify_api_key
from src.domain.services.job_service import JobService

router = APIRouter(prefix="/timeline", tags=["timeline"], dependencies=[Depends(verify_api_key)])


@router.get(
    "/jobs/{job_id}/patients/{patient_id}",
    summary="Get patient timeline",
    description="Retrieve detailed timeline for a specific patient including evacuation and transit events",
    responses={
        200: {"description": "Patient timeline retrieved successfully"},
        404: {"description": "Job or patient not found", "model": ErrorResponse},
        500: {"description": "Internal server error", "model": ErrorResponse},
    },
)
async def get_patient_timeline(
    job_id: str = Path(..., description="Job ID"),
    patient_id: int = Path(..., description="Patient ID within the job"),
    job_service: JobService = Depends(get_job_service),
) -> Dict[str, Any]:
    """
    Get detailed timeline for a specific patient.

    Returns comprehensive timeline data including:
    - Movement events (arrival, evacuation_start, transit_start)
    - Timing details (hours since injury, duration)
    - Final status (KIA, RTD, Remains_Role4)
    - Facility progression
    """
    try:
        # Get job data
        job = await job_service.get_job(job_id)
        if not job:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Job {job_id} not found")

        # Extract patient timeline from job results
        # This would need to be implemented in the job service to parse patient data
        timeline_data = await job_service.get_patient_timeline(job_id, patient_id)
        if not timeline_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Patient {patient_id} not found in job {job_id}"
            )

        return {
            "job_id": job_id,
            "patient_id": patient_id,
            "timeline": timeline_data.get("movement_timeline", []),
            "summary": {
                "total_events": len(timeline_data.get("movement_timeline", [])),
                "final_status": timeline_data.get("final_status"),
                "last_facility": timeline_data.get("last_facility"),
                "total_duration_hours": timeline_data.get("total_duration_hours", 0),
                "facilities_visited": timeline_data.get("facilities_visited", []),
            },
            "patient_details": {
                "triage_category": timeline_data.get("triage_category"),
                "injury_type": timeline_data.get("injury_type"),
                "nationality": timeline_data.get("nationality"),
                "front": timeline_data.get("front"),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to retrieve patient timeline: {e!s}"
        )


@router.get(
    "/jobs/{job_id}/statistics",
    summary="Get evacuation statistics",
    description="Retrieve aggregated evacuation and timeline statistics for a job",
    responses={
        200: {"description": "Evacuation statistics retrieved successfully"},
        404: {"description": "Job not found", "model": ErrorResponse},
        500: {"description": "Internal server error", "model": ErrorResponse},
    },
)
async def get_evacuation_statistics(
    job_id: str = Path(..., description="Job ID"),
    triage_filter: Optional[str] = Query(None, description="Filter by triage category (T1, T2, T3)"),
    facility_filter: Optional[str] = Query(None, description="Filter by facility"),
    job_service: JobService = Depends(get_job_service),
) -> Dict[str, Any]:
    """
    Get aggregated evacuation statistics for a job.

    Returns:
    - KIA/RTD/Remains rates by triage and facility
    - Average evacuation and transit times
    - Timeline distribution analysis
    - Facility utilization metrics
    """
    try:
        # Get job data
        job = await job_service.get_job(job_id)
        if not job:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Job {job_id} not found")

        # Calculate evacuation statistics
        # This would need to be implemented in the job service
        stats = await job_service.get_evacuation_statistics(job_id, triage_filter, facility_filter)

        return {
            "job_id": job_id,
            "filters": {"triage_category": triage_filter, "facility": facility_filter},
            "outcome_statistics": {
                "total_patients": stats.get("total_patients", 0),
                "kia_count": stats.get("kia_count", 0),
                "rtd_count": stats.get("rtd_count", 0),
                "remains_role4_count": stats.get("remains_role4_count", 0),
                "kia_rate": stats.get("kia_rate", 0.0),
                "rtd_rate": stats.get("rtd_rate", 0.0),
                "remains_rate": stats.get("remains_rate", 0.0),
            },
            "timing_statistics": {
                "average_total_duration_hours": stats.get("avg_total_duration", 0.0),
                "average_evacuation_time_by_facility": stats.get("avg_evacuation_times", {}),
                "average_transit_time_by_route": stats.get("avg_transit_times", {}),
                "duration_distribution": {
                    "under_24h": stats.get("under_24h_count", 0),
                    "24_to_72h": stats.get("24_to_72h_count", 0),
                    "over_72h": stats.get("over_72h_count", 0),
                },
            },
            "triage_breakdown": {
                "T1": {
                    "count": stats.get("t1_count", 0),
                    "kia_rate": stats.get("t1_kia_rate", 0.0),
                    "rtd_rate": stats.get("t1_rtd_rate", 0.0),
                    "avg_duration": stats.get("t1_avg_duration", 0.0),
                },
                "T2": {
                    "count": stats.get("t2_count", 0),
                    "kia_rate": stats.get("t2_kia_rate", 0.0),
                    "rtd_rate": stats.get("t2_rtd_rate", 0.0),
                    "avg_duration": stats.get("t2_avg_duration", 0.0),
                },
                "T3": {
                    "count": stats.get("t3_count", 0),
                    "kia_rate": stats.get("t3_kia_rate", 0.0),
                    "rtd_rate": stats.get("t3_rtd_rate", 0.0),
                    "avg_duration": stats.get("t3_avg_duration", 0.0),
                },
            },
            "facility_metrics": stats.get("facility_metrics", {}),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to retrieve evacuation statistics: {e!s}"
        )


@router.get(
    "/jobs/{job_id}/timeline-summary",
    summary="Get timeline summary",
    description="Get high-level timeline summary for all patients in a job",
    responses={
        200: {"description": "Timeline summary retrieved successfully"},
        404: {"description": "Job not found", "model": ErrorResponse},
        500: {"description": "Internal server error", "model": ErrorResponse},
    },
)
async def get_timeline_summary(
    job_id: str = Path(..., description="Job ID"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of patients to include"),
    offset: int = Query(0, ge=0, description="Number of patients to skip"),
    job_service: JobService = Depends(get_job_service),
) -> Dict[str, Any]:
    """
    Get high-level timeline summary for patients in a job.

    Returns paginated list of patient summaries with key timeline metrics.
    """
    try:
        # Get job data
        job = await job_service.get_job(job_id)
        if not job:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Job {job_id} not found")

        # Get timeline summaries
        summaries = await job_service.get_timeline_summaries(job_id, limit, offset)

        return {
            "job_id": job_id,
            "pagination": {"limit": limit, "offset": offset, "total_patients": summaries.get("total_count", 0)},
            "patients": summaries.get("patients", []),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to retrieve timeline summary: {e!s}"
        )


@router.get(
    "/configuration/evacuation-times",
    summary="Get evacuation time configuration",
    description="Retrieve the current evacuation and transit time configuration",
    responses={
        200: {"description": "Evacuation configuration retrieved successfully"},
        500: {"description": "Internal server error", "model": ErrorResponse},
    },
)
async def get_evacuation_configuration() -> Dict[str, Any]:
    """
    Get the current evacuation and transit time configuration.

    Returns the configuration used for timeline calculations including:
    - Evacuation times by facility and triage
    - Transit times by route and triage
    - KIA/RTD rate modifiers
    - Facility hierarchy
    """
    try:
        from patient_generator.evacuation_time_manager import EvacuationTimeManager

        evacuation_manager = EvacuationTimeManager()
        evacuation_manager.get_config_summary()

        return {
            "evacuation_times": evacuation_manager.config.get("evacuation_times", {}),
            "transit_times": evacuation_manager.config.get("transit_times", {}),
            "kia_rate_modifiers": evacuation_manager.config.get("kia_rate_modifiers", {}),
            "rtd_rate_modifiers": evacuation_manager.config.get("rtd_rate_modifiers", {}),
            "facility_hierarchy": evacuation_manager.get_facility_hierarchy(),
            "triage_categories": evacuation_manager.get_valid_triage_categories(),
            "valid_routes": evacuation_manager.get_valid_routes(),
            "metadata": evacuation_manager.config.get("configuration_metadata", {}),
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve evacuation configuration: {e!s}",
        )
