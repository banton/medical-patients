"""
Shared test fixtures for CLI testing.

This module provides reusable fixtures for unit, integration, and e2e tests
of the API Key CLI tool. Fixtures include:
- Database setup and teardown
- Sample test data generation
- CLI environment configuration
- Mock utilities and helpers

Following pytest best practices for fixture organization.
"""

import asyncio
from datetime import datetime, timedelta
from pathlib import Path

# Import project dependencies
import sys
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.domain.repositories.api_key_repository import APIKeyRepository


@pytest.fixture()
def sample_api_key_data():
    """Generate sample API key data for testing."""
    return {
        "name": "Test API Key",
        "email": "test@example.com",
        "is_active": True,
        "is_demo": False,
        "created_at": datetime(2024, 1, 1, 12, 0, 0),
        "updated_at": datetime(2024, 1, 15, 14, 30, 0),
        "expires_at": datetime(2024, 12, 31, 23, 59, 59),
        "last_used_at": datetime(2024, 1, 15, 14, 30, 45),
        "last_reset_at": datetime(2024, 1, 15, 0, 0, 0),
        "total_requests": 150,
        "total_patients_generated": 2500,
        "daily_requests": 25,
        "max_patients_per_request": 1000,
        "max_requests_per_day": 500,
        "max_requests_per_hour": 100,
        "max_requests_per_minute": 10,
        "key_metadata": {"team": "development", "environment": "test"},
    }


@pytest.fixture()
def mock_api_key(sample_api_key_data):
    """Create a mock API key object with realistic data."""
    key = MagicMock()
    key.id = "12345678-1234-1234-1234-123456789012"
    key.key = "test_key_abcdef123456789012345678901234567890abcdef123456789012345678"

    # Set all attributes from sample data
    for attr, value in sample_api_key_data.items():
        setattr(key, attr, value)

    return key


@pytest.fixture()
def multiple_mock_api_keys():
    """Create multiple mock API keys for list testing."""
    keys = []

    key_configs = [
        {
            "name": "Development Key",
            "email": "dev@example.com",
            "is_demo": False,
            "max_patients_per_request": 1000,
            "max_requests_per_day": 500,
            "total_requests": 150,
        },
        {
            "name": "Demo Key",
            "email": "demo@example.com",
            "is_demo": True,
            "max_patients_per_request": 100,
            "max_requests_per_day": 50,
            "total_requests": 25,
        },
        {
            "name": "Production Key",
            "email": "prod@example.com",
            "is_demo": False,
            "max_patients_per_request": 5000,
            "max_requests_per_day": None,  # Unlimited
            "total_requests": 5000,
            "expires_at": datetime.utcnow() + timedelta(days=90),
        },
        {
            "name": "Inactive Key",
            "email": "inactive@example.com",
            "is_demo": False,
            "is_active": False,
            "max_patients_per_request": 1000,
            "max_requests_per_day": 200,
            "total_requests": 0,
        },
    ]

    for i, config in enumerate(key_configs):
        key = MagicMock()
        key.id = f"1234567{i}-1234-1234-1234-123456789012"
        key.key = f"test_key_{i}_abcdef123456789012345678901234567890abcdef12345678901234567"

        # Set default values
        key.is_active = True
        key.is_demo = False
        key.created_at = datetime(2024, 1, 1, 12, 0, 0)
        key.updated_at = datetime(2024, 1, 15, 14, 30, 0)
        key.expires_at = None
        key.last_used_at = datetime(2024, 1, 15, 14, 30, 45)
        key.last_reset_at = datetime(2024, 1, 15, 0, 0, 0)
        key.total_patients_generated = config.get("total_requests", 0) * 10
        key.daily_requests = config.get("total_requests", 0) // 6
        key.max_requests_per_hour = 100
        key.max_requests_per_minute = 10
        key.key_metadata = {"environment": "test"}

        # Override with config values
        for attr, value in config.items():
            setattr(key, attr, value)

        keys.append(key)

    return keys


@pytest.fixture()
def cli_environment_vars(monkeypatch):
    """Set up environment variables for CLI testing."""
    test_env_vars = {
        "DATABASE_URL": "postgresql+asyncpg://test:test@localhost:5432/test_db",
        "TESTING": "true",
        "LOG_LEVEL": "DEBUG",
    }

    for var, value in test_env_vars.items():
        monkeypatch.setenv(var, value)

    return test_env_vars


