"""
Integration Tests for API Key CLI Tool

This module contains integration tests that validate CLI commands with real database
operations using testcontainers. Tests focus on:
- Database operations with PostgreSQL testcontainers
- Command workflows with real data persistence
- Transaction behavior and rollback scenarios
- Concurrent access patterns
- Search and filtering functionality with real queries

Following TDD principles with actual database validation.
"""

import asyncio
from datetime import datetime, timedelta
import json
from pathlib import Path

# Import the CLI module and dependencies
import sys

from click.testing import CliRunner
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.api_key_cli import main
from src.domain.repositories.api_key_repository import APIKeyRepository


@pytest.mark.integration()
@pytest.mark.requires_docker()
class TestAPIKeyCLIIntegration:
    """Integration tests with real database operations."""

    @pytest.fixture()
    async def db_engine(self, test_database_url):
        """Create async database engine for CLI testing."""
        engine = create_async_engine(test_database_url, echo=False)
        yield engine
        await engine.dispose()

    @pytest.fixture()
    async def db_session(self, db_engine):
        """Create async database session for each test."""
        session_factory = sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
        async with session_factory() as session:
            yield session

    @pytest.fixture()
    async def repository(self, db_session):
        """Create API key repository for testing."""
        return APIKeyRepository(db_session)

    @pytest.fixture()
    def cli_runner(self):
        """Create Click test runner."""
        return CliRunner()

    @pytest.fixture()
    async def sample_api_keys(self, repository):
        """Create sample API keys for testing."""
        keys = []

        # Create test keys with different characteristics
        key_configs = [
            {
                "name": "Development Key",
                "email": "dev@example.com",
                "is_demo": False,
                "max_patients_per_request": 1000,
                "max_requests_per_day": 500,
            },
            {
                "name": "Demo Key",
                "email": "demo@example.com",
                "is_demo": True,
                "max_patients_per_request": 100,
                "max_requests_per_day": 50,
            },
            {
                "name": "Production Key",
                "email": "prod@example.com",
                "is_demo": False,
                "expires_at": datetime.utcnow() + timedelta(days=90),
                "max_patients_per_request": 5000,
                "max_requests_per_day": None,  # Unlimited
            },
            {
                "name": "Expired Key",
                "email": "expired@example.com",
                "is_demo": False,
                "expires_at": datetime.utcnow() - timedelta(days=1),
                "max_patients_per_request": 1000,
                "max_requests_per_day": 100,
            },
        ]

        for config in key_configs:
            key = await repository.create_api_key(**config)
            keys.append(key)

        return keys

    @pytest.fixture()
    def patch_cli_database(self, db_session, monkeypatch):
        """Patch CLI database connection to use test database."""

        async def mock_initialize():
            # Mock the CLI app initialization to use test database
            pass

        async def mock_cleanup():
            # Mock cleanup
            pass

        def mock_session_factory():
            # Return a context manager that yields the test session
            class MockSessionContext:
                async def __aenter__(self):
                    return db_session

                async def __aexit__(self, exc_type, exc_val, exc_tb):
                    pass

            return MockSessionContext()

        monkeypatch.setattr("scripts.api_key_cli.cli_app.initialize", mock_initialize)
        monkeypatch.setattr("scripts.api_key_cli.cli_app.cleanup", mock_cleanup)
        monkeypatch.setattr("scripts.api_key_cli.cli_app.session_factory", mock_session_factory)
        monkeypatch.setattr("scripts.api_key_cli.APIKeyRepository", lambda session: repository)


