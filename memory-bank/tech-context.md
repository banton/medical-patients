# Tech Context

## Technologies Used

The Military Medical Exercise Patient Generator is built using modern web technologies and Python libraries, focusing on maintainability, standards compliance, and security.

### Programming Languages

1. **Python 3.8+**: Primary backend language
   - Type hints and modern Python features
   - Object-oriented design for the generator components
   - Used for all data generation, processing, and API logic

2. **JavaScript/TypeScript (TSX)**: Frontend interactivity and component development.
   - `enhanced-visualization-dashboard.tsx` is written in TSX (TypeScript + JSX).
   - AJAX for asynchronous communication with backend.
   - DOM manipulation for dynamic UI updates.
   - Chart rendering and form validation.

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
   - **`psycopg2-binary`**: PostgreSQL adapter for Python (will be added to `requirements.txt`).
   - **`alembic`**: Database migration tool (will be added to `requirements.txt`).
   - `sqlalchemy`: Often used with Alembic and for ORM capabilities with PostgreSQL (may be added).

#### Frontend

1.  **React (19.1.0+)**: For building the user interface, specifically the enhanced visualization dashboard.
2.  **Recharts (2.15.3+)**: Used for rendering complex charts in the enhanced visualization dashboard.
3.  **Lucide-React (0.510.0+)**: For icons within the React components.
4.  **Bootstrap (5.3.0+)**: Used for overall styling and layout, loaded via CDN in HTML.
5.  **FontAwesome (6.4.0+)**: Used for iconography, loaded via CDN in HTML.
6.  **Testing Library (`@testing-library/react`, `@testing-library/jest-dom`)**: For testing React components.

### Development Environment

1. **Required Tools**:
   - Python 3.8 or higher
   - Pip (Python package installer)
   - **PostgreSQL**: Database server.
   - **Alembic**: For managing database schema migrations.
   - Node.js and npm (for frontend dependencies, testing, and building)
   - Git (for version control)
   - Virtual environment tool for Python (venv, conda, etc.)
   - `esbuild` (for building the frontend dashboard component)

2. **Setup Process**:
   - **Backend**:
     - Create and activate Python virtual environment.
     - Install Python dependencies: `pip install -r requirements.txt`.
     - Install package in development mode: `pip install -e .` (if applicable).
   - **Frontend (for enhanced visualization dashboard)**:
     - Install Node.js dependencies: `npm install`.
     - Build the dashboard component: `npm run build:viz-dashboard`. (Note: `npm run build` was the old command for only this component).
     - To build all frontend components (visualization dashboard, configuration panel, military dashboard), use: `npm run build:all-frontend`.

3. **Running the Development Environment**:
   - A convenience script `start-dev.sh` is provided to automate the setup:
     - Installs/updates frontend dependencies (`npm install`).
     - Builds all frontend assets (`npm run build:all-frontend`).
     - Starts Docker services using `docker-compose.dev.yml` (`docker compose -f docker-compose.dev.yml up --build -d`).
     - Waits for the `app` service (the FastAPI backend) to report as "healthy" (leveraging its defined healthcheck) before proceeding.
     - Applies database migrations (`docker compose -f docker-compose.dev.yml exec app alembic upgrade head`). The `alembic_migrations/env.py` script has been updated to prioritize the `DATABASE_URL` environment variable (pointing to the `db` service) when running inside Docker, resolving potential connection issues.
   - To run: `./start-dev.sh` (ensure it's executable: `chmod +x start-dev.sh`).
   - This script simplifies starting the application, database, and ensuring frontend assets are built, and includes a robust wait mechanism for service readiness before running migrations.

4. **Testing**:
   - **Backend**: Python's `unittest` framework. Run with `python -m unittest tests.py` (or similar).
   - **Frontend**: Jest with `ts-jest` for `.tsx` files. Run with `npm test`.
     - Configuration files: `jest.config.js`, `tsconfig.json`, `setupTests.ts`.

### Deployment Options

1. **Local Development Server (using `start-dev.sh`)**:
   - The `start-dev.sh` script handles starting the Dockerized environment.
   - Backend (FastAPI) accessible at: `http://localhost:8000`
   - Main UI: `http://localhost:8000/static/index.html`
   - For manual server start (without Docker, if Python environment and DB are set up separately):
     - Ensure frontend assets are built (`npm run build:all-frontend`).
     - Run backend: `uvicorn app:app --reload` (or `python app.py` if it uses Uvicorn internally).

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
   - Encryption password management (fixed salt identified as a vulnerability).
   - Potential for SQL injection in database queries if not consistently parameterized (applies to PostgreSQL as well).

3. **Performance Factors**:
   - **Memory Management**: Critical for large patient generation (both backend Python processes and FHIR bundle creation). In-memory storage of patient data and job data needs optimization.
   - **Background Task Management**: Efficient handling of long-running generation jobs.
   - **Frontend Bundle Size**: The `enhanced-visualization-dashboard.tsx` bundle (`static/dist/bundle.js`) size is a concern (~2.1MB) and needs optimization (e.g., externalizing libraries, code splitting).
   - **Database Performance**: Query optimization and connection pooling for **PostgreSQL**.
   - **Error Handling**: Inconsistent error handling can impact perceived performance and reliability.
   - **File Size Considerations**: For downloads, especially with multiple formats and large patient counts.

### Dependencies

#### Python Package Dependencies (to be updated)

The `requirements.txt` will need to be updated to include `psycopg2-binary` and `alembic`. `sqlalchemy` might also be added.
Current (example, will change):
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
# psycopg2-binary (to be added)
# alembic (to be added)
# sqlalchemy (potentially to be added)
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
├── app.py                                # Main FastAPI application
├── requirements.txt                    # Python dependencies
├── package.json                        # Frontend Node.js dependencies & scripts (includes `build:all-frontend`)
├── package-lock.json                 # Frontend dependency lock file
├── start-dev.sh                        # Development environment startup script
├── jest.config.js                      # Jest test runner configuration
├── tsconfig.json                       # TypeScript configuration
├── setupTests.ts                       # Jest setup file (e.g., for mocks)
├── enhanced-visualization-dashboard.tsx  # React TSX component for advanced visualizations
├── enhanced-visualization-dashboard.test.tsx # Jest tests for the TSX component
├── setup.py                            # Python package setup
├── tests.py                            # Python unit tests
├── demo.py                             # Demonstration script
├── static/                             # Static web files
│   ├── index.html                    # Main HTML page for generator
│   ├── visualizations.html           # HTML page for advanced visualizations
│   └── dist/
│       └── bundle.js                 # Compiled JavaScript for enhanced dashboard
│   └── js/
│       └── visualization-dashboard.js # Older JS dashboard (if still used)
│
├── patient_generator/                  # Core Python generation modules
│   ├── __init__.py
│   ├── app.py                          # PatientGeneratorApp
│   ├── database.py                     # Database interaction (migrating to PostgreSQL)
│   ├── patient.py                      # Patient class
│   ├── flow_simulator.py               # Patient flow simulator
│   ├── demographics.py                 # Demographics generator
│   ├── medical.py                      # Medical condition generator
│   ├── fhir_generator.py               # FHIR bundle generator
│   └── formatter.py                    # Output formatter
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
