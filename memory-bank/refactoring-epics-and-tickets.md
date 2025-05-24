# Refactoring Epics and Tickets

## Epic 1: UI Testing and Stabilization (High Priority)
**Goal**: Ensure the UI remains fully functional after backend refactoring

### Ticket UI-001: Test and Fix API Endpoints
**Status**: In Progress
**Priority**: High
**Acceptance Criteria**:
- [ ] All UI pages load without errors
- [ ] API endpoints respond correctly with expected data format
- [ ] Authentication headers are properly handled
- [ ] Error messages display appropriately
**Test Plan**:
1. Test index.html configuration panel
2. Test visualizations.html dashboard
3. Verify API connectivity with correct headers
4. Check all CRUD operations work

### Ticket UI-002: Fix CORS and API Integration Issues
**Status**: Pending
**Priority**: High
**Acceptance Criteria**:
- [ ] CORS configured correctly for frontend-backend communication
- [ ] API base URL properly configured in static/js/api-config.js
- [ ] All fetch requests include proper authentication headers
**Test Plan**:
1. Verify CORS settings in FastAPI
2. Test cross-origin requests from UI
3. Check browser console for CORS errors

## Epic 2: Async Patient Generation Pipeline (High Priority)
**Goal**: Replace synchronous threading with async/await for better scalability

### Ticket ASYNC-001: Create Async Patient Generation Service
**Status**: Pending
**Priority**: High
**Acceptance Criteria**:
- [ ] PatientGenerationPipeline class created with async methods
- [ ] Stream-based patient generation implemented
- [ ] Progress callbacks work asynchronously
- [ ] Memory usage reduced by streaming
**Test Plan**:
1. Unit tests for async generation methods
2. Performance tests comparing sync vs async
3. Memory profiling during large batch generation

### Ticket ASYNC-002: Refactor Background Tasks to Use Async
**Status**: Pending
**Priority**: High
**Acceptance Criteria**:
- [ ] Background tasks use asyncio instead of threading
- [ ] Job progress updates work with async pipeline
- [ ] Proper error handling for async operations
**Test Plan**:
1. Generate 1000+ patients and monitor performance
2. Test job cancellation mid-generation
3. Verify progress updates are real-time

### Ticket ASYNC-003: Implement Batch Processing
**Status**: Pending
**Priority**: Medium
**Acceptance Criteria**:
- [ ] Patients generated in configurable batches
- [ ] Batch size optimized for performance
- [ ] Progress updates per batch completion
**Test Plan**:
1. Test different batch sizes (10, 100, 1000)
2. Monitor memory usage across batches
3. Verify no data loss between batches

## Epic 3: Performance Optimization (Medium Priority)
**Goal**: Add caching and optimize resource usage

### Ticket PERF-001: Add Redis Caching Layer
**Status**: Pending
**Priority**: Medium
**Acceptance Criteria**:
- [ ] Redis integrated via docker-compose
- [ ] CacheService implemented with get/set/invalidate
- [ ] Demographics data cached appropriately
- [ ] Medical conditions cached with TTL
**Test Plan**:
1. Test cache hit/miss rates
2. Verify TTL expiration works
3. Performance comparison with/without cache

### Ticket PERF-002: Implement Database Connection Pooling
**Status**: Pending
**Priority**: Medium
**Acceptance Criteria**:
- [ ] Connection pool configured for PostgreSQL
- [ ] Pool size optimized for concurrent requests
- [ ] Connection reuse verified
**Test Plan**:
1. Load test with concurrent requests
2. Monitor database connections
3. Check for connection leaks

## Epic 4: Frontend Modernization (Medium Priority)
**Goal**: Unify frontend architecture with modern React and state management

### Ticket FE-001: Create Unified React Application
**Status**: Pending
**Priority**: Medium
**Acceptance Criteria**:
- [ ] Single React app replaces mixed vanilla JS/React
- [ ] React Router for navigation
- [ ] Consistent component structure
**Test Plan**:
1. All pages render correctly in React
2. Navigation works without page reloads
3. State persists across route changes

### Ticket FE-002: Implement State Management
**Status**: Pending
**Priority**: Medium
**Acceptance Criteria**:
- [ ] Zustand or Redux store implemented
- [ ] Configuration state managed centrally
- [ ] Job state updates reflected in UI
**Test Plan**:
1. State changes reflect across components
2. State persists to localStorage
3. State hydration on page reload

### Ticket FE-003: Build Component Library
**Status**: Pending
**Priority**: Low
**Acceptance Criteria**:
- [ ] Reusable UI components created
- [ ] Consistent styling system
- [ ] Storybook for component documentation
**Test Plan**:
1. All components render in isolation
2. Props validation works
3. Accessibility standards met

## Epic 5: Developer Experience (Low Priority)
**Goal**: Improve development workflow and tooling

### Ticket DX-001: Create Makefile
**Status**: Pending
**Priority**: Low
**Acceptance Criteria**:
- [ ] Common commands available via make
- [ ] Development setup simplified
- [ ] Testing commands included
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
**Status**: Pending
**Priority**: Medium
**Acceptance Criteria**:
- [ ] API integration tests cover all endpoints
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

1. **Immediate (This Session)**:
   - UI-001: Test and Fix API Endpoints
   - UI-002: Fix CORS and API Integration Issues

2. **Next Priority**:
   - ASYNC-001: Create Async Patient Generation Service
   - ASYNC-002: Refactor Background Tasks to Use Async

3. **Following Priorities**:
   - PERF-001: Add Redis Caching Layer
   - FE-001: Create Unified React Application
   - TEST-001: Add Integration Tests

4. **Future Work**:
   - Remaining tickets as time permits