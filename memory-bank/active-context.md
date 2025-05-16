# Active Context

## Current Work Focus

Based on the Military Medical Exercise Patient Generator codebase, this document tracks the current development focus, recent changes, and upcoming priorities.

### Current Focus

The project is enhancing its frontend capabilities, particularly for data visualization. Current focus areas include:

1.  **Enhanced Visualization Dashboard**: Implementing and stabilizing the new React/TSX-based advanced visualization dashboard (`enhanced-visualization-dashboard.tsx`). This includes setting up testing, a build process, and ensuring it integrates correctly with the backend.
2.  **Frontend Testing**: Establishing a robust testing environment for React/TSX components using Jest and React Testing Library.
3.  **Frontend Build Process**: Implementing a build pipeline (using `esbuild`) for frontend components to ensure they are correctly compiled and bundled for browser use.
4.  **Backend API Support**: Ensuring backend FastAPI routes correctly serve data required by the new visualization dashboard and are free of errors.
5.  **User Experience Refinement**: Continued focus on making data visualizations clear and useful.

### Recent Changes

Significant recent development has focused on the enhanced visualization dashboard:

1.  **Frontend Testing Setup**:
    *   Configured Jest (with `ts-jest`) to test `.tsx` (React/TypeScript) components.
    *   Installed necessary dev dependencies: `ts-jest`, `jest-environment-jsdom`, `@types/react-dom`, `@testing-library/react`, `@testing-library/jest-dom`.
    *   Created `jest.config.js` and `tsconfig.json` to support the testing and TypeScript compilation.
    *   Updated `setupTests.ts` to include mocks (e.g., `ResizeObserver`) needed for tests involving charting libraries.
    *   Successfully ran and debugged tests for `enhanced-visualization-dashboard.test.tsx`, resolving `act()` warnings.
2.  **Frontend Build Process**:
    *   Installed `esbuild` as a frontend bundler.
    *   Added a `build` script to `package.json` (`npm run build`) to compile `enhanced-visualization-dashboard.tsx` into `static/dist/bundle.js`.
    *   Modified `enhanced-visualization-dashboard.tsx` to include its own ReactDOM rendering logic, making it a self-contained application entry point when bundled.
3.  **HTML Integration**:
    *   Updated `static/visualizations.html` to load the compiled `bundle.js` instead of attempting in-browser Babel transpilation. Removed CDN links for React, ReactDOM, Recharts, and Lucide-React as they are now part of the bundle.
4.  **Backend API Fixes for Visualizations**:
    *   Diagnosed and resolved 404 errors for `/api/visualizations/job-list` by guiding the user on backend server restarts (related to Docker environment).
    *   Corrected the data format returned by the `/api/visualizations/job-list` endpoint in `app.py` to match frontend expectations.
    *   Diagnosed and fixed a 500 Internal Server Error for `/api/visualizations/dashboard-data`. The root cause was a `TypeError` in `patient_generator/flow_simulator.py` due to inconsistent `datetime.date` vs `datetime.datetime` objects in `treatment_history`. This was resolved by ensuring all treatment dates are `datetime.datetime` objects.
5.  **Previous Work (Context)**:
    *   Development of unit tests for Python core components (e.g., `transform_job_data_for_visualization`).
    *   Creation of Docker deployment documentation and testing of the dev Docker environment.
6.  **Multiple Primary Conditions Implementation**:
    *   Added `generate_multiple_conditions` method to `MedicalConditionGenerator` in `patient_generator/medical.py`.
    *   Modified `_process_patient_batch` in `PatientGeneratorApp` (`patient_generator/app.py`) to use the new method for generating multiple primary conditions based on injury type and triage category.
    *   Added `primary_conditions` list attribute to the `Patient` class in `patient_generator/patient.py`.
    *   Updated `_create_medical_resources` in `FHIRBundleGenerator` (`patient_generator/fhir_generator.py`) to handle the `primary_conditions` list and maintain backward compatibility.

### Next Steps

Building on the recent progress and incorporating findings from the technical review, the following refactoring roadmap is proposed:

**Phase 1: Critical Improvements (1-2 months)**

1.  **Memory Management Optimization**:
    *   Implement streaming/generator pattern for patient data processing (e.g., in `FHIRBundleGenerator`, `FlowSimulator`).
    *   Serialize large datasets (e.g., `patients_data` in `app.py`) to disk instead of keeping them entirely in memory.
    *   Add pagination for large result sets in API responses and UI displays.
2.  **Error Handling Standardization**:
    *   Define a custom exception hierarchy for backend Python code (e.g., `PatientGeneratorError`, `FlowSimulationError`).
    *   Implement consistent try/except blocks and structured logging throughout the backend.
    *   Implement React Error Boundaries in `enhanced-visualization-dashboard.tsx` and improve error feedback/retry mechanisms in the frontend.
3.  **Configuration Management**:
    *   Centralize configuration into a dedicated module (e.g., `config.py`) using Pydantic for validation.
    *   Utilize environment variables with sensible defaults.

**Phase 2: Frontend Improvements (1-2 months)**

4.  **Frontend Architecture Enhancement**:
    *   Optimize `static/dist/bundle.js` size by externalizing large libraries (React, Recharts) and using CDNs or code splitting.
    *   Consolidate visualization logic between `static/index.html` and `enhanced-visualization-dashboard.tsx` by creating shared utility functions or migrating `index.html` visualizations to React components.
    *   Implement a consistent state management approach for the React dashboard (e.g., React Context or a lightweight state management library).
