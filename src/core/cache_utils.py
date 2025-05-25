"""Cache utilities and decorators for the application."""

import functools
import hashlib
import json
import logging
from typing import Callable, Optional

from config import get_settings
from src.core.cache import get_cache_service

logger = logging.getLogger(__name__)
settings = get_settings()


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


import asyncio
