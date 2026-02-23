"""
Enhanced Medical Condition Generator with Hemorrhage Modeling.
Extends the existing MedicalConditionGenerator to include hemorrhage profiles.
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Any, Dict, List

from patient_generator.hemorrhage import BodyRegion, HemorrhageModel
from patient_generator.hemorrhage.integration import HemorrhageIntegration
from patient_generator.medical import MedicalConditionGenerator


class EnhancedMedicalConditionGenerator(MedicalConditionGenerator):
    """Extended medical condition generator with hemorrhage modeling."""

    def __init__(self):
        super().__init__()
        self.hemorrhage_model = HemorrhageModel()
        self.hemorrhage_integration = HemorrhageIntegration()

    def generate_condition_with_hemorrhage(
        self, injury_type: str, triage_category: str, include_body_location: bool = True
    ) -> Dict[str, Any]:
        """
        Generate a medical condition with hemorrhage profile.

        Args:
            injury_type: Type of injury (Battle, Non-Battle, Disease)
            triage_category: Triage level (T1, T2, T3)
            include_body_location: Whether to include body location

        Returns:
            Enhanced condition dictionary with hemorrhage data
        """
        # Generate base condition using parent method
        condition = self.generate_condition(injury_type, triage_category)

        # Add hemorrhage profile if it's a trauma condition
        if injury_type.upper() != "DISEASE":
            hemorrhage_profile = self.hemorrhage_model.calculate_hemorrhage_profile(
                injury_code=condition["code"], severity=condition["severity"]
            )

            # Add hemorrhage data to condition
            condition["hemorrhage"] = {
                "has_hemorrhage": hemorrhage_profile.category.value != "no_hemorrhage",
                "category": hemorrhage_profile.category.value,
                "bleeding_rate_alpha": hemorrhage_profile.alpha_0,
                "lethal_triad_k": hemorrhage_profile.k,
                "blood_loss_ml_min": hemorrhage_profile.blood_loss_ml_per_min,
                "time_to_critical_min": hemorrhage_profile.time_to_exsanguination_min,
            }

            if include_body_location:
                condition["body_location"] = {
                    "region": hemorrhage_profile.body_location.region.value,
                    "specific_area": hemorrhage_profile.body_location.specific_area,
                    "tourniquetable": hemorrhage_profile.body_location.tourniquetable,
                    "major_vessels": hemorrhage_profile.body_location.major_vessels,
                    "organs": hemorrhage_profile.body_location.organs,
                }
        else:
            condition["hemorrhage"] = {"has_hemorrhage": False}

        return condition

    def generate_multiple_conditions_with_hemorrhage(
        self, injury_type: str, triage_category: str, count: int = 2
    ) -> List[Dict[str, Any]]:
        """
        Generate multiple conditions with hemorrhage profiles.

        Args:
            injury_type: Type of injury
            triage_category: Triage level
            count: Number of conditions to generate

        Returns:
            List of enhanced condition dictionaries
        """
        # Generate base conditions
        conditions = self.generate_multiple_conditions(injury_type, triage_category, count)

        # Distribute injuries across body regions for realism
        if injury_type.upper() != "DISEASE":
            body_regions = self._get_injury_distribution(count)

            for i, condition in enumerate(conditions):
                hemorrhage_profile = self.hemorrhage_model.calculate_hemorrhage_profile(
                    injury_code=condition["code"],
                    body_region=body_regions[i] if i < len(body_regions) else None,
                    severity=condition["severity"],
                    multiple_injuries=count > 1,
                )

                # Add hemorrhage and location data
                condition["hemorrhage"] = {
                    "has_hemorrhage": hemorrhage_profile.category.value != "no_hemorrhage",
                    "category": hemorrhage_profile.category.value,
                    "bleeding_rate_alpha": hemorrhage_profile.alpha_0,
                    "lethal_triad_k": hemorrhage_profile.k,
                    "blood_loss_ml_min": hemorrhage_profile.blood_loss_ml_per_min,
                    "time_to_critical_min": hemorrhage_profile.time_to_exsanguination_min,
                }

                condition["body_location"] = {
                    "region": hemorrhage_profile.body_location.region.value,
                    "specific_area": hemorrhage_profile.body_location.specific_area,
                    "tourniquetable": hemorrhage_profile.body_location.tourniquetable,
                }

        return conditions

    def calculate_combined_hemorrhage_effects(self, conditions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate combined hemorrhage effects from multiple conditions.

        Args:
            conditions: List of conditions with hemorrhage data

        Returns:
            Combined hemorrhage summary
        """
        total_blood_loss = 0.0
        max_alpha = 0.0
        max_k = 0.0
        requires_tourniquet = False
        requires_surgery = False
        affected_regions = []

        for condition in conditions:
            if condition.get("hemorrhage", {}).get("has_hemorrhage"):
                hemorrhage = condition["hemorrhage"]
                total_blood_loss += hemorrhage.get("blood_loss_ml_min", 0)
                max_alpha = max(max_alpha, hemorrhage.get("bleeding_rate_alpha", 0))
                max_k = max(max_k, hemorrhage.get("lethal_triad_k", 0))

                if condition.get("body_location", {}).get("tourniquetable"):
                    requires_tourniquet = True

                if hemorrhage.get("category") in ["torso_wound", "massive_hemorrhage"]:
                    requires_surgery = True

                region = condition.get("body_location", {}).get("region")
                if region and region not in affected_regions:
                    affected_regions.append(region)

        # Calculate time to critical (40% blood loss = 2000ml)
        time_to_critical = 2000 / total_blood_loss if total_blood_loss > 0 else float("inf")

        # Determine overall severity
        if time_to_critical < 10:
            severity = "critical"
            recommended_triage = "T1"
        elif time_to_critical < 30:
            severity = "severe"
            recommended_triage = "T1"
        elif time_to_critical < 60:
            severity = "moderate"
            recommended_triage = "T2"
        else:
            severity = "mild"
            recommended_triage = "T3"

        return {
            "total_blood_loss_ml_min": total_blood_loss,
            "max_bleeding_rate_alpha": max_alpha,
            "max_lethal_triad_k": max_k,
            "time_to_critical_min": time_to_critical,
            "severity": severity,
            "recommended_triage": recommended_triage,
            "requires_tourniquet": requires_tourniquet,
            "requires_surgery": requires_surgery,
            "affected_body_regions": affected_regions,
            "number_of_bleeding_sites": len([c for c in conditions if c.get("hemorrhage", {}).get("has_hemorrhage")]),
        }

    @staticmethod
    def _get_injury_distribution(count: int) -> List[BodyRegion]:
        """Get realistic body region distribution for multiple injuries."""
        import random

        if count == 1:
            # Single injury - common locations
            return [random.choice([BodyRegion.CHEST, BodyRegion.ABDOMEN, BodyRegion.LEFT_LEG, BodyRegion.RIGHT_LEG])]
        if count == 2:
            # Two injuries - often related regions
            patterns = [
                [BodyRegion.LEFT_LEG, BodyRegion.RIGHT_LEG],  # Bilateral lower
                [BodyRegion.CHEST, BodyRegion.ABDOMEN],  # Torso
                [BodyRegion.LEFT_ARM, BodyRegion.CHEST],  # Upper body
            ]
            return random.choice(patterns)
        # Multiple injuries - blast/polytrauma pattern
        return [
            BodyRegion.CHEST,
            BodyRegion.ABDOMEN,
            random.choice([BodyRegion.LEFT_LEG, BodyRegion.RIGHT_LEG]),
            random.choice([BodyRegion.LEFT_ARM, BodyRegion.RIGHT_ARM]),
        ][:count]


