"""
Unit tests for APIKey model.

These tests focus on the business logic and methods of the APIKey model
without requiring database connections or external dependencies.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch

from src.domain.models.api_key import APIKey, DEMO_API_KEY_CONFIG


class TestAPIKeyModelCore:
    """Test core APIKey model functionality."""
    
    def test_init_with_required_fields(self):
        """Test APIKey creation with only required fields."""
        api_key = APIKey(key="test_key", name="Test Key")
        
        assert api_key.key == "test_key"
        assert api_key.name == "Test Key"
        # Check defaults - some are None until database assigns them
        assert api_key.email is None
        assert api_key.is_active is None  # Database default
        assert api_key.is_demo is None    # Database default  
        assert api_key.max_patients_per_request is None  # Database default
    
    def test_init_with_all_fields(self):
        """Test APIKey creation with all fields specified."""
        api_key = APIKey(
            key="sk_test_123",
            name="Full Test",
            email="test@example.com",
            is_active=True,
            is_demo=False,
            max_patients_per_request=500,
            max_requests_per_day=1000,
            max_requests_per_minute=30,
            max_requests_per_hour=600,
            total_requests=100,
            total_patients_generated=2500,
            daily_requests=25,
            key_metadata={"test": "data"}
        )
        
        assert api_key.key == "sk_test_123"
        assert api_key.name == "Full Test"
        assert api_key.email == "test@example.com"
        assert api_key.is_active is True
        assert api_key.is_demo is False
        assert api_key.max_patients_per_request == 500
        assert api_key.max_requests_per_day == 1000
        assert api_key.max_requests_per_minute == 30
        assert api_key.max_requests_per_hour == 600
        assert api_key.total_requests == 100
        assert api_key.total_patients_generated == 2500
        assert api_key.daily_requests == 25
        assert api_key.key_metadata == {"test": "data"}
    
    def test_repr_string(self):
        """Test string representation."""
        api_key = APIKey(key="sk_test_12345678", name="Test Key", is_active=True)
        repr_str = repr(api_key)
        
        assert "APIKey" in repr_str
        assert "Test Key" in repr_str
        assert "sk_test_" in repr_str  # First 8 chars
        assert "active=True" in repr_str


class TestAPIKeyExpirationLogic:
    """Test expiration-related functionality."""
    
    def test_is_expired_with_no_expiration(self):
        """Test that keys without expiration are never expired."""
        api_key = APIKey(key="no_expire", name="No Expire", expires_at=None)
        assert api_key.is_expired() is False
    
    def test_is_expired_with_future_date(self):
        """Test that keys with future expiration are not expired."""
        future_date = datetime.utcnow() + timedelta(days=30)
        api_key = APIKey(key="future", name="Future", expires_at=future_date)
        assert api_key.is_expired() is False
    
    def test_is_expired_with_past_date(self):
        """Test that keys with past expiration are expired."""
        past_date = datetime.utcnow() - timedelta(days=1)
        api_key = APIKey(key="past", name="Past", expires_at=past_date)
        assert api_key.is_expired() is True
    
    def test_is_expired_with_exact_time(self):
        """Test expiration with very close times."""
        # Create a time 1 second in the past
        just_past = datetime.utcnow() - timedelta(seconds=1)
        api_key = APIKey(key="just_past", name="Just Past", expires_at=just_past)
        assert api_key.is_expired() is True


class TestAPIKeyUsabilityLogic:
    """Test API key usability checks."""
    
    def test_is_usable_active_and_not_expired(self):
        """Test that active, non-expired keys are usable."""
        api_key = APIKey(
            key="usable",
            name="Usable",
            is_active=True,
            expires_at=datetime.utcnow() + timedelta(days=30)
        )
        assert api_key.is_usable() is True
    
    def test_is_usable_inactive_key(self):
        """Test that inactive keys are not usable."""
        api_key = APIKey(key="inactive", name="Inactive", is_active=False)
        assert api_key.is_usable() is False
    
    def test_is_usable_expired_key(self):
        """Test that expired keys are not usable."""
        api_key = APIKey(
            key="expired",
            name="Expired",
            is_active=True,
            expires_at=datetime.utcnow() - timedelta(days=1)
        )
        assert api_key.is_usable() is False
    
    def test_is_usable_inactive_and_expired(self):
        """Test that inactive and expired keys are not usable."""
        api_key = APIKey(
            key="both",
            name="Both",
            is_active=False,
            expires_at=datetime.utcnow() - timedelta(days=1)
        )
        assert api_key.is_usable() is False


class TestAPIKeyLimitChecking:
    """Test limit checking functionality."""
    
    def test_check_patient_limit_under_limit(self):
        """Test patient limit check under the limit."""
        api_key = APIKey(key="test", name="Test", max_patients_per_request=100)
        assert api_key.check_patient_limit(50) is True
        assert api_key.check_patient_limit(1) is True
    
    def test_check_patient_limit_at_limit(self):
        """Test patient limit check at exactly the limit."""
        api_key = APIKey(key="test", name="Test", max_patients_per_request=100)
        assert api_key.check_patient_limit(100) is True
    
    def test_check_patient_limit_over_limit(self):
        """Test patient limit check over the limit."""
        api_key = APIKey(key="test", name="Test", max_patients_per_request=100)
        assert api_key.check_patient_limit(101) is False
        assert api_key.check_patient_limit(1000) is False
    
    def test_check_patient_limit_zero_patients(self):
        """Test patient limit check with zero patients."""
        api_key = APIKey(key="test", name="Test", max_patients_per_request=100)
        assert api_key.check_patient_limit(0) is True
    
    def test_check_daily_limit_unlimited(self):
        """Test daily limit check with unlimited key."""
        api_key = APIKey(
            key="unlimited",
            name="Unlimited",
            max_requests_per_day=None,
            daily_requests=10000
        )
        assert api_key.check_daily_limit() is True
    
    def test_check_daily_limit_under_limit(self):
        """Test daily limit check under the limit."""
        api_key = APIKey(
            key="limited",
            name="Limited",
            max_requests_per_day=100,
            daily_requests=50
        )
        assert api_key.check_daily_limit() is True
    
    def test_check_daily_limit_at_limit(self):
        """Test daily limit check at exactly the limit."""
        api_key = APIKey(
            key="at_limit",
            name="At Limit",
            max_requests_per_day=100,
            daily_requests=100
        )
        assert api_key.check_daily_limit() is False
    
    def test_check_daily_limit_over_limit(self):
        """Test daily limit check over the limit."""
        api_key = APIKey(
            key="over_limit",
            name="Over Limit",
            max_requests_per_day=100,
            daily_requests=150
        )
        assert api_key.check_daily_limit() is False


class TestAPIKeyDailyResetLogic:
    """Test daily counter reset functionality."""
    
    def test_needs_daily_reset_no_last_reset(self):
        """Test that keys with no last reset need reset."""
        api_key = APIKey(key="no_reset", name="No Reset", last_reset_at=None)
        assert api_key.needs_daily_reset() is True
    
    def test_needs_daily_reset_same_day(self):
        """Test that keys reset today don't need reset."""
        today = datetime.utcnow()
        api_key = APIKey(key="today", name="Today", last_reset_at=today)
        assert api_key.needs_daily_reset() is False
    
    def test_needs_daily_reset_yesterday(self):
        """Test that keys reset yesterday need reset."""
        yesterday = datetime.utcnow() - timedelta(days=1)
        api_key = APIKey(key="yesterday", name="Yesterday", last_reset_at=yesterday)
        assert api_key.needs_daily_reset() is True
    
    def test_needs_daily_reset_earlier_today(self):
        """Test that keys reset earlier today don't need reset."""
        earlier_today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        api_key = APIKey(key="earlier", name="Earlier", last_reset_at=earlier_today)
        assert api_key.needs_daily_reset() is False
    
    @patch('src.domain.models.api_key.datetime')
    def test_reset_daily_counters(self, mock_datetime):
        """Test daily counter reset functionality."""
        fixed_time = datetime(2024, 1, 15, 12, 0, 0)
        mock_datetime.utcnow.return_value = fixed_time
        
        api_key = APIKey(
            key="reset_test",
            name="Reset Test",
            daily_requests=50,
            last_reset_at=datetime(2024, 1, 14, 8, 0, 0)
        )
        
        api_key.reset_daily_counters()
        
        assert api_key.daily_requests == 0
        assert api_key.last_reset_at == fixed_time


