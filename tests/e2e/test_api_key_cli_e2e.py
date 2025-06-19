"""
End-to-End Tests for API Key CLI Tool

This module contains comprehensive end-to-end tests that validate complete user
workflows and system interactions. Tests focus on:
- Complete user workflow scenarios from start to finish
- Cross-command data consistency and state management
- Performance testing with realistic datasets
- Error recovery and system resilience
- Real-world usage patterns and automation scenarios

Following TDD principles with full system validation.
"""

import asyncio
import json
from pathlib import Path

# Import the CLI module and dependencies
import sys
import time

from click.testing import CliRunner
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.api_key_cli import main
from src.domain.repositories.api_key_repository import APIKeyRepository


@pytest.mark.e2e()
@pytest.mark.skip(reason="Requires Docker and database setup")
@pytest.mark.requires_docker()
class TestAPIKeyCLIE2E:
    """Base class for end-to-end CLI tests."""

    @pytest.fixture(scope="class")
    async def db_engine(self, test_database_url):
        """Create async database engine for E2E testing."""
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
    def patch_cli_database(self, db_session, repository, monkeypatch):
        """Patch CLI database connection to use test database."""

        async def mock_initialize():
            pass

        async def mock_cleanup():
            pass

        def mock_session_factory():
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


@pytest.mark.e2e()
@pytest.mark.skip(reason="Requires Docker and database setup")
@pytest.mark.requires_docker()
class TestCompleteAPIKeyLifecycle(TestAPIKeyCLIE2E):
    """Test complete API key lifecycle workflows."""

    async def test_complete_api_key_lifecycle_workflow(self, cli_runner, patch_cli_database, repository, monkeypatch):
        """
        Test complete API key lifecycle: create → monitor → update → rotate → cleanup.

        This test represents a real-world scenario where an administrator:
        1. Creates a new API key for a development team
        2. Monitors its usage over time
        3. Updates limits based on usage patterns
        4. Rotates the key for security
        5. Cleans up expired keys
        """

        # Mock confirmation prompts
        def mock_confirm_ask(message):
            return True

        monkeypatch.setattr("rich.prompt.Confirm.ask", mock_confirm_ask)

        # Step 1: Create a new API key for development team
        print("\n=== Step 1: Create API Key ===")
        create_result = cli_runner.invoke(
            main,
            [
                "create",
                "--name",
                "E2E Development Team",
                "--email",
                "dev-e2e@example.com",
                "--patients",
                "1000",
                "--daily",
                "500",
                "--hourly",
                "100",
                "--format",
                "json",
            ],
        )

        assert create_result.exit_code == 0
        create_data = json.loads(create_result.output)
        key_id = create_data["id"]
        api_key = create_data["key"]

        print(f"Created API key: {key_id}")
        assert create_data["name"] == "E2E Development Team"
        assert create_data["limits"]["patients_per_request"] == 1000
        assert create_data["limits"]["requests_per_day"] == 500

        # Step 2: Verify key appears in list
        print("\n=== Step 2: Verify Key in List ===")
        list_result = cli_runner.invoke(main, ["list", "--active", "--format", "json"])

        assert list_result.exit_code == 0
        list_data = json.loads(list_result.output)
        key_names = [key["name"] for key in list_data]
        assert "E2E Development Team" in key_names

        # Step 3: Show detailed key information
        print("\n=== Step 3: Show Key Details ===")
        show_result = cli_runner.invoke(main, ["show", key_id, "--format", "json"])

        assert show_result.exit_code == 0
        show_data = json.loads(show_result.output)
        assert show_data["name"] == "E2E Development Team"
        assert show_data["is_active"] is True
        assert "usage" in show_data
        assert "limits" in show_data

        # Step 4: Simulate usage and check usage statistics
        print("\n=== Step 4: Simulate Usage ===")
        # Simulate some API usage by updating the key's usage stats
        await repository.update_usage(key_id, patients_generated=150, request_count=25)

        usage_result = cli_runner.invoke(main, ["usage", key_id, "--format", "json"])

        assert usage_result.exit_code == 0
        usage_data = json.loads(usage_result.output)
        assert usage_data["key_name"] == "E2E Development Team"

        # Step 5: Update limits based on usage patterns
        print("\n=== Step 5: Update Limits ===")
        limits_result = cli_runner.invoke(
            main, ["limits", key_id, "--patients", "2000", "--daily", "1000", "--hourly", "200"]
        )

        assert limits_result.exit_code == 0
        assert "Updated limits" in limits_result.output

        # Verify limits were updated
        updated_show_result = cli_runner.invoke(main, ["show", key_id, "--format", "json"])
        updated_show_data = json.loads(updated_show_result.output)
        assert updated_show_data["limits"]["patients_per_request"] == 2000
        assert updated_show_data["limits"]["requests_per_day"] == 1000

        # Step 6: Extend expiration for long-term use
        print("\n=== Step 6: Extend Expiration ===")
        extend_result = cli_runner.invoke(main, ["extend", key_id, "--days", "90"])

        assert extend_result.exit_code == 0
        assert "Extended expiration" in extend_result.output

        # Step 7: Rotate key for security
        print("\n=== Step 7: Rotate Key ===")
        rotate_result = cli_runner.invoke(main, ["rotate", key_id, "--name", "E2E Development Team v2"])

        assert rotate_result.exit_code == 0
        assert "rotated successfully" in rotate_result.output
        assert "New API Key:" in rotate_result.output

        # Verify original key is deactivated and new key exists
        old_key = await repository.get_by_id(key_id)
        assert old_key.is_active is False

        all_keys = await repository.list_keys()
        new_keys = [k for k in all_keys if k.name == "E2E Development Team v2"]
        assert len(new_keys) == 1
        new_key = new_keys[0]
        assert new_key.is_active is True

        # Step 8: Check system statistics
        print("\n=== Step 8: System Statistics ===")
        stats_result = cli_runner.invoke(main, ["stats", "--format", "json"])

        assert stats_result.exit_code == 0
        stats_data = json.loads(stats_result.output)
        assert "statistics" in stats_data

        # Step 9: Search and filter operations
        print("\n=== Step 9: Search Operations ===")
        search_result = cli_runner.invoke(main, ["list", "--search", "E2E Development", "--format", "json"])

        assert search_result.exit_code == 0
        search_data = json.loads(search_result.output)
        assert len(search_data) >= 1  # Should find the new key

        # Step 10: Final cleanup verification
        print("\n=== Step 10: Final State Verification ===")
        final_list_result = cli_runner.invoke(main, ["list", "--format", "json"])

        assert final_list_result.exit_code == 0
        final_data = json.loads(final_list_result.output)

        # Should have at least the new rotated key
        active_keys = [k for k in final_data if k["is_active"]]
        new_key_names = [k["name"] for k in active_keys]
        assert "E2E Development Team v2" in new_key_names

        print("\n=== Lifecycle Test Completed Successfully ===")

    async def test_team_collaboration_workflow(self, cli_runner, patch_cli_database, repository, monkeypatch):
        """
        Test team collaboration workflow with multiple API keys.

        Simulates a scenario where multiple teams need different API keys
        with different permissions and limits.
        """

        def mock_confirm_ask(message):
            return True

        monkeypatch.setattr("rich.prompt.Confirm.ask", mock_confirm_ask)

        # Create keys for different teams
        teams = [
            {"name": "Frontend Team", "email": "frontend@company.com", "patients": 500, "daily": 200, "demo": False},
            {"name": "Backend Team", "email": "backend@company.com", "patients": 2000, "daily": 1000, "demo": False},
            {"name": "QA Team", "email": "qa@company.com", "patients": 100, "daily": 50, "demo": True},
            {"name": "Demo Account", "email": "demo@company.com", "patients": 50, "daily": 25, "demo": True},
        ]

        created_keys = []

        # Create all team keys
        for team in teams:
            create_args = [
                "create",
                "--name",
                team["name"],
                "--email",
                team["email"],
                "--patients",
                str(team["patients"]),
                "--daily",
                str(team["daily"]),
                "--format",
                "json",
            ]

            if team["demo"]:
                create_args.append("--demo")

            result = cli_runner.invoke(main, create_args)
            assert result.exit_code == 0

            key_data = json.loads(result.output)
            created_keys.append(key_data)

        # Verify all teams can be listed
        list_result = cli_runner.invoke(main, ["list", "--format", "json"])
        assert list_result.exit_code == 0

        all_keys = json.loads(list_result.output)
        assert len(all_keys) >= len(teams)

        # Test filtering by demo vs production keys
        demo_result = cli_runner.invoke(main, ["list", "--demo", "--format", "json"])
        assert demo_result.exit_code == 0

        demo_keys = json.loads(demo_result.output)
        demo_names = [k["name"] for k in demo_keys]
        assert "QA Team" in demo_names
        assert "Demo Account" in demo_names
        assert "Frontend Team" not in demo_names

        # Test search functionality
        search_result = cli_runner.invoke(main, ["list", "--search", "Team", "--format", "json"])
        assert search_result.exit_code == 0

        search_keys = json.loads(search_result.output)
        assert len(search_keys) >= 3  # Frontend, Backend, QA teams

        # Simulate different usage patterns for each team
        for i, key_data in enumerate(created_keys):
            # Different usage levels for different teams
            patients = (i + 1) * 25
            requests = (i + 1) * 10

            await repository.update_usage(key_data["id"], patients_generated=patients, request_count=requests)

        # Generate system statistics
        stats_result = cli_runner.invoke(main, ["stats", "--format", "json"])
        assert stats_result.exit_code == 0

        stats_data = json.loads(stats_result.output)
        assert "statistics" in stats_data


