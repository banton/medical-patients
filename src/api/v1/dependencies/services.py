"""
Service dependencies for API endpoints.
"""

from functools import lru_cache

from src.domain.repositories.job_repository import JobRepositoryInterface
from src.domain.services.job_service import JobService
from src.domain.services.patient_generation_service import AsyncPatientGenerationService
from src.infrastructure.database_job_repository import DatabaseJobRepository
from src.infrastructure.database_pool import get_pool


@lru_cache
def get_job_repository() -> JobRepositoryInterface:
    """Get the job repository singleton."""
    # Use database-backed repository for persistent job storage
    db_pool = get_pool()
    return DatabaseJobRepository(db_pool)


def get_job_service() -> JobService:
    """Get job service dependency."""
    repository = get_job_repository()
    return JobService(repository)


@lru_cache
def get_patient_generation_service() -> AsyncPatientGenerationService:
    """Get patient generation service dependency."""
    return AsyncPatientGenerationService()
