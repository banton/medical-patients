# Build stage - for optimizing the final image size
FROM python:3.9-slim AS builder

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install dependencies into a wheel directory
RUN pip wheel --no-cache-dir --wheel-dir /app/wheels -r requirements.txt

# Final stage
FROM python:3.9-slim

# Create a non-root user to run the application
RUN groupadd -r patientgen && useradd -r -g patientgen patientgen

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    HOST="0.0.0.0" \
    PYTHONPATH="/app"

WORKDIR /app

# Copy wheels from builder stage
COPY --from=builder /app/wheels /wheels
# Install dependencies from wheels
RUN pip install --no-cache-dir --no-index --find-links=/wheels/ /wheels/* \
    && rm -rf /wheels

# Copy application code
COPY patient_generator/ /app/patient_generator/
COPY static/ /app/static/
COPY app.py /app/
COPY tests.py /app/
COPY setup.py /app/
COPY run_generator.py /app/

# Create directory for output files with proper permissions
RUN mkdir -p /app/output /app/temp \
    && chown -R patientgen:patientgen /app

# Switch to non-root user
USER patientgen

# Expose the port
EXPOSE 8000

# Default command to run the FastAPI application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