@pytest.mark.integration()
@pytest.mark.requires_docker()
class TestCLICreateOperations(TestAPIKeyCLIIntegration):
    """Test CLI create operations with real database."""

    async def test_create_basic_api_key(self, cli_runner, patch_cli_database, repository):
        """Test creating a basic API key with real database persistence."""
        result = cli_runner.invoke(
            main, ["create", "--name", "Integration Test Key", "--email", "integration@test.com", "--format", "json"]
        )

        assert result.exit_code == 0

        # Parse JSON output
        output_data = json.loads(result.output)
        assert output_data["name"] == "Integration Test Key"
        assert output_data["email"] == "integration@test.com"
        assert "key" in output_data
        assert "id" in output_data

        # Verify key was actually created in database
        created_key = await repository.get_by_id(output_data["id"])
        assert created_key is not None
        assert created_key.name == "Integration Test Key"
        assert created_key.email == "integration@test.com"
        assert created_key.is_active is True

    async def test_create_demo_key_with_limits(self, cli_runner, patch_cli_database, repository):
        """Test creating a demo key with custom limits."""
        result = cli_runner.invoke(
            main,
            [
                "create",
                "--name",
                "Demo Integration Key",
                "--demo",
                "--patients",
                "200",
                "--daily",
                "100",
                "--hourly",
                "50",
                "--minute",
                "5",
                "--format",
                "json",
            ],
        )

        assert result.exit_code == 0

        # Parse output and verify database
        output_data = json.loads(result.output)
        created_key = await repository.get_by_id(output_data["id"])

        assert created_key.is_demo is True
        assert created_key.max_patients_per_request == 200
        assert created_key.max_requests_per_day == 100
        assert created_key.max_requests_per_hour == 50
        assert created_key.max_requests_per_minute == 5

    async def test_create_key_with_expiration(self, cli_runner, patch_cli_database, repository):
        """Test creating a key with expiration date."""
        result = cli_runner.invoke(
            main, ["create", "--name", "Expiring Key", "--expires-days", "30", "--format", "json"]
        )

        assert result.exit_code == 0

        # Verify expiration was set correctly
        output_data = json.loads(result.output)
        created_key = await repository.get_by_id(output_data["id"])

        assert created_key.expires_at is not None
        expected_expiry = datetime.utcnow() + timedelta(days=30)
        time_diff = abs((created_key.expires_at - expected_expiry).total_seconds())
        assert time_diff < 60  # Within 1 minute tolerance


@pytest.mark.integration()
@pytest.mark.requires_docker()
class TestCLIListOperations(TestAPIKeyCLIIntegration):
    """Test CLI list operations with real database queries."""

    async def test_list_all_keys(self, cli_runner, patch_cli_database, sample_api_keys):
        """Test listing all API keys."""
        result = cli_runner.invoke(main, ["list", "--format", "json"])

        assert result.exit_code == 0

        # Parse output and verify all keys are returned
        output_data = json.loads(result.output)
        assert len(output_data) == len(sample_api_keys)

        # Verify key data is correct
        key_names = [key["name"] for key in output_data]
        assert "Development Key" in key_names
        assert "Demo Key" in key_names
        assert "Production Key" in key_names
        assert "Expired Key" in key_names

    async def test_list_active_keys_only(self, cli_runner, patch_cli_database, sample_api_keys):
        """Test listing only active API keys."""
        result = cli_runner.invoke(main, ["list", "--active", "--format", "json"])

        assert result.exit_code == 0

        # All test keys should be active by default
        output_data = json.loads(result.output)
        assert len(output_data) == len(sample_api_keys)

        # Verify all returned keys are active
        for key in output_data:
            assert key["is_active"] is True

    async def test_list_demo_keys_only(self, cli_runner, patch_cli_database, sample_api_keys):
        """Test listing only demo API keys."""
        result = cli_runner.invoke(main, ["list", "--demo", "--format", "json"])

        assert result.exit_code == 0

        # Only one demo key in sample data
        output_data = json.loads(result.output)
        assert len(output_data) == 1
        assert output_data[0]["name"] == "Demo Key"
        assert output_data[0]["is_demo"] is True

    async def test_list_with_search_filter(self, cli_runner, patch_cli_database, sample_api_keys):
        """Test listing with search filter."""
        result = cli_runner.invoke(main, ["list", "--search", "Demo", "--format", "json"])

        assert result.exit_code == 0

        # Should find the Demo Key
        output_data = json.loads(result.output)
        assert len(output_data) == 1
        assert output_data[0]["name"] == "Demo Key"

    async def test_list_with_email_search(self, cli_runner, patch_cli_database, sample_api_keys):
        """Test listing with email search filter."""
        result = cli_runner.invoke(main, ["list", "--search", "prod@example.com", "--format", "json"])

        assert result.exit_code == 0

        # Should find the Production Key
        output_data = json.loads(result.output)
        assert len(output_data) == 1
        assert output_data[0]["name"] == "Production Key"
        assert output_data[0]["email"] == "prod@example.com"

    async def test_list_csv_format(self, cli_runner, patch_cli_database, sample_api_keys):
        """Test list command CSV output format."""
        result = cli_runner.invoke(main, ["list", "--format", "csv"])

        assert result.exit_code == 0

        # Verify CSV format
        lines = result.output.strip().split("\n")
        assert len(lines) >= 2  # Header + at least one data row

        # Check header
        header = lines[0]
        assert "ID" in header
        assert "Name" in header
        assert "Email" in header
        assert "Active" in header

        # Check data rows contain expected content
        csv_content = result.output
        assert "Development Key" in csv_content
        assert "Demo Key" in csv_content


