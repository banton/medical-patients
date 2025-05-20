# Progress

## Current Status

The Military Medical Exercise Patient Generator has undergone a major architectural overhaul, completing Phases 0-3 of the enhanced configurability initiative. This includes:
*   Migration to a PostgreSQL database with Alembic for schema management.
*   A new backend architecture for dynamic configuration of scenarios (fronts, facilities, nationalities, injury distributions).
*   A comprehensive RESTful API for managing configurations and patient generation jobs.
*   An initial frontend UI (React-based modal) for advanced scenario configuration.
*   A Python SDK for programmatic API interaction.

The project is currently at the **beginning of Phase 4: Hardening, Technical Debt, and Final Touches**.

### What Works (After Phases 0-3 of New Initiative)

1.  **Core Patient Generation (Now Configurable)**:
    *   Patient flow simulation through dynamically configured medical facility chains.
    *   Demographics generation supporting all NATO nations (via `demographics.json`).
    *   Configurable front definitions, casualty rates, and per-front nationality distributions.
    *   Configurable overall injury type distribution and total patient counts.
    *   Medical condition generation (SNOMED CT, multiple primary conditions) - *largely unchanged but now driven by configurable inputs*.
    *   HL7 FHIR R4 bundle creation.

2.  **Database & Configuration**:
    *   PostgreSQL backend database.
    *   Alembic for database schema migrations (initial tables for jobs and configurations created).
    *   Configuration templates can be saved, loaded, updated, and deleted via API.
    *   Configuration versioning (basic fields added to Pydantic models, DB migration pending).

3.  **API Layer**:
    *   RESTful API (`/api/v1/configurations/`) for CRUD operations on configuration templates.
    *   API endpoint (`/api/v1/configurations/validate/`) for validating configurations.
    *   Reference data API endpoints for nationalities and condition types.
    *   Main generation API (`/api/generate`) now accepts `configuration_id` or ad-hoc configuration.
    *   Job status, results summary, and download APIs are functional.
    *   Basic API key authentication and rate limiting applied to configuration API.

4.  **Web Interface**:
    *   Existing main UI (`static/index.html`) for basic generation (now needs to be adapted to use new config system or a default config ID).
    *   **New Advanced Configuration Panel**: A React-based modal (`ConfigurationPanel.tsx`) integrated into `static/index.html` for creating, loading, and editing detailed scenario configurations.
        *   Nationality distribution per front uses an ordered list of dropdowns.
        *   Overall injury distribution uses fixed inputs for "Battle Injury", "Disease", "Non-Battle Injury".
        *   Basic API error display.
    *   Enhanced Visualization Dashboard (`static/visualizations.html`) remains functional.

5.  **Python SDK**:
    *   A client library (`patient_generator_sdk.py`) for interacting with the new API.

3.  **Output Options**:
    *   JSON and XML formatting
    *   Compression with gzip
    *   Encryption with AES-256-GCM
    *   NDEF formatting for NFC tags

4.  **Command Line Support**:
    *   Demo script for direct usage
    *   Configuration via JSON - *to be updated for new configuration structure*.

5.  **Testing**:
    *   Unit tests for core Python components.
    *   Frontend tests for `enhanced-visualization-dashboard.tsx` using Jest and React Testing Library.
    *   All existing unit tests (Python and frontend) were passing prior to this new initiative.

6.  **Docker Development Environment**:
    *   Docker Compose files (`docker-compose.dev.yml`, `docker-compose.yml`, `docker-compose.prod.yml`) updated for PostgreSQL.
    *   Added `start-dev.sh` script to automate development environment setup. This script now correctly identifies the application service as `app`, waits for it to be "healthy" using its Docker healthcheck, and then applies DB migrations.
    *   Alembic's `env.py` was updated to prioritize `DATABASE_URL` from the environment, ensuring correct DB connection (to `db` service) when migrations are run inside Docker via `start-dev.sh` (May 16, 2025). This combination significantly improves startup reliability.
7.  **Frontend Build Process**:
    *   Consolidated frontend build commands in `package.json` under `build:all-frontend` (May 16, 2025). This ensures all necessary assets like `configuration-panel.js` are built.

### What's Left to Build/Improve (Focus of Phase 4)

1.  **Technical Debt Resolution**:
    *   **Security - Encryption Salt**: Refactor `formatter.py` to use unique, random salts for encryption (Task 4.1.1). (Completed)
    *   **Frontend Architecture Consolidation**: Review and potentially unify visualization logic between `index.html` and `visualizations.html` (Task 4.1.2).
    *   **Frontend Bundle Size Optimization**: Optimize bundles for `enhanced-visualization-dashboard.tsx` and `ConfigurationPanel.tsx` (Task 4.1.3).
    *   **Docker Optimization**: Implement multi-stage builds and review container security (Task 4.1.4).
    *   **Alembic "Multiple Heads" Issue**: Manually resolve the divergent migration history to allow new migrations to be generated and applied correctly. This is blocking the formal addition of `version` and `parent_config_id` columns to the database schema.
