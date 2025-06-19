"""
Enhanced security module with API key management.

This module provides comprehensive API key validation, context objects,
and legacy compatibility with the existing single API key system.
"""

from dataclasses import dataclass
from datetime import datetime
import os
from typing import Any, Dict, Optional

from fastapi import Depends, Header, HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session as SQLAlchemySession, sessionmaker

from src.core.cache_utils import cache_api_key_limits
from src.domain.models.api_key import DEMO_API_KEY_CONFIG, APIKey
from src.domain.repositories.api_key_repository import APIKeyRepository

# Legacy single API key support (backward compatibility)
LEGACY_API_KEY = os.getenv("API_KEY", "CHANGE_ME_IN_PRODUCTION_DO_NOT_USE_DEFAULT")

# Public demo key - hardcoded for easy access
DEMO_API_KEY: str = str(DEMO_API_KEY_CONFIG["key"])

# Create SQLAlchemy session factory
# Note: This should ideally come from a centralized config, but for backward compatibility
# we need to handle cases where the module is imported before environment is fully set up
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL:
    engine = create_engine(DATABASE_URL.replace("+asyncpg", ""))
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
else:
    # This will only be used if DATABASE_URL is not set at module import time
    # The actual database operations will fail with a proper error message
    SessionLocal = None


def get_sqlalchemy_session():
    """Get SQLAlchemy session for API key operations."""
    if SessionLocal is None:
        raise HTTPException(
            status_code=503,
            detail="Database not configured. Service temporarily unavailable.",
            headers={"X-Error-Type": "database_configuration"}
        )
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@dataclass
class APIKeyContext:
    """
    Rich context object for API key validation and enforcement.

    Provides limit checking, usage tracking, and metadata access
    for API key-based operations.
    """

    api_key: APIKey
    is_demo: bool = False
    is_legacy: bool = False
    rate_limit_remaining: Optional[int] = None
    rate_limit_reset: Optional[datetime] = None

    def check_patient_limit(self, requested: int) -> None:
        """
        Verify request doesn't exceed patient generation limit.

        Args:
            requested: Number of patients requested

        Raises:
            HTTPException: If limit exceeded
        """
        if not self.api_key.check_patient_limit(requested):
            raise HTTPException(
                status_code=400,
                detail=f"Requested {requested} patients exceeds limit of {self.api_key.max_patients_per_request}",
                headers={
                    "X-Limit-Type": "patients_per_request",
                    "X-Limit-Value": str(self.api_key.max_patients_per_request),
                    "X-Requested": str(requested),
                },
            )

    def check_daily_limit(self) -> None:
        """
        Verify daily request limit not exceeded.

        Raises:
            HTTPException: If daily limit exceeded
        """
        if not self.api_key.check_daily_limit():
            raise HTTPException(
                status_code=429,
                detail=f"Daily request limit exceeded ({self.api_key.max_requests_per_day})",
                headers={
                    "X-Limit-Type": "requests_per_day",
                    "X-Limit-Value": str(self.api_key.max_requests_per_day),
                    "X-Current-Usage": str(self.api_key.daily_requests),
                    "Retry-After": str(self._seconds_until_daily_reset()),
                },
            )

    def check_usability(self) -> None:
        """
        Verify API key is active and not expired.

        Raises:
            HTTPException: If key is not usable
        """
        if not self.api_key.is_usable():
            if self.api_key.is_expired():
                raise HTTPException(status_code=401, detail="API key has expired", headers={"X-Key-Status": "expired"})
            raise HTTPException(status_code=401, detail="API key is inactive", headers={"X-Key-Status": "inactive"})

    def get_limits_info(self) -> Dict[str, Any]:
        """Get current limits and usage for response headers."""
        return {
            "patients_per_request": self.api_key.max_patients_per_request,
            "requests_per_day": self.api_key.max_requests_per_day,
            "requests_per_minute": self.api_key.max_requests_per_minute,
            "requests_per_hour": self.api_key.max_requests_per_hour,
            "daily_usage": self.api_key.daily_requests,
            "total_usage": self.api_key.total_requests,
        }

    def get_response_headers(self) -> Dict[str, str]:
        """Get headers to include in API responses."""
        headers = {
            "X-API-Key-Type": "demo" if self.is_demo else "live",
            "X-Patient-Limit": str(self.api_key.max_patients_per_request),
            "X-Daily-Limit": str(self.api_key.max_requests_per_day or "unlimited"),
            "X-Daily-Usage": str(self.api_key.daily_requests),
        }

        if self.rate_limit_remaining is not None:
            headers["X-RateLimit-Remaining"] = str(self.rate_limit_remaining)

        if self.rate_limit_reset:
            headers["X-RateLimit-Reset"] = str(int(self.rate_limit_reset.timestamp()))

        return headers

    def _seconds_until_daily_reset(self) -> int:
        """Calculate seconds until daily counters reset."""
        now = datetime.utcnow()
        tomorrow = now.replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = tomorrow.replace(day=tomorrow.day + 1)
        return int((tomorrow - now).total_seconds())


