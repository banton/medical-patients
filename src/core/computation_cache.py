"""Computation cache for expensive operations."""

import hashlib
import json
import logging
from typing import Any, Callable, Optional, Union

from src.core.cache import CacheService, get_cache_service

logger = logging.getLogger(__name__)


class ComputationCache:
    """Cache expensive computations with automatic key generation."""

    def __init__(self, cache_service: Optional[CacheService] = None):
        """Initialize computation cache.

        Args:
            cache_service: Optional cache service instance
        """
        self.cache = cache_service or get_cache_service()

    async def get_or_compute(
        self,
        cache_key: str,
        compute_func: Callable,
        ttl: int = 3600,
        force_compute: bool = False,
    ) -> Any:
        """Get from cache or compute and cache the result.

        Args:
            cache_key: Key for caching the result
            compute_func: Async function to compute the value if not cached
            ttl: Time to live in seconds (default: 1 hour)
            force_compute: Force computation even if cached

        Returns:
            Cached or computed result
        """
        if not self.cache:
            # No cache available, compute directly
            logger.debug("Cache not available, computing directly")
            return await compute_func()

        # Try cache first unless forced to compute
        if not force_compute:
            cached = await self.cache.get(cache_key)
            if cached is not None:
                logger.debug(f"Cache hit for key: {cache_key}")
                await self._record_hit(cache_key)
                return cached

        # Compute the result
        logger.debug(f"Cache miss for key: {cache_key}, computing...")
        await self._record_miss(cache_key)

        try:
            result = await compute_func()
        except Exception as e:
            logger.error(f"Computation failed for key {cache_key}: {e}")
            raise

        # Cache the result
        try:
            await self.cache.set(cache_key, result, ttl=ttl)
            logger.debug(f"Cached result for key: {cache_key} with TTL: {ttl}s")
        except Exception as e:
            logger.warning(f"Failed to cache result for key {cache_key}: {e}")
            # Don't fail if caching fails, return the computed result

        return result

    def make_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate a cache key from prefix and arguments.

        Args:
            prefix: Key prefix (e.g., "injury_dist")
            *args: Positional arguments to include in key
            **kwargs: Keyword arguments to include in key

        Returns:
            Generated cache key
        """
        # Combine all arguments
        key_parts = [prefix]

        # Add positional arguments
        for arg in args:
            if isinstance(arg, (dict, list)):
                # For complex types, use a hash
                key_parts.append(self._hash_object(arg))
            else:
                key_parts.append(str(arg))

        # Add keyword arguments (sorted for consistency)
        for k, v in sorted(kwargs.items()):
            if isinstance(v, (dict, list)):
                key_parts.append(f"{k}={self._hash_object(v)}")
            else:
                key_parts.append(f"{k}={v}")

        return ":".join(key_parts)

    def _hash_object(self, obj: Union[dict, list]) -> str:
        """Create a hash of a complex object.

        Args:
            obj: Dictionary or list to hash

        Returns:
            Hash string
        """
        # Convert to JSON with sorted keys for consistency
        json_str = json.dumps(obj, sort_keys=True)
        return hashlib.md5(json_str.encode()).hexdigest()[:8]

    async def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all cache entries matching a pattern.

        Args:
            pattern: Pattern to match (e.g., "injury_dist:*")

        Returns:
            Number of keys invalidated
        """
        if not self.cache:
            return 0

        try:
            count = await self.cache.invalidate_pattern(pattern)
            logger.info(f"Invalidated {count} cache entries matching pattern: {pattern}")
            return count
        except Exception as e:
            logger.error(f"Failed to invalidate pattern {pattern}: {e}")
            return 0

    async def clear_all(self) -> bool:
        """Clear all computation cache entries.

        Returns:
            True if successful
        """
        if not self.cache:
            return False

        try:
            # Clear common computation prefixes
            prefixes = ["injury_dist:", "computation:", "expensive:"]
            total = 0
            for prefix in prefixes:
                total += await self.invalidate_pattern(f"{prefix}*")

            logger.info(f"Cleared {total} computation cache entries")
            return True
        except Exception as e:
            logger.error(f"Failed to clear computation cache: {e}")
            return False

    async def _record_hit(self, cache_key: str) -> None:
        """Record a cache hit for metrics.

        Args:
            cache_key: The key that was hit
        """
        if not self.cache:
            return

        try:
            # Increment hit counter
            metrics_key = "metrics:cache:computation:hits"
            await self.cache.increment(metrics_key)

            # Track per-prefix hits
            prefix = cache_key.split(":")[0]
            prefix_key = f"metrics:cache:computation:{prefix}:hits"
            await self.cache.increment(prefix_key)
        except Exception:
            # Don't fail on metrics recording
            pass

    async def _record_miss(self, cache_key: str) -> None:
        """Record a cache miss for metrics.

        Args:
            cache_key: The key that was missed
        """
        if not self.cache:
            return

        try:
            # Increment miss counter
            metrics_key = "metrics:cache:computation:misses"
            await self.cache.increment(metrics_key)

            # Track per-prefix misses
            prefix = cache_key.split(":")[0]
            prefix_key = f"metrics:cache:computation:{prefix}:misses"
            await self.cache.increment(prefix_key)
        except Exception:
            # Don't fail on metrics recording
            pass

    async def get_hit_rate(self) -> float:
        """Get the cache hit rate.

        Returns:
            Hit rate as a percentage (0-100)
        """
        if not self.cache:
            return 0.0

        try:
            hits = await self.cache.get("metrics:cache:computation:hits") or 0
            misses = await self.cache.get("metrics:cache:computation:misses") or 0

            total = hits + misses
            if total == 0:
                return 0.0

            return (hits / total) * 100
        except Exception as e:
            logger.error(f"Failed to calculate hit rate: {e}")
            return 0.0

