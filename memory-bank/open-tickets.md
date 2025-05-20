__Ticket ID:__ TD-001 (Corresponds to Task 4.1.2) __Title:__ Frontend Architecture Consolidation: Unify Visualization Logic __Epic:__ 4.1 Address Remaining Technical Debt __Description:__ The current frontend has visualization logic present in both the older static JavaScript (`static/index.html` using Chart.js) and the newer React-based `ExerciseDashboard` component (`enhanced-visualization-dashboard.tsx` using Recharts). This task aims to consolidate visualization efforts, likely by migrating or ensuring all key visualizations are handled by the React components to reduce redundancy and improve maintainability. __Acceptance Criteria:__

1. Analyze visualization capabilities of the legacy `static/index.html` (Chart.js) and the `ExerciseDashboard` React component.
2. Identify any unique or critical visualizations in the legacy view that are not present or adequately represented in the React dashboard.
3. If gaps exist, implement the missing/required visualizations within the `ExerciseDashboard` React component or a new dedicated React visualization component.
4. Ensure the React-based visualizations are configurable and can display data relevant to the new dynamic configuration system.
5. Update `static/visualizations.html` to be the primary access point for comprehensive visualizations, potentially deprecating or simplifying visualizations in `static/index.html`.
6. Relevant Memory Bank documents (e.g., `system-patterns.md`, `tech-context.md`) are updated to reflect the consolidated architecture.
7. Code is reviewed and merged into the `develop` branch.

---

__Ticket ID:__ TD-002 (Corresponds to Task 4.1.3) __Title:__ Frontend Bundle Size Optimization __Epic:__ 4.1 Address Remaining Technical Debt __Description:__ The JavaScript bundles for React components (`enhanced-visualization-dashboard.tsx`, `ConfigurationPanel.tsx`, `MilitaryMedicalDashboard.tsx`) may be large, impacting load times. This task involves investigating and implementing optimization techniques such as code splitting, lazy loading, and externalizing common libraries. __Acceptance Criteria:__

1. Analyze the current bundle sizes for `static/dist/bundle.js`, `static/dist/configuration-panel.js`, and `static/dist/military-dashboard.js` using tools like `source-map-explorer` or `webpack-bundle-analyzer` (if applicable to `esbuild` outputs, or similar alternatives).

2. Identify opportunities for optimization:

   - Code splitting (e.g., per route or component).
   - Lazy loading non-critical components.
   - Externalizing large common dependencies (e.g., React, Recharts) to be loaded via CDN or as separate chunks, if not already optimal.
   - Tree shaking and dead code elimination (ensure `esbuild` is configured optimally).

3. Implement chosen optimization techniques for all major React components.

4. Verify a measurable reduction in initial load bundle sizes.

5. Ensure all frontend functionalities remain intact after optimization.

6. Document the optimization strategies applied in `memory-bank/tech-context.md`.

7. Code is reviewed and merged into the `develop` branch.

---

__Ticket ID:__ TD-003 (Corresponds to Task 4.1.4) __Title:__ Docker Optimization: Multi-Stage Builds and Security Review __Epic:__ 4.1 Address Remaining Technical Debt __Description:__ Optimize the Docker build process and review container security. This includes implementing multi-stage builds for the application Docker image to reduce its size and attack surface, and reviewing general Docker security best practices. __Acceptance Criteria:__

1. Refactor the main `Dockerfile` to use multi-stage builds, separating build-time dependencies from runtime dependencies.
2. Ensure the final Docker image size for the `app` service is significantly reduced.
3. Verify the application runs correctly using the optimized Docker image.
4. Review Docker Compose files (`docker-compose.dev.yml`, `docker-compose.prod.yml`, etc.) for any potential optimizations or security enhancements (e.g., non-root users, read-only filesystems where appropriate).
5. Document changes to the Docker setup in `DOCKER_DEPLOYMENT.md` and `memory-bank/tech-context.md`.
6. Code is reviewed and merged into the `develop` branch.

---

__Ticket ID:__ TST-001 (Corresponds to Task 4.2.1) __Title:__ API Integration Tests __Epic:__ 4.2 Testing Expansion __Description:__ Develop a suite of integration tests for the backend RESTful API (`/api/v1/`). These tests should cover CRUD operations for configurations, validation, patient generation job submission, status checking, and results retrieval. __Acceptance Criteria:__

