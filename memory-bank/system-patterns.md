# System Patterns

## System Architecture

The Military Medical Exercise Patient Generator employs a modular architecture with a Python-based backend (FastAPI), a PostgreSQL database, and a modern JavaScript/TypeScript frontend (React). This design emphasizes configurability, scalability, and maintainability.

### Architectural Overview

1.  **Frontend Layer (React/TSX & Static HTML)**:
    *   **Main Application Shell (`static/index.html`)**:
        *   Serves as the entry point and hosts the basic UI structure.
        *   Integrates the React-based `ConfigurationPanel.tsx` as a modal for advanced scenario configuration.
        *   Provides basic job submission UI (to be adapted to use new configuration system) and status tracking.
        *   Links to `static/visualizations.html` for detailed graphical dashboards.
        *   Uses Bootstrap for styling (via CDN).
    *   **Advanced Configuration Panel (`ConfigurationPanel.tsx`)**:
        *   A comprehensive React/TSX component for creating, editing, versioning, and managing detailed patient generation scenarios (fronts, facilities, nationalities, injury distributions, etc.).
        *   Communicates with the backend API for CRUD operations on configurations.
        *   Compiled to `static/dist/configuration-panel.js` by `esbuild`.
        *   Includes sub-components like `FrontEditor.tsx` and `FacilityEditor.tsx`.
    *   **Enhanced Visualization Dashboard (`enhanced-visualization-dashboard.tsx`)**:
        *   A React/TSX component hosted by `static/visualizations.html`.
        *   Provides rich, interactive visualizations (charts, graphs) of generated patient data and exercise summaries using Recharts.
        *   Fetches data from backend API endpoints.
        *   Compiled to `static/dist/bundle.js` by `esbuild`.
    *   **Military Medical Dashboard (`MilitaryMedicalDashboard.tsx`)**:
        *   Another specialized React/TSX component for specific operational views or visualizations.
        *   Compiled to `static/dist/military-dashboard.js` by `esbuild`.

2.  **Backend API Layer (FastAPI - `app.py`)**:
    *   **Versioned RESTful API (e.g., `/api/v1/`)**:
        *   Endpoints for full CRUD (Create, Read, Update, Delete) operations on configuration templates (`/configurations/`), including versioning.
        *   Endpoint for validating configurations (`/configurations/validate/`).
        *   Endpoints for patient generation jobs, accepting a `configuration_id` or an ad-hoc configuration object.
        *   Endpoints for job status, results summary, and downloading generated data archives.
        *   Reference data endpoints (e.g., nationalities, condition types).
    *   **Pydantic Models**: Extensively used for request/response validation, data structuring, and defining the shape of configuration objects (see `patient_generator/schemas_config.py`).
    *   **Background Task Processing**: Leverages FastAPI's `BackgroundTasks` for asynchronous patient generation jobs.
    *   **Static File Serving**: Serves the frontend static assets (HTML, JS bundles, CSS).
    *   **API Authentication**: Basic API Key authentication for relevant endpoints.
    *   **Database Interaction**: Uses functions and repositories defined in `patient_generator/database.py` to interact with the PostgreSQL database.

3.  **Core Generation Engine (`patient_generator/`)**:
    *   **`ConfigurationManager` (`patient_generator/config_manager.py`)**:
        *   Central component responsible for loading a specific configuration (identified by ID or provided ad-hoc).
        *   Retrieves configuration details from the PostgreSQL database via `ConfigurationRepository`.
        *   Parses and provides validated configuration parameters (fronts, facilities, nationalities, injury distributions, etc.) to the various generator modules.
    *   **`PatientGeneratorApp` (`patient_generator/app.py` module, distinct from FastAPI `app.py`)**:
        *   Orchestrates the patient generation process.
        *   Instantiated with a `ConfigurationManager` instance.
        *   Coordinates calls to specialized generator modules (`flow_simulator.py`, `demographics.py`, `medical.py`, `fhir_generator.py`, `formatter.py`).
    *   **Specialized Generator Modules**:
        *   `flow_simulator.py`: Simulates patient flow based on dynamic configurations.
        *   `demographics.py` & `nationality_data.py`: Generate demographic data, now supported by `NationalityDataProvider` which can source data from `demographics.json` or potentially other sources.
        *   `medical.py`: Generates medical conditions based on configured distributions.
        *   `fhir_generator.py`: Converts patient objects to HL7 FHIR R4 bundles.
        *   `formatter.py`: Handles output formatting (JSON, XML), compression, and encryption.

