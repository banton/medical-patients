"""
Integration Tests for API Key CLI Tool

This module contains integration tests that validate CLI commands with real database
operations. Tests focus on:
- Database operations with PostgreSQL
- Command workflows with real data persistence
- Transaction behavior and rollback scenarios
- Concurrent access patterns
- Search and filtering functionality with real queries

Following TDD principles with actual database validation.
"""

import asyncio
from datetime import datetime, timedelta
import json
import os
from pathlib import Path

# Import the CLI module and dependencies
import sys

from click.testing import CliRunner
import pytest
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, Session

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.api_key_cli import main
from src.domain.repositories.api_key_repository import APIKeyRepository


@pytest.mark.integration()
class TestAPIKeyCLIIntegration:
    """Integration tests with real database operations."""

    @pytest.fixture()
    def db_url(self):
        """Get database URL for testing."""
        # Use DATABASE_URL from environment if available (CI), otherwise use test URL
        url = os.getenv("DATABASE_URL", os.getenv("TEST_DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/test_db"))
        return url

    @pytest.fixture()
    async def db_engine(self, db_url):
        """Create async database engine for CLI testing."""
        # Convert sync PostgreSQL URL to async if needed
        if db_url.startswith("postgresql://"):
            async_url = db_url.replace("postgresql://", "postgresql+asyncpg://")
        else:
            async_url = db_url
            
        engine = create_async_engine(async_url, echo=False)
        yield engine
        await engine.dispose()

    @pytest.fixture()
    async def db_session(self, db_engine):
        """Create async database session for each test."""
        session_factory = sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
        async with session_factory() as session:
            yield session
            await session.rollback()

    @pytest.fixture()
    def sync_db_session(self, db_url):
        """Create sync database session for test setup/teardown."""
        # Create sync engine for test data setup
        if db_url.startswith("postgresql+asyncpg://"):
            sync_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
        else:
            sync_url = db_url
            
        engine = create_engine(sync_url)
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        yield session
        session.close()
        engine.dispose()

    @pytest.fixture()
    def cli_runner(self, monkeypatch, db_url):
        """Create CLI runner with database URL set."""
        # Set the DATABASE_URL for the CLI to use
        monkeypatch.setenv("DATABASE_URL", db_url)
        return CliRunner()


class TestCLICreateOperations(TestAPIKeyCLIIntegration):
    """Test API key creation operations."""

    def test_create_basic_api_key(self, cli_runner):
        """Test creating a basic API key with minimal options."""
        result = cli_runner.invoke(
            main,
            ["create", "--name", "Test Key", "--email", "test@example.com"],
            catch_exceptions=False
        )
        
        assert result.exit_code == 0
        assert "Created API key" in result.output
        assert "Test Key" in result.output
        assert "test@example.com" in result.output

    def test_create_demo_key_with_limits(self, cli_runner):
        """Test creating a demo key with custom limits."""
        result = cli_runner.invoke(
            main,
            [
                "create",
                "--name", "Demo Key",
                "--demo",
                "--patients", "50",
                "--daily", "100",
                "--hourly", "20",
                "--minute", "5"
            ],
            catch_exceptions=False
        )
        
        assert result.exit_code == 0
        assert "Created API key" in result.output
        assert "Demo Key" in result.output
        assert "Max Patients Per Request: 50" in result.output

    def test_create_key_with_expiration(self, cli_runner):
        """Test creating a key with expiration date."""
        result = cli_runner.invoke(
            main,
            ["create", "--name", "Expiring Key", "--expires-days", "30"],
            catch_exceptions=False
        )
        
        assert result.exit_code == 0
        assert "Created API key" in result.output
        assert "Expires At:" in result.output


