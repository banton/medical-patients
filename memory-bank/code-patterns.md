# Code Patterns and Conventions

## Style Guide and Common Patterns

This document outlines the coding patterns, conventions, and styles used throughout the Military Medical Exercise Patient Generator codebase.

### Naming Conventions

1. **Files and Modules**:
   - Snake case for file names: `flow_simulator.py`, `medical.py`
   - Short, descriptive module names
   - Package organized by functionality

2. **Classes**:
   - PascalCase for class names: `Patient`, `DemographicsGenerator`
   - Noun-based names that describe the entity
   - Specific, descriptive names

3. **Functions and Methods**:
   - Snake case: `generate_casualty_flow()`, `add_treatment()`
   - Verb-based names that describe the action
   - Private methods prefixed with underscore: `_create_initial_patient()`

4. **Variables**:
   - Snake case: `patient_id`, `front_distribution`
   - Clear, descriptive names
   - No single-letter variables except in very short loops

5. **Constants**:
   - Not explicitly defined as constants, but configuration values are used

### Code Organization

1. **Class Structure**:
   - Initialization methods first
   - Public methods next
   - Private helper methods last
   - Clear docstrings for all classes and methods

2. **Module Structure**:
   - Import statements at the top, grouped by standard library, third-party, and local
   - Module-level docstring
   - Classes in order of importance or dependency
   - Main execution block at the bottom with `if __name__ == "__main__"` guard

3. **Package Structure**:
   - Core modules in `patient_generator/` package
   - Main application entry points at root level
   - Separation of concerns between modules

### Documentation Style

1. **Docstrings**:
   - Triple-quoted docstrings for all classes and public methods
   - Brief, descriptive summaries
   - Most docstrings are single-line
   - No specific format (not using Sphinx, Google, or NumPy style)

2. **Comments**:
   - Used sparingly, mostly for clarifying complex logic
   - Section headers in longer methods

3. **README and Documentation Files**:
   - Markdown format for all documentation
   - Structured headers and lists
   - Code examples with syntax highlighting
   - Comprehensive installation and usage instructions

### Coding Patterns

1. **Configuration Handling**:
   - Default configuration provided by methods
   - Configuration passed as dictionaries
   - Fallbacks for missing configuration items
   ```python
   def _default_config(self):
       """Create default configuration"""
       return {
           "total_patients": 1440,
           "front_distribution": {
               "Polish": 0.50,
               "Estonian": 0.333,
               "Finnish": 0.167
           },
           # More defaults...
       }
   ```

2. **Progress Reporting**:
   - Callback functions for progress updates
   - Periodic updates during long-running operations
   ```python
   if progress_callback and i % 100 == 0:
       progress = 20 + int((i / total_patients) * 30)
       progress_callback(min(50, progress), patient_data)
   ```

3. **Random Data Generation**:
   - Use of Python's `random` module for distributions
   - Weighted selection for realistic distributions
   ```python
   def _select_weighted_item(self, weights_dict):
       """Select an item from a dictionary based on weights"""
       items = list(weights_dict.keys())
       weights = list(weights_dict.values())
       return random.choices(items, weights=weights, k=1)[0]
   ```

4. **Data Transformations**:
   - Progressive enhancement of data objects
   - Clear transformation steps
   ```python
   # Generate demographics
   demographics = demographics_generator.generate_person(patient.nationality, patient.gender)
   patient.set_demographics(demographics)
   
   # Generate primary condition
   primary_condition = condition_generator.generate_condition(patient.injury_type, patient.triage_category)
   patient.primary_condition = primary_condition
   ```

5. **Error Handling**:
   - Try/except blocks for error-prone operations
   - Fallbacks for missing data
   ```python
   try:
       # Attempt operation
       shutil.rmtree("temp")
       os.makedirs("temp")
   except Exception as e:
       print(f"Warning: Could not clean temp directory: {e}")
   ```

6. **Factory Methods**:
   - Creation methods that return constructed objects
   ```python
   def generate_person(self, nationality, gender=None):
       """Generate a complete person profile for the given nationality"""
       # Construction logic...
       return person_data
   ```

### Web Application Patterns

1. **FastAPI Endpoint Structure**:
   - Clear route decorators
   - Pydantic models for request validation
   - Async endpoint functions
   ```python
   @app.post("/api/generate")
   async def generate_patients(config: GeneratorConfig, background_tasks: BackgroundTasks):
       """Start a patient generation job"""
       # Implementation...
       return {"job_id": job_id, "status": "queued"}
   ```