@pytest.mark.e2e()
@pytest.mark.requires_docker()
class TestPerformanceWorkflows(TestAPIKeyCLIE2E):
    """Test CLI performance with realistic datasets."""

    @pytest.mark.slow()
    async def test_bulk_operations_performance(self, cli_runner, patch_cli_database, repository):
        """
        Test CLI performance with bulk operations.

        Creates a large number of API keys and tests various operations
        to ensure reasonable performance characteristics.
        """

        # Performance targets
        max_create_time = 2.0  # seconds per key creation
        max_list_time = 5.0  # seconds to list 100 keys
        max_search_time = 3.0  # seconds to search through 100 keys

        num_keys = 50  # Reduced for CI/CD performance
        created_keys = []

        print(f"\n=== Creating {num_keys} API keys for performance testing ===")

        # Bulk create API keys
        start_time = time.time()

        for i in range(num_keys):
            create_result = cli_runner.invoke(
                main,
                [
                    "create",
                    "--name",
                    f"Performance Test Key {i:03d}",
                    "--email",
                    f"perf{i:03d}@test.com",
                    "--patients",
                    "1000",
                    "--daily",
                    "500",
                    "--format",
                    "json",
                ],
            )

            assert create_result.exit_code == 0
            key_data = json.loads(create_result.output)
            created_keys.append(key_data)

            # Check individual create performance
            create_time = time.time() - start_time
            avg_create_time = create_time / (i + 1)
            if avg_create_time > max_create_time:
                pytest.fail(f"Average create time {avg_create_time:.2f}s exceeds target {max_create_time}s")

        total_create_time = time.time() - start_time
        avg_create_time = total_create_time / num_keys
        print(f"Created {num_keys} keys in {total_create_time:.2f}s (avg: {avg_create_time:.3f}s per key)")

        # Test list performance
        print("\n=== Testing list performance ===")
        start_time = time.time()

        list_result = cli_runner.invoke(main, ["list", "--format", "json"])

        list_time = time.time() - start_time
        assert list_result.exit_code == 0

        list_data = json.loads(list_result.output)
        assert len(list_data) >= num_keys

        print(f"Listed {len(list_data)} keys in {list_time:.2f}s")
        if list_time > max_list_time:
            pytest.fail(f"List time {list_time:.2f}s exceeds target {max_list_time}s")

        # Test search performance
        print("\n=== Testing search performance ===")
        start_time = time.time()

        search_result = cli_runner.invoke(main, ["list", "--search", "Performance Test", "--format", "json"])

        search_time = time.time() - start_time
        assert search_result.exit_code == 0

        search_data = json.loads(search_result.output)
        assert len(search_data) == num_keys

        print(f"Searched {len(search_data)} keys in {search_time:.2f}s")
        if search_time > max_search_time:
            pytest.fail(f"Search time {search_time:.2f}s exceeds target {max_search_time}s")

        # Test CSV export performance with large dataset
        print("\n=== Testing CSV export performance ===")
        start_time = time.time()

        csv_result = cli_runner.invoke(main, ["list", "--format", "csv"])

        csv_time = time.time() - start_time
        assert csv_result.exit_code == 0

        csv_lines = csv_result.output.strip().split("\n")
        assert len(csv_lines) >= num_keys + 1  # +1 for header

        print(f"Exported {len(csv_lines)} CSV lines in {csv_time:.2f}s")

        # Test batch status checks
        print("\n=== Testing batch status checks ===")
        start_time = time.time()

        # Check status of every 10th key
        sample_keys = created_keys[::10]
        for key_data in sample_keys:
            show_result = cli_runner.invoke(main, ["show", key_data["id"], "--format", "json"])
            assert show_result.exit_code == 0

        batch_time = time.time() - start_time
        print(f"Checked {len(sample_keys)} key statuses in {batch_time:.2f}s")

        print("\n=== Performance test completed successfully ===")

    @pytest.mark.slow()
    async def test_memory_usage_large_dataset(self, cli_runner, patch_cli_database, repository):
        """
        Test memory usage patterns with large datasets.

        This test ensures the CLI doesn't have memory leaks or excessive
        memory usage when handling large numbers of API keys.
        """
        import os

        import psutil

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        print(f"\nInitial memory usage: {initial_memory:.2f} MB")

        # Create a moderate number of keys for memory testing
        num_keys = 100

        for i in range(num_keys):
            create_result = cli_runner.invoke(
                main,
                [
                    "create",
                    "--name",
                    f"Memory Test Key {i:03d}",
                    "--email",
                    f"memory{i:03d}@test.com",
                    "--format",
                    "json",
                ],
            )
            assert create_result.exit_code == 0

            # Check memory every 25 keys
            if (i + 1) % 25 == 0:
                current_memory = process.memory_info().rss / 1024 / 1024
                memory_growth = current_memory - initial_memory
                print(f"After {i + 1} keys: {current_memory:.2f} MB (growth: {memory_growth:.2f} MB)")

                # Fail if memory growth is excessive (>50MB for 100 keys is concerning)
                if memory_growth > 50:
                    pytest.fail(f"Excessive memory growth: {memory_growth:.2f} MB after {i + 1} keys")

        # Test memory usage during large list operations
        for _ in range(5):
            list_result = cli_runner.invoke(main, ["list", "--format", "json"])
            assert list_result.exit_code == 0

        final_memory = process.memory_info().rss / 1024 / 1024
        total_growth = final_memory - initial_memory

        print(f"Final memory usage: {final_memory:.2f} MB")
        print(f"Total memory growth: {total_growth:.2f} MB")

        # Should not grow more than 100MB for this test
        assert total_growth < 100, f"Memory growth {total_growth:.2f} MB exceeds 100 MB limit"