class TestAPIKeyUsageTracking:
    """Test usage tracking functionality."""
    
    @patch('src.domain.models.api_key.datetime')
    def test_record_usage(self, mock_datetime):
        """Test usage recording functionality."""
        fixed_time = datetime(2024, 1, 15, 12, 0, 0)
        mock_datetime.utcnow.return_value = fixed_time
        
        api_key = APIKey(
            key="usage_test",
            name="Usage Test",
            total_requests=100,
            total_patients_generated=2000,
            daily_requests=10
        )
        
        api_key.record_usage(patients_generated=25)
        
        assert api_key.total_requests == 101
        assert api_key.total_patients_generated == 2025
        assert api_key.daily_requests == 11
        assert api_key.last_used_at == fixed_time
        assert api_key.updated_at == fixed_time
    
    def test_record_usage_zero_patients(self):
        """Test recording usage with zero patients."""
        api_key = APIKey(
            key="zero_test",
            name="Zero Test",
            total_requests=0,
            total_patients_generated=0,
            daily_requests=0
        )
        
        api_key.record_usage(patients_generated=0)
        
        assert api_key.total_requests == 1
        assert api_key.total_patients_generated == 0
        assert api_key.daily_requests == 1


class TestAPIKeyDataMethods:
    """Test data retrieval and conversion methods."""
    
    def test_get_usage_summary(self):
        """Test usage summary generation."""
        last_used = datetime(2024, 1, 15, 10, 30, 0)
        created = datetime(2024, 1, 1, 9, 0, 0)
        
        api_key = APIKey(
            key="summary_test",
            name="Summary Test",
            total_requests=150,
            total_patients_generated=3000,
            daily_requests=25,
            last_used_at=last_used,
            created_at=created,
            is_demo=True,
            is_active=True,
            max_patients_per_request=200,
            max_requests_per_day=500,
            max_requests_per_minute=30,
            max_requests_per_hour=600
        )
        
        summary = api_key.get_usage_summary()
        
        assert summary["total_requests"] == 150
        assert summary["total_patients_generated"] == 3000
        assert summary["daily_requests"] == 25
        assert summary["last_used_at"] == last_used.isoformat()
        assert summary["created_at"] == created.isoformat()
        assert summary["is_demo"] is True
        assert summary["is_active"] is True
        assert summary["is_expired"] is False
        assert summary["limits"]["max_patients_per_request"] == 200
        assert summary["limits"]["max_requests_per_day"] == 500
        assert summary["limits"]["max_requests_per_minute"] == 30
        assert summary["limits"]["max_requests_per_hour"] == 600
    
    def test_get_limits_info(self):
        """Test limits information retrieval."""
        api_key = APIKey(
            key="limits_test",
            name="Limits Test",
            max_patients_per_request=300,
            max_requests_per_day=750,
            max_requests_per_minute=45,
            max_requests_per_hour=900
        )
        
        limits = api_key.get_limits_info()
        
        assert limits["patients_per_request"] == 300
        assert limits["requests_per_day"] == 750
        assert limits["requests_per_minute"] == 45
        assert limits["requests_per_hour"] == 900
    
    def test_to_dict_conversion(self):
        """Test dictionary conversion."""
        created = datetime(2024, 1, 1, 9, 0, 0)
        updated = datetime(2024, 1, 15, 10, 0, 0)
        expires = datetime(2024, 12, 31, 23, 59, 59)
        last_used = datetime(2024, 1, 15, 8, 30, 0)
        
        api_key = APIKey(
            key="dict_test",
            name="Dict Test",
            email="dict@test.com",
            is_active=True,
            is_demo=False,
            created_at=created,
            updated_at=updated,
            expires_at=expires,
            last_used_at=last_used,
            max_patients_per_request=400,
            max_requests_per_day=800,
            total_requests=200,
            total_patients_generated=5000,
            daily_requests=30,
            key_metadata={"test": "value", "env": "test"}
        )
        
        # Mock the id since it's auto-generated
        api_key.id = "test-uuid-123"
        
        api_dict = api_key.to_dict()
        
        assert api_dict["id"] == "test-uuid-123"
        assert api_dict["name"] == "Dict Test"
        assert api_dict["email"] == "dict@test.com"
        assert api_dict["is_active"] is True
        assert api_dict["is_demo"] is False
        assert api_dict["created_at"] == created.isoformat()
        assert api_dict["updated_at"] == updated.isoformat()
        assert api_dict["expires_at"] == expires.isoformat()
        assert api_dict["last_used_at"] == last_used.isoformat()
        
        assert api_dict["limits"]["patients_per_request"] == 400
        assert api_dict["limits"]["requests_per_day"] == 800
        
        assert api_dict["usage"]["total_requests"] == 200
        assert api_dict["usage"]["total_patients_generated"] == 5000
        assert api_dict["usage"]["daily_requests"] == 30
        
        assert api_dict["metadata"]["test"] == "value"
        assert api_dict["metadata"]["env"] == "test"
    
    def test_to_dict_with_none_values(self):
        """Test dictionary conversion with None values."""
        api_key = APIKey(
            key="none_test",
            name="None Test",
            email=None,
            expires_at=None,
            last_used_at=None,
            max_requests_per_day=None
        )
        
        # Mock required fields
        api_key.id = "test-uuid-456"
        api_key.created_at = datetime(2024, 1, 1, 9, 0, 0)
        api_key.updated_at = datetime(2024, 1, 1, 9, 0, 0)
        
        api_dict = api_key.to_dict()
        
        assert api_dict["email"] is None
        assert api_dict["expires_at"] is None
        assert api_dict["last_used_at"] is None
        assert api_dict["limits"]["requests_per_day"] is None


