"""
Test suite for the API Key CLI tool.

Tests the command-line interface for API key management including:
- Command parsing and validation
- Database operations
- Output formatting
- Error handling
- Interactive confirmation prompts
"""

from datetime import datetime
import json
from pathlib import Path

# Import the CLI module
import sys
from unittest.mock import AsyncMock, MagicMock, patch

from click.testing import CliRunner
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.api_key_cli import APIKeyCLI, main


class TestAPIKeyCLI:
    """Test suite for API Key CLI application class."""

    def test_format_key_display(self):
        """Test API key display formatting for security."""
        cli = APIKeyCLI()

        # Test normal key
        key = "abcdef123456789012345678901234567890abcdef123456789012345678901234"
        expected = "abcdef12...1234"
        assert cli.format_key_display(key) == expected

        # Test short key
        short_key = "short"
        expected_short = "short..."
        assert cli.format_key_display(short_key) == expected_short

        # Test None key
        assert cli.format_key_display(None) == "N/A"

        # Test empty key
        assert cli.format_key_display("") == "N/A"

    def test_format_datetime(self):
        """Test datetime formatting for display."""
        cli = APIKeyCLI()

        # Test normal datetime
        dt = datetime(2024, 1, 15, 14, 30, 45)
        expected = "2024-01-15 14:30:45"
        assert cli.format_datetime(dt) == expected

        # Test None datetime
        assert cli.format_datetime(None) == "Never"

    def test_format_usage_stats(self):
        """Test usage statistics formatting."""
        cli = APIKeyCLI()

        # Create mock API key
        api_key = MagicMock()
        api_key.total_requests = 150
        api_key.total_patients_generated = 2500
        api_key.daily_requests = 25
        api_key.last_used_at = datetime(2024, 1, 15, 14, 30, 45)
        api_key.last_reset_at = datetime(2024, 1, 15, 0, 0, 0)

        result = cli.format_usage_stats(api_key)

        expected = {
            "total_requests": 150,
            "total_patients": 2500,
            "daily_requests": 25,
            "last_used": "2024-01-15 14:30:45",
            "last_reset": "2024-01-15 00:00:00",
        }
        assert result == expected

    def test_format_limits(self):
        """Test rate limits formatting."""
        cli = APIKeyCLI()

        # Create mock API key with limits
        api_key = MagicMock()
        api_key.max_patients_per_request = 1000
        api_key.max_requests_per_day = 500
        api_key.max_requests_per_hour = 100
        api_key.max_requests_per_minute = 10

        result = cli.format_limits(api_key)

        expected = {
            "patients_per_request": 1000,
            "requests_per_day": 500,
            "requests_per_hour": 100,
            "requests_per_minute": 10,
        }
        assert result == expected

        # Test unlimited daily requests
        api_key.max_requests_per_day = None
        result = cli.format_limits(api_key)
        assert result["requests_per_day"] == "Unlimited"