class TestCLIListOperations(TestAPIKeyCLIIntegration):
    """Test API key listing operations."""

    async def setup_test_keys(self, db_session):
        """Create test keys for list operations."""
        repo = APIKeyRepository(db_session)
        
        # Create various test keys
        keys = []
        keys.append(await repo.create_api_key("Active Key 1", "active1@test.com"))
        keys.append(await repo.create_api_key("Active Key 2", "active2@test.com"))
        
        demo_key = await repo.create_api_key("Demo Key", "demo@test.com", is_demo=True)
        keys.append(demo_key)
        
        inactive_key = await repo.create_api_key("Inactive Key", "inactive@test.com")
        await repo.deactivate_key(inactive_key.id)
        keys.append(inactive_key)
        
        await db_session.commit()
        return keys

    async def test_list_all_keys(self, cli_runner, db_session):
        """Test listing all API keys."""
        await self.setup_test_keys(db_session)
        
        result = cli_runner.invoke(main, ["list"], catch_exceptions=False)
        
        assert result.exit_code == 0
        assert "Active Key 1" in result.output
        assert "Active Key 2" in result.output
        assert "Demo Key" in result.output
        assert "Inactive Key" in result.output

    async def test_list_active_keys_only(self, cli_runner, db_session):
        """Test listing only active keys."""
        await self.setup_test_keys(db_session)
        
        result = cli_runner.invoke(main, ["list", "--active"], catch_exceptions=False)
        
        assert result.exit_code == 0
        assert "Active Key 1" in result.output
        assert "Active Key 2" in result.output
        assert "Demo Key" in result.output
        assert "Inactive Key" not in result.output

    async def test_list_demo_keys_only(self, cli_runner, db_session):
        """Test listing only demo keys."""
        await self.setup_test_keys(db_session)
        
        result = cli_runner.invoke(main, ["list", "--demo"], catch_exceptions=False)
        
        assert result.exit_code == 0
        assert "Demo Key" in result.output
        assert "Active Key 1" not in result.output

    async def test_list_with_search_filter(self, cli_runner, db_session):
        """Test listing with search filter."""
        await self.setup_test_keys(db_session)
        
        result = cli_runner.invoke(
            main,
            ["list", "--search", "Active"],
            catch_exceptions=False
        )
        
        assert result.exit_code == 0
        assert "Active Key 1" in result.output
        assert "Active Key 2" in result.output
        assert "Demo Key" not in result.output

    async def test_list_with_email_search(self, cli_runner, db_session):
        """Test listing with email search."""
        await self.setup_test_keys(db_session)
        
        result = cli_runner.invoke(
            main,
            ["list", "--search", "demo@test.com"],
            catch_exceptions=False
        )
        
        assert result.exit_code == 0
        assert "Demo Key" in result.output
        assert "demo@test.com" in result.output

    async def test_list_csv_format(self, cli_runner, db_session):
        """Test listing in CSV format."""
        await self.setup_test_keys(db_session)
        
        result = cli_runner.invoke(
            main,
            ["list", "--format", "csv"],
            catch_exceptions=False
        )
        
        assert result.exit_code == 0
        assert "ID,Key Prefix,Name,Email,Active,Demo,Created,Expires,Last Used,Total Requests,Daily Requests" in result.output
        assert "Active Key 1" in result.output


class TestCLIShowOperations(TestAPIKeyCLIIntegration):
    """Test API key show operations."""

    async def test_show_key_by_id(self, cli_runner, db_session):
        """Test showing key details by ID."""
        repo = APIKeyRepository(db_session)
        key = await repo.create_api_key("Show Test Key", "show@test.com")
        await db_session.commit()
        
        result = cli_runner.invoke(
            main,
            ["show", str(key.id)],
            catch_exceptions=False
        )
        
        assert result.exit_code == 0
        assert "Show Test Key" in result.output
        assert "show@test.com" in result.output
        assert str(key.id) in result.output

    def test_show_nonexistent_key(self, cli_runner):
        """Test showing non-existent key."""
        fake_id = "12345678-1234-1234-1234-123456789012"
        
        result = cli_runner.invoke(
            main,
            ["show", fake_id],
            catch_exceptions=False
        )
        
        assert result.exit_code == 1
        assert "not found" in result.output.lower()

    async def test_show_key_table_format(self, cli_runner, db_session):
        """Test showing key in table format."""
        repo = APIKeyRepository(db_session)
        key = await repo.create_api_key(
            "Table Test Key",
            "table@test.com",
            max_patients_per_request=500,
            max_requests_per_day=1000
        )
        await db_session.commit()
        
        result = cli_runner.invoke(
            main,
            ["show", str(key.id), "--format", "table"],
            catch_exceptions=False
        )
        
        assert result.exit_code == 0
        assert "Table Test Key" in result.output
        assert "Max Patients Per Request" in result.output
        assert "500" in result.output


