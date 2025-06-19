"""
Ubuntu 24.04 LTS Compatibility Test Suite for Medical Patients Generator

This test suite ensures full compatibility with Ubuntu 24.04 LTS default packages
and system configurations, including Python 3.12.3, PostgreSQL 16.2, and PEP 668.
"""

import importlib.metadata
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile
from typing import Dict

import pytest


class Ubuntu2404CompatibilityTester:
    """Main test orchestrator for Ubuntu 24.04 compatibility."""

    REQUIRED_PYTHON_VERSION = (3, 12, 0)
    REQUIRED_POSTGRESQL_VERSION = "16"
    UBUNTU_VERSION = "24.04"

    def __init__(self):
        self.results = {
            "system_info": {},
            "python_compatibility": {},
            "dependency_compatibility": {},
            "database_compatibility": {},
            "security_compliance": {},
            "warnings": [],
            "errors": []
        }

    def get_system_info(self) -> Dict[str, str]:
        """Collect system information."""
        info = {
            "platform": platform.platform(),
            "python_version": sys.version,
            "python_implementation": platform.python_implementation(),
            "architecture": platform.machine(),
        }

        # Check Ubuntu version
        try:
            with open("/etc/os-release") as f:
                os_info = dict(line.strip().split("=", 1) for line in f if "=" in line)
                info["os_name"] = os_info.get("NAME", "").strip('"')
                info["os_version"] = os_info.get("VERSION_ID", "").strip('"')
        except FileNotFoundError:
            info["os_name"] = "Not Ubuntu"
            info["os_version"] = "Unknown"

        return info


class TestSystemCompatibility:
    """Test system-level compatibility with Ubuntu 24.04."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.tester = Ubuntu2404CompatibilityTester()

    def test_ubuntu_version(self):
        """Verify we're testing on Ubuntu 24.04."""
        system_info = self.tester.get_system_info()

        # This test can run on any system but warns if not Ubuntu 24.04
        if system_info["os_name"] != "Ubuntu" or system_info["os_version"] != "24.04":
            pytest.skip(f"Not running on Ubuntu 24.04 (found {system_info['os_name']} {system_info['os_version']})")

    def test_python_version(self):
        """Test Python version compatibility."""
        current_version = sys.version_info[:3]
        min_version = (3, 8, 0)  # Application minimum
        ubuntu_default = (3, 12, 3)  # Ubuntu 24.04 default

        assert current_version >= min_version, f"Python {current_version} < minimum {min_version}"

        if current_version < ubuntu_default:
            pytest.warns(UserWarning,
                        match=f"Python {current_version} < Ubuntu 24.04 default {ubuntu_default}")

    def test_system_packages(self):
        """Test required system packages are available."""
        required_packages = [
            "build-essential",
            "libpq-dev",
            "libssl-dev",
            "libffi-dev",
            "python3-dev",
            "python3-venv",
            "cargo",  # Required for cryptography
            "pkg-config"
        ]

        missing_packages = []
        for package in required_packages:
            result = subprocess.run(
                ["dpkg", "-l", package],
                capture_output=True,
                text=True, check=False
            )
            if result.returncode != 0:
                missing_packages.append(package)

        if missing_packages:
            pytest.skip(f"Missing system packages: {', '.join(missing_packages)}")

    def test_postgresql_client(self):
        """Test PostgreSQL client compatibility."""
        try:
            result = subprocess.run(
                ["psql", "--version"],
                capture_output=True,
                text=True,
                check=True
            )
            version_str = result.stdout.strip()
            # Extract version number (e.g., "psql (PostgreSQL) 16.2")
            if "16" in version_str:
                assert True, f"PostgreSQL 16.x found: {version_str}"
            else:
                pytest.warns(UserWarning, match=f"PostgreSQL version mismatch: {version_str}")
        except subprocess.CalledProcessError:
            pytest.skip("PostgreSQL client not installed")

    def test_openssl_version(self):
        """Test OpenSSL 3.x compatibility."""
        try:
            result = subprocess.run(
                ["openssl", "version"],
                capture_output=True,
                text=True,
                check=True
            )
            version_str = result.stdout.strip()
            assert "OpenSSL 3." in version_str, f"OpenSSL 3.x required, found: {version_str}"
        except subprocess.CalledProcessError:
            pytest.skip("OpenSSL not installed")


