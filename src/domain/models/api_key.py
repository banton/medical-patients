"""
API Key domain model for multi-tenant access control.

This module defines the SQLAlchemy model for API keys that support:
- Individual key limits and quotas
- Usage tracking and analytics
- Demo keys with restricted access
- Expiration and lifecycle management
"""

from datetime import datetime
from typing import Any, Dict
import uuid

from sqlalchemy import JSON, Boolean, Column, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class APIKey(Base):
    """
    API Key model for multi-tenant access control.

    Supports individual usage limits, tracking, and demo access.
    Each key has independent quotas and rate limits.
    """

    __tablename__ = "api_keys"

    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True, index=True)

    # Status flags
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_demo = Column(Boolean, default=False, nullable=False)

    # Usage limits - per request and time-based
    max_patients_per_request = Column(Integer, default=1000, nullable=False)
    max_requests_per_day = Column(Integer, nullable=True)  # None = unlimited
    max_requests_per_minute = Column(Integer, default=60, nullable=False)
    max_requests_per_hour = Column(Integer, default=1000, nullable=False)

    # Usage tracking - updated on each API call
    total_requests = Column(Integer, default=0, nullable=False)
    total_patients_generated = Column(Integer, default=0, nullable=False)
    daily_requests = Column(Integer, default=0, nullable=False)
    last_used_at = Column(DateTime(timezone=True), nullable=True, index=True)
    last_reset_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # Lifecycle metadata
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    key_metadata = Column(JSON, default=dict, nullable=False)

    def __init__(self, **kwargs):
        """Initialize APIKey with minimal required defaults."""
        # Set only the bare minimum defaults needed for methods to work
        # These match the SQLAlchemy column defaults for non-nullable fields
        if "total_requests" not in kwargs:
            kwargs["total_requests"] = 0
        if "total_patients_generated" not in kwargs:
            kwargs["total_patients_generated"] = 0
        if "daily_requests" not in kwargs:
            kwargs["daily_requests"] = 0
        if "key_metadata" not in kwargs:
            kwargs["key_metadata"] = {}

        super().__init__(**kwargs)

    def __repr__(self) -> str:
        """String representation for debugging."""
        key_preview = self.key[:8] + "..." if len(self.key) > 8 else self.key
        return f"<APIKey(name='{self.name}', key='{key_preview}', active={self.is_active})>"

    def is_expired(self) -> bool:
        """Check if the API key has expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at

    def is_usable(self) -> bool:
        """Check if the API key can be used (active and not expired)."""
        return self.is_active and not self.is_expired()

    def check_patient_limit(self, requested_patients: int) -> bool:
        """Check if the requested number of patients is within the key's limit."""
        return requested_patients <= self.max_patients_per_request

    def check_daily_limit(self) -> bool:
        """Check if the key is within its daily request limit."""
        if self.max_requests_per_day is None:
            return True  # Unlimited
        return self.daily_requests < self.max_requests_per_day

    def needs_daily_reset(self) -> bool:
        """Check if daily counters need to be reset."""
        if self.last_reset_at is None:
            return True

        now = datetime.utcnow()
        # Reset if it's a new day (UTC)
        return now.date() > self.last_reset_at.date()

    def reset_daily_counters(self) -> None:
        """Reset daily usage counters."""
        self.daily_requests = 0
        self.last_reset_at = datetime.utcnow()

    def record_usage(self, patients_generated: int) -> None:
        """Record API usage for tracking and limits."""
        self.total_requests += 1
        self.daily_requests += 1
        self.total_patients_generated += patients_generated
        self.last_used_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def get_usage_summary(self) -> Dict[str, Any]:
        """Get a summary of usage statistics."""
        return {
            "total_requests": self.total_requests,
            "total_patients_generated": self.total_patients_generated,
            "daily_requests": self.daily_requests,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "created_at": self.created_at.isoformat(),
            "is_demo": self.is_demo,
            "is_active": self.is_active,
            "is_expired": self.is_expired(),
            "limits": {
                "max_patients_per_request": self.max_patients_per_request,
                "max_requests_per_day": self.max_requests_per_day,
                "max_requests_per_minute": self.max_requests_per_minute,
                "max_requests_per_hour": self.max_requests_per_hour,
            },
        }

    def get_limits_info(self) -> Dict[str, Any]:
        """Get limit information for rate limiting middleware."""
        return {
            "patients_per_request": self.max_patients_per_request,
            "requests_per_day": self.max_requests_per_day,
            "requests_per_minute": self.max_requests_per_minute,
            "requests_per_hour": self.max_requests_per_hour,
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "name": self.name,
            "email": self.email,
            "is_active": self.is_active,
            "is_demo": self.is_demo,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "limits": self.get_limits_info(),
            "usage": {
                "total_requests": self.total_requests,
                "total_patients_generated": self.total_patients_generated,
                "daily_requests": self.daily_requests,
            },
            "metadata": self.key_metadata,
        }


# Demo key configuration - used by security module
DEMO_API_KEY_CONFIG = {
    "key": "DEMO_MILMED_2025_50_PATIENTS",
    "name": "Public Demo Key",
    "email": None,
    "is_demo": True,
    "max_patients_per_request": 50,
    "max_requests_per_day": 100,
    "max_requests_per_minute": 10,
    "max_requests_per_hour": 50,
}
