# Cross-Platform Development Environment Refactoring Plan

## Executive Summary

Comprehensive plan to refactor the medical-patients application's setup/startup/management scripts using Task as the primary build tool, creating a unified solution that works seamlessly across Linux, macOS, and Windows while maintaining Docker as core infrastructure.

## 🎯 Objectives
- Eliminate platform-specific issues
- Reduce setup time from 30+ minutes to under 5 minutes
- Maintain backward compatibility during transition
- Create unified developer experience across all platforms

## 📋 Current Development Environment Analysis

### Files Marked for Removal (Post-Migration)
```
🔴 TO BE REMOVED AFTER NEW SYSTEM WORKS:
├── Makefile                    # Current build system - 358 lines, comprehensive
├── start-dev.sh               # Linux/macOS dev startup script
├── start.sh                   # Production startup script
├── start-prod.sh              # Production startup script
├── start-prod 2.sh            # Production startup variant (duplicate?)
├── setup-dev.sh               # Development setup script
├── setup-ubuntu.sh            # Ubuntu-specific setup
├── run_tests.sh               # Test runner script
└── scripts/
    ├── generate-api-key.sh    # API key generation
    └── version.sh             # Version management
```

### Current Makefile Analysis (358 lines)
**Key Commands Currently Available:**
- `make dev` → `start-dev.sh` (core development)
- `make dev-with-data` → `start-dev.sh --test-data`
- `make dev-clean` → `start-dev.sh --clean`
- `make test` → `run_tests.sh all`
- `make lint` → `ruff check` + `mypy` + `npm run lint`
- `make format` → `ruff format` + `npm run format`
- `make build-frontend` → `npm run build:all-frontend`
- `make deps` → `pip install` + `npm install`
- `make migrate` → `alembic upgrade head`
- `make services` → `docker compose up -d db redis`
- Timeline viewer commands (already removed directory)

**Complex Features to Replicate:**
- Docker compose integration
- Redis cache management
- Database operations
- Frontend build pipeline
- Multi-stage testing
- Production build workflow

### Current System Dependencies
- **Make**: Primary build automation (not available on Windows)
- **Bash scripts**: Platform-specific (problematic on Windows)
- **Docker Compose**: Core infrastructure (cross-platform)
- **Manual setup**: Multiple steps, platform-specific issues

## 🏗️ Phase 1: Foundation Setup (Week 1)

### 1.1 Line Ending Consistency - CRITICAL
Create `.gitattributes` to prevent Windows CRLF issues:

```gitattributes
# Line ending normalization
* text=auto

# Shell scripts must use LF
*.sh text eol=lf
*.bash text eol=lf

# Python files
*.py text eol=lf

# Docker files
Dockerfile text eol=lf
Dockerfile.* text eol=lf
docker-compose*.yml text eol=lf
docker-compose*.yaml text eol=lf

# Configuration files
*.json text eol=lf
*.yml text eol=lf
*.yaml text eol=lf
*.toml text eol=lf
*.ini text eol=lf
.env* text eol=lf

# Documentation
*.md text eol=lf
*.txt text eol=lf

# Web files
*.js text eol=lf
*.jsx text eol=lf
*.ts text eol=lf
*.tsx text eol=lf
*.html text eol=lf
*.css text eol=lf

# Binary files
*.png binary
*.jpg binary
*.jpeg binary
*.gif binary
*.ico binary
*.zip binary
*.pdf binary
```

