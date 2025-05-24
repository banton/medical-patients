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

The application features a clean, domain-driven architecture with clear separation of concerns:

### Application Structure

```
/
├── src/                        # Modular application code
│   ├── main.py                # Application entry point
│   ├── core/                  # Core utilities
│   │   ├── exceptions.py      # Custom exceptions
│   │   └── security.py        # API key authentication
│   ├── domain/                # Business domain layer
│   │   ├── models/            # Domain models
│   │   ├── repositories/      # Data access interfaces
│   │   └── services/          # Business logic services
│   └── api/v1/               # API layer
│       ├── routers/          # API endpoints
│       └── dependencies/     # Shared dependencies
├── patient_generator/         # Core generation logic
│   ├── app.py                # Patient generator application
│   ├── config_manager.py     # Configuration management
│   ├── database.py           # Database connection and repositories
│   ├── demographics.py       # Demographics generation
│   ├── medical.py            # Medical condition generation
│   ├── flow_simulator.py     # Patient flow simulation
│   ├── fhir_generator.py     # FHIR bundle generation
│   └── formatter.py          # Output formatting
├── static/                   # Frontend assets
├── alembic_migrations/       # Database migrations
└── config.py                 # Application configuration

### Key Components

1. **API Layer** (`src/api/v1/`):
   - **Routers**: Modular endpoints for configurations, generation, jobs, downloads, and visualizations
   - **Dependencies**: Shared dependencies for database sessions and services
   - **Security**: API key authentication for protected endpoints

2. **Domain Layer** (`src/domain/`):
   - **Models**: Business entities (Job, JobStatus, etc.)
   - **Services**: Business logic (JobService)
   - **Repositories**: Data access interfaces

3. **Core Layer** (`src/core/`):
   - **Security**: Authentication and authorization
   - **Exceptions**: Custom exception hierarchy

4. **Patient Generator** (`patient_generator/`):
   - **ConfigurationManager**: Manages active scenario configurations
   - **Database**: PostgreSQL connection pool and data access
   - **Flow Simulator**: Models patient progression through facilities
   - **Generators**: Demographics, medical conditions, and FHIR bundles
   - **PatientGeneratorApp**: Orchestrates patient generation
   - **Specialized Generators**: Demographics, medical conditions, flow simulation

5. **Frontend Layer**:
   - **Main Shell** (`static/index.html`): Entry point
   - **Configuration Panel** (`ConfigurationPanel.tsx`): React component for scenario design
   - **Visualization Dashboard** (`enhanced-visualization-dashboard.tsx`): Data visualization
   - **Build System**: esbuild for TypeScript/React compilation

6. **Database Layer**:
   - **PostgreSQL**: Configuration storage with versioning
   - **Alembic**: Schema migrations
   - **SQLAlchemy**: ORM for database operations

7. **Python SDK** (`patient_generator_sdk.py`):
   - Client library for programmatic API interaction

For detailed architecture documentation, see [ARCHITECTURE.md](ARCHITECTURE.md).

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
    cd medical-patients
    ```

2.  **Using Docker (Recommended)**:
    ```bash
    chmod +x start-dev.sh
    ./start-dev.sh
    ```
    This script will:
    *   Install/update frontend Node.js dependencies (`npm install`).
    *   Build all frontend React components (`npm run build:all-frontend`).
    *   Start the Docker services defined in `docker-compose.dev.yml` (FastAPI application, PostgreSQL database) in detached mode.
    *   Wait for the application service to be healthy.
    *   Apply any pending database migrations using Alembic.

3.  **Manual Setup (Alternative)**:
    ```bash
    # Start PostgreSQL (via Docker or local installation)
    docker compose up -d db
    
    # Install Python dependencies
    pip install -r requirements.txt
    
    # Run database migrations
    alembic upgrade head
    
    # Start the application
    PYTHONPATH=. python src/main.py
    ```

4.  **Access the application**:
    *   Main UI (including Advanced Configuration Panel): `http://localhost:8000/static/index.html`
    *   Enhanced Visualization Dashboard: `http://localhost:8000/static/visualizations.html`
    *   API Documentation: `http://localhost:8000/docs`

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
├── src/                                # Modularized application code
│   ├── api/v1/                         # API layer
│   │   ├── dependencies/               # Dependency injection
│   │   └── routers/                    # API endpoints
│   ├── core/                           # Core utilities
│   │   ├── exceptions.py               # Custom exceptions
│   │   └── security.py                 # Authentication
│   ├── domain/                         # Business logic
│   │   ├── models/                     # Domain models
│   │   ├── repositories/               # Data access
│   │   └── services/                   # Business services
│   └── main.py                         # Application entry point
│
├── patient_generator/                  # Core generation module
│   ├── app.py                          # PatientGeneratorApp
│   ├── config_manager.py               # Configuration management
│   ├── database.py                     # Database operations
│   └── ... (generators)
│
├── static/                             # Frontend files
│   ├── index.html                      # Main UI
│   ├── js/                             # JavaScript files
│   └── dist/                           # Compiled bundles
│
├── tests/                              # Test files
├── config.py                           # Environment configuration
├── Dockerfile                          # Container definition
├── docker-compose.dev.yml              # Development environment
├── requirements.txt                    # Python dependencies
└── package.json                        # Frontend dependencies
```

For detailed architecture documentation, see [ARCHITECTURE.md](ARCHITECTURE.md).

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

### Git Workflow

This project follows a structured Git workflow, including a specific branching model, commit message conventions, and Pull Request (PR) processes. The core branches are:

-   **`main`**: Stable, production-ready code.
-   **`develop`**: Primary integration branch for ongoing development.
-   **Feature Branches** (e.g., `feature/TICKET-ID-short-description`): For new features, bugs, or tasks.
-   **Release Branches** (e.g., `release/vX.Y.Z`): For preparing releases.
-   **Hotfix Branches** (e.g., `hotfix/TICKET-ID-short-description`): For critical production fixes.

For complete details on the branching strategy, commit message format, PR process, testing requirements, and release procedures, please refer to the [Git Workflow documentation in the Memory Bank](memory-bank/git-workflow.md).

### Key Development Files

- `.gitignore`: Specifies intentionally untracked files that Git should ignore. This has been recently updated to include common OS-generated files, Node.js artifacts, and log files.
- `.clinerules`: Contains project-specific intelligence and patterns for Cline (the AI assistant).
- `memory-bank/`: Stores contextual information about the project to aid AI-assisted development.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- This tool was developed to support NATO medical interoperability exercises
- Special thanks to the medical subject matter experts who provided guidance on realistic patient flow and treatment scenarios
