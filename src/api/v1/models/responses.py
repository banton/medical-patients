"""
Standardized API response models for consistent API contracts.
All endpoints should use these response models for consistent data formats.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from src.domain.models.job import JobStatus


class JobProgressDetails(BaseModel):
    """Detailed progress information for job execution."""

    current_step: str = Field(..., description="Current processing step")
    total_steps: int = Field(..., description="Total number of steps")
    completed_steps: int = Field(..., description="Number of completed steps")
    patients_generated: int = Field(default=0, description="Number of patients generated so far")
    estimated_remaining_time: Optional[int] = Field(None, description="Estimated remaining time in seconds")
    phase_description: Optional[str] = Field(None, description="Human-readable description of current phase")


class JobResponse(BaseModel):
    """Standardized response model for job-related endpoints."""

    job_id: str = Field(..., description="Unique job identifier")
    status: JobStatus = Field(..., description="Current job status")
    created_at: datetime = Field(..., description="Job creation timestamp")
    progress: int = Field(..., ge=0, le=100, description="Job completion percentage")
    config: Dict[str, Any] = Field(..., description="Job configuration")
    completed_at: Optional[datetime] = Field(None, description="Job completion timestamp")
    error: Optional[str] = Field(None, description="Error message if job failed")
    output_files: List[str] = Field(default_factory=list, description="List of generated output files")
    progress_details: Optional[JobProgressDetails] = Field(None, description="Detailed progress information")
    summary: Optional[Dict[str, Any]] = Field(None, description="Job execution summary")

    class Config:
        """Pydantic configuration."""

        json_encoders = {datetime: lambda v: v.isoformat()}


class GenerationResponse(BaseModel):
    """Standardized response model for patient generation endpoint."""

    job_id: str = Field(..., description="Unique job identifier for tracking generation progress")
    status: JobStatus = Field(..., description="Initial job status")
    message: str = Field(..., description="Human-readable status message")
    estimated_duration: Optional[int] = Field(None, description="Estimated completion time in seconds")

    class Config:
        """Pydantic configuration."""

        schema_extra = {
            "example": {
                "job_id": "job_12345",
                "status": "pending",
                "message": "Patient generation job created successfully",
                "estimated_duration": 45,
            }
        }


class ErrorResponse(BaseModel):
    """Standardized error response model for all endpoints."""

    error: str = Field(..., description="Error type or category")
    detail: str = Field(..., description="Detailed error message")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error occurrence timestamp")
    request_id: Optional[str] = Field(None, description="Request tracking identifier")

    class Config:
        """Pydantic configuration."""

        json_encoders = {datetime: lambda v: v.isoformat()}
        schema_extra = {
            "example": {
                "error": "Job Not Found",
                "detail": "Job with ID 'invalid-job' was not found",
                "timestamp": "2024-01-15T10:30:00Z",
                "request_id": "req_12345",
            }
        }


class ConfigurationResponse(BaseModel):
    """Standardized response model for configuration endpoints."""

    id: str = Field(..., description="Configuration identifier")
    name: str = Field(..., description="Configuration name")
    description: Optional[str] = Field(None, description="Configuration description")
    template: Dict[str, Any] = Field(..., description="Configuration template data")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    version: int = Field(default=1, description="Configuration version")
    is_active: bool = Field(default=True, description="Whether configuration is active")

    class Config:
        """Pydantic configuration."""

        json_encoders = {datetime: lambda v: v.isoformat()}


class ConfigurationListResponse(BaseModel):
    """Standardized response model for configuration list endpoint."""

    configurations: List[ConfigurationResponse] = Field(..., description="List of configurations")
    total: int = Field(..., description="Total number of configurations")
    page: int = Field(default=1, description="Current page number")
    per_page: int = Field(default=50, description="Items per page")
    has_next: bool = Field(default=False, description="Whether there are more pages")


class VisualizationDataResponse(BaseModel):
    """Standardized response model for visualization data endpoints."""

    data: Dict[str, Any] = Field(..., description="Visualization data")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Data metadata")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="Data generation timestamp")
    cache_expires_at: Optional[datetime] = Field(None, description="Cache expiration timestamp")

    class Config:
        """Pydantic configuration."""

        json_encoders = {datetime: lambda v: v.isoformat()}


class HealthCheckResponse(BaseModel):
    """Standardized response model for health check endpoints."""

    status: str = Field(..., description="Overall health status")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Health check timestamp")
    version: str = Field(..., description="Application version")
    services: Dict[str, str] = Field(default_factory=dict, description="Service health status")
    uptime_seconds: int = Field(..., description="Application uptime in seconds")

    class Config:
        """Pydantic configuration."""

        json_encoders = {datetime: lambda v: v.isoformat()}


class ValidationResponse(BaseModel):
    """Standardized response model for validation endpoints."""

    is_valid: bool = Field(..., description="Whether the input is valid")
    errors: List[str] = Field(default_factory=list, description="List of validation errors")
    warnings: List[str] = Field(default_factory=list, description="List of validation warnings")
    validated_data: Optional[Dict[str, Any]] = Field(None, description="Validated and normalized data")

    class Config:
        """Pydantic configuration."""

        schema_extra = {
            "example": {
                "is_valid": False,
                "errors": ["Invalid nationality code: XX"],
                "warnings": ["Large patient count may take significant time"],
                "validated_data": None,
            }
        }


class DownloadResponse(BaseModel):
    """Standardized response model for download endpoints (when not returning file directly)."""

    download_url: str = Field(..., description="URL to download the file")
    filename: str = Field(..., description="Suggested filename")
    file_size: int = Field(..., description="File size in bytes")
    content_type: str = Field(..., description="MIME content type")
    expires_at: datetime = Field(..., description="Download URL expiration time")

    class Config:
        """Pydantic configuration."""

        json_encoders = {datetime: lambda v: v.isoformat()}


class DeleteResponse(BaseModel):
    """Standardized response model for DELETE operations."""

    success: bool = Field(..., description="Whether the deletion was successful")
    message: str = Field(..., description="Human-readable message about the deletion")
    deleted_id: str = Field(..., description="ID of the deleted resource")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of the deletion operation")

    class Config:
        """Pydantic configuration."""

        json_encoders = {datetime: lambda v: v.isoformat()}
        schema_extra = {
            "example": {
                "success": True,
                "message": "Resource deleted successfully",
                "deleted_id": "config_12345",
                "timestamp": "2024-01-15T10:30:00Z",
            }
        }


class StreamingPatientResponse(BaseModel):
    """Response model for streaming patient generation endpoints.

    Note: This is used for OpenAPI documentation only. The actual response
    is a streaming JSON response.
    """

    patients: List[Dict[str, Any]] = Field(..., description="Array of patient data objects streamed incrementally")
    total_patients: int = Field(..., description="Total number of patients generated")
    error: Optional[str] = Field(None, description="Error message if generation failed")
    patients_generated: Optional[int] = Field(
        None, description="Number of patients generated before error (only present on error)"
    )

    class Config:
        """Pydantic configuration."""

        schema_extra = {
            "example": {
                "patients": [
                    {"patient_id": "NATO-BEL-12345", "name": "John Doe", "injury_type": "Battle Injury", "timeline": []}
                ],
                "total_patients": 100,
            }
        }
