"""Test smart caching implementation for Epic 001 Task 3."""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.core.cache import CacheService
from src.core.cache_warmup import CacheWarmupService
from src.core.computation_cache import ComputationCache


@pytest.mark.unit()
class TestComputationCache:
    """Test computation caching functionality."""

    @pytest.mark.asyncio()
    async def test_get_or_compute_cache_miss(self):
        """Test computation is performed on cache miss."""
        # Mock cache service
        mock_cache = AsyncMock(spec=CacheService)
        mock_cache.get.return_value = None  # Cache miss
        mock_cache.set.return_value = True

        comp_cache = ComputationCache(mock_cache)

        # Mock computation function
        call_count = 0

        async def expensive_computation():
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.01)  # Simulate work
            return {"result": "computed", "value": 42}

        # First call should compute
        result = await comp_cache.get_or_compute("test:key", expensive_computation, ttl=300)

        assert call_count == 1
        assert result == {"result": "computed", "value": 42}
        mock_cache.get.assert_called_once_with("test:key")
        mock_cache.set.assert_called_once_with("test:key", {"result": "computed", "value": 42}, ttl=300)

    @pytest.mark.asyncio()
    async def test_get_or_compute_cache_hit(self):
        """Test cached result is returned on cache hit."""
        # Mock cache service
        cached_value = {"result": "cached", "value": 100}
        mock_cache = AsyncMock(spec=CacheService)
        mock_cache.get.return_value = cached_value

        comp_cache = ComputationCache(mock_cache)

        # Mock computation function
        call_count = 0

        async def expensive_computation():
            nonlocal call_count
            call_count += 1
            return {"result": "computed", "value": 42}

        # Should return cached value without computing
        result = await comp_cache.get_or_compute("test:key", expensive_computation)

        assert call_count == 0  # Not called
        assert result == cached_value
        mock_cache.get.assert_called_once_with("test:key")
        mock_cache.set.assert_not_called()

    @pytest.mark.asyncio()
    async def test_get_or_compute_force_compute(self):
        """Test force_compute bypasses cache."""
        # Mock cache service
        cached_value = {"result": "cached", "value": 100}
        mock_cache = AsyncMock(spec=CacheService)
        mock_cache.get.return_value = cached_value
        mock_cache.set.return_value = True

        comp_cache = ComputationCache(mock_cache)

        # Mock computation function
        async def expensive_computation():
            return {"result": "fresh", "value": 200}

        # Force compute should bypass cache
        result = await comp_cache.get_or_compute("test:key", expensive_computation, force_compute=True)

        assert result == {"result": "fresh", "value": 200}
        mock_cache.get.assert_not_called()  # Should not check cache
        mock_cache.set.assert_called_once()

    def test_make_key_simple(self):
        """Test cache key generation with simple arguments."""
        comp_cache = ComputationCache()

        key = comp_cache.make_key("injury_dist", "conventional", "T1")
        assert key == "injury_dist:conventional:T1"

        key = comp_cache.make_key("computation", warfare="urban", severity="high")
        assert key == "computation:severity=high:warfare=urban"  # Sorted

    def test_make_key_complex(self):
        """Test cache key generation with complex arguments."""
        comp_cache = ComputationCache()

        base_mix = {"battle": 0.8, "non_battle": 0.2}
        key = comp_cache.make_key("injury_dist", "artillery", base_mix)

        # Should include hash of the dict
        assert key.startswith("injury_dist:artillery:")
        assert len(key.split(":")[2]) == 8  # 8-char hash

    @pytest.mark.asyncio()
    async def test_invalidate_pattern(self):
        """Test pattern-based cache invalidation."""
        mock_cache = AsyncMock(spec=CacheService)
        mock_cache.invalidate_pattern.return_value = 5

        comp_cache = ComputationCache(mock_cache)

        count = await comp_cache.invalidate_pattern("computation:*:config123:*")

        assert count == 5
        mock_cache.invalidate_pattern.assert_called_once_with("computation:*:config123:*")

    @pytest.mark.asyncio()
    async def test_clear_all(self):
        """Test clearing all computation caches."""
        mock_cache = AsyncMock(spec=CacheService)
        mock_cache.invalidate_pattern.side_effect = [3, 2, 1]  # Different counts per prefix

        comp_cache = ComputationCache(mock_cache)

        result = await comp_cache.clear_all()

        assert result is True
        assert mock_cache.invalidate_pattern.call_count == 3
        mock_cache.invalidate_pattern.assert_any_call("injury_dist:*")
        mock_cache.invalidate_pattern.assert_any_call("computation:*")
        mock_cache.invalidate_pattern.assert_any_call("expensive:*")

    @pytest.mark.asyncio()
    async def test_metrics_recording(self):
        """Test cache hit/miss metrics are recorded."""
        mock_cache = AsyncMock(spec=CacheService)
        mock_cache.get.return_value = None  # Cache miss
        mock_cache.set.return_value = True
        mock_cache.increment.return_value = 1

        comp_cache = ComputationCache(mock_cache)

        async def compute_func():
            return {"value": 42}

        # Trigger cache miss
        await comp_cache.get_or_compute("test:key", compute_func)

        # Check metrics were recorded
        mock_cache.increment.assert_any_call("metrics:cache:computation:misses")
        mock_cache.increment.assert_any_call("metrics:cache:computation:test:misses")

    @pytest.mark.asyncio()
    async def test_get_hit_rate(self):
        """Test cache hit rate calculation."""
        mock_cache = AsyncMock(spec=CacheService)
        mock_cache.get.side_effect = [75, 25]  # 75 hits, 25 misses

        comp_cache = ComputationCache(mock_cache)

        hit_rate = await comp_cache.get_hit_rate()

        assert hit_rate == 75.0  # 75%
        mock_cache.get.assert_any_call("metrics:cache:computation:hits")
        mock_cache.get.assert_any_call("metrics:cache:computation:misses")


