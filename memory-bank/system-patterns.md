# System Patterns

## System Architecture

The Military Medical Exercise Patient Generator follows a modular architecture with clear separation of concerns. It consists of a Python backend with a web interface frontend, organized around core generation components that work together to produce realistic patient data.

### Architectural Overview

1. **Frontend Layer**:
   - **Main Application (`static/index.html`)**:
     - Single-page HTML/JavaScript application for job submission and basic status tracking.
     - Uses Bootstrap for styling.
     - AJAX communication with the backend API.
     - Links to the Advanced Visualization Dashboard for detailed per-job visualizations.
   - **Enhanced Visualization Dashboard (`static/visualizations.html`)**:
     - Primary access point for comprehensive exercise visualizations.
     - Hosts the `ExerciseDashboard` React component (`enhanced-visualization-dashboard.tsx`).
     - Compiled to `static/dist/bundle.js`.
     - Uses React, Recharts, Lucide-React.
   - **Advanced Configuration Panel (`ConfigurationPanel.tsx`)**:
     - React component integrated into `static/index.html` as a modal.
     - Allows detailed creation, editing, and management of generation scenarios.
     - Compiled to `static/dist/configuration-panel.js`.
   - **Military Medical Dashboard (`MilitaryMedicalDashboard.tsx`)**:
     - Another React TSX component, likely for specific visualizations or operational views.
     - Compiled to its own bundle (e.g., `static/dist/military-dashboard.js`).

2. **Backend API Layer (FastAPI - `app.py`)**:
   - **Versioned RESTful API (e.g., `/api/v1/`)**:
     - Endpoints for CRUD operations on configuration templates (`/configurations/`).
     - Endpoint for validating configurations (`/configurations/validate/`).
     - Endpoints for patient generation jobs, now accepting `configuration_id` or ad-hoc configurations.
     - Endpoints for job status, results, and downloading generated data.
     - Reference data endpoints (nationalities, condition types).
   - **Pydantic Models**: Used extensively for request/response validation and data structuring.
   - Background task processing for generation jobs.
   - Static file serving for frontend assets.
   - API Authentication (e.g., API Key) and Rate Limiting.

3. **Core Generation Engine (`patient_generator/`)**:
   - **`ConfigurationManager` (`patient_generator/config_manager.py`)**: Central component for loading, interpreting, and providing specific configuration details (fronts, facilities, nationalities, injury distributions, etc.) to the various generator modules.
   - **`PatientGeneratorApp` (`patient_generator/app.py` module, distinct from FastAPI `app.py`)**: Orchestrates generation, now heavily reliant on `ConfigurationManager`.
   - Specialized generator modules (`flow_simulator.py`, `demographics.py`, `medical.py`) are now driven by configurations supplied by `ConfigurationManager`.

4. **Database Layer (PostgreSQL)**:
    - **PostgreSQL**: Backend database for storing:
        - Patient generation job metadata.
        - Configuration templates (fronts, facilities, nationalities, medical flows, injury distributions, etc.).
    - **Alembic**: Manages database schema migrations for PostgreSQL.
    - **`patient_generator/database.py`**: Contains database interaction logic, including:
        - `ConfigurationRepository` for CRUD operations on configuration data.
        - Functions for job data management.
    - Connection pooling for efficient database access.
    - SQLAlchemy might be used for ORM capabilities or with Alembic.

5. **Output Handling**:
   - Multiple format support (JSON, XML)
   - Compression and encryption options
   - NDEF formatting for NFC compatibility

### Key Design Patterns

1. **Factory Pattern**:
   - Used in the demographic and medical condition generators to create patient attributes based on parameters like nationality and injury type.

2. **Strategy Pattern**:
   - Flow simulator uses different strategies for patient progression based on current status and injury type.

3. **Builder Pattern**:
   - FHIR bundle generator builds complex data structures by assembling components from different sources.

4. **Command Pattern**:
   - Generator operations are encapsulated as background tasks that can be queued and monitored.

5. **Observer Pattern**:
   - Progress reporting through callbacks allows the UI to monitor generation progress.

6. **Facade Pattern**:
   - `PatientGeneratorApp` provides a simplified interface to the complex generation system.

7. **Singleton Pattern**:
   - May still be used in `patient_generator/database.py` for managing the PostgreSQL connection pool.

8. **Repository Pattern**:
   - Implemented in `patient_generator/database.py` (e.g., `ConfigurationRepository`) to abstract data persistence logic for configuration templates and other database entities.

### Component Relationships

1.  **`ConfigurationPanel.tsx` / API / SDK**: User defines/selects a configuration.
2.  **FastAPI `app.py` (API Layer)**:
    *   Receives requests for configuration management or patient generation.
    *   Interacts with `ConfigurationRepository` (via `patient_generator/database.py`) to save/load configurations from PostgreSQL.
    *   For generation, passes `configuration_id` or ad-hoc config to `PatientGeneratorApp`.
3.  **`PatientGeneratorApp` (`patient_generator/app.py` module)**:
    *   Orchestrates the generation process.
    *   Initializes and uses `ConfigurationManager`.
4.  **`ConfigurationManager` (`patient_generator/config_manager.py`)**:
    *   Loads the specified configuration (from DB via `ConfigurationRepository` or uses ad-hoc).
    *   Provides parsed and validated configuration details to other generator components.
5.  **`ConfigurationRepository` (`patient_generator/database.py`)**:
    *   Handles all database interactions for configuration templates (CRUD operations against PostgreSQL).
6.  **`PatientFlowSimulator` (`flow_simulator.py`)**:
    *   Receives scenario parameters (facility chain, casualty rates, etc.) from `ConfigurationManager`.
    *   Simulates patient flow based on these dynamic configurations.