class TestCLICommands:
    """Test suite for CLI command functionality."""

    @pytest.fixture()
    def runner(self):
        """Create Click test runner."""
        return CliRunner()

    @pytest.fixture()
    def mock_api_key(self):
        """Create a mock API key for testing."""
        key = MagicMock()
        key.id = "12345678-1234-1234-1234-123456789012"
        key.key = "test_key_abcdef123456789012345678901234567890abcdef123456789012345678"
        key.name = "Test Key"
        key.email = "test@example.com"
        key.is_active = True
        key.is_demo = False
        key.created_at = datetime(2024, 1, 1, 12, 0, 0)
        key.updated_at = datetime(2024, 1, 15, 14, 30, 0)
        key.expires_at = datetime(2024, 12, 31, 23, 59, 59)
        key.last_used_at = datetime(2024, 1, 15, 14, 30, 45)
        key.last_reset_at = datetime(2024, 1, 15, 0, 0, 0)
        key.total_requests = 150
        key.total_patients_generated = 2500
        key.daily_requests = 25
        key.max_patients_per_request = 1000
        key.max_requests_per_day = 500
        key.max_requests_per_hour = 100
        key.max_requests_per_minute = 10
        key.key_metadata = {"team": "development"}
        return key

    @patch("scripts.api_key_cli.cli_app.initialize")
    @patch("scripts.api_key_cli.cli_app.cleanup")
    @patch("scripts.api_key_cli.cli_app.session_factory")
    def test_create_command_success(self, mock_session_factory, mock_cleanup, mock_initialize, runner, mock_api_key):
        """Test successful API key creation."""
        # Setup mocks
        mock_session = AsyncMock()
        mock_session_factory.return_value.__aenter__.return_value = mock_session
        mock_repository = AsyncMock()

        with patch("scripts.api_key_cli.APIKeyRepository", return_value=mock_repository):
            mock_repository.create_api_key.return_value = mock_api_key

            # Run command
            result = runner.invoke(
                main, ["create", "--name", "Test Key", "--email", "test@example.com", "--format", "json"]
            )

            # Assert result
            assert result.exit_code == 0
            output_data = json.loads(result.output)
            assert output_data["name"] == "Test Key"
            assert output_data["email"] == "test@example.com"
            assert "key" in output_data

    @patch("scripts.api_key_cli.cli_app.initialize")
    @patch("scripts.api_key_cli.cli_app.cleanup")
    @patch("scripts.api_key_cli.cli_app.session_factory")
    def test_list_command_success(self, mock_session_factory, mock_cleanup, mock_initialize, runner, mock_api_key):
        """Test successful API key listing."""
        # Setup mocks
        mock_session = AsyncMock()
        mock_session_factory.return_value.__aenter__.return_value = mock_session
        mock_repository = AsyncMock()

        with patch("scripts.api_key_cli.APIKeyRepository", return_value=mock_repository):
            mock_repository.list_keys.return_value = [mock_api_key]

            # Run command
            result = runner.invoke(main, ["list", "--format", "json"])

            # Assert result
            assert result.exit_code == 0
            output_data = json.loads(result.output)
            assert len(output_data) == 1
            assert output_data[0]["name"] == "Test Key"

    @patch("scripts.api_key_cli.cli_app.initialize")
    @patch("scripts.api_key_cli.cli_app.cleanup")
    @patch("scripts.api_key_cli.cli_app.session_factory")
    def test_show_command_success(self, mock_session_factory, mock_cleanup, mock_initialize, runner, mock_api_key):
        """Test successful API key details display."""
        # Setup mocks
        mock_session = AsyncMock()
        mock_session_factory.return_value.__aenter__.return_value = mock_session
        mock_repository = AsyncMock()

        with patch("scripts.api_key_cli.APIKeyRepository", return_value=mock_repository):
            mock_repository.get_by_id.return_value = mock_api_key

            # Run command
            result = runner.invoke(main, ["show", "12345678-1234-1234-1234-123456789012", "--format", "json"])

            # Assert result
            assert result.exit_code == 0
            output_data = json.loads(result.output)
            assert output_data["name"] == "Test Key"
            assert output_data["is_active"] == True
            assert "usage" in output_data
            assert "limits" in output_data

    @patch("scripts.api_key_cli.cli_app.initialize")
    @patch("scripts.api_key_cli.cli_app.cleanup")
    @patch("scripts.api_key_cli.cli_app.session_factory")
    def test_show_command_not_found(self, mock_session_factory, mock_cleanup, mock_initialize, runner):
        """Test API key show command with non-existent key."""
        # Setup mocks
        mock_session = AsyncMock()
        mock_session_factory.return_value.__aenter__.return_value = mock_session
        mock_repository = AsyncMock()

        with patch("scripts.api_key_cli.APIKeyRepository", return_value=mock_repository):
            mock_repository.get_by_id.return_value = None
            mock_repository.get_by_key.return_value = None

            # Run command
            result = runner.invoke(main, ["show", "nonexistent-key-id"])

            # Assert result
            assert result.exit_code == 1
            assert "API key not found" in result.output

    @patch("scripts.api_key_cli.cli_app.initialize")
    @patch("scripts.api_key_cli.cli_app.cleanup")
    @patch("scripts.api_key_cli.cli_app.session_factory")
    def test_activate_command_success(self, mock_session_factory, mock_cleanup, mock_initialize, runner, mock_api_key):
        """Test successful API key activation."""
        # Setup mocks
        mock_session = AsyncMock()
        mock_session_factory.return_value.__aenter__.return_value = mock_session
        mock_repository = AsyncMock()

        # Make key inactive initially
        mock_api_key.is_active = False

        with patch("scripts.api_key_cli.APIKeyRepository", return_value=mock_repository):
            mock_repository.get_by_id.return_value = mock_api_key
            mock_repository.activate_key.return_value = None

            # Run command
            result = runner.invoke(main, ["activate", "12345678-1234-1234-1234-123456789012"])

            # Assert result
            assert result.exit_code == 0
            assert "activated successfully" in result.output
            mock_repository.activate_key.assert_called_once()

    @patch("scripts.api_key_cli.cli_app.initialize")
    @patch("scripts.api_key_cli.cli_app.cleanup")
    @patch("scripts.api_key_cli.cli_app.session_factory")
    def test_activate_command_already_active(
        self, mock_session_factory, mock_cleanup, mock_initialize, runner, mock_api_key
    ):
        """Test activating an already active API key."""
        # Setup mocks
        mock_session = AsyncMock()
        mock_session_factory.return_value.__aenter__.return_value = mock_session
        mock_repository = AsyncMock()

        # Key is already active
        mock_api_key.is_active = True

        with patch("scripts.api_key_cli.APIKeyRepository", return_value=mock_repository):
            mock_repository.get_by_id.return_value = mock_api_key

            # Run command
            result = runner.invoke(main, ["activate", "12345678-1234-1234-1234-123456789012"])

            # Assert result
            assert result.exit_code == 0
            assert "already active" in result.output
            mock_repository.activate_key.assert_not_called()

    @patch("scripts.api_key_cli.cli_app.initialize")
    @patch("scripts.api_key_cli.cli_app.cleanup")
    @patch("scripts.api_key_cli.cli_app.session_factory")
    def test_deactivate_command_success(
        self, mock_session_factory, mock_cleanup, mock_initialize, runner, mock_api_key
    ):
        """Test successful API key deactivation."""
        # Setup mocks
        mock_session = AsyncMock()
        mock_session_factory.return_value.__aenter__.return_value = mock_session
        mock_repository = AsyncMock()

        # Key is active
        mock_api_key.is_active = True

        with patch("scripts.api_key_cli.APIKeyRepository", return_value=mock_repository):
            mock_repository.get_by_id.return_value = mock_api_key
            mock_repository.deactivate_key.return_value = None

            # Run command
            result = runner.invoke(main, ["deactivate", "12345678-1234-1234-1234-123456789012"])

            # Assert result
            assert result.exit_code == 0
            assert "deactivated successfully" in result.output
            mock_repository.deactivate_key.assert_called_once()

    @patch("scripts.api_key_cli.cli_app.initialize")
    @patch("scripts.api_key_cli.cli_app.cleanup")
    @patch("scripts.api_key_cli.cli_app.session_factory")
    @patch("rich.prompt.Confirm.ask")
    def test_delete_command_with_confirmation(
        self, mock_confirm, mock_session_factory, mock_cleanup, mock_initialize, runner, mock_api_key
    ):
        """Test API key deletion with confirmation."""
        # Setup mocks
        mock_session = AsyncMock()
        mock_session_factory.return_value.__aenter__.return_value = mock_session
        mock_repository = AsyncMock()
        mock_confirm.return_value = True

        with patch("scripts.api_key_cli.APIKeyRepository", return_value=mock_repository):
            mock_repository.get_by_id.return_value = mock_api_key
            mock_repository.delete_key.return_value = None

            # Run command
            result = runner.invoke(main, ["delete", "12345678-1234-1234-1234-123456789012"])

            # Assert result
            assert result.exit_code == 0
            assert "deleted successfully" in result.output
            mock_repository.delete_key.assert_called_once()

    @patch("scripts.api_key_cli.cli_app.initialize")
    @patch("scripts.api_key_cli.cli_app.cleanup")
    @patch("scripts.api_key_cli.cli_app.session_factory")
    @patch("rich.prompt.Confirm.ask")
    def test_delete_command_cancelled(
        self, mock_confirm, mock_session_factory, mock_cleanup, mock_initialize, runner, mock_api_key
    ):
        """Test API key deletion cancelled by user."""
        # Setup mocks
        mock_session = AsyncMock()
        mock_session_factory.return_value.__aenter__.return_value = mock_session
        mock_repository = AsyncMock()
        mock_confirm.return_value = False

        with patch("scripts.api_key_cli.APIKeyRepository", return_value=mock_repository):
            mock_repository.get_by_id.return_value = mock_api_key

            # Run command
            result = runner.invoke(main, ["delete", "12345678-1234-1234-1234-123456789012"])

            # Assert result
            assert result.exit_code == 0
            assert "Operation cancelled" in result.output
            mock_repository.delete_key.assert_not_called()

    @patch("scripts.api_key_cli.cli_app.initialize")
    @patch("scripts.api_key_cli.cli_app.cleanup")
    @patch("scripts.api_key_cli.cli_app.session_factory")
    def test_delete_command_with_confirm_flag(
        self, mock_session_factory, mock_cleanup, mock_initialize, runner, mock_api_key
    ):
        """Test API key deletion with --confirm flag (skip prompt)."""
        # Setup mocks
        mock_session = AsyncMock()
        mock_session_factory.return_value.__aenter__.return_value = mock_session
        mock_repository = AsyncMock()

        with patch("scripts.api_key_cli.APIKeyRepository", return_value=mock_repository):
            mock_repository.get_by_id.return_value = mock_api_key
            mock_repository.delete_key.return_value = None

            # Run command with --confirm flag
            result = runner.invoke(main, ["delete", "12345678-1234-1234-1234-123456789012", "--confirm"])

            # Assert result
            assert result.exit_code == 0
            assert "deleted successfully" in result.output
            mock_repository.delete_key.assert_called_once()

    @patch("scripts.api_key_cli.cli_app.initialize")
    @patch("scripts.api_key_cli.cli_app.cleanup")
    @patch("scripts.api_key_cli.cli_app.session_factory")
    def test_usage_command_success(self, mock_session_factory, mock_cleanup, mock_initialize, runner, mock_api_key):
        """Test successful usage statistics display."""
        # Setup mocks
        mock_session = AsyncMock()
        mock_session_factory.return_value.__aenter__.return_value = mock_session
        mock_repository = AsyncMock()

        with patch("scripts.api_key_cli.APIKeyRepository", return_value=mock_repository):
            mock_repository.get_by_id.return_value = mock_api_key

            # Run command
            result = runner.invoke(main, ["usage", "12345678-1234-1234-1234-123456789012", "--format", "json"])

            # Assert result
            assert result.exit_code == 0
            output_data = json.loads(result.output)
            assert output_data["key_name"] == "Test Key"
            assert "usage" in output_data
            assert "limits" in output_data

    @patch("scripts.api_key_cli.cli_app.initialize")
    @patch("scripts.api_key_cli.cli_app.cleanup")
    @patch("scripts.api_key_cli.cli_app.session_factory")
    def test_stats_command_success(self, mock_session_factory, mock_cleanup, mock_initialize, runner):
        """Test successful statistics display."""
        # Setup mocks
        mock_session = AsyncMock()
        mock_session_factory.return_value.__aenter__.return_value = mock_session
        mock_repository = AsyncMock()

        mock_stats = {"total_keys": 10, "active_keys": 8, "total_requests_today": 150, "total_patients_generated": 2500}

        with patch("scripts.api_key_cli.APIKeyRepository", return_value=mock_repository):
            mock_repository.get_usage_stats.return_value = mock_stats

            # Run command
            result = runner.invoke(main, ["stats", "--format", "json"])

            # Assert result
            assert result.exit_code == 0
            output_data = json.loads(result.output)
            assert output_data["statistics"] == mock_stats

    @patch("scripts.api_key_cli.cli_app.initialize")
    @patch("scripts.api_key_cli.cli_app.cleanup")
    @patch("scripts.api_key_cli.cli_app.session_factory")
    def test_limits_command_success(self, mock_session_factory, mock_cleanup, mock_initialize, runner, mock_api_key):
        """Test successful rate limits update."""
        # Setup mocks
        mock_session = AsyncMock()
        mock_session_factory.return_value.__aenter__.return_value = mock_session
        mock_repository = AsyncMock()

        with patch("scripts.api_key_cli.APIKeyRepository", return_value=mock_repository):
            mock_repository.get_by_id.return_value = mock_api_key
            mock_repository.update_limits.return_value = None

            # Run command
            result = runner.invoke(
                main, ["limits", "12345678-1234-1234-1234-123456789012", "--daily", "1000", "--patients", "2000"]
            )

            # Assert result
            assert result.exit_code == 0
            assert "Updated limits" in result.output
            mock_repository.update_limits.assert_called_once()

    @patch("scripts.api_key_cli.cli_app.initialize")
    @patch("scripts.api_key_cli.cli_app.cleanup")
    @patch("scripts.api_key_cli.cli_app.session_factory")
    def test_limits_command_no_updates(self, mock_session_factory, mock_cleanup, mock_initialize, runner, mock_api_key):
        """Test limits command with no updates specified."""
        # Setup mocks
        mock_session = AsyncMock()
        mock_session_factory.return_value.__aenter__.return_value = mock_session
        mock_repository = AsyncMock()

        with patch("scripts.api_key_cli.APIKeyRepository", return_value=mock_repository):
            mock_repository.get_by_id.return_value = mock_api_key

            # Run command with no limit options
            result = runner.invoke(main, ["limits", "12345678-1234-1234-1234-123456789012"])

            # Assert result
            assert result.exit_code == 0
            assert "No limit updates specified" in result.output
            mock_repository.update_limits.assert_not_called()

    @patch("scripts.api_key_cli.cli_app.initialize")
    @patch("scripts.api_key_cli.cli_app.cleanup")
    @patch("scripts.api_key_cli.cli_app.session_factory")
    def test_extend_command_success(self, mock_session_factory, mock_cleanup, mock_initialize, runner, mock_api_key):
        """Test successful expiration extension."""
        # Setup mocks
        mock_session = AsyncMock()
        mock_session_factory.return_value.__aenter__.return_value = mock_session
        mock_repository = AsyncMock()

        with patch("scripts.api_key_cli.APIKeyRepository", return_value=mock_repository):
            mock_repository.get_by_id.return_value = mock_api_key
            mock_repository.extend_expiration.return_value = None

            # Run command
            result = runner.invoke(main, ["extend", "12345678-1234-1234-1234-123456789012", "--days", "30"])

            # Assert result
            assert result.exit_code == 0
            assert "Extended expiration" in result.output
            mock_repository.extend_expiration.assert_called_once()

    @patch("scripts.api_key_cli.cli_app.initialize")
    @patch("scripts.api_key_cli.cli_app.cleanup")
    @patch("scripts.api_key_cli.cli_app.session_factory")
    def test_cleanup_command_dry_run(self, mock_session_factory, mock_cleanup, mock_initialize, runner):
        """Test cleanup command with dry run."""
        # Setup mocks
        mock_session = AsyncMock()
        mock_session_factory.return_value.__aenter__.return_value = mock_session
        mock_repository = AsyncMock()

        with patch("scripts.api_key_cli.APIKeyRepository", return_value=mock_repository):
            mock_repository.cleanup_expired_keys.return_value = 3

            # Run command with dry run
            result = runner.invoke(main, ["cleanup", "--dry-run"])

            # Assert result
            assert result.exit_code == 0
            assert "Dry run: Would delete 3 expired" in result.output
            mock_repository.cleanup_expired_keys.assert_called_once_with(dry_run=True)

    @patch("scripts.api_key_cli.cli_app.initialize")
    @patch("scripts.api_key_cli.cli_app.cleanup")
    @patch("scripts.api_key_cli.cli_app.session_factory")
    @patch("rich.prompt.Confirm.ask")
    def test_rotate_command_success(
        self, mock_confirm, mock_session_factory, mock_cleanup, mock_initialize, runner, mock_api_key
    ):
        """Test successful API key rotation."""
        # Setup mocks
        mock_session = AsyncMock()
        mock_session_factory.return_value.__aenter__.return_value = mock_session
        mock_repository = AsyncMock()
        mock_confirm.return_value = True

        # Create new key mock
        new_key = MagicMock()
        new_key.name = "Test Key (Rotated)"
        new_key.key = "new_key_abcdef123456789012345678901234567890abcdef123456789012345678"

        with patch("scripts.api_key_cli.APIKeyRepository", return_value=mock_repository):
            mock_repository.get_by_id.return_value = mock_api_key
            mock_repository.create_api_key.return_value = new_key
            mock_repository.deactivate_key.return_value = None

            # Run command
            result = runner.invoke(main, ["rotate", "12345678-1234-1234-1234-123456789012"])

            # Assert result
            assert result.exit_code == 0
            assert "rotated successfully" in result.output
            assert "New API Key:" in result.output
            mock_repository.create_api_key.assert_called_once()
            mock_repository.deactivate_key.assert_called_once()


