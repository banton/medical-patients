# Military Medical Exercise Patient Generator

A web-based application to generate realistic dummy patient data for military medical exercises. It features a highly configurable system supporting dynamic scenario definitions (multiple treatment facilities, all 32 NATO nations, varied injury types), a PostgreSQL backend, a comprehensive RESTful API, a Python SDK, and an advanced React-based configuration interface, all following NATO medical standards.

## Overview

This application generates simulated patient data for military medical exercises. It models patient flow through dynamically configurable medical treatment facility chains (e.g., POI, R1, R2, R3, R4) with realistic progression statistics. The system is built upon a PostgreSQL database, managed with Alembic migrations, and offers extensive control via a RESTful API and a Python SDK. The generated data complies with international medical data standards including:

- Minimal Core Medical Data (AMedP-8.1)
- Medical Warning tag (AMedP-8.8)
- International Patient Summary ISO27269:2021
- HL7 FHIR R4 formatted bundles

## Features

- **Highly Configurable Scenarios**: Define and manage complex exercise scenarios including:
    - Dynamic medical facility chains (e.g., POI, R1-R4) with custom parameters.
    - Multiple configurable fronts with specific casualty rates.
    - Detailed nationality distributions per front (goal: all 32 NATO nations).
    - Overall injury type distributions (Disease, Non-Battle Injury, Battle Injury).
- **Advanced Configuration Panel**: A React-based UI (`ConfigurationPanel.tsx`) for creating, editing, saving, and loading scenario templates.
- **Database-Backed Configurations**: Scenarios are stored and versioned in a PostgreSQL database.
- **Comprehensive RESTful API**: Programmatic control over configuration management and patient generation.
- **Python SDK**: Simplifies interaction with the API for automation and integration.
- **Realistic Patient Data**:
    - Demographics generation for a wide range of nationalities.
    - Medical conditions using SNOMED CT codes.
    - HL7 FHIR R4 compliant bundles.
- **Multiple Output Formats**: JSON, XML, with NDEF for NFC tags.
- **Data Security Options**: gzip compression and AES-256-GCM encryption (using unique salts per encryption).
- **Dockerized Development Environment**: Easy setup and consistent environment using Docker and `start-dev.sh` script.
- **Database Schema Management**: Alembic for robust PostgreSQL schema migrations.
- **Enhanced Visualization Dashboard**: React-based dashboard for visualizing generated data.

## Architecture

The application features a modular architecture:

1.  **Frontend Layer**:
    *   Main application shell (`static/index.html`).
    *   Advanced Configuration Panel (`ConfigurationPanel.tsx`): React component for scenario design.
    *   Enhanced Visualization Dashboard (`enhanced-visualization-dashboard.tsx`): React component for data display.
    *   Military Medical Dashboard (`MilitaryMedicalDashboard.tsx`): Additional specialized React component.
    *   Bundled using `esbuild`.
2.  **Backend API Layer (FastAPI)**:
    *   Versioned RESTful API (`/api/v1/`) for configurations, generation, job status, and reference data.
    *   Uses Pydantic for data validation.
3.  **Core Generation Engine (`patient_generator/`)**:
    *   `ConfigurationManager`: Loads and provides scenario configurations.
    *   `PatientGeneratorApp`: Orchestrates patient generation based on loaded configurations.
    *   Specialized generators (flow simulation, demographics, medical conditions) driven by `ConfigurationManager`.
4.  **Database Layer (PostgreSQL)**:
    *   Stores configuration templates and job metadata.
    *   `ConfigurationRepository` handles DB interactions for configurations.
    *   Alembic manages schema migrations.
5.  **Python SDK (`patient_generator_sdk.py`)**:
    *   Client library for easy interaction with the backend API.

## Getting Started (Development Environment)

The recommended way to set up and run the development environment is using Docker and the provided helper script.

### Prerequisites

-   Git
-   Docker Desktop (or Docker Engine + Docker Compose)
-   Node.js and npm (for frontend development, if making changes to React components)
-   Python 3.8+ (if running backend components outside Docker, not recommended for primary dev)

### Setup & Running

1.  **Clone the repository**:
    ```bash
    git clone <repository_url>
    cd military-patient-generator
    ```

2.  **Ensure `start-dev.sh` is executable**:
    ```bash
    chmod +x start-dev.sh
    ```

3.  **Run the development environment startup script**:
    ```bash
    ./start-dev.sh
    ```
    This script will:
    *   Install/update frontend Node.js dependencies (`npm install`).
    *   Build all frontend React components (`npm run build:all-frontend`).
    *   Start the Docker services defined in `docker-compose.dev.yml` (FastAPI application, PostgreSQL database) in detached mode.
    *   Wait for the application service to be healthy.
    *   Apply any pending database migrations using Alembic.

4.  **Access the application**:
    *   Main UI (including Advanced Configuration Panel): `http://localhost:8000/static/index.html`
    *   Enhanced Visualization Dashboard: `http://localhost:8000/static/visualizations.html`
    *   API (e.g., Swagger docs): `http://localhost:8000/docs`

For more details on Docker configurations for different environments (production, Traefik), see [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md).

## Usage

The application offers multiple ways to define scenarios and generate patient data:

1.  **Advanced Configuration Panel (Web UI)**:
    *   Access via `http://localhost:8000/static/index.html`.
    *   Use the "Advanced Configuration" modal to:
        *   Create new scenario templates.
        *   Load, edit, and save existing templates.
        *   Define fronts, facility chains, nationality distributions, injury patterns, and other parameters.
    *   Once a configuration is active, use the main UI to initiate patient generation.

