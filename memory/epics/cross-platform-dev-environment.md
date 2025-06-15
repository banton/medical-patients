# Epic: Cross-Platform Development Environment

**Priority**: 1 (Critical)  
**Epic ID**: EPIC-001  
**Estimated Effort**: 3 weeks  
**Dependencies**: None (foundational)

## 🎯 Epic Overview

Replace the current Make-based development environment with a cross-platform solution using Task runner, enabling seamless development on Linux, macOS, and Windows.

## 📋 Business Value

- **Developer Productivity**: Reduce setup time from 30+ minutes to <5 minutes
- **Platform Inclusivity**: Enable Windows developers to contribute effectively  
- **Maintenance Reduction**: Eliminate platform-specific bug reports
- **Scalability**: Foundation for all future infrastructure improvements

## 🎯 Success Criteria

1. ✅ All platforms can run `task setup && task dev` successfully
2. ✅ CI/CD passes on Linux, macOS, Windows
3. ✅ Zero platform-specific issues in first month post-migration
4. ✅ Developer satisfaction improvement (survey)
5. ✅ Setup time <5 minutes on any platform

## 📊 Current State Analysis

### Files to be Replaced/Retired
```
🔴 LEGACY SYSTEM (358 lines Makefile + 7 shell scripts):
├── Makefile                    # 358 lines, comprehensive build system
├── start-dev.sh               # Linux/macOS dev startup
├── start.sh                   # Production startup  
├── start-prod.sh              # Production startup variant
├── setup-dev.sh               # Development setup
├── setup-ubuntu.sh            # Ubuntu-specific setup
├── run_tests.sh               # Test runner
└── scripts/
    ├── generate-api-key.sh    # API key generation
    └── version.sh             # Version management
```

### ✅ Phase 1 COMPLETED (Foundation)
```
🟢 NEW CROSS-PLATFORM SYSTEM:
├── .gitattributes             # ✅ Line ending consistency
├── Taskfile.yml               # ✅ Base task runner configuration
├── scripts/install-task.sh    # ✅ Cross-platform Task installer
└── tasks/
    ├── docker.yml             # ✅ Docker operations module
    └── development.yml         # ✅ Development environment module
```

### ✅ Phase 2 COMPLETED (Core Migration)
```
🟢 COMPLETE TASK SYSTEM (6 Modules):
├── tasks/docker.yml          # ✅ Docker operations (20+ commands)
├── tasks/development.yml     # ✅ Dev environment (15+ commands) 
├── tasks/testing.yml         # ✅ Test execution (25+ commands)
├── tasks/database.yml        # ✅ DB/Redis operations (30+ commands)
├── tasks/frontend.yml        # ✅ Build pipeline (35+ commands)
└── tasks/linting.yml         # ✅ Code quality (25+ commands)
```

**Status**: **CORE MIGRATION COMPLETE** - 358-line Makefile → 144 Task commands

### Key Commands to Migrate
| Current | New Task | Description |
|---------|----------|-------------|
| `make dev` | `task dev` | Start development environment |
| `make test` | `task test:all` | Run all test suites |
| `make clean` | `task clean` | Clean generated files |
| `make deps` | `task setup` | Install dependencies |
| `make migrate` | `task db:migrate` | Database migrations |
| `make build-frontend` | `task frontend:build` | Build frontend assets |

## 🏗️ Implementation Plan

### Phase 1: Foundation (Week 1)

#### Task 1.1: Line Ending Configuration
**Deliverable**: Cross-platform `.gitattributes`
**Success Criteria**: 
- No CRLF issues on Windows
- Consistent line endings in all text files
- All developers re-clone repository

**Implementation**:
```gitattributes
* text=auto
*.sh text eol=lf
*.py text eol=lf
Dockerfile* text eol=lf
docker-compose*.yml text eol=lf
*.json text eol=lf
*.md text eol=lf
*.js text eol=lf
*.css text eol=lf
```

#### Task 1.2: Task Runner Installation
**Deliverable**: Task installation across all platforms
**Success Criteria**:
- Task installed on all developer machines
- Installation documentation complete
- Platform-specific installation methods documented

**Implementation**:
- Create `scripts/install-task.sh` for automated installation
- Document manual installation methods
- Verify installation on each platform

#### Task 1.3: Base Taskfile Structure  
**Deliverable**: Root `Taskfile.yml` with modular includes
**Success Criteria**:
- `task --list` shows all available commands
- Modular structure with includes working
- Platform detection working (`{{OS}}` variable)

### Phase 2: Core Migration (Week 2)

#### Task 2.1: Docker Task Module
**Deliverable**: `tasks/docker.yml` with complete Docker operations
**Success Criteria**:
- All Docker operations work via Task
- Service health checks implemented
- Log viewing and container management functional

**Key Commands**:
```yaml
tasks:
  up: Start all services
  down: Stop all services  
  logs: Show service logs
  ps: Show running services
  build: Build Docker images
  exec: Execute commands in containers
```

