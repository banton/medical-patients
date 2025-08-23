"""
Warfare Pattern Modifiers - Injury Patterns Based on Combat Type

This module defines injury patterns, severity distributions, and polytrauma
correlations for different warfare scenarios. Based on military medical data
from modern conflicts.

Author: Medical SME Agent + Probabilistic Math SME Agent
Version: 1.0.0
"""

from dataclasses import dataclass
import random
from typing import Any, Dict, List, Optional, Tuple

import numpy as np


@dataclass
class WarfarePattern:
    """Defines injury patterns for a specific type of warfare."""
    name: str
    description: str
    injury_distribution: Dict[str, float]  # SNOMED code -> probability
    severity_modifier: float  # Multiplier for injury severity
    polytrauma_rate: float  # Probability of multiple injuries
    mortality_modifier: float  # Affects base mortality rates
    mass_casualty_probability: float  # Chance of multiple casualties
    environmental_factors: Dict[str, Any]  # Additional modifiers


class WarfareModifiers:
    """
    Manages warfare-specific injury patterns and modifiers.

    Key Features:
    - Artillery: Blast injuries, traumatic amputations, burns
    - Urban: GSW, building collapse, secondary blast
    - IED: Asymmetric injuries, lower extremity trauma
    - Conventional: Mixed small arms and indirect fire
    """

    def __init__(self):
        """Initialize warfare patterns based on military medical data."""
        self.patterns = self._define_warfare_patterns()
        self.injury_correlations = self._define_injury_correlations()
        self.body_regions = self._define_body_regions()

    def _define_warfare_patterns(self) -> Dict[str, WarfarePattern]:
        """Define distinct patterns for each warfare type."""

        return {
            "artillery": WarfarePattern(
                name="Artillery/Indirect Fire",
                description="Heavy indirect fire with blast injuries predominant",
                injury_distribution={
                    # Blast injuries
                    "125596004": 0.35,  # Injury by explosive
                    "361220002": 0.20,  # Penetrating injury (shrapnel)
                    "7200002": 0.15,    # Burn of skin
                    "125689001": 0.10,  # Traumatic amputation
                    "127294003": 0.08,  # Traumatic brain injury
                    "275272006": 0.05,  # Injury of abdomen
                    "125605004": 0.05,  # Fracture of bone
                    "267036007": 0.02,  # Dyspnea (blast lung)
                },
                severity_modifier=1.3,  # More severe injuries
                polytrauma_rate=0.65,   # High polytrauma rate
                mortality_modifier=1.2,  # Higher mortality
                mass_casualty_probability=0.40,  # Often hits multiple
                environmental_factors={
                    "blast_overpressure": True,
                    "fragmentation_pattern": "radial",
                    "burn_risk": "high",
                    "structure_collapse": 0.15
                }
            ),

            "urban": WarfarePattern(
                name="Urban Combat",
                description="Close quarters combat with mixed threats",
                injury_distribution={
                    # Mixed GSW and blast
                    "262574004": 0.30,  # Gunshot wound
                    "361220002": 0.25,  # Penetrating injury
                    "125596004": 0.15,  # Injury by explosive (grenades)
                    "2055003": 0.10,    # Laceration
                    "125605004": 0.08,  # Fracture (falls, debris)
                    "127294003": 0.05,  # TBI (building collapse)
                    "409711008": 0.04,  # Crush injury
                    "16932000": 0.03,   # Nausea and vomiting (stress)
                },
                severity_modifier=1.1,
                polytrauma_rate=0.45,
                mortality_modifier=1.0,
                mass_casualty_probability=0.25,
                environmental_factors={
                    "confined_spaces": True,
                    "multiple_threats": True,
                    "limited_evacuation": True,
                    "civilian_mix": 0.30
                }
            ),

            "ied": WarfarePattern(
                name="IED/Asymmetric",
                description="Improvised explosive devices with under-vehicle focus",
                injury_distribution={
                    # Lower extremity focus
                    "125689001": 0.25,  # Traumatic amputation (legs)
                    "125596004": 0.20,  # Injury by explosive
                    "361220002": 0.15,  # Penetrating injury (upward)
                    "7200002": 0.12,    # Burns
                    "125605004": 0.10,  # Fractures (pelvis, spine)
                    "275272006": 0.08,  # Abdominal injury
                    "127294003": 0.07,  # TBI (vehicle rollover)
                    "68566005": 0.03,   # Urinary tract injury
                },
                severity_modifier=1.4,  # Very severe injuries
                polytrauma_rate=0.70,   # Very high polytrauma
                mortality_modifier=1.3,  # High mortality
                mass_casualty_probability=0.35,  # Vehicle occupants
                environmental_factors={
                    "blast_direction": "upward",
                    "vehicle_entrapment": 0.40,
                    "fire_risk": 0.25,
                    "delayed_evacuation": True
                }
            ),

            "conventional": WarfarePattern(
                name="Conventional Warfare",
                description="Traditional combined arms with mixed injury patterns",
                injury_distribution={
                    # Balanced mix
                    "262574004": 0.25,  # Gunshot wound
                    "125596004": 0.20,  # Explosive injury
                    "361220002": 0.15,  # Penetrating injury
                    "125605004": 0.12,  # Fracture
                    "2055003": 0.10,    # Laceration
                    "275272006": 0.06,  # Abdominal injury
                    "127294003": 0.05,  # TBI
                    "7200002": 0.04,    # Burns
                    "125689001": 0.03,  # Amputation
                },
                severity_modifier=1.0,  # Baseline severity
                polytrauma_rate=0.40,   # Moderate polytrauma
                mortality_modifier=1.0,  # Baseline mortality
                mass_casualty_probability=0.20,  # Some mass casualties
                environmental_factors={
                    "combined_arms": True,
                    "varied_weapons": True,
                    "standard_evacuation": True
                }
            ),

            "mixed": WarfarePattern(
                name="Mixed/Hybrid",
                description="Combination of conventional and asymmetric threats",
                injury_distribution={
                    # Even more balanced
                    "262574004": 0.20,  # GSW
                    "125596004": 0.18,  # Explosive
                    "361220002": 0.16,  # Penetrating
                    "125605004": 0.12,  # Fracture
                    "2055003": 0.10,    # Laceration
                    "125689001": 0.06,  # Amputation
                    "275272006": 0.06,  # Abdominal
                    "127294003": 0.05,  # TBI
                    "7200002": 0.04,    # Burns
                    "16932000": 0.03,   # Stress/psychological
                },
                severity_modifier=1.1,
                polytrauma_rate=0.50,
                mortality_modifier=1.1,
                mass_casualty_probability=0.30,
                environmental_factors={
                    "unpredictable": True,
                    "mixed_threats": True,
                    "variable_intensity": True
                }
            )
        }


    def _define_injury_correlations(self) -> Dict[str, List[str]]:
        """Define which injuries commonly occur together (polytrauma)."""

        return {
            # Blast polytrauma pattern
            "125596004": [  # Injury by explosive often with:
                "361220002",  # Penetrating injury (shrapnel)
                "7200002",    # Burns
                "127294003",  # TBI
                "267036007",  # Blast lung
            ],

            # IED polytrauma pattern
            "125689001": [  # Traumatic amputation often with:
                "125605004",  # Pelvic/spine fractures
                "275272006",  # Abdominal injury
                "68566005",   # Genitourinary injury
                "7200002",    # Burns
            ],

            # Penetrating trauma pattern
            "361220002": [  # Penetrating injury often with:
                "275272006",  # Abdominal injury
                "125605004",  # Fractures
                "87991007",   # Hemothorax
            ],

            # TBI pattern
            "127294003": [  # TBI often with:
                "125605004",  # Skull fractures
                "2055003",    # Facial lacerations
                "409711008",  # Crush injuries
            ],

            # GSW pattern
            "262574004": [  # Gunshot wound often with:
                "361220002",  # Penetrating injury
                "125605004",  # Fractures
                "275272006",  # Internal organ damage
            ]
        }


    def _define_body_regions(self) -> Dict[str, List[str]]:
        """Define body regions for injury localization."""

        return {
            "head_neck": ["127294003", "2055003", "62315008"],
            "thorax": ["87991007", "267036007", "125596004"],
            "abdomen": ["275272006", "68566005", "25374005"],
            "extremities": ["125689001", "125605004", "2055003"],
            "multiple": ["125596004", "361220002", "409711008"]
        }


    def get_injuries_for_scenario(
        self,
        scenario: str,
        base_injuries: Optional[List[str]] = None
    ) -> Tuple[List[str], int, Dict[str, Any]]:
        """
        Generate injuries based on warfare scenario.

        Args:
            scenario: Type of warfare (artillery, urban, ied, etc.)
            base_injuries: Optional predetermined injuries to modify

        Returns:
            Tuple of (injury_codes, severity, metadata)
        """
        pattern = self.patterns.get(scenario, self.patterns["mixed"])

        # Determine if polytrauma occurs
        is_polytrauma = random.random() < pattern.polytrauma_rate

        # Select primary injury
        injuries = []
        if base_injuries:
            injuries.extend(base_injuries)
        else:
            # Weight selection by distribution
            injury_codes = list(pattern.injury_distribution.keys())
            probabilities = list(pattern.injury_distribution.values())
            primary_injury = np.random.choice(injury_codes, p=probabilities)  # noqa: NPY002
            injuries.append(primary_injury)

        # Add correlated injuries for polytrauma
        if is_polytrauma and injuries:
            primary = injuries[0]
            if primary in self.injury_correlations:
                # Add 1-3 correlated injuries
                num_additional = min(3, np.random.poisson(1.5))  # noqa: NPY002
                correlated = self.injury_correlations[primary]
                additional = random.sample(
                    correlated,
                    min(num_additional, len(correlated))
                )
                injuries.extend(additional)

        # Calculate severity (1-10 scale)
        base_severity = random.randint(3, 8)
        if is_polytrauma:
            base_severity += 2

        modified_severity = int(base_severity * pattern.severity_modifier)
        modified_severity = min(10, max(1, modified_severity))

        # Build metadata
        metadata = {
            "warfare_type": scenario,
            "polytrauma": is_polytrauma,
            "injury_count": len(injuries),
            "environmental_factors": pattern.environmental_factors,
            "mass_casualty": random.random() < pattern.mass_casualty_probability,
            "mortality_modifier": pattern.mortality_modifier
        }

        return injuries, modified_severity, metadata

    def get_scenario_modifiers(self, scenario: str) -> Dict[str, Any]:
        """
        Get modifiers for a specific warfare scenario.

        Args:
            scenario: Type of warfare

        Returns:
            Dictionary of modifiers for patient generation
        """
        pattern = self.patterns.get(scenario, self.patterns["mixed"])

        return {
            "severity_modifier": pattern.severity_modifier,
            "mortality_modifier": pattern.mortality_modifier,
            "mass_casualty_probability": pattern.mass_casualty_probability,
            "polytrauma_rate": pattern.polytrauma_rate,
            "environmental_factors": pattern.environmental_factors
        }

    def analyze_injury_pattern(self, injuries: List[str]) -> str:
        """
        Analyze a list of injuries to determine likely warfare type.

        Args:
            injuries: List of SNOMED codes

        Returns:
            Most likely warfare scenario
        """
        if not injuries:
            return "mixed"

        # Score each pattern
        scores = {}
        for scenario, pattern in self.patterns.items():
            score = 0
            for injury in injuries:
                if injury in pattern.injury_distribution:
                    score += pattern.injury_distribution[injury]
            scores[scenario] = score

        # Return highest scoring scenario
        return max(scores, key=scores.get)


