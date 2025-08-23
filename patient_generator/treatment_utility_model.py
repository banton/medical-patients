"""
Treatment Utility Model - Probabilistic treatment selection system.
Replaces hardcoded keyword matching with evidence-based utility scoring.

This module implements a multi-attribute utility function for treatment selection
based on medical appropriateness, urgency, effectiveness, and resource availability.
"""

from dataclasses import dataclass, field
from datetime import datetime
import json
import logging
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class TreatmentOption:
    """Represents a treatment option with utility scoring."""

    name: str
    utility_score: float
    resource_cost: int = 1
    time_minutes: int = 5
    facility_level_required: str = "POI"
    contraindications: List[str] = field(default_factory=list)
    urgency_factor: float = 1.0
    effectiveness: float = 0.8


class TreatmentUtilityModel:
    """
    Probabilistic treatment selection using multi-attribute utility scoring.

    Implements the mathematical framework:
    U(t,i,p,f) = w₁·M(t,i) + w₂·Urgency(t,i,p) + w₃·E(t,i,p) + w₄·R(t,f) + w₅·C(t,f)

    Where:
    - M(t,i): Medical appropriateness score
    - Urgency(t,i,p): Time-sensitive urgency factor
    - E(t,i,p): Treatment effectiveness
    - R(t,f): Resource availability
    - C(t,f): Facility capability
    """

    # Utility function weights (sum to 1.0)
    WEIGHTS = {
        "appropriateness": 0.35,
        "urgency": 0.25,
        "effectiveness": 0.20,
        "availability": 0.15,
        "capability": 0.05,
    }

    # Softmax temperature for treatment selection
    TEMPERATURE = 0.5

    def __init__(self, config_path: Optional[Path] = None):
        """Initialize treatment utility model with configuration."""
        self.config_path = config_path or Path(__file__).parent / "treatment_protocols.json"
        self.protocols: Dict[str, Any] = {}
        self.treatment_matrix: Dict[str, Dict[str, float]] = {}
        self.facility_capabilities: Dict[str, List[str]] = {}
        self._load_protocols()
        self._build_treatment_matrix()

    def _load_protocols(self) -> None:
        """Load treatment protocols from JSON configuration."""
        try:
            with open(self.config_path) as f:
                self.protocols = json.load(f)

            # Extract facility capabilities
            self.facility_capabilities = {
                facility: data.get("available_treatments", [])
                for facility, data in self.protocols.get("facility_capabilities", {}).items()
            }

            logger.info(f"Loaded {len(self.protocols.get('treatment_appropriateness_matrix', {}))} treatment protocols")

        except FileNotFoundError:
            logger.error(f"Treatment protocols not found at {self.config_path}")
            self.protocols = self._get_default_protocols()
        except Exception as e:
            logger.error(f"Error loading treatment protocols: {e}")
            self.protocols = self._get_default_protocols()

    def _build_treatment_matrix(self) -> None:
        """Build treatment appropriateness matrix from protocols."""
        matrix = self.protocols.get("treatment_appropriateness_matrix", {})

        for snomed_code, protocol in matrix.items():
            self.treatment_matrix[snomed_code] = protocol.get("utility_scores", {})

    def _get_default_protocols(self) -> Dict[str, Any]:
        """Return minimal default protocols as fallback."""
        return {
            "treatment_appropriateness_matrix": {},
            "facility_capabilities": {
                "POI": {"available_treatments": ["pressure_dressing", "morphine_autoinjector"]},
                "Role1": {"available_treatments": ["iv_fluids", "antibiotics"]},
                "Role2": {"available_treatments": ["blood_transfusion", "surgery"]},
                "Role3": {"available_treatments": ["icu_care", "definitive_surgery"]},
            },
            "default_fallbacks": {
                "POI": "pressure_dressing",
                "Role1": "iv_fluids",
                "Role2": "supportive_care",
                "Role3": "comprehensive_assessment",
            },
        }

    def calculate_utility(
        self,
        treatment: str,
        injury_code: str,
        severity: str,
        facility: str,
        time_elapsed_minutes: int = 0,
        available_resources: Optional[Dict[str, int]] = None,
    ) -> float:
        """
        Calculate utility score for a treatment option.

        Args:
            treatment: Treatment name
            injury_code: SNOMED code for injury
            severity: Injury severity (Severe, Moderate, etc.)
            facility: Current facility (POI, Role1, Role2, Role3)
            time_elapsed_minutes: Time since injury
            available_resources: Current resource availability

        Returns:
            Utility score between 0 and 1
        """
        available_resources = available_resources or {"supplies": 100}

        # Component 1: Medical appropriateness
        appropriateness = self._get_appropriateness_score(treatment, injury_code)

        # Component 2: Urgency factor (exponential decay for time-critical treatments)
        urgency = self._calculate_urgency(treatment, time_elapsed_minutes)

        # Component 3: Treatment effectiveness
        effectiveness = self._get_effectiveness(treatment, severity)

        # Component 4: Resource availability
        availability = self._calculate_availability(treatment, available_resources)

        # Component 5: Facility capability (binary)
        capability = self._check_facility_capability(treatment, facility)

        # Weighted sum of components
        utility = (
            self.WEIGHTS["appropriateness"] * appropriateness
            + self.WEIGHTS["urgency"] * urgency
            + self.WEIGHTS["effectiveness"] * effectiveness
            + self.WEIGHTS["availability"] * availability
            + self.WEIGHTS["capability"] * capability
        )

        return min(1.0, max(0.0, utility))  # Clamp to [0, 1]

    def _get_appropriateness_score(self, treatment: str, injury_code: str) -> float:
        """Get medical appropriateness score from matrix."""
        # Check if we have specific scores for this injury
        if injury_code in self.treatment_matrix:
            scores = self.treatment_matrix[injury_code]
            if treatment in scores:
                return scores[treatment]

        # Check if treatment is contraindicated
        protocol = self.protocols.get("treatment_appropriateness_matrix", {}).get(injury_code, {})
        contraindicated = protocol.get("contraindicated_treatments", [])
        if treatment in contraindicated:
            return 0.0

        # Default score for unknown combinations
        return 0.3

    def _calculate_urgency(self, treatment: str, time_elapsed: int) -> float:
        """Calculate urgency factor with exponential decay."""
        golden_hour = self.protocols.get("urgency_parameters", {}).get("golden_hour_treatments", {})

        if treatment in golden_hour:
            params = golden_hour[treatment]
            max_time = params.get("max_minutes", 60)
            decay_rate = params.get("decay_rate", 0.02)

            if time_elapsed <= max_time:
                # Exponential decay: e^(-λt)
                return math.exp(-decay_rate * time_elapsed)
            # Past golden hour, reduced urgency
            return 0.2

        # Non-urgent treatment
        return 0.8

    def _get_effectiveness(self, treatment: str, severity: str) -> float:
        """Get treatment effectiveness based on severity."""
        # Severity modifiers
        severity_modifiers = {
            "Severe": 0.9,  # High effectiveness needed
            "Moderate to severe": 0.85,
            "Moderate": 0.8,
            "Mild to moderate": 0.75,
            "Mild": 0.7,
        }

        base_effectiveness = 0.8  # Default effectiveness
        severity_modifier = severity_modifiers.get(severity, 0.8)

        # Some treatments are more effective for severe cases
        if treatment in ["tourniquet", "blood_transfusion", "damage_control_surgery"]:
            if severity in ["Severe", "Moderate to severe"]:
                return min(1.0, base_effectiveness * 1.2)

        return base_effectiveness * severity_modifier

    def _calculate_availability(self, treatment: str, resources: Dict[str, int]) -> float:
        """Calculate resource availability score."""
        # Simple resource check
        available_supplies = resources.get("supplies", 0)

        # High-resource treatments
        high_resource_treatments = ["blood_transfusion", "surgery", "icu_care"]

        if treatment in high_resource_treatments:
            if available_supplies < 10:
                return 0.2
            if available_supplies < 50:
                return 0.6

        # Normal resource availability
        if available_supplies > 0:
            return min(1.0, available_supplies / 20)  # Normalize to [0, 1]

        return 0.0

    def _check_facility_capability(self, treatment: str, facility: str) -> float:
        """Check if facility can provide treatment (binary)."""
        available_treatments = self.facility_capabilities.get(facility, [])

        # Check if treatment is available or 'all' is specified
        if treatment in available_treatments or "all" in available_treatments:
            return 1.0

        return 0.0

    def select_treatments(
        self,
        injury_code: str,
        severity: str,
        facility: str,
        time_elapsed_minutes: int = 0,
        available_resources: Optional[Dict[str, int]] = None,
        max_treatments: int = 3,
    ) -> List[Dict[str, Any]]:
        """
        Select treatments using softmax probability distribution.

        Args:
            injury_code: SNOMED code for injury
            severity: Injury severity
            facility: Current facility
            time_elapsed_minutes: Time since injury
            available_resources: Available resources
            max_treatments: Maximum number of treatments to select

        Returns:
            List of selected treatments with metadata
        """
        available_resources = available_resources or {"supplies": 100}

        # First, get recommended treatments for this specific injury
        protocol = self.protocols.get("treatment_appropriateness_matrix", {}).get(injury_code, {})
        primary_treatments = protocol.get("primary_treatments", {}).get(facility, [])

        # If we have specific treatments for this injury, use those
        if primary_treatments:
            possible_treatments = primary_treatments
        else:
            # Otherwise, get all possible treatments for this facility
            possible_treatments = self.facility_capabilities.get(facility, [])

        # Check for contraindicated treatments
        contraindicated = protocol.get("contraindicated_treatments", [])

        if not possible_treatments:
            # Fallback to default treatment
            default = self.protocols.get("default_fallbacks", {}).get(facility, "basic_bandage")
            return [{"name": default, "utility_score": 0.5, "applied_at": datetime.now()}]

        # Calculate utilities for possible treatments
        treatment_utilities = []
        for treatment in possible_treatments:
            if treatment == "all":  # Skip meta-indicator
                continue

            # Skip contraindicated treatments
            if treatment in contraindicated:
                continue

            utility = self.calculate_utility(
                treatment, injury_code, severity, facility, time_elapsed_minutes, available_resources
            )

            # Only consider treatments with positive utility
            if utility > 0.2:  # Threshold for minimum viability
                treatment_utilities.append({"name": treatment, "utility": utility})

        if not treatment_utilities:
            # No viable treatments, use injury-appropriate fallback
            if "45170000" in injury_code:  # Psychological stress
                return [{"name": "psychological_first_aid", "utility_score": 0.5, "applied_at": datetime.now()}]
            if "62315008" in injury_code:  # Diarrhea
                return [{"name": "oral_rehydration", "utility_score": 0.5, "applied_at": datetime.now()}]
            default = self.protocols.get("default_fallbacks", {}).get(facility, "supportive_care")
            return [{"name": default, "utility_score": 0.3, "applied_at": datetime.now()}]

        # Apply softmax to convert utilities to probabilities
        selected = self._softmax_selection(treatment_utilities, max_treatments)

        # Format results
        results = []
        for treatment in selected:
            results.append(
                {
                    "name": treatment["name"],
                    "utility_score": round(treatment["utility"], 3),
                    "applied_at": datetime.now(),
                    "facility": facility,
                }
            )

        return results

    def _softmax_selection(
        self, treatment_utilities: List[Dict[str, Any]], max_selections: int
    ) -> List[Dict[str, Any]]:
        """
        Select treatments using softmax probability distribution.

        P(treatment) = exp(utility/τ) / Σ exp(utilities/τ)
        """
        if not treatment_utilities:
            return []

        # Extract utilities
        utilities = np.array([t["utility"] for t in treatment_utilities])

        # Apply softmax with temperature
        exp_utilities = np.exp(utilities / self.TEMPERATURE)
        probabilities = exp_utilities / np.sum(exp_utilities)

        # Select treatments probabilistically
        n_selections = min(max_selections, len(treatment_utilities))

        # Use numpy's random choice with probabilities
        indices = np.random.choice(  # noqa: NPY002
            len(treatment_utilities), size=min(n_selections, len(treatment_utilities)), replace=False, p=probabilities
        )

        selected = [treatment_utilities[i] for i in indices]

        # Sort by utility (highest first)
        selected.sort(key=lambda x: x["utility"], reverse=True)

        return selected

    def get_treatment_for_snomed(self, snomed_code: str, facility: str = "POI") -> List[str]:
        """
        Get recommended treatments for a SNOMED code at a facility.

        Simple interface for basic treatment lookup.
        """
        protocol = self.protocols.get("treatment_appropriateness_matrix", {}).get(snomed_code, {})
        primary_treatments = protocol.get("primary_treatments", {}).get(facility, [])

        if primary_treatments:
            return primary_treatments[:3]  # Return top 3 treatments

        # Return facility default
        default = self.protocols.get("default_fallbacks", {}).get(facility, "supportive_care")
        return [default]

    def validate_treatment_selection(self, treatment: str, injury_code: str, facility: str) -> Tuple[bool, str]:
        """
        Validate if a treatment is appropriate for an injury at a facility.

        Returns:
            Tuple of (is_valid, reason)
        """
        # Check contraindications
        protocol = self.protocols.get("treatment_appropriateness_matrix", {}).get(injury_code, {})
        contraindicated = protocol.get("contraindicated_treatments", [])

        if treatment in contraindicated:
            return False, f"Treatment {treatment} is contraindicated for {injury_code}"

        # Check facility capability
        if not self._check_facility_capability(treatment, facility):
            return False, f"Treatment {treatment} not available at {facility}"

        # Check appropriateness score
        score = self._get_appropriateness_score(treatment, injury_code)
        if score < 0.2:
            return False, f"Treatment {treatment} has low appropriateness score ({score:.2f})"

        return True, "Treatment is appropriate"
