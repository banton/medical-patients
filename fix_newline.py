#!/usr/bin/env python3
"""Fix file ending."""

with open('tests/test_api_key_cli.py', 'r') as f:
    content = f.read()

# Ensure file ends with newline
if not content.endswith('\n'):
    content += '\n'

with open('tests/test_api_key_cli.py', 'w') as f:
    f.write(content)

print("Fixed file ending")