def demonstrate_enhanced_generator():
    """Demonstrate the enhanced medical generator with hemorrhage."""

    generator = EnhancedMedicalConditionGenerator()

    print("=" * 60)
    print("ENHANCED MEDICAL CONDITION GENERATOR WITH HEMORRHAGE MODEL")
    print("=" * 60)

    # Example 1: Single severe battle injury
    print("\n1. SINGLE SEVERE BATTLE INJURY (T1)")
    print("-" * 40)
    condition = generator.generate_condition_with_hemorrhage("Battle Injury", "T1")
    print(f"Condition: {condition['display']}")
    print(f"Severity: {condition['severity']}")
    if condition["hemorrhage"]["has_hemorrhage"]:
        print(f"Hemorrhage Category: {condition['hemorrhage']['category']}")
        print(f"Blood Loss Rate: {condition['hemorrhage']['blood_loss_ml_min']:.1f} ml/min")
        print(f"Time to Critical: {condition['hemorrhage']['time_to_critical_min']:.1f} min")
        print(f"Body Region: {condition['body_location']['region']}")
        print(f"Tourniquetable: {condition['body_location']['tourniquetable']}")

    # Example 2: Multiple injuries (polytrauma)
    print("\n2. POLYTRAUMA - MULTIPLE INJURIES (T1)")
    print("-" * 40)
    conditions = generator.generate_multiple_conditions_with_hemorrhage("Battle Injury", "T1", count=3)
    for i, cond in enumerate(conditions, 1):
        print(f"\nInjury {i}: {cond['display']} ({cond['severity']})")
        if cond["hemorrhage"]["has_hemorrhage"]:
            print(f"  - Location: {cond['body_location']['region']}")
            print(f"  - Blood Loss: {cond['hemorrhage']['blood_loss_ml_min']:.1f} ml/min")
            print(f"  - Tourniquetable: {cond['body_location']['tourniquetable']}")

    # Calculate combined effects
    combined = generator.calculate_combined_hemorrhage_effects(conditions)
    print("\nCOMBINED HEMORRHAGE EFFECTS:")
    print(f"  Total Blood Loss: {combined['total_blood_loss_ml_min']:.1f} ml/min")
    print(f"  Time to Critical: {combined['time_to_critical_min']:.1f} min")
    print(f"  Severity: {combined['severity']}")
    print(f"  Recommended Triage: {combined['recommended_triage']}")
    print(f"  Requires Tourniquet: {combined['requires_tourniquet']}")
    print(f"  Requires Surgery: {combined['requires_surgery']}")
    print(f"  Affected Regions: {', '.join(combined['affected_body_regions'])}")

    # Example 3: Non-battle injury
    print("\n3. NON-BATTLE INJURY (T2)")
    print("-" * 40)
    condition = generator.generate_condition_with_hemorrhage("Non-Battle Injury", "T2")
    print(f"Condition: {condition['display']}")
    print(f"Severity: {condition['severity']}")
    if condition["hemorrhage"]["has_hemorrhage"]:
        print(f"Hemorrhage Category: {condition['hemorrhage']['category']}")
        print(f"Blood Loss Rate: {condition['hemorrhage']['blood_loss_ml_min']:.1f} ml/min")
    else:
        print("No significant hemorrhage")

    # Example 4: Disease (no hemorrhage)
    print("\n4. DISEASE CONDITION (T3)")
    print("-" * 40)
    condition = generator.generate_condition_with_hemorrhage("Disease", "T3")
    print(f"Condition: {condition['display']}")
    print(f"Severity: {condition['severity']}")
    print(f"Has Hemorrhage: {condition['hemorrhage']['has_hemorrhage']}")


if __name__ == "__main__":
    demonstrate_enhanced_generator()
