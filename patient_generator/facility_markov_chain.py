"""
Facility Markov Chain Module - Probabilistic Medical Facility Routing

This module implements a Markov chain for realistic patient movement through
military medical facilities based on triage severity and medical conditions.

Mathematical Model:
- Discrete-time Markov chain with states: POI, Role1-4, KIA, RTD
- Transition probabilities based on triage category (T1-T4)
- Modifiers for mass casualty, golden hour, special conditions
- Validation of stochastic matrices and realistic flow patterns

Author: Probabilistic Math SME Agent + Medical SME Agent
Version: 1.0.0
"""

import json
import random
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
from datetime import datetime, timedelta
import os


class FacilityMarkovChain:
    """
    Implements Markov chain-based facility routing for military medical evacuation.
    
    Key Features:
    - Severity-based transition probabilities
    - Special condition routing (burns, TBI, amputations)
    - Mass casualty and environmental modifiers
    - Golden hour time-critical routing
    - Realistic evacuation times with variance
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the Facility Markov Chain.
        
        Args:
            config_path: Path to transition_matrices.json config file
        """
        self.config_path = config_path or os.path.join(
            os.path.dirname(__file__), "transition_matrices.json"
        )
        self.config = self._load_transition_matrices()
        
        # Extract key components
        self.base_transitions = self.config["base_transitions"]
        self.modifiers = self.config["modifiers"]
        self.special_conditions = self.config["special_conditions"]
        self.evacuation_times = self.config["evacuation_times"]
        self.mortality_checkpoints = self.config["mortality_checkpoints"]
        
        # Terminal states
        self.terminal_states = {"KIA", "RTD"}
        
        # Validate transition matrices
        self._validate_transition_matrices()
        
    def _load_transition_matrices(self) -> Dict[str, Any]:
        """Load transition matrices configuration from JSON file."""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Transition matrices config not found: {self.config_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in transition matrices config: {e}")
    
    def _validate_transition_matrices(self):
        """Validate that transition matrices are stochastic (rows sum to 1)."""
        for facility, data in self.base_transitions.items():
            if facility in self.terminal_states:
                continue
                
            for triage_cat in ["T1", "T2", "T3", "T4"]:
                if triage_cat not in data.get("transitions", {}):
                    continue
                    
                transitions = data["transitions"][triage_cat]
                # Extract only probability values (skip description)
                probs = [v for k, v in transitions.items() if isinstance(v, (int, float))]
                total = sum(probs)
                
                if abs(total - 1.0) > 0.01:  # Allow small rounding errors
                    raise ValueError(f"Transition probabilities for {facility} {triage_cat} "
                                   f"sum to {total}, not 1.0")
    
    def get_next_facility(
        self, 
        current_facility: str, 
        triage_category: str,
        patient_conditions: Optional[List[str]] = None,
        modifiers: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Determine next facility using Markov chain transition probabilities.
        
        Args:
            current_facility: Current facility (POI, Role1-4)
            triage_category: Patient triage category (T1-T4)
            patient_conditions: List of special conditions (burns, TBI, etc.)
            modifiers: Environmental modifiers (mass_casualty, golden_hour, etc.)
            
        Returns:
            Next facility name or terminal state (KIA, RTD)
        """
        # Terminal states don't transition
        if current_facility in self.terminal_states:
            return current_facility
        
        # Get base transitions
        if current_facility not in self.base_transitions:
            raise ValueError(f"Unknown facility: {current_facility}")
        
        facility_transitions = self.base_transitions[current_facility]["transitions"]
        
        if triage_category not in facility_transitions:
            # Default to T3 if triage category not found
            triage_category = "T3"
        
        base_probs = facility_transitions[triage_category].copy()
        
        # Remove description field if present
        if "description" in base_probs:
            del base_probs["description"]
        
        # Apply special condition modifiers
        adjusted_probs = self._apply_special_conditions(
            base_probs, current_facility, patient_conditions
        )
        
        # Apply environmental modifiers
        adjusted_probs = self._apply_modifiers(
            adjusted_probs, modifiers, triage_category
        )
        
        # Normalize probabilities
        total = sum(adjusted_probs.values())
        if total > 0:
            normalized_probs = {k: v/total for k, v in adjusted_probs.items()}
        else:
            # Fallback if all probabilities are zero
            normalized_probs = base_probs
        
        # Select next facility using weighted random choice
        facilities = list(normalized_probs.keys())
        probabilities = list(normalized_probs.values())
        
        next_facility = np.random.choice(facilities, p=probabilities)
        
        return next_facility
    
    def _apply_special_conditions(
        self, 
        base_probs: Dict[str, float], 
        current_facility: str,
        conditions: Optional[List[str]] = None
    ) -> Dict[str, float]:
        """
        Apply special condition routing rules (burns, TBI, amputations).
        Role1 is always the first stop from POI, but special conditions
        affect priority and speed of evacuation FROM Role1.
        
        Args:
            base_probs: Base transition probabilities
            current_facility: Current facility
            conditions: List of special conditions
            
        Returns:
            Adjusted transition probabilities
        """
        if not conditions:
            return base_probs
        
        adjusted = base_probs.copy()
        
        # Check for special conditions
        for condition in conditions:
            if "amputation" in condition.lower() and current_facility == "Role1":
                # Amputations get priority evacuation from Role1 to Role2
                if "Role2" in adjusted and "RTD" in adjusted:
                    # Increase Role2 probability, decrease RTD
                    adjusted["Role2"] = min(0.85, adjusted.get("Role2", 0) * 1.5)
                    adjusted["RTD"] = adjusted.get("RTD", 0) * 0.3
            
            elif "burn" in condition.lower() and current_facility == "Role1":
                # Major burns need specialized care at Role3+
                if "Role3" in adjusted:
                    # Increase Role3 probability for burn centers
                    adjusted["Role3"] = min(0.60, adjusted.get("Role3", 0) * 2.0)
                    if "RTD" in adjusted:
                        adjusted["RTD"] = adjusted.get("RTD", 0) * 0.2
            
            elif ("tbi" in condition.lower() or "brain" in condition.lower()) and current_facility == "Role1":
                # TBI needs neurosurgical capability at Role2+
                if "Role2" in adjusted:
                    # Priority evacuation to neurosurgery-capable facility
                    adjusted["Role2"] = min(0.80, adjusted.get("Role2", 0) * 1.5)
                    if "RTD" in adjusted:
                        adjusted["RTD"] = adjusted.get("RTD", 0) * 0.2
            
            elif "psychological" in condition.lower() or "stress" in condition.lower():
                # Psychological cases often managed at Role1
                if current_facility == "POI" and "Role1" in adjusted:
                    adjusted["Role1"] = min(0.9, adjusted["Role1"] * 1.5)
                elif current_facility == "Role1" and "RTD" in adjusted:
                    # Higher RTD rate for psych from Role1
                    adjusted["RTD"] = min(0.75, adjusted.get("RTD", 0) * 1.5)
            
            elif "vehicle" in condition.lower() or "armor" in condition.lower():
                # Casualty in vehicle might bypass Role1
                if current_facility == "POI" and "Role2" in adjusted:
                    # Small chance of direct evac in vehicle
                    vehicle_prob = self.special_conditions.get("vehicle_evacuation", {}).get("direct_evac_probability", 0.15)
                    if "Role1" in adjusted and adjusted["Role1"] > vehicle_prob:
                        # Transfer some Role1 probability to Role2/3
                        transfer = adjusted["Role1"] * vehicle_prob
                        adjusted["Role1"] -= transfer
                        adjusted["Role2"] = adjusted.get("Role2", 0) + transfer * 0.7
                        adjusted["Role3"] = adjusted.get("Role3", 0) + transfer * 0.3
        
        return adjusted
    
    def _apply_modifiers(
        self, 
        base_probs: Dict[str, float], 
        modifiers: Optional[Dict[str, Any]] = None,
        triage_category: str = "T3"
    ) -> Dict[str, float]:
        """
        Apply environmental and situational modifiers.
        
        Args:
            base_probs: Base transition probabilities
            modifiers: Environmental modifiers
            triage_category: Patient triage category
            
        Returns:
            Modified transition probabilities
        """
        if not modifiers:
            return base_probs
        
        adjusted = base_probs.copy()
        
        # Mass casualty modifier
        if modifiers.get("mass_casualty", False):
            mass_cas_mod = self.modifiers["mass_casualty"]
            
            # Increase KIA probability
            if "KIA" in adjusted:
                adjusted["KIA"] *= mass_cas_mod["kia_multiplier"]
            
            # Reduce RTD probability (overwhelmed resources)
            if "RTD" in adjusted:
                adjusted["RTD"] *= mass_cas_mod["rtd_reduction"]
            
            # In mass casualty, Role1 may expedite evacuation due to overwhelm
            # But patients still go through Role1 first (from POI)
            if current_facility == "Role1" and triage_category == "T1":
                # Faster evacuation from Role1 when overwhelmed
                if "Role2" in adjusted:
                    adjusted["Role2"] = min(0.90, adjusted["Role2"] * 1.3)
        
        # Golden hour modifier for critical patients
        if triage_category == "T1" and "time_since_injury" in modifiers:
            hours = modifiers["time_since_injury"]
            
            if hours <= 1.0:
                # Within golden hour - better survival
                survival_bonus = self.modifiers["golden_hour"]["within_1hr"]["survival_bonus"]
                if "KIA" in adjusted:
                    adjusted["KIA"] *= (1 - survival_bonus)
            else:
                # Beyond golden hour - worse survival
                kia_mult = self.modifiers["golden_hour"]["beyond_1hr"]["kia_multiplier"]
                if "KIA" in adjusted:
                    adjusted["KIA"] *= kia_mult
        
        # Degraded environment modifier
        if modifiers.get("degraded_environment", False):
            deg_env_mod = self.modifiers["degraded_environment"]
            
            if "KIA" in adjusted:
                adjusted["KIA"] *= deg_env_mod["kia_multiplier"]
        
        return adjusted
    
    def generate_full_path(
        self, 
        triage_category: str,
        patient_conditions: Optional[List[str]] = None,
        modifiers: Optional[Dict[str, Any]] = None,
        max_steps: int = 10
    ) -> List[str]:
        """
        Generate complete patient path from POI to terminal state.
        
        Args:
            triage_category: Patient triage category (T1-T4)
            patient_conditions: List of special conditions
            modifiers: Environmental modifiers
            max_steps: Maximum transitions to prevent infinite loops
            
        Returns:
            List of facilities visited in order
        """
        path = ["POI"]
        current_facility = "POI"
        
        for _ in range(max_steps):
            next_facility = self.get_next_facility(
                current_facility, 
                triage_category,
                patient_conditions,
                modifiers
            )
            
            path.append(next_facility)
            
            if next_facility in self.terminal_states:
                break
            
            current_facility = next_facility
        
        return path
    
    def get_evacuation_time(
        self, 
        from_facility: str, 
        to_facility: str,
        transport_type: str = "ground"
    ) -> int:
        """
        Get evacuation time between facilities with realistic variance.
        
        Args:
            from_facility: Origin facility
            to_facility: Destination facility
            transport_type: "ground" or "air"
            
        Returns:
            Evacuation time in minutes
        """
        # Build route key
        route_key = f"{from_facility}_to_{to_facility}"
        
        if route_key not in self.evacuation_times:
            # Try reverse route
            reverse_key = f"{to_facility}_to_{from_facility}"
            if reverse_key in self.evacuation_times:
                route_key = reverse_key
            else:
                # Default time if route not found
                return 60
        
        route_times = self.evacuation_times[route_key]
        
        if transport_type not in route_times:
            # Use first available transport type
            transport_type = list(route_times.keys())[0]
        
        time_params = route_times[transport_type]
        mean_time = time_params["mean"]
        std_time = time_params.get("std", mean_time * 0.2)
        
        # Generate time with normal distribution, ensure positive
        evac_time = max(5, int(np.random.normal(mean_time, std_time)))
        
        return evac_time
    
    def assess_mortality(
        self, 
        triage_category: str, 
        checkpoint: str,
        cumulative_mortality: float = 0.0
    ) -> bool:
        """
        Assess if patient dies at a mortality checkpoint.
        
        Args:
            triage_category: Patient triage category
            checkpoint: Mortality checkpoint name
            cumulative_mortality: Previous cumulative mortality
            
        Returns:
            True if patient dies, False if survives
        """
        base_rates = self.mortality_checkpoints["base_mortality_rates"].get(
            triage_category, self.mortality_checkpoints["base_mortality_rates"]["T3"]
        )
        
        # Get checkpoint-specific mortality rate
        checkpoint_rate = base_rates.get(checkpoint, 0.02)
        
        # Check cumulative cap
        cumulative_cap = base_rates.get("cumulative_cap", 1.0)
        if cumulative_mortality >= cumulative_cap:
            return False  # Already at mortality cap
        
        # Adjust rate based on remaining mortality budget
        adjusted_rate = min(checkpoint_rate, cumulative_cap - cumulative_mortality)
        
        # Roll for mortality
        return random.random() < adjusted_rate
    
    def validate_path(self, path: List[str]) -> Dict[str, Any]:
        """
        Validate that a generated path follows realistic patterns.
        
        Args:
            path: List of facilities in order
            
        Returns:
            Validation results with any warnings or errors
        """
        validation = {
            "valid": True,
            "warnings": [],
            "errors": [],
            "metrics": {}
        }
        
        # Check for duplicate facilities (shouldn't revisit)
        non_terminal = [f for f in path if f not in self.terminal_states]
        if len(non_terminal) != len(set(non_terminal)):
            validation["warnings"].append("Patient revisited a facility")
        
        # Check path length
        if len(path) > 6:
            validation["warnings"].append(f"Unusually long path: {len(path)} facilities")
        
        # Check if path ends in terminal state
        if path[-1] not in self.terminal_states:
            validation["errors"].append("Path does not end in terminal state")
            validation["valid"] = False
        
        # Calculate metrics
        validation["metrics"]["total_facilities"] = len(non_terminal)
        validation["metrics"]["outcome"] = path[-1]
        validation["metrics"]["bypassed_role1"] = "Role1" not in path and len(path) > 2
        
        return validation


# Utility functions for integration

def create_markov_chain(config_path: Optional[str] = None) -> FacilityMarkovChain:
    """
    Factory function to create Facility Markov Chain.
    
    Args:
        config_path: Optional path to transition matrices config
        
    Returns:
        Configured FacilityMarkovChain instance
    """
    return FacilityMarkovChain(config_path)


def test_markov_chain():
    """Test the Facility Markov Chain with different scenarios."""
    chain = FacilityMarkovChain()
    
    print("Testing Facility Markov Chain")
    print("=" * 50)
    
    # Test different triage categories
    test_cases = [
        ("T1", ["traumatic_brain_injury"], {"mass_casualty": True}),
        ("T2", ["burn_injury"], {}),
        ("T3", ["fracture"], {}),
        ("T4", ["psychological_stress"], {}),
    ]
    
    for triage, conditions, modifiers in test_cases:
        print(f"\nTriage: {triage}, Conditions: {conditions}")
        
        # Generate multiple paths to see distribution
        paths = []
        for _ in range(10):
            path = chain.generate_full_path(triage, conditions, modifiers)
            paths.append(path)
        
        # Analyze paths
        outcomes = [p[-1] for p in paths]
        avg_length = sum(len(p) for p in paths) / len(paths)
        bypassed_role1 = sum(1 for p in paths if "Role1" not in p)
        
        print(f"  Average path length: {avg_length:.1f}")
        print(f"  Outcomes: KIA={outcomes.count('KIA')}, RTD={outcomes.count('RTD')}")
        print(f"  Bypassed Role1: {bypassed_role1}/10")
        print(f"  Sample path: {' -> '.join(paths[0])}")


if __name__ == "__main__":
    test_markov_chain()