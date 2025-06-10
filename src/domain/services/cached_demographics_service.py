"""Cached demographics service for improved performance."""

import json
import logging
import os
from typing import Any, Dict

from config import get_settings
from patient_generator.demographics import DemographicsGenerator
from src.core.cache import get_cache_service

logger = logging.getLogger(__name__)
settings = get_settings()


class CachedDemographicsService:
    """Service that provides cached access to demographics data."""

    DEMOGRAPHICS_CACHE_KEY = "demographics:data"
    DEMOGRAPHICS_JSON_CACHE_KEY = "demographics:json"

    def __init__(self):
        self._demographics_generator = None
        self._cached_data = None

    async def get_demographics_data(self) -> Dict[str, Any]:
        """Get demographics data with caching.

        Returns:
            Demographics data dictionary
        """
        # If caching is disabled, load directly
        if not settings.CACHE_ENABLED:
            return self._load_demographics_data()

        cache_service = get_cache_service()
        if not cache_service:
            return self._load_demographics_data()

        # Try to get from cache
        cached_data = await cache_service.get(self.DEMOGRAPHICS_JSON_CACHE_KEY)
        if cached_data is not None:
            logger.debug("Demographics data loaded from cache")
            return cached_data

        # Load from file and cache
        data = self._load_demographics_data()

        # Cache for 24 hours (demographics data rarely changes)
        await cache_service.set(
            self.DEMOGRAPHICS_JSON_CACHE_KEY,
            data,
            ttl=86400,  # 24 hours
        )
        logger.info("Demographics data cached")

        return data

    def _load_demographics_data(self) -> Dict[str, Any]:
        """Load demographics data from JSON file.

        Returns:
            Demographics data dictionary
        """
        base_dir = os.path.dirname(os.path.abspath(__file__))
        # Navigate to patient_generator directory
        patient_gen_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(base_dir))), "patient_generator")
        json_path = os.path.join(patient_gen_dir, "demographics.json")

        try:
            with open(json_path, encoding="utf-8") as f:
                data = json.load(f)
                return data.get("NATO_NATIONS", {})
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Error loading demographics data: {e}")
            return {}

    def get_demographics_generator(self) -> DemographicsGenerator:
        """Get a demographics generator instance.

        Returns:
            DemographicsGenerator instance
        """
        if self._demographics_generator is None:
            self._demographics_generator = DemographicsGenerator()
        return self._demographics_generator

    async def warm_cache(self) -> None:
        """Pre-load demographics data into cache."""
        logger.info("Warming demographics cache...")
        await self.get_demographics_data()

    async def invalidate_cache(self) -> bool:
        """Invalidate the demographics cache.

        Returns:
            True if cache was invalidated
        """
        if not settings.CACHE_ENABLED:
            return False

        cache_service = get_cache_service()
        if not cache_service:
            return False

        result = await cache_service.delete(self.DEMOGRAPHICS_JSON_CACHE_KEY)
        if result:
            logger.info("Demographics cache invalidated")
        return result
