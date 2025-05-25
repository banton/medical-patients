"""Tests for the simplified UI."""

import pytest
import requests

BASE_URL = "http://localhost:8000"


class TestSimpleUI:
    """Test the simplified UI elements and functionality."""
    
    def test_ui_loads(self):
        """Test that the UI page loads successfully."""
        response = requests.get(f"{BASE_URL}/")
        assert response.status_code == 200
        
        # Check title
        assert "<title>Military Patient Generator</title>" in response.text
        
        # Check header
        assert "<h1>Military Patient Generator</h1>" in response.text
    
    def test_ui_elements_present(self):
        """Test that all required UI elements are present."""
        response = requests.get(f"{BASE_URL}/")
        
        # Check info box
        assert 'class="info-box"' in response.text
        
        # Check configuration files are mentioned
        assert "demographics.json" in response.text
        assert "fronts_config.json" in response.text
        assert "injuries.json" in response.text
        
        # Check generate button
        assert 'id="generateBtn"' in response.text
        assert "Generate Patients" in response.text
        
        # Check status box exists (hidden initially)
        assert 'id="statusBox"' in response.text
    
    def test_javascript_loaded(self):
        """Test that the JavaScript file is properly referenced."""
        response = requests.get(f"{BASE_URL}/")
        
        # Find script tag
        assert 'src="/static/js/simple-app.js"' in response.text
        
        # Verify the JS file exists
        js_response = requests.get(f"{BASE_URL}/static/js/simple-app.js")
        assert js_response.status_code == 200
        assert "handleGenerate" in js_response.text
    
    def test_no_external_dependencies(self):
        """Test that the UI has no external CSS/JS dependencies."""
        response = requests.get(f"{BASE_URL}/")
        
        # Check no external CSS (Bootstrap, etc.)
        assert 'cdn.jsdelivr.net' not in response.text
        assert 'cdnjs.cloudflare.com' not in response.text
        assert 'link href="http' not in response.text
        
        # Check no external JS
        assert 'script src="http' not in response.text
    
    def test_api_config_js_exists(self):
        """Test that api-config.js exists for backward compatibility."""
        response = requests.get(f"{BASE_URL}/static/js/api-config.js")
        assert response.status_code == 200
    
    def test_css_inline(self):
        """Test that CSS is inline in the HTML."""
        response = requests.get(f"{BASE_URL}/")
        
        # Check for style tag
        assert "<style>" in response.text
        assert ".generate-button" in response.text
        assert ".info-box" in response.text