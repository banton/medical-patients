"""
Unit tests for APIKeyRepository business logic.

These tests focus on the business logic and validation in the repository
without requiring actual database connections. Database interactions are mocked.
"""

from datetime import datetime, timedelta
from unittest.mock import Mock, call, patch

import pytest

from src.domain.models.api_key import DEMO_API_KEY_CONFIG, APIKey
from src.domain.repositories.api_key_repository import APIKeyRepository


class TestAPIKeyRepositoryKeyGeneration:
    """Test API key generation logic."""

    @patch("src.domain.repositories.api_key_repository.secrets")
    def test_create_api_key_live_key_format(self, mock_secrets):
        """Test live API key format generation."""
        mock_secrets.token_hex.return_value = "a" * 56  # 56 chars
        mock_db = Mock()
        repo = APIKeyRepository(mock_db)

        # Mock successful database operations
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()

        result = repo.create_api_key(name="Test Key", is_demo=False)

        # Verify key format
        assert result.key.startswith("sk_live_")
        assert len(result.key) == 64  # 8 + 56 chars
        assert result.key == "sk_live_" + "a" * 56

        # Verify other properties
        assert result.name == "Test Key"
        assert result.is_demo is False

        # Verify database operations
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    @patch("src.domain.repositories.api_key_repository.secrets")
    def test_create_api_key_demo_key_format(self, mock_secrets):
        """Test demo API key format generation."""
        mock_secrets.token_hex.return_value = "b" * 56  # 56 chars
        mock_db = Mock()
        repo = APIKeyRepository(mock_db)

        # Mock successful database operations
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()

        result = repo.create_api_key(name="Demo Key", is_demo=True)

        # Verify key format
        assert result.key.startswith("sk_demo_")
        assert len(result.key) == 64  # 8 + 56 chars total
        assert result.key == "sk_demo_" + "b" * 56  # token_hex(28) = 56 chars

        # Verify other properties
        assert result.name == "Demo Key"
        assert result.is_demo is True

    def test_create_api_key_with_all_parameters(self):
        """Test creating API key with all parameters specified."""
        mock_db = Mock()
        repo = APIKeyRepository(mock_db)

        # Mock successful database operations
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()

        expires_date = datetime.utcnow() + timedelta(days=365)
        metadata = {"created_by": "test", "purpose": "testing"}

        result = repo.create_api_key(
            name="Full Test Key",
            email="test@example.com",
            is_demo=False,
            max_patients_per_request=500,
            max_requests_per_day=1000,
            max_requests_per_minute=30,
            max_requests_per_hour=600,
            expires_at=expires_date,
            metadata=metadata,
        )

        # Verify all parameters were set
        assert result.name == "Full Test Key"
        assert result.email == "test@example.com"
        assert result.is_demo is False
        assert result.max_patients_per_request == 500
        assert result.max_requests_per_day == 1000
        assert result.max_requests_per_minute == 30
        assert result.max_requests_per_hour == 600
        assert result.expires_at == expires_date
        assert result.key_metadata == metadata

    @patch("src.domain.repositories.api_key_repository.secrets")
    def test_create_api_key_handles_collision(self, mock_secrets):
        """Test handling of extremely rare key collision."""
        from sqlalchemy.exc import IntegrityError

        mock_secrets.token_hex.side_effect = ["collision", "unique_key"]
        mock_db = Mock()
        repo = APIKeyRepository(mock_db)

        # Mock collision on first attempt, success on second
        mock_db.add = Mock()
        mock_db.commit = Mock(side_effect=[IntegrityError("", "", ""), None])
        mock_db.rollback = Mock()
        mock_db.refresh = Mock()

        result = repo.create_api_key(name="Collision Test")

        # Verify retry occurred
        assert mock_secrets.token_hex.call_count == 2
        assert mock_db.rollback.called
        assert result.key.endswith("unique_key")


