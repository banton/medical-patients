# Docker CI Patterns & Requirements

## Overview
This document outlines the Docker build process, CI requirements, and testing patterns for the Medical Patients Generator project. Use this as a reference for future PRs and Docker-related changes.

## Docker Build Process

### Local Development
```bash
# Test Docker build locally before pushing
docker build -t medical-patients-test .

# Verify the build works
docker run --rm medical-patients-test --help

# Clean up test image
docker rmi medical-patients-test
```

### CI Pipeline Integration
The Docker build is integrated into the CI pipeline as the final validation step:

1. **Dependencies**: Docker build only runs after all tests pass
   - `needs: [test, test-integration]`
   - Ensures code quality before containerization

2. **Build Configuration**:
   - **Platform**: `linux/amd64` (single platform for faster CI)
   - **Mode**: Test-only (no registry push)
   - **Caching**: GitHub Actions cache enabled for faster builds

3. **No Registry Dependencies**: 
   - Removed Docker Hub login requirements
   - No external secrets needed
   - Build validates container creation only

## CI Requirements for PRs

### All PRs Must Pass These 5 Jobs:

#### 1. Lint and Format ✅
- **Python**: `ruff check` and `mypy` type checking
- **JavaScript**: ESLint and Prettier formatting
- **Files**: `src/`, `patient_generator/`, `static/js/`
- **Dependencies**: Python 3.10, Node.js 18

#### 2. Test (Unit Tests) ✅
- **Command**: `pytest tests/ -v -m "not integration and not e2e"`
- **Coverage**: Includes `--cov=src --cov=patient_generator`
- **Services**: PostgreSQL 14, Redis 7
- **Tests**: 43+ unit tests covering core functionality
- **Files**: All `test_*.py` files except integration/e2e

#### 3. Integration Tests ✅
- **Command**: `./run_tests.sh integration`
- **Environment**: Real services via Docker Compose
- **API Testing**: Full v1 API endpoint validation
- **Tests**: 21+ integration tests
- **Authentication**: API key validation
- **Database**: Real PostgreSQL with migrations

#### 4. Security Scan ✅
- **Tool**: Trivy vulnerability scanner
- **Scope**: Filesystem scan of entire codebase
- **Severity**: CRITICAL and HIGH vulnerabilities
- **Format**: SARIF output for GitHub Security tab
- **Exit**: Non-blocking (exit-code: '0')

#### 5. Build Docker Image ✅
- **Platform**: `linux/amd64`
- **Mode**: Test build only (no push)
- **Cache**: GitHub Actions cache for efficiency
- **Validation**: Ensures Dockerfile builds successfully
- **Tag**: `medical-patients:test`

## Dockerfile Requirements

### Multi-Stage Build Structure
```dockerfile
# Builder stage - compile dependencies
FROM python:3.11-bookworm as builder
WORKDIR /app
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /app/wheels -r requirements.txt

# Runtime stage - minimal production image
FROM python:3.11-bookworm
RUN groupadd -r patientgen && useradd -r -g patientgen patientgen
WORKDIR /app
COPY --from=builder /app/wheels /wheels
RUN pip install --no-cache-dir --no-index --find-links=/wheels/ /wheels/* \
    && rm -rf /wheels
```

### Required Files in Container
- `patient_generator/` - Core generation logic
- `src/` - FastAPI application and v1 API
- `static/` - Frontend assets
- `config.py` - Application configuration
- `setup.py` - Package setup
- `run_generator.py` - CLI entry point

### Security Best Practices
- Non-root user (`patientgen`)
- Minimal base image
- No cache directories in final image
- Proper file permissions
- Isolated working directory

## Common CI Failure Patterns & Solutions

### 1. Docker Build Failures
**Symptoms**:
- Missing dependencies in requirements.txt
- File not found errors during COPY
- Permission denied errors

**Solutions**:
```bash
# Test locally first
docker build -t test .

# Check missing files
ls -la src/ patient_generator/ static/

# Verify requirements.txt includes all dependencies
pip freeze > requirements-check.txt
diff requirements.txt requirements-check.txt
```

### 2. Registry Authentication Issues
**Historical Problem**: Docker Hub login failures
**Current Solution**: Test-only builds (no push)
**Future Setup**: If registry push needed:
```yaml
# Add to repository secrets:
# DOCKER_USERNAME: your_dockerhub_username  
# DOCKER_TOKEN: your_dockerhub_token

# Then update CI to:
- name: Log in to Docker Hub
  if: github.event_name != 'pull_request'
  uses: docker/login-action@v3
  with:
    username: ${{ secrets.DOCKER_USERNAME }}
    password: ${{ secrets.DOCKER_TOKEN }}
```

### 3. Platform Compatibility
**Issue**: ARM64 builds slow on GitHub Actions
**Solution**: Use `linux/amd64` only for CI
**Production**: Can use multi-platform if needed

## Testing Strategy for Docker Changes

### Before Submitting PR
1. **Local Build Test**:
   ```bash
   docker build -t medical-patients-test .
   docker run --rm medical-patients-test python -c "import src.main; print('Import successful')"
   ```

2. **Dependency Verification**:
   ```bash
   # Check all Python imports work
   docker run --rm medical-patients-test python -c "
   import patient_generator
   import src.main
   import src.api.v1.routers.generation
   print('All imports successful')
   "
   ```

3. **Size Optimization Check**:
   ```bash
   docker images medical-patients-test
   # Image should be reasonable size (< 1GB typically)
   ```

### During PR Review
- Verify CI passes all 5 jobs
- Check Docker build logs for warnings
- Confirm no security vulnerabilities introduced
- Validate no unnecessary files included

## CI Configuration Files

### Main CI Workflow
**File**: `.github/workflows/ci.yml`
**Key Sections**:
- `lint`: Code quality and formatting
- `test`: Unit tests with coverage
- `test-integration`: Full API integration tests  
- `security`: Vulnerability scanning
- `build`: Docker image validation

### Dependencies
**File**: `requirements.txt`
**Categories**:
- FastAPI and web framework dependencies
- Database and ORM (SQLAlchemy, Alembic)
- Testing frameworks (pytest, coverage)
- Development tools (ruff, mypy)

## Future Enhancements

### Potential Improvements
1. **Multi-Stage Optimization**: Smaller final image
2. **Health Checks**: Built-in container health validation
3. **Registry Push**: For deployment automation
4. **Security Scanning**: Container image vulnerability checks
5. **Performance Testing**: Load testing in containers

### Monitoring
- Build time trends (currently ~1m20s)
- Image size optimization
- Cache hit rates
- Dependency update automation

## Troubleshooting Guide

### Build Failures
1. Check local build first: `docker build .`
2. Verify all required files exist
3. Check requirements.txt completeness
4. Review Dockerfile COPY commands

### CI Failures  
1. Check previous successful builds
2. Review dependency changes
3. Verify no missing test files
4. Check for syntax errors in workflow

### Security Issues
1. Review Trivy scan results
2. Update vulnerable dependencies
3. Check for secrets in code
4. Validate user permissions

---

**Last Updated**: Docker CI pipeline fully functional with all 5 jobs passing
**Current Status**: Production-ready with test-only Docker builds
**Next Steps**: Consider registry push automation for deployment workflows