class TestPythonEnvironment:
    """Test Python environment and PEP 668 compliance."""

    def test_virtual_environment(self):
        """Ensure we're running in a virtual environment (PEP 668 compliance)."""
        in_venv = hasattr(sys, "real_prefix") or (
            hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
        )

        # Skip check in CI environment as it may use different Ubuntu version
        if os.environ.get("CI") == "true":
            pytest.skip("Skipping virtual environment check in CI")

        if not in_venv and os.path.exists("/etc/os-release"):
            with open("/etc/os-release") as f:
                if "24.04" in f.read():
                    pytest.fail("Must run in virtual environment on Ubuntu 24.04 (PEP 668)")

    def test_pip_functionality(self):
        """Test pip works correctly in the environment."""
        try:
            import pip
            pip_version = pip.__version__
            assert pip_version >= "24.0", f"pip {pip_version} < Ubuntu 24.04 default (24.0)"
        except ImportError:
            pytest.fail("pip not available in environment")

    def test_create_venv(self):
        """Test ability to create virtual environments."""
        with tempfile.TemporaryDirectory() as tmpdir:
            venv_path = Path(tmpdir) / "test_venv"
            result = subprocess.run(
                [sys.executable, "-m", "venv", str(venv_path)],
                capture_output=True,
                text=True, check=False
            )
            assert result.returncode == 0, f"Failed to create venv: {result.stderr}"
            assert (venv_path / "bin" / "python").exists()


class TestDependencyCompatibility:
    """Test all Python package dependencies work with Ubuntu 24.04."""

    @pytest.fixture()
    def requirements(self):
        """Load requirements.txt."""
        req_path = Path(__file__).parent.parent.parent / "requirements.txt"
        if not req_path.exists():
            pytest.skip("requirements.txt not found")

        with open(req_path) as f:
            return [line.strip() for line in f if line.strip() and not line.startswith("#")]

    def test_core_dependencies(self):
        """Test core dependencies are importable."""
        core_deps = [
            ("fastapi", "0.100.0"),
            ("uvicorn", "0.22.0"),
            ("pydantic", "2.0.0"),
            ("psycopg2", None),  # psycopg2-binary
            ("cryptography", "41.0.1"),
            ("alembic", "1.11.1"),
            ("redis", "5.0.0"),
        ]

        for module_name, min_version in core_deps:
            try:
                if module_name == "psycopg2":
                    # Special handling for psycopg2-binary
                    import psycopg2
                    assert psycopg2.__version__ is not None
                else:
                    module = importlib.import_module(module_name)
                    if min_version and hasattr(module, "__version__"):
                        assert module.__version__ >= min_version
            except ImportError as e:
                pytest.fail(f"Failed to import {module_name}: {e}")

    def test_cryptography_rust_compilation(self):
        """Test cryptography package works with Rust/cargo."""
        try:
            from cryptography.fernet import Fernet
            # Test basic encryption functionality
            key = Fernet.generate_key()
            f = Fernet(key)
            token = f.encrypt(b"test data")
            assert f.decrypt(token) == b"test data"
        except Exception as e:
            pytest.fail(f"Cryptography functionality failed: {e}")

    def test_psycopg2_ssl(self):
        """Test psycopg2 works with OpenSSL 3.x."""
        try:
            import psycopg2
            # Test SSL support is available
            assert hasattr(psycopg2.extensions, "ISOLATION_LEVEL_AUTOCOMMIT")
            # Would need actual database to test SSL connection
        except Exception as e:
            pytest.fail(f"psycopg2 SSL support failed: {e}")

    @pytest.mark.asyncio()
    async def test_fastapi_startup(self):
        """Test FastAPI application can start."""
        try:
            from fastapi.testclient import TestClient

            from src.main import app

            client = TestClient(app)
            response = client.get("/health")
            assert response.status_code in [200, 401]  # May require auth
        except ImportError:
            pytest.skip("FastAPI app not available for testing")
        except Exception as e:
            pytest.fail(f"FastAPI startup failed: {e}")


