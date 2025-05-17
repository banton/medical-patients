#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

echo "🚀 Starting Development Environment for Medical Patients Data System..."
echo "--------------------------------------------------------------------"

# 1. Ensure frontend dependencies are installed
echo "📦 Step 1/4: Installing/updating frontend dependencies (npm install)..."
npm install
echo "✅ Frontend dependencies are up to date."
echo "--------------------------------------------------------------------"

# 2. Build all frontend assets
echo "🎨 Step 2/4: Building all frontend assets (npm run build:all-frontend)..."
npm run build:all-frontend
echo "✅ Frontend assets built successfully to static/dist/."
echo "--------------------------------------------------------------------"

# 3. Start Docker services using docker-compose.dev.yml
# The --build flag rebuilds images if Dockerfile or context changes.
# The -d flag runs containers in detached mode.
echo "🐳 Step 3/4: Starting Docker services (PostgreSQL, Backend via docker-compose.dev.yml)..."
docker compose -f docker-compose.dev.yml up --build -d
echo "✅ Docker services initiated. Waiting for backend service to be ready..."

RETRY_COUNT=0
# Wait for up to 2 minutes (24 * 5 seconds = 120 seconds)
MAX_RETRIES=24 

# Loop until 'docker compose ps app' shows the app service as "healthy"
# This relies on the healthcheck defined in docker-compose.dev.yml for the 'app' service.
while ! docker compose -f docker-compose.dev.yml ps app | grep -Eiq 'healthy'; do
    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        echo "❌ Error: App service (app) did not become healthy in time."
        echo "Current status of services:"
        docker compose -f docker-compose.dev.yml ps
        echo "Logs from app service:"
        docker compose -f docker-compose.dev.yml logs app
        echo "Logs from db service:"
        docker compose -f docker-compose.dev.yml logs db
        exit 1
    fi
    RETRY_COUNT=$((RETRY_COUNT+1))
    echo "App service not healthy yet (attempt $RETRY_COUNT/$MAX_RETRIES), waiting 5 seconds..."
    sleep 5
done

echo "✅ App service (app) is healthy."
echo "--------------------------------------------------------------------"

# 4. Apply database migrations
echo "🗄️ Step 4/4: Applying database migrations (Alembic)..."
# Ensure 'app' is the correct service name from docker-compose.dev.yml
docker compose -f docker-compose.dev.yml exec app alembic upgrade head
echo "✅ Database migrations applied."
echo "--------------------------------------------------------------------"

echo "🎉 Development environment is ready! 🎉"
echo ""
echo "🔗 FastAPI Backend available at: http://localhost:8000"
echo "📄 API Docs (Swagger UI):     http://localhost:8000/docs"
echo "📄 API Docs (ReDoc):          http://localhost:8000/redoc"
echo "🖥️ Main Application UI:       http://localhost:8000/static/index.html"
echo "📊 Advanced Visualizations:   http://localhost:8000/static/visualizations.html"
echo ""
echo "👉 To view logs for the app service:   docker compose -f docker-compose.dev.yml logs -f app"
echo "👉 To stop all development services:   docker compose -f docker-compose.dev.yml down"
echo "--------------------------------------------------------------------"
