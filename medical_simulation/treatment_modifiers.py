"""
Treatment Modifiers for Medical Simulation
Models the effects of medical interventions on patient health
"""

from typing import Dict, List, Optional, Tuple


class TreatmentModifiers:
    """
    Calculates how treatments affect patient deterioration and health.
    Provides realistic medical intervention modeling.
    """

    def __init__(self):
        """Initialize treatment definitions"""
        self.treatments = self._define_treatments()
        self.facility_capabilities = self._define_facility_capabilities()

    def _define_treatments(self) -> Dict[str, Dict]:
        """Define available treatments and their effects"""
        return {
            # Immediate interventions (Role 1 / POI)
            "tourniquet": {
                "health_boost": 15,
                "deterioration_modifier": 0.3,  # Reduces bleeding by 80%
                "duration_hours": 2,  # Needs replacement/adjustment
                "facility_required": "any",
                "time_to_apply_minutes": 1,
            },
            "pressure_dressing": {
                "health_boost": 10,
                "deterioration_modifier": 0.4,
                "duration_hours": 4,
                "facility_required": "any",
                "time_to_apply_minutes": 2,
            },
            "hemostatic_agent": {
                "health_boost": 12,
                "deterioration_modifier": 0.35,
                "duration_hours": 6,
                "facility_required": "any",
                "time_to_apply_minutes": 3,
            },
            # Basic medical care (Role 1+)
            "iv_fluids": {
                "health_boost": 20,
                "deterioration_modifier": 0.6,
                "duration_hours": 8,
                "facility_required": "role1",
                "time_to_apply_minutes": 5,
            },
            "morphine": {
                "health_boost": 5,  # Pain relief, not healing
                "deterioration_modifier": 0.9,  # Slight benefit from reduced stress
                "duration_hours": 4,
                "facility_required": "role1",
                "time_to_apply_minutes": 2,
            },
            "antibiotics": {
                "health_boost": 8,
                "deterioration_modifier": 0.8,
                "duration_hours": 24,
                "facility_required": "role1",
                "time_to_apply_minutes": 5,
            },
            # Advanced interventions (Role 2+)
            "blood_transfusion": {
                "health_boost": 30,
                "deterioration_modifier": 0.4,
                "duration_hours": 12,
                "facility_required": "role2",
                "time_to_apply_minutes": 15,
            },
            "chest_tube": {
                "health_boost": 25,
                "deterioration_modifier": 0.3,
                "duration_hours": 48,
                "facility_required": "role2",
                "time_to_apply_minutes": 10,
            },
            "surgical_stabilization": {
                "health_boost": 35,
                "deterioration_modifier": 0.2,
                "duration_hours": 72,
                "facility_required": "role2",
                "time_to_apply_minutes": 45,
            },
            # Definitive care (Role 3)
            "major_surgery": {
                "health_boost": 45,
                "deterioration_modifier": 0.1,
                "duration_hours": 168,  # 1 week
                "facility_required": "role3",
                "time_to_apply_minutes": 120,
            },
            "organ_repair": {
                "health_boost": 40,
                "deterioration_modifier": 0.15,
                "duration_hours": 168,
                "facility_required": "role3",
                "time_to_apply_minutes": 180,
            },
        }

    def _define_facility_capabilities(self) -> Dict[str, List[str]]:
        """Define what treatments each facility level can provide"""
        return {
            "poi": ["tourniquet", "pressure_dressing", "hemostatic_agent"],
            "role1": ["tourniquet", "pressure_dressing", "hemostatic_agent", "iv_fluids", "morphine", "antibiotics"],
            "role2": [
                "tourniquet",
                "pressure_dressing",
                "hemostatic_agent",
                "iv_fluids",
                "morphine",
                "antibiotics",
                "blood_transfusion",
                "chest_tube",
                "surgical_stabilization",
            ],
            "role3": [
                "tourniquet",
                "pressure_dressing",
                "hemostatic_agent",
                "iv_fluids",
                "morphine",
                "antibiotics",
                "blood_transfusion",
                "chest_tube",
                "surgical_stabilization",
                "major_surgery",
                "organ_repair",
            ],
            "csu": ["tourniquet", "pressure_dressing", "iv_fluids", "morphine"],
        }

    def get_available_treatments(self, facility_type: str, patient_condition: Optional[str] = None) -> List[str]:
        """
        Get treatments available at a facility for a patient.

        Args:
            facility_type: Type of medical facility
            patient_condition: Optional specific condition to treat

        Returns:
            List of available treatment names
        """
        base_treatments = self.facility_capabilities.get(facility_type.lower(), [])

        # Filter by patient condition if specified
        if patient_condition:
            condition_lower = patient_condition.lower()

            # Extremity bleeding (tourniquets appropriate)
            if any(word in condition_lower for word in ["leg", "arm", "femoral", "extremity", "limb"]):
                return [
                    t
                    for t in base_treatments
                    if t in ["tourniquet", "pressure_dressing", "hemostatic_agent", "blood_transfusion", "iv_fluids"]
                ]

            # Chest/torso injuries (NO tourniquets!)
            if any(word in condition_lower for word in ["chest", "thorax", "pneumothorax", "lung", "respiratory"]):
                return [
                    t
                    for t in base_treatments
                    if t
                    in [
                        "chest_tube",
                        "pressure_dressing",
                        "surgical_stabilization",
                        "blood_transfusion",
                        "iv_fluids",
                        "morphine",
                    ]
                ]

            # Abdominal injuries (NO tourniquets!)
            if any(word in condition_lower for word in ["abdomen", "abdominal", "gut", "intestinal"]):
                return [
                    t
                    for t in base_treatments
                    if t
                    in [
                        "pressure_dressing",
                        "iv_fluids",
                        "blood_transfusion",
                        "surgical_stabilization",
                        "antibiotics",
                        "morphine",
                    ]
                ]

            # Head injuries (very limited field treatments)
            if any(word in condition_lower for word in ["head", "skull", "brain", "cranial"]):
                return [t for t in base_treatments if t in ["pressure_dressing", "iv_fluids", "morphine"]]

            # General hemorrhage (unspecified location)
            if "hemorrhage" in condition_lower or "bleeding" in condition_lower:
                # Be conservative - no tourniquet unless we know it's an extremity
                return [
                    t
                    for t in base_treatments
                    if t in ["pressure_dressing", "hemostatic_agent", "blood_transfusion", "iv_fluids"]
                ]

        return base_treatments

    def apply_treatment(
        self, treatment_name: str, current_health: int, current_deterioration: float
    ) -> Tuple[int, float, Dict]:
        """
        Apply a treatment and return modified health and deterioration.

        Args:
            treatment_name: Name of treatment to apply
            current_health: Current health score
            current_deterioration: Current deterioration rate

        Returns:
            Tuple of (new_health, new_deterioration, treatment_info)
        """
        if treatment_name not in self.treatments:
            return current_health, current_deterioration, {}

        treatment = self.treatments[treatment_name]

        # Apply health boost
        new_health = min(100, current_health + treatment["health_boost"])

        # Apply deterioration modifier
        new_deterioration = current_deterioration * treatment["deterioration_modifier"]

        # Return treatment info for tracking
        treatment_info = {
            "name": treatment_name,
            "applied_health_boost": treatment["health_boost"],
            "deterioration_modifier": treatment["deterioration_modifier"],
            "duration_hours": treatment["duration_hours"],
            "expires_at_hour": treatment["duration_hours"],  # Caller tracks current time
        }

        return new_health, new_deterioration, treatment_info

    def calculate_stacked_effects(self, active_treatments: List[Dict]) -> float:
        """
        Calculate combined effect of multiple active treatments.

        Args:
            active_treatments: List of currently active treatments

        Returns:
            Combined deterioration modifier (0-1 scale)
        """
        if not active_treatments:
            return 1.0

        # Start with full deterioration
        combined_modifier = 1.0

        # Apply each treatment's effect with diminishing returns
        for i, treatment in enumerate(active_treatments):
            treatment_data = self.treatments.get(treatment["name"], {})
            modifier = treatment_data.get("deterioration_modifier", 1.0)

            # Diminishing returns: each additional treatment is 80% as effective
            effectiveness = 0.8**i
            effective_modifier = 1.0 - (1.0 - modifier) * effectiveness

            combined_modifier *= effective_modifier

        return max(0.1, combined_modifier)  # Never reduce below 10%

    def get_treatment_priority(
        self, available_treatments: List[str], patient_health: int, deterioration_rate: float
    ) -> List[str]:
        """
        Prioritize treatments based on patient condition.

        Returns:
            Ordered list of treatments to apply
        """
        priorities = []

        # Critical interventions first
        if patient_health < 30 and deterioration_rate > 20:
            critical = ["tourniquet", "blood_transfusion", "surgical_stabilization"]
            priorities.extend([t for t in critical if t in available_treatments])

        # Stabilization next
        if patient_health < 50:
            stabilize = ["iv_fluids", "chest_tube", "hemostatic_agent"]
            priorities.extend([t for t in stabilize if t in available_treatments and t not in priorities])

        # Comfort and infection prevention
        comfort = ["morphine", "antibiotics", "pressure_dressing"]
        priorities.extend([t for t in comfort if t in available_treatments and t not in priorities])

        # Add any remaining available treatments
        priorities.extend([t for t in available_treatments if t not in priorities])

        return priorities


if __name__ == "__main__":
    # Test the treatment system
    tm = TreatmentModifiers()

    # Test available treatments at different facilities
    print("POI treatments:", tm.get_available_treatments("poi"))
    print("Role2 treatments:", tm.get_available_treatments("role2"))

    # Test applying treatment
    health, deterioration, info = tm.apply_treatment("tourniquet", current_health=30, current_deterioration=25)
    print(f"\nAfter tourniquet: Health={health}, Deterioration={deterioration:.1f}")
    print(f"Treatment info: {info}")

    # Test stacked treatments
    active = [{"name": "tourniquet"}, {"name": "iv_fluids"}, {"name": "morphine"}]
    combined = tm.calculate_stacked_effects(active)
    print(f"\nCombined effect of 3 treatments: {combined:.2f}x deterioration")

    # Test treatment prioritization
    available = ["morphine", "tourniquet", "iv_fluids", "antibiotics"]
    priority = tm.get_treatment_priority(available, patient_health=25, deterioration_rate=30)
    print(f"\nTreatment priority order: {priority}")
