# Developer Guide

This guide provides practical information for developers working on the Military Medical Exercise Patient Generator project, including key commands, SDK usage, coding conventions, and testing procedures relevant to the current architecture.

## 1. Development Environment Setup & Key Commands

Refer to `memory-bank/tech-context.md` for a detailed list of required tools and technologies.

### Primary Development Script: `start-dev.sh`

The `./start-dev.sh` script is the **recommended and most reliable way** to set up and start the complete development environment. It automates:
1.  `npm install`: Installs/updates frontend Node.js dependencies.
2.  `npm run build:all-frontend`: Builds all React/TSX frontend components (`ConfigurationPanel`, `ExerciseDashboard`, `MilitaryMedicalDashboard`) into their respective JavaScript bundles in `static/dist/`.
3.  `docker compose -f docker-compose.dev.yml up --build -d`: Starts the Docker services (FastAPI `app` service, PostgreSQL `db` service) in detached mode.
4.  **Health Check Wait**: Waits for the `app` service (FastAPI backend) to report as "healthy" via its Docker healthcheck.
5.  `docker compose -f docker-compose.dev.yml exec app alembic upgrade head`: Applies any pending database migrations to the PostgreSQL database within the `db` Docker container.

**Usage**:
```bash
chmod +x start-dev.sh  # If not already executable
./start-dev.sh
```
*   Backend API will be accessible at `http://localhost:8000` (or as mapped by Docker).
*   Main UI shell: `http://localhost:8000/static/index.html`.
*   Enhanced Visualizations: `http://localhost:8000/static/visualizations.html`.

### Other Useful Docker Compose Commands (using `docker-compose.dev.yml`)

*   **View Logs**:
    ```bash
    docker compose -f docker-compose.dev.yml logs -f app  # For FastAPI app logs
    docker compose -f docker-compose.dev.yml logs -f db   # For PostgreSQL logs
    ```
*   **Stop Services**:
    ```bash
    docker compose -f docker-compose.dev.yml down
    ```
*   **Access Shell in `app` Container**:
    ```bash
    docker compose -f docker-compose.dev.yml exec app /bin/bash
    ```
*   **Rebuild Services**:
    ```bash
    docker compose -f docker-compose.dev.yml up --build -d
    ```

### Frontend Development (Node.js/npm)

Managed via `package.json`.
*   **Install Dependencies**:
    ```bash
    npm install
    ```
*   **Build All Frontend Components**:
    ```bash
    npm run build:all-frontend
    ```
    (This runs `build:viz-dashboard`, `build:config-panel`, and `build:military-dashboard` scripts)
*   **Build Individual Components**:
    ```bash
    npm run build:viz-dashboard
    npm run build:config-panel
    npm run build:military-dashboard
    ```
*   **Run Frontend Tests (Jest)**:
    ```bash
    npm test
    ```
    (Tests `.tsx` files using configuration in `jest.config.js`, `tsconfig.json`, `setupTests.ts`)

### Database Migrations (Alembic)

Managed via commands executed *inside* the `app` Docker container (or locally if running Python environment directly with DB access).
*   **Create a New Migration (after changing SQLAlchemy models in `patient_generator/models_db.py`)**:
    ```bash
    # Inside app container or with local venv activated:
    alembic revision -m "your_descriptive_migration_message"
    ```
    Then edit the generated migration script in `alembic_migrations/versions/`.
*   **Apply Migrations**:
    ```bash
    # Inside app container or with local venv activated:
    alembic upgrade head
    ```
    (The `start-dev.sh` script does this automatically).
*   **Check Current DB Revision**:
    ```bash
    alembic current
    ```
*   **View Migration History**:
    ```bash
    alembic history
    ```

## 2. Python SDK Usage (`patient_generator_sdk.py`)

The `patient_generator_sdk.py` provides a `PatientGeneratorClient` class for programmatic interaction with the backend API.

