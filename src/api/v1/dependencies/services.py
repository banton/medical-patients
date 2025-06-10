"""
Service dependencies for API endpoints.
"""

from functools import lru_cache

from src.domain.repositories.job_repository import InMemoryJobRepository
from src.domain.services.job_service import JobService
from src.domain.services.patient_generation_service import AsyncPatientGenerationService


@lru_cache
def get_job_repository() -> InMemoryJobRepository:
    """Get the job repository singleton."""
    return InMemoryJobRepository()


def get_job_service() -> JobService:
    """Get job service dependency."""
    repository = get_job_repository()
    return JobService(repository)


@lru_cache
def get_patient_generation_service() -> AsyncPatientGenerationService:
    """Get patient generation service dependency."""
    return AsyncPatientGenerationService()