@pytest.mark.integration()
@pytest.mark.requires_docker()
class TestCLIShowOperations(TestAPIKeyCLIIntegration):
    """Test CLI show operations with real database queries."""

    async def test_show_key_by_id(self, cli_runner, patch_cli_database, sample_api_keys):
        """Test showing API key details by ID."""
        target_key = sample_api_keys[0]  # Development Key

        result = cli_runner.invoke(main, ["show", str(target_key.id), "--format", "json"])

        assert result.exit_code == 0

        # Verify output contains correct key details
        output_data = json.loads(result.output)
        assert output_data["name"] == "Development Key"
        assert output_data["email"] == "dev@example.com"
        assert output_data["is_demo"] is False
        assert "usage" in output_data
        assert "limits" in output_data
        assert "metadata" in output_data

    async def test_show_nonexistent_key(self, cli_runner, patch_cli_database, sample_api_keys):
        """Test showing nonexistent API key."""
        fake_id = "00000000-0000-0000-0000-000000000000"

        result = cli_runner.invoke(main, ["show", fake_id])

        assert result.exit_code == 1
        assert "API key not found" in result.output

    async def test_show_key_table_format(self, cli_runner, patch_cli_database, sample_api_keys):
        """Test show command with table format."""
        target_key = sample_api_keys[0]

        result = cli_runner.invoke(main, ["show", str(target_key.id)])

        assert result.exit_code == 0
        assert "API Key Details" in result.output
        assert "Development Key" in result.output
        assert "dev@example.com" in result.output


@pytest.mark.integration()
@pytest.mark.requires_docker()
class TestCLIActivationOperations(TestAPIKeyCLIIntegration):
    """Test CLI activation/deactivation operations with real database."""

    async def test_deactivate_and_activate_key(self, cli_runner, patch_cli_database, sample_api_keys, repository):
        """Test deactivating and reactivating an API key."""
        target_key = sample_api_keys[0]
        key_id = str(target_key.id)

        # Deactivate the key
        result = cli_runner.invoke(main, ["deactivate", key_id])

        assert result.exit_code == 0
        assert "deactivated successfully" in result.output

        # Verify in database
        updated_key = await repository.get_by_id(target_key.id)
        assert updated_key.is_active is False

        # Reactivate the key
        result = cli_runner.invoke(main, ["activate", key_id])

        assert result.exit_code == 0
        assert "activated successfully" in result.output

        # Verify in database
        updated_key = await repository.get_by_id(target_key.id)
        assert updated_key.is_active is True

    async def test_activate_already_active_key(self, cli_runner, patch_cli_database, sample_api_keys):
        """Test activating an already active key."""
        target_key = sample_api_keys[0]  # Should be active by default

        result = cli_runner.invoke(main, ["activate", str(target_key.id)])

        assert result.exit_code == 0
        assert "already active" in result.output

    async def test_deactivate_already_inactive_key(self, cli_runner, patch_cli_database, sample_api_keys, repository):
        """Test deactivating an already inactive key."""
        target_key = sample_api_keys[0]
        key_id = str(target_key.id)

        # First deactivate it
        await repository.deactivate_key(target_key.id)

        # Try to deactivate again
        result = cli_runner.invoke(main, ["deactivate", key_id])

        assert result.exit_code == 0
        assert "already inactive" in result.output


