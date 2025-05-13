# Component Reference

## Key Components and Their Functions

This document provides a detailed reference of the main components in the Military Medical Exercise Patient Generator, their responsibilities, interfaces, and interactions.

### 1. PatientGeneratorApp (`patient_generator/app.py`)

**Purpose**: Main orchestrator that coordinates the entire patient generation process.

**Key Functions**:
- `__init__(self, config=None)`: Initializes with optional configuration or defaults.
- `_default_config(self)`: Creates default configuration with realistic distributions.
- `run(self, progress_callback=None)`: Executes the complete generation pipeline with optional progress reporting.

**Configuration Parameters**:
- `total_patients`: Number of patients to generate (default: 1440)
- `front_distribution`: Casualty distribution across fronts
- `nationality_distribution`: Nationality distribution within each front
- `injury_distribution`: Distribution of injury types
- `output_formats`: Output format options (json, xml)
- `output_directory`: Where to save generated files
- `use_compression`: Whether to generate compressed files
- `use_encryption`: Whether to encrypt output files
- `encryption_key`: Key for AES-256-GCM encryption

**Interactions**:
- Uses `PatientFlowSimulator` to create initial patients and simulate flow
- Uses `DemographicsGenerator` to add realistic personal details
- Uses `MedicalConditionGenerator` to add medical conditions
- Uses `FHIRBundleGenerator` to convert patients to FHIR format
- Uses `OutputFormatter` to create final output files

### 2. Patient (`patient_generator/patient.py`)

**Purpose**: Core data model representing an individual patient with medical history.

**Key Functions**:
- `__init__(self, patient_id)`: Creates a new patient with the given ID.
- `add_treatment(self, facility, date, treatments=None, observations=None)`: Adds a treatment event to the patient's history.
- `set_demographics(self, demographics)`: Sets patient demographic information.
- `get_age(self)`: Calculates patient age from birthdate.

**Key Attributes**:
- `id`: Unique patient identifier
- `demographics`: Dictionary of personal information
- `treatment_history`: List of treatment events
- `current_status`: Current facility or status (POI, R1-R4, RTD, KIA)
- `injury_type`: Type of injury (DISEASE, NON_BATTLE, BATTLE_TRAUMA)
- `triage_category`: Severity category (T1, T2, T3)
- `nationality`: ISO country code
- `front`: Origin of casualty (Polish, Estonian, Finnish)
- `primary_condition`: Main medical condition
- `additional_conditions`: Secondary medical conditions

### 3. PatientFlowSimulator (`patient_generator/flow_simulator.py`)

**Purpose**: Simulates patient movement through medical treatment facilities.

**Key Functions**:
- `__init__(self, config)`: Initialize with configuration parameters.
- `generate_casualty_flow(self, total_casualties=1440)`: Create initial patients and simulate their flow.
- `_create_initial_patient(self, patient_id)`: Create a new patient with basic attributes.
- `_simulate_patient_flow(self)`: Model movement through medical facilities.
- `_determine_next_location(self, patient, current_location)`: Decide where patient goes next.
- `_generate_treatments(self, patient, facility)`: Create appropriate treatments for the facility.
- `_generate_observations(self, patient, facility)`: Create medical observations.

**Key Distributions**:
- `day_distribution`: Distribution of casualties across exercise days
- `front_distribution`: Distribution across geographic fronts
- `nationality_distribution`: Nationalities within each front
- `injury_distribution`: Types of injuries and diseases

**Flow Simulation Logic**:
- Patients start at Point of Injury (POI)
- Move through Role 1-4 medical facilities based on probability
- Terminal states are Return to Duty (RTD) or Killed in Action (KIA)
- Probability of each outcome based on current location and patient condition

### 4. DemographicsGenerator (`patient_generator/demographics.py`)

**Purpose**: Generates realistic person data based on nationality.

**Key Functions**:
- `__init__(self)`: Initializes with name data for different nationalities.
- `generate_person(self, nationality, gender=None)`: Creates a complete person profile.
- `_init_name_data(self)`: Sets up name lists by nationality and gender.
- `_init_id_formats(self)`: Configures ID number formats for different countries.

**Supported Nationalities**:
- POL (Poland)
- EST (Estonia)
- FIN (Finland)
- GBR (United Kingdom)
- USA (United States)
- LIT (Lithuania)
- ESP (Spain)
- NLD (Netherlands)

**Generated Demographics**:
- First and last names appropriate to nationality and gender
- Realistic ID numbers formatted for the country
- Age-appropriate birthdate
- Religion (optional)
- Physical attributes (weight, blood type)

