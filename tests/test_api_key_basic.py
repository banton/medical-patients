"""
Basic API Key Management Tests

Simple tests for API key models and core functionality
without database dependencies.
"""

from datetime import datetime, timedelta

import pytest

from src.domain.models.api_key import DEMO_API_KEY_CONFIG, APIKey


class TestAPIKeyModel:
    """Test the APIKey model functionality."""

    def test_api_key_creation(self):
        """Test basic API key creation with explicit defaults."""
        api_key = APIKey(
            key="sk_test_123456789",
            name="Test Key",
            email="test@example.com",
            is_active=True,
            is_demo=False,
            max_patients_per_request=1000,
        )

        assert api_key.key == "sk_test_123456789"
        assert api_key.name == "Test Key"
        assert api_key.email == "test@example.com"
        assert api_key.is_active is True
        assert api_key.is_demo is False
        assert api_key.max_patients_per_request == 1000

    def test_api_key_usability_checks(self):
        """Test API key usability and expiration checks."""
        # Active, non-expired key
        active_key = APIKey(key="active", name="Active", is_active=True)
        assert active_key.is_usable() is True

        # Inactive key
        inactive_key = APIKey(key="inactive", name="Inactive", is_active=False)
        assert inactive_key.is_usable() is False

        # Expired key
        expired_key = APIKey(
            key="expired", name="Expired", is_active=True, expires_at=datetime.utcnow() - timedelta(days=1)
        )
        assert expired_key.is_expired() is True
        assert expired_key.is_usable() is False

    def test_patient_limit_checking(self):
        """Test patient limit validation."""
        api_key = APIKey(key="test", name="Test", max_patients_per_request=100)

        assert api_key.check_patient_limit(50) is True
        assert api_key.check_patient_limit(100) is True
        assert api_key.check_patient_limit(101) is False

    def test_daily_limit_checking(self):
        """Test daily request limit validation."""
        # Unlimited key
        unlimited_key = APIKey(key="unlimited", name="Unlimited", max_requests_per_day=None)
        unlimited_key.daily_requests = 1000
        assert unlimited_key.check_daily_limit() is True

        # Limited key under limit
        limited_key = APIKey(key="limited", name="Limited", max_requests_per_day=100)
        limited_key.daily_requests = 50
        assert limited_key.check_daily_limit() is True

        # Limited key at limit
        limited_key.daily_requests = 100
        assert limited_key.check_daily_limit() is False

    def test_usage_recording(self):
        """Test usage tracking functionality."""
        api_key = APIKey(key="usage", name="Usage Test")
        initial_requests = api_key.total_requests
        initial_patients = api_key.total_patients_generated

        api_key.record_usage(patients_generated=25)

        assert api_key.total_requests == initial_requests + 1
        assert api_key.total_patients_generated == initial_patients + 25
        assert api_key.daily_requests == 1
        assert api_key.last_used_at is not None

    def test_daily_reset_detection(self):
        """Test daily counter reset detection."""
        api_key = APIKey(key="reset", name="Reset Test")

        # Fresh key needs reset (no last_reset_at)
        assert api_key.needs_daily_reset() is True

        # Set reset to today
        api_key.last_reset_at = datetime.utcnow()
        assert api_key.needs_daily_reset() is False

        # Set reset to yesterday
        api_key.last_reset_at = datetime.utcnow() - timedelta(days=1)
        assert api_key.needs_daily_reset() is True

    def test_demo_key_configuration(self):
        """Test demo key configuration constants."""
        assert DEMO_API_KEY_CONFIG["key"] == "DEMO_MILMED_2025_50_PATIENTS"
        assert DEMO_API_KEY_CONFIG["max_patients_per_request"] == 50
        assert DEMO_API_KEY_CONFIG["max_requests_per_day"] == 100
        assert DEMO_API_KEY_CONFIG["max_requests_per_minute"] == 10
        assert DEMO_API_KEY_CONFIG["is_demo"] is True

    def test_api_key_string_representation(self):
        """Test API key string representation."""
        api_key = APIKey(key="sk_test_12345678", name="Test Key", is_active=True)
        repr_str = repr(api_key)

        assert "Test Key" in repr_str
        assert "sk_test_" in repr_str  # First 8 chars
        assert "active=True" in repr_str

    def test_limits_info_generation(self):
        """Test limits information dictionary."""
        api_key = APIKey(
            key="limits_test",
            name="Limits Test",
            max_patients_per_request=200,
            max_requests_per_day=500,
            max_requests_per_minute=30,
            max_requests_per_hour=600,
        )

        limits = api_key.get_limits_info()

        assert limits["patients_per_request"] == 200
        assert limits["requests_per_day"] == 500
        assert limits["requests_per_minute"] == 30
        assert limits["requests_per_hour"] == 600

    def test_usage_summary_generation(self):
        """Test usage summary generation."""
        api_key = APIKey(
            key="summary_test",
            name="Summary Test",
            total_requests=150,
            total_patients_generated=2500,
            daily_requests=25,
            is_demo=True,
        )

        summary = api_key.get_usage_summary()

        assert summary["total_requests"] == 150
        assert summary["total_patients_generated"] == 2500
        assert summary["daily_requests"] == 25
        assert summary["is_demo"] is True
        assert summary["is_active"] is True
        assert summary["is_expired"] is False

    def test_to_dict_conversion(self):
        """Test API key to dictionary conversion."""
        api_key = APIKey(
            key="dict_test", name="Dict Test", email="dict@test.com", total_requests=100, key_metadata={"test": "value"}
        )

        api_dict = api_key.to_dict()

        assert api_dict["name"] == "Dict Test"
        assert api_dict["email"] == "dict@test.com"
        assert api_dict["usage"]["total_requests"] == 100
        assert api_dict["metadata"]["test"] == "value"
        assert "id" in api_dict
        assert "limits" in api_dict


class TestDemoKeyConfiguration:
    """Test demo key configuration and constants."""

    def test_demo_key_defaults(self):
        """Test demo key has secure defaults."""
        config = DEMO_API_KEY_CONFIG

        # Verify restrictive limits
        assert config["max_patients_per_request"] == 50  # Limited patients
        assert config["max_requests_per_day"] == 100  # Limited daily requests
        assert config["max_requests_per_minute"] == 10  # Limited rate
        assert config["max_requests_per_hour"] == 50  # Limited hourly

        # Verify it's marked as demo
        assert config["is_demo"] is True
        assert config["name"] == "Public Demo Key"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
