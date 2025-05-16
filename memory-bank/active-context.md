# Active Context

## Current Work Focus

The project is embarking on a significant architectural enhancement to introduce comprehensive configurability for the patient generator. This initiative aims to support all NATO nations, allow customization of medical flow parameters, fronts, and other scenario details, and enable programmatic control via a new API layer.

The immediate focus is **Phase 0: Foundation & Setup**, which includes:
1.  **Establishing a robust Git branching model.**
2.  **Migrating the backend database from SQLite to PostgreSQL (clean install).**
3.  **Integrating Alembic for database schema migrations.**
4.  **Refactoring database interaction layer for PostgreSQL.**
5.  **Updating all Memory Bank documents to reflect this new plan.**

This foundational work will pave the way for subsequent phases involving backend configuration abstraction, API development, and frontend enhancements.

### Recent Changes

(This section reflects work prior to the new architectural initiative. It will be updated as new phases progress.)

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

The project will follow a phased approach to implement the enhanced configurability architecture.

**Overarching Principles:**
*   **Git Branching Strategy:** `main` (stable), `develop` (integration), `feature/<epic>/<task>`, `release/vX.Y.Z`, `hotfix/<issue>`.
*   **Task Breakdown & Acceptance Criteria:** Small, manageable units with clear, testable acceptance criteria.
*   **Iterative Memory Bank Updates:** Memory Bank and `.clinerules` updated at the end of each significant task or phase.
*   **Prioritize Technical Debt:** Integrate technical debt resolution into relevant feature development.

---

**Phase 0: Foundation & Setup (Current Focus)**
*   **Task 0.1: Update Memory Bank - Initial Plan (Completed)**
    *   Description: Document overall plan and architectural decisions in `active-context.md` and `progress.md`.
    *   Status: Completed.
*   **Task 0.2: Establish Git Branching Model**
    *   Description: Create `develop` branch. Document strategy.
    *   Acceptance Criteria: `develop` branch exists. Strategy documented.
*   **Task 0.3: Setup PostgreSQL Database**
    *   Description: Install/configure PostgreSQL. Update Docker Compose.
    *   Acceptance Criteria: PostgreSQL running and accessible.
*   **Task 0.4: Integrate Alembic for Database Migrations**
    *   Description: Add Alembic. Initialize. Create initial migration.
    *   Acceptance Criteria: Alembic configured. `alembic upgrade head` runs.
*   **Task 0.5: Refactor `patient_generator/database.py` for PostgreSQL**
    *   Description: Replace SQLite logic with PostgreSQL (psycopg2-binary). Implement connection pooling.
    *   Acceptance Criteria: Backend connects to PostgreSQL. Basic DB operations adapted.

---

**Phase 1: Backend Configuration Abstraction & Core Logic**
*   **Epic 1.1: Configuration Data Models & Database Schema**
    *   Task 1.1.1: Define Core Pydantic Models for Configuration (`FrontConfig`, `NationalityConfig`, `FacilityConfig`, `ConfigurationTemplate`).
    *   Task 1.1.2: Design PostgreSQL Schema & Create Alembic Migrations for configuration tables.
    *   Task 1.1.3: Implement `ConfigurationRepository` (CRUD for configurations in PostgreSQL).
*   **Epic 1.2: NATO Nations Data Repository**
    *   Task 1.2.1: Research and Collate NATO Nations Data (demographics, ID formats, etc.).
    *   Task 1.2.2: Implement `NationalityConfiguration` logic to load/access NATO data.
*   **Epic 1.3: Refactor Core Generation Logic for Configurability**
    *   Task 1.3.1: Create `ConfigurationManager` to load and provide active configuration.
    *   Task 1.3.2: Refactor `PatientFlowSimulator` for dynamic, configurable facility chains and parameters.
    *   Task 1.3.3: Refactor `DemographicsGenerator` to use configurable nationality data.
    *   Task 1.3.4: Refactor `MedicalConditionGenerator` (if needed for configurable flow parameters).
    *   Task 1.3.5: Update `patient_generator.app.PatientGeneratorApp` & FastAPI `app.py` to use `ConfigurationManager`.
    *   Task 1.3.6: Address Memory Management in Generation (streaming/generator patterns).
