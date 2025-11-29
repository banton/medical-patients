"""
Triage Mapper for Medical Simulation
Maps patient conditions to military triage categories
"""

from typing import Dict, List, Optional, Tuple


class TriageMapper:
    """
    Maps patient health status and injuries to triage categories.
    Implements military triage protocols (T1/T2/T3/T4).
    """

    def __init__(self):
        """Initialize triage category definitions"""
        self.categories = self._define_categories()
        self.injury_triage_map = self._define_injury_mappings()

    def _define_categories(self) -> Dict[str, Dict]:
        """Define military triage categories"""
        return {
            "T1": {
                "name": "Immediate",
                "color": "red",
                "priority": 1,
                "description": "Life-threatening injuries requiring immediate treatment",
                "health_range": (0, 40),
                "max_wait_minutes": 60,
                "examples": ["Airway obstruction", "Tension pneumothorax", "Uncontrolled hemorrhage", "Severe shock"],
            },
            "T2": {
                "name": "Delayed",
                "color": "yellow",
                "priority": 2,
                "description": "Urgent injuries that can wait short period",
                "health_range": (40, 70),
                "max_wait_minutes": 240,
                "examples": ["Open fractures", "Moderate burns", "Stable abdominal wounds", "Eye injuries"],
            },
            "T3": {
                "name": "Minimal",
                "color": "green",
                "priority": 3,
                "description": "Minor injuries, ambulatory patients",
                "health_range": (70, 100),
                "max_wait_minutes": 1440,
                "examples": ["Minor lacerations", "Sprains", "Minor burns", "Walking wounded"],
            },
            "T4": {
                "name": "Expectant",
                "color": "black",
                "priority": 4,
                "description": "Injuries incompatible with life given resources",
                "health_range": (-1, 10),
                "max_wait_minutes": 0,
                "examples": ["Massive head trauma", "90% burns", "Exposed brain matter", "Agonal respirations"],
            },
        }

    def _define_injury_mappings(self) -> Dict[str, Dict]:
        """Map specific injury patterns to triage categories"""
        return {
            # Immediate (T1) conditions
            "arterial_bleeding": {"category": "T1", "modifier": -10},
            "airway_compromise": {"category": "T1", "modifier": -15},
            "tension_pneumothorax": {"category": "T1", "modifier": -20},
            "hemorrhagic_shock": {"category": "T1", "modifier": -25},
            "severe_tbi": {"category": "T1", "modifier": -30},
            # Delayed (T2) conditions
            "open_fracture": {"category": "T2", "modifier": -5},
            "closed_head_injury": {"category": "T2", "modifier": -10},
            "penetrating_abdomen": {"category": "T2", "modifier": -8},
            "moderate_burns": {"category": "T2", "modifier": -5},
            # Minimal (T3) conditions
            "simple_fracture": {"category": "T3", "modifier": 0},
            "laceration": {"category": "T3", "modifier": 0},
            "minor_burns": {"category": "T3", "modifier": 0},
            "sprain": {"category": "T3", "modifier": 0},
            # Expectant (T4) conditions
            "massive_head_trauma": {"category": "T4", "modifier": -50},
            "full_thickness_burns_90": {"category": "T4", "modifier": -60},
            "traumatic_arrest": {"category": "T4", "modifier": -100},
        }

    def calculate_triage_category(
        self,
        health_score: int,
        injury_severity: str,
        specific_injuries: Optional[List[str]] = None,
        mass_casualty: bool = False,
    ) -> Tuple[str, Dict]:
        """
        Calculate triage category for a patient.

        Args:
            health_score: Current health (0-100)
            injury_severity: Overall severity level
            specific_injuries: List of specific injury codes
            mass_casualty: Whether this is a mass casualty event

        Returns:
            Tuple of (category, details)
        """
        # Start with health-based category
        base_category = self._get_category_by_health(health_score)

        # Check for specific injury overrides
        if specific_injuries:
            for injury in specific_injuries:
                injury_lower = injury.lower()
                for pattern, mapping in self.injury_triage_map.items():
                    if pattern in injury_lower:
                        override_cat = mapping["category"]
                        # Immediate conditions always override
                        if override_cat == "T1":
                            base_category = "T1"
                            break
                        # Expectant overrides if health very low
                        if override_cat == "T4" and health_score < 20:
                            base_category = "T4"
                            break

        # Mass casualty adjustments
        if mass_casualty:
            base_category = self._adjust_for_mass_casualty(base_category, health_score, injury_severity)

        # Get category details
        details = self.categories[base_category].copy()
        details["assigned_category"] = base_category
        details["health_score"] = health_score
        details["mass_casualty_adjusted"] = mass_casualty

        return base_category, details

    def _get_category_by_health(self, health: int) -> str:
        """Get base category from health score"""
        if health < 10:
            return "T4"  # Expectant
        if health < 40:
            return "T1"  # Immediate
        if health < 70:
            return "T2"  # Delayed
        return "T3"  # Minimal

    def _adjust_for_mass_casualty(self, category: str, health: int, severity: str) -> str:
        """
        Adjust triage in mass casualty situations.
        More conservative with resources.
        """
        # In mass casualty, borderline T1 might become T4
        if category == "T1" and health < 15 and severity == "Severe":
            return "T4"  # Save resources for more viable patients

        # Borderline T2 might become T3
        if category == "T2" and health > 65 and severity in ["Mild to moderate", "Mild"]:
            return "T3"  # Can wait longer

        return category

    def get_bed_assignment(self, triage_category: str) -> str:
        """
        Get appropriate bed type for triage category.

        Returns:
            Bed type (T1_bed, T2_bed, T3_bed, or None)
        """
        bed_map = {
            "T1": "T1_bed",  # ICU/Resuscitation
            "T2": "T2_bed",  # Urgent care
            "T3": "T3_bed",  # Routine care
            "T4": None,  # Comfort care only
        }
        return bed_map.get(triage_category)

    def calculate_treatment_priority(self, patients: List[Dict]) -> List[Dict]:
        """
        Sort patients by treatment priority.

        Args:
            patients: List of patient dicts with health and triage info

        Returns:
            Sorted list by priority
        """
        # Add priority scores
        for patient in patients:
            category = patient.get("triage_category", "T3")
            cat_priority = self.categories[category]["priority"]

            # Within category, prioritize by health (lower health = more urgent)
            health = patient.get("health_score", 50)

            # Combined score (category is primary, health is secondary)
            # Lower priority_score = higher priority, so use health directly
            patient["priority_score"] = cat_priority * 1000 + health

        # Sort by priority score (lower = higher priority)
        return sorted(patients, key=lambda x: x["priority_score"])

    def estimate_survival_probability(
        self, triage_category: str, wait_time_minutes: int, has_treatment: bool = False
    ) -> float:
        """
        Estimate survival probability based on triage and wait time.

        Returns:
            Probability of survival (0.0 to 1.0)
        """
        base_survival = {
            "T1": 0.7,  # With immediate treatment
            "T2": 0.9,  # Good prognosis
            "T3": 0.99,  # Minor injuries
            "T4": 0.05,  # Poor prognosis
        }

        prob = base_survival.get(triage_category, 0.5)
        max_wait = self.categories[triage_category]["max_wait_minutes"]

        # Reduce survival for excessive wait
        if max_wait > 0 and wait_time_minutes > max_wait:
            excess_ratio = wait_time_minutes / max_wait
            prob *= 1.0 / excess_ratio  # Exponential decay

        # Treatment improves odds
        if has_treatment:
            prob = min(1.0, prob * 1.2)

        return max(0.0, min(1.0, prob))