5.  **User Experience Refinements (Frontend)**:
    *   Add more comprehensive loading states and progress indicators.
    *   Improve error feedback mechanisms.

**Phase 3: Testing and Documentation (1 month)**

6.  **Testing Coverage Expansion**:
    *   Add integration tests for API endpoints, covering full generation-to-visualization flows.
    *   Expand unit tests for key backend components and frontend React components.
    *   Consider implementing end-to-end tests.
7.  **Documentation Improvements**:
    *   Enhance API documentation (FastAPI route summaries, OpenAPI spec).
    *   Create/update user guides for both frontend interfaces.
    *   Update technical documentation, including `DOCKER_DEPLOYMENT.md` and notes on the frontend build/test process.

**Phase 4: Deployment Optimizations (1 month)**

8.  **Docker Optimization**:
    *   Implement multi-stage Docker builds to reduce final image sizes.
    *   Optimize Docker Compose configurations for different environments (dev, prod), including resource limits and health checks.
    *   Review and implement container security best practices.
9.  **Database Improvements**:
    *   Implement proper connection pooling for SQLite (if applicable, or consider if a more robust DB is needed for future scale).
    *   Ensure all SQL queries are parameterized to prevent injection vulnerabilities.
    *   Consider adding a migration management system (e.g., Alembic) if schema changes become frequent.

**Ongoing/General Project Goals**:
*   Continue documentation expansion.
*   Consider feature extensions (additional nationalities, medical conditions, etc.).
*   Address security vulnerabilities (e.g., fixed salt in encryption).

### Active Decisions

Key architectural and implementation decisions from recent work:

1.  **Dedicated Frontend Build**: Adopted `esbuild` for compiling and bundling the TSX-based `enhanced-visualization-dashboard`. This moves away from in-browser transpilation for this component.
2.  **Component Self-Rendering**: The `enhanced-visualization-dashboard.tsx` now includes logic to render itself into a DOM element, making the bundled output directly usable in an HTML page.
3.  **Jest for Frontend Testing**: Standardized on Jest with `ts-jest` for testing React/TSX components.
4.  **Consistent Datetime Objects**: Ensured `datetime.datetime` objects are used consistently for dates in `treatment_history` within the Python backend to prevent comparison errors.
5.  **Bundling Core Frontend Libraries**: Currently, React, ReactDOM, Recharts, and Lucide-React are bundled into `bundle.js`. This simplifies deployment but results in a larger bundle file. (Future decision: externalize these to CDNs if needed).
6.  **Multiple Primary Conditions Logic**: The new logic for generating multiple primary conditions has been implemented as per the user's detailed specification. This enhances medical realism.

### Current Challenges

Reflecting the technical review, key challenges include:

1.  **Memory Management**:
    *   In-memory storage of large patient datasets (e.g., `jobs[job_id]["patients_data"]` in `app.py`, FHIR bundle generation) is a primary concern for scalability.
2.  **Error Handling**:
    *   Inconsistent error handling across the backend and frontend. Lack of standardized exceptions and recovery mechanisms.
3.  **Frontend Architecture**:
    *   Managing the mix of traditional JS and React/TSX, including duplicate visualization logic.
    *   The large bundle size of `static/dist/bundle.js` (~2.1MB) requires optimization.
    *   Inconsistent state management in the React dashboard.
4.  **Configuration Management**:
    *   Potential for redundant or scattered configuration settings.
5.  **Testing Coverage**:
    *   Uneven test coverage, especially for API integrations and some frontend aspects.
6.  **Database Implementation**:
    *   Limited connection pooling and potential SQL injection risks. Lack of schema migration management.
7.  **Docker Optimization**:
    *   Large container images and opportunities for optimizing Docker Compose files.
8.  **Security**:
    *   Identified vulnerabilities like fixed salt in encryption.
9.  **Development Workflow**: Managing the hybrid Python/Node.js environment.
10. **Data Consistency**: Ensuring data structures align between backend and frontend.

### Working Environment

The project is developed using:

1.  **Python 3.8+**: For the backend, using FastAPI.
2.  **Node.js & npm**: For frontend dependency management, testing (Jest), and building (esbuild).
3.  **TypeScript/TSX**: For the `enhanced-visualization-dashboard` React component.
4.  **React**: Frontend library for the enhanced dashboard.
5.  **Recharts, Lucide-React**: Charting and icon libraries for the React dashboard.
6.  **FastAPI**: Asynchronous web framework for the backend API.
7.  **Bootstrap 5 & FontAwesome**: For general UI styling (loaded via CDN for HTML pages).
8.  **Standard Development Tools**:
    *   Python: Virtual environments, pip.
    *   Frontend: `package.json` for scripts and dependencies.
    *   Testing: `unittest` (Python), Jest (`ts-jest`) (Frontend).
    *   Version Control: Git.
    *   Containerization: Docker (as implied by user and project files like `Dockerfile`).

### Collaboration Context

The project appears to be set up for collaboration with:

1. **Modular Architecture**: Clear separation of concerns allowing developers to work on different components.

2. **Comprehensive Documentation**: README, installation guides, and getting started documentation.

3. **Unit Testing**: Test coverage for core functionality to ensure collaborative changes don't break existing features.

4. **Standardized Interfaces**: Well-defined interfaces between components to facilitate parallel development.