*   **Epic 1.4: Configuration Versioning & Default/Backward Compatibility**
    *   Task 1.4.1: Add Versioning to `ConfigurationTemplate` model and database.
    *   Task 1.4.2: Implement Default Configuration mimicking current hardcoded behavior.

---

**Phase 2: API Enhancement**
*   **Epic 2.1: Configuration Management API Endpoints**
    *   Task 2.1.1: Implement FastAPI Router and Pydantic Models for Config API.
    *   Task 2.1.2: Implement CRUD Endpoints for Configurations (`/api/v1/configurations/`).
    *   Task 2.1.3: Implement `/api/v1/configurations/validate/` Endpoint.
*   **Epic 2.2: Generation API Endpoints**
    *   Task 2.2.1: Implement FastAPI Router and Pydantic Models for Generation API.
    *   Task 2.2.2: Implement `POST /api/v1/generate/` Endpoint for job creation.
    *   Task 2.2.3: Implement Job Status (`/jobs/{job_id}/`) and Download Endpoints.
*   **Epic 2.3: Reference Data API Endpoints**
    *   Task 2.3.1: Implement Endpoints for reference data (nationalities, facility types, etc.).
*   **Epic 2.4: API Security & Documentation**
    *   Task 2.4.1: Implement API Authentication (Token-Based).
    *   Task 2.4.2: Implement Rate Limiting.
    *   Task 2.4.3: Generate/Enhance OpenAPI/Swagger Documentation.

---

**Phase 3: Frontend Enhancement & SDK**
*   **Epic 3.1: Frontend Configuration UI (`ConfigurationPanel` React Component)**
    *   Task 3.1.1: Basic Structure of `ConfigurationPanel.tsx`.
    *   Task 3.1.2: Fetch and Display Saved Configurations from API.
    *   Task 3.1.3: Implement Front Management UI (`FrontEditor` sub-component).
    *   Task 3.1.4: Implement Facility Management UI (`FacilityEditor` sub-component).
    *   Task 3.1.5: Implement Nationality Configuration UI.
    *   Task 3.1.6: Implement Save/Load/Apply Configuration Logic (interacting with API).
    *   Task 3.1.7: Implement Parameter Impact Preview (Basic).
    *   Task 3.1.8: Integrate Configuration Modal into `static/index.html`.
*   **Epic 3.2: Python SDK Development**
    *   Task 3.2.1: Implement `PatientGeneratorClient` Class structure.
    *   Task 3.2.2: Implement SDK Methods for Configuration API.
    *   Task 3.2.3: Implement SDK Methods for Generation API.
    *   Task 3.2.4: Add Examples and Documentation for SDK.

---

**Phase 4: Hardening, Technical Debt, and Final Touches**
*   **Epic 4.1: Address Remaining Technical Debt**
    *   Task 4.1.1: Security - Fix Encryption Salt in `formatter.py`.
    *   Task 4.1.2: Frontend Architecture Consolidation (visualization logic).
    *   Task 4.1.3: Frontend Bundle Size Optimization (externalize libraries/code splitting).
    *   Task 4.1.4: Docker Optimization (Multi-stage builds).
*   **Epic 4.2: Testing Expansion**
    *   Task 4.2.1: API Integration Tests.
    *   Task 4.2.2: End-to-End Tests (Consider Selenium/Playwright).
*   **Epic 4.3: Documentation Finalization**
    *   Task 4.3.1: Update User Guides for new features.
    *   Task 4.3.2: Update all Technical Documentation (Memory Bank, READMEs).

### Active Decisions

Key architectural and implementation decisions for the new initiative:

1.  **Architectural Shift:** Adopt a new architecture focused on comprehensive configurability, managed through a `ConfigurationManager` and database-backed persistence.
2.  **Database Migration:** Migrate from SQLite to PostgreSQL for the backend database, using a clean install (no data migration from SQLite).
3.  **Schema Management:** Utilize Alembic for managing PostgreSQL database schema migrations.
4.  **API-Driven Approach:** Implement a RESTful API for programmatic configuration and patient generation.
5.  **Phased Implementation:** Follow the detailed 5-phase plan (Phase 0 to Phase 4) outlined above.
6.  **Git Workflow:** Adopt a structured Git branching model (`main`, `develop`, feature branches, etc.).
7.  **SDK Development:** Provide a Python SDK for easier API integration.

Decisions from previous work (still relevant until refactored):
*   Dedicated Frontend Build: `esbuild` for `enhanced-visualization-dashboard.tsx`.
*   Component Self-Rendering: `enhanced-visualization-dashboard.tsx` handles its own DOM rendering.
*   Jest for Frontend Testing: Standard for React/TSX components.
*   Consistent Datetime Objects: Use `datetime.datetime` for `treatment_history`.
*   Bundling Core Frontend Libraries: Currently, React, ReactDOM, Recharts, and Lucide-React are bundled into `bundle.js`. (Future decision: externalize these to CDNs if needed).
*   Multiple Primary Conditions Logic: Implemented as per previous specifications.

### Current Challenges

Many previous challenges are being directly addressed by the new architectural plan. The primary challenges now revolve around the successful execution of this plan:

1.  **Complexity of New Architecture:** Managing the development and integration of the new configuration layer, database, API, and updated frontend components.
2.  **Scope Management:** Ensuring the phased implementation stays on track and avoids scope creep within each phase.
3.  **Data Sourcing (NATO Nations):** Collating and structuring comprehensive demographic data for all 32 NATO nations.
4.  **Performance with Dynamic Configurations:** Ensuring the generation engine remains performant with highly flexible and potentially complex configurations. This is an ongoing concern that the memory management tasks in Phase 1 aim to mitigate.
5.  **UI/UX for Advanced Configuration:** Designing an intuitive yet powerful UI for the new configuration capabilities.
6.  **Transition and Integration:** Smoothly integrating the new configuration system with the existing generation logic and frontend.
7.  **Technical Debt Integration:** Effectively tackling identified technical debt (e.g., encryption salt, frontend bundle size) alongside new feature development.

Challenges from previous technical review that are being actively addressed by the new plan:
*   Memory Management (addressed in Phase 1).
*   Error Handling Standardization (to be incorporated throughout new development).
*   Configuration Management (core of the new architecture).
*   Database Implementation (migrating to PostgreSQL, using Alembic).
*   Docker Optimization (Phase 4).
*   Security - Encryption Salt (Phase 4).

### Working Environment

The project is developed using:

1.  **Python 3.8+**: For the backend, using FastAPI.
2.  **PostgreSQL**: New backend database.
3.  **Alembic**: For database migrations.
4.  **Node.js & npm**: For frontend dependency management, testing (Jest), and building (esbuild).
5.  **TypeScript/TSX**: For the `enhanced-visualization-dashboard` React component and new configuration UI components.
6.  **React**: Frontend library for the enhanced dashboard and new UI.
7.  **Recharts, Lucide-React**: Charting and icon libraries for the React dashboard.
8.  **Bootstrap 5 & FontAwesome**: For general UI styling (loaded via CDN for HTML pages).
9.  **Standard Development Tools**:
    *   Python: Virtual environments, pip.
    *   Frontend: `package.json` for scripts and dependencies.
    *   Testing: `unittest` (Python), Jest (`ts-jest`) (Frontend).
    *   Version Control: Git.
    *   Containerization: Docker.

### Collaboration Context

The project appears to be set up for collaboration with:

1. **Modular Architecture**: Clear separation of concerns allowing developers to work on different components. This will be further enhanced by the new architecture.
2. **Comprehensive Documentation**: README, installation guides, and getting started documentation. Memory Bank is central.
3. **Unit Testing**: Test coverage for core functionality to ensure collaborative changes don't break existing features. Will be expanded.
4. **Standardized Interfaces**: Well-defined interfaces between components to facilitate parallel development, especially with the new API.
