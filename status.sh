#!/bin/bash
echo "Medical Patients Generator - Service Status"
echo "==========================================="
echo ""

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
  echo "❌ Docker is not running"
  exit 1
fi

# Get container status
echo "Container Status:"
docker compose ps
echo ""

# Check for errors in logs
echo "Recent Errors (last 10 lines per service):"
echo "------------------------------------------"

# Check each service for errors
for service in db redis app; do
  if docker compose ps -q $service 2>/dev/null | grep -q .; then
    ERROR_COUNT=$(docker compose logs $service 2>/dev/null | tail -50 | grep -iE "error|exception|failed|fatal" | wc -l | tr -d ' ')
    if [ "$ERROR_COUNT" -gt 0 ]; then
      echo ""
      echo "⚠️  $service - Found $ERROR_COUNT errors:"
      docker compose logs $service 2>/dev/null | tail -50 | grep -iE "error|exception|failed|fatal" | tail -10
    else
      echo "✅ $service - No recent errors"
    fi
  else
    echo "⚠️  $service - Not running"
  fi
done

echo ""

# Check timeline viewer status
echo "Timeline Viewer Status:"
echo "----------------------"
if command -v lsof >/dev/null 2>&1; then
  PID=$(lsof -ti:5174 2>/dev/null)
  if [ -n "$PID" ]; then
    echo "✅ Timeline viewer running on http://localhost:5174 (PID: $PID)"
  else
    echo "❌ Timeline viewer not running"
  fi
else
  # Fallback check using curl
  if curl -s http://localhost:5174 >/dev/null 2>&1; then
    echo "✅ Timeline viewer running on http://localhost:5174"
  else
    echo "❌ Timeline viewer not running"
  fi
fi

echo ""
echo "Health Check URLs:"
echo "- App Health: http://localhost:8000/health"
echo "- API Docs:   http://localhost:8000/docs"
echo "- Main UI:    http://localhost:8000/static/index.html"
echo "- Timeline:   http://localhost:5174 (if running)"