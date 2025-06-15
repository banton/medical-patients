# Military Medical Exercise Patient Generator

<img src="https://milmed.tech/atlantis-logo.svg" width="250px" alt="Atlantis">

A web-based application to generate realistic dummy patient data for military medical exercises. It features a highly configurable system supporting dynamic scenario definitions with temporal warfare patterns, multiple treatment facilities, all 32 NATO nations, varied injury types, environmental conditions, and realistic timeline distributions. Built with a PostgreSQL backend, comprehensive RESTful API with v1 standardization, Python SDK, and modern web interface, all following NATO medical standards.

## Overview

This application generates simulated patient data for military medical exercises with advanced temporal warfare scenario modeling. It creates realistic patient flow through dynamically configurable medical treatment facility chains (e.g., POI, R1, R2, R3, R4) with authentic timing patterns, environmental conditions, and progression statistics. The system features a temporal generation engine that models 8 distinct warfare types, special events, and environmental factors affecting casualty patterns over time. Built upon a PostgreSQL database with Alembic migrations, it offers extensive control via a RESTful API and Python SDK. The generated data complies with international medical data standards including:

- Minimal Core Medical Data (AMedP-8.1)
- Medical Warning tag (AMedP-8.8)
- International Patient Summary ISO27269:2021
- NATO medical interoperability standards

## Features

- **Advanced Temporal Warfare Modeling**: Comprehensive scenario generation with realistic timing patterns:
    - **8 Warfare Types**: Conventional, Artillery/Indirect Fire, Urban Warfare, Guerrilla/Insurgency, Drone/Remote, Naval/Amphibious, CBRN, and Peacekeeping operations
    - **Special Events**: Major offensives, ambush attacks, and mass casualty incidents with dynamic timing
    - **Environmental Conditions**: Weather effects (rain, fog, storms), terrain modifiers (mountainous, urban debris), and operational factors (night operations, visibility restrictions)
    - **Intensity & Tempo Control**: Configurable conflict intensity (low/medium/high/extreme) and operational tempo (sustained/escalating/surge/declining/intermittent)
    - **Realistic Casualty Patterns**: Time-distributed patient generation over configurable battle duration (1-30+ days)

- **Highly Configurable Scenarios**: Define and manage complex exercise scenarios including:
    - Dynamic medical facility chains (e.g., POI, R1-R4) with custom parameters and evacuation timing
    - Multiple configurable battle fronts with specific casualty rates and geographic characteristics
    - Detailed nationality distributions per front supporting all 32 NATO nations
    - Comprehensive injury type distributions (Disease, Non-Battle Injury, Battle Injury) with warfare-specific modifiers

- **Modern Web Interface**: Clean, responsive interface with enhanced user experience:
    - **Scenario Generation Configuration**: Intuitive accordion-based JSON editors for complex configurations
    - **Dynamic Configuration Overview**: Real-time display of selected parameters (patients, fronts, nationalities, warfare types, duration)
    - **Real-time Progress Tracking**: Detailed generation status with fun progress messages and time estimation
    - **Configuration History**: Automatic saving and loading of previous configurations with metadata

- **React Timeline Viewer**: Advanced interactive visualization tool for patient flow analysis:
    - Interactive timeline playback with speed control (0.25x-10x) and patient movement visualization
    - 5-facility progression display (POI → Role1 → Role2 → Role3 → Role4) with fixed headers
    - Patient status tracking with visual KIA/RTD indicators and name display
    - Smart tallying system and auto-hide for terminal cases to reduce visual clutter
    - File upload interface with drag-and-drop support and format validation

- **Database-Backed Configurations**: Scenarios stored and versioned in PostgreSQL with full audit trail
- **Standardized RESTful API**: v1 API endpoints with consistent request/response models, comprehensive validation, and OpenAPI documentation
- **Python SDK**: Simplified API interaction for automation and integration workflows
- **Realistic Patient Data**:
    - Demographics generation for all NATO nations with authentic names and ID formats
    - Medical conditions using SNOMED CT codes with warfare-specific injury patterns
    - Temporal metadata including casualty event IDs, mass casualty classification, and environmental conditions
- **Multiple Output Formats**: JSON and CSV formats with compressed ZIP archives
- **Data Security Options**: AES-256-GCM encryption with unique salts per encryption operation
- **Dockerized Development Environment**: Complete Docker Compose setup with PostgreSQL and Redis support
- **Database Schema Management**: Alembic migrations for robust schema versioning
- **Background Job Processing**: Async patient generation with real-time progress tracking and job management

## Architecture

The application features a clean, domain-driven architecture with clear separation of concerns. The codebase has been recently refactored (May 2024) to improve scalability, maintainability, and developer experience.

### Recent Architecture Improvements (June 2025)

**✅ API Standardization**: Complete v1 API standardization with consistent request/response models, comprehensive validation, and proper error handling.

