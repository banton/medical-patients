"""
Integration layer for hemorrhage modeling with existing medical system.
Example usage and helper functions.
"""

from datetime import datetime
import json
from typing import Any, Dict, List, Optional

from .body_regions import BodyRegion
from .hemorrhage_model import HemorrhageCategory, HemorrhageModel, HemorrhageProfile


class HemorrhageIntegration:
    """Helper class to integrate hemorrhage modeling with patient generator."""

    def __init__(self):
        self.hemorrhage_model = HemorrhageModel()

    def enhance_patient_with_hemorrhage(self, patient: Any) -> Dict:
        """
        Add hemorrhage profile to an existing patient based on their conditions.
        
        Args:
            patient: Patient object with primary_conditions
            
        Returns:
            Dictionary with hemorrhage data
        """
        hemorrhage_data = {
            "has_hemorrhage": False,
            "profiles": [],
            "total_blood_loss_rate": 0.0,
            "time_to_critical": float("inf"),
            "requires_tourniquet": False,
            "requires_surgery": False
        }

        # Check if patient has conditions that could cause hemorrhage
        if not hasattr(patient, "primary_conditions") or not patient.primary_conditions:
            return hemorrhage_data

        # Generate hemorrhage profiles for each condition
        profiles = []
        for condition in patient.primary_conditions:
            profile = self.hemorrhage_model.calculate_hemorrhage_profile(
                injury_code=condition.get("code", "125670008"),
                severity=condition.get("severity", "Moderate"),
                multiple_injuries=len(patient.primary_conditions) > 1
            )

            if profile.category != HemorrhageCategory.NO_HEMORRHAGE:
                profiles.append(profile)

        if profiles:
            hemorrhage_data["has_hemorrhage"] = True
            hemorrhage_data["profiles"] = [self._profile_to_dict(p) for p in profiles]

            # Calculate combined effects
            total_blood_loss = sum(p.blood_loss_ml_per_min for p in profiles)
            hemorrhage_data["total_blood_loss_rate"] = total_blood_loss

            # Time to critical (40% blood loss = 2000ml)
            if total_blood_loss > 0:
                hemorrhage_data["time_to_critical"] = 2000 / total_blood_loss

            # Treatment requirements
            hemorrhage_data["requires_tourniquet"] = any(p.controllable for p in profiles)
            hemorrhage_data["requires_surgery"] = any(
                p.category in [HemorrhageCategory.MASSIVE_HEMORRHAGE,
                              HemorrhageCategory.TORSO_WOUND]
                for p in profiles
            )

        return hemorrhage_data

    def calculate_blood_volume_timeline(
        self,
        hemorrhage_profile: HemorrhageProfile,
        duration_minutes: int = 60,
        tourniquet_time: Optional[int] = None
    ) -> List[Dict]:
        """
        Calculate blood volume over time for a hemorrhage profile.
        
        Args:
            hemorrhage_profile: The hemorrhage profile
            duration_minutes: How long to simulate
            tourniquet_time: When tourniquet is applied (minutes from injury)
            
        Returns:
            Timeline of blood volume changes
        """
        timeline = []
        initial_blood_volume = 5000  # ml
        current_volume = initial_blood_volume

        for minute in range(duration_minutes):
            # Check if tourniquet applied
            if tourniquet_time and minute >= tourniquet_time and hemorrhage_profile.controllable:
                # Reduce bleeding by 95% with tourniquet
                blood_loss_rate = hemorrhage_profile.blood_loss_ml_per_min * 0.05
            else:
                # Apply lethal triad progression
                progression_factor = 1 + (hemorrhage_profile.k * minute / 60)
                blood_loss_rate = hemorrhage_profile.blood_loss_ml_per_min * progression_factor

            # Calculate volume loss
            current_volume -= blood_loss_rate
            current_volume = max(0, current_volume)

            # Record state
            timeline.append({
                "minute": minute,
                "blood_volume_ml": current_volume,
                "blood_volume_percent": (current_volume / initial_blood_volume) * 100,
                "blood_loss_rate": blood_loss_rate,
                "status": self._get_hemorrhage_status(current_volume / initial_blood_volume)
            })

            # Stop if exsanguinated
            if current_volume <= 0:
                break

        return timeline

    def get_treatment_priority(self, hemorrhage_data: Dict) -> str:
        """
        Determine treatment priority based on hemorrhage severity.
        
        Args:
            hemorrhage_data: Hemorrhage data dictionary
            
        Returns:
            Priority level: "T1", "T2", or "T3"
        """
        if not hemorrhage_data.get("has_hemorrhage"):
            return "T3"

        time_to_critical = hemorrhage_data.get("time_to_critical", float("inf"))

        if time_to_critical < 10:  # Less than 10 minutes
            return "T1"
        if time_to_critical < 30:  # Less than 30 minutes
            return "T2"
        return "T3"

    @staticmethod
    def _profile_to_dict(profile: HemorrhageProfile) -> Dict:
        """Convert HemorrhageProfile to dictionary."""
        return {
            "category": profile.category.value,
            "alpha_0": profile.alpha_0,
            "k": profile.k,
            "body_region": profile.body_location.region.value,
            "specific_area": profile.body_location.specific_area,
            "vessel_type": profile.vessel_type.value,
            "tourniquetable": profile.controllable,
            "blood_loss_ml_per_min": profile.blood_loss_ml_per_min,
            "time_to_exsanguination_min": profile.time_to_exsanguination_min
        }

    @staticmethod
    def _get_hemorrhage_status(blood_volume_percent: float) -> str:
        """Get clinical status based on blood volume percentage."""
        if blood_volume_percent >= 85:
            return "stable"
        if blood_volume_percent >= 70:
            return "compensated_shock"
        if blood_volume_percent >= 50:
            return "decompensated_shock"
        if blood_volume_percent >= 40:
            return "critical"
        return "exsanguinated"

    def generate_hemorrhage_report(self, patient: Any) -> str:
        """
        Generate a clinical report of hemorrhage status.
        
        Args:
            patient: Patient object
            
        Returns:
            Text report
        """
        hemorrhage_data = self.enhance_patient_with_hemorrhage(patient)

        if not hemorrhage_data["has_hemorrhage"]:
            return "No significant hemorrhage identified."

        report = []
        report.append(f"HEMORRHAGE ASSESSMENT - Patient ID: {patient.id}")
        report.append(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        report.append("-" * 50)

        for i, profile in enumerate(hemorrhage_data["profiles"], 1):
            report.append(f"\nHemorrhage Site {i}:")
            report.append(f"  Location: {profile['body_region']} - {profile['specific_area']}")
            report.append(f"  Category: {profile['category']}")
            report.append(f"  Vessel Type: {profile['vessel_type']}")
            report.append(f"  Blood Loss Rate: {profile['blood_loss_ml_per_min']:.1f} ml/min")
            report.append(f"  Tourniquetable: {'Yes' if profile['tourniquetable'] else 'No'}")
            report.append(f"  Time to Exsanguination: {profile['time_to_exsanguination_min']:.1f} min")

        report.append("\nSUMMARY:")
        report.append(f"  Total Blood Loss Rate: {hemorrhage_data['total_blood_loss_rate']:.1f} ml/min")
        report.append(f"  Time to Critical (40% loss): {hemorrhage_data['time_to_critical']:.1f} min")
        report.append(f"  Requires Tourniquet: {'Yes' if hemorrhage_data['requires_tourniquet'] else 'No'}")
        report.append(f"  Requires Surgery: {'Yes' if hemorrhage_data['requires_surgery'] else 'No'}")
        report.append(f"  Recommended Triage: {self.get_treatment_priority(hemorrhage_data)}")

        return "\n".join(report)


# Example usage function
def example_usage():
    """Demonstrate how to use the hemorrhage model with a patient."""

    # Create a mock patient class for demonstration
    class MockPatient:
        def __init__(self):
            self.id = 12345
            self.primary_conditions = [
                {
                    "code": "262574004",  # Bullet wound
                    "display": "Bullet wound",
                    "severity": "Severe"
                },
                {
                    "code": "125689001",  # Shrapnel injury
                    "display": "Shrapnel injury",
                    "severity": "Moderate"
                }
            ]

    # Create patient and hemorrhage integration
    patient = MockPatient()
    hemorrhage_int = HemorrhageIntegration()

    # Get hemorrhage data
    hemorrhage_data = hemorrhage_int.enhance_patient_with_hemorrhage(patient)

    print("Hemorrhage Data:")
    print(json.dumps(hemorrhage_data, indent=2, default=str))

    # Generate clinical report
    report = hemorrhage_int.generate_hemorrhage_report(patient)
    print("\n" + report)

    # Calculate blood volume timeline for first hemorrhage
    if hemorrhage_data["profiles"]:
        first_profile = HemorrhageModel.calculate_hemorrhage_profile(
            injury_code="262574004",
            body_region=BodyRegion.CHEST,
            severity="Severe"
        )

        timeline = hemorrhage_int.calculate_blood_volume_timeline(
            first_profile,
            duration_minutes=30,
            tourniquet_time=5  # Applied at 5 minutes
        )

        print("\nBlood Volume Timeline (first 30 minutes):")
        for i, point in enumerate(timeline[::5]):  # Every 5 minutes
            print(f"  {point['minute']:2d} min: {point['blood_volume_percent']:.1f}% "
                  f"({point['status']}) - Loss rate: {point['blood_loss_rate']:.1f} ml/min")


if __name__ == "__main__":
    example_usage()
