#!/usr/bin/env python3
"""
Ubuntu 24.04 Migration Helper for Medical Patients Generator

This script assists in migrating the application to Ubuntu 24.04 LTS compatibility,
handling PEP 668 restrictions, dependency updates, and configuration changes.
"""

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Dict, List


class Ubuntu2404MigrationHelper:
    """Helper class for migrating to Ubuntu 24.04."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.venv_path = project_root / ".venv"
        self.backup_dir = project_root / ".migration_backup"
        self.issues_found = []
        self.fixes_applied = []

    def check_system(self) -> Dict[str, any]:
        """Check current system configuration."""
        checks = {
            "os_version": self._check_ubuntu_version(),
            "python_version": self._check_python_version(),
            "virtual_env": self._check_virtual_environment(),
            "system_packages": self._check_system_packages(),
            "docker": self._check_docker_compatibility(),
        }
        return checks

    def _check_ubuntu_version(self) -> Dict[str, str]:
        """Check Ubuntu version."""
        try:
            with open("/etc/os-release") as f:
                os_info = dict(line.strip().split("=", 1) for line in f if "=" in line)
                version = os_info.get("VERSION_ID", "").strip('"')
                return {
                    "current": version,
                    "target": "24.04",
                    "compatible": version == "24.04"
                }
        except:
            return {
                "current": "unknown",
                "target": "24.04",
                "compatible": False
            }

    def _check_python_version(self) -> Dict[str, any]:
        """Check Python version compatibility."""
        current = sys.version_info[:3]
        return {
            "current": f"{current[0]}.{current[1]}.{current[2]}",
            "minimum": "3.8.0",
            "ubuntu_default": "3.12.3",
            "compatible": current >= (3, 8, 0),
            "optimal": current >= (3, 12, 0)
        }

    def _check_virtual_environment(self) -> bool:
        """Check if running in virtual environment."""
        return hasattr(sys, "real_prefix") or (
            hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
        )

    def _check_system_packages(self) -> Dict[str, bool]:
        """Check required system packages."""
        packages = {
            "build-essential": "Development tools",
            "libpq-dev": "PostgreSQL development",
            "libssl-dev": "OpenSSL development",
            "libffi-dev": "Foreign function interface",
            "python3-dev": "Python development headers",
            "python3-venv": "Virtual environment support",
            "cargo": "Rust compiler (for cryptography)",
            "pkg-config": "Package configuration",
            "postgresql-client-16": "PostgreSQL 16 client"
        }

        results = {}
        for pkg, desc in packages.items():
            result = subprocess.run(
                ["dpkg", "-l", pkg],
                capture_output=True,
                text=True, check=False
            )
            results[pkg] = {
                "installed": result.returncode == 0,
                "description": desc
            }

        return results

    def _check_docker_compatibility(self) -> Dict[str, any]:
        """Check Docker configuration for Ubuntu 24.04."""
        docker_checks = {
            "installed": shutil.which("docker") is not None,
            "dockerfile_updates_needed": [],
            "compose_updates_needed": []
        }

        # Check Dockerfile for compatibility
        dockerfile_path = self.project_root / "Dockerfile"
        if dockerfile_path.exists():
            with open(dockerfile_path) as f:
                content = f.read()

                # Check base image
                if "python:3.11" in content and "ubuntu:24.04" not in content:
                    docker_checks["dockerfile_updates_needed"].append(
                        "Consider using ubuntu:24.04 base image for better compatibility"
                    )

                # Check for PEP 668 compliance
                if "pip install" in content and "venv" not in content:
                    docker_checks["dockerfile_updates_needed"].append(
                        "Add virtual environment creation for PEP 668 compliance"
                    )

        return docker_checks

    def create_migration_plan(self) -> Dict[str, List[str]]:
        """Create a detailed migration plan."""
        plan = {
            "preparation": [],
            "system_updates": [],
            "python_updates": [],
            "dependency_updates": [],
            "configuration_updates": [],
            "testing_steps": []
        }

        # Preparation steps
        plan["preparation"] = [
            "Backup current environment and configurations",
            "Document current package versions",
            "Review breaking changes in Python 3.12",
            "Test application in Docker with Ubuntu 24.04 base image"
        ]

        # System updates
        system_check = self._check_system_packages()
        for pkg, info in system_check.items():
            if not info["installed"]:
                plan["system_updates"].append(
                    f"Install {pkg} - {info['description']}"
                )

        # Python updates
        plan["python_updates"] = [
            "Create new virtual environment with Python 3.12",
            "Update pip to latest version (24.0+)",
            "Install packages in virtual environment only (PEP 668)",
            "Update any Python 3.8-3.11 specific code for 3.12 compatibility"
        ]

        # Dependency updates
        plan["dependency_updates"] = [
            "Update psycopg2-binary for PostgreSQL 16 support",
            "Ensure cryptography>=41.0.1 for OpenSSL 3.x",
            "Update all packages to versions tested with Python 3.12",
            "Add cargo to system dependencies for cryptography build"
        ]

        # Configuration updates
        plan["configuration_updates"] = [
            "Update CI/CD pipelines for Ubuntu 24.04",
            "Modify Docker configurations for PEP 668",
            "Update documentation for new setup process",
            "Adjust AppArmor profiles if using custom security"
        ]

        # Testing steps
        plan["testing_steps"] = [
            "Run full test suite in Ubuntu 24.04 environment",
            "Test database migrations with PostgreSQL 16",
            "Verify SSL/TLS connections with OpenSSL 3.x",
            "Test Docker deployment with new base image",
            "Performance testing with Python 3.12"
        ]

        return plan

    def backup_current_environment(self):
        """Backup current environment configuration."""
        print("Creating backup of current environment...")

        self.backup_dir.mkdir(exist_ok=True)

        # Backup files
        files_to_backup = [
            "requirements.txt",
            "pyproject.toml",
            "Dockerfile",
            "docker-compose.yml",
            ".env",
            "alembic.ini"
        ]

        for filename in files_to_backup:
            src = self.project_root / filename
            if src.exists():
                dst = self.backup_dir / filename
                shutil.copy2(src, dst)
                print(f"  Backed up {filename}")

        # Save current package versions
        if self._check_virtual_environment():
            result = subprocess.run(
                [sys.executable, "-m", "pip", "freeze"],
                capture_output=True,
                text=True, check=False
            )
            if result.returncode == 0:
                freeze_file = self.backup_dir / "pip_freeze.txt"
                freeze_file.write_text(result.stdout)
                print("  Saved current package versions")

    def create_compatible_venv(self):
        """Create Ubuntu 24.04 compatible virtual environment."""
        print("\nCreating PEP 668 compliant virtual environment...")

        if self.venv_path.exists():
            response = input(f"Virtual environment exists at {self.venv_path}. Replace? [y/N]: ")
            if response.lower() != "y":
                print("Skipping virtual environment creation")
                return

            shutil.rmtree(self.venv_path)

        # Create new virtual environment
        subprocess.run(
            [sys.executable, "-m", "venv", str(self.venv_path)],
            check=True
        )

        print(f"Created virtual environment at {self.venv_path}")
        print("\nTo activate:")
        print(f"  source {self.venv_path}/bin/activate")

    def update_dockerfile(self):
        """Update Dockerfile for Ubuntu 24.04 compatibility."""
        dockerfile_path = self.project_root / "Dockerfile"
        if not dockerfile_path.exists():
            print("No Dockerfile found, skipping...")
            return

        print("\nUpdating Dockerfile for Ubuntu 24.04...")

        with open(dockerfile_path) as f:
            content = f.read()

        updated_content = content
        changes = []

        # Update base image if using Python
        if "FROM python:" in content and "ubuntu:" not in content:
            updated_content = self._create_ubuntu_based_dockerfile()
            changes.append("Converted to Ubuntu 24.04 base image with PEP 668 compliance")

        if changes:
            new_dockerfile = self.project_root / "Dockerfile.ubuntu24"
            new_dockerfile.write_text(updated_content)
            print(f"Created {new_dockerfile}")
            for change in changes:
                print(f"  - {change}")

    def _create_ubuntu_based_dockerfile(self) -> str:
        """Create Ubuntu 24.04 based Dockerfile."""
        return """# Ubuntu 24.04 LTS base image with Python 3.12
