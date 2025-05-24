# Environment Configuration Guide

This document describes the environment variables used by the Military Medical Exercise Patient Generator application.

## Quick Start

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and set your values:
   ```bash
   nano .env  # or use your preferred editor
   ```

3. For Docker deployments, the variables will be automatically loaded.

## Environment Variables

### Security

- **`API_KEY`** (required in production)
  - Description: API key for securing configuration endpoints
  - Default: `your_secret_api_key_here` (development only)
  - Example: `API_KEY=a-long-secure-random-string`
  - **Important**: Always set a secure value in production!

### Database

- **`DATABASE_URL`**
  - Description: PostgreSQL connection string
  - Default: `postgresql://patient_user:patient_pass@localhost:5432/patient_generator`
  - Format: `postgresql://[user]:[password]@[host]:[port]/[database]`

### Application Settings

- **`DEBUG`**
  - Description: Enable debug mode
  - Default: `False`
  - Values: `True`, `False`, `1`, `0`, `yes`, `no`

- **`APP_NAME`**
  - Description: Application name shown in API docs
  - Default: `Military Medical Exercise Patient Generator`

### CORS Configuration

- **`CORS_ORIGINS`**
  - Description: Comma-separated list of allowed origins for CORS
  - Default: `http://localhost:3000,http://localhost:8000`
  - Example: `https://app.example.com,https://api.example.com`

### File Storage

- **`OUTPUT_DIRECTORY`**
  - Description: Directory for generated patient files
  - Default: `output`
  - Note: Directory will be created if it doesn't exist

- **`TEMP_DIRECTORY`**
  - Description: Directory for temporary files during generation
  - Default: `temp`
  - Note: Directory will be created if it doesn't exist

### Generation Limits

- **`MAX_PATIENTS_PER_JOB`**
  - Description: Maximum number of patients allowed per generation job
  - Default: `10000`
  - Type: Integer

- **`JOB_TIMEOUT_SECONDS`**
  - Description: Maximum time allowed for a generation job (in seconds)
  - Default: `3600` (1 hour)
  - Type: Integer

### Optional Settings

- **`DEFAULT_ENCRYPTION_PASSWORD`**
  - Description: Default password for file encryption if not provided per-job
  - Default: None (must be provided per-job if encryption is used)
  - Note: Only use for development/testing

## Docker Configuration

When using Docker Compose, environment variables can be set in multiple ways:

1. **Using an `.env` file** (recommended):
   ```bash
   # .env file in project root
   API_KEY=my-secure-api-key
   DEBUG=False
   ```

2. **Using shell environment**:
   ```bash
   export API_KEY=my-secure-api-key
   docker-compose up
   ```

3. **Inline with docker-compose**:
   ```bash
   API_KEY=my-secure-api-key docker-compose up
   ```

## Frontend Configuration

The frontend requires the API key to make authenticated requests. During deployment:

1. **Development**: Uses the default key from `static/js/api-config.js`
2. **Production**: Replace the file during build/deployment:
   ```javascript
   window.API_CONFIG = {
       API_KEY: 'your-production-api-key',
       API_BASE_URL: 'https://api.yourdomain.com'
   };
   ```

## Security Best Practices

1. **Never commit real API keys** to version control
2. **Use strong, random API keys** in production (e.g., 32+ characters)
3. **Rotate API keys** regularly
4. **Use secrets management** tools in production (e.g., AWS Secrets Manager, Vault)
5. **Restrict CORS origins** to only trusted domains in production

## Troubleshooting

### API Key Issues
- **401 Unauthorized**: Check that the API_KEY environment variable is set correctly
- **CORS errors**: Ensure your frontend origin is included in CORS_ORIGINS

### Database Connection
- **Connection refused**: Check DATABASE_URL host and port
- **Authentication failed**: Verify username and password in DATABASE_URL

### File Permissions
- **Cannot write to output directory**: Ensure the application has write permissions to OUTPUT_DIRECTORY
- **Temp file errors**: Check TEMP_DIRECTORY permissions

## Example Production Configuration

```bash
# Production .env file
API_KEY=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0
DATABASE_URL=postgresql://prod_user:strong_password@db.internal:5432/patient_gen_prod
DEBUG=False
CORS_ORIGINS=https://medical-exercise.mil,https://api.medical-exercise.mil
OUTPUT_DIRECTORY=/var/data/patient-output
TEMP_DIRECTORY=/var/tmp/patient-gen
MAX_PATIENTS_PER_JOB=50000
JOB_TIMEOUT_SECONDS=7200
```