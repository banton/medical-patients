# Refactoring Epics and Tickets

## Epic 1: UI Testing and Stabilization (High Priority)
**Goal**: Ensure the UI remains fully functional after backend refactoring

### Ticket UI-001: Test and Fix API Endpoints
**Status**: Completed
**Priority**: High
**Acceptance Criteria**:
- [x] All UI pages load without errors
- [x] API endpoints respond correctly with expected data format
- [x] Authentication headers are properly handled
- [x] Error messages display appropriately
**Test Plan**:
1. Test index.html configuration panel
2. Test visualizations.html dashboard
3. Verify API connectivity with correct headers
4. Check all CRUD operations work

### Ticket UI-002: Fix CORS and API Integration Issues
**Status**: Completed
**Priority**: High
**Acceptance Criteria**:
- [x] CORS configured correctly for frontend-backend communication
- [x] API base URL properly configured in static/js/api-config.js
- [x] All fetch requests include proper authentication headers
**Test Plan**:
1. Verify CORS settings in FastAPI
2. Test cross-origin requests from UI
3. Check browser console for CORS errors

### Ticket UI-003: Implement Dynamic Front Configuration
**Status**: Completed
**Priority**: High
**Acceptance Criteria**:
- [x] Remove React dependencies from main UI
- [x] Implement dynamic add/remove fronts functionality
- [x] Per-front nationality distribution configuration
- [x] Real-time validation of casualty rates (sum to 100%)
- [x] Real-time validation of nationality percentages per front
- [x] Duplicate nationality prevention within fronts
**Test Plan**:
1. Users can add/remove fronts dynamically
2. Validation prevents invalid configurations
3. Form submission generates correct API payload
4. UI remains responsive with multiple fronts

## Epic 2: Async Patient Generation Pipeline (High Priority)
**Goal**: Replace synchronous threading with async/await for better scalability

### Ticket ASYNC-001: Create Async Patient Generation Service
**Status**: Completed
**Priority**: High
**Acceptance Criteria**:
- [x] PatientGenerationPipeline class created with async methods
- [x] Stream-based patient generation implemented
- [x] Progress callbacks work asynchronously
- [x] Memory usage reduced by streaming
**Test Plan**:
1. Unit tests for async generation methods
2. Performance tests comparing sync vs async
3. Memory profiling during large batch generation

### Ticket ASYNC-002: Refactor Background Tasks to Use Async
**Status**: Completed
**Priority**: High
**Acceptance Criteria**:
- [x] Background tasks use asyncio instead of threading
- [x] Job progress updates work with async pipeline
- [x] Proper error handling for async operations
**Test Plan**:
1. Generate 1000+ patients and monitor performance
2. Test job cancellation mid-generation
3. Verify progress updates are real-time

### Ticket ASYNC-003: Implement Batch Processing
**Status**: Completed
**Priority**: Medium
**Acceptance Criteria**:
- [x] Patients generated in configurable batches
- [x] Batch size optimized for performance (100 patients per batch)
- [x] Progress updates per batch completion
**Test Plan**:
1. Test different batch sizes (10, 100, 1000)
2. Monitor memory usage across batches
3. Verify no data loss between batches

## Epic 3: Performance Optimization (Medium Priority)
**Goal**: Add caching and optimize resource usage

### Ticket PERF-001: Add Redis Caching Layer
**Status**: Completed
**Priority**: Medium
**Acceptance Criteria**:
- [x] Redis integrated via docker-compose
- [x] CacheService implemented with get/set/invalidate
- [x] Demographics data cached appropriately
- [x] Medical conditions cached with TTL
**Test Plan**:
1. Test cache hit/miss rates
2. Verify TTL expiration works
3. Performance comparison with/without cache

### Ticket PERF-002: Implement Database Connection Pooling
**Status**: Completed
**Priority**: Medium
**Acceptance Criteria**:
- [x] Connection pool configured for PostgreSQL (SimpleConnectionPool)
- [x] Pool size optimized for concurrent requests (1-20 connections)
- [x] Connection reuse verified (get/release pattern)
**Test Plan**:
1. Load test with concurrent requests
2. Monitor database connections
3. Check for connection leaks

## Epic 4: Frontend Enhancement (Medium Priority)
**Goal**: Enhance vanilla JavaScript architecture for better maintainability and user experience

### Ticket FE-001: Modularize JavaScript Architecture
**Status**: Completed
**Priority**: Medium
**Acceptance Criteria**:
- [x] Separate concerns into modules (config, validation, api, ui)
- [x] Use ES6 modules with proper imports/exports
- [x] Implement event-driven architecture for component communication
- [x] Create reusable UI component functions
- [x] Document module interfaces and dependencies
**Test Plan**:
1. Each module can be tested in isolation
2. No global variable pollution
3. Module dependencies are explicit and minimal
4. UI updates work through event system

### Ticket FE-002: Add Configuration Persistence
**Status**: Pending
**Priority**: Medium
**Acceptance Criteria**:
- [ ] Save/load front configurations to localStorage
- [ ] Import/export configurations as JSON files
- [ ] Configuration templates (preset scenarios)
- [ ] Undo/redo for configuration changes
- [ ] Auto-save draft configurations
**Test Plan**:
1. Configurations persist across browser sessions
2. Export produces valid JSON matching schema
3. Import validates and loads configurations correctly
4. Undo/redo maintains consistent state
5. Auto-save recovers from browser crashes