class TestCLIActivationOperations(TestAPIKeyCLIIntegration):
    """Test API key activation/deactivation operations."""

    async def test_deactivate_and_activate_key(self, cli_runner, db_session):
        """Test deactivating and reactivating a key."""
        repo = APIKeyRepository(db_session)
        key = await repo.create_api_key("Toggle Test Key", "toggle@test.com")
        await db_session.commit()
        
        # Deactivate
        result = cli_runner.invoke(
            main,
            ["deactivate", str(key.id)],
            catch_exceptions=False
        )
        assert result.exit_code == 0
        assert "deactivated" in result.output.lower()
        
        # Verify deactivated
        await db_session.refresh(key)
        assert not key.is_active
        
        # Activate
        result = cli_runner.invoke(
            main,
            ["activate", str(key.id)],
            catch_exceptions=False
        )
        assert result.exit_code == 0
        assert "activated" in result.output.lower()
        
        # Verify activated
        await db_session.refresh(key)
        assert key.is_active

    async def test_activate_already_active_key(self, cli_runner, db_session):
        """Test activating an already active key."""
        repo = APIKeyRepository(db_session)
        key = await repo.create_api_key("Already Active", "active@test.com")
        await db_session.commit()
        
        result = cli_runner.invoke(
            main,
            ["activate", str(key.id)],
            catch_exceptions=False
        )
        
        assert result.exit_code == 0
        assert "already active" in result.output.lower()

    async def test_deactivate_already_inactive_key(self, cli_runner, db_session):
        """Test deactivating an already inactive key."""
        repo = APIKeyRepository(db_session)
        key = await repo.create_api_key("Already Inactive", "inactive@test.com")
        await repo.deactivate_key(key.id)
        await db_session.commit()
        
        result = cli_runner.invoke(
            main,
            ["deactivate", str(key.id)],
            catch_exceptions=False
        )
        
        assert result.exit_code == 0
        assert "already inactive" in result.output.lower()


class TestCLIDeleteOperations(TestAPIKeyCLIIntegration):
    """Test API key deletion operations."""

    async def test_delete_key_with_confirmation(self, cli_runner, db_session):
        """Test deleting a key with confirmation."""
        repo = APIKeyRepository(db_session)
        key = await repo.create_api_key("Delete Test Key", "delete@test.com")
        await db_session.commit()
        
        result = cli_runner.invoke(
            main,
            ["delete", str(key.id), "--confirm"],
            catch_exceptions=False
        )
        
        assert result.exit_code == 0
        assert "deleted successfully" in result.output.lower()
        
        # Verify deleted
        deleted_key = await repo.get_by_id(key.id)
        assert deleted_key is None

    def test_delete_nonexistent_key(self, cli_runner):
        """Test deleting non-existent key."""
        fake_id = "12345678-1234-1234-1234-123456789012"
        
        result = cli_runner.invoke(
            main,
            ["delete", fake_id, "--confirm"],
            catch_exceptions=False
        )
        
        assert result.exit_code == 1
        assert "not found" in result.output.lower()


class TestCLIUsageOperations(TestAPIKeyCLIIntegration):
    """Test API key usage tracking operations."""

    async def test_usage_command_for_existing_key(self, cli_runner, db_session):
        """Test showing usage statistics for a key."""
        repo = APIKeyRepository(db_session)
        key = await repo.create_api_key("Usage Test Key", "usage@test.com")
        
        # Record some usage
        await repo.record_usage(key.id, patients_generated=100)
        await repo.record_usage(key.id, patients_generated=50)
        await db_session.commit()
        
        result = cli_runner.invoke(
            main,
            ["usage", str(key.id)],
            catch_exceptions=False
        )
        
        assert result.exit_code == 0
        assert "Usage Test Key" in result.output
        assert "Total Requests: 2" in result.output
        assert "Total Patients: 150" in result.output

    async def test_stats_command(self, cli_runner, db_session):
        """Test showing overall statistics."""
        repo = APIKeyRepository(db_session)
        
        # Create test keys with usage
        for i in range(3):
            key = await repo.create_api_key(f"Stats Key {i}", f"stats{i}@test.com")
            await repo.record_usage(key.id, patients_generated=100 * (i + 1))
        
        await db_session.commit()
        
        result = cli_runner.invoke(
            main,
            ["stats", "--days", "30"],
            catch_exceptions=False
        )
        
        assert result.exit_code == 0
        assert "API Key Statistics" in result.output
        assert "Total Keys:" in result.output
        assert "Active Keys:" in result.output