1. Set up a testing environment/framework suitable for API integration tests (e.g., using Python's `requests` library with `unittest` or `pytest`).

2. Tests should run against a live (test instance) API, potentially interacting with a test database.

3. Cover key API endpoints:

   - `POST, GET, PUT, DELETE /api/v1/configurations/`
   - `POST /api/v1/configurations/validate/`
   - `POST /api/v1/generate/`
   - `GET /api/v1/jobs/{job_id}/status`
   - `GET /api/v1/jobs/{job_id}/results`
   - `GET /api/v1/reference/nationalities`
   - `GET /api/v1/reference/condition_types`

4. Tests should validate request/response schemas, status codes, and basic data integrity.

5. Tests should cover both successful scenarios and common error conditions (e.g., invalid input, unauthorized access if applicable).

6. Achieve a target code coverage for the API endpoint handlers (e.g., >70%).

7. Integrate tests into a CI/CD pipeline if one exists, or ensure they can be run easily by developers.

8. Document how to run API integration tests in `README.md` or a dedicated testing guide.

9. Code is reviewed and merged into the `develop` branch.

---

__Ticket ID:__ TST-002 (Corresponds to Task 4.2.2) __Title:__ End-to-End (E2E) Tests for Key User Flows __Epic:__ 4.2 Testing Expansion __Description:__ Implement End-to-End tests for critical user flows, such as creating a new configuration scenario via the `ConfigurationPanel.tsx`, saving it, initiating a patient generation job with it, and verifying basic output or job completion. __Acceptance Criteria:__

1. Select an E2E testing framework (e.g., Selenium, Playwright, Cypress).

2. Set up the chosen framework and integrate it into the project.

3. Identify 2-3 critical user flows to be covered by E2E tests. Examples:

   - Full scenario creation: Open `ConfigurationPanel`, define fronts, facilities, nationalities, save configuration.
   - Generation from saved config: Load a saved configuration, initiate generation, check for job completion status.
   - Basic generation from main UI (once adapted to new config system).

4. Implement E2E tests for the selected flows.

5. Tests should run in a browser and interact with the UI as a user would.

6. Ensure tests are stable and provide reliable results.

7. Document how to run E2E tests in `README.md` or a dedicated testing guide.

8. Code is reviewed and merged into the `develop` branch.

---

__Ticket ID:__ GEN-001 (Corresponds to "API Key Management" from Known Issues) __Title:__ Implement Secure API Key Management __Epic:__ General Hardening (Implied from Phase 4 goals & Known Issues) __Description:__ The current API key is a placeholder and potentially hardcoded or easily discoverable. This task is to implement a more secure way to manage and use API keys for accessing protected API endpoints. __Acceptance Criteria:__

1. Research and select a suitable method for API key management (e.g., environment variables, configuration files not committed to VCS, a secrets management system if available).
2. Implement the chosen solution for storing and accessing the API key(s) by the FastAPI backend.
3. Update the API authentication logic in `app.py` to use the new secure key retrieval method.
4. Ensure the Python SDK (`patient_generator_sdk.py`) and any example scripts are updated to demonstrate how to provide the API key securely (e.g., via parameter, environment variable).
5. Document the new API key setup and usage for developers and administrators in `README.md` and `memory-bank/tech-context.md`.
6. Remove any hardcoded placeholder API keys from the codebase.
7. Code is reviewed and merged into the `develop` branch.

---

__Ticket ID:__ LINT-001 __Title:__ Address Pylance Static Analysis Errors __Epic:__ General Hardening __Description:__ A number of Pylance static analysis errors have been identified in Python files (`schemas_config.py`, `database.py`, `flow_simulator.py`). These errors relate to type mismatches, missing default values for overridden fields, and unsupported operations. This task is to investigate and resolve these errors to improve code quality and type safety. __Acceptance Criteria:__

1. All Pylance errors listed in the workspace diagnostics (dated May 20, 2025, 3:55 PM) are resolved in `patient_generator/schemas_config.py`.
2. All Pylance errors listed in the workspace diagnostics are resolved in `patient_generator/database.py`.
3. All Pylance errors listed in the workspace diagnostics are resolved in `patient_generator/flow_simulator.py`.
4. The application remains functionally equivalent after the changes.
5. Code changes are reviewed and merged into the `develop` branch.
6. Relevant Memory Bank documents are updated if any significant changes to logic or types are made.

---

__Ticket ID:__ LINT-002 __Title:__ Alembic Migration - Specify Constraint Name in Downgrade __Epic:__ General Hardening __Description:__ The `downgrade` function in migration `2b84a220e9ac` uses `op.drop_constraint(None, ...)`. This causes a Pylance error because the constraint name should be specified. The auto-generated foreign key constraint name needs to be identified and used in the `drop_constraint` call. __Acceptance Criteria:__

1. Identify the auto-generated name for the foreign key constraint created in the `upgrade` function of migration `2b84a220e9ac`.
2. Update the `op.drop_constraint` call in the `downgrade` function of `2b84a220e9ac` to use the identified constraint name.
3. The Pylance error on line 33 of `alembic_migrations/versions/2b84a220e9ac_add_version_and_parent_to_config_.py` is resolved.
4. Code is reviewed and merged into the `develop` branch.