**Example Usage (Conceptual - refer to SDK file for exact methods)**:
```python
from patient_generator_sdk import PatientGeneratorClient
import os

# API Key should be securely managed, e.g., via environment variable
API_KEY = os.environ.get("PATIENT_GENERATOR_API_KEY", "testapikey") # Default for local dev
BASE_URL = "http://localhost:8000/api/v1"

client = PatientGeneratorClient(base_url=BASE_URL, api_key=API_KEY)

# --- Configuration Management ---
# Create a new configuration
new_config_payload = {
    "name": "SDK Test Scenario",
    "description": "A scenario created via SDK for testing.",
    "version": 1,
    # ... other detailed configuration parameters for fronts, facilities, etc.
    # (Refer to patient_generator.schemas_config for the full structure)
}
try:
    created_config = client.create_configuration(new_config_payload)
    config_id = created_config["id"]
    print(f"Created configuration with ID: {config_id}")

    # Get a configuration
    retrieved_config = client.get_configuration(config_id)
    print(f"Retrieved configuration: {retrieved_config['name']}")

    # List configurations
    configs = client.list_configurations()
    print(f"Found {len(configs)} configurations.")

    # Update a configuration
    update_payload = {"description": "Updated description via SDK."}
    updated_config = client.update_configuration(config_id, update_payload)
    print(f"Updated config description: {updated_config['description']}")

except Exception as e:
    print(f"Error during configuration management: {e}")


# --- Patient Generation ---
if 'config_id' in locals(): # Check if config_id was successfully created
    generation_payload = {
        "configuration_id": config_id,
        # Can also pass an ad-hoc configuration object directly
        # "configuration": { ... detailed config ... }
    }
    try:
        job_submission_response = client.submit_generation_job(generation_payload)
        job_id = job_submission_response["job_id"]
        print(f"Submitted generation job with ID: {job_id}")

        # Poll for job status
        import time
        while True:
            status_response = client.get_job_status(job_id)
            print(f"Job Status: {status_response['status']}, Progress: {status_response.get('progress', 0)}%")
            if status_response["status"] in ["completed", "failed"]:
                break
            time.sleep(5)

        if status_response["status"] == "completed":
            print("Job completed successfully.")
            # Download results (SDK might need a dedicated download method or provide URL)
            # For example, if client.download_job_results(job_id, "results.zip") exists:
            # client.download_job_results(job_id, "results.zip")
            # print("Results downloaded to results.zip")
            results_url = f"{BASE_URL}/jobs/{job_id}/download" # Construct download URL
            print(f"Download results from: {results_url}")
            print(f"Job summary: {status_response.get('summary')}")
        else:
            print(f"Job failed. Details: {status_response.get('error_message', 'No details')}")

    except Exception as e:
        print(f"Error during patient generation: {e}")

# --- Reference Data ---
try:
    nationalities = client.get_nationalities()
    print(f"Available nationalities: {nationalities}")
except Exception as e:
    print(f"Error fetching nationalities: {e}")
```
*   **Note**: The SDK methods should align with the API endpoints defined in `app.py`. Ensure the SDK is kept up-to-date with API changes.

## 3. Core Coding Patterns & Conventions (Current Stack)

### Backend (Python, FastAPI, Pydantic, SQLAlchemy)

*   **FastAPI Endpoints (`app.py`)**:
    *   Use clear route decorators (`@app.get`, `@app.post`, etc.) with versioned paths (e.g., `/api/v1/...`).
    *   Employ Pydantic models for request body validation and response serialization. Define these in `app.py` or import from `patient_generator.schemas_config`.
    *   Use `async def` for endpoint functions.
    *   Utilize FastAPI's dependency injection for database sessions, `ConfigurationManager`, etc.
    *   Handle long-running tasks with `BackgroundTasks`.
    *   Return structured JSON responses, often using Pydantic `response_model`.
*   **Pydantic Models (`patient_generator/schemas_config.py`, `app.py`)**:
    *   Define clear, typed data structures for configurations, API requests, and API responses.
    *   Use `BaseModel` as the base for all Pydantic models.
    *   Employ validators for complex field validation if needed.
    *   Use `ConfigDict` (formerly `class Config`) for ORM mode, example generation, etc.