FROM ubuntu:24.04

# Install system dependencies
RUN apt-get update && \\
    DEBIAN_FRONTEND=noninteractive apt-get install -y \\
    python3-full \\
    python3-pip \\
    python3-venv \\
    build-essential \\
    libpq-dev \\
    libssl-dev \\
    libffi-dev \\
    cargo \\
    pkg-config \\
    postgresql-client-16 \\
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Create virtual environment (PEP 668 compliance)
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip in virtual environment
RUN pip install --upgrade pip

# Copy requirements
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

# Run application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
"""

    def update_ci_config(self):
        """Update CI/CD configuration for Ubuntu 24.04."""
        github_workflow = self.project_root / ".github" / "workflows"
        if not github_workflow.exists():
            print("No GitHub Actions workflow found, skipping...")
            return

        print("\nCI/CD configuration updates needed:")
        print("  - Update runner to: ubuntu-24.04")
        print("  - Add virtual environment creation step")
        print("  - Install system dependencies before Python packages")
        print("  - Use 'python3 -m pip' instead of 'pip' directly")

    def generate_test_script(self):
        """Generate comprehensive test script."""
        test_script = self.project_root / "test_ubuntu2404_compatibility.sh"

        script_content = """#!/bin/bash
# Ubuntu 24.04 Compatibility Test Script