def create_legacy_api_key() -> APIKey:
    """
    Create a virtual APIKey for legacy single-key mode.

    Returns:
        APIKey instance representing the legacy key
    """
    return APIKey(
        key=LEGACY_API_KEY,
        name="Legacy API Key",
        email=None,
        is_active=True,
        is_demo=False,
        max_patients_per_request=10000,  # High limit for legacy
        max_requests_per_day=None,  # Unlimited
        max_requests_per_minute=1000,  # High limit
        max_requests_per_hour=10000,  # High limit
        total_requests=0,
        total_patients_generated=0,
        daily_requests=0,
        key_metadata={"legacy_mode": True},
    )


def create_demo_api_key() -> APIKey:
    """
    Create a virtual APIKey for the demo key.

    Returns:
        APIKey instance representing the demo key
    """
    return APIKey(
        key=DEMO_API_KEY,
        name=DEMO_API_KEY_CONFIG["name"],
        email=DEMO_API_KEY_CONFIG["email"],
        is_active=True,
        is_demo=True,
        max_patients_per_request=DEMO_API_KEY_CONFIG["max_patients_per_request"],
        max_requests_per_day=DEMO_API_KEY_CONFIG["max_requests_per_day"],
        max_requests_per_minute=DEMO_API_KEY_CONFIG["max_requests_per_minute"],
        max_requests_per_hour=DEMO_API_KEY_CONFIG["max_requests_per_hour"],
        total_requests=0,
        total_patients_generated=0,
        daily_requests=0,
        key_metadata={"public_demo": True},
    )


async def verify_api_key_context(
    api_key: Optional[str] = Header(None, alias="X-API-Key"), db: SQLAlchemySession = Depends(get_sqlalchemy_session)
) -> APIKeyContext:
    """
    Enhanced API key verification with context and legacy support.

    Args:
        api_key: API key from X-API-Key header
        db: Database session

    Returns:
        APIKeyContext with validated key and metadata

    Raises:
        HTTPException: If key is invalid, expired, or inactive
    """
    # Check if API key is provided
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="Missing API Key",
            headers={"X-Key-Status": "missing", "WWW-Authenticate": "ApiKey"}
        )

    # Try to get cached limits first
    # TODO: Implement cached limits usage in future optimization
    # cached_limits = await get_cached_api_key_limits(api_key)

    try:
        repo = APIKeyRepository(db)
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Database service temporarily unavailable",
            headers={"X-Error-Type": "database_error"}
        )

    # Check for demo key first (most common case)
    if api_key == DEMO_API_KEY:
        try:
            # For demo key, try to get from database or create virtual
            demo_key = repo.get_by_key(DEMO_API_KEY)
            if not demo_key:
                # Create virtual demo key for immediate use
                # In production, this should be pre-created in the database
                demo_key = create_demo_api_key()

            context = APIKeyContext(api_key=demo_key, is_demo=True, is_legacy=False)

            # Check if demo key is usable
            context.check_usability()

            # Cache the limits for future requests
            await cache_api_key_limits(api_key, context.get_limits_info())

            return context
        except HTTPException:
            # Re-raise HTTP exceptions as-is
            raise
        except Exception:
            raise HTTPException(
                status_code=500,
                detail="Error processing demo API key",
                headers={"X-Error-Type": "demo_key_error"}
            )

    # Check for legacy API key (backward compatibility)
    if api_key == LEGACY_API_KEY:
        legacy_key = create_legacy_api_key()
        context = APIKeyContext(api_key=legacy_key, is_demo=False, is_legacy=True)

        # Cache the limits for future requests
        await cache_api_key_limits(api_key, context.get_limits_info())

        return context

    # Look up key in database
    try:
        key_record = repo.get_active_key(api_key)
        if not key_record:
            raise HTTPException(status_code=401, detail="Invalid or inactive API key", headers={"X-Key-Status": "invalid"})

        # Create context with database key
        context = APIKeyContext(api_key=key_record, is_demo=key_record.is_demo, is_legacy=False)

        # Verify key is usable
        context.check_usability()

        # Cache the limits for future requests
        await cache_api_key_limits(api_key, context.get_limits_info())

        return context
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Database lookup failed. Service temporarily unavailable.",
            headers={"X-Error-Type": "database_lookup_error"}
        )


