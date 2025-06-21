"""Cache warmup service for application startup."""

import asyncio
import logging
from typing import Optional

from sqlalchemy import text

from config import get_settings
from src.core.cache import CacheService
from src.domain.services.cached_demographics_service import CachedDemographicsService
from src.domain.services.cached_medical_service import CachedMedicalService
from src.infrastructure.database_adapter import get_enhanced_database

logger = logging.getLogger(__name__)
settings = get_settings()


class CacheWarmupService:
    """Warm critical caches on application startup."""

    def __init__(self, cache_service: Optional[CacheService] = None):
        """Initialize cache warmup service.

        Args:
            cache_service: Optional cache service instance
        """
        self.cache = cache_service
        self.demographics_service = CachedDemographicsService()
        self.medical_service = CachedMedicalService()

    async def warm_all_caches(self) -> None:
        """Warm all critical caches concurrently."""
        if not self.cache:
            logger.warning("Cache service not available, skipping warmup")
            return

        logger.info("Starting cache warmup...")

        # Run all warmup tasks concurrently
        await asyncio.gather(
            self._warm_demographics_cache(),
            self._warm_medical_cache(),
            self._warm_configuration_cache(),
            self._warm_computation_cache(),
            return_exceptions=True,  # Don't fail if one warmup fails
        )

        logger.info("Cache warmup completed")

    async def _warm_demographics_cache(self) -> None:
        """Warm demographics data cache."""
        try:
            await self.demographics_service.warm_cache()
            logger.info("Demographics cache warmed successfully")
        except Exception as e:
            logger.error(f"Failed to warm demographics cache: {e}")

    async def _warm_medical_cache(self) -> None:
        """Warm medical conditions cache."""
        try:
            await self.medical_service.warm_cache()
            logger.info("Medical conditions cache warmed successfully")
        except Exception as e:
            logger.error(f"Failed to warm medical cache: {e}")

    async def _warm_configuration_cache(self) -> None:
        """Cache frequently used configurations."""
        try:
            db = get_enhanced_database()
            if db is None:
                logger.warning("Database not available for configuration cache warming")
                return
            
            # Get top 10 most used configs from last 30 days
            query = text("""
                    SELECT DISTINCT c.*
                    FROM configurations c
                    JOIN jobs j ON j.config_id = c.id
                    WHERE j.created_at > NOW() - INTERVAL '30 days'
                    GROUP BY c.id, c.name, c.description, c.config, c.template_id,
                             c.is_public, c.api_key_id, c.created_at, c.updated_at
                    ORDER BY COUNT(j.id) DESC
                    LIMIT 10
                """)

            # Execute query using sync method (wrapped in error handling)
            configs = None
            try:
                configs = db._execute_query(
                    str(query),
                    fetch_all=True
                )
            except Exception:
                # If connection pool is closed, skip cache warmup
                logger.warning("Database connection not available for cache warmup")
                return

            # Cache each configuration
            cached_count = 0
            if configs:
                for config in configs:
                    cache_key = f"config:{config['id']}:v2"
                    config_dict = {
                        "id": str(config['id']),
                        "name": config['name'],
                        "description": config['description'],
                        "config": config['config'],
                        "template_id": str(config['template_id']) if config['template_id'] else None,
                        "is_public": config['is_public'],
                        "api_key_id": str(config['api_key_id']) if config['api_key_id'] else None,
                        "created_at": config['created_at'].isoformat() if config['created_at'] else None,
                        "updated_at": config['updated_at'].isoformat() if config['updated_at'] else None,
                    }
                    if self.cache:
                        await self.cache.set(cache_key, config_dict, ttl=86400)  # 24 hours
                    cached_count += 1

            logger.info(f"Configuration cache warmed with {cached_count} configs")

        except Exception as e:
            logger.error(f"Failed to warm configuration cache: {e}")

    async def _warm_computation_cache(self) -> None:
        """Pre-compute and cache common expensive computations."""
        try:
            # Define common warfare type and injury combinations
            warfare_types = ["conventional", "urban", "artillery", "chemical", "ied"]
            base_mixes = [
                {"battle_injury": 0.8, "non_battle_injury": 0.15, "disease": 0.05},
                {"battle_injury": 0.7, "non_battle_injury": 0.2, "disease": 0.1},
                {"battle_injury": 0.9, "non_battle_injury": 0.08, "disease": 0.02},
            ]

            cached_count = 0
            for warfare_type in warfare_types:
                for _i, base_mix in enumerate(base_mixes):
                    # Create cache key for injury distribution
                    mix_hash = hash(str(sorted(base_mix.items())))
                    cache_key = f"injury_dist:{warfare_type}:{mix_hash}"

                    # Pre-compute common distributions
                    # Note: This is a simplified version - actual computation would be more complex
                    computed_distribution = {
                        "warfare_type": warfare_type,
                        "base_mix": base_mix,
                        "computed": True,
                        "ttl_seconds": 7200,
                    }

                    if self.cache:
                        await self.cache.set(cache_key, computed_distribution, ttl=7200)  # 2 hours
                    cached_count += 1

            logger.info(f"Computation cache warmed with {cached_count} pre-computed values")

        except Exception as e:
            logger.error(f"Failed to warm computation cache: {e}")

    async def get_cache_stats(self) -> dict:
        """Get cache warmup statistics.

        Returns:
            Dictionary with cache statistics
        """
        if not self.cache:
            return {"error": "Cache service not available"}

        try:
            # Get cache info if available
            info = await self.cache.info()

            # Count keys by pattern
            demographics_count = await self.cache.count_keys("demographics:*")
            medical_count = await self.cache.count_keys("medical:*")
            config_count = await self.cache.count_keys("config:*")
            computation_count = await self.cache.count_keys("injury_dist:*")

            return {
                "total_keys": info.get("db0", {}).get("keys", 0) if info else 0,
                "demographics_keys": demographics_count,
                "medical_keys": medical_count,
                "config_keys": config_count,
                "computation_keys": computation_count,
                "memory_used": info.get("used_memory_human", "unknown") if info else "unknown",
            }
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {"error": str(e)}