2.  **Python SDK (`patient_generator_sdk.py`)**:
    *   Provides a `PatientGeneratorClient` class to interact with the API.
    *   Allows programmatic creation, retrieval, and management of configuration templates.
    *   Enables scripting of patient generation jobs.
    *   See examples within the SDK file and future documentation.

3.  **Direct API Interaction**:
    *   The RESTful API (Swagger docs at `http://localhost:8000/docs`) can be used directly with any HTTP client.

Generated data can be used for:
-   Importing into exercise management systems.
-   Deploying to NFC smarttags.
-   Medical treatment facility simulations.

## Data Structure and Configuration

Patient data adheres to HL7 FHIR R4 standards, including Patient, Condition, Observation, and Procedure resources.

Scenario configurations are complex objects managed via the API and stored in the database. They define all aspects of the generation, such as:
-   Overall exercise parameters (total patients, base date).
-   Front definitions (name, casualty rates, nationality mix).
-   Facility definitions (type, capabilities, progression statistics) arranged in chains.
-   Injury distributions (battle, non-battle, disease percentages).

Refer to the API documentation (`/docs`) or the `ConfigurationPanel.tsx` UI for details on the structure of configuration templates.

## Security

-   **Data Encryption**: Supports AES-256-GCM encryption for output files. Unique salts are generated for each encryption using PBKDF2 with a user-provided password.
-   **API Security**: Basic API key authentication is implemented for configuration management endpoints. (Note: The default API key is for development and should be changed for production).

## Project Structure

A simplified overview of the project structure:

```
military-patient-generator/
├── .clinerules
├── .dockerignore
├── .gitignore
├── alembic.ini
├── app.py                              # Main FastAPI application
├── ConfigurationPanel.tsx              # React component for advanced config UI
├── Dockerfile
├── docker-compose.dev.yml              # Docker Compose for development
├── enhanced-visualization-dashboard.tsx
├── jest.config.js
├── package.json                        # Frontend dependencies and scripts
├── patient_generator_sdk.py            # Python SDK
├── README.md
├── requirements.txt                    # Python dependencies
├── start-dev.sh                        # Dev environment startup script
├── tsconfig.json
│
├── alembic_migrations/                 # Alembic migration scripts
│   └── versions/
│
├── patient_generator/                  # Core Python generation module
│   ├── __init__.py
│   ├── app.py                          # PatientGeneratorApp class
│   ├── config_manager.py
│   ├── database.py                     # PostgreSQL interaction, ConfigurationRepository
│   ├── models_db.py                    # SQLAlchemy DB models
│   ├── schemas_config.py               # Pydantic schemas for configurations
│   └── ... (other generator modules)
│
├── static/                             # Static web files
│   ├── index.html
│   ├── visualizations.html
│   └── dist/                           # Compiled JS bundles
│       ├── bundle.js
│       └── configuration-panel.js
│
└── ... (other configuration files, test files, etc.)
```
For a more detailed structure, see `memory-bank/tech-context.md`.

## Standards Compliance

This generator creates data compliant with:
- HL7 FHIR R4 standard
- SNOMED CT for conditions, procedures and other medical items
- LOINC for lab values and observations
- ISO3166 alpha-3 for country codes
- ISO8601 for dates and times
- NDEF format specifications for NFC compatibility

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Git Branching Strategy

This project follows a structured Git branching model:

-   **`main`**: This branch represents the most stable, production-ready version of the code. Only tested and approved code from the `develop` branch is merged into `main`, typically during a release. Direct commits to `main` are discouraged.
-   **`develop`**: This is the primary integration branch for new features and ongoing development. All feature branches are created from `develop` and merged back into `develop` upon completion and review. Nightly builds or CI/CD processes may run against this branch.
-   **Feature Branches (`feature/<epic-name>/<task-name>`)**:
    *   When starting a new feature or task (e.g., as defined in `memory-bank/active-context.md`), create a new branch from `develop`.
    *   Use a descriptive naming convention, for example: `feature/config-api/add-crud-endpoints` or `feature/db-migration/setup-postgres`.
    *   Commit work regularly to your feature branch.
    *   Once the feature is complete, tested, and reviewed, create a Pull Request to merge it into `develop`.
-   **Release Branches (`release/vX.Y.Z`)**:
    *   When `develop` has accumulated enough features for a new release, a `release` branch is created from `develop`.
    *   This branch is used for final testing, bug fixes, and preparing release-specific documentation. No new features are added here.
    *   Once ready, the `release` branch is merged into `main` (and tagged with the version number, e.g., `v1.2.0`) and also back into `develop` to ensure any fixes made during the release process are incorporated into future development.
-   **Hotfix Branches (`hotfix/<issue-id>` or `hotfix/<description>`)**:
    *   If a critical bug is found in `main` (production), a `hotfix` branch is created directly from `main`.
    *   The fix is applied and tested on this branch.
    *   Once complete, the `hotfix` branch is merged into `main` (and tagged with an incremented patch version, e.g., `v1.2.1`) and also into `develop` to ensure the fix is included in ongoing development.

This strategy helps maintain a clean and stable `main` branch while allowing for parallel development and organized integration of new features.

### Key Development Files

- `.gitignore`: Specifies intentionally untracked files that Git should ignore. This has been recently updated to include common OS-generated files, Node.js artifacts, and log files.
- `.clinerules`: Contains project-specific intelligence and patterns for Cline (the AI assistant).
- `memory-bank/`: Stores contextual information about the project to aid AI-assisted development.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- This tool was developed to support NATO medical interoperability exercises
- Special thanks to the medical subject matter experts who provided guidance on realistic patient flow and treatment scenarios