2. **Background Tasks**:
   - Long-running operations in background tasks
   - Status tracking for monitoring
   ```python
   background_tasks.add_task(
       run_generator_job, 
       job_id=job_id, 
       config=config
   )
   ```

3. **In-Memory Store**:
   - Dictionary-based storage for job data
   ```python
   jobs[job_id] = {
       "status": "queued",
       "config": config.dict(),
       "created_at": datetime.now().isoformat(),
       "output_files": [],
       "progress": 0,
       "summary": {},
   }
   ```

4. **File Handling**:
   - Temporary file creation for downloads
   - ZIP file creation for multiple outputs
   ```python
   with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
       output_dir = f"output/{job_id}"
       for file_name in os.listdir(output_dir):
           file_path = os.path.join(output_dir, file_name)
           zip_file.write(file_path, file_name)
   ```

### Frontend JavaScript Patterns

1. **Event Listeners**:
   - DOM-ready event handler
   - Form submission handlers
   ```javascript
   document.addEventListener('DOMContentLoaded', function() {
       // Initialize handlers
       generatorForm.addEventListener('submit', async function(e) {
           e.preventDefault();
           // Form handling...
       });
   });
   ```

2. **Polling for Updates**:
   - Regular interval polling for job status
   - Clearing intervals when complete
   ```javascript
   jobPollingIntervals[jobId] = setInterval(async function() {
       // Poll for updates...
       if (jobData.status === 'completed' || jobData.status === 'failed') {
           clearInterval(jobPollingIntervals[jobId]);
           delete jobPollingIntervals[jobId];
       }
   }, 1000); // Poll every second
   ```

3. **Dynamic UI Updates**:
   - Function-based UI updates
   - Chart creation and updates
   ```javascript
   function updateJobUI(jobId, jobData) {
       // Update various UI elements based on job data
       // ...
       if (jobData.summary && Object.keys(jobData.summary).length > 0) {
           // Update charts and statistics
       }
   }
   ```

4. **Form Validation**:
   - Input-based validation
   - Percentage validation for distributions
   ```javascript
   function validateFrontPercentages() {
       let total = 0;
       frontPercentInputs.forEach(input => {
           total += parseFloat(input.value);
       });
       
       if (Math.abs(total - 100) > 0.1) {
           frontPercentError.classList.remove('hidden');
           return false;
       } else {
           frontPercentError.classList.add('hidden');
           return true;
       }
   }
   ```

### Testing Patterns

1. **Unit Test Structure**:
   - Python's `unittest` framework
   - Test methods prefixed with `test_`
   - Setup method for test fixtures
   ```python
   def setUp(self):
       """Set up test fixtures"""
       self.config = {
           # Test configuration...
       }
   
   def test_patient_creation(self):
       """Test that a patient can be created with basic attributes"""
       patient = Patient(1)
       self.assertEqual(patient.id, 1)
       # More assertions...
   ```

2. **Test Coverage**:
   - Tests for core components
   - Specific test cases for edge cases
   - Assertions for expected outcomes

### Security Patterns

1. **Encryption Implementation**:
   - AES-256-GCM for encryption
   - PBKDF2 for key derivation from passwords
   ```python
   def encrypt_aes(self, data, key):
       """Encrypt data using AES-256-GCM"""
       # Encryption implementation...
   ```

2. **Temporary File Management**:
   - Cleanup on startup
   - Temporary files with unique IDs
   ```python
   @app.on_event("startup")
   async def startup_event():
       """Startup event to clean temporary files"""
       if os.path.exists("temp"):
           try:
               shutil.rmtree("temp")
               os.makedirs("temp")
           except Exception as e:
               print(f"Warning: Could not clean temp directory: {e}")
   ```

### Common Anti-patterns to Avoid

1. **Hard-coded Values**:
   - Use configuration parameters instead of hard-coded values
   - Extract magic numbers to named variables or constants

2. **Excessive Method Length**:
   - Break down long methods into smaller, focused functions
   - Use private helper methods for implementation details

3. **Deeply Nested Logic**:
   - Limit nesting of if/for statements
   - Use early returns to reduce nesting

4. **Unclear Variable Names**:
   - Use descriptive variable names
   - Avoid abbreviations unless they are well-known

5. **Missing Error Handling**:
   - Add appropriate error handling for I/O operations
   - Provide fallbacks or graceful failures