if __name__ == "__main__":
    # Test the triage system
    tm = TriageMapper()

    # Test different scenarios
    scenarios = [
        (25, "Severe", ["arterial bleeding"], False),
        (60, "Moderate", ["open fracture"], False),
        (80, "Mild", ["laceration"], False),
        (5, "Severe", ["massive head trauma"], False),
        (35, "Severe", ["hemorrhage"], True),  # Mass casualty
    ]

    print("Triage Category Assignments:")
    print("-" * 60)

    for health, severity, injuries, mass_cas in scenarios:
        category, details = tm.calculate_triage_category(health, severity, injuries, mass_cas)

        mass_str = " (MASCAL)" if mass_cas else ""
        print(f"Health: {health:3d}%, Severity: {severity:15s}, Injuries: {injuries[0]:20s}")
        print(f"  → {category} ({details['name']}){mass_str}")
        print(f"     Max wait: {details['max_wait_minutes']} min")
        print()

    # Test priority sorting
    patients = [
        {"id": 1, "health_score": 25, "triage_category": "T1"},
        {"id": 2, "health_score": 60, "triage_category": "T2"},
        {"id": 3, "health_score": 15, "triage_category": "T1"},
        {"id": 4, "health_score": 80, "triage_category": "T3"},
    ]

    sorted_patients = tm.calculate_treatment_priority(patients)
    print("Treatment Priority Order:")
    for p in sorted_patients:
        print(f"  Patient {p['id']}: {p['triage_category']} (score: {p['priority_score']})")
