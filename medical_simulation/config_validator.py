"""
Config Validator for Medical Simulation
Validates JSON configurations for compatibility and correctness
"""
import json
from pathlib import Path
from typing import Dict, List, Any, Tuple


class ValidationResult:
    """Simple container for validation results"""
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        
    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0
        
    def add_error(self, message: str):
        self.errors.append(f"ERROR: {message}")
        
    def add_warning(self, message: str):
        self.warnings.append(f"WARNING: {message}")


def validate_configs(injuries_path: str, fronts_path: str) -> ValidationResult:
    """
    Main validation function - checks both config files
    Returns ValidationResult with errors and warnings
    """
    result = ValidationResult()
    
    # Load JSON files
    try:
        with open(injuries_path) as f:
            injuries = json.load(f)
    except Exception as e:
        result.add_error(f"Cannot load injuries.json: {e}")
        return result
        
    try:
        with open(fronts_path) as f:
            fronts = json.load(f)
    except Exception as e:
        result.add_error(f"Cannot load fronts_config.json: {e}")
        return result
    
    # Check versions
    check_versions(injuries, fronts, result)
    
    # Validate injuries.json
    validate_injuries_config(injuries, result)
    
    # Validate fronts_config.json
    validate_fronts_config(fronts, result)
    
    # Cross-validate between files
    cross_validate_configs(injuries, fronts, result)
    
    return result


def check_versions(injuries: Dict, fronts: Dict, result: ValidationResult):
    """Check version compatibility between configs"""
    
    injuries_version = injuries.get("config_version", "0.9.0")
    fronts_version = fronts.get("config_version", "0.9.0")
    
    # Check if versions are compatible
    if injuries_version != fronts_version:
        # Check compatibility lists
        fronts_compat = injuries.get("compatible_with", {}).get("fronts_config", [])
        injuries_compat = fronts.get("compatible_with", {}).get("injuries", [])
        
        if fronts_version not in fronts_compat and injuries_version not in injuries_compat:
            result.add_error(f"Version mismatch: injuries.json v{injuries_version} incompatible with fronts_config.json v{fronts_version}")


def validate_injuries_config(config: Dict, result: ValidationResult):
    """Validate injuries.json specific rules"""
    
    # Check deterioration model
    if "deterioration_model" in config:
        model = config["deterioration_model"]
        
        for injury_type, severities in model.items():
            if injury_type not in ["Battle Injury", "Non-Battle Injury", "Disease"]:
                result.add_warning(f"Unknown injury type: {injury_type}")
                
            for severity, params in severities.items():
                # Check health scores
                initial = params.get("initial_health", 0)
                if not 0 <= initial <= 100:
                    result.add_error(f"{injury_type}/{severity}: initial_health must be 0-100, found {initial}")
                    
                # Check deterioration rates
                rate = params.get("deterioration_rate", 0)
                if not 0 <= rate <= 100:
                    result.add_error(f"{injury_type}/{severity}: deterioration_rate must be 0-100, found {rate}")
                    
                # Check hemorrhage multiplier
                hemorrhage = params.get("hemorrhage_multiplier", 1.0)
                if not 0.5 <= hemorrhage <= 3.0:
                    result.add_warning(f"{injury_type}/{severity}: unusual hemorrhage_multiplier {hemorrhage}")
    
    # Check environmental modifiers
    if "environmental_modifiers" in config:
        for condition, modifier in config["environmental_modifiers"].items():
            mult = modifier.get("deterioration_multiplier", 1.0)
            if not 0.5 <= mult <= 3.0:
                result.add_warning(f"Environmental modifier {condition}: unusual multiplier {mult}")


def validate_fronts_config(config: Dict, result: ValidationResult):
    """Validate fronts_config.json specific rules"""
    
    total_ratio = 0.0
    
    for front in config.get("fronts", []):
        name = front.get("name", "Unknown")
        ratio = front.get("ratio", 0)
        total_ratio += ratio
        
        # Check medical facilities
        if "medical_facilities" in front:
            facilities = front["medical_facilities"]
            
            # Validate Role hierarchy
            role1_capacity = facilities.get("role1", {}).get("capacity_per_facility", 0) * facilities.get("role1", {}).get("count", 0)
            role2_capacity = facilities.get("role2", {}).get("capacity_per_facility", 0) * facilities.get("role2", {}).get("count", 0)
            
            if role1_capacity > role2_capacity * 2:
                result.add_warning(f"{name}: Role1 total capacity ({role1_capacity}) seems high compared to Role2 ({role2_capacity})")
            
            # Check OR capacity
            for role in ["role1", "role2", "role3"]:
                if role in facilities:
                    or_capacity = facilities[role].get("or_capacity", 0)
                    if role == "role1" and or_capacity > 0:
                        result.add_error(f"{name}: Role1 cannot have OR capacity (found {or_capacity})")
                    
                    if role == "role2" and or_capacity > 4:
                        result.add_warning(f"{name}: Role2 OR capacity {or_capacity} seems high")
        
        # Check transport assets
        if "transport_assets" in front:
            helicopters = front["transport_assets"].get("casevac_helicopters", 0)
            if helicopters > 5:
                result.add_warning(f"{name}: {helicopters} helicopters seems high for one front")
    
    # Check total ratio
    if abs(total_ratio - 1.0) > 0.01:
        result.add_error(f"Front ratios sum to {total_ratio:.2f}, should be 1.0")


def cross_validate_configs(injuries: Dict, fronts: Dict, result: ValidationResult):
    """Validate references between configs"""
    
    # Check that injury types in deterioration model are referenced
    total_patients = injuries.get("total_patients", 0)
    
    # Calculate expected patients per front
    for front in fronts.get("fronts", []):
        name = front.get("name")
        ratio = front.get("ratio", 0)
        expected_patients = int(total_patients * ratio)
        
        # Check if medical capacity is reasonable
        if "medical_facilities" in front:
            total_beds = 0
            for facility_type, facility in front["medical_facilities"].items():
                if isinstance(facility, dict) and "capacity_per_facility" in facility:
                    total_beds += facility.get("capacity_per_facility", 0) * facility.get("count", 0)
            
            if total_beds < expected_patients * 0.1:
                result.add_warning(f"{name}: Only {total_beds} beds for ~{expected_patients} expected casualties")


if __name__ == "__main__":
    # Test validation
    result = validate_configs(
        "patient_generator/injuries.json",
        "patient_generator/fronts_config.json"
    )
    
    print(f"Validation {'PASSED' if result.is_valid else 'FAILED'}")
    
    for error in result.errors:
        print(error)
    
    for warning in result.warnings:
        print(warning)