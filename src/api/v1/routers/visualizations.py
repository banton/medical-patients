"""
API router for visualization data.
"""
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, Query
import random

from patient_generator.visualization_data import transform_job_data_for_visualization
from src.domain.services.job_service import JobService
from src.domain.models.job import JobStatus
from src.api.v1.dependencies.services import get_job_service
from src.core.security import verify_api_key


# Router configuration
router = APIRouter(
    prefix="/api/visualizations",
    tags=["visualizations"],
    dependencies=[Depends(verify_api_key)]
)


@router.get("/dashboard-data")
async def get_dashboard_data(
    job_id: Optional[str] = Query(None),
    job_service: JobService = Depends(get_job_service)
) -> Dict[str, Any]:
    """Get data for the visualization dashboard."""
    
    # Get all jobs
    jobs = await job_service.list_jobs()
    completed_jobs = [j for j in jobs if j.status == JobStatus.COMPLETED]
    
    # If specific job requested
    target_job_data = None
    if job_id:
        try:
            job = await job_service.get_job(job_id)
            if job.status == JobStatus.COMPLETED and job.summary:
                target_job_data = transform_job_data_for_visualization({
                    "config": job.config,
                    "summary": job.summary,
                    "bundles": []  # Bundles not stored in job
                })
        except:
            pass
    
    # If no specific job or job not found, use most recent
    if not target_job_data and completed_jobs:
        recent_job = max(completed_jobs, key=lambda j: j.created_at)
        if recent_job.summary:
            target_job_data = transform_job_data_for_visualization({
                "config": recent_job.config,
                "summary": recent_job.summary,
                "bundles": []
            })
    
    # Return data or empty structure
    if target_job_data:
        return target_job_data
    
    # Return empty dashboard data
    return {
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
        "facility_load": []
    }


@router.get("/patient-detail/{patient_id}")
async def get_patient_detail(
    patient_id: str,
    job_id: Optional[str] = Query(None),
    job_service: JobService = Depends(get_job_service)
) -> Dict[str, Any]:
    """Get detailed data for a specific patient."""
    
    # This would need to load patient data from files
    # For now, return mock data
    return {
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
                "treatments": ["First aid", "Stabilization"]
            }
        ],
        "final_status": "Evacuated"
    }


@router.get("/sample-patients")
async def get_sample_patients(
    job_id: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=100),
    job_service: JobService = Depends(get_job_service)
) -> List[Dict[str, Any]]:
    """Get a sample of patients from a job."""
    
    # This would need to load patient data from files
    # For now, return mock data
    sample_patients = []
    
    for i in range(limit):
        sample_patients.append({
            "id": f"patient_{i}",
            "name": f"Patient {i}",
            "nationality": random.choice(["USA", "POL", "EST", "FIN"]),
            "age": random.randint(18, 45),
            "gender": random.choice(["male", "female"]),
            "injury_type": random.choice(["Battle Injury", "Disease", "Non-Battle Injury"]),
            "final_status": random.choice(["RTD", "KIA", "Evacuated"])
        })
    
    return sample_patients