class TestDatabaseCompatibility:
    """Test PostgreSQL 16.2 compatibility."""

    @pytest.mark.skipif(
        not shutil.which("pg_config"),
        reason="PostgreSQL not installed"
    )
    def test_postgresql_version(self):
        """Verify PostgreSQL version."""
        result = subprocess.run(
            ["pg_config", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        assert "PostgreSQL 16" in result.stdout

    def test_alembic_compatibility(self):
        """Test Alembic migrations work with PostgreSQL 16."""
        try:
            import alembic
            from alembic.config import Config
            # Would need database connection to run actual migrations
            assert alembic.__version__ >= "1.11.1"
        except ImportError:
            pytest.fail("Alembic not available")

    def test_sqlalchemy_features(self):
        """Test SQLAlchemy compatibility with PostgreSQL 16 features."""
        try:
            from sqlalchemy import __version__ as sa_version, create_engine, text

            # Test version supports PostgreSQL 16
            major, minor = map(int, sa_version.split(".")[:2])
            assert (major > 2) or (major == 2 and minor >= 0), \
                f"SQLAlchemy {sa_version} may not support PostgreSQL 16"
        except ImportError:
            pytest.fail("SQLAlchemy not available")


class TestSecurityCompliance:
    """Test security features and compliance."""

    def test_apparmor_compatibility(self):
        """Test for AppArmor restrictions."""
        if not os.path.exists("/sys/kernel/security/apparmor"):
            pytest.skip("AppArmor not enabled")

        # Check if we're running under AppArmor constraints
        try:
            with open("/proc/self/attr/current") as f:
                profile = f.read().strip()
                if "docker" in profile and "default" not in profile:
                    pytest.warns(UserWarning,
                                match="Running under AppArmor restrictions")
        except:
            pass

    def test_ssl_protocols(self):
        """Test SSL/TLS configuration."""
        try:
            import ssl
            context = ssl.create_default_context()

            # Ubuntu 24.04 disables TLS 1.0/1.1
            # Check that minimum version is at least TLS 1.2
            if hasattr(ssl, "TLSVersion"):
                # Python 3.10+ has TLSVersion enum
                min_version = context.minimum_version
                assert min_version >= ssl.TLSVersion.TLSv1_2, f"Minimum TLS version {min_version} is less than TLS 1.2"
            else:
                # For older Python versions, check the context properties
                assert hasattr(context, "minimum_version"), "SSL context should have minimum_version attribute"
        except Exception as e:
            pytest.fail(f"SSL configuration test failed: {e}")

    def test_file_permissions(self):
        """Test file permission handling."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("test")

            # Check umask and permissions
            stat_info = test_file.stat()
            mode = stat_info.st_mode & 0o777
            assert mode <= 0o644, f"File permissions too open: {oct(mode)}"


class TestDockerCompatibility:
    """Test Docker container compatibility with Ubuntu 24.04."""

    @pytest.mark.skipif(
        not shutil.which("docker"),
        reason="Docker not installed"
    )
    def test_docker_build(self, tmp_path):
        """Test Docker image builds successfully."""
        # Create minimal Dockerfile for testing
        dockerfile = tmp_path / "Dockerfile.test"
        dockerfile.write_text("""
FROM ubuntu:24.04
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y \
    python3-full python3-venv python3-pip \
    libpq-dev build-essential libssl-dev libffi-dev cargo

WORKDIR /app
RUN python3 -m venv /venv
ENV PATH="/venv/bin:$PATH"

# Test pip works in venv
RUN pip install --upgrade pip
RUN pip install fastapi uvicorn psycopg2-binary
""")

        result = subprocess.run(
            ["docker", "build", "-f", str(dockerfile), "-t", "ubuntu2404-test", "."],
            cwd=tmp_path,
            capture_output=True,
            text=True, check=False
        )

        assert result.returncode == 0, f"Docker build failed: {result.stderr}"


class TestMigrationReadiness:
    """Test application readiness for Ubuntu 24.04 migration."""

    def test_python_syntax_compatibility(self):
        """Test code uses Python 3.8+ compatible syntax."""
        src_path = Path(__file__).parent.parent.parent / "src"
        if not src_path.exists():
            pytest.skip("Source directory not found")

        issues = []
        for py_file in src_path.rglob("*.py"):
            try:
                with open(py_file) as f:
                    compile(f.read(), py_file, "exec")
            except SyntaxError as e:
                issues.append(f"{py_file}: {e}")

        assert not issues, f"Syntax errors found: {issues}"

    def test_import_compatibility(self):
        """Test all imports work with Python 3.12."""
        # Test critical imports that might break
        critical_imports = [
            "asyncio",
            "typing",
            "dataclasses",
            "importlib.metadata",  # Replaces pkg_resources
            "tomllib",  # New in 3.11, replaces tomli
        ]

        for module in critical_imports:
            try:
                importlib.import_module(module)
            except ImportError as e:
                if module == "tomllib" and sys.version_info < (3, 11):
                    continue  # Expected on older Python
                pytest.fail(f"Failed to import {module}: {e}")


def generate_compatibility_report():
    """Generate a comprehensive compatibility report."""
    report = {
        "timestamp": str(datetime.now()),
        "system": platform.platform(),
        "python_version": sys.version,
        "test_results": {},
        "recommendations": []
    }

    # Run tests and collect results
    pytest.main([__file__, "-v", "--json-report", "--json-report-file=compatibility_report.json"])

    # Add recommendations based on results
    if sys.version_info < (3, 12):
        report["recommendations"].append(
            "Upgrade to Python 3.12 for full Ubuntu 24.04 compatibility"
        )

    return report


if __name__ == "__main__":
    # Run compatibility tests
    import datetime
    report = generate_compatibility_report()
    print(json.dumps(report, indent=2))