### 1.2 Task Runner Installation
**Tool**: Task (https://taskfile.dev) - Go-based, cross-platform build tool

Installation methods:
- **Linux/macOS**: `curl -sL https://taskfile.dev/install.sh | sh`
- **Windows**: `irm https://taskfile.dev/install.ps1 | iex`
- **Homebrew**: `brew install go-task`
- **Scoop**: `scoop install task`
- **Chocolatey**: `choco install go-task`

### 1.3 Base Taskfile Structure
Root `Taskfile.yml` with modular design:

```yaml
version: '3'

env:
  COMPOSE_PROJECT_NAME: medical-patients
  DOCKER_BUILDKIT: 1
  
includes:
  docker: ./tasks/docker.yml
  dev: ./tasks/development.yml
  test: ./tasks/testing.yml
  db: ./tasks/database.yml
  frontend: ./tasks/frontend.yml

tasks:
  default:
    desc: Show available tasks
    cmds:
      - task --list

  setup:
    desc: Complete initial setup for development
    deps: [check-requirements]
    cmds:
      - task: setup:{{OS}}
      - task: docker:pull
      - task: frontend:install
```

## 🔧 Phase 2: Task Migration (Week 2)

### 2.1 Task Module Structure
```
tasks/
├── docker.yml       # Docker operations
├── development.yml  # Dev environment management
├── testing.yml      # Test execution
├── database.yml     # Database operations
├── frontend.yml     # Frontend build tasks
└── production.yml   # Production deployment
```

### 2.2 Migration Mapping
| Current Command | New Task Command | Description |
|----------------|------------------|-------------|
| `make dev` | `task dev` | Start development environment |
| `make test` | `task test:all` | Run all tests |
| `make clean` | `task clean` | Clean generated files |
| `make build-frontend` | `task frontend:build` | Build frontend |
| `make deps` | `task setup` | Install dependencies |
| `make migrate` | `task db:migrate` | Run migrations |
| `./start-dev.sh` | `task dev:start` | Start with options |
| `./run_tests.sh` | `task test:suite` | Run test suites |

### 2.3 Platform-Specific Implementation

#### Windows PowerShell Script (`scripts/setup-windows.ps1`)
- Docker Desktop validation
- Directory creation with proper permissions
- Environment file setup
- Windows-specific path handling

#### macOS Script (`scripts/setup-macos.sh`)
- Homebrew package checks
- Docker Desktop for Mac validation
- File system performance optimizations

#### Linux Script (`scripts/setup-linux.sh`)
- Native Docker Engine support
- User group management
- Permission setup

## 🐳 Phase 3: Docker Optimization (Week 3)

### 3.1 Cross-Platform Dockerfile
Key improvements:
- Multi-stage builds for efficiency
- Configurable USER_ID/GROUP_ID for permissions
- Platform-specific build arguments
- Health check implementation

### 3.2 Docker Compose Enhancements
- Volume mounting with performance flags
- Named volumes for dependencies
- Platform-specific environment variables
- Service health checks

### 3.3 Windows-Specific Optimizations
- Use named volumes for node_modules (performance)
- Delegated mounts for source code
- WSL2 vs native Docker considerations

## 📚 Phase 4: Documentation (Week 4)

### 4.1 Platform-Specific README Sections
- Prerequisites for each platform
- Quick start guide
- Common issues and solutions
- Performance tips

### 4.2 VS Code Dev Container
Complete `.devcontainer/devcontainer.json` with:
- Extension recommendations
- Settings synchronization
- Task runner integration
- Platform-agnostic configuration

## 🧪 Phase 5: Testing and CI/CD (Week 5)

### 5.1 Cross-Platform CI Matrix
GitHub Actions workflow testing on:
- ubuntu-latest
- windows-latest
- macos-latest

### 5.2 Test Execution Strategy
- Platform-specific test configurations
- Artifact collection on failure
- Performance benchmarking across platforms

## 🚀 Phase 6: Migration and Rollout

### 6.1 Backward Compatibility
- Temporary `make` → `task` aliases
- Parallel systems during transition
- Command mapping documentation

### 6.2 Rollout Timeline
1. **Week 1**: Foundation (gitattributes, Task setup)
2. **Week 2**: Task modules, maintain Make compatibility
3. **Week 3**: Docker cross-platform updates
4. **Week 4**: Documentation and devcontainer
5. **Week 5**: CI/CD implementation
6. **Week 6**: Team training, full migration

### 6.3 Success Metrics
- ✅ All platforms: `task setup` completes in <5 minutes
- ✅ CI/CD passes on Linux, macOS, Windows
- ✅ Zero platform-specific bugs in first month
- ✅ Developer satisfaction improvement

## ⚠️ Critical Considerations

### Line Endings
- **CRITICAL**: `.gitattributes` must be committed first
- Developers must re-clone after gitattributes addition
- Use `git config core.autocrlf false` on Windows

### Docker Desktop Requirements
- **Windows**: WSL2 backend recommended
- **macOS**: VirtioFS for performance
- **Linux**: Native Docker Engine preferred

### File System Performance
- **Windows**: Use named volumes for dependencies
- **macOS**: Delegated mounts for source code
- **All**: Avoid mounting large directories

## 📋 Implementation Checklist

### Immediate Actions
- [ ] Create and commit `.gitattributes`
- [ ] Create base `Taskfile.yml`
- [ ] Create `tasks/` directory structure
- [ ] Install Task on development machines

### Migration Phase
- [ ] Implement task modules
- [ ] Create platform setup scripts
- [ ] Update Dockerfile for cross-platform
- [ ] Update docker-compose configurations
- [ ] Create VS Code devcontainer

### Documentation & Training
- [ ] Update README with platform guides
- [ ] Create migration documentation
- [ ] Record setup video tutorials
- [ ] Conduct team training sessions

### Cleanup Phase (After Verification)
- [ ] Remove Makefile
- [ ] Remove bash scripts
- [ ] Archive old documentation
- [ ] Update CI/CD pipelines

## 🔍 Maintenance Plan

### Monthly Reviews
- Task command optimization
- Platform-specific issue tracking
- Performance metrics analysis

### Quarterly Updates
- Docker base image updates
- Dependency updates
- Security patches

### Automation
- Dependabot for dependencies
- Automated testing on all platforms
- Performance regression detection

---

*Priority: HIGHEST - Blocks all development efficiency*
*Complexity: Medium - Well-defined migration path*
*Risk: Low - Gradual migration with backward compatibility*
*Timeline: 6 weeks with parallel systems during transition*