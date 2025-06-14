# Medical Patients Generator - Claude Code Development Guide

## 🧠 External Memory System
This document serves as Claude Code's persistent memory across sessions. Read this first in every session.

## 🎯 Project Overview
**Project**: Medical Patients Generator
**Type**: Low-use specialist tool for military medical exercises
**Purpose**: Generate simulated patient data with configurable parameters
**Stack**: FastAPI backend, Vanilla JS frontend
**Architecture**: Clean architecture with domain/infrastructure/api separation
**Database**: PostgreSQL
**Deployment**: Traditional VPS and local use

## 📋 Session Protocol

### Start of Session
1. Read this CLAUDE.md file completely
2. Check `memory/current-session.md` for handoff notes
3. Review relevant memory files based on current task
4. **🚨 MANDATORY: Check current git branch and status**
5. **🚨 MANDATORY: Verify git workflow compliance before ANY code changes**
6. Ask: "What are we working on today?"

### During Session
1. **🚨 MANDATORY: Follow git workflow for ALL code changes (no exceptions)**
2. **🔄 MANDATORY TASK TRANSITION PROTOCOL:**
   - **Before starting ANY new task**: Update memory files and todo list
   - **After completing ANY task**: Update progress documentation
   - **Between task phases**: Commit work and update session status
3. Document all significant decisions in appropriate memory files
4. Update progress in `memory/current-session.md`
5. When stuck, write questions in `memory/questions/`
6. Apply "Fix Don't Skip" policy - solve and document all issues
7. **🚨 MANDATORY: Never push directly to main branch**

### End of Session
1. Update `memory/current-session.md` with:
   - What was accomplished
   - Current state
   - Next steps
   - Any blockers or questions
2. **🚨 MANDATORY: Commit all memory updates following git workflow**
3. **🚨 MANDATORY: Document current branch status for next session**

## 🏗️ Project Structure

### Backend Structure
```
src/
├── main.py              # FastAPI application entry
├── api/                 # API layer
│   └── v1/
│       ├── routers/     # API endpoints
│       ├── dependencies/# Dependency injection
│       └── middleware/  # API middleware
├── domain/              # Business logic
│   ├── models/         # Domain models
│   ├── services/       # Business services
│   └── repositories/   # Repository interfaces
├── infrastructure/      # External interfaces
│   └── repositories/   # Repository implementations
└── core/               # Shared utilities
    ├── cache.py        # Redis caching
    ├── exceptions.py   # Custom exceptions
    └── security.py     # API key validation
```

### Configuration Files
```
patient_generator/
├── demographics.json    # NATO nations data, names, IDs
├── fronts_config.json  # Battle fronts, casualty ratios
└── injuries.json       # Injury distributions
```

### Key API Endpoints (v1 Standardized)
- `POST /api/v1/generation/` - Generate patients (enhanced validation)
- `GET /api/v1/jobs/{job_id}` - Get job status (standardized response)
- `GET /api/v1/jobs/` - List all jobs
- `GET /api/v1/downloads/{job_id}` - Download job results
- `GET /api/v1/visualizations/dashboard-data` - Get dashboard data
- `GET /api/v1/configurations/` - List configurations
- `POST /api/v1/configurations/` - Create configuration
- `GET /docs` - OpenAPI documentation with enhanced schemas

## 🧪 Development Principles

### API First Approach
1. Define API contracts before implementation
2. Use OpenAPI/Swagger documentation
3. Test API endpoints independently
4. Frontend consumes only documented APIs

### TDD Workflow
1. Write test first (failing)
2. Implement minimal code to pass
3. Refactor with confidence
4. Document test purpose
5. Maintain high coverage

### Code Standards
- Type hints for all functions
- Docstrings for modules, classes, methods
- Async/await for I/O operations
- Dependency injection pattern
- Repository pattern for data access
- No complex abstractions - keep it simple

## 🎯 Current Implementation Status & Roadmap

