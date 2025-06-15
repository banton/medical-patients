"""
Test API Key Management System

Tests for the complete API key management infrastructure including
models, repository, and security components.
"""

import pytest
from datetime import datetime, timedelta

from src.domain.models.api_key import APIKey, DEMO_API_KEY_CONFIG
from src.domain.repositories.api_key_repository import APIKeyRepository
from src.core.security_enhanced import APIKeyContext, DEMO_API_KEY


class TestAPIKeyModel:
    """Test the APIKey SQLAlchemy model."""
    
    def test_api_key_creation(self):
        """Test basic API key creation."""
        api_key = APIKey(
            key="sk_test_123456789",
            name="Test Key",
            email="test@example.com"
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
            key="expired", 
            name="Expired", 
            is_active=True,
            expires_at=datetime.utcnow() - timedelta(days=1)
        )
        assert expired_key.is_expired() is True
        assert expired_key.is_usable() is False
    
    def test_patient_limit_checking(self):
        """Test patient limit validation."""
        api_key = APIKey(
            key="test",
            name="Test",
            max_patients_per_request=100
        )
        
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
        
        # Fresh key doesn't need reset
        assert api_key.needs_daily_reset() is True  # No last_reset_at
        
        # Set reset to today
        api_key.last_reset_at = datetime.utcnow()
        assert api_key.needs_daily_reset() is False
        
        # Set reset to yesterday
        api_key.last_reset_at = datetime.utcnow() - timedelta(days=1)
        assert api_key.needs_daily_reset() is True


class TestAPIKeyRepository:
    """Test the API key repository functionality."""
    
    def test_create_api_key(self, api_key_repo):
        """Test API key creation via repository."""
        api_key = api_key_repo.create_api_key(
            name="Test Client",
            email="client@example.com",
            max_patients_per_request=500
        )
        
        assert api_key.name == "Test Client"
        assert api_key.email == "client@example.com"
        assert api_key.max_patients_per_request == 500
        assert api_key.key.startswith("sk_live_")
        assert len(api_key.key) == 64  # 8 + 56 chars
    
    def test_create_demo_key(self, api_key_repo):
        """Test demo key creation."""
        demo_key = api_key_repo.create_api_key(
            name="Demo Key",
            is_demo=True,
            max_patients_per_request=50
        )
        
        assert demo_key.is_demo is True
        assert demo_key.key.startswith("sk_demo_")
        assert demo_key.max_patients_per_request == 50
    
    def test_get_by_key(self, api_key_repo):
        """Test retrieving API key by key value."""
        # Create a test key
        original_key = api_key_repo.create_api_key(name="Lookup Test")
        
        # Retrieve by key
        found_key = api_key_repo.get_by_key(original_key.key)
        
        assert found_key is not None
        assert found_key.id == original_key.id
        assert found_key.name == "Lookup Test"
        
        # Test non-existent key
        not_found = api_key_repo.get_by_key("nonexistent")
        assert not_found is None
    
    def test_get_active_key(self, api_key_repo):
        """Test retrieving only active, non-expired keys."""
        # Create active key
        active_key = api_key_repo.create_api_key(name="Active Key")
        
        # Create inactive key
        inactive_key = api_key_repo.create_api_key(name="Inactive Key")
        api_key_repo.deactivate_key(str(inactive_key.id))
        
        # Test retrieval
        found_active = api_key_repo.get_active_key(active_key.key)
        assert found_active is not None
        assert found_active.is_active is True
        
        found_inactive = api_key_repo.get_active_key(inactive_key.key)
        assert found_inactive is None
    
    def test_usage_tracking(self, api_key_repo):
        """Test usage tracking through repository."""
        api_key = api_key_repo.create_api_key(name="Usage Tracking")
        
        # Record usage
        api_key_repo.update_usage(api_key, patients_generated=15)
        
        # Verify tracking
        updated_key = api_key_repo.get_by_key(api_key.key)
        assert updated_key.total_requests == 1
        assert updated_key.total_patients_generated == 15
        assert updated_key.daily_requests == 1
    
    def test_key_lifecycle_management(self, api_key_repo):
        """Test deactivating, activating, and deleting keys."""
        api_key = api_key_repo.create_api_key(name="Lifecycle Test")
        key_id = str(api_key.id)
        
        # Test deactivation
        assert api_key_repo.deactivate_key(key_id) is True
        deactivated = api_key_repo.get_by_id(key_id)
        assert deactivated.is_active is False
        
        # Test reactivation
        assert api_key_repo.activate_key(key_id) is True
        reactivated = api_key_repo.get_by_id(key_id)
        assert reactivated.is_active is True
        
        # Test deletion
        assert api_key_repo.delete_key(key_id) is True
        deleted = api_key_repo.get_by_id(key_id)
        assert deleted is None
    
    def test_list_keys_filtering(self, api_key_repo):
        """Test listing keys with filtering options."""
        # Create test keys
        live_key = api_key_repo.create_api_key(name="Live Key", is_demo=False)
        demo_key = api_key_repo.create_api_key(name="Demo Key", is_demo=True)
        api_key_repo.deactivate_key(str(demo_key.id))
        
        # Test listing all active keys
        active_keys = api_key_repo.list_keys(active_only=True)
        active_names = [key.name for key in active_keys]
        assert "Live Key" in active_names
        assert "Demo Key" not in active_names
        
        # Test listing demo keys only
        demo_keys = api_key_repo.list_keys(demo_only=True, active_only=False)
        demo_names = [key.name for key in demo_keys]
        assert "Demo Key" in demo_names
        assert "Live Key" not in demo_names
    
    def test_search_functionality(self, api_key_repo):
        """Test key search by name and email."""
        api_key_repo.create_api_key(name="Searchable Client", email="search@test.com")
        api_key_repo.create_api_key(name="Other Client", email="other@test.com")
        
        # Search by name
        name_results = api_key_repo.search_keys("Searchable")
        assert len(name_results) == 1
        assert name_results[0].name == "Searchable Client"
        
        # Search by email
        email_results = api_key_repo.search_keys("search@test.com")
        assert len(email_results) == 1
        assert email_results[0].email == "search@test.com"
    
    def test_demo_key_creation(self, api_key_repo):
        """Test automatic demo key creation."""
        # Should create the standard demo key
        demo_key = api_key_repo.create_demo_key_if_not_exists()
        
        assert demo_key.key == DEMO_API_KEY_CONFIG["key"]
        assert demo_key.name == DEMO_API_KEY_CONFIG["name"]
        assert demo_key.is_demo is True
        assert demo_key.max_patients_per_request == 50
        
        # Should return existing key on second call
        same_demo_key = api_key_repo.create_demo_key_if_not_exists()
        assert same_demo_key.id == demo_key.id