@pytest.mark.integration()
@pytest.mark.requires_docker()
class TestCLIDeleteOperations(TestAPIKeyCLIIntegration):
    """Test CLI delete operations with real database."""

    async def test_delete_key_with_confirmation(self, cli_runner, patch_cli_database, sample_api_keys, repository):
        """Test deleting an API key with confirmation flag."""
        target_key = sample_api_keys[0]
        key_id = str(target_key.id)

        # Delete with --confirm flag to skip prompt
        result = cli_runner.invoke(main, ["delete", key_id, "--confirm"])

        assert result.exit_code == 0
        assert "deleted successfully" in result.output

        # Verify key is actually deleted from database
        deleted_key = await repository.get_by_id(target_key.id)
        assert deleted_key is None

    async def test_delete_nonexistent_key(self, cli_runner, patch_cli_database, sample_api_keys):
        """Test deleting a nonexistent key."""
        fake_id = "00000000-0000-0000-0000-000000000000"

        result = cli_runner.invoke(main, ["delete", fake_id, "--confirm"])

        assert result.exit_code == 1
        assert "API key not found" in result.output


@pytest.mark.integration()
@pytest.mark.requires_docker()
class TestCLIUsageOperations(TestAPIKeyCLIIntegration):
    """Test CLI usage and statistics operations."""

    async def test_usage_command_for_existing_key(self, cli_runner, patch_cli_database, sample_api_keys):
        """Test usage command for an existing key."""
        target_key = sample_api_keys[0]

        result = cli_runner.invoke(main, ["usage", str(target_key.id), "--format", "json"])

        assert result.exit_code == 0

        # Verify usage data structure
        output_data = json.loads(result.output)
        assert "key_name" in output_data
        assert "usage" in output_data
        assert "limits" in output_data
        assert output_data["key_name"] == "Development Key"

    async def test_stats_command(self, cli_runner, patch_cli_database, sample_api_keys):
        """Test system statistics command."""
        result = cli_runner.invoke(main, ["stats", "--format", "json"])

        assert result.exit_code == 0

        # Verify stats data structure
        output_data = json.loads(result.output)
        assert "statistics" in output_data
        assert "period_days" in output_data
        assert "generated_at" in output_data
        assert output_data["period_days"] == 30  # default