class TestCLIErrorHandling:
    """Test suite for CLI error handling scenarios."""

    @pytest.fixture()
    def runner(self):
        """Create Click test runner."""
        return CliRunner()

    @patch("scripts.api_key_cli.cli_app.initialize")
    def test_database_connection_error(self, mock_initialize, runner):
        """Test CLI behavior when database connection fails."""
        mock_initialize.side_effect = Exception("Database connection failed")

        result = runner.invoke(main, ["list"])

        assert result.exit_code == 1
        assert "Error listing API keys" in result.output

    @patch("scripts.api_key_cli.cli_app.initialize")
    @patch("scripts.api_key_cli.cli_app.cleanup")
    @patch("scripts.api_key_cli.cli_app.session_factory")
    def test_repository_error_handling(self, mock_session_factory, mock_cleanup, mock_initialize, runner):
        """Test CLI behavior when repository operations fail."""
        # Setup mocks
        mock_session = AsyncMock()
        mock_session_factory.return_value.__aenter__.return_value = mock_session
        mock_repository = AsyncMock()

        with patch("scripts.api_key_cli.APIKeyRepository", return_value=mock_repository):
            mock_repository.list_keys.side_effect = Exception("Database error")

            # Run command
            result = runner.invoke(main, ["list"])

            # Assert error handling
            assert result.exit_code == 1
            assert "Error listing API keys" in result.output


if __name__ == "__main__":
    pytest.main([__file__])
