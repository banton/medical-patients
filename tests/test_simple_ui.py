"""Tests for the simplified UI."""

from fastapi.testclient import TestClient
import pytest

from src.main import app

client = TestClient(app)

pytestmark = [pytest.mark.integration]


class TestSimpleUI:
    """Test the simplified UI elements and functionality."""

    def test_ui_loads(self):
        """Test that the UI page loads successfully."""
        response = client.get("/")
        assert response.status_code == 200

        # Check title (updated for temporal capabilities)
        assert "<title>Military Medical Exercise Patient Generator</title>" in response.text

        # Check header (new modern format with temporal capabilities)
        assert "Military Medical Exercise Patient Generator" in response.text
        assert 'class="text-2xl font-bold' in response.text

    def test_ui_elements_present(self):
        """Test that all required UI elements are present."""
        response = client.get("/")

        # Check API banner
        assert 'class="api-banner"' in response.text

        # Check accordion structure exists
        assert 'class="accordion"' in response.text

        # Check generate button (new format)
        assert 'id="generateBtn"' in response.text
        assert "Generate" in response.text

        # Check status box exists
        assert 'id="statusBox"' in response.text

    def test_javascript_loaded(self):
        """Test that the JavaScript file is properly referenced."""
        response = client.get("/")

        # Find script tag (new app structure)
        assert 'src="js/app.js"' in response.text

        # Verify the JS file exists
        js_response = client.get("/static/js/app.js")
        assert js_response.status_code == 200

    def test_modern_dependencies_loaded(self):
        """Test that the modern UI loads expected dependencies."""
        response = client.get("/")

        # Modern UI uses external dependencies for professional appearance
        assert "flowbite" in response.text  # Component library
        assert "tailwindcss" in response.text  # CSS framework
        assert "font-awesome" in response.text  # Icons

    def test_api_service_exists(self):
        """Test that api service file exists."""
        response = client.get("/static/js/services/api.js")
        assert response.status_code == 200

    def test_css_structure(self):
        """Test that CSS structure is properly loaded."""
        response = client.get("/")

        # Check for external CSS files
        assert "css/main.css" in response.text
        assert "css/components/banner.css" in response.text
        assert "css/components/accordion.css" in response.text