### Ticket FE-003: Enhance Accessibility and UX
**Status**: Partially Complete
**Priority**: Medium
**Acceptance Criteria**:
- [ ] Full keyboard navigation support
- [ ] ARIA labels and roles for all interactive elements
- [ ] Screen reader compatible
- [x] Loading states and progress indicators
- [ ] Tooltip help for complex fields
- [x] Form validation with inline error messages
- [ ] Responsive design for mobile/tablet
**Test Plan**:
1. Tab navigation works through all form elements
2. Screen reader announces all actions correctly
3. Color contrast meets WCAG AA standards
4. Works on mobile devices (iOS/Android)
5. Loading states prevent duplicate submissions

### Ticket FE-004: Improve Performance and Error Handling
**Status**: Pending
**Priority**: Low
**Acceptance Criteria**:
- [ ] Debounce validation on input fields
- [ ] Lazy load nationality data
- [ ] Implement request retry logic with exponential backoff
- [ ] Graceful degradation when API is unavailable
- [ ] Client-side caching of reference data
- [ ] Performance monitoring and metrics
**Test Plan**:
1. Page loads in under 2 seconds
2. Input validation doesn't block typing
3. API failures show user-friendly messages
4. Offline mode shows cached data
5. Memory usage stays constant during long sessions

## Epic 5: Developer Experience (Low Priority)
**Goal**: Improve development workflow and tooling

### Ticket DX-001: Create Makefile
**Status**: Completed
**Priority**: Low
**Acceptance Criteria**:
- [x] Common commands available via make
- [x] Development setup simplified (make dev, make dev-with-data)
- [x] Testing commands included
**Test Plan**:
1. make dev starts environment
2. make test runs all tests
3. make clean removes artifacts

### Ticket DX-002: Set Up CI/CD Pipeline
**Status**: Pending
**Priority**: Low
**Acceptance Criteria**:
- [ ] GitHub Actions workflow created
- [ ] Tests run on PR
- [ ] Docker images built and pushed
- [ ] Deployment automation configured
**Test Plan**:
1. PR triggers test suite
2. Main branch builds deploy
3. Failed tests block merge

### Ticket DX-003: Add Linting and Formatting
**Status**: Pending
**Priority**: Low
**Acceptance Criteria**:
- [ ] Ruff configured for Python
- [ ] ESLint/Prettier for JavaScript
- [ ] Pre-commit hooks set up
**Test Plan**:
1. Linting catches style issues
2. Formatting auto-fixes code
3. Pre-commit prevents bad commits

## Epic 6: Enhanced Testing Infrastructure (Low Priority)
**Goal**: Comprehensive testing coverage and tooling

### Ticket TEST-001: Add Integration Tests
**Status**: Partially Complete
**Priority**: Medium
**Acceptance Criteria**:
- [x] API integration tests cover all endpoints (tests_api.py)
- [ ] Database integration tests with test containers
- [ ] End-to-end user flow tests
**Test Plan**:
1. All API endpoints have tests
2. Database operations tested in isolation
3. Critical user paths covered

### Ticket TEST-002: Set Up Test Containers
**Status**: Pending
**Priority**: Low
**Acceptance Criteria**:
- [ ] PostgreSQL test container configured
- [ ] Redis test container for cache tests
- [ ] Tests run in isolated environments
**Test Plan**:
1. Tests start/stop containers
2. No test data pollution
3. Parallel test execution works

## Implementation Order

1. **Completed**:
   - ✅ UI-001: Test and Fix API Endpoints
   - ✅ UI-002: Fix CORS and API Integration Issues
   - ✅ UI-003: Implement Dynamic Front Configuration

2. **Completed (This Session)**:
   - ✅ ASYNC-001: Create Async Patient Generation Service
   - ✅ ASYNC-002: Refactor Background Tasks to Use Async
   - ✅ FE-001: Modularize JavaScript Architecture

3. **Completed (Previous Work)**:
   - ✅ ASYNC-003: Implement Batch Processing
   - ✅ PERF-002: Implement Database Connection Pooling
   - ✅ DX-001: Create Makefile

4. **Completed (This Session - Part 2)**:
   - ✅ PERF-001: Add Redis Caching Layer

5. **Next Priority (Medium)**:
   - FE-002: Add Configuration Persistence
   - FE-003: Enhance Accessibility and UX (Partial)
   - TEST-001: Add Integration Tests (Partial)

6. **Low Priority**:
   - FE-004: Improve Performance and Error Handling
   - DX-002: Set Up CI/CD Pipeline
   - DX-003: Add Linting and Formatting
   - TEST-002: Set Up Test Containers
   - Remaining tickets as time permits

## Notes on Priority Changes

- **React Migration Cancelled**: Based on successful vanilla JS implementation, React migration (old FE-001/FE-002) has been replaced with vanilla JS enhancements
- **Frontend Focus**: New FE tickets focus on improving the existing vanilla JS architecture rather than introducing framework complexity
- **User Experience**: Emphasis on accessibility, persistence, and performance improvements that directly benefit end users