@pytest.mark.integration()
@pytest.mark.requires_docker()
class TestCLILimitsOperations(TestAPIKeyCLIIntegration):
    """Test CLI limits management operations."""

    async def test_update_limits_single_parameter(self, cli_runner, patch_cli_database, sample_api_keys, repository):
        """Test updating a single limit parameter."""
        target_key = sample_api_keys[0]
        key_id = str(target_key.id)

        result = cli_runner.invoke(main, ["limits", key_id, "--daily", "1000"])

        assert result.exit_code == 0
        assert "Updated limits" in result.output

        # Verify limit was updated in database
        updated_key = await repository.get_by_id(target_key.id)
        assert updated_key.max_requests_per_day == 1000

    async def test_update_multiple_limits(self, cli_runner, patch_cli_database, sample_api_keys, repository):
        """Test updating multiple limit parameters."""
        target_key = sample_api_keys[0]
        key_id = str(target_key.id)

        result = cli_runner.invoke(
            main, ["limits", key_id, "--patients", "2000", "--daily", "800", "--hourly", "200", "--minute", "20"]
        )

        assert result.exit_code == 0
        assert "Updated limits" in result.output

        # Verify all limits were updated
        updated_key = await repository.get_by_id(target_key.id)
        assert updated_key.max_patients_per_request == 2000
        assert updated_key.max_requests_per_day == 800
        assert updated_key.max_requests_per_hour == 200
        assert updated_key.max_requests_per_minute == 20

    async def test_limits_no_parameters(self, cli_runner, patch_cli_database, sample_api_keys):
        """Test limits command with no update parameters."""
        target_key = sample_api_keys[0]

        result = cli_runner.invoke(main, ["limits", str(target_key.id)])

        assert result.exit_code == 0
        assert "No limit updates specified" in result.output


@pytest.mark.integration()
@pytest.mark.requires_docker()
class TestCLIExpirationOperations(TestAPIKeyCLIIntegration):
    """Test CLI expiration management operations."""

    async def test_extend_expiration(self, cli_runner, patch_cli_database, sample_api_keys, repository):
        """Test extending API key expiration."""
        target_key = sample_api_keys[2]  # Production Key with expiration
        key_id = str(target_key.id)
        original_expiry = target_key.expires_at

        result = cli_runner.invoke(main, ["extend", key_id, "--days", "30"])

        assert result.exit_code == 0
        assert "Extended expiration" in result.output

        # Verify expiration was extended
        updated_key = await repository.get_by_id(target_key.id)
        expected_new_expiry = original_expiry + timedelta(days=30)
        time_diff = abs((updated_key.expires_at - expected_new_expiry).total_seconds())
        assert time_diff < 60  # Within 1 minute tolerance

    async def test_extend_key_without_expiration(self, cli_runner, patch_cli_database, sample_api_keys, repository):
        """Test extending a key that doesn't have an expiration."""
        target_key = sample_api_keys[0]  # Development Key (no expiration)
        key_id = str(target_key.id)

        result = cli_runner.invoke(main, ["extend", key_id, "--days", "90"])

        assert result.exit_code == 0
        assert "Extended expiration" in result.output

        # Should set expiration based on current time
        updated_key = await repository.get_by_id(target_key.id)
        assert updated_key.expires_at is not None
        expected_expiry = datetime.utcnow() + timedelta(days=90)
        time_diff = abs((updated_key.expires_at - expected_expiry).total_seconds())
        assert time_diff < 300  # Within 5 minutes tolerance


@pytest.mark.integration()
@pytest.mark.requires_docker()
class TestCLICleanupOperations(TestAPIKeyCLIIntegration):
    """Test CLI cleanup operations."""

    async def test_cleanup_dry_run(self, cli_runner, patch_cli_database, sample_api_keys):
        """Test cleanup with dry run option."""
        result = cli_runner.invoke(main, ["cleanup", "--dry-run"])

        assert result.exit_code == 0
        assert "Dry run:" in result.output
        # Should find the expired key from sample data
        assert "1 expired" in result.output

    async def test_cleanup_actual_run(self, cli_runner, patch_cli_database, sample_api_keys, repository):
        """Test actual cleanup operation."""
        result = cli_runner.invoke(main, ["cleanup"])

        assert result.exit_code == 0
        assert "Cleaned up" in result.output

        # Verify expired key was actually removed
        # (The expired key from sample data should be deleted)
        remaining_keys = await repository.list_keys()
        key_names = [key.name for key in remaining_keys]
        assert "Expired Key" not in key_names


