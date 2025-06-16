#!/usr/bin/env python3
"""Script to fix all CLI test methods to use proper async mocking."""

import re

# Read the test file
with open('tests/test_api_key_cli.py', 'r') as f:
    content = f.read()

# Pattern to match test methods with decorators
pattern = r'(@patch\("scripts\.api_key_cli\.cli_app\.initialize"\)\s*' + \
          r'@patch\("scripts\.api_key_cli\.cli_app\.cleanup"\)\s*' + \
          r'@patch\("scripts\.api_key_cli\.cli_app\.session_factory"\)\s*' + \
          r'def test_\w+\(self, mock_session_factory, mock_cleanup, mock_initialize, runner(?:, \w+)*\):)'

# Find all matches
matches = list(re.finditer(pattern, content, re.MULTILINE | re.DOTALL))

# Process from end to beginning to maintain positions
for match in reversed(matches):
    # Extract the method signature
    full_match = match.group(0)
    method_match = re.search(r'def (test_\w+)\(self, mock_session_factory, mock_cleanup, mock_initialize, runner((?:, \w+)*)\):', full_match)
    
    if method_match:
        method_name = method_match.group(1)
        extra_params = method_match.group(2)
        
        # Create the new method signature without decorators
        new_signature = f'def {method_name}(self, runner{extra_params}):'
        
        # Replace the decorated method with undecorated version
        start = match.start()
        end = match.end()
        content = content[:start] + new_signature + content[end:]

# Now fix the mock setup in each test method
# Pattern to find the mock setup block
setup_pattern = r'(def test_\w+\(self, runner(?:, \w+)*\):\s*"""[^"]*"""\s*# Setup mocks\s*)(mock_session = AsyncMock\(\)\s*mock_session_factory\.return_value\.__aenter__\.return_value = mock_session\s*mock_repository = AsyncMock\(\))'

# Replace with proper setup
def replace_mock_setup(match):
    prefix = match.group(1)
    new_setup = '''# Setup mocks for async context manager
        mock_session = MagicMock()
        mock_session_factory = MagicMock()
        mock_session_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_factory.return_value.__aexit__ = AsyncMock(return_value=None)
        
        # Mock repository with async methods
        mock_repository = MagicMock()'''
    return prefix + new_setup

content = re.sub(setup_pattern, replace_mock_setup, content)

# Fix the with patch blocks
patch_pattern = r'with patch\("scripts\.api_key_cli\.APIKeyRepository", return_value=mock_repository\):'

new_patch_block = '''# Apply patches with proper async mocks
        with patch("scripts.api_key_cli.cli_app.initialize", new_callable=AsyncMock) as mock_initialize, \\
             patch("scripts.api_key_cli.cli_app.cleanup", new_callable=AsyncMock) as mock_cleanup, \\
             patch("scripts.api_key_cli.cli_app.session_factory", mock_session_factory), \\
             patch("scripts.api_key_cli.APIKeyRepository", return_value=mock_repository):'''

content = content.replace('        with patch("scripts.api_key_cli.APIKeyRepository", return_value=mock_repository):', new_patch_block)

# Fix specific async method mocks
content = re.sub(r'mock_repository\.(\w+)\.return_value = ', r'mock_repository.\1 = AsyncMock(return_value=', content)

# Write the fixed content back
with open('tests/test_api_key_cli.py', 'w') as f:
    f.write(content)

print("Fixed API key CLI tests!")