class TestDemoKeyConfiguration:
    """Test demo key configuration constants."""
    
    def test_demo_key_config_structure(self):
        """Test that demo key config has all required fields."""
        config = DEMO_API_KEY_CONFIG
        
        required_fields = [
            "key", "name", "email", "is_demo",
            "max_patients_per_request", "max_requests_per_day",
            "max_requests_per_minute", "max_requests_per_hour"
        ]
        
        for field in required_fields:
            assert field in config, f"Missing required field: {field}"
    
    def test_demo_key_config_values(self):
        """Test demo key configuration values."""
        config = DEMO_API_KEY_CONFIG
        
        assert config["key"] == "DEMO_MILMED_2025_50_PATIENTS"
        assert config["name"] == "Public Demo Key"
        assert config["email"] is None
        assert config["is_demo"] is True
        assert config["max_patients_per_request"] == 50
        assert config["max_requests_per_day"] == 100
        assert config["max_requests_per_minute"] == 10
        assert config["max_requests_per_hour"] == 50
    
    def test_demo_key_security_limits(self):
        """Test that demo key has appropriately restrictive limits."""
        config = DEMO_API_KEY_CONFIG
        
        # Verify limits are restrictive for public use
        assert config["max_patients_per_request"] <= 50  # Limited patients
        assert config["max_requests_per_day"] <= 100     # Limited daily use
        assert config["max_requests_per_minute"] <= 10   # Limited rate
        assert config["max_requests_per_hour"] <= 50     # Limited hourly use
        
        # Verify it's clearly marked as demo
        assert config["is_demo"] is True
        assert "DEMO" in config["key"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])