2.  **Testing Expansion**:
    *   Develop comprehensive API integration tests (Task 4.2.1).
    *   Consider and implement End-to-End (E2E) tests for key user flows (Task 4.2.2).
3.  **Documentation Finalization**:
    *   Update user guides for the new configuration panel and API usage (Task 4.3.1).
    *   Ensure all technical documentation (Memory Bank, READMEs, SDK docs) is current and complete (Task 4.3.2).
4.  **UI/UX Refinements for Configuration Panel**:
    *   Drag-and-drop for reordering facilities.
    *   Enhanced parameter impact preview.
    *   More robust error handling and user feedback (beyond current basic display).
5.  **Default Configuration Seeding**:
    *   Create and execute a script to seed the database with the "Default Scenario (Legacy)" configuration template.
6.  **Main UI (`static/index.html`) Adaptation**:
    *   Update the main generation form to either use a default `configuration_id` or allow selection from saved templates, rather than individual parameter inputs.
7.  **UI for Static Fronts Configuration (New - Phase 4, Epic 4.4)**:
    *   Task 4.4.1: Create a UI section in the advanced configuration panel to view (and eventually edit) parameters from `patient_generator/fronts_config.json`. (Pending)
8.  **Nationality Distribution UI Refinement (Completed)**:
    *   The nationality distribution input in the `FrontEditor.tsx` component (within `ConfigurationPanel.tsx`) has been changed from a dictionary-based input to an ordered list of entries.
    *   Each entry now features a dropdown to select the nationality and an input for its percentage.
    *   The UI enforces that at least one nationality is always present in a front's distribution.
    *   Backend Pydantic schemas (`patient_generator/schemas_config.py`) were updated to support `List[NationalityDistributionItem]` for `nationality_distribution` in `FrontConfig`.
    *   An Alembic migration (`f5e470301516_update_front_config_nationality_.py`) was created to mark this structural change.
9.  **Injury Distribution UI and Error Handling (Completed - Reverted to simpler model)**:
    *   The injury distribution input in `ConfigurationPanel.tsx` has been reverted to use three fixed input fields for "Battle Injury", "Disease", and "Non-Battle Injury" percentages. This aligns with user feedback for a simpler interface.
    *   Backend Pydantic schemas (`patient_generator/schemas_config.py`) were updated to expect `injury_distribution` as `Dict[str, float]` with these three fixed keys and their sum validated to 100%.
    *   Facility ID submission in `ConfigurationPanel.tsx` was confirmed/corrected to include facility IDs.
    *   A basic error display area in `ConfigurationPanel.tsx` remains to show API validation errors.
10. **Database Schema for Versioning (Completed)**:
    *   After the user resolved Alembic "multiple heads" issues, the migration `2b84a220e9ac_add_version_and_parent_to_config_template.py` was successfully applied. This added the `version` and `parent_config_id` columns to the `configuration_templates` table.
    *   The temporary workaround in `ConfigurationPanel.tsx` for conditionally sending these fields remains suitable.


### Overall Status

Phases 0-3 of the enhanced configurability initiative are complete. The system now has a flexible backend, a comprehensive API, and an initial UI for advanced configuration. The current focus is on Phase 4: hardening the system, addressing technical debt, improving test coverage, UI refinements, and finalizing documentation. The critical Alembic "multiple heads" issue has been resolved by the user, allowing database schema migrations to proceed.

### Known Issues

**Resolved Recently (Prior to New Initiative):**
*   Initial loading errors for the Enhanced Visualization Dashboard.
*   404 errors for visualization API endpoints.
*   500 Internal Server Error for `/api/visualizations/dashboard-data`.
*   React Testing Library `act()` warnings in frontend tests.
*   Implemented generation of multiple primary medical conditions.

**Current Considerations / Known Issues (Focus of Phase 4):**

1.  **Alembic Multiple Heads:** (Resolved by user) The Alembic migration history had diverged, but this has been fixed.
2.  **Missing DB Columns:** (Resolved) The `version` and `parent_config_id` columns have been added to the `configuration_templates` table via migration `2b84a220e9ac`.
3.  **Security - Encryption Salt:** Fixed salt in `formatter.py` has been addressed by implementing PBKDF2 with unique salts per encryption. (Completed)
4.  **Frontend Architecture & Performance:** Bundle sizes and potential duplication in visualization logic.
5.  **Testing Coverage:** API and E2E tests are needed.
6.  **API Key Management:** The current hardcoded API key is a placeholder and needs a secure solution.
7.  **Pylance Type Errors & Warnings (May 2025):**
    *   Most Pylance errors in `patient_generator/database.py` and `patient_generator/formatter.py` have been addressed.
    *   Persistent Pylance errors in `app.py` remain.
    *   "Possibly unbound" warnings for cryptography components in `patient_generator/formatter.py` persist.
    *   Import warnings for `slowapi` and `requests` should be resolved by environment updates.

### Next Steps

The project is currently in **Phase 4: Hardening, Technical Debt, and Final Touches**. With the Alembic issue resolved and critical DB columns added, focus can shift to other Phase 4 tasks, particularly testing and further UI/UX refinements as needed.
