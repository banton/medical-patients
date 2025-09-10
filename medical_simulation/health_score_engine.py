"""
Health Score Engine for Medical Simulation
Manages patient health scores (0-100) and calculates health timelines
"""

import json
import random
from typing import Any, Dict, List, Optional, Tuple


class HealthScoreEngine:
    """
    Calculates and tracks patient health scores over time.
    Works with Deterioration Calculator to build complete health timelines.
    """

    def __init__(self, injuries_config_path: str = "patient_generator/injuries.json"):
        """Initialize with injuries configuration"""
        self.config = self._load_config(injuries_config_path)
        self.deterioration_model = self.config.get("deterioration_model", {})

    def _load_config(self, path: str) -> Dict:
        """Load injuries.json configuration"""
        with open(path) as f:
            return json.load(f)

    def get_initial_health(self, injury_type: str, severity: str, condition: Optional[str] = None) -> int:
        """
        Get initial health score for injury type and severity.

        Args:
            injury_type: "Battle Injury", "Non-Battle Injury", or "Disease"
            severity: "Severe", "Moderate to severe", "Moderate", "Mild to moderate"
            condition: Optional specific condition like "Traumatic amputation"

        Returns:
            Initial health score (0-100)
        """
        # Map injury types from uppercase/underscore format to expected format
        injury_type_map = {
            "BATTLE_TRAUMA": "Battle Injury",
            "DISEASE": "Disease",
            "NON_BATTLE_INJURY": "Non-Battle Injury",
            "Battle Injury": "Battle Injury",
            "Disease": "Disease",
            "Non-Battle Injury": "Non-Battle Injury",
        }

        # Map numeric severity to text descriptions
        severity_map = {
            # Numeric severity (1-10 scale)
            1: "Mild to moderate",
            2: "Mild to moderate",
            3: "Mild to moderate",
            4: "Moderate",
            5: "Moderate",
            6: "Moderate",
            7: "Moderate to severe",
            8: "Moderate to severe",
            9: "Severe",
            10: "Severe",
            # Text severity (keep as-is)
            "Severe": "Severe",
            "Moderate to severe": "Moderate to severe",
            "Moderate": "Moderate",
            "Mild to moderate": "Mild to moderate",
        }

        # Convert inputs to expected format
        mapped_injury = injury_type_map.get(injury_type, injury_type)
        mapped_severity = (
            severity_map.get(severity, severity)
            if isinstance(severity, int)
            else severity_map.get(severity, "Moderate")
        )

        if mapped_injury not in self.deterioration_model:
            # More varied defaults based on triage/severity
            if isinstance(severity, int):
                if severity >= 9:
                    return random.randint(30, 50)  # Critical (was 15-30)
                if severity >= 7:
                    return random.randint(50, 65)  # Severe (was 35-50)
                if severity >= 4:
                    return random.randint(70, 85)  # Moderate (was 55-70)
                return random.randint(85, 95)  # Mild (was 75-90)
            return 70

        severity_data = self.deterioration_model[mapped_injury].get(mapped_severity, {})

        # Check for specific conditions first
        if condition and "specific_conditions" in severity_data:
            specific = severity_data["specific_conditions"].get(condition, {})
            if "initial_health" in specific:
                return specific["initial_health"]

        # Use base initial health
        base_health = severity_data.get("initial_health", 70)

        # Add variance for realism
        variance = severity_data.get("variance", 2)
        health = base_health + random.randint(-variance, variance)

        # Ensure bounds
        return max(0, min(100, health))

    def calculate_health_timeline(
        self,
        injury_type: str,
        severity: str,
        duration_hours: int,
        deterioration_rate: float,
        modifiers: Optional[List[Dict]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Calculate complete health timeline from injury to outcome.

        Args:
            injury_type: Type of injury
            severity: Severity level
            duration_hours: How many hours to simulate
            deterioration_rate: Base deterioration per hour
            modifiers: List of time-based modifiers (treatments, environment, etc.)
                      Format: [{"hour": 2, "type": "treatment", "modifier": 0.5}, ...]

        Returns:
            Timeline of health scores: [{"hour": 0, "health": 60, "status": "stable"}, ...]
        """
        timeline = []
        current_health = self.get_initial_health(injury_type, severity)

        # Sort modifiers by hour if provided
        active_modifiers = []
        if modifiers:
            modifiers = sorted(modifiers, key=lambda x: x.get("hour", 0))

        for hour in range(duration_hours + 1):
            # Apply any new modifiers at this hour
            if modifiers:
                for mod in modifiers:
                    if mod.get("hour") == hour:
                        active_modifiers.append(mod)

            # Calculate effective deterioration rate
            effective_rate = deterioration_rate
            for mod in active_modifiers:
                if mod.get("type") == "treatment" or mod.get("type") == "environment":
                    effective_rate *= mod.get("modifier", 1.0)

            # Apply golden hour effect (from config)
            golden_hour = self.config.get("golden_hour_effect", {})
            if hour > golden_hour.get("hours_before_golden_hour", 1):
                multiplier = golden_hour.get("multiplier_after_golden_hour", 1.5)
                max_hours = golden_hour.get("max_multiplier_at_hours", 6)
                max_mult = golden_hour.get("max_multiplier_value", 2.5)

                # Scale multiplier based on hours passed
                if hour < max_hours:
                    scale = (hour - 1) / (max_hours - 1)
                    multiplier = 1.0 + (multiplier - 1.0) + scale * (max_mult - multiplier)
                else:
                    multiplier = max_mult

                effective_rate *= multiplier

            # Check for cliff events (sudden deterioration)
            cliff_config = self.config.get("cliff_events", {})
            if (
                cliff_config.get("enabled", False)
                and hour > 0
                and random.random() < cliff_config.get("probability_per_hour", 0.05)
            ):
                health_range = cliff_config.get("applies_to_health_range", [20, 60])
                if health_range[0] <= current_health <= health_range[1]:
                    drop_range = cliff_config.get("health_drop_range", [15, 30])
                    cliff_drop = random.randint(drop_range[0], drop_range[1])
                    current_health -= cliff_drop
                    timeline.append(
                        {
                            "hour": hour,
                            "health": max(0, current_health),
                            "status": "cliff_event",
                            "event": f"Sudden deterioration: -{cliff_drop} health",
                        }
                    )
                    continue

            # Regular deterioration
            if hour > 0:
                current_health -= effective_rate

            # Determine status
            status = self._determine_status(current_health)

            # Add to timeline
            timeline.append(
                {
                    "hour": hour,
                    "health": max(0, min(100, current_health)),
                    "status": status,
                    "deterioration_rate": effective_rate if hour > 0 else 0,
                }
            )

            # Stop if patient dies
            if current_health <= 0:
                break

        return timeline

    def _determine_status(self, health: int) -> str:
        """Determine patient status based on health score"""
        if health <= 0:
            return "dead"
        if health < 10:
            return "critical"
        if health < 40:
            return "unstable"
        if health < 70:
            return "stable"
        return "good"

    def apply_treatment_effect(
        self, current_health: int, treatment: str, treatment_config: Optional[Dict] = None
    ) -> Tuple[int, float]:
        """
        Apply immediate treatment effect to health score.

        Args:
            current_health: Current health score
            treatment: Treatment type (tourniquet, iv_fluids, etc.)
            treatment_config: Optional treatment configuration

        Returns:
            Tuple of (new_health, deterioration_modifier)
        """
        if not treatment_config:
            # Default effects if no config provided
            default_effects = {
                "tourniquet": (5, 0.2),  # +5 health, 0.2x deterioration
                "iv_fluids": (10, 0.7),  # +10 health, 0.7x deterioration
                "morphine": (0, 0.9),  # No health boost, 0.9x deterioration
                "surgery": (20, 0.1),  # +20 health, 0.1x deterioration
            }
            health_boost, modifier = default_effects.get(treatment, (0, 1.0))
        else:
            health_boost = treatment_config.get("health_boost", 0)
            modifier = treatment_config.get("deterioration_modifier", 1.0)

        new_health = min(100, current_health + health_boost)
        return new_health, modifier

    def predict_outcome(self, timeline: List[Dict]) -> Dict[str, Any]:
        """
        Predict patient outcome based on health timeline.

        Returns:
            Dictionary with outcome type, time, and final health
        """
        if not timeline:
            return {"outcome": "unknown", "time_hours": 0, "final_health": 0}

        final_entry = timeline[-1]
        final_health = final_entry["health"]
        time_hours = final_entry["hour"]

        if final_health <= 0:
            return {
                "outcome": "death",
                "time_hours": time_hours,
                "final_health": 0,
                "category": "DOW",  # Died of Wounds
            }
        if final_health < 40:
            return {
                "outcome": "critical_survival",
                "time_hours": time_hours,
                "final_health": final_health,
                "needs_evacuation": True,
            }
        return {
            "outcome": "stable_survival",
            "time_hours": time_hours,
            "final_health": final_health,
            "rtd_eligible": final_health > 70,
        }


if __name__ == "__main__":
    # Test the engine
    engine = HealthScoreEngine()

    # Test severe battle injury
    initial = engine.get_initial_health("Battle Injury", "Severe")
    print(f"Initial health for severe battle injury: {initial}")

    # Calculate timeline with treatment
    modifiers = [
        {"hour": 1, "type": "treatment", "modifier": 0.5},  # Tourniquet at hour 1
        {"hour": 3, "type": "treatment", "modifier": 0.7},  # IV fluids at hour 3
    ]

    timeline = engine.calculate_health_timeline(
        injury_type="Battle Injury", severity="Severe", duration_hours=8, deterioration_rate=30, modifiers=modifiers
    )

    print("\nHealth timeline:")
    for entry in timeline:
        print(f"Hour {entry['hour']}: Health={entry['health']}, Status={entry['status']}")

    outcome = engine.predict_outcome(timeline)
    print(f"\nPredicted outcome: {outcome}")
