"""Tests for the cache service functionality."""

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, Mock, patch

import pytest
import redis.asyncio as redis

from src.core.cache import CacheService, close_cache, get_cache_service, initialize_cache


@pytest.fixture()
async def cache_service():
    """Create a cache service instance for testing."""
    service = CacheService("redis://localhost:6379/15", default_ttl=60)  # Use test database
    await service.initialize()
    yield service
    # Clean up after tests
    async with service._get_client() as client:
        await client.flushdb()
    await service.close()


@pytest.fixture()
async def mock_cache_service():
    """Create a mock cache service for testing without Redis."""
    service = Mock(spec=CacheService)
    service.get = AsyncMock()
    service.set = AsyncMock()
    service.delete = AsyncMock()
    service.invalidate_pattern = AsyncMock()
    service.exists = AsyncMock()
    service.health_check = AsyncMock()
    return service


class TestCacheService:
    """Test cases for CacheService."""

    @pytest.mark.asyncio()
    async def test_initialize_success(self):
        """Test successful cache initialization."""
        service = CacheService("redis://localhost:6379/15", default_ttl=60)
        await service.initialize()
        assert service._pool is not None
        await service.close()

    @pytest.mark.asyncio()
    async def test_initialize_failure(self):
        """Test cache initialization with invalid URL."""
        import redis.exceptions
        service = CacheService("redis://invalid:9999/0", default_ttl=60)
        with pytest.raises((ConnectionError, OSError, redis.exceptions.ConnectionError)):
            await service.initialize()

    @pytest.mark.asyncio()
    async def test_set_and_get_string(self, cache_service):
        """Test setting and getting string values."""
        key = "test:string"
        value = "Hello, Redis!"

        # Set value
        result = await cache_service.set(key, value)
        assert result is True

        # Get value
        retrieved = await cache_service.get(key)
        assert retrieved == value

    @pytest.mark.asyncio()
    async def test_set_and_get_dict(self, cache_service):
        """Test setting and getting dictionary values."""
        key = "test:dict"
        value = {"name": "John", "age": 30, "active": True}

        # Set value
        result = await cache_service.set(key, value)
        assert result is True

        # Get value
        retrieved = await cache_service.get(key)
        assert retrieved == value

    @pytest.mark.asyncio()
    async def test_set_with_ttl(self, cache_service):
        """Test setting values with custom TTL."""
        key = "test:ttl"
        value = "temporary"

        # Set with 2 second TTL
        result = await cache_service.set(key, value, ttl=2)
        assert result is True

        # Check TTL
        ttl = await cache_service.get_ttl(key)
        assert 0 < ttl <= 2

    @pytest.mark.asyncio()
    async def test_delete(self, cache_service):
        """Test deleting keys."""
        key = "test:delete"
        value = "to be deleted"

        # Set value
        await cache_service.set(key, value)

        # Delete key
        result = await cache_service.delete(key)
        assert result is True

        # Verify deletion
        retrieved = await cache_service.get(key)
        assert retrieved is None

    @pytest.mark.asyncio()
    async def test_delete_nonexistent(self, cache_service):
        """Test deleting non-existent keys."""
        result = await cache_service.delete("nonexistent:key")
        assert result is False

    @pytest.mark.asyncio()
    async def test_exists(self, cache_service):
        """Test checking key existence."""
        key = "test:exists"
        value = "exists"

        # Check non-existent key
        exists = await cache_service.exists(key)
        assert exists is False

        # Set key
        await cache_service.set(key, value)

        # Check existing key
        exists = await cache_service.exists(key)
        assert exists is True

    @pytest.mark.asyncio()
    async def test_invalidate_pattern(self, cache_service):
        """Test invalidating keys by pattern."""
        # Set multiple keys
        await cache_service.set("pattern:key1", "value1")
        await cache_service.set("pattern:key2", "value2")
        await cache_service.set("pattern:key3", "value3")
        await cache_service.set("other:key", "other")

        # Invalidate pattern
        deleted = await cache_service.invalidate_pattern("pattern:*")
        assert deleted == 3

        # Verify keys are deleted
        assert await cache_service.get("pattern:key1") is None
        assert await cache_service.get("pattern:key2") is None
        assert await cache_service.get("pattern:key3") is None

        # Other key should still exist
        assert await cache_service.get("other:key") == "other"

    @pytest.mark.asyncio()
    async def test_health_check(self, cache_service):
        """Test health check functionality."""
        result = await cache_service.health_check()
        assert result is True

    @pytest.mark.asyncio()
    async def test_health_check_failure(self):
        """Test health check with invalid connection."""
        service = CacheService("redis://invalid:9999/0")
        service._pool = Mock()  # Fake pool to bypass initialization check
        result = await service.health_check()
        assert result is False

    @pytest.mark.asyncio()
    async def test_global_cache_service(self):
        """Test global cache service management."""
        # Initialize global service
        service = await initialize_cache("redis://localhost:6379/15", default_ttl=60)
        assert service is not None

        # Get global service
        retrieved = get_cache_service()
        assert retrieved is service

        # Close global service
        await close_cache()
        assert get_cache_service() is None


class TestCacheIntegration:
    """Integration tests with mock Redis."""

    @pytest.mark.asyncio()
    @patch("src.core.cache.redis")
    async def test_get_with_redis_error(self, mock_redis):
        """Test get operation with Redis error."""
        # Setup mock
        mock_client = AsyncMock()
        mock_client.get.side_effect = redis.RedisError("Connection error")
        mock_pool = Mock()

        # Create service with mocked pool
        service = CacheService("redis://localhost:6379/0")
        service._pool = mock_pool

        # Create a proper async context manager
        @asynccontextmanager
        async def mock_get_client():
            yield mock_client

        with patch.object(service, "_get_client", mock_get_client):
            result = await service.get("test:key")
            assert result is None

    @pytest.mark.asyncio()
    @patch("src.core.cache.redis")
    async def test_set_with_redis_error(self, mock_redis):
        """Test set operation with Redis error."""
        # Setup mock
        mock_client = AsyncMock()
        mock_client.setex.side_effect = redis.RedisError("Connection error")
        mock_pool = Mock()

        # Create service with mocked pool
        service = CacheService("redis://localhost:6379/0")
        service._pool = mock_pool

        # Create a proper async context manager
        @asynccontextmanager
        async def mock_get_client():
            yield mock_client

        with patch.object(service, "_get_client", mock_get_client):
            result = await service.set("test:key", "value")
            assert result is False