@pytest.mark.e2e()
@pytest.mark.requires_docker()
class TestErrorRecoveryWorkflows(TestAPIKeyCLIE2E):
    """Test error recovery and system resilience."""

    async def test_error_recovery_workflow(self, cli_runner, patch_cli_database, repository, monkeypatch):
        """
        Test CLI error recovery in various failure scenarios.

        Simulates various error conditions and verifies the CLI
        handles them gracefully and maintains data consistency.
        """

        # Create a test key to work with
        create_result = cli_runner.invoke(
            main, ["create", "--name", "Error Recovery Test", "--email", "error@test.com", "--format", "json"]
        )

        assert create_result.exit_code == 0
        key_data = json.loads(create_result.output)
        key_id = key_data["id"]

        # Test 1: Handle invalid key ID gracefully
        print("\n=== Test 1: Invalid Key ID ===")
        invalid_result = cli_runner.invoke(main, ["show", "invalid-key-id"])

        assert invalid_result.exit_code == 1
        assert "API key not found" in invalid_result.output

        # Test 2: Handle non-existent key operations
        print("\n=== Test 2: Non-existent Key Operations ===")
        fake_id = "00000000-0000-0000-0000-000000000000"

        operations = [
            ["activate", fake_id],
            ["deactivate", fake_id],
            ["usage", fake_id],
            ["limits", fake_id, "--daily", "100"],
            ["extend", fake_id, "--days", "30"],
        ]

        for operation in operations:
            result = cli_runner.invoke(main, operation)
            assert result.exit_code == 1
            assert "API key not found" in result.output

        # Test 3: Test partial failure recovery in limits update
        print("\n=== Test 3: Partial Failure Recovery ===")

        # First, successfully update limits
        limits_result = cli_runner.invoke(main, ["limits", key_id, "--daily", "1000"])
        assert limits_result.exit_code == 0

        # Verify the key still exists and has correct limits
        show_result = cli_runner.invoke(main, ["show", key_id, "--format", "json"])
        assert show_result.exit_code == 0
        show_data = json.loads(show_result.output)
        assert show_data["limits"]["requests_per_day"] == 1000

        # Test 4: Test operation with no changes specified
        print("\n=== Test 4: No-op Operations ===")

        # Try limits update with no parameters
        noop_result = cli_runner.invoke(main, ["limits", key_id])
        assert noop_result.exit_code == 0
        assert "No limit updates specified" in noop_result.output

        # Test 5: Test data consistency after operations
        print("\n=== Test 5: Data Consistency Verification ===")

        # Perform multiple operations and verify data consistency
        operations_sequence = [
            (["deactivate", key_id], "deactivated successfully"),
            (["activate", key_id], "activated successfully"),
            (["limits", key_id, "--patients", "2000"], "Updated limits"),
            (["extend", key_id, "--days", "60"], "Extended expiration"),
        ]

        for operation, expected_message in operations_sequence:
            result = cli_runner.invoke(main, operation)
            assert result.exit_code == 0
            assert expected_message in result.output

        # Final verification - key should be active with updated settings
        final_show_result = cli_runner.invoke(main, ["show", key_id, "--format", "json"])
        assert final_show_result.exit_code == 0
        final_data = json.loads(final_show_result.output)

        assert final_data["is_active"] is True
        assert final_data["limits"]["patients_per_request"] == 2000
        assert final_data["expires_at"] is not None  # Should have expiration set

        print("\n=== Error recovery test completed successfully ===")

    async def test_concurrent_modification_handling(self, cli_runner, patch_cli_database, repository):
        """
        Test handling of concurrent modifications to the same API key.

        Simulates scenarios where multiple operations might be performed
        on the same key simultaneously.
        """

        # Create a test key
        create_result = cli_runner.invoke(
            main, ["create", "--name", "Concurrent Test Key", "--email", "concurrent@test.com", "--format", "json"]
        )

        assert create_result.exit_code == 0
        key_data = json.loads(create_result.output)
        key_id = key_data["id"]

        # Simulate concurrent operations through repository
        # (CLI runner can't truly do concurrent operations)

        # Test concurrent limit updates
        tasks = []

        async def update_limits_async(max_patients, max_daily):
            """Helper to update limits asynchronously."""
            return await repository.update_limits(
                key_id, max_patients_per_request=max_patients, max_requests_per_day=max_daily
            )

        # Run concurrent updates
        results = await asyncio.gather(
            update_limits_async(1000, 500),
            update_limits_async(2000, 1000),
            update_limits_async(1500, 750),
            return_exceptions=True,
        )

        # At least one should succeed
        successful_updates = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_updates) >= 1

        # Verify final state is consistent
        final_key = await repository.get_by_id(key_id)
        assert final_key is not None
        assert final_key.is_active is True

        # Verify through CLI that key is in consistent state
        show_result = cli_runner.invoke(main, ["show", key_id, "--format", "json"])
        assert show_result.exit_code == 0

        show_data = json.loads(show_result.output)
        assert show_data["name"] == "Concurrent Test Key"
        assert "limits" in show_data