*   **SQLAlchemy Models (`patient_generator/models_db.py`)**:
    *   Define database table structures using SQLAlchemy's declarative base.
    *   Establish relationships (one-to-many, many-to-many) between models.
    *   Ensure models align with Pydantic schemas for easy conversion (ORM mode).
*   **Database Interactions (`patient_generator/database.py`)**:
    *   Use a Repository pattern (e.g., `ConfigurationRepository`) to encapsulate CRUD logic for specific entities.
    *   Interact with the database using SQLAlchemy sessions.
    *   Ensure database operations are efficient and secure (e.g., avoid N+1 query problems).
*   **Configuration Management (`patient_generator/config_manager.py`)**:
    *   The `ConfigurationManager` is responsible for loading, parsing, and providing validated configuration data to the generation engine. It fetches data from the `ConfigurationRepository`.
*   **General Python**:
    *   Follow PEP 8 style guidelines.
    *   Use type hints extensively.
    *   Organize imports: standard library, then third-party, then local application.
    *   Write clear docstrings for public classes, methods, and functions.
    *   Modular design: break down complex logic into smaller, manageable functions/classes.

### Frontend (React, TypeScript/TSX)

*   **Component Structure**:
    *   Use functional components with Hooks (`useState`, `useEffect`, `useContext`, etc.).
    *   Organize components into logical directories.
    *   Define props using TypeScript interfaces.
    *   Keep components focused on a single responsibility.
*   **State Management**:
    *   For local component state, use `useState`.
    *   For more complex or shared state, consider `useReducer` or React Context API. (Evaluate if a more robust state management library like Zustand or Redux Toolkit is needed if complexity grows significantly).
*   **API Interaction**:
    *   Use `fetch` API or a lightweight library like `axios` for making requests to the backend.
    *   Handle API responses asynchronously (async/await).
    *   Implement proper error handling and user feedback for API calls.
*   **Styling**:
    *   Leverage Bootstrap classes (loaded via CDN) for general layout and styling.
    *   For component-specific styles, consider CSS Modules or styled-components if needed, though current setup relies on Bootstrap.
*   **TypeScript**:
    *   Use strong typing for props, state, API responses, and function signatures.
    *   Define interfaces and types in relevant files or a shared `types.ts` if applicable.
*   **File Naming**:
    *   PascalCase for component files (e.g., `ConfigurationPanel.tsx`).
    *   camelCase or kebab-case for non-component TS/JS files.

## 4. Testing

### Backend Testing (`tests.py`, `unittest`)

*   Python's `unittest` framework is currently used. Consider migrating to `pytest` for more features and flexibility if desired.
*   Focus on testing:
    *   API endpoint logic (request validation, response structure, status codes). This often requires a test client like FastAPI's `TestClient`.
    *   Business logic in `patient_generator` modules (e.g., `ConfigurationManager`, individual generator components).
    *   Database interaction logic (CRUD operations in repositories).
*   Use mocking (`unittest.mock`) to isolate units and control dependencies.
*   Aim for good test coverage of critical paths and edge cases.
*   **Running Backend Tests**:
    ```bash
    # Typically run inside the app Docker container or a local venv
    python -m unittest tests.py
    ```
    (Or specific test discovery command if using pytest).

### Frontend Testing (Jest, React Testing Library)

*   Located in files like `enhanced-visualization-dashboard.test.tsx`.
*   Use Jest as the test runner and assertion library.
*   Use React Testing Library (`@testing-library/react`) for rendering components and interacting with them in a user-centric way.
*   Focus on testing component behavior from the user's perspective.
*   Mock API calls and other external dependencies.
*   **Running Frontend Tests**:
    ```bash
    npm test
    ```

### API Integration Tests (TST-001 - To be developed)

*   These will test the deployed API endpoints, likely using Python `requests` or `httpx` against a running instance of the application (potentially with a dedicated test database).

### End-to-End (E2E) Tests (TST-002 - To be developed)

*   These will use browser automation tools (e.g., Playwright, Cypress, Selenium) to test full user flows through the web interface.

## 5. Git Workflow

Refer to `memory-bank/git-workflow.md` for detailed branching, commit message, and PR guidelines.

This guide should be updated as development practices evolve.
