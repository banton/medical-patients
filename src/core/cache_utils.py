"""Cache utilities and decorators for the application.

This module provides caching decorators and specific caching functions for:
- API key limits (TTL: 5 minutes)
- Active job status (TTL: job duration)
- Configuration templates (TTL: 1 hour)
"""

import asyncio
import functools
import hashlib
import json
import logging
from typing import Any, Callable, Dict, Optional

from config import get_settings
from src.core.cache import get_cache_service
from src.domain.models.job import Job, JobStatus

logger = logging.getLogger(__name__)
settings = get_settings()

# Cache TTL constants
API_KEY_LIMITS_TTL = 300  # 5 minutes
CONFIGURATION_TTL = 3600  # 1 hour
JOB_STATUS_TTL = 300  # Default 5 minutes for active jobs


def cache_key_generator(*args, **kwargs) -> str:
    """Generate a cache key from function arguments.

    Args:
        *args: Positional arguments
        **kwargs: Keyword arguments

    Returns:
        SHA256 hash of the serialized arguments
    """
    # Create a stable string representation of arguments
    key_data = {"args": args, "kwargs": kwargs}
    key_string = json.dumps(key_data, sort_keys=True)
    return hashlib.sha256(key_string.encode()).hexdigest()


def cached(key_prefix: str, ttl: Optional[int] = None, condition: Optional[Callable[..., bool]] = None):
    """Decorator for caching function results.

    Args:
        key_prefix: Prefix for the cache key
        ttl: Time-to-live in seconds (uses default if not specified)
        condition: Optional function to determine if result should be cached

    Returns:
        Decorated function with caching
    """

    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Skip caching if disabled
            if not settings.CACHE_ENABLED:
                return await func(*args, **kwargs)

            cache_service = get_cache_service()
            if not cache_service:
                return await func(*args, **kwargs)

            # Generate cache key
            key_suffix = cache_key_generator(*args, **kwargs)
            cache_key = f"{key_prefix}:{key_suffix}"

            # Try to get from cache
            cached_value = await cache_service.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit for key: {cache_key}")
                return cached_value

            # Execute function
            result = await func(*args, **kwargs)

            # Cache result if condition is met
            if condition is None or condition(result):
                await cache_service.set(cache_key, result, ttl)
                logger.debug(f"Cached result for key: {cache_key}")

            return result

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # For synchronous functions, we can't use async cache
            # Just execute the function normally
            return func(*args, **kwargs)

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def invalidate_cache_pattern(pattern: str):
    """Decorator to invalidate cache keys matching a pattern after function execution.

    Args:
        pattern: Redis key pattern to invalidate (e.g., "config:*")

    Returns:
        Decorated function that invalidates cache after execution
    """

    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)

            # Invalidate cache if enabled
            if settings.CACHE_ENABLED:
                cache_service = get_cache_service()
                if cache_service:
                    deleted = await cache_service.invalidate_pattern(pattern)
                    logger.debug(f"Invalidated {deleted} cache keys matching pattern: {pattern}")

            return result

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # For synchronous functions, we can't invalidate cache
            # Just execute the function normally
            return func(*args, **kwargs)

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def get_api_key_hash(api_key: str) -> str:
    """Generate a secure hash for an API key."""
    return hashlib.sha256(api_key.encode()).hexdigest()[:16]


async def cache_api_key_limits(api_key: str, limits_data: Dict[str, Any]) -> None:
    """
    Cache API key limits and usage data.

    Args:
        api_key: The API key (will be hashed)
        limits_data: Dictionary containing limit information
    """
    cache = get_cache_service()
    if not cache:
        return

    key_hash = get_api_key_hash(api_key)
    cache_key = f"apikey:{key_hash}:limits"

    try:
        await cache.set(cache_key, limits_data, ttl=API_KEY_LIMITS_TTL)
        logger.debug(f"Cached API key limits for hash {key_hash}")
    except Exception as e:
        logger.error(f"Failed to cache API key limits: {e}")


async def get_cached_api_key_limits(api_key: str) -> Optional[Dict[str, Any]]:
    """
    Get cached API key limits.

    Args:
        api_key: The API key (will be hashed)

    Returns:
        Cached limits data or None if not found
    """
    cache = get_cache_service()
    if not cache:
        return None

    key_hash = get_api_key_hash(api_key)
    cache_key = f"apikey:{key_hash}:limits"

    try:
        data = await cache.get(cache_key)
        if data:
            logger.debug(f"Cache hit for API key limits hash {key_hash}")
        return data
    except Exception as e:
        logger.error(f"Failed to get cached API key limits: {e}")
        return None