@pytest.fixture()
def mock_repository():
    """Create a mock repository for unit testing."""
    repo = AsyncMock(spec=APIKeyRepository)

    # Set up default behaviors
    repo.create_api_key.return_value = AsyncMock()
    repo.get_by_id.return_value = None
    repo.get_by_key.return_value = None
    repo.list_keys.return_value = []
    repo.search_keys.return_value = []
    repo.activate_key.return_value = None
    repo.deactivate_key.return_value = None
    repo.delete_key.return_value = None
    repo.update_limits.return_value = None
    repo.extend_expiration.return_value = None
    repo.cleanup_expired_keys.return_value = 0
    repo.get_usage_stats.return_value = {}
    repo.update_usage.return_value = None

    return repo


@pytest.fixture()
def cli_database_patches(mock_repository, monkeypatch):
    """Patch CLI database operations for unit testing."""

    async def mock_initialize():
        pass

    async def mock_cleanup():
        pass

    def mock_session_factory():
        class MockSessionContext:
            async def __aenter__(self):
                return AsyncMock()

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass

        return MockSessionContext()

    monkeypatch.setattr("scripts.api_key_cli.cli_app.initialize", mock_initialize)
    monkeypatch.setattr("scripts.api_key_cli.cli_app.cleanup", mock_cleanup)
    monkeypatch.setattr("scripts.api_key_cli.cli_app.session_factory", mock_session_factory)
    monkeypatch.setattr("scripts.api_key_cli.APIKeyRepository", lambda session: mock_repository)

    return mock_repository


@pytest.fixture()
def performance_test_data():
    """Generate data for performance testing."""

    def generate_keys(count: int) -> List[Dict[str, Any]]:
        """Generate specified number of test key configurations."""
        keys = []
        for i in range(count):
            keys.append(
                {
                    "name": f"Performance Test Key {i:03d}",
                    "email": f"perf{i:03d}@test.com",
                    "is_demo": i % 10 == 0,  # Every 10th key is demo
                    "max_patients_per_request": 1000 + (i % 5) * 500,
                    "max_requests_per_day": 500 + (i % 3) * 250,
                    "expires_at": datetime.utcnow() + timedelta(days=30 + (i % 90)),
                }
            )
        return keys

    return generate_keys


@pytest.fixture()
def edge_case_test_data():
    """Generate edge case data for boundary testing."""
    return {
        "empty_strings": {
            "name": "",
            "email": "",
        },
        "very_long_strings": {
            "name": "x" * 1000,
            "email": "very_long_email_address_" + "x" * 500 + "@example.com",
        },
        "special_characters": {
            "name": "Test !@#$%^&*()_+-=[]{}|;:,.<>? Name",
            "email": "test+special@example-domain.co.uk",
        },
        "unicode_characters": {
            "name": "Test ñáéíóú 测试 🔑 Name",
            "email": "test.unicode@例え.テスト",
        },
        "boundary_numbers": {
            "max_patients_per_request": 0,
            "max_requests_per_day": 2**31 - 1,  # Max 32-bit int
            "max_requests_per_hour": -1,
            "max_requests_per_minute": 2**63 - 1,  # Max 64-bit int
        },
        "extreme_dates": {
            "expires_at": datetime(1900, 1, 1),
            "created_at": datetime(2100, 12, 31),
        },
    }


@pytest.fixture()
def error_scenarios():
    """Define error scenarios for testing."""
    return {
        "database_errors": {
            "connection_failed": Exception("Database connection failed"),
            "query_timeout": Exception("Query timeout"),
            "constraint_violation": Exception("Unique constraint violation"),
            "transaction_rollback": Exception("Transaction rolled back"),
        },
        "validation_errors": {
            "invalid_uuid": "not-a-valid-uuid",
            "invalid_email": "not-an-email",
            "negative_limits": -1,
            "zero_limits": 0,
        },
        "not_found_errors": {
            "nonexistent_key_id": "00000000-0000-0000-0000-000000000000",
            "deleted_key_id": "11111111-1111-1111-1111-111111111111",
        },
    }


@pytest.fixture()
def automation_test_scenarios():
    """Define scenarios for automation testing."""
    return {
        "ci_cd_pipeline": {
            "test_key": {
                "name": "CI Test Key",
                "is_demo": True,
                "expires_days": 1,
                "max_patients_per_request": 100,
                "max_requests_per_day": 50,
            },
            "production_key": {
                "name": "Production Key",
                "is_demo": False,
                "expires_days": 365,
                "max_patients_per_request": 5000,
                "max_requests_per_day": 10000,
            },
        },
        "team_management": {
            "teams": [
                {"name": "Frontend Team", "email": "frontend@company.com", "limits": {"patients": 500, "daily": 200}},
                {"name": "Backend Team", "email": "backend@company.com", "limits": {"patients": 2000, "daily": 1000}},
                {
                    "name": "QA Team",
                    "email": "qa@company.com",
                    "limits": {"patients": 100, "daily": 50},
                    "is_demo": True,
                },
            ]
        },
        "security_rotation": {
            "rotation_interval_days": 90,
            "notification_threshold_days": 7,
            "cleanup_expired_after_days": 30,
        },
    }