### Backend Core - COMPLETED ✅
- ✅ FastAPI application structure with clean architecture
- ✅ Async patient generation service
- ✅ Job management system with database tracking
- ✅ Configuration management and validation
- ✅ Redis caching (optional)
- ✅ API key authentication (single key)
- ✅ OpenAPI documentation with enhanced schemas
- ✅ API v1 standardization with consistent response models
- ✅ Enhanced input validation with comprehensive error handling
- ✅ Standardized error responses across all endpoints
- ✅ Comprehensive test coverage for API contracts

### Infrastructure Modernization - IN PROGRESS 🚧
- ✅ **Cross-Platform Development Environment** (Priority 1) - **COMPLETED**
- 🏗️ **Multi-Tenant API Key Management** (Priority 1) 
- 🏗️ **Production Scalability Improvements** (Priority 1)
- 🏗️ **DigitalOcean Staging Environment** (Priority 2)
- 🏗️ **Timeline Viewer Standalone Deployment** (Priority 3)

### Frontend Enhancements - PLANNED 📋
- ❌ API promotion banner with live demo key
- ❌ Vertical accordion JSON editors
- ❌ Load previous configurations from database
- ❌ Nationality code validation and assistance
- ❌ Progress tracking with engaging messages
- ❌ Error handling with retry mechanisms
- ❌ File download functionality
- ✅ Basic static HTML interface with Med Atlantis branding

## 🔧 Key Technical Decisions

### Backend Optimizations COMPLETED
1. ✅ **API Standardization** - All endpoints use consistent v1 versioning
2. ✅ **Response Models** - Standardized Pydantic models for all responses
3. ✅ **Error Handling** - Consistent exception patterns with proper HTTP status codes
4. ✅ **Input Validation** - Comprehensive validation with descriptive error messages
5. ✅ **API Documentation** - Enhanced OpenAPI specs with examples and descriptions

### Frontend Architecture
- **Framework**: Vanilla JS (no framework complexity)
- **Target**: 1080p military laptops
- **Features**: 
  - Single page application
  - API promotion banner (always visible)
  - Vertical accordion layout (one editor visible at a time)
  - JSON editors with nationality validation
  - Load previous configurations from DB
  - Fun progress messages (minimum 2 seconds)
  - Developer-friendly error reporting
  - Download generated files
- **No bells and whistles** - Focus on functionality

## 📝 Memory Map

### `/memory/architecture/`
Design decisions, system architecture, API contracts

### `/memory/implementations/`
Completed features, code patterns, implementation notes

### `/memory/fixes/`
Solved problems, debugging notes, workarounds

### `/memory/patterns/`
Reusable code patterns, testing strategies, common solutions

### `/memory/questions/`
Unresolved questions, clarifications needed, design considerations

### `/memory/context/`
Current task context, work in progress, temporary notes

## 📋 Epic Implementation Roadmap

### Phase 1: Foundation & Stability (Weeks 1-3)
**Epic Links**: 
- [`memory/epics/cross-platform-dev-environment.md`](memory/epics/cross-platform-dev-environment.md)
- [`memory/epics/api-key-management-system.md`](memory/epics/api-key-management-system.md)
- [`memory/epics/production-scalability-improvements.md`](memory/epics/production-scalability-improvements.md)

### Phase 2: Infrastructure Expansion (Weeks 4-6)
**Epic Links**:
- [`memory/epics/digitalocean-staging-environment.md`](memory/epics/digitalocean-staging-environment.md)
- [`memory/epics/timeline-viewer-standalone.md`](memory/epics/timeline-viewer-standalone.md)

### Phase 3: Frontend Enhancement (Weeks 7-9)
**Epic Links**:
- [`memory/epics/frontend-modernization.md`](memory/epics/frontend-modernization.md)

## 📊 Progress Tracking

### Completed This Session ✅
- ✅ Production rollback executed successfully
- ✅ UI modernization with Med Atlantis branding
- ✅ Technical debt analysis documented
- ✅ Cross-platform dev environment plan created
- ✅ API key management system specification completed

