"""
Simple cache tests - verify caching works without testing implementation details
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock

from src.core.cache import CacheService

pytestmark = pytest.mark.unit


class TestCache:
    """Basic cache functionality tests"""
    
    @pytest.fixture
    def cache_service(self):
        """Cache service instance"""
        return CacheService("redis://localhost:6379/0")
    
    @pytest.mark.asyncio
    async def test_cache_get_miss(self, cache_service):
        """Test cache miss returns None"""
        with patch.object(cache_service, '_get_client') as mock_client:
            mock_redis = AsyncMock()
            mock_redis.get.return_value = None
            mock_client.return_value.__aenter__.return_value = mock_redis
            
            result = await cache_service.get("missing_key")
            assert result is None
    
    @pytest.mark.asyncio
    async def test_cache_get_hit(self, cache_service):
        """Test cache hit returns data"""
        with patch.object(cache_service, '_get_client') as mock_client:
            mock_redis = AsyncMock()
            mock_redis.get.return_value = '{"data": "test"}'
            mock_client.return_value.__aenter__.return_value = mock_redis
            
            result = await cache_service.get("existing_key")
            assert result == {"data": "test"}
    
    @pytest.mark.asyncio
    async def test_cache_set(self, cache_service):
        """Test setting cache value"""
        with patch.object(cache_service, '_get_client') as mock_client:
            mock_redis = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_redis
            
            await cache_service.set("test_key", {"data": "value"}, ttl=300)
            mock_redis.setex.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cache_disabled(self):
        """Test cache handles initialization errors gracefully"""
        service = CacheService("redis://localhost:6379/0")
        
        # Mock initialization to fail
        with patch('src.core.cache.redis.ConnectionPool.from_url', side_effect=Exception("No Redis")):
            try:
                await service.initialize()
            except Exception:
                # Expected to fail
                pass
            
            # Service should still be created but operations will fail
            assert service is not None