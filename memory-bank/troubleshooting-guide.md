# Troubleshooting Guide

This document provides solutions to common issues that might be encountered when developing or running the Military Medical Exercise Patient Generator with its current architecture (PostgreSQL, FastAPI, Docker, React).

## 1. Development Environment & Docker Issues

### Issue: `start-dev.sh` script fails.
*   **Symptom**: Script exits prematurely, Docker containers don't start, or migrations fail.
*   **Solutions**:
    1.  **Permissions**: Ensure the script is executable: `chmod +x start-dev.sh`.
    2.  **Docker Not Running**: Verify Docker Desktop or Docker Engine is running.
    3.  **Port Conflicts**: Check if port 8000 (FastAPI) or 5432 (PostgreSQL) are already in use by other applications.
        *   Use `docker compose -f docker-compose.dev.yml logs app` and `docker compose -f docker-compose.dev.yml logs db` to check for port binding errors.
        *   Modify ports in `docker-compose.dev.yml` if necessary.
    4.  **Build Failures**: If `docker compose ... --build` fails:
        *   Check `Dockerfile` for errors.
        *   Ensure network connectivity for downloading base images or dependencies.
        *   Look for errors in the build output (e.g., `npm install` failures within Docker).
    5.  **Migration Failures**: If Alembic migrations fail (check `start-dev.sh` output or `app` container logs):
        *   Ensure the `db` container (PostgreSQL) started successfully and is healthy before migrations attempt to run. The `start-dev.sh` script has a health check for the `app` service, which depends on `db`.
        *   Inspect the failing migration script in `alembic_migrations/versions/` for SQL errors or incorrect logic.
        *   Check `alembic.ini` and `alembic_migrations/env.py` for correct database connection URLs, especially `DATABASE_URL` environment variable usage within Docker.
    6.  **`npm install` or `npm run build:all-frontend` failures**:
        *   Check `package.json` for valid dependencies.
        *   Ensure Node.js and npm are installed correctly on your host if these steps are run before Docker, or that the Node.js version in the Dockerfile (if frontend build happens in Docker) is compatible.
        *   Look for specific error messages from npm.

### Issue: FastAPI application (`app` service) fails to start or is unhealthy.
*   **Symptom**: `docker compose -f docker-compose.dev.yml ps` shows `app` service as unhealthy, restarting, or exited. Logs show errors.
*   **Solutions**:
    1.  **Check Logs**: `docker compose -f docker-compose.dev.yml logs -f app`.
    2.  **Python Errors**: Look for Python tracebacks (e.g., import errors, syntax errors in `app.py` or `patient_generator/` modules).
    3.  **Database Connection**: Ensure `app` can connect to the `db` service.
        *   Verify `DATABASE_URL` in `docker-compose.dev.yml` is correct (e.g., `postgresql://user:password@db:5432/patient_generator_db`).
        *   Check `db` service logs: `docker compose -f docker-compose.dev.yml logs -f db`.
    4.  **Pydantic Model Errors**: Invalid Pydantic model definitions in `schemas_config.py` or `app.py` can prevent FastAPI from starting.
    5.  **Alembic `env.py`**: If `env.py` has issues connecting to the DB for migrations, it might prevent the app from starting if migrations are run at startup.

### Issue: Cannot connect to PostgreSQL (`db` service).
*   **Symptom**: `app` service logs show connection errors to PostgreSQL. Unable to connect using a DB client.
*   **Solutions**:
    1.  **DB Service Running**: `docker compose -f docker-compose.dev.yml ps` should show `db` service as up and running.
    2.  **DB Logs**: `docker compose -f docker-compose.dev.yml logs -f db` for PostgreSQL errors.
    3.  **Credentials**: Verify username, password, database name in `DATABASE_URL` (used by `app` and Alembic) match those in `docker-compose.dev.yml` for the `db` service environment variables.
    4.  **Port Mapping**: If connecting from host, ensure port 5432 is correctly mapped in `docker-compose.dev.yml` (e.g., `ports: "5433:5432"` would mean connect to host port 5433).

## 2. API & Backend Issues (FastAPI)

### Issue: API endpoint returns 404 Not Found.
*   **Solutions**:
    1.  **URL Typo**: Double-check the request URL, including version prefix (e.g., `/api/v1/...`).
    2.  **Route Definition**: Ensure the route is correctly defined in `app.py` with the appropriate decorator (`@app.get`, `@app.post`, etc.) and path.
    3.  **Server Running**: Verify the FastAPI server (`app` service) is running.

### Issue: API endpoint returns 422 Unprocessable Entity.
*   **Symptom**: Usually indicates request validation failure by Pydantic.
*   **Solutions**:
    1.  **Check Request Body**: Ensure the JSON payload matches the Pydantic model defined for the endpoint (e.g., in `schemas_config.py` or `app.py`).
    2.  **Data Types**: Verify all fields have the correct data types.
    3.  **Required Fields**: Ensure all mandatory fields are present in the request.
    4.  **FastAPI Docs**: Check the auto-generated API docs (`http://localhost:8000/docs`) for the expected request schema.