async def cache_job_status(job: Job) -> None:
    """
    Cache job status information.

    Args:
        job: The job object to cache
    """
    cache = get_cache_service()
    if not cache:
        return

    cache_key = f"job:{job.job_id}:status"

    # Determine TTL based on job status
    if job.status in [JobStatus.PENDING, JobStatus.RUNNING]:
        ttl = JOB_STATUS_TTL
    elif job.status == JobStatus.COMPLETED:
        ttl = 3600  # 1 hour for completed jobs
    else:
        ttl = 1800  # 30 minutes for failed/cancelled jobs

    job_data = {
        "id": job.job_id,
        "status": job.status.value,
        "progress": job.progress,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        "error": job.error,
        "summary": job.summary,
        "progress_details": {
            "current_phase": job.progress_details.current_phase,
            "phase_description": job.progress_details.phase_description,
            "phase_progress": job.progress_details.phase_progress,
            "total_patients": job.progress_details.total_patients,
            "processed_patients": job.progress_details.processed_patients,
            "time_estimates": job.progress_details.time_estimates,
        }
        if job.progress_details
        else None,
    }

    try:
        await cache.set(cache_key, job_data, ttl=ttl)
        logger.debug(f"Cached job status for {job.job_id} with TTL {ttl}s")
    except Exception as e:
        logger.error(f"Failed to cache job status: {e}")


async def get_cached_job_status(job_id: str) -> Optional[Dict[str, Any]]:
    """
    Get cached job status.

    Args:
        job_id: The job ID

    Returns:
        Cached job data or None if not found
    """
    cache = get_cache_service()
    if not cache:
        return None

    cache_key = f"job:{job_id}:status"

    try:
        data = await cache.get(cache_key)
        if data:
            logger.debug(f"Cache hit for job status {job_id}")
        return data
    except Exception as e:
        logger.error(f"Failed to get cached job status: {e}")
        return None


async def invalidate_job_cache(job_id: str) -> None:
    """
    Invalidate cached job status.

    Args:
        job_id: The job ID to invalidate
    """
    cache = get_cache_service()
    if not cache:
        return

    cache_key = f"job:{job_id}:status"

    try:
        await cache.delete(cache_key)
        logger.debug(f"Invalidated job cache for {job_id}")
    except Exception as e:
        logger.error(f"Failed to invalidate job cache: {e}")


async def cache_configuration_template(config_id: str, config_data: Dict[str, Any]) -> None:
    """
    Cache configuration template data.

    Args:
        config_id: The configuration ID
        config_data: The configuration data to cache
    """
    cache = get_cache_service()
    if not cache:
        return

    cache_key = f"config:{config_id}"

    try:
        await cache.set(cache_key, config_data, ttl=CONFIGURATION_TTL)
        logger.debug(f"Cached configuration template {config_id}")
    except Exception as e:
        logger.error(f"Failed to cache configuration template: {e}")


async def get_cached_configuration(config_id: str) -> Optional[Dict[str, Any]]:
    """
    Get cached configuration template.

    Args:
        config_id: The configuration ID

    Returns:
        Cached configuration data or None if not found
    """
    cache = get_cache_service()
    if not cache:
        return None

    cache_key = f"config:{config_id}"

    try:
        data = await cache.get(cache_key)
        if data:
            logger.debug(f"Cache hit for configuration {config_id}")
        return data
    except Exception as e:
        logger.error(f"Failed to get cached configuration: {e}")
        return None


async def invalidate_configuration_cache(config_id: str) -> None:
    """
    Invalidate cached configuration template and related computation caches.

    Args:
        config_id: The configuration ID to invalidate
    """
    cache = get_cache_service()
    if not cache:
        return

    cache_key = f"config:{config_id}"

    try:
        # Delete the configuration cache
        await cache.delete(cache_key)
        logger.debug(f"Invalidated configuration cache for {config_id}")
        
        # Also invalidate any computation caches that might depend on this config
        # Using v2 suffix to match the cache warmup service pattern
        cache_key_v2 = f"config:{config_id}:v2"
        await cache.delete(cache_key_v2)
        
        # Invalidate related computation caches
        deleted = await cache.invalidate_pattern(f"computation:*:{config_id}:*")
        if deleted > 0:
            logger.debug(f"Invalidated {deleted} computation cache entries for config {config_id}")
            
    except Exception as e:
        logger.error(f"Failed to invalidate configuration cache: {e}")


async def get_cache_stats() -> Dict[str, Any]:
    """
    Get cache statistics for monitoring.

    Returns:
        Dictionary with cache stats or empty dict if cache unavailable
    """
    cache = get_cache_service()
    if not cache:
        return {"available": False}

    try:
        # Check Redis health
        healthy = await cache.health_check()

        return {
            "available": True,
            "healthy": healthy,
            "ttls": {
                "api_key_limits": API_KEY_LIMITS_TTL,
                "configuration": CONFIGURATION_TTL,
                "job_status": JOB_STATUS_TTL,
            },
        }
    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}")
        return {"available": False, "error": str(e)}
