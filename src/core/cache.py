"""Cache service for Redis integration.

This module provides a centralized caching layer using Redis for improved performance.
"""

from contextlib import asynccontextmanager
import json
import logging
from typing import Any, Optional

import redis.asyncio as redis
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)


class CacheService:
    """Service for managing Redis cache operations."""

    def __init__(self, redis_url: str, default_ttl: int = 3600):
        """Initialize the cache service.

        Args:
            redis_url: Redis connection URL (e.g., redis://localhost:6379/0)
            default_ttl: Default time-to-live in seconds for cached items
        """
        self.redis_url = redis_url
        self.default_ttl = default_ttl
        self._pool: Optional[redis.ConnectionPool] = None

    async def initialize(self) -> None:
        """Initialize the Redis connection pool."""
        try:
            # Redis-py 5.0+ automatically handles SSL for rediss:// URLs
            self._pool = redis.ConnectionPool.from_url(self.redis_url, decode_responses=True, max_connections=50)
            # Test connection
            async with self._get_client() as client:
                await client.ping()
            logger.info("Redis cache initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Redis cache: {e}")
            raise

    async def close(self) -> None:
        """Close the Redis connection pool."""
        if self._pool:
            await self._pool.disconnect()
            logger.info("Redis cache connection closed")

    @asynccontextmanager
    async def _get_client(self):
        """Get a Redis client from the pool."""
        if not self._pool:
            msg = "Cache service not initialized"
            raise RuntimeError(msg)

        client = redis.Redis(connection_pool=self._pool)
        try:
            yield client
        finally:
            await client.close()

    async def get(self, key: str) -> Optional[Any]:
        """Get a value from the cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        try:
            async with self._get_client() as client:
                value = await client.get(key)
                if value is not None:
                    # Try to deserialize JSON, otherwise return as string
                    try:
                        return json.loads(value)
                    except json.JSONDecodeError:
                        return value
                return None
        except RedisError as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set a value in the cache.

        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized if not string)
            ttl: Time-to-live in seconds (uses default if not specified)

        Returns:
            True if successful, False otherwise
        """
        try:
            async with self._get_client() as client:
                # Serialize non-string values as JSON
                if not isinstance(value, str):
                    value = json.dumps(value)

                ttl = ttl or self.default_ttl
                await client.setex(key, ttl, value)
                return True
        except RedisError as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete a key from the cache.

        Args:
            key: Cache key to delete

        Returns:
            True if key was deleted, False otherwise
        """
        try:
            async with self._get_client() as client:
                result = await client.delete(key)
                return result > 0
        except RedisError as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False

    async def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching a pattern.

        Args:
            pattern: Redis key pattern (e.g., "user:*")

        Returns:
            Number of keys deleted
        """
        try:
            async with self._get_client() as client:
                # Use SCAN to avoid blocking on large datasets
                cursor = 0
                deleted = 0

                while True:
                    cursor, keys = await client.scan(cursor, match=pattern, count=100)

                    if keys:
                        deleted += await client.delete(*keys)

                    if cursor == 0:
                        break

                logger.info(f"Invalidated {deleted} keys matching pattern: {pattern}")
                return deleted
        except RedisError as e:
            logger.error(f"Cache invalidate pattern error for {pattern}: {e}")
            return 0

    async def exists(self, key: str) -> bool:
        """Check if a key exists in the cache.

        Args:
            key: Cache key

        Returns:
            True if key exists, False otherwise
        """
        try:
            async with self._get_client() as client:
                return await client.exists(key) > 0
        except RedisError as e:
            logger.error(f"Cache exists error for key {key}: {e}")
            return False

    async def get_ttl(self, key: str) -> int:
        """Get the remaining TTL for a key.

        Args:
            key: Cache key

        Returns:
            TTL in seconds, -1 if key has no TTL, -2 if key doesn't exist
        """
        try:
            async with self._get_client() as client:
                return await client.ttl(key)
        except RedisError as e:
            logger.error(f"Cache TTL error for key {key}: {e}")
            return -2

    async def health_check(self) -> bool:
        """Check if Redis is accessible.

        Returns:
            True if Redis is healthy, False otherwise
        """
        try:
            async with self._get_client() as client:
                await client.ping()
                return True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False


# Singleton instance
_cache_service: Optional[CacheService] = None


def get_cache_service() -> Optional[CacheService]:
    """Get the global cache service instance."""
    return _cache_service


async def initialize_cache(redis_url: str, default_ttl: int = 3600) -> CacheService:
    """Initialize the global cache service.

    Args:
        redis_url: Redis connection URL
        default_ttl: Default TTL in seconds

    Returns:
        Initialized CacheService instance
    """
    global _cache_service

    if _cache_service is None:
        _cache_service = CacheService(redis_url, default_ttl)
        await _cache_service.initialize()

    return _cache_service


async def close_cache() -> None:
    """Close the global cache service."""
    global _cache_service

    if _cache_service is not None:
        await _cache_service.close()
        _cache_service = None