async def verify_api_key_optional(
    api_key: Optional[str] = Header(None, alias="X-API-Key"), db: SQLAlchemySession = Depends(get_sqlalchemy_session)
) -> Optional[APIKeyContext]:
    """
    Optional API key verification for endpoints that support both authenticated and unauthenticated access.

    Args:
        api_key: Optional API key from X-API-Key header
        db: Database session

    Returns:
        APIKeyContext if key provided and valid, None otherwise
    """
    if not api_key:
        return None

    try:
        return await verify_api_key(api_key, db)
    except HTTPException:
        # For optional verification, invalid keys are treated as no key
        return None


# Legacy function for backward compatibility
async def verify_api_key_legacy(api_key: str = Header(..., alias="X-API-Key")) -> str:
    """
    Legacy API key verification function.

    This maintains backward compatibility with the existing codebase
    while the transition to the new system occurs.

    Args:
        api_key: API key from header

    Returns:
        The API key string if valid

    Raises:
        HTTPException: If key is invalid
    """
    # Accept demo key, legacy key, or any database key
    if api_key in [DEMO_API_KEY, LEGACY_API_KEY]:
        return api_key

    # For now, during transition, accept any non-empty key
    # This will be tightened once all endpoints are migrated
    if api_key and len(api_key) > 10:
        return api_key

    raise HTTPException(
        status_code=401,
        detail="Invalid API key",
        headers={"X-Key-Status": "invalid"}
    )


def get_api_key_info(context: APIKeyContext) -> Dict[str, Any]:
    """
    Get API key information for logging and monitoring.

    Args:
        context: API key context

    Returns:
        Dictionary with key information (no sensitive data)
    """
    return {
        "key_id": str(context.api_key.id) if hasattr(context.api_key, "id") and context.api_key.id else "virtual",
        "key_name": context.api_key.name,
        "is_demo": context.is_demo,
        "is_legacy": context.is_legacy,
        "limits": context.get_limits_info(),
        "last_used": context.api_key.last_used_at.isoformat() if context.api_key.last_used_at else None,
    }


# Backward compatibility: Provide the old verify_api_key signature
# that returns a string instead of APIKeyContext
async def verify_api_key(
    api_key: Optional[str] = Header(None, alias="X-API-Key"), db: SQLAlchemySession = Depends(get_sqlalchemy_session)
) -> str:
    """
    Backward-compatible API key verification that returns a string.

    This wrapper maintains compatibility with existing code that expects
    verify_api_key to return a string instead of APIKeyContext.
    """
    # Call the enhanced function that returns context
    context = await verify_api_key_context(api_key, db)
    # Return the API key string for backward compatibility
    return context.api_key.key


# Export the enhanced version for new code that needs the full context
verify_api_key_enhanced = verify_api_key_context
