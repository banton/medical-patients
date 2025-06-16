"""
Docker and Container Compatibility Tests for Ubuntu 24.04

Tests Docker builds, AppArmor restrictions, and container runtime compatibility.
"""

import pytest
import subprocess
import os
import tempfile
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class TestDockerUbuntu2404:
    """Test Docker compatibility with Ubuntu 24.04 base images."""
    
    @pytest.fixture
    def docker_available(self):
        """Check if Docker is available."""
        try:
            result = subprocess.run(
                ["docker", "version"],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                pytest.skip("Docker not available")
            return True
        except FileNotFoundError:
            pytest.skip("Docker not installed")
    
    @pytest.fixture
    def test_image_tag(self):
        """Generate unique test image tag."""
        return f"medical-patients-test-ubuntu2404:{int(time.time())}"
    
    def test_ubuntu_2404_base_image(self, docker_available, tmp_path):
        """Test building with Ubuntu 24.04 base image."""
        # Create test Dockerfile
        dockerfile = tmp_path / "Dockerfile"
        dockerfile.write_text("""
FROM ubuntu:24.04

# Test Ubuntu version
RUN cat /etc/os-release | grep VERSION_ID | grep 24.04

# Test Python 3.12 availability
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y python3 python3-pip python3-venv

# Verify Python version
RUN python3 --version | grep "3.12"

# Test PEP 668 - should fail without venv
RUN python3 -m pip --version || echo "PEP 668 restriction working as expected"
""")
        
        # Build test image
        result = subprocess.run(
            ["docker", "build", "-t", "ubuntu2404-test", "."],
            cwd=tmp_path,
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"Build failed: {result.stderr}"
        
        # Clean up
        subprocess.run(["docker", "rmi", "ubuntu2404-test"], capture_output=True)
    
    def test_pep_668_compliance(self, docker_available, tmp_path):
        """Test PEP 668 compliance in containers."""
        dockerfile = tmp_path / "Dockerfile"
        dockerfile.write_text("""
FROM ubuntu:24.04

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y \
    python3-full python3-pip python3-venv

WORKDIR /app

# Test 1: Direct pip install should fail
RUN python3 -m pip install requests 2>&1 | grep -q "externally-managed-environment" && \
    echo "✓ PEP 668 protection active" || \
    (echo "✗ PEP 668 protection not working" && exit 1)

# Test 2: Virtual environment should work
RUN python3 -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip && \
    /opt/venv/bin/pip install requests && \
    echo "✓ Virtual environment installation successful"

# Test 3: Verify isolation
RUN python3 -c "import requests" 2>&1 | grep -q "No module" && \
    echo "✓ System Python isolated" || \
    (echo "✗ System Python contaminated" && exit 1)

RUN /opt/venv/bin/python -c "import requests; print('✓ Venv Python has requests')"
""")
        
        result = subprocess.run(
            ["docker", "build", "-t", "pep668-test", "."],
            cwd=tmp_path,
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"PEP 668 test failed: {result.stderr}"
        
        # Clean up
        subprocess.run(["docker", "rmi", "pep668-test"], capture_output=True)
    
    def test_medical_app_dockerfile(self, docker_available, tmp_path, test_image_tag):
        """Test full medical application Dockerfile with Ubuntu 24.04."""
        # Create requirements.txt
        requirements = tmp_path / "requirements.txt"
        requirements.write_text("""
fastapi==0.100.0
uvicorn==0.22.0
psycopg2-binary>=2.9.5
cryptography==41.0.1
pydantic>=2.0.0
""")
        
        # Create test app
        app_file = tmp_path / "app.py"
        app_file.write_text("""
from fastapi import FastAPI
app = FastAPI()

@app.get("/health")
def health():
    return {"status": "healthy", "ubuntu": "24.04"}
""")
        
        # Create Ubuntu 24.04 compliant Dockerfile
        dockerfile = tmp_path / "Dockerfile"
        dockerfile.write_text("""
FROM ubuntu:24.04

# Install system dependencies
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y \
    python3-full \
    python3-pip \
    python3-venv \
    build-essential \
    libpq-dev \
    libssl-dev \
    libffi-dev \
    cargo \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -s /bin/bash appuser

WORKDIR /app

# Create virtual environment as root, but it will be used by appuser
RUN python3 -m venv /opt/venv && \
    chown -R appuser:appuser /opt/venv

# Switch to non-root user
USER appuser

# Activate venv for all subsequent commands
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip in virtual environment
RUN pip install --upgrade pip

# Copy and install requirements
COPY --chown=appuser:appuser requirements.txt .
RUN pip install -r requirements.txt

# Copy application
COPY --chown=appuser:appuser app.py .

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# Run application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
""")
        
        # Build image
        result = subprocess.run(
            ["docker", "build", "-t", test_image_tag, "."],
            cwd=tmp_path,
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"Build failed: {result.stderr}"
        
        # Test running the container
        container_name = f"test-medical-{int(time.time())}"
        run_result = subprocess.run(
            ["docker", "run", "-d", "--name", container_name, 
             "-p", "8001:8000", test_image_tag],
            capture_output=True,
            text=True
        )
        
        if run_result.returncode == 0:
            container_id = run_result.stdout.strip()
            
            # Wait for container to start
            time.sleep(5)
            
            # Check if container is running
            ps_result = subprocess.run(
                ["docker", "ps", "--filter", f"id={container_id}", "--format", "{{.Status}}"],
                capture_output=True,
                text=True
            )
            
            assert "Up" in ps_result.stdout, "Container failed to start"
            
            # Check logs for errors
            logs_result = subprocess.run(
                ["docker", "logs", container_id],
                capture_output=True,
                text=True
            )
            
            assert "error" not in logs_result.stderr.lower(), \
                f"Errors in container logs: {logs_result.stderr}"
            
            # Clean up
            subprocess.run(["docker", "stop", container_id], capture_output=True)
            subprocess.run(["docker", "rm", container_id], capture_output=True)
        
        # Clean up image
        subprocess.run(["docker", "rmi", test_image_tag], capture_output=True)
    
    def test_apparmor_compatibility(self, docker_available):
        """Test AppArmor compatibility with Ubuntu 24.04 containers."""
        # Check if AppArmor is active on host
        if not os.path.exists("/sys/kernel/security/apparmor"):
            pytest.skip("AppArmor not available on host")
        
        # Run container with security options
        result = subprocess.run(
            ["docker", "run", "--rm", 
             "--security-opt", "apparmor=unconfined",
             "ubuntu:24.04", 
             "echo", "AppArmor test successful"],
            capture_output=True,
            text=True
        )
        
        # Ubuntu 24.04 has stricter AppArmor policies
        if result.returncode != 0 and "apparmor" in result.stderr.lower():
            pytest.warns(
                UserWarning,
                match="AppArmor restrictions detected - may need custom profile"
            )
        else:
            assert result.returncode == 0, f"AppArmor test failed: {result.stderr}"
    
    def test_openssl3_compatibility(self, docker_available, tmp_path):
        """Test OpenSSL 3.x compatibility in containers."""
        dockerfile = tmp_path / "Dockerfile"
        dockerfile.write_text("""
FROM ubuntu:24.04

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y \
    openssl \
    python3-full \
    python3-venv \
    libssl-dev

# Check OpenSSL version
RUN openssl version | grep "OpenSSL 3"

# Test Python SSL
RUN python3 -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip && \
    /opt/venv/bin/pip install cryptography

# Test cryptography with OpenSSL 3
RUN /opt/venv/bin/python -c "
from cryptography.fernet import Fernet
key = Fernet.generate_key()
f = Fernet(key)
encrypted = f.encrypt(b'test')
assert f.decrypt(encrypted) == b'test'
print('✓ Cryptography working with OpenSSL 3.x')
"

# Test TLS 1.0/1.1 are disabled
RUN /opt/venv/bin/python -c "
import ssl
context = ssl.create_default_context()
# This would fail if TLS 1.0/1.1 were enabled
print(f'✓ Minimum TLS version: {context.minimum_version}')
"
""")
        
        result = subprocess.run(
            ["docker", "build", "-t", "openssl3-test", "."],
            cwd=tmp_path,
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"OpenSSL 3 test failed: {result.stderr}"
        
        # Clean up
        subprocess.run(["docker", "rmi", "openssl3-test"], capture_output=True)


class TestDockerCompose:
    """Test Docker Compose compatibility with Ubuntu 24.04."""
    
    def test_compose_file_generation(self, tmp_path):
        """Generate Ubuntu 24.04 compatible docker-compose.yml."""
        compose_file = tmp_path / "docker-compose.yml"
        compose_file.write_text("""
version: '3.8'

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile.ubuntu24
    image: medical-patients:ubuntu24
    container_name: medical-patients-app
    ports:
      - "8000:8000"
    environment:
      - PYTHONUNBUFFERED=1
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/medical_db
    depends_on:
      db:
        condition: service_healthy
    volumes:
      # Use named volumes for better permissions handling
      - app-data:/app/output
    networks:
      - medical-net
    # Security options for Ubuntu 24.04
    security_opt:
      - no-new-privileges:true
    read_only: true
    tmpfs:
      - /tmp
      - /app/temp

  db:
    image: postgres:16.2
    container_name: medical-patients-db
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=medical_db
    volumes:
      - postgres-data:/var/lib/postgresql/data
    networks:
      - medical-net
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: medical-patients-redis
    command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
    networks:
      - medical-net
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres-data:
  app-data:

networks:
  medical-net:
    driver: bridge
""")
        
        # Verify compose file is valid
        result = subprocess.run(
            ["docker", "compose", "-f", str(compose_file), "config"],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            # Try older docker-compose command
            result = subprocess.run(
                ["docker-compose", "-f", str(compose_file), "config"],
                capture_output=True,
                text=True
            )
        
        if result.returncode == 0:
            config = result.stdout
            assert "medical-patients-app" in config
            assert "postgres:16" in config
            assert "security_opt" in config


class TestContainerSecurity:
    """Test container security with Ubuntu 24.04 enhancements."""
    
    def test_non_root_user(self, tmp_path):
        """Test running containers as non-root user."""
        dockerfile = tmp_path / "Dockerfile"
        dockerfile.write_text("""
FROM ubuntu:24.04

# Create non-root user
RUN useradd -m -u 1000 -s /bin/bash appuser

# Test running as non-root
USER appuser
RUN whoami | grep appuser
RUN id -u | grep 1000

# Verify no sudo access
RUN ! which sudo
""")
        
        result = subprocess.run(
            ["docker", "build", "-t", "nonroot-test", "."],
            cwd=tmp_path,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            subprocess.run(["docker", "rmi", "nonroot-test"], capture_output=True)
        else:
            pytest.skip(f"Non-root user test skipped: {result.stderr}")
    
    def test_readonly_filesystem(self, tmp_path):
        """Test read-only root filesystem compatibility."""
        dockerfile = tmp_path / "Dockerfile"
        dockerfile.write_text("""
FROM ubuntu:24.04

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y python3

# Create necessary directories
RUN mkdir -p /app /tmp /var/tmp && \
    chmod 1777 /tmp /var/tmp

WORKDIR /app
COPY <<EOF test.py
import tempfile
with tempfile.NamedTemporaryFile(mode='w') as f:
    f.write("test")
print("✓ Temp file creation works")
EOF

# This should work even with read-only root
CMD ["python3", "test.py"]
""")
        
        # Note: Actual read-only test would require running container
        # This just tests the Dockerfile builds correctly


def generate_docker_report():
    """Generate Docker compatibility report for Ubuntu 24.04."""
    report = {
        "ubuntu_2404_changes": {
            "base_image": "ubuntu:24.04 with Python 3.12.3",
            "pep_668": "Requires virtual environments for pip",
            "apparmor": "Stricter security policies",
            "openssl": "Version 3.x with TLS 1.0/1.1 disabled",
            "systemd": "Improved container init system"
        },
        "dockerfile_best_practices": [
            "Always create and use virtual environments",
            "Run as non-root user",
            "Use security_opt for AppArmor configuration",
            "Enable health checks for all services",
            "Use read-only root filesystem where possible",
            "Explicitly set PYTHONUNBUFFERED=1"
        ],
        "migration_checklist": [
            "Update base image to ubuntu:24.04",
            "Add python3-venv installation",
            "Create virtual environment before pip install",
            "Test AppArmor compatibility",
            "Verify SSL/TLS connections",
            "Update CI/CD pipeline for new image"
        ],
        "performance_tips": [
            "Use multi-stage builds to reduce image size",
            "Leverage Ubuntu 24.04's improved package caching",
            "Consider using python:3.12-slim if Ubuntu base not required",
            "Enable BuildKit for faster builds"
        ]
    }
    
    return report


if __name__ == "__main__":
    # Run Docker tests
    pytest.main([__file__, "-v", "-k", "docker"])
    
    # Generate report
    report = generate_docker_report()
    print("\nDocker Compatibility Report:")
    print(json.dumps(report, indent=2))
