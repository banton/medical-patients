"""
Domain models for job management.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class JobStatus(str, Enum):
    """Job status enumeration."""

    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class JobProgressDetails:
    """Details about job progress."""

    current_phase: str
    phase_description: str
    phase_progress: int
    total_patients: Optional[int] = None
    processed_patients: Optional[int] = None
    time_estimates: Optional[Dict[str, float]] = None


@dataclass
class Job:
    """Domain model for a generation job."""

    job_id: str
    status: JobStatus
    created_at: datetime
    config: Dict[str, Any]
    progress: int = 0
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    result_files: List[str] = field(default_factory=list)
    output_directory: Optional[str] = None
    progress_details: Optional[JobProgressDetails] = None
    summary: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert job to dictionary representation."""
        data: Dict[str, Any] = {
            "job_id": self.job_id,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "progress": self.progress,
            "config": self.config,
        }

        if self.completed_at:
            data["completed_at"] = self.completed_at.isoformat()

        if self.error:
            data["error"] = self.error

        if self.result_files:
            data["output_files"] = self.result_files

        if self.output_directory:
            data["output_directory"] = self.output_directory

        if self.progress_details:
            data["progress_details"] = {
                "current_phase": self.progress_details.current_phase,
                "phase_description": self.progress_details.phase_description,
                "phase_progress": self.progress_details.phase_progress,
                "total_patients": self.progress_details.total_patients,
                "processed_patients": self.progress_details.processed_patients,
                "time_estimates": self.progress_details.time_estimates,
            }

        if self.summary:
            data["summary"] = self.summary

        return data
