# API Key Management CLI

A comprehensive command-line interface for managing API keys in the Medical Patients Generator system. This tool provides full lifecycle management of API keys including creation, activation/deactivation, usage monitoring, and administrative functions.

## Installation

The CLI tool is included with the Medical Patients Generator installation. Ensure you have the required dependencies:

```bash
pip install click tabulate rich
```

## Quick Start

```bash
# Create a new API key
python scripts/api_key_cli.py create --name "Development Team"

# List all API keys
python scripts/api_key_cli.py list

# Show detailed information about a key
python scripts/api_key_cli.py show <key-id>

# Get help for any command
python scripts/api_key_cli.py <command> --help
```

## Commands Reference

### Key Management

#### `create` - Create New API Key

Create a new API key with specified parameters.

```bash
python scripts/api_key_cli.py create --name "Team Name" [OPTIONS]
```

**Options:**
- `--name TEXT` (required): Human-readable name for the API key
- `--email TEXT`: Contact email for the key holder
- `--demo`: Create a demo key with restricted access
- `--expires-days INTEGER`: Number of days until expiration
- `--patients INTEGER`: Max patients per request (default: 1000)
- `--daily INTEGER`: Max requests per day (default: unlimited)
- `--hourly INTEGER`: Max requests per hour (default: 1000)
- `--minute INTEGER`: Max requests per minute (default: 60)
- `--format [json|table]`: Output format (default: table)

**Examples:**
```bash
# Basic API key
python scripts/api_key_cli.py create --name "Development Team"

# API key with email and expiration
python scripts/api_key_cli.py create \
  --name "Production API" \
  --email "admin@company.com" \
  --expires-days 90

# Demo key with custom limits
python scripts/api_key_cli.py create \
  --name "Demo Access" \
  --demo \
  --patients 100 \
  --daily 50

# Get JSON output for automation
python scripts/api_key_cli.py create \
  --name "Automated System" \
  --format json
```

#### `list` - List API Keys

Display a list of API keys with filtering options.

```bash
python scripts/api_key_cli.py list [OPTIONS]
```

**Options:**
- `--active`: Show only active keys
- `--demo`: Show only demo keys
- `--search TEXT`: Search by name or email
- `--format [json|table|csv]`: Output format (default: table)
- `--limit INTEGER`: Maximum number of keys to display (default: 50)

**Examples:**
```bash
# List all keys
python scripts/api_key_cli.py list

# List only active keys
python scripts/api_key_cli.py list --active

# Search for keys
python scripts/api_key_cli.py list --search "development"

# Export to CSV
python scripts/api_key_cli.py list --format csv > api_keys.csv
```

#### `show` - Show Key Details

Display detailed information about a specific API key.

```bash
python scripts/api_key_cli.py show <key-id> [OPTIONS]
```

**Arguments:**
- `key-id`: API key ID (UUID) or the key string itself

**Options:**
- `--format [json|table]`: Output format (default: table)

**Examples:**
```bash
# Show key details by ID
python scripts/api_key_cli.py show 12345678-1234-1234-1234-123456789012

# Show key details by key string
python scripts/api_key_cli.py show abcdef123456...

# Get JSON output
python scripts/api_key_cli.py show 12345678-1234-1234-1234-123456789012 --format json
```

#### `activate` - Activate API Key

Enable an API key for use.

```bash
python scripts/api_key_cli.py activate <key-id>
```

**Examples:**
```bash
python scripts/api_key_cli.py activate 12345678-1234-1234-1234-123456789012
```

#### `deactivate` - Deactivate API Key

Disable an API key without deleting it.

```bash
python scripts/api_key_cli.py deactivate <key-id>
```

**Examples:**
```bash
python scripts/api_key_cli.py deactivate 12345678-1234-1234-1234-123456789012
```

#### `delete` - Delete API Key

Permanently remove an API key from the system.

```bash
python scripts/api_key_cli.py delete <key-id> [OPTIONS]
```

**Options:**
- `--confirm`: Skip confirmation prompt