**✅ Background Task Processing**: Fixed patient generation workflow with proper background task execution and database configuration management.

**✅ Clean Codebase**: Systematic removal of deprecated code, auto-generated files, and unused artifacts for a clean foundation.

**✅ Enhanced Testing**: Comprehensive API contract tests ensuring reliable endpoints and proper validation.

**✅ Modular Backend Architecture**: Clean domain-driven design with proper separation of concerns and dependency injection.

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
├── patient-timeline-viewer/  # React timeline visualization app
├── alembic_migrations/       # Database migrations
└── config.py                 # Application configuration
```
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
   - **ConfigurationManager**: Manages active scenario configurations with temporal pattern support
   - **Database**: PostgreSQL connection pool and data access with job tracking
   - **Flow Simulator**: Models patient progression through facilities with temporal distribution
   - **Temporal Generator**: Advanced warfare scenario engine with 8 warfare types and environmental modeling
   - **Demographics Generator**: NATO nation-specific name and ID generation
   - **Medical Generator**: SNOMED CT-based medical conditions with injury pattern distributions
   - **PatientGeneratorApp**: Orchestrates patient generation with background job processing

5. **Frontend Layer**:
   - **Main Application** (`static/index.html`): Simple web interface for patient generation
   - **JavaScript** (`static/js/simple-app.js`): Handles API communication and user interactions

6. **Database Layer**:
   - **PostgreSQL**: Configuration storage with versioning
   - **Alembic**: Schema migrations
   - **SQLAlchemy**: ORM for database operations

7. **Python SDK** (`patient_generator_sdk.py`):
   - Client library for programmatic API interaction

For detailed architecture documentation, see [ARCHITECTURE.md](ARCHITECTURE.md).

## Getting Started (Development Environment)

The application now includes a comprehensive Task runner configuration for streamlined cross-platform development workflows. This is the recommended approach for all development tasks.

### Prerequisites

-   Git
-   Docker Desktop (or Docker Engine + Docker Compose)
-   Node.js and npm (for frontend development)
-   Python 3.8+ (for local development)

### Quick Start

1.  **Clone the repository**:
    ```bash
    git clone <repository_url>
    cd medical-patients
    ```

2.  **Install dependencies and start development environment**:
    ```bash
    task setup && task dev
    ```

3.  **Access the application**:
    *   Main Application: `http://localhost:8000/static/index.html`
    *   API Documentation: `http://localhost:8000/docs`
    *   Alternative API Docs: `http://localhost:8000/redoc`

4.  **Start the timeline viewer** (optional):
    ```bash
    task timeline-viewer
    ```
    *   Timeline Viewer: `http://localhost:5174`

### Development Commands

Use `task --list` to see all available commands:

```bash
task --list               # Show all available commands
task dev                  # Start development environment (DB + App)
task test:all             # Run all tests
task test:api             # Run API integration tests
task lint:all             # Run linting checks
task lint:format          # Format code automatically
task clean                # Clean up generated files and cache
task frontend:build       # Build all frontend components
task setup                # Install all dependencies
task db:migrate           # Run database migrations
task check-requirements   # Check environment setup
```

### Alternative Setup Methods

**Using the legacy script**:
```bash
chmod +x start-dev.sh
./start-dev.sh
```

**Manual Setup**:
```bash
# Start PostgreSQL
docker compose up -d db

# Install Python dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start the application
PYTHONPATH=. python src/main.py
```

For more details on Docker configurations for different environments (production, Traefik), see [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md).

### Testing and Quality Assurance

The application includes comprehensive testing infrastructure:

```bash
# Run all tests
task test:all

# Run only unit tests
task test:unit

# Run API integration tests (requires running server)
task test:api

# Check code quality (linting + type checking)
task lint:all

# Format code automatically
task lint:format
```

### Development Workflow

1. **Start Development Environment**: `task dev`
2. **Make Code Changes**: Edit files as needed
3. **Test Changes**: `task test:all` or `task test:api`
4. **Check Code Quality**: `task lint:all`
5. **Format Code**: `task lint:format`
6. **Generate Test Data**: `task dev:generate-test`

For complete development guidelines, see the [Git Workflow documentation](memory-bank/git-workflow.md).

## Usage

The application offers multiple ways to generate patient data:

### 1. Web Interface

Access the simple web interface at `http://localhost:8000/static/index.html`:
- Click "Generate Patients" to start a new generation job
- Monitor job progress in real-time
- Download generated patient data as ZIP archives when complete

### 2. Python SDK

Use the included Python SDK for programmatic access:

```python
from patient_generator_sdk import PatientGeneratorClient

# Initialize client
client = PatientGeneratorClient(
    base_url="http://localhost:8000",
    api_key="your_secret_api_key_here"
)

# Start generation job
job = client.start_generation_job({
    "configuration": {
        "name": "Test Generation",
        "total_patients": 10
    },
    "output_formats": ["json"],
    "priority": "normal"
})

# Monitor progress
while True:
    status = client.get_job_status(job["job_id"])
    if status["status"] == "completed":
        break
    elif status["status"] == "failed":
        break
    time.sleep(2)

# Download results
client.download_job_output(job["job_id"], "patients.zip")
```

### 3. Direct API Usage

Use the standardized v1 API endpoints directly:

```bash
# Start generation
curl -X POST "http://localhost:8000/api/v1/generation/" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_secret_api_key_here" \
  -d '{
    "configuration": {
      "name": "API Test",
      "total_patients": 5
    },
    "output_formats": ["json"]
  }'

# Check job status
curl -H "X-API-Key: your_secret_api_key_here" \
  "http://localhost:8000/api/v1/jobs/{job_id}"

# Download results
curl -H "X-API-Key: your_secret_api_key_here" \
  "http://localhost:8000/api/v1/downloads/{job_id}" \
  --output patients.zip
```

### 4. API Documentation

Complete API documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

Generated data can be used for:
-   Importing into exercise management systems.
-   Deploying to NFC smarttags.
-   Medical treatment facility simulations.

## Data Structure and Configuration

Patient data follows NATO medical standards with comprehensive metadata for training scenarios. Each patient includes demographics, medical conditions with SNOMED CT codes, temporal metadata (casualty event ID, mass casualty classification, environmental conditions), and complete evacuation timeline data.

### Scenario Configuration Format

Scenario configurations are complex JSON objects managed via the API and stored in the database with full versioning. The modern temporal configuration format includes:

#### Core Parameters
- **total_patients**: Number of patients to generate (1-10,000+)
- **days_of_fighting**: Battle duration in days (1-30+)
- **base_date**: Starting date for scenario timeline (ISO 8601 format)

#### Warfare Type Configuration
- **conventional**: Traditional military operations with sustained combat patterns
- **artillery**: Indirect fire with surge patterns and bombardment cycles
- **urban**: Building-to-building combat with phased assault patterns
- **guerrilla**: Sporadic attacks with dawn/dusk preference and low-intensity operations
- **drone**: Precision strikes with daylight preference and minimal collateral damage
- **naval**: Wave assault patterns with coordinated attack timing
- **cbrn**: Chemical/biological/radiological/nuclear warfare with contamination spread
- **peacekeeping**: Low-intensity stabilization operations during business hours

#### Operational Parameters
- **intensity**: Conflict intensity level (low/medium/high/extreme)
- **tempo**: Operational tempo (sustained/escalating/surge/declining/intermittent)

#### Special Events
- **major_offensive**: Large-scale operations with 3x casualty multiplier
- **ambush**: Sudden attacks during vulnerability periods with 2x multiplier
- **mass_casualty**: Coordinated events with 5x multiplier and guaranteed mass casualties

#### Environmental Conditions
- **Weather Effects**: rain, fog, storm, extreme_heat, extreme_cold, dust_storm
- **Terrain Modifiers**: mountainous_terrain, urban_debris
- **Operational Factors**: night_operations affecting evacuation timing and casualty rates

#### Medical Configuration
- **injury_mix**: Percentage distribution of injury types
  - Disease (typically 40-60% in sustained operations)
  - Non-Battle Injury (typically 25-40%)
  - Battle Injury (typically 10-25% varying by warfare type)

#### Battle Front Definitions
- **Front configurations**: Multiple fronts with specific casualty rates, nationality distributions, and geographic characteristics
- **Nationality distributions**: Percentage allocations for all 32 NATO nations per front
- **Casualty rates**: Front-specific casualty generation rates