class TestAPIKeyRepositoryQueryLogic:
    """Test query and filtering logic."""

    def test_get_by_key_query_structure(self):
        """Test get_by_key query structure."""
        mock_db = Mock()
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = "result"

        repo = APIKeyRepository(mock_db)
        result = repo.get_by_key("test_key")

        # Verify query structure
        mock_db.query.assert_called_once_with(APIKey)
        mock_query.filter.assert_called_once()
        mock_query.first.assert_called_once()
        assert result == "result"

    def test_get_by_id_query_structure(self):
        """Test get_by_id query structure."""
        mock_db = Mock()
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = "result"

        repo = APIKeyRepository(mock_db)
        result = repo.get_by_id("test-uuid")

        # Verify query structure
        mock_db.query.assert_called_once_with(APIKey)
        mock_query.filter.assert_called_once()
        mock_query.first.assert_called_once()
        assert result == "result"

    def test_get_active_key_with_reset_needed(self):
        """Test get_active_key when daily reset is needed."""
        mock_db = Mock()
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query

        # Create mock key that needs reset
        mock_key = Mock()
        mock_key.needs_daily_reset.return_value = True
        mock_key.reset_daily_counters = Mock()
        mock_query.first.return_value = mock_key

        mock_db.commit = Mock()

        repo = APIKeyRepository(mock_db)
        result = repo.get_active_key("test_key")

        # Verify reset was called
        mock_key.needs_daily_reset.assert_called_once()
        mock_key.reset_daily_counters.assert_called_once()
        mock_db.commit.assert_called_once()
        assert result == mock_key

    def test_get_active_key_no_reset_needed(self):
        """Test get_active_key when no reset is needed."""
        mock_db = Mock()
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query

        # Create mock key that doesn't need reset
        mock_key = Mock()
        mock_key.needs_daily_reset.return_value = False
        mock_key.reset_daily_counters = Mock()
        mock_query.first.return_value = mock_key

        mock_db.commit = Mock()

        repo = APIKeyRepository(mock_db)
        result = repo.get_active_key("test_key")

        # Verify reset was NOT called
        mock_key.needs_daily_reset.assert_called_once()
        mock_key.reset_daily_counters.assert_not_called()
        mock_db.commit.assert_not_called()
        assert result == mock_key


class TestAPIKeyRepositoryFilteringLogic:
    """Test filtering and search logic."""

    def test_list_keys_active_only_filter(self):
        """Test list_keys with active_only filter."""
        mock_db = Mock()
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = ["result1", "result2"]

        repo = APIKeyRepository(mock_db)
        result = repo.list_keys(active_only=True, demo_only=None)

        # Verify filtering was applied
        assert mock_query.filter.call_count == 1  # Only active filter
        mock_query.order_by.assert_called_once()
        mock_query.offset.assert_called_once_with(0)
        mock_query.limit.assert_called_once_with(100)
        assert result == ["result1", "result2"]

    def test_list_keys_demo_only_filter(self):
        """Test list_keys with demo_only filter."""
        mock_db = Mock()
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        repo = APIKeyRepository(mock_db)
        result = repo.list_keys(active_only=True, demo_only=True, limit=50, offset=10)

        # Verify both filters were applied
        assert mock_query.filter.call_count == 2  # Active + demo filters
        mock_query.offset.assert_called_once_with(10)
        mock_query.limit.assert_called_once_with(50)

    def test_search_keys_query_pattern(self):
        """Test search_keys query pattern construction."""
        mock_db = Mock()
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = ["search_result"]

        repo = APIKeyRepository(mock_db)
        result = repo.search_keys("test search", limit=25)

        # Verify search was performed
        mock_db.query.assert_called_once_with(APIKey)
        mock_query.filter.assert_called_once()  # OR filter for name/email
        mock_query.order_by.assert_called_once()
        mock_query.limit.assert_called_once_with(25)
        assert result == ["search_result"]


