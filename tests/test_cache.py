"""
Simple cache tests - verify caching works without testing implementation details
"""

import pytest
from unittest.mock import Mock, patch

from src.core.cache import CacheService

pytestmark = pytest.mark.unit


class TestCache:
    """Basic cache functionality tests"""
    
    @pytest.fixture
    def mock_redis(self):
        """Simple Redis mock"""
        with patch('src.core.cache.redis.Redis') as mock:
            redis_instance = Mock()
            mock.from_url.return_value = redis_instance
            yield redis_instance
    
    @pytest.fixture
    def cache_service(self, mock_redis):
        """Cache service with mocked Redis"""
        return CacheService()
    
    def test_cache_get_miss(self, cache_service, mock_redis):
        """Test cache miss returns None"""
        mock_redis.get.return_value = None
        result = cache_service.get("missing_key")
        assert result is None
    
    def test_cache_get_hit(self, cache_service, mock_redis):
        """Test cache hit returns data"""
        mock_redis.get.return_value = b'{"data": "test"}'
        result = cache_service.get("existing_key")
        assert result == {"data": "test"}
    
    def test_cache_set(self, cache_service, mock_redis):
        """Test setting cache value"""
        cache_service.set("test_key", {"data": "value"}, ttl=300)
        mock_redis.setex.assert_called_once()
        
    def test_cache_invalidate(self, cache_service, mock_redis):
        """Test cache invalidation"""
        cache_service.invalidate("test_key")
        mock_redis.delete.assert_called_once_with("test_key")
    
    def test_cache_disabled(self):
        """Test cache works when Redis is not available"""
        with patch('src.core.cache.redis.Redis') as mock:
            mock.from_url.side_effect = Exception("No Redis")
            service = CacheService()
            
            # Should not crash
            assert service.get("key") is None
            service.set("key", "value")
            service.invalidate("key")