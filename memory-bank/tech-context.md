# Tech Context

## Technologies Used

The Military Medical Exercise Patient Generator is built using modern web technologies and Python libraries, focusing on maintainability, standards compliance, and security.

### Programming Languages

1. **Python 3.8+**: Primary backend language
   - Type hints and modern Python features
   - Object-oriented design for the generator components
   - Used for all data generation, processing, and API logic

2. **JavaScript**: Frontend interactivity
   - AJAX for asynchronous communication with backend
   - DOM manipulation for dynamic UI updates
   - Chart rendering and form validation

3. **HTML/CSS**: Frontend structure and styling
   - Bootstrap 5 framework for responsive design
   - FontAwesome for iconography
   - Clean, modern interface

### Frameworks & Libraries

#### Backend

1. **FastAPI (0.100.0+)**:
   - Modern, high-performance web framework
   - Automatic API documentation
   - Background task support
   - Type validation with Pydantic

2. **Uvicorn (0.22.0+)**:
   - ASGI server for running the FastAPI application
   - High performance for async operations

3. **Cryptography (41.0.1+)**:
   - Secure encryption (AES-256-GCM)
   - Key derivation (PBKDF2)

4. **Dicttoxml (1.7.16+)**:
   - Dictionary to XML conversion for output formatting

5. **Faker (18.10.1+)**:
   - Realistic data generation
   - Localization support

6. **Pydantic (2.0.0+)**:
   - Data validation
   - Configuration management

7. **Additional Utilities**:
   - `aiofiles`: Async file operations
   - `python-multipart`: Form data handling
   - `psutil`: System resource monitoring

#### Frontend

1. **Bootstrap (5.3.0+)**:
   - Responsive grid layout
   - Form components
   - Card and alert components

2. **Chart.js**:
   - Interactive data visualizations
   - Pie charts for data distribution display

3. **FontAwesome (6.4.0+)**:
   - Icon library for improved UI

### Development Environment

1. **Required Tools**:
   - Python 3.8 or higher
   - Pip (Python package installer)
   - Git (for version control)
   - Virtual environment tool (venv, conda, etc.)

2. **Setup Process**:
   - Create and activate virtual environment
   - Install dependencies from `requirements.txt`
   - Install package in development mode with `pip install -e .`

3. **Testing**:
   - Python's `unittest` framework
   - Test modules in `tests.py`

### Deployment Options

1. **Local Development Server**:
   - Run with `python app.py`
   - Access via http://localhost:8000

2. **Production Deployment**:
   - Containerization possible (though not explicitly included)
   - Should be deployed behind reverse proxy for production
   - Background worker considerations for long-running tasks

### Technical Constraints

1. **Browser Compatibility**:
   - Modern browsers with ES6 support
   - Chart.js and Bootstrap 5 requirements

2. **Security Considerations**:
   - CORS configuration in FastAPI
   - Temporary file handling
   - Encryption password management

3. **Performance Factors**:
   - Memory usage for large patient generation
   - Background task management
   - File size considerations for downloads

### Dependencies

#### Python Package Dependencies

```
fastapi==0.100.0
uvicorn==0.22.0
python-multipart==0.0.6
pydantic>=2.0.0
cryptography==41.0.1
faker==18.10.1
dicttoxml==1.7.16
aiofiles==23.1.0
psutil>=7.0.0
```

#### Frontend Dependencies (CDN-loaded)

```
bootstrap@5.3.0
font-awesome@6.4.0
chart.js (latest)
```

### File Structure

```
military-patient-generator/
├── app.py                      # Main FastAPI application
├── requirements.txt            # Python dependencies
├── setup.py                    # Package setup
├── tests.py                    # Unit tests
├── demo.py                     # Demonstration script
├── static/                     # Static web files
│   └── index.html              # Single page interface
│
└── patient_generator/          # Core generation modules
    ├── __init__.py
    ├── app.py                  # PatientGeneratorApp
    ├── patient.py              # Patient class
    ├── flow_simulator.py       # Patient flow simulator
    ├── demographics.py         # Demographics generator
    ├── medical.py              # Medical condition generator
    ├── fhir_generator.py       # FHIR bundle generator
    └── formatter.py            # Output formatter
```

### Data Standards

1. **HL7 FHIR R4**: Primary medical data standard
2. **SNOMED CT**: Medical terminology for conditions and procedures
3. **LOINC**: Lab values and observations
4. **ISO3166**: Country codes
5. **ISO8601**: Date and time formatting
6. **NDEF**: NFC data exchange format