# Utility functions for integration

def create_warfare_modifiers() -> WarfareModifiers:
    """Factory function to create WarfareModifiers instance."""
    return WarfareModifiers()


def test_warfare_patterns():
    """Test warfare pattern generation."""
    modifiers = WarfareModifiers()

    print("Testing Warfare Pattern Generation")
    print("=" * 60)

    scenarios = ["artillery", "urban", "ied", "conventional", "mixed"]

    for scenario in scenarios:
        print(f"\n{scenario.upper()} Warfare Pattern:")
        print("-" * 40)

        # Generate 5 casualties
        for i in range(5):
            injuries, severity, metadata = modifiers.get_injuries_for_scenario(scenario)

            print(f"Casualty {i+1}:")
            print(f"  Injuries: {len(injuries)} codes")
            print(f"  Severity: {severity}/10")
            print(f"  Polytrauma: {metadata['polytrauma']}")
            print(f"  Mass casualty: {metadata['mass_casualty']}")

            if i == 0:  # Show first casualty details
                print(f"  Injury codes: {injuries[:3]}...")  # First 3 codes

    # Test pattern analysis
    print("\n" + "=" * 60)
    print("Testing Pattern Analysis:")

    test_cases = [
        (["125596004", "361220002", "7200002"], "artillery"),  # Blast pattern
        (["262574004", "361220002"], "urban"),  # GSW pattern
        (["125689001", "125605004", "275272006"], "ied"),  # IED pattern
    ]

    for injuries, expected in test_cases:
        detected = modifiers.analyze_injury_pattern(injuries)
        result = "✓" if detected == expected else "✗"
        print(f"  {result} Injuries {injuries[:2]}... detected as: {detected} (expected: {expected})")


if __name__ == "__main__":
    test_warfare_patterns()
