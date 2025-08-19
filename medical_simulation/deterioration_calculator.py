"""
Deterioration Calculator for Medical Simulation
Calculates patient health deterioration based on injuries and conditions
"""
import json
import random
from typing import Dict, List, Optional


class DeteriorationCalculator:
    """
    Calculates deterioration rates based on injury patterns and conditions.
    Works with Health Score Engine to model patient decline over time.
    """

    def __init__(self, injuries_config_path: str = "patient_generator/injuries.json"):
        """Initialize with injuries configuration"""
        with open(injuries_config_path) as f:
            self.config = json.load(f)
        self.deterioration_model = self.config.get("deterioration_model", {})
        self.environmental_modifiers = self.config.get("environmental_modifiers", {})

    def calculate_base_deterioration(
        self,
        injury_type: str,
        severity: str,
        injuries: Optional[List[Dict]] = None
    ) -> float:
        """
        Calculate base deterioration rate from injury profile.

        Args:
            injury_type: "Battle Injury", "Non-Battle Injury", or "Disease"
            severity: Injury severity level
            injuries: Optional list of specific injuries

        Returns:
            Base deterioration rate per hour (0-100 scale)
        """
        # Get base rate from model
        if injury_type not in self.deterioration_model:
            return 5.0  # Default mild deterioration

        severity_data = self.deterioration_model[injury_type].get(severity, {})
        base_rate = severity_data.get("deterioration_rate", 5.0)

        # Check for hemorrhage multiplier
        if injuries:
            for injury in injuries:
                if self._has_hemorrhage(injury):
                    multiplier = severity_data.get("hemorrhage_multiplier", 1.5)
                    base_rate *= multiplier
                    break  # Apply once

        return min(100.0, base_rate)  # Cap at 100

    def _has_hemorrhage(self, injury: Dict) -> bool:
        """Check if injury involves significant bleeding"""
        hemorrhage_keywords = [
            "hemorrhage", "bleeding", "laceration", "amputation",
            "arterial", "vascular", "penetrating", "gunshot"
        ]
        injury_text = str(injury).lower()
        return any(keyword in injury_text for keyword in hemorrhage_keywords)

    def apply_environmental_factors(
        self,
        base_rate: float,
        conditions: List[str]
    ) -> float:
        """
        Apply environmental modifiers to deterioration rate.

        Args:
            base_rate: Base deterioration rate
            conditions: List of environmental conditions

        Returns:
            Modified deterioration rate
        """
        modified_rate = base_rate

        for condition in conditions:
            if condition in self.environmental_modifiers:
                modifier = self.environmental_modifiers[condition]
                multiplier = modifier.get("deterioration_multiplier", 1.0)
                modified_rate *= multiplier

        return modified_rate

    def calculate_compound_deterioration(
        self,
        injuries: List[Dict[str, str]]
    ) -> float:
        """
        Calculate deterioration for multiple injuries.

        Args:
            injuries: List of injuries with type and severity

        Returns:
            Combined deterioration rate
        """
        if not injuries:
            return 0.0

        # Find the most severe injury as primary driver
        primary_rate = 0.0
        secondary_sum = 0.0

        for injury in injuries:
            injury_type = injury.get("type", "Battle Injury")
            severity = injury.get("severity", "Moderate")
            rate = self.calculate_base_deterioration(injury_type, severity)

            if rate > primary_rate:
                # New primary, old primary becomes secondary
                if primary_rate > 0:
                    secondary_sum += primary_rate * 0.3
                primary_rate = rate
            else:
                # Add as secondary with reduced impact
                secondary_sum += rate * 0.3

        # Combined rate: primary + diminished secondaries
        return min(100.0, primary_rate + secondary_sum)

    def get_stabilization_window(
        self,
        injury_type: str,
        severity: str
    ) -> Dict[str, float]:
        """
        Get time windows for stabilization opportunities.

        Returns:
            Dict with golden_hour, platinum_10, and maximum_survivable times
        """
        base_times = {
            "Severe": {
                "platinum_10_minutes": 10,
                "golden_hour": 60,
                "maximum_survivable": 180
            },
            "Moderate to severe": {
                "platinum_10_minutes": 15,
                "golden_hour": 90,
                "maximum_survivable": 360
            },
            "Moderate": {
                "platinum_10_minutes": 30,
                "golden_hour": 180,
                "maximum_survivable": 720
            },
            "Mild to moderate": {
                "platinum_10_minutes": 60,
                "golden_hour": 360,
                "maximum_survivable": 1440
            }
        }

        # Adjust for injury type
        multipliers = {
            "Battle Injury": 1.0,
            "Non-Battle Injury": 1.5,
            "Disease": 3.0
        }

        windows = base_times.get(severity, base_times["Moderate"])
        multiplier = multipliers.get(injury_type, 1.0)

        return {
            key: value * multiplier
            for key, value in windows.items()
        }

    def calculate_intervention_points(
        self,
        deterioration_rate: float,
        initial_health: int
    ) -> List[Dict[str, float]]:
        """
        Calculate critical intervention points in patient timeline.

        Returns:
            List of intervention points with time and required action
        """
        points = []
        current_health = initial_health

        # Calculate time to various thresholds
        thresholds = [
            (70, "preventive_care", "Preventive interventions recommended"),
            (50, "urgent_treatment", "Urgent treatment required"),
            (30, "critical_intervention", "Critical intervention needed"),
            (10, "life_saving", "Immediate life-saving measures required"),
            (0, "death", "Patient death without intervention")
        ]

        for threshold, category, description in thresholds:
            if current_health <= threshold:
                continue  # Already below this threshold

            health_drop = current_health - threshold
            time_hours = health_drop / deterioration_rate if deterioration_rate > 0 else float('inf')

            points.append({
                "health_threshold": threshold,
                "time_hours": round(time_hours, 2),
                "category": category,
                "description": description
            })

        return points


if __name__ == "__main__":
    # Test the calculator
    calc = DeteriorationCalculator()

    # Test single injury
    rate = calc.calculate_base_deterioration("Battle Injury", "Severe")
    print(f"Severe battle injury deterioration: {rate} health/hour")

    # Test with hemorrhage
    injuries = [{"condition": "Gunshot wound with arterial bleeding"}]
    rate_hemorrhage = calc.calculate_base_deterioration(
        "Battle Injury", "Severe", injuries
    )
    print(f"With hemorrhage: {rate_hemorrhage} health/hour")

    # Test environmental factors
    conditions = ["extreme_cold", "high_altitude"]
    modified = calc.apply_environmental_factors(rate, conditions)
    print(f"In harsh environment: {modified} health/hour")

    # Test compound injuries
    multiple = [
        {"type": "Battle Injury", "severity": "Severe"},
        {"type": "Battle Injury", "severity": "Moderate"}
    ]
    compound = calc.calculate_compound_deterioration(multiple)
    print(f"Multiple injuries: {compound} health/hour")

    # Get intervention points
    points = calc.calculate_intervention_points(
        deterioration_rate=30,
        initial_health=60
    )
    print("\nIntervention timeline:")
    for point in points:
        print(f"  {point['time_hours']:.1f}h: {point['description']}")