class TestAPIKeyContext:
    """Test the API key context and security functionality."""
    
    def test_context_creation(self):
        """Test creating API key context."""
        api_key = APIKey(
            key="test_context",
            name="Context Test",
            max_patients_per_request=100
        )
        
        context = APIKeyContext(api_key=api_key, is_demo=False)
        
        assert context.api_key == api_key
        assert context.is_demo is False
        assert context.is_legacy is False
    
    def test_patient_limit_enforcement(self):
        """Test patient limit checking in context."""
        api_key = APIKey(
            key="limit_test",
            name="Limit Test",
            max_patients_per_request=50
        )
        context = APIKeyContext(api_key=api_key)
        
        # Should pass
        try:
            context.check_patient_limit(25)
            context.check_patient_limit(50)
        except Exception:
            pytest.fail("Valid patient limits should not raise exceptions")
        
        # Should fail
        with pytest.raises(Exception) as exc_info:
            context.check_patient_limit(51)
        assert "exceeds limit" in str(exc_info.value)
    
    def test_daily_limit_enforcement(self):
        """Test daily limit checking in context."""
        # Key under daily limit
        under_limit_key = APIKey(
            key="under_limit",
            name="Under Limit",
            max_requests_per_day=100,
            daily_requests=50
        )
        under_context = APIKeyContext(api_key=under_limit_key)
        
        try:
            under_context.check_daily_limit()
        except Exception:
            pytest.fail("Under daily limit should not raise exception")
        
        # Key at daily limit
        at_limit_key = APIKey(
            key="at_limit",
            name="At Limit",
            max_requests_per_day=100,
            daily_requests=100
        )
        at_context = APIKeyContext(api_key=at_limit_key)
        
        with pytest.raises(Exception) as exc_info:
            at_context.check_daily_limit()
        assert "Daily request limit exceeded" in str(exc_info.value)
    
    def test_response_headers_generation(self):
        """Test generating response headers from context."""
        api_key = APIKey(
            key="headers_test",
            name="Headers Test",
            max_patients_per_request=100,
            max_requests_per_day=1000,
            daily_requests=50,
            is_demo=True
        )
        context = APIKeyContext(api_key=api_key, is_demo=True)
        
        headers = context.get_response_headers()
        
        assert headers["X-API-Key-Type"] == "demo"
        assert headers["X-Patient-Limit"] == "100"
        assert headers["X-Daily-Limit"] == "1000"
        assert headers["X-Daily-Usage"] == "50"


class TestSecurityIntegration:
    """Test the complete security integration."""
    
    def test_demo_key_constants(self):
        """Test demo key configuration consistency."""
        assert DEMO_API_KEY == "DEMO_MILMED_2025_50_PATIENTS"
        assert DEMO_API_KEY_CONFIG["key"] == DEMO_API_KEY
        assert DEMO_API_KEY_CONFIG["max_patients_per_request"] == 50
        assert DEMO_API_KEY_CONFIG["is_demo"] is True
    
    def test_context_limits_info(self):
        """Test context limits information retrieval."""
        api_key = APIKey(
            key="limits_info",
            name="Limits Info Test",
            max_patients_per_request=200,
            max_requests_per_day=500,
            total_requests=150,
            daily_requests=25
        )
        context = APIKeyContext(api_key=api_key)
        
        limits_info = context.get_limits_info()
        
        assert limits_info["patients_per_request"] == 200
        assert limits_info["requests_per_day"] == 500
        assert limits_info["total_usage"] == 150
        assert limits_info["daily_usage"] == 25


if __name__ == "__main__":
    pytest.main([__file__, "-v"])