class TestCLILimitsOperations(TestAPIKeyCLIIntegration):
    """Test API key limits update operations."""

    async def test_update_limits_single_parameter(self, cli_runner, db_session):
        """Test updating a single limit parameter."""
        repo = APIKeyRepository(db_session)
        key = await repo.create_api_key("Limits Test Key", "limits@test.com")
        await db_session.commit()
        
        result = cli_runner.invoke(
            main,
            ["limits", str(key.id), "--patients", "2000"],
            catch_exceptions=False
        )
        
        assert result.exit_code == 0
        assert "Limits updated successfully" in result.output
        
        # Verify update
        await db_session.refresh(key)
        assert key.max_patients_per_request == 2000

    async def test_update_multiple_limits(self, cli_runner, db_session):
        """Test updating multiple limit parameters."""
        repo = APIKeyRepository(db_session)
        key = await repo.create_api_key("Multi Limits Key", "multilimits@test.com")
        await db_session.commit()
        
        result = cli_runner.invoke(
            main,
            [
                "limits", str(key.id),
                "--patients", "5000",
                "--daily", "1000",
                "--hourly", "100",
                "--minute", "10"
            ],
            catch_exceptions=False
        )
        
        assert result.exit_code == 0
        assert "Limits updated successfully" in result.output
        
        # Verify updates
        await db_session.refresh(key)
        assert key.max_patients_per_request == 5000
        assert key.max_requests_per_day == 1000
        assert key.max_requests_per_hour == 100
        assert key.max_requests_per_minute == 10

    async def test_limits_no_parameters(self, cli_runner, db_session):
        """Test limits command with no parameters shows current limits."""
        repo = APIKeyRepository(db_session)
        key = await repo.create_api_key(
            "Show Limits Key",
            "showlimits@test.com",
            max_patients_per_request=3000,
            max_requests_per_day=500
        )
        await db_session.commit()
        
        result = cli_runner.invoke(
            main,
            ["limits", str(key.id)],
            catch_exceptions=False
        )
        
        assert result.exit_code == 0
        assert "Current limits" in result.output
        assert "3000" in result.output
        assert "500" in result.output


class TestCLIExpirationOperations(TestAPIKeyCLIIntegration):
    """Test API key expiration operations."""

    async def test_extend_expiration(self, cli_runner, db_session):
        """Test extending key expiration."""
        repo = APIKeyRepository(db_session)
        expires_at = datetime.utcnow() + timedelta(days=10)
        key = await repo.create_api_key(
            "Expiring Key",
            "expire@test.com",
            expires_at=expires_at
        )
        await db_session.commit()
        
        result = cli_runner.invoke(
            main,
            ["extend", str(key.id), "--days", "30"],
            catch_exceptions=False
        )
        
        assert result.exit_code == 0
        assert "Extended expiration" in result.output
        
        # Verify extension
        await db_session.refresh(key)
        assert key.expires_at > expires_at

    async def test_extend_key_without_expiration(self, cli_runner, db_session):
        """Test extending key that doesn't expire."""
        repo = APIKeyRepository(db_session)
        key = await repo.create_api_key("Non-expiring Key", "noexpire@test.com")
        await db_session.commit()
        
        result = cli_runner.invoke(
            main,
            ["extend", str(key.id), "--days", "30"],
            catch_exceptions=False
        )
        
        assert result.exit_code == 0
        # Should set expiration 30 days from now
        await db_session.refresh(key)
        assert key.expires_at is not None


