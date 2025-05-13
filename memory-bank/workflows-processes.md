# Workflows and Processes

## Key Process Flows and Interactions

This document outlines the main workflows, processes, and interactions in the Military Medical Exercise Patient Generator system.

### 1. Patient Generation Process

The core workflow for generating patient data:

1. **Initialization**:
   - `PatientGeneratorApp` loads configuration parameters
   - Initial progress callback (0%)

2. **Patient Flow Simulation** (20% of total progress):
   - `PatientFlowSimulator` creates basic patient objects
   - Assigns nationality, front, injury type, triage category
   - Simulates movement through medical facilities (POI → R1 → R2 → R3 → R4)
   - Determines final outcomes (RTD or KIA)
   - Progress reported at 20%

3. **Patient Enhancement** (30% of total progress):
   - For each patient:
     - Generate demographics using `DemographicsGenerator`
     - Create primary condition using `MedicalConditionGenerator`
     - Add additional conditions based on triage severity
     - Generate medications based on conditions
     - Add allergies (10% probability)
   - Progress updates during this phase from 20% to 50%

4. **FHIR Bundle Creation** (40% of total progress):
   - For each patient:
     - Create FHIR Patient resource
     - Create Condition resources
     - Create Procedure resources for treatments
     - Create Observation resources
     - Assemble complete Bundle
   - Progress updates during this phase from 50% to 90%

5. **Output Formatting** (10% of total progress):
   - Format data as JSON and/or XML
   - Create compressed versions if requested
   - Create encrypted versions if requested
   - Create sample NDEF files for NFC
   - Final progress update to 100%

### 2. Web Interface Job Management

The process flow for the web interface:

1. **Configuration**:
   - User sets parameters in web form (patient count, distributions, etc.)
   - Form validates percentages add up to 100%
   - User selects output formats and options
   - User submits form

2. **Job Creation**:
   - Backend creates new job record with "queued" status
   - Job ID is returned to frontend
   - Frontend adds job to display and begins polling

3. **Background Processing**:
   - Backend starts `run_generator_job` in background task
   - Job status updated to "running"
   - Web generator configuration converted to internal config format
   - Patient generator process executes with progress callbacks
   - Progress updates sent to frontend via polling

4. **Results Preparation**:
   - Job status updated with summary statistics
   - List of output files recorded
   - File sizes calculated
   - Job status set to "completed"

5. **Download and Visualization**:
   - Frontend displays summary charts
   - Download button becomes available
   - User can download ZIP archive of all generated files

### 3. Patient Flow Simulation

The specific process for simulating patient movement through facilities:

1. **Initial Casualty Creation**:
   - Assign origin front based on distribution
   - Assign nationality based on front distribution
   - Assign injury type (DISEASE, NON_BATTLE, BATTLE_TRAUMA)
   - Assign triage category (T1, T2, T3) with weighting by injury type
   - Create initial POI status with timestamp

2. **Facility Progression**:
   - For each patient, starting at POI:
     - Determine next location based on probabilities
     - If KIA or RTD, record final status and stop
     - Otherwise, create treatment event for next facility
     - Generate appropriate treatments for facility level
     - Generate observations (vitals, labs) for facility level
     - Update patient status to new facility
     - Continue until reaching terminal state (KIA, RTD, R4)

3. **Treatment Generation Logic**:
   - R1: Basic first aid, stabilization
   - R2: More advanced treatments, some surgery
   - R3: Specialized treatments, more surgery
   - R4: Definitive care

4. **Observation Generation Logic**:
   - All facilities: Vital signs (temp, HR, BP)
   - R2/R3: Add lab tests (Hgb, WBC)
   - R3: More specialized tests (glucose, blood type)

### 4. FHIR Bundle Generation

The process for converting patients to FHIR format:

1. **Bundle Initialization**:
   - Generate unique bundle ID
   - Set timestamp
   - Add NFC tag ID extension

2. **Patient Resource Creation**:
   - Generate unique patient resource ID
   - Add demographics (name, gender, birthdate)
   - Add nationality and other extensions
   - Add identifiers with appropriate systems

3. **Medical Resource Creation**:
   - Create Condition resource for primary condition
   - Create Condition resources for additional conditions
   - Create Procedure resources for each treatment
   - Create Observation resources for each observation
   - Create additional resources based on demographics (blood type, weight)

4. **Bundle Assembly**:
   - Add all resources to bundle entries
   - Ensure proper references between resources

### 5. Data Security Implementation

The process for securing output data:

1. **Compression (if enabled)**:
   - Convert data to bytes if string
   - Apply gzip compression
   - Save with .gz extension

2. **Encryption (if enabled)**:
   - If password provided, derive key using PBKDF2
   - Otherwise, use random key (for testing)
   - Generate random initialization vector (IV)
   - Encrypt using AES-256-GCM
   - Combine IV + tag + ciphertext in output
   - Save with .enc extension

3. **Combined Security**:
   - Apply compression first
   - Then encrypt the compressed data
   - Save with .gz.enc extension

### 6. Command Line Usage

The process for using the command-line interface:

1. **Configuration Setup**:
   - Create configuration dictionary
   - Set output directory and formats
   - Set patient count and other parameters

2. **Generator Execution**:
   - Initialize PatientGeneratorApp with config
   - Run generation process
   - Display progress in terminal

3. **Summary Output**:
   - Print statistics on generated patients
   - Show counts by status (KIA, RTD, in treatment)
   - Display output file location

### 7. Error Handling Processes

How errors are managed in the system:

1. **Web Interface Errors**:
   - Form validation prevents invalid configurations
   - Server errors during generation are caught and recorded
   - Job status updated to "failed" with error message
   - Error displayed to user in UI

2. **Generation Process Errors**:
   - Exceptions caught and reported
   - Try/except blocks around critical operations
   - Fallbacks for missing data (e.g., default to USA if nationality not found)

3. **File Operation Errors**:
   - Directory creation with exist_ok=True
   - Error checking for file operations
   - Cleanup of temporary files

### 8. Demo Process

The demonstration workflow (demo.py):

1. **Setup**:
   - Create sample configuration with small patient count
   - Create output directory

2. **Patient Generation**:
   - Generate patient flow
   - Display sample patient details

3. **Data Enhancement**:
   - Add demographics and medical conditions
   - Show sample demographics and conditions

4. **FHIR Bundle Creation**:
   - Convert patients to FHIR format

5. **Output Creation**:
   - Generate sample output files
   - Create sample NFC data
   - Display list of generated files

### 9. Testing Process

The workflow for running tests:

1. **Test Setup**:
   - Create test configuration
   - Initialize test fixtures

2. **Patient Creation Tests**:
   - Test basic patient attributes
   - Test treatment addition

3. **Demographics Tests**:
   - Test generation for different nationalities
   - Verify name and gender correctness

4. **Medical Condition Tests**:
   - Test condition generation for different injury types
   - Verify severity is appropriate for triage level

5. **Flow Simulation Tests**:
   - Test full patient flow generation
   - Verify treatments and final statuses
