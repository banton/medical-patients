"""Integration tests for cache invalidation on configuration updates."""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from src.core.cache import CacheService
from src.core.cache_utils import (
    cache_configuration_template,
    get_cached_configuration,
    invalidate_configuration_cache,
)
from src.core.computation_cache import ComputationCache


@pytest.mark.integration()
class TestCacheInvalidationIntegration:
    """Test cache invalidation integration with configuration updates."""

    @pytest.mark.asyncio()
    async def test_configuration_update_invalidates_cache(self):
        """Test that updating a configuration invalidates all related caches."""
        # Mock cache service
        mock_cache = AsyncMock(spec=CacheService)
        mock_cache.delete.return_value = True
        mock_cache.invalidate_pattern.return_value = 3
        mock_cache.set.return_value = True
        mock_cache.get.return_value = None

        with patch("src.core.cache_utils.get_cache_service", return_value=mock_cache):
            config_id = "test-config-123"
            config_data = {
                "id": config_id,
                "name": "Test Config",
                "config": {"total_patients": 100},
            }

            # Cache the configuration
            await cache_configuration_template(config_id, config_data)
            mock_cache.set.assert_called_once_with(f"config:{config_id}", config_data, ttl=3600)

            # Invalidate the cache
            await invalidate_configuration_cache(config_id)

            # Verify both v1 and v2 keys were deleted
            assert mock_cache.delete.call_count == 2
            mock_cache.delete.assert_any_call(f"config:{config_id}")
            mock_cache.delete.assert_any_call(f"config:{config_id}:v2")

            # Verify computation caches were invalidated
            mock_cache.invalidate_pattern.assert_called_once_with(f"computation:*:{config_id}:*")

    @pytest.mark.asyncio()
    async def test_cache_hit_after_warmup(self):
        """Test that cached configurations are served after warmup."""
        mock_cache = AsyncMock(spec=CacheService)
        cached_config = {
            "id": "config-456",
            "name": "Warmed Config",
            "config": {"total_patients": 200},
        }
        mock_cache.get.return_value = cached_config

        with patch("src.core.cache_utils.get_cache_service", return_value=mock_cache):
            # Get cached configuration
            result = await get_cached_configuration("config-456")

            assert result == cached_config
            mock_cache.get.assert_called_once_with("config:config-456")

    @pytest.mark.asyncio()
    async def test_concurrent_cache_operations(self):
        """Test concurrent cache operations don't interfere."""
        mock_cache = AsyncMock(spec=CacheService)
        mock_cache.set.return_value = True
        mock_cache.get.return_value = {"cached": "value"}  # Return cached value
        mock_cache.delete.return_value = True
        mock_cache.invalidate_pattern.return_value = 0  # No computation caches to invalidate

        with patch("src.core.cache_utils.get_cache_service", return_value=mock_cache):
            # Run concurrent operations
            tasks = [
                cache_configuration_template("config1", {"data": 1}),
                cache_configuration_template("config2", {"data": 2}),
                get_cached_configuration("config3"),
                invalidate_configuration_cache("config4"),
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Verify all operations completed
            assert len(results) == 4
            assert results[2] == {"cached": "value"}  # get_cached_configuration result

            # Verify correct cache operations
            assert mock_cache.set.call_count == 2
            assert mock_cache.get.call_count == 1
            assert mock_cache.delete.call_count >= 2  # At least v1 and v2 keys

    @pytest.mark.asyncio()
    async def test_cache_disabled_behavior(self):
        """Test behavior when cache is disabled."""
        with patch("src.core.cache_utils.get_cache_service", return_value=None):
            config_id = "no-cache-config"
            config_data = {"id": config_id, "name": "No Cache"}

            # Operations should complete without errors
            await cache_configuration_template(config_id, config_data)
            result = await get_cached_configuration(config_id)
            await invalidate_configuration_cache(config_id)

            # No cached value should be returned
            assert result is None

    @pytest.mark.asyncio()
    async def test_computation_cache_integration(self):
        """Test computation cache integration with configuration changes."""
        mock_cache = AsyncMock(spec=CacheService)
        mock_cache.get.side_effect = [None, {"cached": "result"}]
        mock_cache.set.return_value = True
        mock_cache.invalidate_pattern.return_value = 5

        comp_cache = ComputationCache(mock_cache)

        # Create a computation that depends on a config
        config_id = "comp-test-config"

        async def config_dependent_computation():
            # Simulate computation that uses configuration
            await asyncio.sleep(0.01)
            return {"result": "computed", "config_id": config_id}

        # First call computes
        cache_key = comp_cache.make_key("computation", "injury", config_id=config_id)
        result1 = await comp_cache.get_or_compute(cache_key, config_dependent_computation)

        assert result1["result"] == "computed"
        mock_cache.set.assert_called_once()

        # Second call should hit cache
        result2 = await comp_cache.get_or_compute(cache_key, config_dependent_computation)
        assert result2["cached"] == "result"

        # Invalidate computations for this config
        count = await comp_cache.invalidate_pattern(f"computation:*:{config_id}:*")
        assert count == 5

    @pytest.mark.asyncio()
    async def test_cache_ttl_behavior(self):
        """Test cache TTL is respected."""
        mock_cache = AsyncMock(spec=CacheService)
        mock_cache.set.return_value = True
        mock_cache.get_ttl.return_value = 1800  # 30 minutes remaining

        with patch("src.core.cache_utils.get_cache_service", return_value=mock_cache):
            config_id = "ttl-test-config"
            config_data = {"id": config_id, "ttl_test": True}

            # Cache with specific TTL
            await cache_configuration_template(config_id, config_data)

            # Verify TTL was set correctly (1 hour = 3600 seconds)
            mock_cache.set.assert_called_once_with(f"config:{config_id}", config_data, ttl=3600)

    @pytest.mark.asyncio()
    async def test_error_handling_in_cache_operations(self):
        """Test error handling in cache operations."""
        mock_cache = AsyncMock(spec=CacheService)
        mock_cache.set.side_effect = Exception("Redis connection error")
        mock_cache.get.side_effect = Exception("Redis connection error")
        mock_cache.delete.side_effect = Exception("Redis connection error")

        with patch("src.core.cache_utils.get_cache_service", return_value=mock_cache):
            # Operations should handle errors gracefully
            await cache_configuration_template("error-config", {"data": "test"})
            result = await get_cached_configuration("error-config")
            await invalidate_configuration_cache("error-config")

            # Should return None on error
            assert result is None