@pytest.fixture()
async def async_test_helper():
    """Helper utilities for async testing."""

    class AsyncTestHelper:
        @staticmethod
        async def wait_for_condition(condition_func, timeout=5.0, interval=0.1):
            """Wait for a condition to become true."""
            import asyncio

            start_time = asyncio.get_event_loop().time()

            while True:
                if condition_func():
                    return True

                if asyncio.get_event_loop().time() - start_time > timeout:
                    return False

                await asyncio.sleep(interval)

        @staticmethod
        async def run_with_timeout(coro, timeout=10.0):
            """Run a coroutine with timeout."""
            return await asyncio.wait_for(coro, timeout=timeout)

        @staticmethod
        def create_future_result(result):
            """Create a future with a predetermined result."""
            future = asyncio.Future()
            future.set_result(result)
            return future

        @staticmethod
        def create_future_exception(exception):
            """Create a future with a predetermined exception."""
            future = asyncio.Future()
            future.set_exception(exception)
            return future

    return AsyncTestHelper()


@pytest.fixture()
def performance_benchmarks():
    """Define performance benchmarks for testing."""
    return {
        "response_times": {
            "create_key": 2.0,  # seconds
            "list_keys_100": 5.0,  # seconds for 100 keys
            "search_keys": 3.0,  # seconds
            "show_key": 1.0,  # seconds
            "update_limits": 1.5,  # seconds
        },
        "memory_usage": {
            "baseline": 50,  # MB
            "per_100_keys": 10,  # MB additional per 100 keys
            "max_growth": 100,  # MB maximum growth
        },
        "concurrency": {
            "max_concurrent_ops": 10,
            "timeout_per_op": 30.0,  # seconds
        },
    }


@pytest.fixture()
def test_data_cleanup():
    """Provide cleanup utilities for test data."""
    cleanup_tasks = []

    def register_cleanup(cleanup_func):
        """Register a cleanup function to run after test."""
        cleanup_tasks.append(cleanup_func)

    yield register_cleanup

    # Run all cleanup tasks
    for cleanup_func in cleanup_tasks:
        try:
            if asyncio.iscoroutinefunction(cleanup_func):
                asyncio.create_task(cleanup_func())
            else:
                cleanup_func()
        except Exception as e:
            # Log cleanup errors but don't fail tests
            print(f"Cleanup error: {e}")


@pytest.fixture()
def cli_test_utilities():
    """Provide utilities for CLI testing."""

    class CLITestUtilities:
        @staticmethod
        def extract_json_from_output(output: str) -> dict:
            """Extract JSON data from CLI output."""
            import json

            return json.loads(output)

        @staticmethod
        def extract_key_id_from_output(output: str) -> str:
            """Extract API key ID from CLI output."""
            import re

            # Look for UUID pattern in output
            uuid_pattern = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
            match = re.search(uuid_pattern, output)
            return match.group(0) if match else None

        @staticmethod
        def extract_api_key_from_output(output: str) -> str:
            """Extract API key value from CLI output."""
            # Look for "New API Key:" or "Key:" in output
            lines = output.split("\n")
            for line in lines:
                if "New API Key:" in line:
                    return line.split("New API Key: ")[1].strip()
                if line.strip().startswith("Key:"):
                    return line.split("Key: ")[1].strip()
            return None

        @staticmethod
        def validate_json_structure(data: dict, required_fields: List[str]) -> bool:
            """Validate JSON structure has required fields."""
            return all(field in data for field in required_fields)

        @staticmethod
        def count_csv_rows(csv_output: str) -> int:
            """Count rows in CSV output."""
            return len(csv_output.strip().split("\n")) - 1  # Exclude header

        @staticmethod
        def parse_csv_header(csv_output: str) -> List[str]:
            """Parse CSV header fields."""
            import csv
            from io import StringIO

            reader = csv.reader(StringIO(csv_output))
            return next(reader)

    return CLITestUtilities()


# Pytest configuration
def pytest_configure(config):
    """Configure pytest for CLI testing."""
    config.addinivalue_line("markers", "cli_unit: Unit tests for CLI components")
    config.addinivalue_line("markers", "cli_integration: Integration tests with database")
    config.addinivalue_line("markers", "cli_e2e: End-to-end workflow tests")
    config.addinivalue_line("markers", "cli_performance: Performance and load tests")
    config.addinivalue_line("markers", "cli_automation: Automation and scripting tests")
