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
6. **🚨 NEVER DECLARE VICTORY WITHOUT TESTING** - Always verify with actual tests before claiming something works
7. **🚦 DO NOT TEST DO THINGS BEFORE GH CI HAS PASSED WITH FLYING COLOURS** - Wait for GitHub CI to pass completely before testing deployments or claiming fixes work

## 🚨 Workflow Memory
- Always use Makefile and stop being a hacker :D
- Do not test Digitalocean before GH tests pass

---

*Last Updated: Complete React Timeline Viewer + CI/CD Pipeline Integration*
*Current Status: Production-ready system with interactive visualization*

## 🚀 React Timeline Viewer Implementation - COMPLETE

### What Was Accomplished
- **Complete React Application**: Interactive patient timeline visualization with POI → Role1-4 flow
- **Advanced Features**: Patient names, smart KIA/RTD tallying, fixed headers, viewport indicators
- **Data Compatibility**: Handles real generator output format with flexible validation
- **Professional UI**: React 18 + TypeScript + Tailwind CSS + Framer Motion animations
- **Full Integration**: Makefile commands, comprehensive testing, documentation
- **Robust CI/CD**: GitHub Actions pipeline with React integration across all jobs

### Files Created/Modified
```
patient-timeline-viewer/                     # Complete React application
├── src/
│   ├── components/
│   │   ├── PatientCard.tsx                 # Animated patient display
│   │   ├── FacilityColumn.tsx              # Medical facility container  
│   │   ├── TimelineControls.tsx            # Playback interface
│   │   └── FileUploader.tsx                # File upload with validation
│   ├── types/patient.types.ts              # TypeScript definitions
│   ├── utils/timelineEngine.ts             # Timeline calculation logic
│   ├── App.tsx                             # Main application
│   └── main.tsx                            # Entry point
├── package.json                            # Dependencies and scripts
└── README.md                               # Comprehensive documentation

.github/workflows/ci.yml                    # Enhanced CI pipeline with React support
tests/test_timeline_integration.py          # Integration test suite
Makefile                                    # Added timeline viewer commands
README.md                                   # Updated with timeline viewer documentation
run_tests.sh                               # Added timeline and frontend test categories

memory/implementations/
├── react-timeline-viewer-complete.md       # Implementation documentation
└── complete-feature-summary.md             # Updated with React integration

memory/fixes/
└── ci-pipeline-timeline-viewer-integration.md  # CI/CD pipeline fix documentation
```

### Completed Successfully ✅
1. ✅ Complete React timeline viewer with interactive visualization
2. ✅ Data compatibility with real generator output format
3. ✅ Full CI/CD pipeline integration across all GitHub Actions jobs
4. ✅ All tests passing: 77 unit + 21 integration + 9 E2E + 6 timeline tests
5. ✅ Production-ready build system with optimized assets
6. ✅ Pull Request #7 ready for merge with robust CI pipeline

### Current System Capabilities
- **Interactive Timeline**: Real-time patient movement visualization through military medical facilities
- **Professional Interface**: Clean, responsive design with animations and status indicators
- **Data Processing**: Handles complex patient data with timeline events and facility tracking
- **CI/CD Pipeline**: Automated testing and validation for both backend and React application
- **Production Deployment**: Ready for immediate use with comprehensive documentation

```