7.  **`DemographicsGenerator` (`demographics.py`)**:
    *   Receives nationality lists and distributions from `ConfigurationManager`.
    *   Generates demographic data accordingly.
8.  **`MedicalConditionGenerator` (`medical.py`)**:
    *   Receives injury type distributions and severity parameters from `ConfigurationManager`.
    *   Generates medical conditions.
9.  **`FHIRGenerator` (`fhir_generator.py`)**:
    *   Converts patient objects (now with dynamically generated attributes) to HL7 FHIR R4 bundles.
10. **`OutputFormatter` (`formatter.py`)**:
    *   Formats data (JSON, XML), handles compression/encryption.
11. **`Patient` Class (`patient.py`)**:
    *   Core data model, largely unchanged but populated based on dynamic configurations.

### Data Flow

1.  **Configuration Phase**:
    *   User interacts with `ConfigurationPanel.tsx` (UI) or uses the Python SDK/API.
    *   A detailed scenario configuration (fronts, facilities, nationalities, injury types, etc.) is created or selected.
    *   This configuration is sent to the backend API (`/api/v1/configurations/`).
    *   The API, using `ConfigurationRepository`, saves or retrieves the configuration from the PostgreSQL database. Configurations can be validated, versioned (conceptually), and listed.
2.  **Generation Phase**:
    *   User initiates a generation job via UI or API/SDK, providing a `configuration_id` or an ad-hoc configuration object.
    *   The backend API (`/api/generate/`) receives the request and starts a background task.
    *   `PatientGeneratorApp` is instantiated.
    *   `PatientGeneratorApp` uses `ConfigurationManager` to load and parse the specified scenario configuration (from DB or ad-hoc).
    *   `ConfigurationManager` provides specific parameters to:
        *   `PatientFlowSimulator`: To set up facility chains, patient numbers per front, etc.
        *   `DemographicsGenerator`: To define nationality mixes and data sources.
        *   `MedicalConditionGenerator`: To set injury distributions and severities.
    *   These generators create patient data according to the loaded configuration.
    *   `FHIRGenerator` converts patient objects to FHIR bundles.
    *   `OutputFormatter` produces files in requested formats (JSON, XML), with optional compression/encryption.
3.  **Results & Download**:
    *   Generated files are stored.
    *   Job status and summary statistics are updated (and accessible via API).
    *   User downloads the completed files via UI or API.

### Concurrency Model

- Background tasks for long-running generation jobs
- Job status tracking for concurrent users
- Progress reporting via callbacks

### Security Considerations

- Optional AES-256-GCM encryption for sensitive data
- Password-based key derivation
- Temporary file management for downloads

### Extensibility Points

The new architecture significantly enhances extensibility:
-   **Dynamic Configurations**: New scenarios (fronts, facilities, nationalities, medical flows, injury patterns) can be defined and stored in the database via the API or UI without code changes.
-   **Nationality Support**: Adding new NATO nations involves updating the `demographics.json` (or future DB table) and ensuring `DemographicsGenerator` can handle them. The system aims for all 32.
-   **Medical Conditions**: New condition types or patterns can be incorporated into the configuration.
-   **API Expansion**: New API endpoints can be added to expose more granular control or data.
-   **Output Formats**: Still possible to add new formatters in `formatter.py`.

### Identified Technical Debt Areas

Based on a recent technical review, the following areas have been identified for potential improvement:

1.  **Memory Management**:
    *   In-memory storage of large patient datasets (e.g., `jobs[job_id]["patients_data"]` in `app.py`, FHIR bundle generation) can lead to issues with very large generation jobs.
    *   Opportunities for streaming processing and disk-based serialization.

2.  **Error Handling**:
    *   Inconsistent error handling approaches across backend (Python) and frontend (React/TSX) components.
    *   Need for standardized custom exceptions, structured logging, and robust error recovery mechanisms (e.g., React Error Boundaries).

3.  **Frontend Architecture**:
    *   Mix of traditional JavaScript (`static/index.html` for basic job submission) and modern React/TypeScript (for `enhanced-visualization-dashboard.tsx`, `ConfigurationPanel.tsx`, etc.).
    *   Visualization Consolidation: `static/index.html` provides basic job status and textual summaries, and links to `static/visualizations.html` (hosting the `ExerciseDashboard` React component) for comprehensive graphical visualizations. This ensures graphical chart rendering is centralized in React components using Recharts, avoiding duplication of charting libraries or logic.
    *   Large bundle size for the enhanced dashboard and other React components remains a concern (addressed by TD-002).
    *   Inconsistent state management in the React application (if applicable beyond current components, to be reviewed).

4.  **Configuration Management (Now an Architectural Pillar)**:
    *   The new system centralizes configuration via the `ConfigurationManager`, API, and PostgreSQL database.
    *   Ongoing considerations include UI/UX for managing complex configurations, versioning strategies, and ensuring consistency between UI, API, and backend logic.

5.  **Testing Coverage**:
    *   Uneven test coverage, particularly for some frontend components and API integration aspects.
    *   Need for expanded unit, integration, and potentially end-to-end tests.

6.  **Database Implementation (PostgreSQL & Alembic)**:
    *   The migration to PostgreSQL and use of Alembic addresses previous schema management and some SQLite limitations.
    *   Ensuring efficient connection pooling for PostgreSQL is important.
    *   Parameterized queries remain crucial to prevent SQL injection.
    *   Optimizing database queries for performance with potentially complex configuration data.

7.  **Docker Optimization**:
    *   Container images could be large due to unnecessary dependencies.
    *   Opportunity for multi-stage builds and optimized Docker Compose configurations for different environments (dev, prod).
    *   Review container security best practices.
