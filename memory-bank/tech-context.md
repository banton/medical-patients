# Tech Context

## Technologies Used

The Military Medical Exercise Patient Generator is built using modern web technologies and Python libraries, focusing on maintainability, standards compliance, and security.

### Programming Languages

1. **Python 3.8+**: Primary backend language
   - Type hints and modern Python features
   - Object-oriented design for the generator components
   - Used for all data generation, processing, and API logic

2. **JavaScript/TypeScript (TSX)**: Frontend interactivity and component development.
   - React components like `enhanced-visualization-dashboard.tsx`, `ConfigurationPanel.tsx`, and `MilitaryMedicalDashboard.tsx` are written in TSX (TypeScript + JSX).
   - Asynchronous communication with the backend API (e.g., using `fetch`).
   - DOM manipulation for dynamic UI updates, largely managed by React.
   - Advanced charting, complex form interactions, and state management within React components.

3. **HTML/CSS**: Frontend structure and styling
   - Bootstrap 5 framework for responsive design
   - FontAwesome for iconography
   - Clean, modern interface

### Frameworks & Libraries

#### Backend

1. **FastAPI (0.100.0+)**:
   - Modern, high-performance web framework
   - Automatic API documentation (OpenAPI/Swagger)
   - Background task support for patient generation
   - Type validation with Pydantic
   - Dependency injection system
   - Async/await support throughout

2. **Uvicorn (0.22.0+)**:
   - ASGI server for running the FastAPI application
   - High performance for async operations
   - Auto-reload in development mode

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

7. **Database & Migration**:
   - **`psycopg2-binary`**: PostgreSQL adapter for Python.
   - **`alembic`**: Database migration tool for managing PostgreSQL schema changes.
   - **`SQLAlchemy`**: Core ORM and SQL toolkit, often used with Alembic and for interacting with PostgreSQL (used for model definitions in `models_db.py` and by Alembic).
8. **API Interaction**:
    - **`requests`**: HTTP library, used by the Python SDK (`patient_generator_sdk.py`).
9. **Additional Utilities**:
   - `aiofiles`: Async file operations.
   - `python-multipart`: Form data handling.
   - `psutil`: System resource monitoring.

#### Frontend

1.  **React (19.1.0+)**: Core library for building user interfaces, used for `enhanced-visualization-dashboard.tsx`, `ConfigurationPanel.tsx`, `MilitaryMedicalDashboard.tsx`, and their sub-components (e.g., `FrontEditor.tsx`, `FacilityEditor.tsx`).
2.  **Recharts (2.15.3+)**: Used for rendering complex charts in the enhanced visualization dashboard.
3.  **Lucide-React (0.510.0+)**: For icons within the React components.
4.  **Bootstrap (5.3.0+)**: Used for overall styling and layout, loaded via CDN in HTML.
5.  **FontAwesome (6.4.0+)**: Used for iconography, loaded via CDN in HTML.
6.  **Testing Library (`@testing-library/react`, `@testing-library/jest-dom`)**: For testing React components.
7.  **Chart.js**: Previously used in `static/index.html`. This page now links to `static/visualizations.html` (which uses Recharts via `enhanced-visualization-dashboard.tsx`) for comprehensive graphical visualizations. Chart.js is not an active rendering dependency for `static/index.html`.

### Development Environment

1. **Required Tools**:
   - Python 3.8 or higher
   - Pip (Python package installer)
   - **PostgreSQL**: Database server.
   - **Alembic**: CLI tool for managing database schema migrations.
   - Node.js and npm (for frontend dependencies, testing, and building)
   - Git (for version control)
   - Virtual environment tool for Python (venv, conda, etc.)
   - `esbuild` (for building frontend React components).
   - Docker and Docker Compose (for containerized development environment).

2. **Setup Process**:
   - **Backend & Database**:
     - Primarily managed via Docker Compose (`docker-compose.dev.yml`).
     - `requirements.txt` lists Python dependencies.
     - Alembic (`alembic.ini`, `alembic_migrations/`) manages DB schema.
   - **Frontend**:
     - `package.json` manages Node.js dependencies and build scripts.
     - Install Node.js dependencies: `npm install`.
     - Build all frontend components: `npm run build:all-frontend`.
     - Individual components can be built using:
        - `npm run build:viz-dashboard`
        - `npm run build:config-panel`
        - `npm run build:military-dashboard`

