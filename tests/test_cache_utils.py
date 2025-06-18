"""
Tests for cache utility functions.
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.core.cache_utils import (
    API_KEY_LIMITS_TTL,
    CONFIGURATION_TTL,
    JOB_STATUS_TTL,
    cache_api_key_limits,
    cache_configuration_template,
    cache_job_status,
    get_api_key_hash,
    get_cache_stats,
    get_cached_api_key_limits,
    get_cached_configuration,
    get_cached_job_status,
    invalidate_configuration_cache,
    invalidate_job_cache,
)
from src.domain.models.job import Job, JobProgressDetails, JobStatus


@pytest.fixture
def mock_cache_service():
    """Mock cache service for testing."""
    cache_mock = AsyncMock()
    cache_mock.get = AsyncMock()
    cache_mock.set = AsyncMock()
    cache_mock.delete = AsyncMock()
    cache_mock.health_check = AsyncMock(return_value=True)
    return cache_mock


@pytest.fixture
def sample_job():
    """Sample job for testing."""
    from datetime import datetime
    
    return Job(
        job_id="test-job-123",
        status=JobStatus.RUNNING,
        progress=50,
        config={"patients": 100},
        created_at=datetime.utcnow(),
        progress_details=JobProgressDetails(
            current_phase="Generating patients",
            phase_description="Processing patient generation",
            phase_progress=50,
            total_patients=100,
            processed_patients=50
        )
    )


class TestAPIKeyHashFunction:
    """Test API key hashing function."""
    
    def test_get_api_key_hash(self):
        """Test that API key hashing works correctly."""
        api_key = "test-api-key-12345"
        hash1 = get_api_key_hash(api_key)
        hash2 = get_api_key_hash(api_key)
        
        # Same key should produce same hash
        assert hash1 == hash2
        assert len(hash1) == 16  # Hash should be truncated to 16 chars
        
        # Different key should produce different hash
        different_key = "different-api-key"
        different_hash = get_api_key_hash(different_key)
        assert hash1 != different_hash


class TestAPIKeyLimitsCaching:
    """Test API key limits caching functions."""
    
    @pytest.mark.asyncio
    async def test_cache_api_key_limits(self, mock_cache_service):
        """Test caching API key limits."""
        with patch("src.core.cache_utils.get_cache_service", return_value=mock_cache_service):
            api_key = "test-key"
            limits_data = {
                "max_patients_per_request": 1000,
                "max_requests_per_day": 100,
                "daily_usage": 50
            }
            
            await cache_api_key_limits(api_key, limits_data)
            
            # Verify cache was called correctly
            key_hash = get_api_key_hash(api_key)
            expected_key = f"apikey:{key_hash}:limits"
            mock_cache_service.set.assert_called_once_with(
                expected_key, limits_data, ttl=API_KEY_LIMITS_TTL
            )
    
    @pytest.mark.asyncio
    async def test_get_cached_api_key_limits(self, mock_cache_service):
        """Test retrieving cached API key limits."""
        api_key = "test-key"
        cached_data = {"max_patients_per_request": 1000}
        mock_cache_service.get.return_value = cached_data
        
        with patch("src.core.cache_utils.get_cache_service", return_value=mock_cache_service):
            result = await get_cached_api_key_limits(api_key)
            
            assert result == cached_data
            key_hash = get_api_key_hash(api_key)
            expected_key = f"apikey:{key_hash}:limits"
            mock_cache_service.get.assert_called_once_with(expected_key)
    
    @pytest.mark.asyncio
    async def test_cache_unavailable(self):
        """Test behavior when cache is unavailable."""
        with patch("src.core.cache_utils.get_cache_service", return_value=None):
            # Should not raise error, just return None
            result = await get_cached_api_key_limits("test-key")
            assert result is None
            
            # Should not raise error when setting
            await cache_api_key_limits("test-key", {"data": "test"})


class TestJobStatusCaching:
    """Test job status caching functions."""
    
    @pytest.mark.asyncio
    async def test_cache_job_status_running(self, mock_cache_service, sample_job):
        """Test caching job status for running job."""
        with patch("src.core.cache_utils.get_cache_service", return_value=mock_cache_service):
            await cache_job_status(sample_job)
            
            expected_key = f"job:{sample_job.job_id}:status"
            expected_data = {
                "id": sample_job.job_id,
                "status": "running",
                "progress": 50,
                "created_at": sample_job.created_at.isoformat(),
                "completed_at": None,
                "error": None,
                "summary": None,
                "progress_details": {
                    "current_phase": "Generating patients",
                    "phase_description": "Processing patient generation",
                    "phase_progress": 50,
                    "total_patients": 100,
                    "processed_patients": 50,
                    "time_estimates": None
                }
            }
            
            mock_cache_service.set.assert_called_once()
            call_args = mock_cache_service.set.call_args
            assert call_args[0][0] == expected_key
            assert call_args[1]["ttl"] == JOB_STATUS_TTL
    
    @pytest.mark.asyncio
    async def test_cache_job_status_completed(self, mock_cache_service, sample_job):
        """Test caching job status for completed job."""
        sample_job.status = JobStatus.COMPLETED
        
        with patch("src.core.cache_utils.get_cache_service", return_value=mock_cache_service):
            await cache_job_status(sample_job)
            
            # Completed jobs should have longer TTL
            call_args = mock_cache_service.set.call_args
            assert call_args[1]["ttl"] == 3600  # 1 hour
    
    @pytest.mark.asyncio
    async def test_get_cached_job_status(self, mock_cache_service):
        """Test retrieving cached job status."""
        job_id = "test-job-123"
        cached_data = {"status": "running", "progress": 75}
        mock_cache_service.get.return_value = cached_data
        
        with patch("src.core.cache_utils.get_cache_service", return_value=mock_cache_service):
            result = await get_cached_job_status(job_id)
            
            assert result == cached_data
            expected_key = f"job:{job_id}:status"
            mock_cache_service.get.assert_called_once_with(expected_key)
    
    @pytest.mark.asyncio
    async def test_invalidate_job_cache(self, mock_cache_service):
        """Test invalidating job cache."""
        job_id = "test-job-123"
        
        with patch("src.core.cache_utils.get_cache_service", return_value=mock_cache_service):
            await invalidate_job_cache(job_id)
            
            expected_key = f"job:{job_id}:status"
            mock_cache_service.delete.assert_called_once_with(expected_key)


class TestConfigurationCaching:
    """Test configuration template caching functions."""
    
    @pytest.mark.asyncio
    async def test_cache_configuration_template(self, mock_cache_service):
        """Test caching configuration template."""
        config_id = "test-config-123"
        config_data = {
            "name": "Test Config",
            "description": "Test configuration",
            "config": {"fronts": ["north", "south"]}
        }
        
        with patch("src.core.cache_utils.get_cache_service", return_value=mock_cache_service):
            await cache_configuration_template(config_id, config_data)
            
            expected_key = f"config:{config_id}"
            mock_cache_service.set.assert_called_once_with(
                expected_key, config_data, ttl=CONFIGURATION_TTL
            )
    
    @pytest.mark.asyncio
    async def test_get_cached_configuration(self, mock_cache_service):
        """Test retrieving cached configuration."""
        config_id = "test-config-123"
        cached_data = {"name": "Test Config"}
        mock_cache_service.get.return_value = cached_data
        
        with patch("src.core.cache_utils.get_cache_service", return_value=mock_cache_service):
            result = await get_cached_configuration(config_id)
            
            assert result == cached_data
            expected_key = f"config:{config_id}"
            mock_cache_service.get.assert_called_once_with(expected_key)
    
    @pytest.mark.asyncio
    async def test_invalidate_configuration_cache(self, mock_cache_service):
        """Test invalidating configuration cache."""
        config_id = "test-config-123"
        
        with patch("src.core.cache_utils.get_cache_service", return_value=mock_cache_service):
            await invalidate_configuration_cache(config_id)
            
            expected_key = f"config:{config_id}"
            mock_cache_service.delete.assert_called_once_with(expected_key)


class TestCacheStats:
    """Test cache statistics function."""
    
    @pytest.mark.asyncio
    async def test_get_cache_stats_healthy(self, mock_cache_service):
        """Test getting cache stats when cache is healthy."""
        with patch("src.core.cache_utils.get_cache_service", return_value=mock_cache_service):
            stats = await get_cache_stats()
            
            assert stats["available"] is True
            assert stats["healthy"] is True
            assert stats["ttls"]["api_key_limits"] == API_KEY_LIMITS_TTL
            assert stats["ttls"]["configuration"] == CONFIGURATION_TTL
            assert stats["ttls"]["job_status"] == JOB_STATUS_TTL
    
    @pytest.mark.asyncio
    async def test_get_cache_stats_unavailable(self):
        """Test getting cache stats when cache is unavailable."""
        with patch("src.core.cache_utils.get_cache_service", return_value=None):
            stats = await get_cache_stats()
            
            assert stats["available"] is False
            assert "healthy" not in stats
            assert "ttls" not in stats
    
    @pytest.mark.asyncio
    async def test_get_cache_stats_error(self, mock_cache_service):
        """Test getting cache stats when health check fails."""
        mock_cache_service.health_check.side_effect = Exception("Connection failed")
        
        with patch("src.core.cache_utils.get_cache_service", return_value=mock_cache_service):
            stats = await get_cache_stats()
            
            assert stats["available"] is False
            assert stats["error"] == "Connection failed"


class TestCacheErrorHandling:
    """Test error handling in cache functions."""
    
    @pytest.mark.asyncio
    async def test_cache_set_error_handling(self, mock_cache_service, sample_job):
        """Test error handling when cache set fails."""
        mock_cache_service.set.side_effect = Exception("Redis error")
        
        with patch("src.core.cache_utils.get_cache_service", return_value=mock_cache_service):
            # Should not raise exception
            await cache_api_key_limits("test-key", {"data": "test"})
            await cache_job_status(sample_job)
            await cache_configuration_template("test-config", {"data": "test"})
    
    @pytest.mark.asyncio
    async def test_cache_get_error_handling(self, mock_cache_service):
        """Test error handling when cache get fails."""
        mock_cache_service.get.side_effect = Exception("Redis error")
        
        with patch("src.core.cache_utils.get_cache_service", return_value=mock_cache_service):
            # Should return None instead of raising
            result = await get_cached_api_key_limits("test-key")
            assert result is None
            
            result = await get_cached_job_status("test-job")
            assert result is None
            
            result = await get_cached_configuration("test-config")
            assert result is None
    
    @pytest.mark.asyncio
    async def test_cache_delete_error_handling(self, mock_cache_service):
        """Test error handling when cache delete fails."""
        mock_cache_service.delete.side_effect = Exception("Redis error")
        
        with patch("src.core.cache_utils.get_cache_service", return_value=mock_cache_service):
            # Should not raise exception
            await invalidate_job_cache("test-job")
            await invalidate_configuration_cache("test-config")