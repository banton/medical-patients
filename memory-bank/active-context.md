# Active Context

## Current Work Focus

The project has completed the primary implementation phases (0-3) for the new enhanced configurability architecture. This includes the migration to PostgreSQL, a new API layer, refactored core generation logic, an initial frontend configuration panel, and a Python SDK.

The current focus is **Phase 4: Hardening, Technical Debt, and Final Touches**. This involves:
1.  Addressing identified technical debt (frontend architecture, bundle sizes, Docker optimization).
2.  Expanding testing coverage (API integration, E2E tests).
3.  Finalizing all user and technical documentation (Current Task: 4.3.2).
4.  Ensuring overall system stability and performance.
5.  Implementing UI enhancements for static configurations (Task 4.4.1).

### Recent Changes

**Completion of Phases 0-3 (Enhanced Configurability Architecture):**
*   **Phase 0 (Foundation & Setup):** Established Git branching, migrated to PostgreSQL, integrated Alembic, and refactored the database layer.
*   **Phase 1 (Backend Configuration Abstraction):** Implemented Pydantic models for configuration, designed the PostgreSQL schema for configurations, created `ConfigurationRepository`, `NationalityDataProvider`, `ConfigurationManager`, and refactored core generation logic (`PatientFlowSimulator`, `DemographicsGenerator`, `PatientGeneratorApp`) to be configuration-driven. Basic configuration versioning and default configuration concepts were introduced.
*   **Phase 2 (API Enhancement):** Developed a versioned RESTful API (`/api/v1/`) with endpoints for CRUD operations on configurations, validation, patient generation (accepting `configuration_id`), job status, results, and reference data. Basic API security (API key) and rate limiting were implemented. OpenAPI documentation is auto-generated.
*   **Phase 3 (Frontend Enhancement & SDK):** Created the `ConfigurationPanel.tsx` React component for advanced scenario configuration (integrated into `static/index.html`), including UI for managing fronts, facilities, and basic parameter impact previews. Developed a Python SDK (`patient_generator_sdk.py`) for programmatic API interaction.

**Specific Phase 4 Completions (Committed May 20, 2025):**
1.  **Security Fix (Task 4.1.1):** Implemented unique salt generation using PBKDF2 for encryption in `formatter.py`, enhancing security.
2.  **UI Update - Nationality Distribution (Task 4.1.5):** Modified `FrontEditor.tsx` (within `ConfigurationPanel.tsx`) to use an ordered list of dropdowns for nationality distribution per front, improving usability and data structure. Backend Pydantic schemas and an Alembic migration marker were updated accordingly.
3.  **UI Update - Injury Distribution & Error Handling (Task 4.1.6):** Reverted injury distribution input in `ConfigurationPanel.tsx` to three fixed categories ("Battle Injury", "Disease", "Non-Battle Injury") based on user feedback. Backend Pydantic schemas were updated. Basic API error display in the panel remains.
4.  **Database Fix - Configuration Versioning (Task 4.1.7):** Corrected `parent_config_id` (was `parent_id`) usage in `patient_generator/database.py` SQL queries to ensure accurate linking for configuration versioning, following the successful application of Alembic migration `2b84a220e9ac` (which added `version` and `parent_config_id` columns).
5.  **Developer Experience Improvement (Prior to current commit, May 16, 2025):**
    *   Consolidated frontend build commands in `package.json` (`build:all-frontend`).
    *   Created `start-dev.sh` script for automated dev environment setup (npm install, frontend build, Docker services, DB migrations with health checks).
    *   Updated `alembic_migrations/env.py` for robust Docker DB connections.

### Next Steps

The project will follow a phased approach to implement the enhanced configurability architecture.

**Overarching Principles:**
*   **Git Branching Strategy:** `main` (stable), `develop` (integration), `feature/<epic>/<task>`, `release/vX.Y.Z`, `hotfix/<issue>`.
*   **Task Breakdown & Acceptance Criteria:** Small, manageable units with clear, testable acceptance criteria.
*   **Iterative Memory Bank Updates:** Memory Bank and `.clinerules` updated at the end of each significant task or phase.
*   **Prioritize Technical Debt:** Integrate technical debt resolution into relevant feature development.

---

**Phase 0: Foundation & Setup (Completed)**
*   Task 0.1: Update Memory Bank - Initial Plan (Completed)
*   Task 0.2: Establish Git Branching Model (Completed)
*   Task 0.3: Setup PostgreSQL Database (Completed)
*   Task 0.4: Integrate Alembic for Database Migrations (Completed)
*   Task 0.5: Refactor `patient_generator/database.py` for PostgreSQL (Completed)

---

**Phase 1: Backend Configuration Abstraction & Core Logic (Completed)**
*   **Epic 1.1: Configuration Data Models & Database Schema (Completed)**
    *   Task 1.1.1: Define Core Pydantic Models (Completed)
    *   Task 1.1.2: Design PostgreSQL Schema & Create Alembic Migrations (Completed)
    *   Task 1.1.3: Implement `ConfigurationRepository` (Completed)
*   **Epic 1.2: NATO Nations Data Repository (Completed)**
    *   Task 1.2.1: Collate NATO Nations Data (User Provided) (Completed)
    *   Task 1.2.2: Implement `NationalityDataProvider` (Completed)
