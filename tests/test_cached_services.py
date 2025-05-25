"""Tests for cached demographics and medical services."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import json

from src.domain.services.cached_demographics_service import CachedDemographicsService
from src.domain.services.cached_medical_service import CachedMedicalService
from src.core.cache import CacheService


@pytest.fixture
def mock_cache_service():
    """Create a mock cache service."""
    service = Mock(spec=CacheService)
    service.get = AsyncMock()
    service.set = AsyncMock()
    service.delete = AsyncMock()
    service.invalidate_pattern = AsyncMock()
    return service


@pytest.fixture
def mock_settings():
    """Mock settings with cache enabled."""
    with patch('src.domain.services.cached_demographics_service.settings') as mock:
        mock.CACHE_ENABLED = True
        yield mock


class TestCachedDemographicsService:
    """Test cases for CachedDemographicsService."""
    
    @pytest.mark.asyncio
    async def test_get_demographics_data_from_cache(self, mock_cache_service, mock_settings):
        """Test getting demographics data from cache."""
        # Setup
        service = CachedDemographicsService()
        cached_data = {"USA": {"first_names": {"male": ["John", "Mike"]}}}
        mock_cache_service.get.return_value = cached_data
        
        with patch('src.domain.services.cached_demographics_service.get_cache_service', 
                  return_value=mock_cache_service):
            # Execute
            result = await service.get_demographics_data()
            
            # Verify
            assert result == cached_data
            mock_cache_service.get.assert_called_once_with(
                CachedDemographicsService.DEMOGRAPHICS_JSON_CACHE_KEY
            )
            mock_cache_service.set.assert_not_called()
            
    @pytest.mark.asyncio
    async def test_get_demographics_data_cache_miss(self, mock_cache_service, mock_settings):
        """Test getting demographics data with cache miss."""
        # Setup
        service = CachedDemographicsService()
        mock_cache_service.get.return_value = None
        
        # Mock file loading
        expected_data = {"USA": {"first_names": {"male": ["John"]}}}
        with patch.object(service, '_load_demographics_data', return_value=expected_data), \
             patch('src.domain.services.cached_demographics_service.get_cache_service', 
                   return_value=mock_cache_service):
            # Execute
            result = await service.get_demographics_data()
            
            # Verify
            assert result == expected_data
            mock_cache_service.get.assert_called_once()
            mock_cache_service.set.assert_called_once_with(
                CachedDemographicsService.DEMOGRAPHICS_JSON_CACHE_KEY,
                expected_data,
                ttl=86400
            )
            
    @pytest.mark.asyncio
    async def test_get_demographics_data_cache_disabled(self):
        """Test getting demographics data with cache disabled."""
        # Setup
        service = CachedDemographicsService()
        expected_data = {"USA": {"first_names": {"male": ["John"]}}}
        
        with patch('src.domain.services.cached_demographics_service.settings.CACHE_ENABLED', False), \
             patch.object(service, '_load_demographics_data', return_value=expected_data):
            # Execute
            result = await service.get_demographics_data()
            
            # Verify
            assert result == expected_data
            
    def test_get_demographics_generator(self):
        """Test getting demographics generator instance."""
        service = CachedDemographicsService()
        
        # First call creates instance
        gen1 = service.get_demographics_generator()
        assert gen1 is not None
        
        # Second call returns same instance
        gen2 = service.get_demographics_generator()
        assert gen2 is gen1
        
    @pytest.mark.asyncio
    async def test_warm_cache(self, mock_cache_service, mock_settings):
        """Test cache warming."""
        service = CachedDemographicsService()
        
        with patch.object(service, 'get_demographics_data') as mock_get:
            await service.warm_cache()
            mock_get.assert_called_once()
            
    @pytest.mark.asyncio
    async def test_invalidate_cache(self, mock_cache_service, mock_settings):
        """Test cache invalidation."""
        service = CachedDemographicsService()
        mock_cache_service.delete.return_value = True
        
        with patch('src.domain.services.cached_demographics_service.get_cache_service', 
                  return_value=mock_cache_service):
            result = await service.invalidate_cache()
            
            assert result is True
            mock_cache_service.delete.assert_called_once_with(
                CachedDemographicsService.DEMOGRAPHICS_JSON_CACHE_KEY
            )


class TestCachedMedicalService:
    """Test cases for CachedMedicalService."""
    
    @pytest.mark.asyncio
    async def test_get_medical_data_from_cache(self, mock_cache_service):
        """Test getting medical data from cache."""
        # Setup
        service = CachedMedicalService()
        cached_data = {
            "battle_trauma_conditions": [{"code": "125670008", "display": "War injury"}],
            "severity_modifiers": [{"code": "371923003", "display": "Mild to moderate"}]
        }
        mock_cache_service.get.return_value = cached_data
        
        with patch('src.domain.services.cached_medical_service.settings.CACHE_ENABLED', True), \
             patch('src.domain.services.cached_medical_service.get_cache_service', 
                   return_value=mock_cache_service):
            # Execute
            result = await service.get_medical_data()
            
            # Verify
            assert result == cached_data
            mock_cache_service.get.assert_called_once_with(
                CachedMedicalService.MEDICAL_DATA_CACHE_KEY
            )
            
    @pytest.mark.asyncio
    async def test_get_medical_data_cache_miss(self, mock_cache_service):
        """Test getting medical data with cache miss."""
        # Setup
        service = CachedMedicalService()
        mock_cache_service.get.return_value = None
        
        expected_data = {
            "battle_trauma_conditions": [{"code": "125670008", "display": "War injury"}]
        }
        
        with patch('src.domain.services.cached_medical_service.settings.CACHE_ENABLED', True), \
             patch('src.domain.services.cached_medical_service.get_cache_service', 
                   return_value=mock_cache_service), \
             patch.object(service, '_get_medical_data', return_value=expected_data):
            # Execute
            result = await service.get_medical_data()
            
            # Verify
            assert result == expected_data
            mock_cache_service.set.assert_called_once_with(
                CachedMedicalService.MEDICAL_DATA_CACHE_KEY,
                expected_data,
                ttl=86400
            )
            
    @pytest.mark.asyncio
    async def test_get_condition_no_caching(self):
        """Test that individual conditions are not cached."""
        service = CachedMedicalService()
        
        # Mock the generator
        mock_generator = Mock()
        expected_condition = {"code": "125670008", "display": "War injury"}
        mock_generator.generate_condition.return_value = expected_condition
        
        with patch('src.domain.services.cached_medical_service.settings.CACHE_ENABLED', True), \
             patch.object(service, '_get_condition_generator', return_value=mock_generator):
            # Execute
            result = await service.get_condition("BATTLE_TRAUMA", "T1")
            
            # Verify
            assert result == expected_condition
            mock_generator.generate_condition.assert_called_once_with("BATTLE_TRAUMA", "T1")
            
    @pytest.mark.asyncio
    async def test_get_multiple_conditions_no_caching(self):
        """Test that multiple conditions are not cached."""
        service = CachedMedicalService()
        
        # Mock the generator
        mock_generator = Mock()
        expected_conditions = [
            {"code": "125670008", "display": "War injury"},
            {"code": "262574004", "display": "Bullet wound"}
        ]
        mock_generator.generate_multiple_conditions.return_value = expected_conditions
        
        with patch.object(service, '_get_condition_generator', return_value=mock_generator):
            # Execute
            result = await service.get_multiple_conditions("BATTLE_TRAUMA", "T1", 2)
            
            # Verify
            assert result == expected_conditions
            mock_generator.generate_multiple_conditions.assert_called_once_with(
                "BATTLE_TRAUMA", "T1", 2
            )
            
    @pytest.mark.asyncio
    async def test_invalidate_cache(self, mock_cache_service):
        """Test cache invalidation."""
        service = CachedMedicalService()
        mock_cache_service.invalidate_pattern.side_effect = [5, 3]  # Two pattern calls
        mock_cache_service.delete.return_value = 1
        
        with patch('src.domain.services.cached_medical_service.settings.CACHE_ENABLED', True), \
             patch('src.domain.services.cached_medical_service.get_cache_service', 
                   return_value=mock_cache_service):
            result = await service.invalidate_cache()
            
            assert result is True
            assert mock_cache_service.invalidate_pattern.call_count == 2
            mock_cache_service.delete.assert_called_once()