"""
Simplified test suite for the API Key CLI tool.

Tests the command-line interface focusing on testable components.
"""

from datetime import datetime
import json
from pathlib import Path
import sys
from unittest.mock import AsyncMock, MagicMock, patch

from click.testing import CliRunner
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.api_key_cli import APIKeyCLI, main


class TestAPIKeyCLI:
    """Test suite for API Key CLI application class."""

    def test_format_key_display(self):
        """Test formatting API key for display."""
        cli = APIKeyCLI()

        # Test with proper length key
        key = "sk-1234567890abcdef1234567890abcdef"
        masked = cli.format_key_display(key)
        assert masked.startswith("sk-12345...")
        assert masked.endswith("...cdef")
        assert len(masked) < len(key)

        # Test with empty key
        assert cli.format_key_display("") == "N/A"
        assert cli.format_key_display(None) == "N/A"

    def test_format_datetime(self):
        """Test datetime formatting."""
        cli = APIKeyCLI()

        # Test with datetime
        dt = datetime(2024, 1, 15, 10, 30, 45)
        formatted = cli.format_datetime(dt)
        assert "2024-01-15" in formatted
        assert "10:30:45" in formatted

        # Test with None
        assert cli.format_datetime(None) == "Never"

    def test_format_usage_stats(self):
        """Test usage statistics formatting."""
        cli = APIKeyCLI()

        # Create mock API key
        api_key = MagicMock()
        api_key.total_requests = 100
        api_key.total_patients_generated = 5000
        api_key.daily_requests = 50
        api_key.last_used_at = datetime(2024, 1, 15, 10, 30, 45)
        api_key.last_reset_at = datetime(2024, 1, 15, 0, 0, 0)

        stats = cli.format_usage_stats(api_key)
        assert stats["total_requests"] == 100
        assert stats["total_patients"] == 5000
        assert stats["daily_requests"] == 50
        assert "2024-01-15" in stats["last_used"]

    def test_format_limits(self):
        """Test rate limit formatting."""
        cli = APIKeyCLI()

        # Create mock API key with limits
        api_key = MagicMock()
        api_key.max_patients_per_request = 1000
        api_key.max_requests_per_day = 100
        api_key.max_requests_per_hour = 50
        api_key.max_requests_per_minute = 10

        limits = cli.format_limits(api_key)
        assert limits["patients_per_request"] == 1000
        assert limits["requests_per_day"] == 100
        assert limits["requests_per_hour"] == 50
        assert limits["requests_per_minute"] == 10

        # Test with unlimited daily requests
        api_key.max_requests_per_day = None
        limits = cli.format_limits(api_key)
        assert limits["requests_per_day"] == "Unlimited"


class TestCLIHelp:
    """Test CLI help and command structure."""

    @pytest.fixture
    def runner(self):
        """Create a CLI test runner."""
        return CliRunner()

    def test_main_help(self, runner):
        """Test main help message."""
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "Medical Patients Generator API Key Management CLI" in result.output

    def test_create_help(self, runner):
        """Test create command help."""
        result = runner.invoke(main, ["create", "--help"])
        assert result.exit_code == 0
        assert "Create a new API key" in result.output
        assert "--name" in result.output
        assert "--email" in result.output

    def test_list_help(self, runner):
        """Test list command help."""
        result = runner.invoke(main, ["list", "--help"])
        assert result.exit_code == 0
        assert "List API keys" in result.output
        assert "--active" in result.output
        assert "--format" in result.output

    def test_show_help(self, runner):
        """Test show command help."""
        result = runner.invoke(main, ["show", "--help"])
        assert result.exit_code == 0
        assert "Show detailed information" in result.output
        assert "KEY_ID" in result.output

    def test_invalid_command(self, runner):
        """Test invalid command."""
        result = runner.invoke(main, ["invalid-command"])
        assert result.exit_code == 2
        assert "Error" in result.output or "No such command" in result.output

    def test_missing_required_arg(self, runner):
        """Test missing required argument."""
        result = runner.invoke(main, ["show"])
        assert result.exit_code == 2
        assert "Missing argument" in result.output