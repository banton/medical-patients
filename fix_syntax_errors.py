#!/usr/bin/env python3
"""Fix syntax errors in the test file."""

import re

# Read the test file
with open('tests/test_api_key_cli.py', 'r') as f:
    content = f.read()

# Fix missing closing parentheses for AsyncMock calls
content = re.sub(r'(mock_repository\.\w+) = AsyncMock\(return_value=([^)]+)$', r'\1 = AsyncMock(return_value=\2)', content, flags=re.MULTILINE)

# Fix specific patterns that are broken
patterns_to_fix = [
    (r'mock_repository\.list_keys = AsyncMock\(return_value=\[mock_api_key\]$', 
     'mock_repository.list_keys = AsyncMock(return_value=[mock_api_key])'),
    (r'mock_repository\.get_by_id = AsyncMock\(return_value=mock_api_key$',
     'mock_repository.get_by_id = AsyncMock(return_value=mock_api_key)'),
    (r'mock_repository\.get_by_key = AsyncMock\(return_value=None$',
     'mock_repository.get_by_key = AsyncMock(return_value=None)'),
    (r'mock_repository\.activate_key = AsyncMock\(return_value=None$',
     'mock_repository.activate_key = AsyncMock(return_value=None)'),
    (r'mock_repository\.deactivate_key = AsyncMock\(return_value=None$',
     'mock_repository.deactivate_key = AsyncMock(return_value=None)'),
    (r'mock_repository\.delete_key = AsyncMock\(return_value=None$',
     'mock_repository.delete_key = AsyncMock(return_value=None)'),
    (r'mock_repository\.update_limits = AsyncMock\(return_value=None$',
     'mock_repository.update_limits = AsyncMock(return_value=None)'),
    (r'mock_repository\.extend_expiration = AsyncMock\(return_value=None$',
     'mock_repository.extend_expiration = AsyncMock(return_value=None)'),
    (r'mock_repository\.cleanup_expired_keys = AsyncMock\(return_value=3$',
     'mock_repository.cleanup_expired_keys = AsyncMock(return_value=3)'),
    (r'mock_repository\.get_usage_stats = AsyncMock\(return_value=mock_stats$',
     'mock_repository.get_usage_stats = AsyncMock(return_value=mock_stats)'),
    (r'mock_repository\.create_api_key = AsyncMock\(return_value=new_key$',
     'mock_repository.create_api_key = AsyncMock(return_value=new_key)'),
]

for pattern, replacement in patterns_to_fix:
    content = re.sub(pattern, replacement, content, flags=re.MULTILINE)

# Also fix the broken decorator lines
content = re.sub(r'@patch\("scripts\.api_key_cli\.cli_app\.\w+"\)$', '', content, flags=re.MULTILINE)

# Fix indentation issues after the with statements
lines = content.split('\n')
fixed_lines = []
for i, line in enumerate(lines):
    # Skip empty lines after with blocks
    if line.strip() == '' and i > 0 and lines[i-1].strip().startswith('with patch'):
        continue
    fixed_lines.append(line)

content = '\n'.join(fixed_lines)

# Write the fixed content back
with open('tests/test_api_key_cli.py', 'w') as f:
    f.write(content)

print("Fixed syntax errors in API key CLI tests!")