class TestCLICleanupOperations(TestAPIKeyCLIIntegration):
    """Test API key cleanup operations."""

    async def test_cleanup_dry_run(self, cli_runner, db_session):
        """Test cleanup in dry-run mode."""
        repo = APIKeyRepository(db_session)
        
        # Create expired key
        expired_date = datetime.utcnow() - timedelta(days=10)
        expired_key = await repo.create_api_key(
            "Expired Key",
            "expired@test.com",
            expires_at=expired_date
        )
        
        # Create active key
        await repo.create_api_key("Active Key", "active@test.com")
        await db_session.commit()
        
        result = cli_runner.invoke(
            main,
            ["cleanup", "--dry-run"],
            catch_exceptions=False
        )
        
        assert result.exit_code == 0
        assert "Would delete" in result.output
        assert "Expired Key" in result.output
        
        # Verify not actually deleted
        check_key = await repo.get_by_id(expired_key.id)
        assert check_key is not None

    async def test_cleanup_actual_run(self, cli_runner, db_session):
        """Test cleanup with actual deletion."""
        repo = APIKeyRepository(db_session)
        
        # Create expired key
        expired_date = datetime.utcnow() - timedelta(days=10)
        expired_key = await repo.create_api_key(
            "Expired Key",
            "expired@test.com",
            expires_at=expired_date
        )
        await db_session.commit()
        
        result = cli_runner.invoke(
            main,
            ["cleanup"],
            input="y\n",  # Confirm deletion
            catch_exceptions=False
        )
        
        assert result.exit_code == 0
        assert "Deleted 1 expired" in result.output
        
        # Verify deleted
        check_key = await repo.get_by_id(expired_key.id)
        assert check_key is None


class TestCLIRotateOperations(TestAPIKeyCLIIntegration):
    """Test API key rotation operations."""

    async def test_rotate_key_with_confirmation(self, cli_runner, db_session):
        """Test rotating an API key."""
        repo = APIKeyRepository(db_session)
        old_key = await repo.create_api_key("Old Key", "rotate@test.com")
        old_key_value = old_key.key
        await db_session.commit()
        
        result = cli_runner.invoke(
            main,
            ["rotate", str(old_key.id)],
            input="y\n",  # Confirm rotation
            catch_exceptions=False
        )
        
        assert result.exit_code == 0
        assert "New API key created" in result.output
        assert "deactivated" in result.output
        
        # Verify old key is deactivated
        await db_session.refresh(old_key)
        assert not old_key.is_active
        
        # Verify new key exists
        new_keys = await repo.search_keys("Old Key (Rotated")
        assert len(new_keys) == 1
        assert new_keys[0].key != old_key_value

    async def test_rotate_with_custom_name(self, cli_runner, db_session):
        """Test rotating with custom name."""
        repo = APIKeyRepository(db_session)
        old_key = await repo.create_api_key("Original Key", "original@test.com")
        await db_session.commit()
        
        result = cli_runner.invoke(
            main,
            ["rotate", str(old_key.id), "--name", "New Key Name"],
            input="y\n",
            catch_exceptions=False
        )
        
        assert result.exit_code == 0
        assert "New Key Name" in result.output


class TestCLIConcurrentOperations(TestAPIKeyCLIIntegration):
    """Test concurrent CLI operations."""

    async def test_concurrent_key_creation(self, cli_runner):
        """Test creating multiple keys concurrently."""
        # Run multiple create commands in parallel
        tasks = []
        for i in range(5):
            result = cli_runner.invoke(
                main,
                ["create", "--name", f"Concurrent Key {i}", "--email", f"concurrent{i}@test.com"],
                catch_exceptions=False
            )
            assert result.exit_code == 0

    async def test_concurrent_list_operations(self, cli_runner, db_session):
        """Test concurrent list operations."""
        # Create test data
        repo = APIKeyRepository(db_session)
        for i in range(10):
            await repo.create_api_key(f"List Test {i}", f"list{i}@test.com")
        await db_session.commit()
        
        # Run multiple list commands
        for _ in range(3):
            result = cli_runner.invoke(
                main,
                ["list", "--format", "json"],
                catch_exceptions=False
            )
            assert result.exit_code == 0
            data = json.loads(result.output)
            assert len(data) >= 10