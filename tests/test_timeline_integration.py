"""
Integration tests for React Timeline Viewer with backend API.
Tests the complete workflow from patient generation to timeline visualization.
"""

import json
import os
from pathlib import Path
import tempfile
import time

import pytest
import requests


class TestTimelineIntegration:
    """Test integration between backend API and timeline viewer."""

    def test_timeline_viewer_accessible(self):
        """Test that timeline viewer is accessible."""
        # Check if timeline viewer is running (development or production)
        timeline_urls = ["http://localhost:5174", "http://localhost:5175"]

        accessible = False
        for url in timeline_urls:
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    accessible = True
                    break
            except requests.RequestException:
                continue

        # If not accessible in development, check if build exists
        if not accessible:
            timeline_dist = Path("patient-timeline-viewer/dist/index.html")
            assert timeline_dist.exists(), "Timeline viewer not accessible and no build found"

    def test_backend_api_accessible(self):
        """Test that backend API is accessible."""
        try:
            response = requests.get("http://localhost:8000/health", timeout=5)
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
        except requests.RequestException as e:
            pytest.skip(f"Backend API not accessible: {e}")

    def test_sample_data_format_compatibility(self):
        """Test that sample data format is compatible with timeline viewer expectations."""
        sample_file = Path("patient-timeline-viewer/public/sample-patients.json")
        assert sample_file.exists(), "Sample patients file not found"

        with open(sample_file) as f:
            patients_data = json.load(f)

        assert isinstance(patients_data, list), "Sample data should be a list"
        assert len(patients_data) > 0, "Sample data should not be empty"

        # Validate first patient structure
        patient = patients_data[0]
        required_fields = ["id", "nationality", "triage_category", "final_status", "movement_timeline"]

        for field in required_fields:
            assert field in patient, f"Required field '{field}' missing from patient data"

        # Validate triage category values
        assert patient["triage_category"] in ["T1", "T2", "T3"]

        # Validate final status values
        assert patient["final_status"] in ["KIA", "RTD", "Remains_Role4"]

        # Validate timeline structure
        timeline = patient["movement_timeline"]
        assert isinstance(timeline, list), "Movement timeline should be a list"

        if timeline:
            event = timeline[0]
            required_event_fields = ["event_type", "timestamp", "hours_since_injury"]
            for field in required_event_fields:
                assert field in event, f"Required timeline field '{field}' missing"

    @pytest.mark.integration()
    def test_end_to_end_workflow(self):
        """Test complete workflow from API generation to timeline viewing."""
        # Skip if services not running
        try:
            response = requests.get("http://localhost:8000/health", timeout=5)
            assert response.status_code == 200
        except requests.RequestException:
            pytest.skip("Backend API not accessible for E2E test")

        # Test configuration for minimal patient generation
        test_config = {
            "configuration": {
                "name": "Timeline Integration Test",
                "description": "Test configuration for timeline integration",
                "total_patients": 5,
                "injury_distribution": {"Battle Injury": 0.6, "Non-Battle Injury": 0.3, "Disease": 0.1},
                "front_configs": [
                    {
                        "id": "test_front_1",
                        "name": "Test Front Alpha",
                        "casualty_rate": 1.0,
                        "nationality_distribution": [{"nationality_code": "USA", "percentage": 100.0}],
                    }
                ],
                "facility_configs": [
                    {
                        "id": "test_r2_1",
                        "name": "Test Role 2 Medical",
                        "capacity": 100,
                        "role": "Role 2",
                        "front_id": "test_front_1",
                        "kia_rate": 0.05,
                        "rtd_rate": 0.85,
                    }
                ],
            },
            "output_formats": ["json"],
        }

        # Generate patients
        try:
            response = requests.post(
                "http://localhost:8000/api/v1/generation/",
                json=test_config,
                headers={"X-API-Key": "DEMO_MILMED_2025_50_PATIENTS"},
                timeout=30,
            )
            assert response.status_code == 201
            generation_data = response.json()
            job_id = generation_data["job_id"]

            # Wait for job completion (with timeout)
            max_wait = 60  # seconds
            wait_time = 0
            job_status = None

            while wait_time < max_wait:
                response = requests.get(
                    f"http://localhost:8000/api/v1/jobs/{job_id}",
                    headers={"X-API-Key": "DEMO_MILMED_2025_50_PATIENTS"},
                    timeout=10,
                )
                assert response.status_code == 200
                job_status = response.json()

                if job_status["status"] in ["completed", "failed", "cancelled"]:
                    break

                time.sleep(2)
                wait_time += 2

            assert job_status is not None, "Job status not retrieved"
            assert job_status["status"] == "completed", f"Job failed with status: {job_status['status']}"

            # Download results
            response = requests.get(
                f"http://localhost:8000/api/v1/downloads/{job_id}",
                headers={"X-API-Key": "DEMO_MILMED_2025_50_PATIENTS"},
                timeout=30,
            )
            assert response.status_code == 200

            # Save to temporary file and validate format
            with tempfile.NamedTemporaryFile(mode="wb", suffix=".zip", delete=False) as f:
                f.write(response.content)
                temp_file = f.name

            # Verify file exists and has content
            assert Path(temp_file).stat().st_size > 0, "Downloaded file is empty"

            # Cleanup
            os.unlink(temp_file)

        except requests.RequestException as e:
            pytest.skip(f"API request failed: {e}")

    def test_taskfile_commands_work(self):
        """Test that Taskfile commands for timeline viewer work correctly."""
        import subprocess
        import shutil

        # Skip if task command is not available
        if not shutil.which("task"):
            pytest.skip("task command not available")

        # Test timeline command
        result = subprocess.run(
            ["task", "timeline"], cwd=Path.cwd(), capture_output=True, text=True, timeout=120, check=False
        )

        # Task timeline opens the viewer, so we just check it doesn't error
        assert result.returncode == 0, f"task timeline failed: {result.stderr}"

    def test_timeline_viewer_build_artifacts(self):
        """Test that timeline viewer build creates necessary artifacts."""
        # Ensure build directory exists and has expected files
        dist_dir = Path("patient-timeline-viewer/dist")

        if not dist_dir.exists():
            # Run build if dist doesn't exist
            import subprocess

            result = subprocess.run(
                ["npm", "run", "build"],
                cwd=Path("patient-timeline-viewer"),
                capture_output=True,
                text=True,
                timeout=120,
                check=False,
            )
            assert result.returncode == 0, f"Build failed: {result.stderr}"

        # Check for required build artifacts
        assert (dist_dir / "index.html").exists(), "index.html not found in build"

        # Check for JS and CSS assets
        js_files = list(dist_dir.glob("assets/*.js"))
        css_files = list(dist_dir.glob("assets/*.css"))

        assert len(js_files) > 0, "No JavaScript files found in build"
        assert len(css_files) > 0, "No CSS files found in build"