4.  **Database Layer (PostgreSQL & Alembic)**:
    *   **PostgreSQL**: The primary relational database for storing:
        *   Patient generation job metadata (status, progress, links to results).
        *   Detailed configuration templates, including their versions and relationships (e.g., fronts, facilities, nationality setups, medical flow parameters, injury distributions).
    *   **Alembic**: Manages all database schema migrations for PostgreSQL, ensuring controlled evolution of the database structure. Migration scripts are located in `alembic_migrations/versions/`.
    *   **SQLAlchemy**: Used as the ORM for defining database models (see `patient_generator/models_db.py`) and for some direct database interactions. Alembic also leverages SQLAlchemy.
    *   **`patient_generator/database.py`**: Contains database interaction logic, including:
        *   `ConfigurationRepository`: Handles all CRUD operations for configuration templates and their components in PostgreSQL.
        *   Functions for managing job data (creating, updating status, storing results).
    *   Connection pooling is managed by FastAPI/SQLAlchemy for efficient database access.

5.  **Output Handling (`patient_generator/formatter.py`)**:
    *   Supports multiple output formats (JSON, XML).
    *   Handles data compression (gzip) and encryption (AES-256-GCM with unique salts via PBKDF2).
    *   Prepares data for NDEF/NFC smart tag deployment.

### Key Design Patterns

1.  **Repository Pattern**:
    *   Implemented in `patient_generator/database.py` (e.g., `ConfigurationRepository`) to abstract data persistence logic for configuration templates and job data, promoting separation of concerns between business logic and data access.
2.  **Strategy Pattern**:
    *   Implicitly used in generator modules where different configurations can lead to different generation strategies (e.g., `PatientFlowSimulator` behavior changes based on facility parameters).
3.  **Factory Pattern**:
    *   Used in demographic and medical condition generators to create patient attributes based on parameters.
4.  **Builder Pattern**:
    *   The `FHIRBundleGenerator` builds complex FHIR bundle data structures by assembling components.
5.  **Command Pattern (via BackgroundTasks)**:
    *   Patient generation operations are encapsulated as background tasks managed by FastAPI, allowing them to be queued, executed asynchronously, and monitored.
6.  **Facade Pattern**:
    *   `PatientGeneratorApp` provides a simplified interface to the complex underlying generation system.
7.  **Dependency Injection**:
    *   FastAPI uses this extensively for request handling, background tasks, and managing dependencies like database sessions. `ConfigurationManager` is injected into `PatientGeneratorApp`.

### Component Relationships & Data Flow

1.  **Configuration Phase**:
    *   User interacts with `ConfigurationPanel.tsx` (UI) or uses the Python SDK (`patient_generator_sdk.py`) / API directly.
    *   A detailed scenario configuration (defining fronts, facilities, nationalities, injury types, etc.) is created, edited, or selected.
    *   This configuration object is sent to the backend API (e.g., `POST /api/v1/configurations/`).
    *   The API, using `ConfigurationRepository` (in `patient_generator/database.py`), saves or retrieves the configuration from the PostgreSQL database. Configurations can be validated, versioned, and listed.

