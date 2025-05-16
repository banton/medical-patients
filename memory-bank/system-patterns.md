# System Patterns

## System Architecture

The Military Medical Exercise Patient Generator follows a modular architecture with clear separation of concerns. It consists of a Python backend with a web interface frontend, organized around core generation components that work together to produce realistic patient data.

### Architectural Overview

1. **Frontend Layer**:
   - **Main Application (`static/index.html`)**:
     - Single-page HTML/JavaScript application.
     - Uses Bootstrap for styling and Chart.js for basic visualizations.
     - AJAX communication with the backend API.
   - **Enhanced Visualization Dashboard (`static/visualizations.html`)**:
     - Hosts the `ExerciseDashboard` React component.
     - The component is written in TSX (`enhanced-visualization-dashboard.tsx`).
     - Compiled into a JavaScript bundle (`static/dist/bundle.js`) using `esbuild`.
     - Uses React, Recharts for advanced charting, and Lucide-React for icons.
     - Also communicates with the backend API for data.

2. **Backend API Layer**:
   - FastAPI web server (`app.py`)
   - RESTful endpoints for job management
   - Background task processing for generation jobs
   - Static file serving

3. **Core Generation Engine**:
   - Modular Python package (`patient_generator/`)
   - Configurable through a central application class (`PatientGeneratorApp`)
   - Component-based design with specialized generators

4. **Database Layer**:
    - SQLite for job persistence (`patient_generator/database.py`).
    - Singleton pattern for database connection management.

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
   - Used in `patient_generator/database.py` for managing the database connection, ensuring only one instance is created and shared.

### Component Relationships

1. **Patient Generator Core** (`patient_generator/app.py`):
   - Orchestrates the overall generation process
   - Manages configuration
   - Coordinates between components
   - Reports progress

2. **Patient Flow Simulator** (`flow_simulator.py`):
   - Creates initial patients with basic attributes
   - Simulates movement through medical facilities
   - Applies statistical models for outcomes (RTD, KIA)

3. **Demographics Generator** (`demographics.py`):
   - Generates realistic person data based on nationality
   - Produces names, birthdates, ID numbers
   - Manages country-specific data formats

4. **Medical Condition Generator** (`medical.py`):
   - Creates appropriate medical conditions based on injury type
   - Manages SNOMED CT codes for conditions
   - Generates related conditions, allergies, and medications

5. **FHIR Generator** (`fhir_generator.py`):
   - Converts patient objects to HL7 FHIR R4 bundles
   - Creates patient, condition, observation, and procedure resources
   - Ensures compliance with FHIR standards

6. **Output Formatter** (`formatter.py`):
   - Converts data to different output formats
   - Handles compression and encryption
   - Creates NDEF-formatted data for NFC tags

7. **Patient Class** (`patient.py`):
   - Core data model representing a patient
   - Tracks demographics, medical history, and status
   - Provides methods for adding treatments

### Data Flow

1. User configures generation parameters via web UI
2. Backend creates a generation job and starts background processing
3. `PatientGeneratorApp` orchestrates the generation process:
   - Patient flow simulation creates basic patients with statuses
   - Demographics and medical conditions are added to patients
   - Patients are converted to FHIR bundles
   - Bundles are formatted for output in requested formats
4. Generated files are stored for download
5. UI updates with progress and summary statistics
6. User downloads the completed files

### Concurrency Model

- Background tasks for long-running generation jobs
- Job status tracking for concurrent users
- Progress reporting via callbacks

### Security Considerations

- Optional AES-256-GCM encryption for sensitive data
- Password-based key derivation
- Temporary file management for downloads

### Extensibility Points

- New nationality support can be added to the demographics generator
- Additional medical conditions can be added to the condition generator
- New output formats can be implemented in the formatter
- The flow simulator can be adjusted for different exercise scenarios

### Identified Technical Debt Areas

Based on a recent technical review, the following areas have been identified for potential improvement:

1.  **Memory Management**:
    *   In-memory storage of large patient datasets (e.g., `jobs[job_id]["patients_data"]` in `app.py`, FHIR bundle generation) can lead to issues with very large generation jobs.
    *   Opportunities for streaming processing and disk-based serialization.

2.  **Error Handling**:
    *   Inconsistent error handling approaches across backend (Python) and frontend (React/TSX) components.
    *   Need for standardized custom exceptions, structured logging, and robust error recovery mechanisms (e.g., React Error Boundaries).

3.  **Frontend Architecture**:
    *   Mix of traditional JavaScript (`static/index.html`) and modern React/TypeScript (`enhanced-visualization-dashboard.tsx`).
    *   Duplicate visualization logic between the two frontend interfaces.
    *   Large bundle size for the enhanced dashboard.
    *   Inconsistent state management in the React application.

4.  **Configuration Management**:
    *   Potential for redundant configuration definitions.
    *   Opportunity to centralize configuration using a dedicated module (e.g., `config.py` with Pydantic) and environment variables.

5.  **Testing Coverage**:
    *   Uneven test coverage, particularly for some frontend components and API integration aspects.
    *   Need for expanded unit, integration, and potentially end-to-end tests.

6.  **Database Implementation**:
    *   Limited connection pooling.
    *   Potential for SQL injection if queries are not consistently parameterized.
    *   Lack of a migration management system for schema changes.

7.  **Docker Optimization**:
    *   Container images could be large due to unnecessary dependencies.
    *   Opportunity for multi-stage builds and optimized Docker Compose configurations for different environments (dev, prod).
    *   Review container security best practices.