@pytest.mark.e2e()
@pytest.mark.requires_docker()
class TestAutomationWorkflows(TestAPIKeyCLIE2E):
    """Test CLI workflows for automation and scripting."""

    async def test_automation_friendly_workflow(self, cli_runner, patch_cli_database, repository, monkeypatch):
        """
        Test CLI workflows designed for automation and scripting.

        Validates that the CLI can be effectively used in automated
        environments with proper exit codes, JSON output, and
        non-interactive operations.
        """

        # Mock confirmation to always confirm for automation
        def mock_confirm_ask(message):
            return True

        monkeypatch.setattr("rich.prompt.Confirm.ask", mock_confirm_ask)

        # Automation Scenario: Daily key management script
        print("\n=== Automation Scenario: Daily Key Management ===")

        # Step 1: Create keys for automated testing environments
        test_environments = ["staging", "integration", "development"]
        created_keys = {}

        for env in test_environments:
            create_result = cli_runner.invoke(
                main,
                [
                    "create",
                    "--name",
                    f"Automated {env.title()} Key",
                    "--email",
                    f"{env}@automation.test",
                    "--patients",
                    "500",
                    "--daily",
                    "200",
                    "--format",
                    "json",
                ],
            )

            assert create_result.exit_code == 0
            key_data = json.loads(create_result.output)
            created_keys[env] = key_data

            print(f"Created {env} key: {key_data['id']}")

        # Step 2: Automated health check - verify all keys are active
        print("\n=== Step 2: Automated Health Check ===")

        for env, key_data in created_keys.items():
            show_result = cli_runner.invoke(main, ["show", key_data["id"], "--format", "json"])

            assert show_result.exit_code == 0
            show_data = json.loads(show_result.output)
            assert show_data["is_active"] is True

            print(f"{env} key health: OK")

        # Step 3: Automated usage monitoring
        print("\n=== Step 3: Usage Monitoring ===")

        # Simulate some usage
        for env, key_data in created_keys.items():
            usage_amount = {"staging": 50, "integration": 30, "development": 100}
            await repository.update_usage(
                key_data["id"], patients_generated=usage_amount[env], request_count=usage_amount[env] // 5
            )

        # Generate automated report
        stats_result = cli_runner.invoke(main, ["stats", "--format", "json"])

        assert stats_result.exit_code == 0
        stats_data = json.loads(stats_result.output)

        print(f"System statistics generated: {stats_data['generated_at']}")

        # Step 4: Automated key rotation based on age
        print("\n=== Step 4: Automated Key Rotation ===")

        # Rotate the staging key as part of security policy
        staging_key = created_keys["staging"]
        rotate_result = cli_runner.invoke(main, ["rotate", staging_key["id"], "--name", "Automated Staging Key v2"])

        assert rotate_result.exit_code == 0
        assert "rotated successfully" in rotate_result.output

        # Extract new key from output for automation
        output_lines = rotate_result.output.split("\n")
        new_key_line = [line for line in output_lines if "New API Key:" in line][0]
        new_key = new_key_line.split("New API Key: ")[1].strip()

        print(f"Rotated staging key, new key: {new_key[:16]}...")

        # Step 5: Automated cleanup of expired keys
        print("\n=== Step 5: Automated Cleanup ===")

        # First do a dry run for safety
        cleanup_dry_result = cli_runner.invoke(main, ["cleanup", "--dry-run"])

        assert cleanup_dry_result.exit_code == 0
        print("Cleanup dry run completed")

        # Step 6: Generate automation report in multiple formats
        print("\n=== Step 6: Generate Reports ===")

        # JSON report for further processing
        json_report_result = cli_runner.invoke(main, ["list", "--format", "json"])
        assert json_report_result.exit_code == 0
        json_report = json.loads(json_report_result.output)

        # CSV report for spreadsheet analysis
        csv_report_result = cli_runner.invoke(main, ["list", "--format", "csv"])
        assert csv_report_result.exit_code == 0

        print(f"Generated reports: {len(json_report)} keys in JSON, CSV exported")

        # Step 7: Verify automation exit codes
        print("\n=== Step 7: Exit Code Validation ===")

        # Test various scenarios to ensure proper exit codes for automation
        test_cases = [
            (["list"], 0),  # Success
            (["show", "nonexistent-id"], 1),  # Error
            (["stats"], 0),  # Success
            (["cleanup", "--dry-run"], 0),  # Success
        ]

        for command, expected_exit_code in test_cases:
            result = cli_runner.invoke(main, command)
            assert result.exit_code == expected_exit_code
            print(f"Command {' '.join(command)}: exit code {result.exit_code} ✓")

        print("\n=== Automation workflow completed successfully ===")

    async def test_ci_cd_integration_workflow(self, cli_runner, patch_cli_database, repository, monkeypatch):
        """
        Test CLI integration in CI/CD pipeline scenarios.

        Simulates how the CLI would be used in continuous integration
        and deployment pipelines.
        """

        def mock_confirm_ask(message):
            return True

        monkeypatch.setattr("rich.prompt.Confirm.ask", mock_confirm_ask)

        print("\n=== CI/CD Integration Workflow ===")

        # CI/CD Step 1: Create temporary keys for testing
        print("\n=== CI Step 1: Create Test Keys ===")

        test_key_result = cli_runner.invoke(
            main,
            [
                "create",
                "--name",
                "CI Test Key",
                "--demo",
                "--patients",
                "100",
                "--daily",
                "50",
                "--expires-days",
                "1",  # Short-lived for CI
                "--format",
                "json",
            ],
        )

        assert test_key_result.exit_code == 0
        test_key_data = json.loads(test_key_result.output)
        test_key_id = test_key_data["id"]
        test_api_key = test_key_data["key"]

        print(f"Created CI test key: {test_key_id}")

        # CI/CD Step 2: Validate key properties for testing
        print("\n=== CI Step 2: Validate Test Key ===")

        validate_result = cli_runner.invoke(main, ["show", test_key_id, "--format", "json"])

        assert validate_result.exit_code == 0
        validate_data = json.loads(validate_result.output)

        # Verify test key has proper restrictions
        assert validate_data["is_demo"] is True
        assert validate_data["limits"]["patients_per_request"] == 100
        assert validate_data["limits"]["requests_per_day"] == 50
        assert validate_data["expires_at"] is not None

        print("Test key validation: PASSED")

        # CI/CD Step 3: Simulate test usage
        print("\n=== CI Step 3: Simulate Test Usage ===")

        await repository.update_usage(test_key_id, patients_generated=25, request_count=10)

        usage_result = cli_runner.invoke(main, ["usage", test_key_id, "--format", "json"])

        assert usage_result.exit_code == 0
        usage_data = json.loads(usage_result.output)

        print(f"Test usage recorded: {usage_data['usage']['total_patients']} patients")

        # CI/CD Step 4: Create production key (simulated)
        print("\n=== CI Step 4: Create Production Key ===")

        prod_key_result = cli_runner.invoke(
            main,
            [
                "create",
                "--name",
                "Production Key",
                "--email",
                "production@company.com",
                "--patients",
                "5000",
                "--daily",
                "10000",
                "--expires-days",
                "365",
                "--format",
                "json",
            ],
        )

        assert prod_key_result.exit_code == 0
        prod_key_data = json.loads(prod_key_result.output)

        print(f"Created production key: {prod_key_data['id']}")

        # CI/CD Step 5: Cleanup test keys
        print("\n=== CI Step 5: Cleanup Test Keys ===")

        # Remove the test key
        cleanup_result = cli_runner.invoke(main, ["delete", test_key_id, "--confirm"])

        assert cleanup_result.exit_code == 0
        print("Test key cleanup: COMPLETED")

        # CI/CD Step 6: Final validation
        print("\n=== CI Step 6: Final Validation ===")

        # Verify test key is gone
        verify_cleanup_result = cli_runner.invoke(main, ["show", test_key_id])

        assert verify_cleanup_result.exit_code == 1
        assert "API key not found" in verify_cleanup_result.output

        # Verify production key still exists
        verify_prod_result = cli_runner.invoke(main, ["show", prod_key_data["id"], "--format", "json"])

        assert verify_prod_result.exit_code == 0

        print("CI/CD workflow validation: PASSED")
        print("\n=== CI/CD Integration completed successfully ===")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--requires-docker", "-s"])