@pytest.mark.integration()
@pytest.mark.requires_docker()
class TestCLIRotateOperations(TestAPIKeyCLIIntegration):
    """Test CLI key rotation operations."""

    async def test_rotate_key_with_confirmation(
        self, cli_runner, patch_cli_database, sample_api_keys, repository, monkeypatch
    ):
        """Test key rotation with confirmation."""
        target_key = sample_api_keys[0]
        key_id = str(target_key.id)
        original_key_value = target_key.key

        # Mock confirmation to return True
        def mock_confirm_ask(message):
            return True

        monkeypatch.setattr("rich.prompt.Confirm.ask", mock_confirm_ask)

        result = cli_runner.invoke(main, ["rotate", key_id])

        assert result.exit_code == 0
        assert "rotated successfully" in result.output
        assert "New API Key:" in result.output

        # Verify original key was deactivated
        old_key = await repository.get_by_id(target_key.id)
        assert old_key.is_active is False

        # Verify new key exists with same settings but different key value
        all_keys = await repository.list_keys()
        new_keys = [k for k in all_keys if k.name == "Development Key (Rotated)"]
        assert len(new_keys) == 1

        new_key = new_keys[0]
        assert new_key.is_active is True
        assert new_key.key != original_key_value
        assert new_key.email == target_key.email
        assert new_key.max_patients_per_request == target_key.max_patients_per_request

    async def test_rotate_with_custom_name(
        self, cli_runner, patch_cli_database, sample_api_keys, repository, monkeypatch
    ):
        """Test key rotation with custom name."""
        target_key = sample_api_keys[1]  # Demo Key
        key_id = str(target_key.id)

        # Mock confirmation
        def mock_confirm_ask(message):
            return True

        monkeypatch.setattr("rich.prompt.Confirm.ask", mock_confirm_ask)

        result = cli_runner.invoke(main, ["rotate", key_id, "--name", "Rotated Demo Key"])

        assert result.exit_code == 0
        assert "rotated successfully" in result.output

        # Verify new key has custom name
        all_keys = await repository.list_keys()
        new_keys = [k for k in all_keys if k.name == "Rotated Demo Key"]
        assert len(new_keys) == 1

        new_key = new_keys[0]
        assert new_key.is_demo is True  # Should preserve demo status


@pytest.mark.integration()
@pytest.mark.requires_docker()
class TestCLIConcurrentOperations(TestAPIKeyCLIIntegration):
    """Test CLI operations under concurrent access scenarios."""

    async def test_concurrent_key_creation(self, cli_runner, patch_cli_database, repository):
        """Test concurrent key creation operations."""

        async def create_key(name_suffix):
            """Helper to create a key asynchronously."""
            # Note: CliRunner is not async, so we'd need to use repository directly
            # for true concurrent testing. This is a simplified test.
            return await repository.create_api_key(
                name=f"Concurrent Key {name_suffix}", email=f"concurrent{name_suffix}@test.com"
            )

        # Create multiple keys concurrently
        tasks = [create_key(i) for i in range(5)]
        created_keys = await asyncio.gather(*tasks)

        # Verify all keys were created successfully
        assert len(created_keys) == 5
        for i, key in enumerate(created_keys):
            assert key.name == f"Concurrent Key {i}"
            assert key.email == f"concurrent{i}@test.com"

        # Verify keys exist in database
        all_keys = await repository.list_keys()
        concurrent_keys = [k for k in all_keys if k.name.startswith("Concurrent Key")]
        assert len(concurrent_keys) == 5

    async def test_concurrent_list_operations(self, cli_runner, patch_cli_database, sample_api_keys):
        """Test concurrent list operations don't interfere."""

        # Run multiple list commands "concurrently" (sequential due to CliRunner limitations)
        results = []
        for _i in range(3):
            result = cli_runner.invoke(main, ["list", "--format", "json"])
            results.append(result)

        # All should succeed and return consistent results
        for result in results:
            assert result.exit_code == 0
            output_data = json.loads(result.output)
            assert len(output_data) == len(sample_api_keys)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--requires-docker"])