Refer to the API documentation (`/docs`) or the web interface's Scenario Generation Configuration section for complete configuration schema details.

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
│   └── js/                             # JavaScript files
│
├── patient-timeline-viewer/            # React timeline visualization
│   ├── src/                            # React app source code
│   │   ├── components/                 # React components
│   │   ├── types/                      # TypeScript definitions
│   │   └── utils/                      # Timeline utilities
│   ├── public/                         # Static assets
│   └── package.json                    # React app dependencies
│
├── tests/                              # Test files
├── config.py                           # Environment configuration
├── Dockerfile                          # Container definition
├── docker-compose.dev.yml              # Development environment
├── requirements.txt                    # Python dependencies
└── package.json                        # Frontend dependencies
```

For detailed architecture documentation, see [ARCHITECTURE.md](ARCHITECTURE.md).

## React Timeline Viewer

The React Timeline Viewer is a standalone visualization tool that provides interactive playback of patient movement through medical evacuation facilities. It's designed to help analyze patient flow patterns and evacuation timing.

### Features

- **Interactive Timeline Playback**: Play, pause, and control speed (0.25x-10x) of patient movement visualization
- **Facility Visualization**: 5-column layout with fixed-height headers showing POI → Role1 → Role2 → Role3 → Role4 progression
- **Patient Status Tracking**: Visual indicators for KIA, RTD, and active patients with smooth animations
- **Patient Name Display**: Shows "FirstInitial. LastName, Nationality" format with battlefield front information
- **Smart KIA/RTD Tallying**: POI tracks pre-Role1 deaths, other facilities track treatment-specific outcomes
- **Compact Design**: 50% more patients visible with optimized spacing and tighter layout
- **Auto-Hide Terminal Cases**: KIA/RTD patients disappear after 15 minutes to reduce visual clutter
- **Viewport Indicators**: Shows count of patients below visible area with scroll hints
- **File Upload Interface**: Drag-and-drop support for patients.json files with format validation
- **Real-time Statistics**: Cumulative and current patient counts with always-visible counters

### Usage

1. **Start the timeline viewer**:
   ```bash
   make timeline-viewer
   ```

2. **Generate patient data** from the main application and download the results

3. **Upload the patients.json file** to the timeline viewer via drag-and-drop

4. **Use playback controls** to visualize patient flow:
   - Play/Pause timeline progression
   - Adjust speed (0.5x to 60x)
   - Seek to specific time points
   - Reset to beginning

### Timeline Viewer Commands

**Current (Makefile - Legacy)**:
```bash
make timeline-viewer    # Start development server (port 5174)
make timeline-build     # Build for production
make timeline-test      # Test build process
make dev-full          # Start both backend and timeline viewer
```

**Future (Task - Under Migration)**:
Timeline viewer commands will be migrated to Task runner in the next phase of EPIC-001.

### Integration Workflow

The timeline viewer is designed to work seamlessly with the main patient generator:

1. Configure and generate patients using the main application
2. Download the generated patients.json file
3. Load the file into the timeline viewer for visualization
4. Analyze patient flow patterns and evacuation timing

## Standards Compliance

This generator creates data compliant with:
- NATO medical data standards (AMedP-8.1, AMedP-8.8)
- SNOMED CT for medical conditions, procedures and clinical terminology
- LOINC for laboratory values and medical observations
- ISO3166 alpha-3 for country codes and nationality identification
- ISO8601 for dates and times throughout temporal scenarios
- International Patient Summary ISO27269:2021 for medical data structure
- NDEF format specifications for NFC tag compatibility

## Project Status

### ✅ Recently Completed (June 2025)
- **Temporal Patient Generation System**: Complete implementation of advanced warfare scenario modeling with 8 warfare types, environmental conditions, and realistic timing patterns
- **API v1 Standardization**: Complete API standardization with consistent endpoints, models, and validation
- **Background Task Processing**: Fixed patient generation with proper async background tasks and progress tracking
- **Modern Web Interface**: Enhanced UI with scenario configuration, dynamic overview, and terminology cleanup
- **React Timeline Viewer**: Interactive patient flow visualization with timeline playback and facility progression
- **Clean Codebase Foundation**: Systematic cleanup of deprecated and unused code
- **Enhanced Download Functionality**: Working file downloads with proper authentication and ZIP packaging
- **Comprehensive Testing**: Full API contract test coverage with temporal system validation

### 🔄 In Progress
- Performance optimization with Redis caching
- Advanced frontend development with modern framework
- Enhanced visualization dashboard

### 📋 Planned Features
- CI/CD pipeline with GitHub Actions
- Comprehensive monitoring and observability
- Plugin architecture for extensible configurations
- Advanced analytics and reporting

For detailed progress tracking, see the memory system documentation in the `memory/` directory.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Git Workflow

This project follows a structured Git workflow, including a specific branching model, commit message conventions, and Pull Request (PR) processes. The core branches are:

-   **`main`**: Stable, production-ready code.
-   **`develop`**: Primary integration branch for ongoing development.
-   **Feature Branches** (e.g., `feature/TICKET-ID-short-description`): For new features, bugs, or tasks.
-   **Release Branches** (e.g., `release/vX.Y.Z`): For preparing releases.
-   **Hotfix Branches** (e.g., `hotfix/TICKET-ID-short-description`): For critical production fixes.

For complete details on the branching strategy, commit message format, PR process, testing requirements, and release procedures, please refer to the Git Workflow documentation in the `memory/` directory.

### Key Development Files

- `.gitignore`: Specifies intentionally untracked files that Git should ignore. This has been recently updated to include common OS-generated files, Node.js artifacts, and log files.
- `memory/`: Stores contextual information about the project including patterns, implementations, and architectural decisions.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- This tool was developed to support NATO medical interoperability exercises
- Special thanks to the medical subject matter experts who provided guidance on realistic patient flow and treatment scenarios
