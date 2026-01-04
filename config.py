"""
Configuration management for the Medical Patients Generator application.
Handles environment variables and application settings.
"""

from functools import lru_cache
import os
from typing import List, Optional


class Settings:
    """Application settings loaded from environment variables."""

    # API Security
    API_KEY: str = os.getenv("API_KEY", "CHANGE_ME_IN_PRODUCTION_DO_NOT_USE_DEFAULT")

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "postgresql://patient_user:patient_pass@localhost:5432/patient_generator"
    )

    # Application
    APP_NAME: str = "Military Medical Exercise Patient Generator"
    VERSION: str = "2.0.0"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")

    # CORS
    CORS_ORIGINS: List[str] = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8000").split(",")

    # File paths
    OUTPUT_DIRECTORY: str = os.getenv("OUTPUT_DIRECTORY", "output")
    TEMP_DIRECTORY: str = os.getenv("TEMP_DIRECTORY", "temp")

    # Generation limits
    MAX_PATIENTS_PER_JOB: int = int(os.getenv("MAX_PATIENTS_PER_JOB", "10000"))
    JOB_TIMEOUT_SECONDS: int = int(os.getenv("JOB_TIMEOUT_SECONDS", "3600"))

    # Encryption
    DEFAULT_ENCRYPTION_PASSWORD: Optional[str] = os.getenv("DEFAULT_ENCRYPTION_PASSWORD")

    # Redis Cache
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "3600"))  # Default 1 hour
    CACHE_ENABLED: bool = os.getenv("CACHE_ENABLED", "True").lower() in ("true", "1", "yes")

    # Database Pool Configuration
    # By default, serverless mode is ON to allow Neon to auto-suspend and save costs
    # Set DB_ALWAYS_ON=true to keep connections warm (disables serverless optimizations)
    DB_ALWAYS_ON: bool = os.getenv("DB_ALWAYS_ON", "False").lower() in ("true", "1", "yes")
    # Pool settings - serverless defaults unless DB_ALWAYS_ON is set
    DB_POOL_MIN: int = int(os.getenv("DB_POOL_MIN", "5" if os.getenv("DB_ALWAYS_ON", "False").lower() in ("true", "1", "yes") else "0"))
    DB_POOL_MAX: int = int(os.getenv("DB_POOL_MAX", "20"))
    DB_POOL_TIMEOUT: float = float(os.getenv("DB_POOL_TIMEOUT", "30"))
    # Connection recycle time - shorter by default to close idle connections faster
    DB_POOL_RECYCLE: int = int(os.getenv("DB_POOL_RECYCLE", "3600" if os.getenv("DB_ALWAYS_ON", "False").lower() in ("true", "1", "yes") else "300"))
    # Idle timeout: close connections after this many seconds of inactivity
    # Default 60s allows Neon to sleep; set to 0 or use DB_ALWAYS_ON to disable
    DB_IDLE_TIMEOUT: int = int(os.getenv("DB_IDLE_TIMEOUT", "0" if os.getenv("DB_ALWAYS_ON", "False").lower() in ("true", "1", "yes") else "60"))
    DB_POOL_PRE_PING: bool = os.getenv("DB_POOL_PRE_PING", "true").lower() == "true"
    DB_QUERY_TIMEOUT: int = int(os.getenv("DB_QUERY_TIMEOUT", "30000"))  # milliseconds

    @classmethod
    def validate(cls) -> None:
        """Validate critical settings."""
        if cls.API_KEY == "CHANGE_ME_IN_PRODUCTION_DO_NOT_USE_DEFAULT":
            import warnings

            warnings.warn(
                "Using default API key. Set API_KEY environment variable for production.", UserWarning, stacklevel=2
            )

        # Ensure directories exist
        os.makedirs(cls.OUTPUT_DIRECTORY, exist_ok=True)
        os.makedirs(cls.TEMP_DIRECTORY, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    settings = Settings()
    settings.validate()
    return settings
