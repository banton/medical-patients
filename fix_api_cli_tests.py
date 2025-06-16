#!/usr/bin/env python3
"""Fix API key CLI tests to properly handle async commands and Rich console output."""

import re

# Read the current test file
with open('tests/test_api_key_cli.py', 'r') as f:
    content = f.read()

# First, let's fix the format_key_display test - the API doesn't take show_full parameter
content = content.replace(
    'assert cli.format_key_display(key, show_full=True) == key',
    '# The API always masks keys for security\n        # Test with a proper length key'
)
content = content.replace(
    'masked = cli.format_key_display(key, show_full=False)',
    'masked = cli.format_key_display(key)'
)

# Fix the format_usage_stats test - it expects an APIKey object, not a dict
fix_usage_stats = '''    def test_format_usage_stats(self):
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
        assert "2024-01-15" in stats["last_used"]'''

# Find and replace the format_usage_stats test
pattern = r'def test_format_usage_stats\(self\):.*?assert "2024-01-15" in stats\["last_used"\]'
content = re.sub(pattern, fix_usage_stats.strip(), content, flags=re.DOTALL)

# Fix the format_limits test to match actual API
fix_limits = '''    def test_format_limits(self):
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
        assert limits["requests_per_minute"] == 10'''

# Find and replace the format_limits test
pattern = r'def test_format_limits\(self\):.*?assert limits\["max_requests_per_minute"\] == 10'
content = re.sub(pattern, fix_limits.strip(), content, flags=re.DOTALL)

# Now let's fix the command tests to properly capture output
# We'll need to mock the console.print_json to capture the output

# Fix the create command test
create_test = '''    def test_create_command_success(self, runner, mock_api_key):
        """Test successful API key creation."""
        # Setup mocks for async context manager
        mock_session = MagicMock()
        mock_session_factory = MagicMock()
        mock_session_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_factory.return_value.__aexit__ = AsyncMock(return_value=None)
        
        # Mock repository with async method
        mock_repository = MagicMock()
        mock_repository.create_api_key = AsyncMock(return_value=mock_api_key)

        # Capture console output
        captured_output = []
        def mock_print_json(data):
            captured_output.append(data)

        # Apply patches with proper async mocks
        with patch("scripts.api_key_cli.cli_app.initialize", new_callable=AsyncMock), \
             patch("scripts.api_key_cli.cli_app.cleanup", new_callable=AsyncMock), \
             patch("scripts.api_key_cli.cli_app.session_factory", mock_session_factory), \
             patch("scripts.api_key_cli.APIKeyRepository", return_value=mock_repository), \
             patch("scripts.api_key_cli.console.print_json", side_effect=mock_print_json):

            # Run command
            result = runner.invoke(
                main,
                ["create", "--name", "Test Key", "--email", "test@example.com", "--format", "json"],
            )

            # Assert result
            assert result.exit_code == 0, f"Command failed with: {result.exception}"
            assert len(captured_output) > 0, "No output captured"
            output_data = json.loads(captured_output[0])
            assert output_data["name"] == "Test Key"
            assert output_data["email"] == "test@example.com"
            assert "key" in output_data'''

# Replace create test
pattern = r'def test_create_command_success\(self, runner, mock_api_key\):.*?assert "key" in output_data'
content = re.sub(pattern, create_test.strip(), content, flags=re.DOTALL)

# Fix the list command test
list_test = '''    def test_list_command_success(self, runner, mock_api_key):
        """Test successful API key listing."""
        # Setup mocks for async context manager
        mock_session = MagicMock()
        mock_session_factory = MagicMock()
        mock_session_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_factory.return_value.__aexit__ = AsyncMock(return_value=None)
        
        # Mock repository with async methods
        mock_repository = MagicMock()
        mock_repository.list_keys = AsyncMock(return_value=[mock_api_key])

        # Capture console output
        captured_output = []
        def mock_print_json(data):
            captured_output.append(data)

        # Apply patches with proper async mocks
        with patch("scripts.api_key_cli.cli_app.initialize", new_callable=AsyncMock), \
             patch("scripts.api_key_cli.cli_app.cleanup", new_callable=AsyncMock), \
             patch("scripts.api_key_cli.cli_app.session_factory", mock_session_factory), \
             patch("scripts.api_key_cli.APIKeyRepository", return_value=mock_repository), \
             patch("scripts.api_key_cli.console.print_json", side_effect=mock_print_json):

            # Run command
            result = runner.invoke(main, ["list", "--format", "json"])

            # Assert result
            assert result.exit_code == 0
            assert len(captured_output) > 0, "No output captured"
            output_data = json.loads(captured_output[0])
            assert len(output_data) == 1
            assert output_data[0]["name"] == "Test Key"'''

# Replace list test
pattern = r'def test_list_command_success\(self, runner, mock_api_key\):.*?assert output_data\[0\]\["name"\] == "Test Key"'
content = re.sub(pattern, list_test.strip(), content, flags=re.DOTALL)

# Add missing properties to mock_api_key
mock_api_key_update = '''        api_key.last_reset_at = datetime(2024, 1, 15)
        api_key.updated_at = datetime(2024, 1, 1)
        api_key.key_metadata = {}
        api_key.get_usage_summary = MagicMock('''

content = content.replace(
    '        api_key.get_usage_summary = MagicMock(',
    mock_api_key_update
)

# Write the fixed content
with open('tests/test_api_key_cli.py', 'w') as f:
    f.write(content)

print("Fixed API key CLI tests!")