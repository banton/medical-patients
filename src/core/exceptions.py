"""
Custom exceptions for the application.
"""

from typing import Any, Dict, Optional


class PatientGeneratorException(Exception):
    """Base exception for the patient generator application."""


class ConfigurationNotFoundError(PatientGeneratorException):
    """Raised when a configuration template is not found."""

    def __init__(self, config_id: str):
        self.config_id = config_id
        super().__init__(f"Configuration template not found: {config_id}")


class JobNotFoundError(PatientGeneratorException):
    """Raised when a job is not found."""

    def __init__(self, job_id: str):
        self.job_id = job_id
        super().__init__(f"Job not found: {job_id}")


class InvalidConfigurationError(PatientGeneratorException):
    """Raised when a configuration is invalid."""

    def __init__(self, message: str, errors: Optional[Dict[str, Any]] = None):
        self.errors = errors
        super().__init__(message)


class GenerationError(PatientGeneratorException):
    """Raised when patient generation fails."""


class StorageError(PatientGeneratorException):
    """Raised when file storage operations fail."""


class InvalidOperationError(PatientGeneratorException):
    """Raised when an invalid operation is attempted."""


class ResourceLimitExceeded(PatientGeneratorException):
    """Raised when a job exceeds resource limits."""


class InvalidInputError(PatientGeneratorException):
    """Raised when invalid input is provided to an API endpoint."""

    def __init__(self, detail: str):
        self.status_code = 422
        self.detail = detail
        super().__init__(detail)


class NotFoundError(PatientGeneratorException):
    """Raised when a requested resource is not found."""

    def __init__(self, detail: str):
        self.status_code = 404
        self.detail = detail
        super().__init__(detail)


class UnauthorizedError(PatientGeneratorException):
    """Raised when authentication fails or is missing."""

    def __init__(self, detail: str):
        self.status_code = 401
        self.detail = detail
        super().__init__(detail)