**Examples:**
```bash
# Delete with confirmation prompt
python scripts/api_key_cli.py delete 12345678-1234-1234-1234-123456789012

# Delete without confirmation (automation)
python scripts/api_key_cli.py delete 12345678-1234-1234-1234-123456789012 --confirm
```

### Usage Monitoring

#### `usage` - Show Key Usage

Display usage statistics for a specific API key.

```bash
python scripts/api_key_cli.py usage <key-id> [OPTIONS]
```

**Options:**
- `--format [json|table]`: Output format (default: table)

**Examples:**
```bash
# Show usage statistics
python scripts/api_key_cli.py usage 12345678-1234-1234-1234-123456789012

# Get JSON output for monitoring
python scripts/api_key_cli.py usage 12345678-1234-1234-1234-123456789012 --format json
```

#### `stats` - System Statistics

Show overall API usage statistics across all keys.

```bash
python scripts/api_key_cli.py stats [OPTIONS]
```

**Options:**
- `--days INTEGER`: Number of days to include (default: 30)
- `--format [json|table]`: Output format (default: table)

**Examples:**
```bash
# Show 30-day statistics
python scripts/api_key_cli.py stats

# Show last 7 days
python scripts/api_key_cli.py stats --days 7

# Get JSON for reporting
python scripts/api_key_cli.py stats --format json
```

### Rate Limit Management

#### `limits` - Update Rate Limits

Modify rate limits for an existing API key.

```bash
python scripts/api_key_cli.py limits <key-id> [OPTIONS]
```

**Options:**
- `--patients INTEGER`: Max patients per request
- `--daily INTEGER`: Max requests per day
- `--hourly INTEGER`: Max requests per hour
- `--minute INTEGER`: Max requests per minute

**Examples:**
```bash
# Update daily limit
python scripts/api_key_cli.py limits 12345678-1234-1234-1234-123456789012 --daily 1000

# Update multiple limits
python scripts/api_key_cli.py limits 12345678-1234-1234-1234-123456789012 \
  --patients 2000 \
  --daily 500 \
  --hourly 100
```

#### `extend` - Extend Expiration

Extend the expiration date of an API key.

```bash
python scripts/api_key_cli.py extend <key-id> --days <days>
```

**Options:**
- `--days INTEGER` (required): Number of days to extend

**Examples:**
```bash
# Extend by 30 days
python scripts/api_key_cli.py extend 12345678-1234-1234-1234-123456789012 --days 30

# Extend by 1 year
python scripts/api_key_cli.py extend 12345678-1234-1234-1234-123456789012 --days 365
```

### Administrative Functions

#### `cleanup` - Remove Expired Keys

Remove expired API keys from the system.

```bash
python scripts/api_key_cli.py cleanup [OPTIONS]
```

**Options:**
- `--dry-run`: Show what would be deleted without actually deleting

**Examples:**
```bash
# Preview cleanup (safe)
python scripts/api_key_cli.py cleanup --dry-run

# Perform actual cleanup
python scripts/api_key_cli.py cleanup
```

#### `rotate` - Rotate API Key

Create a new API key with the same settings and deactivate the old one.

```bash
python scripts/api_key_cli.py rotate <key-id> [OPTIONS]
```

**Options:**
- `--name TEXT`: Name for the new API key (defaults to old name + " (Rotated)")

**Examples:**
```bash
# Rotate with automatic naming
python scripts/api_key_cli.py rotate 12345678-1234-1234-1234-123456789012

# Rotate with custom name
python scripts/api_key_cli.py rotate 12345678-1234-1234-1234-123456789012 --name "Production API v2"
```

## Output Formats

The CLI supports multiple output formats for different use cases:

### Table Format (Default)
Human-readable table format suitable for interactive use.

### JSON Format
Machine-readable JSON output perfect for automation and integration.

```bash
python scripts/api_key_cli.py list --format json | jq '.[] | select(.is_active == true)'
```

### CSV Format (List Only)
Comma-separated values format for data analysis and reporting.

```bash
python scripts/api_key_cli.py list --format csv > api_keys.csv
```

## Security Considerations

### Key Display
- API keys are never displayed in full
- Only the first 8 and last 4 characters are shown (e.g., "abcdef12...1234")
- Full keys are only shown during creation and rotation

