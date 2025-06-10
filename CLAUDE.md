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
4. Ask: "What are we working on today?"

### During Session
1. Document all significant decisions in appropriate memory files
2. Update progress in `memory/current-session.md`
3. When stuck, write questions in `memory/questions/`
4. Apply "Fix Don't Skip" policy - solve and document all issues

### End of Session
1. Update `memory/current-session.md` with:
   - What was accomplished
   - Current state
   - Next steps
   - Any blockers or questions
2. Commit all memory updates

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

## 🎯 Current Implementation Status

### Backend (Priority 1) - COMPLETED
- ✅ FastAPI application structure
- ✅ Async patient generation service
- ✅ Job management system
- ✅ Configuration management
- ✅ Redis caching (optional)
- ✅ API key authentication
- ✅ OpenAPI documentation
- ✅ **NEW**: API v1 standardization with consistent response models
- ✅ **NEW**: Enhanced input validation with comprehensive error handling
- ✅ **NEW**: Standardized error responses across all endpoints
- ✅ **NEW**: Comprehensive test coverage for API contracts

### Frontend (Priority 2)
- ❌ API promotion banner
- ❌ Vertical accordion JSON editors
- ❌ Load previous configurations
- ❌ Nationality code validation  
- ❌ Fun progress messages (2+ seconds)
- ❌ Error retry with reporting
- ❌ Download functionality
- ✅ Basic static HTML interface

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

## 🚦 Progress Tracking

### Backend Analysis & Optimization - COMPLETED
- ✅ Complete backend evaluation
- ✅ Document optimization opportunities  
- ✅ Implement API standardization optimizations
- ✅ Update test coverage with comprehensive API contract tests
- ✅ Create standardized request/response models
- ✅ Enhance input validation and error handling

### Frontend Development
- [ ] Design UI mockup
- [ ] Implement JSON editor component
- [ ] Add generation controls
- [ ] Implement progress tracking
- [ ] Add download functionality
- [ ] Write unit tests
- [ ] Write E2E tests

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

## ⚠️ Important Reminders
1. **Keep it simple** - This is a specialist tool, not a SaaS
2. **No over-engineering** - Avoid unnecessary complexity
3. **Focus on functionality** - UI should be clean and functional
4. **Document everything** - Future Claude sessions need context
5. **Test everything** - TDD is mandatory

---

*Last Updated: Backend API Standardization Complete - Services Deployed Successfully*
*Current Focus: Frontend development with new v1 API contracts*

## 📋 API Standardization Summary

### What Was Accomplished
- **Consistent Versioning**: All API endpoints now use `/api/v1/` prefix
- **Response Models**: Created comprehensive Pydantic models for all endpoints
- **Request Validation**: Enhanced input validation with cross-field validation
- **Error Handling**: Standardized error responses with proper HTTP status codes
- **Documentation**: Rich OpenAPI documentation with examples and descriptions
- **Test Coverage**: Comprehensive failing tests to drive implementation

### Files Created/Modified
```
src/api/v1/models/
├── __init__.py           # Model exports
├── requests.py           # Enhanced request models with validation  
└── responses.py          # Standardized response models

src/api/v1/routers/
├── generation.py         # New versioned generation endpoint
├── jobs.py              # Updated with JobResponse models
├── downloads.py         # Enhanced download functionality
└── visualizations.py    # Standardized visualization responses

tests/
└── test_api_standardization.py  # Comprehensive API contract tests

memory/implementations/
└── api-standardization-implementation.md

memory/patterns/
└── api-first-development-patterns.md
```

### Completed Successfully ✅
1. ✅ Updated main FastAPI application to include v1 routers
2. ✅ Ran test suite and verified implementation working
3. ✅ Services deployed and API endpoints tested
4. ✅ All changes committed (commit d508721)

### Next Steps (Next Session)
1. Update frontend to use new v1 API endpoints
2. Implement frontend TDD development as planned
3. Add API banner component and JSON editors
4. Begin frontend development with new API contracts
