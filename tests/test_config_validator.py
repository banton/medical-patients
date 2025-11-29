"""Tests for Config Validator"""

import json
from pathlib import Path
import tempfile

from medical_simulation.config_validator import validate_configs


def test_valid_configs():
    """Test that current configs pass validation"""
    result = validate_configs("patient_generator/injuries.json", "patient_generator/fronts_config.json")
    assert result.is_valid, f"Validation failed: {result.errors}"


def test_version_mismatch():
    """Test version incompatibility detection"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create mismatched configs
        injuries = {
            "config_version": "1.0.0",
            "compatible_with": {"fronts_config": ["1.0.0"]},
            "deterioration_model": {},
        }
        fronts = {"config_version": "2.0.0", "compatible_with": {"injuries": ["2.0.0"]}, "fronts": []}

        injuries_path = Path(tmpdir) / "injuries.json"
        fronts_path = Path(tmpdir) / "fronts.json"

        with open(injuries_path, "w") as f:
            json.dump(injuries, f)
        with open(fronts_path, "w") as f:
            json.dump(fronts, f)

        result = validate_configs(str(injuries_path), str(fronts_path))
        assert not result.is_valid
        assert any("Version mismatch" in e for e in result.errors)


def test_invalid_deterioration_rate():
    """Test catching invalid deterioration rates"""
    with tempfile.TemporaryDirectory() as tmpdir:
        injuries = {
            "config_version": "1.0.0",
            "deterioration_model": {
                "Battle Injury": {
                    "Severe": {
                        "initial_health": 150,  # Invalid!
                        "deterioration_rate": 200,  # Invalid!
                    }
                }
            },
        }
        fronts = {"config_version": "1.0.0", "fronts": []}

        injuries_path = Path(tmpdir) / "injuries.json"
        fronts_path = Path(tmpdir) / "fronts.json"

        with open(injuries_path, "w") as f:
            json.dump(injuries, f)
        with open(fronts_path, "w") as f:
            json.dump(fronts, f)

        result = validate_configs(str(injuries_path), str(fronts_path))
        assert not result.is_valid
        assert any("initial_health must be 0-100" in e for e in result.errors)
        assert any("deterioration_rate must be 0-100" in e for e in result.errors)


def test_role1_or_capacity():
    """Test that Role1 cannot have OR capacity"""
    with tempfile.TemporaryDirectory() as tmpdir:
        injuries = {"config_version": "1.0.0"}
        fronts = {
            "config_version": "1.0.0",
            "fronts": [
                {
                    "name": "Test",
                    "ratio": 1.0,
                    "medical_facilities": {
                        "role1": {
                            "count": 1,
                            "or_capacity": 2,  # Invalid for Role1!
                        }
                    },
                }
            ],
        }

        injuries_path = Path(tmpdir) / "injuries.json"
        fronts_path = Path(tmpdir) / "fronts.json"

        with open(injuries_path, "w") as f:
            json.dump(injuries, f)
        with open(fronts_path, "w") as f:
            json.dump(fronts, f)

        result = validate_configs(str(injuries_path), str(fronts_path))
        assert not result.is_valid
        assert any("Role1 cannot have OR capacity" in e for e in result.errors)


def test_front_ratios():
    """Test that front ratios sum to 1.0"""
    with tempfile.TemporaryDirectory() as tmpdir:
        injuries = {"config_version": "1.0.0"}
        fronts = {
            "config_version": "1.0.0",
            "fronts": [
                {"name": "A", "ratio": 0.5},
                {"name": "B", "ratio": 0.3},
                # Missing 0.2!
            ],
        }

        injuries_path = Path(tmpdir) / "injuries.json"
        fronts_path = Path(tmpdir) / "fronts.json"

        with open(injuries_path, "w") as f:
            json.dump(injuries, f)
        with open(fronts_path, "w") as f:
            json.dump(fronts, f)

        result = validate_configs(str(injuries_path), str(fronts_path))
        assert not result.is_valid
        assert any("Front ratios sum to 0.80" in e for e in result.errors)
