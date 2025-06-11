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