class TestAPIKeyRepositoryUsageTracking:
    """Test usage tracking and update logic."""

    def test_update_usage_calls_record_usage(self):
        """Test that update_usage calls the model's record_usage method."""
        mock_db = Mock()
        mock_db.commit = Mock()

        mock_api_key = Mock()
        mock_api_key.record_usage = Mock()

        repo = APIKeyRepository(mock_db)
        repo.update_usage(mock_api_key, patients_generated=25)

        # Verify model method was called
        mock_api_key.record_usage.assert_called_once_with(25)
        mock_db.commit.assert_called_once()

    def test_increment_request_count_logic(self):
        """Test increment_request_count logic."""
        mock_db = Mock()
        mock_db.commit = Mock()

        mock_api_key = Mock()
        mock_api_key.total_requests = 100
        mock_api_key.daily_requests = 25

        with patch("src.domain.repositories.api_key_repository.datetime") as mock_datetime:
            fixed_time = datetime(2024, 1, 15, 12, 0, 0)
            mock_datetime.utcnow.return_value = fixed_time

            repo = APIKeyRepository(mock_db)
            repo.increment_request_count(mock_api_key)

        # Verify counters were incremented
        assert mock_api_key.total_requests == 101
        assert mock_api_key.daily_requests == 26
        assert mock_api_key.last_used_at == fixed_time
        assert mock_api_key.updated_at == fixed_time
        mock_db.commit.assert_called_once()


class TestAPIKeyRepositoryStateManagement:
    """Test key state management (activate/deactivate/delete)."""

    def test_deactivate_key_by_id_success(self):
        """Test successful key deactivation by ID."""
        mock_db = Mock()
        mock_db.commit = Mock()

        mock_key = Mock()
        mock_key.is_active = True

        repo = APIKeyRepository(mock_db)
        repo.get_by_id = Mock(return_value=mock_key)
        repo.get_by_key = Mock(return_value=None)

        with patch("src.domain.repositories.api_key_repository.datetime") as mock_datetime:
            fixed_time = datetime(2024, 1, 15, 12, 0, 0)
            mock_datetime.utcnow.return_value = fixed_time

            result = repo.deactivate_key("test-id")

        assert result is True
        assert mock_key.is_active is False
        assert mock_key.updated_at == fixed_time
        mock_db.commit.assert_called_once()

    def test_deactivate_key_by_key_success(self):
        """Test successful key deactivation by key string."""
        mock_db = Mock()
        mock_db.commit = Mock()

        mock_key = Mock()
        mock_key.is_active = True

        repo = APIKeyRepository(mock_db)
        repo.get_by_id = Mock(return_value=None)
        repo.get_by_key = Mock(return_value=mock_key)

        result = repo.deactivate_key("sk_test_123")

        assert result is True
        assert mock_key.is_active is False
        mock_db.commit.assert_called_once()

    def test_deactivate_key_not_found(self):
        """Test key deactivation when key is not found."""
        mock_db = Mock()

        repo = APIKeyRepository(mock_db)
        repo.get_by_id = Mock(return_value=None)
        repo.get_by_key = Mock(return_value=None)

        result = repo.deactivate_key("nonexistent")

        assert result is False
        mock_db.commit.assert_not_called()

    def test_activate_key_success(self):
        """Test successful key activation."""
        mock_db = Mock()
        mock_db.commit = Mock()

        mock_key = Mock()
        mock_key.is_active = False

        repo = APIKeyRepository(mock_db)
        repo.get_by_id = Mock(return_value=mock_key)
        repo.get_by_key = Mock(return_value=None)

        result = repo.activate_key("test-id")

        assert result is True
        assert mock_key.is_active is True
        mock_db.commit.assert_called_once()

    def test_delete_key_success(self):
        """Test successful key deletion."""
        mock_db = Mock()
        mock_db.delete = Mock()
        mock_db.commit = Mock()

        mock_key = Mock()

        repo = APIKeyRepository(mock_db)
        repo.get_by_id = Mock(return_value=mock_key)
        repo.get_by_key = Mock(return_value=None)

        result = repo.delete_key("test-id")

        assert result is True
        mock_db.delete.assert_called_once_with(mock_key)
        mock_db.commit.assert_called_once()


