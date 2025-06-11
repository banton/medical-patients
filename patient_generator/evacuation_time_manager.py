"""
Evacuation Time Manager

Manages evacuation and transit time calculations based on triage categories.
Provides timing logic for patient flow through military medical facilities.
"""

import json
import random
from typing import Dict, Optional, Union
from pathlib import Path


class EvacuationTimeManager:
    """
    Manages evacuation and transit time calculations based on triage categories.
    
    This class loads configuration from JSON and provides methods to calculate
    randomized evacuation times, transit times, and apply triage-based modifiers
    for KIA and RTD rates.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize EvacuationTimeManager with configuration.
        
        Args:
            config_path: Path to evacuation_transit_times.json config file.
                        If None, uses default path in patient_generator directory.
        """
        if config_path is None:
            # Default to evacuation_transit_times.json in patient_generator directory
            base_dir = Path(__file__).parent
            config_path = base_dir / "evacuation_transit_times.json"
        
        self.config_path = config_path
        self.config = self._load_config(config_path)
        self._validate_config()
    
    def _load_config(self, config_path: Union[str, Path]) -> Dict:
        """
        Load evacuation times configuration from JSON file.
        
        Args:
            config_path: Path to the JSON configuration file
            
        Returns:
            Loaded configuration dictionary
            
        Raises:
            FileNotFoundError: If configuration file doesn't exist
            json.JSONDecodeError: If configuration file is invalid JSON
            ValueError: If configuration structure is invalid
        """
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Verify required top-level keys exist
            required_keys = ["evacuation_times", "transit_times", "kia_rate_modifiers"]
            missing_keys = [key for key in required_keys if key not in config]
            if missing_keys:
                raise ValueError(f"Missing required configuration keys: {missing_keys}")
            
            return config
            
        except FileNotFoundError:
            raise FileNotFoundError(f"Evacuation configuration file not found: {config_path}")
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(f"Invalid JSON in configuration file: {e}")
    
    def _validate_config(self) -> None:
        """
        Validate the loaded configuration structure and data ranges.
        
        Raises:
            ValueError: If configuration validation fails
        """
        # Validate evacuation times structure
        evacuation_times = self.config.get("evacuation_times", {})
        expected_facilities = ["POI", "Role1", "Role2", "Role3", "Role4"]
        expected_triage = ["T1", "T2", "T3"]
        
        for facility in expected_facilities:
            if facility not in evacuation_times:
                raise ValueError(f"Missing evacuation times for facility: {facility}")
            
            for triage in expected_triage:
                if triage not in evacuation_times[facility]:
                    raise ValueError(f"Missing triage {triage} for facility {facility}")
                
                time_config = evacuation_times[facility][triage]
                if "min_hours" not in time_config or "max_hours" not in time_config:
                    raise ValueError(f"Missing min_hours/max_hours for {facility} {triage}")
                
                min_hours = time_config["min_hours"]
                max_hours = time_config["max_hours"]
                
                if min_hours < 0 or max_hours < 0:
                    raise ValueError(f"Negative time values not allowed: {facility} {triage}")
                
                if min_hours > max_hours:
                    raise ValueError(f"min_hours > max_hours: {facility} {triage}")
        
        # Validate transit times structure
        transit_times = self.config.get("transit_times", {})
        expected_routes = [
            "POI_to_Role1", "Role1_to_Role2", 
            "Role2_to_Role3", "Role3_to_Role4"
        ]
        
        for route in expected_routes:
            if route not in transit_times:
                raise ValueError(f"Missing transit times for route: {route}")
            
            for triage in expected_triage:
                if triage not in transit_times[route]:
                    raise ValueError(f"Missing triage {triage} for route {route}")
                
                time_config = transit_times[route][triage]
                min_hours = time_config.get("min_hours", 0)
                max_hours = time_config.get("max_hours", 0)
                
                if min_hours < 0 or max_hours < 0:
                    raise ValueError(f"Negative transit time: {route} {triage}")
                
                if min_hours > max_hours:
                    raise ValueError(f"min_hours > max_hours: {route} {triage}")
        
        # Validate KIA rate modifiers
        kia_modifiers = self.config.get("kia_rate_modifiers", {})
        for triage in expected_triage:
            if triage not in kia_modifiers:
                raise ValueError(f"Missing KIA rate modifier for triage: {triage}")
            
            modifier = kia_modifiers[triage]
            if not isinstance(modifier, (int, float)) or modifier < 0:
                raise ValueError(f"Invalid KIA rate modifier for {triage}: {modifier}")
    
    def get_evacuation_time(self, facility: str, triage_category: str) -> float:
        """
        Get randomized evacuation time in hours for given facility and triage.
        
        Args:
            facility: Military facility name (POI, Role1, Role2, Role3, Role4)
            triage_category: Triage category (T1, T2, T3)
            
        Returns:
            Randomized evacuation time in hours (float)
            
        Raises:
            ValueError: If facility or triage category is unknown
        """
        # Validate inputs
        if facility not in self.config["evacuation_times"]:
            raise ValueError(f"Unknown facility: {facility}")
        
        if triage_category not in self.config["evacuation_times"][facility]:
            raise ValueError(f"Unknown triage category: {triage_category}")
        
        # Get time range for facility and triage
        time_config = self.config["evacuation_times"][facility][triage_category]
        min_hours = time_config["min_hours"]
        max_hours = time_config["max_hours"]
        
        # Return randomized time within range
        if min_hours == max_hours:
            return float(min_hours)
        
        return round(random.uniform(min_hours, max_hours), 1)
    
    def get_transit_time(self, from_facility: str, to_facility: str, triage_category: str) -> float:
        """
        Get randomized transit time in hours for given route and triage.
        
        Args:
            from_facility: Source facility
            to_facility: Destination facility  
            triage_category: Triage category (T1, T2, T3)
            
        Returns:
            Randomized transit time in hours (float)
            
        Raises:
            ValueError: If route or triage category is unknown
        """
        # Build route key
        route_key = f"{from_facility}_to_{to_facility}"
        
        # Validate route exists
        if route_key not in self.config["transit_times"]:
            raise ValueError(f"Unknown transit route: {route_key}")
        
        # Validate triage category
        if triage_category not in self.config["transit_times"][route_key]:
            raise ValueError(f"Unknown triage category: {triage_category}")
        
        # Get time range for route and triage
        time_config = self.config["transit_times"][route_key][triage_category]
        min_hours = time_config["min_hours"]
        max_hours = time_config["max_hours"]
        
        # Return randomized time within range
        if min_hours == max_hours:
            return float(min_hours)
        
        return round(random.uniform(min_hours, max_hours), 1)
    
    def get_kia_rate_modifier(self, triage_category: str) -> float:
        """
        Get KIA rate modifier for given triage category.
        
        Args:
            triage_category: Triage category (T1, T2, T3)
            
        Returns:
            KIA rate modifier (float)
            
        Raises:
            ValueError: If triage category is unknown
        """
        if triage_category not in self.config["kia_rate_modifiers"]:
            raise ValueError(f"Unknown triage category: {triage_category}")
        
        return float(self.config["kia_rate_modifiers"][triage_category])
    
    def get_rtd_rate_modifier(self, triage_category: str) -> float:
        """
        Get RTD rate modifier for given triage category.
        
        Args:
            triage_category: Triage category (T1, T2, T3)
            
        Returns:
            RTD rate modifier (float)
            
        Raises:
            ValueError: If triage category is unknown
        """
        # Check if RTD modifiers exist in config
        if "rtd_rate_modifiers" not in self.config:
            # Fallback: inverse of KIA modifiers (higher KIA = lower RTD)
            kia_modifier = self.get_kia_rate_modifier(triage_category)
            return round(2.0 - kia_modifier, 1)  # T1=0.5, T2=1.0, T3=1.5
        
        if triage_category not in self.config["rtd_rate_modifiers"]:
            raise ValueError(f"Unknown triage category: {triage_category}")
        
        return float(self.config["rtd_rate_modifiers"][triage_category])
    
    def get_valid_facilities(self) -> list:
        """
        Get list of valid facility names.
        
        Returns:
            List of facility names
        """
        return list(self.config["evacuation_times"].keys())
    
    def get_valid_triage_categories(self) -> list:
        """
        Get list of valid triage categories.
        
        Returns:
            List of triage category names
        """
        # Get from first facility (all should have same triage categories)
        first_facility = next(iter(self.config["evacuation_times"].values()))
        return list(first_facility.keys())
    
    def get_valid_routes(self) -> list:
        """
        Get list of valid transit routes.
        
        Returns:
            List of route names (e.g., ['POI_to_Role1', 'Role1_to_Role2'])
        """
        return list(self.config["transit_times"].keys())
    
    def get_facility_hierarchy(self) -> list:
        """
        Get ordered list of facilities in evacuation hierarchy.
        
        Returns:
            List of facilities in order (POI → Role1 → Role2 → Role3 → Role4)
        """
        # Return from config if available, otherwise use default order
        if "facility_hierarchy" in self.config:
            return self.config["facility_hierarchy"]
        
        return ["POI", "Role1", "Role2", "Role3", "Role4"]
    
    def get_next_facility(self, current_facility: str) -> Optional[str]:
        """
        Get the next facility in the evacuation hierarchy.
        
        Args:
            current_facility: Current facility name
            
        Returns:
            Next facility name, or None if at end of hierarchy
        """
        hierarchy = self.get_facility_hierarchy()
        
        try:
            current_index = hierarchy.index(current_facility)
            if current_index + 1 < len(hierarchy):
                return hierarchy[current_index + 1]
            return None
        except ValueError:
            raise ValueError(f"Unknown facility: {current_facility}")
    
    def apply_triage_modifier(self, base_rate: float, triage_category: str, 
                             modifier_type: str = "kia") -> float:
        """
        Apply triage-based modifier to a base rate.
        
        Args:
            base_rate: Base rate to modify (0.0 to 1.0)
            triage_category: Triage category (T1, T2, T3)
            modifier_type: Type of modifier ("kia" or "rtd")
            
        Returns:
            Modified rate with triage modifier applied
            
        Raises:
            ValueError: If modifier type is unknown
        """
        if modifier_type == "kia":
            modifier = self.get_kia_rate_modifier(triage_category)
        elif modifier_type == "rtd":
            modifier = self.get_rtd_rate_modifier(triage_category)
        else:
            raise ValueError(f"Unknown modifier type: {modifier_type}")
        
        # Apply modifier and ensure result stays within valid range [0.0, 1.0]
        modified_rate = base_rate * modifier
        return min(1.0, max(0.0, modified_rate))
    
    def get_config_summary(self) -> Dict:
        """
        Get summary of configuration for debugging and validation.
        
        Returns:
            Dictionary with configuration summary
        """
        return {
            "config_path": str(self.config_path),
            "facilities": self.get_valid_facilities(),
            "triage_categories": self.get_valid_triage_categories(),
            "transit_routes": self.get_valid_routes(),
            "facility_hierarchy": self.get_facility_hierarchy(),
            "kia_modifiers": self.config.get("kia_rate_modifiers", {}),
            "rtd_modifiers": self.config.get("rtd_rate_modifiers", {}),
            "metadata": self.config.get("configuration_metadata", {})
        }