@pytest.mark.unit()
class TestCacheWarmupService:
    """Test cache warmup functionality."""

    @pytest.mark.asyncio()
    async def test_warm_all_caches(self):
        """Test all caches are warmed on startup."""
        # Mock cache service
        mock_cache = AsyncMock(spec=CacheService)
        mock_cache.set.return_value = True

        # Mock database results
        mock_configs = [
            {
                "id": "config1",
                "name": "Test Config",
                "description": "Test",
                "config": {"test": "data"},
                "template_id": None,
                "is_public": True,
                "api_key_id": None,
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
            }
        ]
        
        # Mock enhanced database with synchronous _execute_query method
        mock_db = MagicMock()
        mock_db._execute_query.return_value = mock_configs

        with patch("src.core.cache_warmup.get_enhanced_database", return_value=mock_db):
            warmup_service = CacheWarmupService(mock_cache)

            # Mock the individual service warm_cache methods
            with patch.object(warmup_service.demographics_service, "warm_cache", new_callable=AsyncMock) as mock_demo, \
                 patch.object(warmup_service.medical_service, "warm_cache", new_callable=AsyncMock) as mock_med:
                    await warmup_service.warm_all_caches()

                    # Verify all warmup methods were called
                    mock_demo.assert_called_once()
                    mock_med.assert_called_once()

                    # Verify configuration cache was warmed
                    assert mock_db._execute_query.called
                    assert mock_cache.set.called

    @pytest.mark.asyncio()
    async def test_warm_configuration_cache(self):
        """Test configuration cache warming with top configs."""
        mock_cache = AsyncMock(spec=CacheService)
        mock_cache.set.return_value = True

        # Mock database with multiple configs
        configs = []
        for i in range(3):
            config = {
                "id": f"config{i}",
                "name": f"Config {i}",
                "description": f"Description {i}",
                "config": {"patients": 100 + i},
                "template_id": None,
                "is_public": True,
                "api_key_id": None,
                "created_at": datetime.now() - timedelta(days=i),
                "updated_at": datetime.now(),
            }
            configs.append(config)

        # Mock enhanced database with synchronous _execute_query method
        mock_db = MagicMock()
        mock_db._execute_query.return_value = configs

        with patch("src.core.cache_warmup.get_enhanced_database", return_value=mock_db):
            warmup_service = CacheWarmupService(mock_cache)
            await warmup_service._warm_configuration_cache()

            # Verify SQL query was executed
            mock_db._execute_query.assert_called_once()
            query = mock_db._execute_query.call_args[0][0]
            assert "SELECT DISTINCT c.*" in str(query)
            assert "ORDER BY COUNT(j.id) DESC" in str(query)
            assert "LIMIT 10" in str(query)

            # Verify configs were cached
            assert mock_cache.set.call_count == 3
            for i, config in enumerate(configs):
                cache_key = f"config:{config['id']}:v2"
                expected_dict = {
                    "id": config['id'],
                    "name": config['name'],
                    "description": config['description'],
                    "config": config['config'],
                    "template_id": config['template_id'],
                    "is_public": config['is_public'],
                    "api_key_id": config['api_key_id'],
                    "created_at": config['created_at'].isoformat() if config['created_at'] else None,
                    "updated_at": config['updated_at'].isoformat() if config['updated_at'] else None,
                }
                mock_cache.set.assert_any_call(cache_key, expected_dict, ttl=86400)

    @pytest.mark.asyncio()
    async def test_warm_computation_cache(self):
        """Test computation cache warming with common patterns."""
        mock_cache = AsyncMock(spec=CacheService)
        mock_cache.set.return_value = True

        warmup_service = CacheWarmupService(mock_cache)
        await warmup_service._warm_computation_cache()

        # Verify pre-computed values were cached
        warfare_types = ["conventional", "urban", "artillery", "chemical", "ied"]
        base_mixes = [
            {"battle_injury": 0.8, "non_battle_injury": 0.15, "disease": 0.05},
            {"battle_injury": 0.7, "non_battle_injury": 0.2, "disease": 0.1},
            {"battle_injury": 0.9, "non_battle_injury": 0.08, "disease": 0.02},
        ]

        expected_calls = len(warfare_types) * len(base_mixes)
        assert mock_cache.set.call_count == expected_calls

        # Verify cache keys follow expected pattern
        for call in mock_cache.set.call_args_list:
            key = call[0][0]
            value = call[0][1]
            ttl = call[1]["ttl"]

            assert key.startswith("injury_dist:")
            assert ttl == 7200  # 2 hours
            assert "warfare_type" in value
            assert "base_mix" in value
            assert value["computed"] is True

    @pytest.mark.asyncio()
    async def test_warm_cache_error_handling(self):
        """Test cache warming handles errors gracefully."""
        mock_cache = AsyncMock(spec=CacheService)

        # Make one warmup fail
        mock_db = AsyncMock()
        mock_db.execute.side_effect = Exception("Database error")

        # Mock the async context manager
        mock_db_cm = AsyncMock()
        mock_db_cm.__aenter__.return_value = mock_db
        mock_db_cm.__aexit__.return_value = None

        with patch("src.core.cache_warmup.get_enhanced_database", return_value=mock_db_cm):
            warmup_service = CacheWarmupService(mock_cache)

            # Should not raise exception
            await warmup_service.warm_all_caches()

            # Other warmup methods should still be called
            with patch.object(warmup_service.demographics_service, "warm_cache", new_callable=AsyncMock) as mock_demo, \
                 patch.object(warmup_service.medical_service, "warm_cache", new_callable=AsyncMock) as mock_med:
                    await warmup_service.warm_all_caches()
                    mock_demo.assert_called_once()
                    mock_med.assert_called_once()

    @pytest.mark.asyncio()
    async def test_get_cache_stats(self):
        """Test cache statistics retrieval."""
        mock_cache = AsyncMock(spec=CacheService)
        mock_cache.info.return_value = {"db0": {"keys": 42}, "used_memory_human": "1.5M"}
        mock_cache.count_keys.side_effect = [10, 5, 15, 12]  # Different counts per pattern

        warmup_service = CacheWarmupService(mock_cache)
        stats = await warmup_service.get_cache_stats()

        assert stats["total_keys"] == 42
        assert stats["demographics_keys"] == 10
        assert stats["medical_keys"] == 5
        assert stats["config_keys"] == 15
        assert stats["computation_keys"] == 12
        assert stats["memory_used"] == "1.5M"

        # Verify correct patterns were counted
        mock_cache.count_keys.assert_any_call("demographics:*")
        mock_cache.count_keys.assert_any_call("medical:*")
        mock_cache.count_keys.assert_any_call("config:*")
        mock_cache.count_keys.assert_any_call("injury_dist:*")

    @pytest.mark.asyncio()
    async def test_no_cache_service(self):
        """Test warmup handles missing cache service gracefully."""
        warmup_service = CacheWarmupService(None)

        # Should not raise exception
        await warmup_service.warm_all_caches()

        stats = await warmup_service.get_cache_stats()
        assert stats == {"error": "Cache service not available"}