#### Task 2.2: Development Task Module
**Deliverable**: `tasks/development.yml` with dev environment management
**Success Criteria**:
- `task dev` starts complete environment
- Environment health checks working
- URL display after startup
- Test data generation functional

#### Task 2.3: Testing Task Module
**Deliverable**: `tasks/testing.yml` with comprehensive test execution
**Success Criteria**:
- All test types executable via Task
- CI-compatible test running
- Cross-platform test execution

#### Task 2.4: Database Task Module
**Deliverable**: `tasks/database.yml` with database operations
**Success Criteria**:
- Migration execution working
- Database reset functional
- Connection management working

### Phase 3: Platform Optimization (Week 3)

#### Task 3.1: Platform-Specific Setup Scripts
**Deliverable**: Setup scripts for Windows, macOS, Linux
**Success Criteria**:
- Automated prerequisite checking
- Platform-specific optimizations
- Error handling and user guidance

**Files**:
- `scripts/setup-windows.ps1` - PowerShell setup
- `scripts/setup-macos.sh` - macOS with Homebrew
- `scripts/setup-linux.sh` - Native Docker setup

#### Task 3.2: Docker Cross-Platform Optimization
**Deliverable**: Updated Dockerfile and docker-compose for all platforms
**Success Criteria**:
- Consistent performance across platforms
- Proper file system permissions
- Windows-specific volume optimizations

#### Task 3.3: VS Code Dev Container
**Deliverable**: Complete `.devcontainer/devcontainer.json`
**Success Criteria**:
- One-click development environment
- All extensions and settings configured
- Task runner integration working

### Phase 4: Documentation & Training (Parallel)

#### Task 4.1: Platform-Specific Documentation
**Deliverable**: README sections for each platform
**Success Criteria**:
- Clear setup instructions per platform
- Common issues and solutions documented
- Performance tips included

#### Task 4.2: Migration Documentation
**Deliverable**: Migration guide and command mappings
**Success Criteria**:
- Backward compatibility documented
- Command mapping complete
- Team training materials ready

#### Task 4.3: CI/CD Integration
**Deliverable**: Cross-platform GitHub Actions
**Success Criteria**:
- Tests pass on Linux, macOS, Windows
- Task runner used in CI
- Platform-specific issues caught early

## 🧪 Testing Strategy

### Integration Tests
- [ ] `task setup` completes successfully on all platforms
- [ ] `task dev` starts environment within 5 minutes
- [ ] All core tasks function identically across platforms
- [ ] Database operations work consistently
- [ ] Frontend build process platform-agnostic

### Performance Tests
- [ ] Setup time <5 minutes on each platform
- [ ] Docker performance comparable across platforms
- [ ] File watching works efficiently (especially Windows)

### User Acceptance Tests
- [ ] New developer can setup environment independently
- [ ] Existing developers can transition seamlessly
- [ ] Documentation sufficient for troubleshooting

## 🔄 Migration Strategy

### Parallel Systems Approach
1. **Week 1**: Implement Task alongside existing Makefile
2. **Week 2**: Complete Task implementation, encourage adoption
3. **Week 3**: Deprecate Makefile, make Task primary
4. **Week 4**: Remove Makefile after team confirmation

### Backward Compatibility
- Maintain Makefile during transition
- Create `make` → `task` aliases
- Document migration path clearly
- Provide rollback option if needed

## 🚨 Risk Mitigation

### High Risk: Line Ending Issues
**Mitigation**: 
- Implement `.gitattributes` first
- Require repository re-clone
- Test on Windows early

### Medium Risk: Docker Performance on Windows
**Mitigation**:
- Use named volumes for node_modules
- Implement delegated mounts
- Provide WSL2 setup guidance

### Low Risk: Team Adoption Resistance
**Mitigation**:
- Maintain parallel systems
- Provide clear migration benefits
- Offer hands-on training sessions

## 📈 Success Metrics

### Quantitative
- Setup time: <5 minutes (target) vs 30+ minutes (current)
- Platform issues: 0 reports in first month
- CI success rate: >99% across all platforms
- Developer productivity: Time to first contribution <1 hour

### Qualitative  
- Developer satisfaction survey improvement
- Reduced support requests for environment issues
- Positive feedback on cross-platform consistency

## 🔗 Dependencies & Related Epics

### Blocks
- Epic: API Key Management System (development environment needed)
- Epic: Production Scalability (testing infrastructure needed)

### Enables
- All future development work
- Contributor onboarding
- Infrastructure improvements

## 📝 Definition of Done

- [ ] All tasks migrated from Makefile to Task modules
- [ ] Platform-specific setup scripts functional
- [ ] Documentation complete for all platforms
- [ ] CI/CD updated to use Task runner
- [ ] Team trained on new workflow
- [ ] Old Makefile and scripts archived
- [ ] Success metrics validated
- [ ] Post-implementation review completed

---

**Epic Owner**: Development Team  
**Stakeholders**: All developers, DevOps, new contributors  
**Review Date**: End of Week 3  
**Go/No-Go Criteria**: All success criteria met, no platform-specific issues