set -e

echo "Ubuntu 24.04 Compatibility Test Suite"
echo "===================================="

# Check Ubuntu version
echo -n "Checking Ubuntu version... "
if grep -q "24.04" /etc/os-release; then
    echo "✓ Ubuntu 24.04"
else
    echo "✗ Not Ubuntu 24.04"
    exit 1
fi

# Check Python version
echo -n "Checking Python version... "
python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
if [[ "$python_version" == "3.12."* ]]; then
    echo "✓ Python $python_version"
else
    echo "⚠ Python $python_version (expected 3.12.x)"
fi

# Check virtual environment
echo -n "Checking virtual environment... "
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "✓ Active"
else
    echo "✗ Not in virtual environment (required for PEP 668)"
    exit 1
fi

# Check system packages
echo "Checking system packages..."
packages=(
    "build-essential"
    "libpq-dev"
    "libssl-dev"
    "libffi-dev"
    "python3-dev"
    "cargo"
    "postgresql-client-16"
)

for pkg in "${packages[@]}"; do
    if dpkg -l "$pkg" &>/dev/null; then
        echo "  ✓ $pkg"
    else
        echo "  ✗ $pkg (missing)"
    fi
done

# Test Python imports
echo "Testing Python package imports..."
python3 -c "
import sys
print(f'  Python {sys.version}')
try:
    import fastapi
    print('  ✓ FastAPI')
except ImportError:
    print('  ✗ FastAPI')
try:
    import psycopg2
    print('  ✓ psycopg2')
except ImportError:
    print('  ✗ psycopg2')
try:
    import cryptography
    print('  ✓ cryptography')
except ImportError:
    print('  ✗ cryptography')
"

# Run pytest if available
if command -v pytest &>/dev/null; then
    echo "Running test suite..."
    pytest tests/ubuntu_24_04_compatibility/ -v
else
    echo "⚠ pytest not installed, skipping tests"
fi

echo ""
echo "Compatibility check complete!"
"""

        test_script.write_text(script_content)
        test_script.chmod(0o755)
        print(f"\nCreated test script: {test_script}")

    def generate_report(self) -> Dict[str, any]:
        """Generate migration readiness report."""
        report = {
            "system_check": self.check_system(),
            "migration_plan": self.create_migration_plan(),
            "issues_found": self.issues_found,
            "fixes_applied": self.fixes_applied,
            "next_steps": [
                "Review the migration plan",
                "Run backup_current_environment()",
                "Create new virtual environment",
                "Update configurations as needed",
                "Run comprehensive tests"
            ]
        }

        return report


def main():
    """Main migration helper entry point."""
    parser = argparse.ArgumentParser(
        description="Ubuntu 24.04 Migration Helper for Medical Patients Generator"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check compatibility without making changes"
    )
    parser.add_argument(
        "--backup",
        action="store_true",
        help="Backup current environment"
    )
    parser.add_argument(
        "--migrate",
        action="store_true",
        help="Perform migration steps"
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="Project root directory"
    )

    args = parser.parse_args()

    helper = Ubuntu2404MigrationHelper(args.project_root)

    if args.check or not any([args.backup, args.migrate]):
        print("Checking Ubuntu 24.04 compatibility...\n")
        report = helper.generate_report()
        print(json.dumps(report, indent=2))

    if args.backup:
        helper.backup_current_environment()

    if args.migrate:
        print("\nStarting migration process...")
        helper.backup_current_environment()
        helper.create_compatible_venv()
        helper.update_dockerfile()
        helper.update_ci_config()
        helper.generate_test_script()
        print("\nMigration steps completed!")
        print("Next: Activate virtual environment and install dependencies")


if __name__ == "__main__":
    main()