### Current Focus 🎯
- 🎉 **EPIC-001 Phase 1-2 COMPLETED**: Cross-platform development environment
- 🚧 **EPIC-001 Phase 3 READY**: Platform optimization and documentation
- 🏗️ React timeline viewer cleanup
- 🏗️ Remaining epic documentation (5 epics)

## 🔐 Security Notes
- API key authentication required
- No personal data generated
- No compliance requirements (HIPAA/GDPR)
- Local/VPS deployment only

## 🎓 Quick Commands

### Development
```bash
# Start development server
python -m uvicorn src.main:app --reload

# Run tests
pytest

# Check code quality
ruff check .
ruff format .

# Generate test data
python demo.py
```

### Frontend Build
```bash
# Build frontend (when implemented)
# No build step needed for vanilla JS
```

## ⚠️ CRITICAL DEVELOPMENT RULES (NON-NEGOTIABLE)

### 🚨 PRODUCTION SAFETY (ABSOLUTE REQUIREMENTS)
1. **🚫 NEVER PUSH TO MAIN** - main branch auto-deploys to live production (https://milmed.tech)
2. **🚫 NO DIRECT MAIN COMMITS** - All changes must go through git workflow
3. **🚫 NO BYPASSING WORKFLOW** - Epic → Develop → Main progression is mandatory
4. **🚫 NO UNTESTED DEPLOYMENTS** - Wait for GitHub CI to pass before any deployment testing

### 🔄 MANDATORY GIT WORKFLOW COMPLIANCE
1. **Branch Check**: Always verify current branch before making changes
2. **Epic Isolation**: Work in epic/feature branches only
3. **Gradual Integration**: Follow Feature → Epic → Develop → Main
4. **Protection Rules**: Respect branch protection (2+ reviews for main)
5. **Emergency Only**: Hotfix directly to main only for critical production issues

### 📋 DEVELOPMENT STANDARDS
1. **Keep it simple** - This is a specialist tool, not a SaaS
2. **No over-engineering** - Avoid unnecessary complexity
3. **Focus on functionality** - UI should be clean and functional
4. **Document everything** - Future Claude sessions need context
5. **Test everything** - TDD is mandatory
6. **🚨 NEVER DECLARE VICTORY WITHOUT TESTING** - Always verify with actual tests before claiming something works

### ⚡ PRE-CHANGE CHECKLIST (MANDATORY)
Before ANY code changes, verify:
- [ ] Current branch identified (`git branch` or `git status`)
- [ ] Working in correct epic/feature branch (NOT main)
- [ ] Git workflow documented and understood
- [ ] Epic context clear and documented
- [ ] Changes align with epic scope and goals

## 🚨 MANDATORY Workflow Enforcement

### SESSION START REQUIREMENTS (NON-NEGOTIABLE)
Before ANY development work, MUST verify:
1. **🔍 Git Status Check**: `git status` and `git branch`
2. **🚫 Main Branch Check**: If on main, immediately switch to epic branch
3. **📋 Epic Context**: Verify current epic and task from memory files
4. **🔄 Workflow Compliance**: Confirm understanding of git workflow rules

### DEVELOPMENT PROTOCOLS (ENFORCED)
- **🏗️ EPIC ISOLATION**: All development in epic/feature branches only
- **🔄 PROGRESSION RULES**: Feature → Epic → Develop → Main (no exceptions)
- **🛡️ PROTECTION RESPECT**: Never bypass branch protection rules
- **📚 DOCUMENTATION**: Update memory files with every significant change

### MIGRATION STATUS
- **ACTIVE**: Transitioning from Makefile to Task runner for cross-platform support
- **PARALLEL**: Makefile remains during transition period
- **TESTING**: Do not test DigitalOcean deployments before GitHub CI passes
- **HANDOFFS**: Always check `memory/current-session.md` and relevant epic files

### 🚨 EMERGENCY PROTOCOLS
- **Production Issues**: Use hotfix branches only
- **Workflow Violations**: Immediate branch correction required
- **CI Failures**: No deployment testing until resolved

## 🗂️ Epic Documentation Structure
```
memory/epics/
├── cross-platform-dev-environment.md       # Priority 1: Task runner migration
├── api-key-management-system.md            # Priority 1: Multi-tenant auth
├── production-scalability-improvements.md  # Priority 1: Database & monitoring
├── digitalocean-staging-environment.md     # Priority 2: Staging infrastructure
├── timeline-viewer-standalone.md           # Priority 3: Separate VM deployment
└── frontend-modernization.md               # Priority 3: UI enhancements

memory/patterns/
└── git-workflow-epic-implementation.md     # Production-safe git workflow
```

## 🔄 MANDATORY Git Workflow for Production Safety

**🚨 CRITICAL**: `main` branch auto-deploys to production (https://milmed.tech)

### REQUIRED Branch Strategy
```
main (PRODUCTION - AUTO-DEPLOY) 🚨 ← NEVER PUSH DIRECTLY
├── develop (INTEGRATION TESTING) ← Safe for epic integration
│   ├── epic/cross-platform-dev-env (EPIC-001) ← Work here
│   ├── epic/api-key-management (EPIC-002) ← Work here
│   └── epic/production-scalability (EPIC-003) ← Work here
└── hotfix/* (EMERGENCY ONLY) ← Critical fixes only
```

### ENFORCED Safety Protocols
1. **🚫 NO MAIN BRANCH WORK** - Epic isolation is mandatory
2. **🔄 REQUIRED PROGRESSION** - Feature → Epic → Develop → Main (no shortcuts)
3. **🛡️ PROTECTION ENFORCED** - Main requires 2+ reviews + all CI tests
4. **🔙 ROLLBACK READY** - DigitalOcean deployment rollback available
5. **🚨 EMERGENCY PATH** - Hotfix to main only for critical production issues

### WORKFLOW VALIDATION COMMANDS
```bash
# ALWAYS run before ANY changes
git status                    # Verify current branch
git branch                    # Confirm not on main
git log --oneline -5          # Check recent commits

# REQUIRED branch check
if [ "$(git branch --show-current)" = "main" ]; then
  echo "🚨 ERROR: Cannot work on main branch!"
  echo "Switch to epic branch immediately"
  exit 1
fi
```

### BRANCH TRANSITION PROTOCOL
```bash
# CORRECT: Epic branch creation
git checkout main
git pull origin main
git checkout -b epic/your-epic-name

# CORRECT: Feature branch creation  
git checkout epic/your-epic-name
git checkout -b feature/your-epic-name/task-name

# WRONG: Direct main branch work
git checkout main  # 🚨 FORBIDDEN for development
```

**📚 Complete Workflow Documentation**: [`memory/patterns/git-workflow-epic-implementation.md`](memory/patterns/git-workflow-epic-implementation.md)

### 🚨 VIOLATION CONSEQUENCES
- **Main branch violations**: Immediate revert + process review
- **Workflow bypassing**: Epic restart from correct branch
- **Production incidents**: Emergency protocols + post-mortem required

---

## 🚨 FINAL WORKFLOW ENFORCEMENT NOTICE

**THIS DOCUMENT ESTABLISHES MANDATORY PROTOCOLS**

Every future Claude Code session MUST:
1. ✅ Read this CLAUDE.md file completely
2. ✅ Verify git branch status before ANY changes
3. ✅ Follow epic workflow for ALL development
4. ✅ Never push directly to main branch
5. ✅ Document all work in memory files

**NON-COMPLIANCE WILL RESULT IN:**
- Immediate workflow correction
- Epic restart from proper branch
- Production safety protocol activation

**🔒 PRODUCTION SAFETY IS NON-NEGOTIABLE**

The `main` branch is directly connected to live production at https://milmed.tech. Any violation of this workflow could impact real users and must be prevented at all costs.

---

*Last Updated: Infrastructure Modernization + Mandatory Workflow Enforcement*
*Current Status: Production-safe development protocols established*
*Next Session: MANDATORY git status check + epic workflow compliance verification*