class TestAPIKeyRepositoryLimitUpdates:
    """Test limit update functionality."""

    def test_update_limits_partial_update(self):
        """Test updating only some limits."""
        mock_db = Mock()
        mock_db.commit = Mock()

        mock_key = Mock()
        mock_key.max_patients_per_request = 1000
        mock_key.max_requests_per_day = 5000
        mock_key.max_requests_per_minute = 60
        mock_key.max_requests_per_hour = 1000

        repo = APIKeyRepository(mock_db)
        repo.get_by_id = Mock(return_value=mock_key)
        repo.get_by_key = Mock(return_value=None)

        with patch("src.domain.repositories.api_key_repository.datetime") as mock_datetime:
            fixed_time = datetime(2024, 1, 15, 12, 0, 0)
            mock_datetime.utcnow.return_value = fixed_time

            result = repo.update_limits(
                "test-id",
                max_patients_per_request=500,
                max_requests_per_minute=30,
                # Note: not updating daily or hourly limits
            )

        assert result is True
        assert mock_key.max_patients_per_request == 500
        assert mock_key.max_requests_per_day == 5000  # Unchanged
        assert mock_key.max_requests_per_minute == 30
        assert mock_key.max_requests_per_hour == 1000  # Unchanged
        assert mock_key.updated_at == fixed_time
        mock_db.commit.assert_called_once()

    def test_update_limits_not_found(self):
        """Test updating limits for non-existent key."""
        mock_db = Mock()

        repo = APIKeyRepository(mock_db)
        repo.get_by_id = Mock(return_value=None)
        repo.get_by_key = Mock(return_value=None)

        result = repo.update_limits("nonexistent", max_patients_per_request=500)

        assert result is False
        mock_db.commit.assert_not_called()


class TestAPIKeyRepositoryExpirationManagement:
    """Test expiration date management."""

    def test_extend_expiration_existing_expiration(self):
        """Test extending expiration when key already has expiration."""
        mock_db = Mock()
        mock_db.commit = Mock()

        original_expiration = datetime(2024, 6, 1, 0, 0, 0)
        mock_key = Mock()
        mock_key.expires_at = original_expiration

        repo = APIKeyRepository(mock_db)
        repo.get_by_id = Mock(return_value=mock_key)
        repo.get_by_key = Mock(return_value=None)

        result = repo.extend_expiration("test-id", days=30)

        expected_expiration = original_expiration + timedelta(days=30)
        assert result is True
        assert mock_key.expires_at == expected_expiration
        mock_db.commit.assert_called_once()

    def test_extend_expiration_no_existing_expiration(self):
        """Test extending expiration when key has no expiration."""
        mock_db = Mock()
        mock_db.commit = Mock()

        mock_key = Mock()
        mock_key.expires_at = None

        repo = APIKeyRepository(mock_db)
        repo.get_by_id = Mock(return_value=mock_key)
        repo.get_by_key = Mock(return_value=None)

        with patch("src.domain.repositories.api_key_repository.datetime") as mock_datetime:
            current_time = datetime(2024, 1, 15, 12, 0, 0)
            mock_datetime.utcnow.return_value = current_time

            result = repo.extend_expiration("test-id", days=365)

        expected_expiration = current_time + timedelta(days=365)
        assert result is True
        assert mock_key.expires_at == expected_expiration
        mock_db.commit.assert_called_once()