### Issue: API endpoint returns 500 Internal Server Error.
*   **Symptom**: An unhandled exception occurred in the backend.
*   **Solutions**:
    1.  **Check `app` Logs**: `docker compose -f docker-compose.dev.yml logs -f app`. Look for Python tracebacks. This is the most important step.
    2.  **Debugging**: Add print statements or use a debugger in the relevant backend code path.
    3.  **Database Issues**: Could be due to database errors (e.g., constraint violations, connection problems). Check `db` logs.
    4.  **Logic Errors**: Bugs in the endpoint handler, service layer, or generation logic.

### Issue: Patient generation job fails or gets stuck.
*   **Solutions**:
    1.  **Check `app` Logs**: Look for tracebacks during the background task execution.
    2.  **Configuration Issues**: The provided `configuration_id` or ad-hoc configuration might be invalid or cause errors in the `patient_generator` modules. Validate the configuration.
    3.  **Resource Limits**: Very large generation tasks might hit memory or CPU limits within the Docker container. Monitor `docker stats`.
    4.  **Infinite Loops/Deadlocks**: Rare, but possible in complex generation logic.

## 3. Frontend Issues (React, TSX)

### Issue: Frontend components don't load or display incorrectly.
*   **Symptom**: Blank page, JavaScript errors in browser console, UI elements missing or broken.
*   **Solutions**:
    1.  **Browser Console**: Open developer tools (F12) and check the console for JavaScript errors.
    2.  **Build Process**: Ensure `npm run build:all-frontend` (or individual build scripts) completed successfully. Check for errors during the `esbuild` process.
    3.  **Bundle Paths**: Verify `static/index.html` and `static/visualizations.html` correctly link to the JS bundles in `static/dist/` (e.g., `bundle.js`, `configuration-panel.js`).
    4.  **TypeScript Errors**: Check for TypeScript compilation errors during the build.
    5.  **React Errors**: Look for React-specific errors in the console (e.g., issues with props, state, hooks).

### Issue: API calls from frontend fail.
*   **Symptom**: Network errors in browser console, UI not updating with data from backend.
*   **Solutions**:
    1.  **Network Tab**: Use browser developer tools Network tab to inspect API requests and responses. Check status codes, request payloads, and response data.
    2.  **CORS Issues**: If frontend and backend are on different origins (not typical for this project's default setup but possible if deployed differently), ensure CORS is configured correctly in FastAPI.
    3.  **API Endpoint URL**: Verify the frontend is calling the correct API endpoint URLs.
    4.  **Backend Server**: Ensure the FastAPI server is running and accessible.
    5.  **API Key**: If the endpoint requires an API key, ensure the frontend is sending it correctly.

### Issue: Jest tests (`npm test`) fail.
*   **Solutions**:
    1.  **Test Output**: Examine the Jest output for specific error messages and failing test suites/cases.
    2.  **Component Rendering**: Ensure components render correctly with given props. Use `@testing-library/react`'s debug functions.
    3.  **Mocking**: Verify mocks for API calls, hooks, or child components are set up correctly.
    4.  **Async Operations**: Ensure tests correctly handle asynchronous operations (e.g., using `async/await` with `findBy*` queries from React Testing Library).
    5.  **Snapshot Mismatches**: If using snapshot tests, update snapshots (`npm test -- -u`) if changes are intentional.

## 4. Database & Migration Issues (PostgreSQL, Alembic)

### Issue: Alembic migration fails to apply.
*   **Symptom**: `alembic upgrade head` command fails.
*   **Solutions**:
    1.  **Error Message**: Carefully read the Alembic error output. It often points to SQL syntax errors, constraint violations, or issues with the migration script itself.
    2.  **Database Connection**: Ensure Alembic can connect to the database (check `alembic.ini` and `env.py`, especially `DATABASE_URL`).
    3.  **Manual Inspection**: Connect to the database using a client (e.g., `psql`, DBeaver, pgAdmin) and inspect the schema or data causing the issue.
    4.  **Conflicting Migrations / "Multiple Heads"**: If Alembic reports multiple heads, it means there's a divergence in migration history. This usually requires manual intervention to merge heads or choose one path. Consult Alembic documentation.
    5.  **Migration Script Logic**: Review the Python code in the failing migration script in `alembic_migrations/versions/`.

### Issue: Data inconsistency or unexpected data in the database.
*   **Solutions**:
    1.  **SQLAlchemy Models**: Verify `patient_generator/models_db.py` accurately reflects the intended schema.
    2.  **Pydantic Schemas**: Ensure `patient_generator/schemas_config.py` (used for API input/output) aligns with database models to prevent data mismatches.
    3.  **Repository Logic**: Check CRUD operations in `patient_generator/database.py` for correct data handling.
    4.  **Data Validation**: Implement or enhance Pydantic validators or database constraints if needed.

## 5. General Debugging Tips
*   **Read Logs Carefully**: Backend logs (`docker compose logs app`), frontend console logs, and build tool outputs are your first line of defense.
*   **Simplify**: Try to reproduce the issue with the simplest possible case or configuration.
*   **Divide and Conquer**: Isolate whether the problem is in the frontend, backend API, core generation logic, or database.
*   **Use `.clinerules`**: This file might contain project-specific intelligence or known quirks.
*   **Consult Memory Bank**: Files like `active-context.md`, `system-patterns.md`, and `tech-context.md` provide crucial context.