3. **Running the Development Environment**:
   - A convenience script `start-dev.sh` is provided to automate the setup:
     - Installs/updates frontend dependencies (`npm install`).
     - Builds all frontend assets (`npm run build:all-frontend`).
     - Starts Docker services using `docker-compose.dev.yml` (`docker compose -f docker-compose.dev.yml up --build -d`). This includes the FastAPI application (`app` service) and PostgreSQL (`db` service).
     - Waits for the `app` service (the FastAPI backend) to report as "healthy" (leveraging its defined healthcheck) before proceeding.
     - Applies database migrations (`docker compose -f docker-compose.dev.yml exec app alembic upgrade head`). The `alembic_migrations/env.py` script has been updated to prioritize the `DATABASE_URL` environment variable (pointing to the `db` service) when running inside Docker, resolving potential connection issues.
   - To run: `./start-dev.sh` (ensure it's executable: `chmod +x start-dev.sh`).
   - This script simplifies starting the application, database, and ensuring frontend assets are built, and includes a robust wait mechanism for service readiness before running migrations.
   - Backend (FastAPI) accessible at: `http://localhost:8000` (or as mapped by Docker).
   - Main UI: `http://localhost:8000/static/index.html`.

4. **Testing**:
   - **Backend**: Python's `unittest` framework. Run with `python -m unittest tests.py` (or similar, potentially executed within the Docker container).
   - **Frontend**: Jest with `ts-jest` for `.tsx` files. Run with `npm test`.
     - Configuration files: `jest.config.js`, `tsconfig.json`, `setupTests.ts`.

### Deployment Options

1. **Local Development Server (using `start-dev.sh` & Docker)**:
   - The `start-dev.sh` script handles starting the Dockerized environment.
   - FastAPI application and PostgreSQL database run in Docker containers.
   - Backend (FastAPI) accessible at: `http://localhost:8000` (or configured port).
   - Main UI: `http://localhost:8000/static/index.html`.
   - For manual server start (without Docker, if Python environment and DB are set up separately):
     - Ensure frontend assets are built (`npm run build:all-frontend`).
     - Run backend: `uvicorn app:app --reload` (or `python app.py` if it uses Uvicorn internally).

2. **Production Deployment**:
   - Containerization possible (though not explicitly included)
   - Should be deployed behind reverse proxy for production
   - Background worker considerations for long-running tasks

### Architecture Updates (Post-Modularization)

The application has been refactored from a monolithic structure to a clean, domain-driven architecture:

1. **Modular Structure**:
   - `src/main.py`: Application entry point (replaces monolithic `app.py`)
   - `src/core/`: Core utilities (exceptions, security)
   - `src/domain/`: Business domain layer (models, services, repositories)
   - `src/api/v1/`: API endpoints organized by domain
   - `patient_generator/`: Core generation logic remains separate

2. **Key Improvements**:
   - Separation of concerns with clear layer boundaries
   - Dependency injection for better testability
   - Repository pattern for data access
   - Service layer for business logic
   - Proper exception hierarchy
   - Environment-based configuration

3. **Running the Modular Application**:
   ```bash
   # Set PYTHONPATH for proper imports
   export PYTHONPATH=/path/to/medical-patients
   
   # Run the application
   python src/main.py
   ```

### Technical Constraints

1. **Browser Compatibility**:
   - Modern browsers with ES6 support.
   - Bootstrap 5 requirements for styling.
   - Recharts (via React components) for advanced visualizations.

2. **Security Considerations**:
   - CORS configuration in FastAPI
   - Temporary file handling
   - Encryption password management (fixed salt vulnerability has been addressed with unique salts per encryption using PBKDF2).
   - Potential for SQL injection in database queries if not consistently parameterized (applies to PostgreSQL).

3. **Performance Factors**:
   - **Memory Management**: Critical for large patient generation. Addressed in part by Phase 1 refactoring, but ongoing vigilance needed.
   - **Background Task Management**: Efficient handling of long-running generation jobs.
   - **Frontend Bundle Sizes**: Bundles for `enhanced-visualization-dashboard.tsx`, `ConfigurationPanel.tsx`, and `MilitaryMedicalDashboard.tsx` need monitoring and potential optimization (e.g., code splitting, externalizing libraries).
   - **Database Performance**: Query optimization and efficient connection pooling for PostgreSQL.
   - **Error Handling**: Inconsistent error handling can impact perceived performance and reliability.
   - **File Size Considerations**: For downloads, especially with multiple formats and large patient counts.

### Dependencies

#### Python Package Dependencies (to be updated)

The `requirements.txt` will need to be updated to include `psycopg2-binary` and `alembic`. `sqlalchemy` might also be added.
Current (example, will change):
```
fastapi>=0.100.0
uvicorn>=0.22.0
python-multipart>=0.0.6
pydantic>=2.0.0 # Crucial for API models and configuration schemas
cryptography>=41.0.1
faker>=18.10.1
dicttoxml>=1.7.16
aiofiles>=23.1.0
psutil>=7.0.0
psycopg2-binary # PostgreSQL adapter
alembic # Database migrations
sqlalchemy # ORM and SQL toolkit, used with Alembic and models
requests # For Python SDK HTTP calls
# Other specific versions as per requirements.txt
```

#### Frontend Dependencies (npm packages from `package.json`)

Key dependencies for the enhanced visualization dashboard:
- `react`
- `react-dom`
- `recharts`
- `lucide-react`
- `@testing-library/react`
- `@testing-library/jest-dom`
- `ts-jest` (dev)
- `jest` (implied by `ts-jest`, often a direct dev dependency)
- `jest-environment-jsdom` (dev)
- `@types/react`, `@types/jest` (dev)
- `esbuild` (dev)

Bootstrap and FontAwesome are still loaded via CDN in `visualizations.html` and `index.html`.

### File Structure

```
military-patient-generator/
├── .clinerules                         # Cline's project intelligence
├── .dockerignore                       # Specifies files to ignore for Docker builds
├── .gitignore                          # Specifies intentionally untracked files for Git
├── alembic.ini                         # Configuration file for Alembic
├── app.py                              # Main FastAPI application entry point
├── ConfigurationPanel.tsx              # React component for advanced configuration UI
├── FacilityEditor.tsx                  # React sub-component for facility editing
├── FrontEditor.tsx                     # React sub-component for front editing
├── MilitaryMedicalDashboard.tsx        # React component for a specialized dashboard
├── Dockerfile                          # Instructions for building the application Docker image
├── docker-compose.*.yml                # Docker Compose files for different environments
├── enhanced-visualization-dashboard.tsx  # React component for general visualizations
├── enhanced-visualization-dashboard.test.tsx # Tests for visualization dashboard
├── jest.config.js                      # Jest test runner configuration
├── package.json                        # Frontend Node.js dependencies & scripts
├── package-lock.json                   # Frontend dependency lock file
├── patient_generator_sdk.py            # Python SDK for interacting with the API
├── README.md                           # Main project README
├── requirements.txt                    # Python dependencies
├── setup.py                            # Python package setup (for `patient_generator` module)
├── setupTests.ts                       # Jest setup file (e.g., for mocks)
├── start-dev.sh                        # Script to start the development environment
├── tests.py                            # Python backend unit tests
├── tsconfig.json                       # TypeScript configuration
│
├── alembic_migrations/                 # Alembic migration scripts
│   ├── versions/                       # Individual migration files
│   ├── env.py                          # Alembic environment setup
│   └── script.py.mako                  # Alembic script template
│
├── patient_generator/                  # Core Python patient generation module
│   ├── __init__.py
│   ├── app.py                          # Contains PatientGeneratorApp class (distinct from root app.py)
│   ├── config_manager.py               # Manages loading and providing configurations
│   ├── database.py                     # Database interaction logic (PostgreSQL, ConfigurationRepository)
│   ├── demographics.py                 # Demographics generator
│   ├── fhir_generator.py               # FHIR bundle generator
│   ├── flow_simulator.py               # Patient flow simulator
│   ├── formatter.py                    # Output formatter
│   ├── medical.py                      # Medical condition generator
│   ├── models_db.py                    # SQLAlchemy database models
│   ├── patient.py                      # Patient class
│   └── schemas_config.py               # Pydantic schemas for configuration objects
│
├── static/                             # Static web files served by FastAPI
│   ├── index.html                      # Main HTML page for generator (hosts ConfigurationPanel)
│   ├── visualizations.html             # HTML page for enhanced visualization dashboard
│   └── dist/                           # Compiled frontend JavaScript bundles
│       ├── bundle.js                   # For enhanced-visualization-dashboard.tsx
│       ├── configuration-panel.js      # For ConfigurationPanel.tsx
│       └── military-dashboard.js       # For MilitaryMedicalDashboard.tsx (if applicable)
│
└── node_modules/                       # Frontend Node.js packages (usually in .gitignore)
```

### Data Standards

1. **HL7 FHIR R4**: Primary medical data standard
2. **SNOMED CT**: Medical terminology for conditions and procedures
3. **LOINC**: Lab values and observations
4. **ISO3166**: Country codes
5. **ISO8601**: Date and time formatting
6. **NDEF**: NFC data exchange format
