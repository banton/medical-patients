"""Cached medical conditions service for improved performance."""

import json
import logging
from typing import Dict, List, Any, Optional
import hashlib

from src.core.cache import get_cache_service
from patient_generator.medical import MedicalConditionGenerator
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class CachedMedicalService:
    """Service that provides cached access to medical conditions."""
    
    CONDITION_CACHE_PREFIX = "medical:condition"
    MULTIPLE_CONDITIONS_CACHE_PREFIX = "medical:conditions"
    MEDICAL_DATA_CACHE_KEY = "medical:data"
    
    def __init__(self):
        self._condition_generator = None
        self._conditions_data = None
        
    def _get_cache_key(self, prefix: str, injury_type: str, triage_category: str, count: Optional[int] = None) -> str:
        """Generate a cache key for medical conditions.
        
        Args:
            prefix: Cache key prefix
            injury_type: Type of injury
            triage_category: Triage category
            count: Number of conditions (for multiple conditions)
            
        Returns:
            Cache key string
        """
        if count is not None:
            key_data = f"{injury_type}:{triage_category}:{count}"
        else:
            key_data = f"{injury_type}:{triage_category}"
        return f"{prefix}:{key_data}"
        
    async def get_condition(self, injury_type: str, triage_category: str) -> Dict[str, Any]:
        """Get a medical condition with caching.
        
        Args:
            injury_type: Type of injury
            triage_category: Triage category
            
        Returns:
            Medical condition dictionary
        """
        # If caching is disabled, generate directly
        if not settings.CACHE_ENABLED:
            return self._get_condition_generator().generate_condition(injury_type, triage_category)
            
        cache_service = get_cache_service()
        if not cache_service:
            return self._get_condition_generator().generate_condition(injury_type, triage_category)
            
        # For medical conditions, we don't want to cache individual random results
        # as they should vary. Instead, we'll cache the pool of conditions
        # and let the generator randomly select from the cached pool
        
        # Just generate fresh conditions each time
        return self._get_condition_generator().generate_condition(injury_type, triage_category)
        
    async def get_multiple_conditions(
        self, 
        injury_type: str, 
        triage_category: str, 
        count: int = 2
    ) -> List[Dict[str, Any]]:
        """Get multiple medical conditions.
        
        Args:
            injury_type: Type of injury
            triage_category: Triage category
            count: Number of conditions to generate
            
        Returns:
            List of medical condition dictionaries
        """
        # Similarly, don't cache random selections
        return self._get_condition_generator().generate_multiple_conditions(
            injury_type, triage_category, count
        )
        
    async def get_medical_data(self) -> Dict[str, Any]:
        """Get all medical conditions data with caching.
        
        Returns:
            Medical conditions data dictionary
        """
        # If caching is disabled, return the data directly
        if not settings.CACHE_ENABLED:
            return self._get_medical_data()
            
        cache_service = get_cache_service()
        if not cache_service:
            return self._get_medical_data()
            
        # Try to get from cache
        cached_data = await cache_service.get(self.MEDICAL_DATA_CACHE_KEY)
        if cached_data is not None:
            logger.debug("Medical data loaded from cache")
            return cached_data
            
        # Get fresh data and cache it
        data = self._get_medical_data()
        
        # Cache for 24 hours (medical conditions rarely change)
        await cache_service.set(
            self.MEDICAL_DATA_CACHE_KEY,
            data,
            ttl=86400  # 24 hours
        )
        logger.info("Medical data cached")
        
        return data
        
    def _get_medical_data(self) -> Dict[str, Any]:
        """Get medical conditions data from the generator.
        
        Returns:
            Dictionary containing all medical conditions pools
        """
        generator = self._get_condition_generator()
        return {
            "battle_trauma_conditions": generator.battle_trauma_conditions,
            "non_battle_injuries": generator.non_battle_injuries,
            "disease_conditions": generator.disease_conditions,
            "severity_modifiers": generator.severity_modifiers
        }
        
    def _get_condition_generator(self) -> MedicalConditionGenerator:
        """Get a medical condition generator instance.
        
        Returns:
            MedicalConditionGenerator instance
        """
        if self._condition_generator is None:
            self._condition_generator = MedicalConditionGenerator()
        return self._condition_generator
        
    async def warm_cache(self) -> None:
        """Pre-load medical data into cache."""
        logger.info("Warming medical conditions cache...")
        await self.get_medical_data()
        
    async def invalidate_cache(self) -> bool:
        """Invalidate the medical conditions cache.
        
        Returns:
            True if cache was invalidated
        """
        if not settings.CACHE_ENABLED:
            return False
            
        cache_service = get_cache_service()
        if not cache_service:
            return False
            
        # Invalidate all medical-related cache keys
        deleted = await cache_service.invalidate_pattern(f"{self.CONDITION_CACHE_PREFIX}:*")
        deleted += await cache_service.invalidate_pattern(f"{self.MULTIPLE_CONDITIONS_CACHE_PREFIX}:*")
        deleted += await cache_service.delete(self.MEDICAL_DATA_CACHE_KEY)
        
        if deleted > 0:
            logger.info(f"Medical conditions cache invalidated ({deleted} keys)")
        return deleted > 0