### Confirmation Prompts
- Destructive operations (delete, rotate) require confirmation
- Use `--confirm` flag to skip prompts for automation

### Access Control
- The CLI requires database access
- Ensure proper database credentials are configured
- Limit CLI access to authorized administrators only

## Common Workflows

### Initial Setup
```bash
# Create initial admin API key
python scripts/api_key_cli.py create \
  --name "Administrator" \
  --email "admin@company.com" \
  --patients 5000 \
  --daily 10000

# Create demo key for testing
python scripts/api_key_cli.py create \
  --name "Demo Access" \
  --demo \
  --patients 100 \
  --daily 50
```

### Regular Monitoring
```bash
# Check overall system usage
python scripts/api_key_cli.py stats

# List all active keys
python scripts/api_key_cli.py list --active

# Check usage for high-volume keys
python scripts/api_key_cli.py usage <key-id>
```

### Key Rotation (Security Best Practice)
```bash
# Rotate production keys quarterly
python scripts/api_key_cli.py rotate <old-key-id> --name "Production Q2 2024"

# Update client systems with new key
# Verify new key is working
# Clean up old keys
python scripts/api_key_cli.py cleanup --dry-run
python scripts/api_key_cli.py cleanup
```

### Automation Scripts

#### Daily Usage Report
```bash
#!/bin/bash
# daily_report.sh
echo "Daily API Usage Report - $(date)"
echo "=================================="

python scripts/api_key_cli.py stats --days 1 --format json | \
  jq -r '"Total Requests: " + (.statistics.total_requests_today // 0 | tostring)'

echo ""
echo "Active API Keys:"
python scripts/api_key_cli.py list --active --format table
```

#### Weekly Cleanup
```bash
#!/bin/bash
# weekly_cleanup.sh
echo "Weekly API Key Cleanup - $(date)"
echo "Expired keys to be removed:"

python scripts/api_key_cli.py cleanup --dry-run

echo ""
read -p "Proceed with cleanup? (y/N): " confirm
if [[ $confirm == [yY] ]]; then
    python scripts/api_key_cli.py cleanup
    echo "Cleanup completed."
else
    echo "Cleanup cancelled."
fi
```

## Error Handling

The CLI provides detailed error messages for common issues:

- **Database Connection Errors**: Check DATABASE_URL configuration
- **Key Not Found**: Verify the key ID or key string is correct
- **Permission Errors**: Ensure proper database access credentials
- **Validation Errors**: Check command arguments and options

## Integration with CI/CD

### GitHub Actions Example
```yaml
- name: Create API Key for Testing
  run: |
    python scripts/api_key_cli.py create \
      --name "CI Test Key" \
      --demo \
      --patients 100 \
      --daily 50 \
      --format json > test_key.json
    
    echo "TEST_API_KEY=$(jq -r '.key' test_key.json)" >> $GITHUB_ENV

- name: Cleanup Test Keys
  if: always()
  run: |
    python scripts/api_key_cli.py list --search "CI Test" --format json | \
      jq -r '.[].id' | \
      xargs -I {} python scripts/api_key_cli.py delete {} --confirm
```

## Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   # Ensure dependencies are installed
   pip install click tabulate rich
   ```

2. **Database Connection Issues**
   ```bash
   # Check database configuration
   echo $DATABASE_URL
   
   # Test database connectivity
   python -c "import config; print(config.DATABASE_URL)"
   ```

3. **Permission Denied**
   ```bash
   # Make script executable
   chmod +x scripts/api_key_cli.py
   ```

### Getting Help

```bash
# General help
python scripts/api_key_cli.py --help

# Command-specific help
python scripts/api_key_cli.py create --help
python scripts/api_key_cli.py list --help
```

## Contributing

When extending the CLI:

1. Follow existing command patterns
2. Add comprehensive tests in `tests/test_api_key_cli.py`
3. Update this documentation
4. Ensure all output formats (table, JSON, CSV) are supported where applicable

---

*For more information about the Medical Patients Generator system, see the main [README.md](../README.md) and [API documentation](../docs/api.md).*