### 5. MedicalConditionGenerator (`patient_generator/medical.py`)

**Purpose**: Creates realistic medical conditions using standardized coding.

**Key Functions**:
- `__init__(self)`: Sets up condition pools and severity modifiers.
- `generate_condition(self, injury_type, triage_category)`: Creates a condition based on injury type and severity.
- `generate_additional_conditions(self, primary_condition, count=0)`: Creates related secondary conditions.
- `generate_allergies(self, count=0)`: Creates random allergies.
- `generate_medications(self, conditions, count=1)`: Generates appropriate medications for conditions.

**Condition Types**:
- Battle trauma conditions (wounds, injuries from combat)
- Non-battle injuries (accidents, environmental injuries)
- Disease conditions (illnesses, infections)

**Coding Systems**:
- SNOMED CT codes for conditions and severity
- Logical relationships between conditions (e.g., TBI may lead to secondary issues)
- Appropriate medication mapping for conditions

### 6. FHIRBundleGenerator (`patient_generator/fhir_generator.py`)

**Purpose**: Converts patient objects to HL7 FHIR R4 standard bundles.

**Key Functions**:
- `__init__(self, demographics_generator=None)`: Initializes with optional demographics generator.
- `create_fhir_bundles(self, patients)`: Creates FHIR bundles for multiple patients.
- `create_patient_bundle(self, patient)`: Creates a complete FHIR bundle for one patient.
- `_create_patient_resource(self, patient)`: Creates FHIR Patient resource.
- `_create_medical_resources(self, patient, patient_id)`: Creates condition, procedure and observation resources.
- Various helper methods for specific resource types.

**FHIR Resources Created**:
- Patient resources with demographics
- Condition resources for medical conditions
- Observation resources for vital signs and measurements
- Procedure resources for treatments
- Bundle resources to contain all related resources

**Standards Compliance**:
- HL7 FHIR R4 format
- SNOMED CT coding for conditions and procedures
- LOINC coding for observations
- ISO8601 for dates and times

### 7. OutputFormatter (`patient_generator/formatter.py`)

**Purpose**: Creates final output files in various formats with security options.

**Key Functions**:
- `format_json(self, bundles)`: Formats bundles as JSON.
- `format_xml(self, bundles)`: Formats bundles as XML.
- `compress_gzip(self, data)`: Compresses data using gzip.
- `encrypt_aes(self, data, key)`: Encrypts data using AES-256-GCM.
- `format_ndef(self, data, format_type="plain")`: Formats data for NFC tags.
- `create_output_files(self, bundles, output_dir, formats=None, use_compression=True, use_encryption=False, encryption_key=None)`: Creates all required output files.

**Output Options**:
- JSON and XML formats
- Compressed versions using gzip
- Encrypted versions using AES-256-GCM
- Combined compression and encryption
- NDEF formatting for NFC tags

**File Organization**:
- Standard format files (e.g., patients.json, patients.xml)
- Compressed files with .gz extension
- Encrypted files with .enc extension
- Sample NDEF files for NFC testing

### 8. Web Application (`app.py`)

**Purpose**: Provides the web interface and API for the generator.

**Key Functions**:
- `generate_patients(config: GeneratorConfig, background_tasks: BackgroundTasks)`: API endpoint to start a generation job.
- `get_job_status(job_id: str)`: API endpoint to check job status.
- `download_job_output(job_id: str)`: API endpoint to download generated files.
- `run_generator_job(job_id: str, config: GeneratorConfig)`: Background task function for generation.

**API Endpoints**:
- `GET /`: Serves the main HTML page
- `POST /api/generate`: Starts a patient generation job
- `GET /api/jobs/{job_id}`: Gets the status of a generation job
- `GET /api/download/{job_id}`: Downloads generated files as ZIP
- `GET /api/config/defaults`: Gets default configuration values

**Job Management**:
- Jobs stored in memory with status tracking
- Progress reporting during generation
- Summary statistics collection
- File management for completed jobs

### 9. Web Interface (`static/index.html`)

**Purpose**: User interface for configuring and running the generator.

**Key Sections**:
- Configuration Form: Patient count, distribution settings, output options
- Jobs Panel: Displays active and completed jobs with progress
- Summary Visualizations: Charts showing generated data distribution
- Download Controls: Access to generated files

**Technologies**:
- Bootstrap 5 for responsive layout
- Chart.js for data visualization
- JavaScript for dynamic updates and form validation
- AJAX for asynchronous communication with API

**UI Features**:
- Real-time progress updates
- Visual data distribution summaries
- Form validation for percentages
- Responsive design for different devices
