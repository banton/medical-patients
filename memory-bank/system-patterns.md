# System Patterns

## System Architecture

The Military Medical Exercise Patient Generator follows a modular architecture with clear separation of concerns. It consists of a Python backend with a web interface frontend, organized around core generation components that work together to produce realistic patient data.

### Architectural Overview

1. **Frontend Layer**:
   - Single-page HTML/JavaScript application (`static/index.html`)
   - Bootstrap for styling and responsive design
   - Chart.js for data visualizations
   - AJAX communication with the backend API

2. **Backend API Layer**:
   - FastAPI web server (`app.py`)
   - RESTful endpoints for job management
   - Background task processing for generation jobs
   - Static file serving

3. **Core Generation Engine**:
   - Modular Python package (`patient_generator/`)
   - Configurable through a central application class (`PatientGeneratorApp`)
   - Component-based design with specialized generators

4. **Output Handling**:
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