class TestAPIKeyRepositoryDemoKeyManagement:
    """Test demo key creation and management."""

    def test_create_demo_key_if_not_exists_new_key(self):
        """Test creating demo key when it doesn't exist."""
        mock_db = Mock()
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()

        repo = APIKeyRepository(mock_db)
        repo.get_by_key = Mock(return_value=None)  # Key doesn't exist

        result = repo.create_demo_key_if_not_exists()

        # Verify new key was created
        assert result.key == DEMO_API_KEY_CONFIG["key"]
        assert result.name == DEMO_API_KEY_CONFIG["name"]
        assert result.is_demo is True
        assert result.max_patients_per_request == 50
        assert result.key_metadata["auto_created"] is True
        assert result.key_metadata["public_demo"] is True

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    def test_create_demo_key_if_not_exists_existing_key(self):
        """Test creating demo key when it already exists."""
        mock_db = Mock()
        existing_key = Mock()

        repo = APIKeyRepository(mock_db)
        repo.get_by_key = Mock(return_value=existing_key)  # Key exists

        result = repo.create_demo_key_if_not_exists()

        # Verify existing key was returned
        assert result == existing_key
        mock_db.add.assert_not_called()
        mock_db.commit.assert_not_called()


class TestAPIKeyRepositoryStatistics:
    """Test statistics and reporting functionality."""

    def test_get_usage_stats_calculation(self):
        """Test usage statistics calculation logic."""
        mock_db = Mock()

        # Mock recent keys with usage
        mock_key1 = Mock()
        mock_key1.total_requests = 100
        mock_key1.total_patients_generated = 2000

        mock_key2 = Mock()
        mock_key2.total_requests = 50
        mock_key2.total_patients_generated = 1000

        recent_keys = [mock_key1, mock_key2]

        # Mock query builder
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = recent_keys
        mock_query.count.side_effect = [10, 8, 3]  # total, active, demo

        repo = APIKeyRepository(mock_db)

        with patch("src.domain.repositories.api_key_repository.datetime") as mock_datetime:
            current_time = datetime(2024, 1, 15, 12, 0, 0)
            mock_datetime.utcnow.return_value = current_time

            stats = repo.get_usage_stats(days=30)

        # Verify calculations
        assert stats["total_keys"] == 10
        assert stats["active_keys"] == 8
        assert stats["demo_keys"] == 3
        assert stats["live_keys"] == 7  # total - demo
        assert stats["recently_used_keys"] == 2
        assert stats["total_requests_all_time"] == 150  # 100 + 50
        assert stats["total_patients_all_time"] == 3000  # 2000 + 1000
        assert stats["period_days"] == 30

    def test_cleanup_expired_keys_dry_run(self):
        """Test cleanup of expired keys in dry run mode."""
        mock_db = Mock()

        expired_key1 = Mock()
        expired_key1.name = "Expired Key 1"
        expired_key2 = Mock()
        expired_key2.name = "Expired Key 2"

        expired_keys = [expired_key1, expired_key2]

        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = expired_keys

        repo = APIKeyRepository(mock_db)
        result = repo.cleanup_expired_keys(dry_run=True)

        # Verify keys were identified but not deleted
        assert result == ["Expired Key 1", "Expired Key 2"]
        mock_db.delete.assert_not_called()
        mock_db.commit.assert_not_called()

    def test_cleanup_expired_keys_actual_cleanup(self):
        """Test actual cleanup of expired keys."""
        mock_db = Mock()
        mock_db.delete = Mock()
        mock_db.commit = Mock()

        expired_key1 = Mock()
        expired_key1.name = "Expired Key 1"
        expired_key2 = Mock()
        expired_key2.name = "Expired Key 2"

        expired_keys = [expired_key1, expired_key2]

        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = expired_keys

        repo = APIKeyRepository(mock_db)
        result = repo.cleanup_expired_keys(dry_run=False)

        # Verify keys were deleted
        assert result == ["Expired Key 1", "Expired Key 2"]
        assert mock_db.delete.call_count == 2
        mock_db.delete.assert_has_calls([call(expired_key1), call(expired_key2)])
        mock_db.commit.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