2.  **Generation Phase**:
    *   User initiates a generation job via UI, API, or SDK, providing a `configuration_id` (referencing a stored configuration) or an ad-hoc configuration object.
    *   The backend API (e.g., `POST /api/v1/generate/`) receives the request and enqueues a background task.
    *   The background task instantiates `PatientGeneratorApp`.
    *   `PatientGeneratorApp` initializes `ConfigurationManager` with the `configuration_id` or ad-hoc data.
    *   `ConfigurationManager` loads the full, parsed configuration details from the database (if `configuration_id` was used) or uses the provided ad-hoc data.
    *   `ConfigurationManager` provides specific parameters from the loaded scenario to:
        *   `PatientFlowSimulator`: To set up facility chains, patient numbers per front, casualty rates, etc.
        *   `DemographicsGenerator` (with `NationalityDataProvider`): To define nationality mixes and data sources.
        *   `MedicalConditionGenerator`: To set injury distributions and severities.
    *   These generator modules create patient data according to the loaded configuration.
    *   `FHIRGenerator` converts patient objects to FHIR bundles.
    *   `OutputFormatter` produces files in requested formats (JSON, XML), with optional compression/encryption.

3.  **Results & Download**:
    *   Generated files are stored (e.g., in a designated output directory or cloud storage, path recorded in DB).
    *   Job status, progress, and summary statistics are updated in the PostgreSQL database and accessible via API.
    *   User downloads the completed files (typically as a ZIP archive) via UI or API.

### Extensibility Points

The architecture is designed for extensibility:
*   **Dynamic Configurations**: New scenarios (fronts, facilities, nationalities, medical flows, injury patterns) can be defined and stored in the database via the API or UI without code changes to the core engine.
*   **Nationality Support**: Adding new NATO nations involves updating the `demographics.json` (or future DB table for demographics data) and ensuring `NationalityDataProvider` and `DemographicsGenerator` can handle them. The system aims for all 32 NATO nations.
*   **Medical Conditions/Treatments**: New condition types, treatments, or patterns can be incorporated into the configuration data.
*   **API Expansion**: New API endpoints can be added to expose more granular control, new data entities, or new functionalities.
*   **Output Formats**: New formatters can be added to `formatter.py` and integrated.
*   **Frontend Components**: New React components can be added for new UI features or dashboards.

### Identified Technical Debt Areas (Refer to `active-context.md` and `open-tickets.md` for current status)

1.  **Memory Management (Backend)**:
    *   While improved, generating extremely large FHIR bundles or handling massive patient lists in memory before writing to disk can still be a concern. Opportunities for streaming processing.
    *   *Status: Partially addressed in Phase 1, ongoing monitoring. TD-002 (Bundle Size Optimization) is related to frontend assets.*

2.  **Error Handling Standardization**:
    *   Ensuring consistent, user-friendly error reporting from API to frontend, and robust error handling within backend processes.
    *   *Status: Ongoing improvement throughout development.*

3.  **Frontend Architecture & Performance**:
    *   **Bundle Size Optimization (TD-002 / Task 4.1.3)**: JavaScript bundles for React components can become large.
    *   **Visualization Logic Consolidation (TD-001 / Task 4.1.2 - Completed)**: Ensured `static/index.html` links to the React-based `ExerciseDashboard` for graphical charts.
    *   Potential for further state management refinement in complex React components.

4.  **Testing Coverage**:
    *   Need for expanded API integration tests (TST-001 / Task 4.2.1) and End-to-End (E2E) tests (TST-002 / Task 4.2.2).
    *   Reviewing and updating existing Python unit tests for compatibility with refactored code.

5.  **Database Performance & Optimization**:
    *   Ensuring efficient queries, especially for complex configuration lookups or large job tables.
    *   Optimizing Alembic migrations for large datasets if schema changes affect existing data.

6.  **Docker Optimization (TD-003 / Task 4.1.4)**:
    *   Implementing multi-stage builds for smaller, more secure container images.
    *   Reviewing Docker Compose configurations for production readiness.

7.  **API Key Management (GEN-001)**:
    *   Current API key mechanism might be basic; needs a more robust solution for production.