*   **Epic 1.3: Refactor Core Generation Logic (Completed)**
    *   Task 1.3.1: Create `ConfigurationManager` (Completed)
    *   Task 1.3.2: Refactor `PatientFlowSimulator` (Completed)
    *   Task 1.3.3: Refactor `DemographicsGenerator` (Completed)
    *   Task 1.3.4: Refactor `MedicalConditionGenerator` (No changes needed at this stage) (Completed)
    *   Task 1.3.5: Update `patient_generator.app.PatientGeneratorApp` & FastAPI `app.py` (Completed)
    *   Task 1.3.6: Address Memory Management (Initial improvements made) (Completed for Phase 1 scope)
*   **Epic 1.4: Configuration Versioning & Default/Backward Compatibility (Completed)**
    *   Task 1.4.1: Add Versioning to `ConfigurationTemplate` (DB migration `2b84a220e9ac` applied) (Completed)
    *   Task 1.4.2: Implement Default Configuration (Design completed, seeding separate) (Completed for Phase 1 scope)

---

**Phase 2: API Enhancement (Completed)**
*   **Epic 2.1: Configuration Management API Endpoints (Completed)**
    *   Task 2.1.1: Implement FastAPI Router and Models (Completed)
    *   Task 2.1.2: Implement CRUD Endpoints (Completed)
    *   Task 2.1.3: Implement `/validate/` Endpoint (Completed)
*   **Epic 2.2: Generation API Endpoints (Completed)**
    *   Task 2.2.1: Implement FastAPI Router and Models (Completed as part of main app.py refactor)
    *   Task 2.2.2: Implement `POST /api/generate/` Endpoint (Completed)
    *   Task 2.2.3: Implement Job Status & Download Endpoints (Existing adapted, new `/results` added) (Completed)
*   **Epic 2.3: Reference Data API Endpoints (Completed)**
    *   Task 2.3.1: Implement Endpoints for nationalities, condition types (Completed)
*   **Epic 2.4: API Security & Documentation (Completed)**
    *   Task 2.4.1: Implement API Authentication (Basic API Key) (Completed)
    *   Task 2.4.2: Implement Rate Limiting (Basic global) (Completed)
    *   Task 2.4.3: Generate/Enhance OpenAPI/Swagger Documentation (Via FastAPI auto-docs) (Completed)

---

**Phase 3: Frontend Enhancement & SDK (Completed)**
*   **Epic 3.1: Frontend Configuration UI (`ConfigurationPanel` React Component) (Completed)**
    *   Task 3.1.1: Basic Structure of `ConfigurationPanel.tsx` (Completed)
    *   Task 3.1.2: Fetch and Display Saved Configurations (Completed)
    *   Task 3.1.3: Implement Front Management UI (Completed)
    *   Task 3.1.4: Implement Facility Management UI (Completed)
    *   Task 3.1.5: Implement Nationality Configuration UI (Part of FrontEditor, ordered list dropdowns) (Completed)
    *   Task 3.1.6: Implement Save/Load/Apply Configuration Logic (Save/Load completed)
    *   Task 3.1.7: Implement Parameter Impact Preview (Basic textual) (Completed)
    *   Task 3.1.8: Integrate Configuration Modal into `static/index.html` (Completed)
*   **Epic 3.2: Python SDK Development (Completed)**
    *   Task 3.2.1: Implement `PatientGeneratorClient` Class structure (Completed)
    *   Task 3.2.2: Implement SDK Methods for Configuration API (Completed)
    *   Task 3.2.3: Implement SDK Methods for Generation API (Completed)
    *   Task 3.2.4: Add Examples and Documentation for SDK (Basic example in file) (Completed)

---

**Phase 4: Hardening, Technical Debt, and Final Touches (Current Focus)**
*   **Epic 4.1: Address Remaining Technical Debt**
    *   Task 4.1.1: Security - Fix Encryption Salt in `formatter.py`. (Completed)
    *   Task 4.1.2: Frontend Architecture Consolidation (visualization logic).
        *   **Objective:** Consolidate Visualization Logic into React Components.
        *   **Status:** Pending.
    *   Task 4.1.3: Frontend Bundle Size Optimization (externalize libraries/code splitting).
        *   **Status:** Pending.
    *   Task 4.1.4: Docker Optimization (Multi-stage builds).
        *   **Status:** Pending.
    *   Task 4.1.5: UI Refinement - Nationality Distribution in Front Editor. (Completed)
    *   Task 4.1.6: UI Refinement - Injury Distribution and Error Handling. (Completed - Reverted to simpler model)
    *   Task 4.1.7: Database Schema Update for `version` and `parent_config_id` (DB fix for `parent_config_id` usage). (Completed)
*   **Epic 4.2: Testing Expansion**
    *   Task 4.2.1: API Integration Tests.
        *   **Status:** Pending.
    *   Task 4.2.2: End-to-End Tests (Consider Selenium/Playwright).
        *   **Status:** Pending.
*   **Epic 4.3: Documentation Finalization**
    *   Task 4.3.1: Update User Guides for new features.
        *   **Status:** Pending.
    *   Task 4.3.2: Update all Technical Documentation (Memory Bank, READMEs, SDK). (Current Task)
*   **Epic 4.4: UI Enhancements for Static Configurations**
    *   Task 4.4.1: UI for Static Fronts Configuration.
        *   **Objective:** Create a UI section within `ConfigurationPanel.tsx` to view/edit parameters from `patient_generator/fronts_config.json`.
        *   **Status:** Pending.

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
