"""
Unit tests for APIKeyContext and security functionality.

These tests focus on the API key context, validation logic, and
security-related functionality without external dependencies.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from fastapi import HTTPException

from src.core.security_enhanced import (
    APIKeyContext,
    create_legacy_api_key,
    create_demo_api_key,
    get_api_key_info,
    DEMO_API_KEY,
    LEGACY_API_KEY
)
from src.domain.models.api_key import APIKey


class TestAPIKeyContextCreation:
    """Test APIKeyContext creation and initialization."""
    
    def test_context_creation_basic(self):
        """Test basic context creation."""
        api_key = APIKey(key="test", name="Test")
        context = APIKeyContext(api_key=api_key)
        
        assert context.api_key == api_key
        assert context.is_demo is False
        assert context.is_legacy is False
        assert context.rate_limit_remaining is None
        assert context.rate_limit_reset is None
    
    def test_context_creation_demo(self):
        """Test demo context creation."""
        api_key = APIKey(key="demo", name="Demo", is_demo=True)
        context = APIKeyContext(api_key=api_key, is_demo=True)
        
        assert context.api_key == api_key
        assert context.is_demo is True
        assert context.is_legacy is False
    
    def test_context_creation_legacy(self):
        """Test legacy context creation."""
        api_key = APIKey(key="legacy", name="Legacy")
        context = APIKeyContext(api_key=api_key, is_legacy=True)
        
        assert context.api_key == api_key
        assert context.is_demo is False
        assert context.is_legacy is True
    
    def test_context_creation_with_rate_limits(self):
        """Test context creation with rate limit info."""
        api_key = APIKey(key="rate", name="Rate")
        reset_time = datetime.utcnow() + timedelta(minutes=5)
        
        context = APIKeyContext(
            api_key=api_key,
            rate_limit_remaining=45,
            rate_limit_reset=reset_time
        )
        
        assert context.rate_limit_remaining == 45
        assert context.rate_limit_reset == reset_time


class TestAPIKeyContextLimitChecking:
    """Test limit checking functionality in APIKeyContext."""
    
    def test_check_patient_limit_success(self):
        """Test successful patient limit check."""
        api_key = APIKey(key="test", name="Test", max_patients_per_request=100)
        context = APIKeyContext(api_key=api_key)
        
        # Should not raise exception
        context.check_patient_limit(50)
        context.check_patient_limit(100)
        context.check_patient_limit(1)
    
    def test_check_patient_limit_failure(self):
        """Test patient limit check failure."""
        api_key = APIKey(key="test", name="Test", max_patients_per_request=100)
        context = APIKeyContext(api_key=api_key)
        
        with pytest.raises(HTTPException) as exc_info:
            context.check_patient_limit(101)
        
        assert exc_info.value.status_code == 400
        assert "exceeds limit" in exc_info.value.detail
        assert "101" in exc_info.value.detail
        assert "100" in exc_info.value.detail
        
        # Check headers
        headers = exc_info.value.headers
        assert headers["X-Limit-Type"] == "patients_per_request"
        assert headers["X-Limit-Value"] == "100"
        assert headers["X-Requested"] == "101"
    
    def test_check_patient_limit_edge_cases(self):
        """Test patient limit check edge cases."""
        api_key = APIKey(key="test", name="Test", max_patients_per_request=1)
        context = APIKeyContext(api_key=api_key)
        
        # Zero patients should pass
        context.check_patient_limit(0)
        
        # Exactly at limit should pass
        context.check_patient_limit(1)
        
        # Just over limit should fail
        with pytest.raises(HTTPException):
            context.check_patient_limit(2)
    
    def test_check_daily_limit_success(self):
        """Test successful daily limit check."""
        api_key = APIKey(
            key="test",
            name="Test",
            max_requests_per_day=100,
            daily_requests=50
        )
        context = APIKeyContext(api_key=api_key)
        
        # Should not raise exception
        context.check_daily_limit()
    
    def test_check_daily_limit_unlimited(self):
        """Test daily limit check with unlimited key."""
        api_key = APIKey(
            key="unlimited",
            name="Unlimited",
            max_requests_per_day=None,
            daily_requests=10000
        )
        context = APIKeyContext(api_key=api_key)
        
        # Should not raise exception even with high usage
        context.check_daily_limit()
    
    def test_check_daily_limit_failure(self):
        """Test daily limit check failure."""
        api_key = APIKey(
            key="test",
            name="Test",
            max_requests_per_day=100,
            daily_requests=100
        )
        context = APIKeyContext(api_key=api_key)
        
        with pytest.raises(HTTPException) as exc_info:
            context.check_daily_limit()
        
        assert exc_info.value.status_code == 429
        assert "Daily request limit exceeded" in exc_info.value.detail
        assert "100" in exc_info.value.detail
        
        # Check headers
        headers = exc_info.value.headers
        assert headers["X-Limit-Type"] == "requests_per_day"
        assert headers["X-Limit-Value"] == "100"
        assert headers["X-Current-Usage"] == "100"
        assert "Retry-After" in headers
    
    @patch('src.core.security_enhanced.datetime')
    def test_check_daily_limit_retry_after_calculation(self, mock_datetime):
        """Test retry-after calculation in daily limit check."""
        # Mock current time as 2:30 PM
        current_time = datetime(2024, 1, 15, 14, 30, 0)
        mock_datetime.utcnow.return_value = current_time
        
        api_key = APIKey(
            key="test",
            name="Test",
            max_requests_per_day=100,
            daily_requests=100
        )
        context = APIKeyContext(api_key=api_key)
        
        with pytest.raises(HTTPException) as exc_info:
            context.check_daily_limit()
        
        # Should calculate seconds until midnight UTC
        expected_seconds = (24 - 14) * 3600 - 30 * 60  # 9.5 hours in seconds
        assert exc_info.value.headers["Retry-After"] == str(expected_seconds)


class TestAPIKeyContextUsabilityChecking:
    """Test usability checking in APIKeyContext."""
    
    def test_check_usability_success(self):
        """Test successful usability check."""
        api_key = APIKey(key="test", name="Test", is_active=True)
        context = APIKeyContext(api_key=api_key)
        
        # Should not raise exception
        context.check_usability()
    
    def test_check_usability_inactive(self):
        """Test usability check with inactive key."""
        api_key = APIKey(key="test", name="Test", is_active=False)
        context = APIKeyContext(api_key=api_key)
        
        with pytest.raises(HTTPException) as exc_info:
            context.check_usability()
        
        assert exc_info.value.status_code == 401
        assert "inactive" in exc_info.value.detail
        assert exc_info.value.headers["X-Key-Status"] == "inactive"
    
    def test_check_usability_expired(self):
        """Test usability check with expired key."""
        api_key = APIKey(
            key="test",
            name="Test",
            is_active=True,
            expires_at=datetime.utcnow() - timedelta(days=1)
        )
        context = APIKeyContext(api_key=api_key)
        
        with pytest.raises(HTTPException) as exc_info:
            context.check_usability()
        
        assert exc_info.value.status_code == 401
        assert "expired" in exc_info.value.detail
        assert exc_info.value.headers["X-Key-Status"] == "expired"


class TestAPIKeyContextDataMethods:
    """Test data retrieval methods in APIKeyContext."""
    
    def test_get_limits_info(self):
        """Test limits info retrieval."""
        api_key = APIKey(
            key="test",
            name="Test",
            max_patients_per_request=200,
            max_requests_per_day=500,
            max_requests_per_minute=30,
            max_requests_per_hour=600,
            daily_requests=25,
            total_requests=150
        )
        context = APIKeyContext(api_key=api_key)
        
        limits = context.get_limits_info()
        
        assert limits["patients_per_request"] == 200
        assert limits["requests_per_day"] == 500
        assert limits["requests_per_minute"] == 30
        assert limits["requests_per_hour"] == 600
        assert limits["daily_usage"] == 25
        assert limits["total_usage"] == 150
    
    def test_get_response_headers_demo(self):
        """Test response headers for demo key."""
        api_key = APIKey(
            key="demo",
            name="Demo",
            is_demo=True,
            max_patients_per_request=50,
            max_requests_per_day=100,
            daily_requests=15
        )
        context = APIKeyContext(api_key=api_key, is_demo=True)
        
        headers = context.get_response_headers()
        
        assert headers["X-API-Key-Type"] == "demo"
        assert headers["X-Patient-Limit"] == "50"
        assert headers["X-Daily-Limit"] == "100"
        assert headers["X-Daily-Usage"] == "15"
    
    def test_get_response_headers_live(self):
        """Test response headers for live key."""
        api_key = APIKey(
            key="live",
            name="Live",
            is_demo=False,
            max_patients_per_request=1000,
            max_requests_per_day=None,  # Unlimited
            daily_requests=50
        )
        context = APIKeyContext(api_key=api_key, is_demo=False)
        
        headers = context.get_response_headers()
        
        assert headers["X-API-Key-Type"] == "live"
        assert headers["X-Patient-Limit"] == "1000"
        assert headers["X-Daily-Limit"] == "unlimited"
        assert headers["X-Daily-Usage"] == "50"
    
    def test_get_response_headers_with_rate_limits(self):
        """Test response headers with rate limit information."""
        api_key = APIKey(key="rate", name="Rate")
        reset_time = datetime(2024, 1, 15, 12, 0, 0)
        
        context = APIKeyContext(
            api_key=api_key,
            rate_limit_remaining=45,
            rate_limit_reset=reset_time
        )
        
        headers = context.get_response_headers()
        
        assert headers["X-RateLimit-Remaining"] == "45"
        assert headers["X-RateLimit-Reset"] == str(int(reset_time.timestamp()))


class TestKeyCreationHelpers:
    """Test helper functions for creating virtual keys."""
    
    def test_create_legacy_api_key(self):
        """Test legacy API key creation."""
        legacy_key = create_legacy_api_key()
        
        assert legacy_key.key == LEGACY_API_KEY
        assert legacy_key.name == "Legacy API Key"
        assert legacy_key.email is None
        assert legacy_key.is_active is True
        assert legacy_key.is_demo is False
        assert legacy_key.max_patients_per_request == 10000  # High limit
        assert legacy_key.max_requests_per_day is None       # Unlimited
        assert legacy_key.max_requests_per_minute == 1000    # High limit
        assert legacy_key.max_requests_per_hour == 10000     # High limit
        assert legacy_key.key_metadata["legacy_mode"] is True
    
    def test_create_demo_api_key(self):
        """Test demo API key creation."""
        demo_key = create_demo_api_key()
        
        assert demo_key.key == DEMO_API_KEY
        assert demo_key.name == "Public Demo Key"
        assert demo_key.email is None
        assert demo_key.is_active is True
        assert demo_key.is_demo is True
        assert demo_key.max_patients_per_request == 50
        assert demo_key.max_requests_per_day == 100
        assert demo_key.max_requests_per_minute == 10
        assert demo_key.max_requests_per_hour == 50
        assert demo_key.key_metadata["public_demo"] is True
    
    def test_legacy_vs_demo_key_differences(self):
        """Test that legacy and demo keys have appropriate differences."""
        legacy_key = create_legacy_api_key()
        demo_key = create_demo_api_key()
        
        # Legacy should have much higher limits
        assert legacy_key.max_patients_per_request > demo_key.max_patients_per_request
        assert legacy_key.max_requests_per_minute > demo_key.max_requests_per_minute
        assert legacy_key.max_requests_per_hour > demo_key.max_requests_per_hour
        
        # Legacy should be unlimited daily, demo should be limited
        assert legacy_key.max_requests_per_day is None
        assert demo_key.max_requests_per_day is not None
        
        # Demo status should differ
        assert legacy_key.is_demo is False
        assert demo_key.is_demo is True


class TestAPIKeyInfoGeneration:
    """Test API key information generation for logging."""
    
    def test_get_api_key_info_regular_key(self):
        """Test API key info for regular database key."""
        api_key = APIKey(
            key="test_key",
            name="Test Key",
            is_demo=False,
            max_patients_per_request=500,
            max_requests_per_day=1000,
            total_requests=150,
            last_used_at=datetime(2024, 1, 15, 10, 30, 0)
        )
        api_key.id = "test-uuid-123"
        
        context = APIKeyContext(api_key=api_key, is_demo=False, is_legacy=False)
        info = get_api_key_info(context)
        
        assert info["key_id"] == "test-uuid-123"
        assert info["key_name"] == "Test Key"
        assert info["is_demo"] is False
        assert info["is_legacy"] is False
        assert info["limits"]["patients_per_request"] == 500
        assert info["limits"]["requests_per_day"] == 1000
        assert info["limits"]["total_usage"] == 150
        assert info["last_used"] == "2024-01-15T10:30:00"
    
    def test_get_api_key_info_demo_key(self):
        """Test API key info for demo key."""
        api_key = create_demo_api_key()
        context = APIKeyContext(api_key=api_key, is_demo=True, is_legacy=False)
        
        info = get_api_key_info(context)
        
        assert info["key_id"] == "virtual"  # No database ID
        assert info["key_name"] == "Public Demo Key"
        assert info["is_demo"] is True
        assert info["is_legacy"] is False
        assert info["limits"]["patients_per_request"] == 50
    
    def test_get_api_key_info_legacy_key(self):
        """Test API key info for legacy key."""
        api_key = create_legacy_api_key()
        context = APIKeyContext(api_key=api_key, is_demo=False, is_legacy=True)
        
        info = get_api_key_info(context)
        
        assert info["key_id"] == "virtual"  # No database ID
        assert info["key_name"] == "Legacy API Key"
        assert info["is_demo"] is False
        assert info["is_legacy"] is True
        assert info["limits"]["patients_per_request"] == 10000
    
    def test_get_api_key_info_no_last_used(self):
        """Test API key info with no last used time."""
        api_key = APIKey(key="test", name="Test", last_used_at=None)
        context = APIKeyContext(api_key=api_key)
        
        info = get_api_key_info(context)
        
        assert info["last_used"] is None


class TestSecurityConstants:
    """Test security-related constants and configuration."""
    
    def test_demo_api_key_constant(self):
        """Test demo API key constant."""
        assert DEMO_API_KEY == "DEMO_MILMED_2025_50_PATIENTS"
        assert "DEMO" in DEMO_API_KEY
        assert "2025" in DEMO_API_KEY
        assert "50" in DEMO_API_KEY
        assert "PATIENTS" in DEMO_API_KEY
    
    def test_legacy_api_key_environment(self):
        """Test legacy API key from environment."""
        # Note: This tests the default value when env var is not set
        assert LEGACY_API_KEY == "your-api-key-here"
    
    def test_demo_key_security_properties(self):
        """Test that demo key has secure properties."""
        demo_key = create_demo_api_key()
        
        # Should have restrictive limits appropriate for public use
        assert demo_key.max_patients_per_request <= 50
        assert demo_key.max_requests_per_day <= 100
        assert demo_key.max_requests_per_minute <= 10
        assert demo_key.max_requests_per_hour <= 50
        
        # Should be clearly marked as demo
        assert demo_key.is_demo is True
        assert "public_demo" in demo_key.key_metadata


if __name__ == "__main__":
    pytest.main([__file__, "-v"])