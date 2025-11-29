"""
Disability Tracker for Medical Simulation
Tracks permanent injuries and determines RTD eligibility based on realistic military medical standards
"""

from enum import Enum
from typing import Dict, List, Optional, Tuple


class DisabilityType(Enum):
    """Types of permanent disabilities that affect RTD eligibility"""

    NONE = "none"
    AMPUTATION = "amputation"
    PARALYSIS = "paralysis"
    TBI_SEVERE = "traumatic_brain_injury_severe"
    VISION_LOSS = "vision_loss"
    HEARING_LOSS = "hearing_loss"
    BURNS_SEVERE = "burns_severe"
    ORGAN_LOSS = "organ_loss"
    PSYCHOLOGICAL = "psychological_severe"
    MULTIPLE = "multiple_disabilities"


class DisabilityTracker:
    """
    Tracks permanent disabilities from combat injuries and determines RTD eligibility.
    Based on military medical discharge criteria.
    """

    def __init__(self):
        """Initialize disability definitions and RTD criteria"""
        self.injury_disability_map = self._define_injury_disabilities()
        self.rtd_criteria = self._define_rtd_criteria()

    def _define_injury_disabilities(self) -> Dict[str, Dict]:
        """
        Map SNOMED codes to permanent disability outcomes.
        These are realistic assessments based on military medical standards.
        """
        return {
            # Battle Injuries
            "284551006": {  # Traumatic amputation of limb
                "disability_type": DisabilityType.AMPUTATION,
                "rtd_possible": False,
                "disability_chance": 1.0,  # Always permanent
                "max_recovery_health": 60,  # Can never fully recover
                "evacuation_priority": "urgent",
                "requires_prosthetic": True,
            },
            "19130008": {  # Traumatic brain injury
                "disability_type": DisabilityType.TBI_SEVERE,
                "rtd_possible": False,  # Severe TBI = no RTD
                "disability_chance": 0.7,  # 70% result in permanent disability
                "max_recovery_health": 50,
                "evacuation_priority": "immediate",
                "cognitive_impact": True,
            },
            "125596004": {  # Injury by explosive (IED/blast)
                "disability_type": DisabilityType.MULTIPLE,
                "rtd_possible": False,  # Usually multiple trauma
                "disability_chance": 0.6,
                "max_recovery_health": 55,
                "evacuation_priority": "immediate",
                "polytrauma": True,
            },
            "7200002": {  # Burn of skin
                "disability_type": DisabilityType.BURNS_SEVERE,
                "rtd_possible": False,  # Severe burns (>30% TBSA)
                "disability_chance": 0.5,  # Depends on extent
                "max_recovery_health": 65,
                "evacuation_priority": "urgent",
                "requires_skin_graft": True,
            },
            "361220002": {  # Penetrating injury
                "disability_type": DisabilityType.ORGAN_LOSS,
                "rtd_possible": False,  # If organs damaged
                "disability_chance": 0.4,  # Depends on location
                "max_recovery_health": 70,
                "evacuation_priority": "immediate",
            },
            # Non-Battle Injuries (less likely to cause permanent disability)
            "37782003": {  # Fracture of bone
                "disability_type": DisabilityType.NONE,
                "rtd_possible": True,  # Usually can RTD after healing
                "disability_chance": 0.1,  # Only if complications
                "max_recovery_health": 85,
                "evacuation_priority": "routine",
                "recovery_weeks": 8,
            },
            "409711008": {  # Vehicle accident injury
                "disability_type": DisabilityType.MULTIPLE,
                "rtd_possible": False,  # Often severe
                "disability_chance": 0.5,
                "max_recovery_health": 60,
                "evacuation_priority": "urgent",
            },
            "275272006": {  # Crush injury
                "disability_type": DisabilityType.AMPUTATION,
                "rtd_possible": False,
                "disability_chance": 0.6,  # Often requires amputation
                "max_recovery_health": 55,
                "evacuation_priority": "immediate",
                "compartment_syndrome_risk": True,
            },
            # Psychological conditions
            "45170000": {  # Psychological stress
                "disability_type": DisabilityType.PSYCHOLOGICAL,
                "rtd_possible": True,  # Possible with treatment
                "disability_chance": 0.2,  # If becomes chronic PTSD
                "max_recovery_health": 75,
                "evacuation_priority": "routine",
                "requires_psychiatric_care": True,
            },
        }

    def _define_rtd_criteria(self) -> Dict:
        """
        Define military standards for Return to Duty eligibility.
        Based on actual military medical fitness standards.
        """
        return {
            "minimum_health": 70,  # Need 70% functional capacity
            "minimum_recovery_days": 30,  # Minimum recovery period
            "disqualifying_disabilities": [
                DisabilityType.AMPUTATION,
                DisabilityType.PARALYSIS,
                DisabilityType.TBI_SEVERE,
                DisabilityType.VISION_LOSS,
                DisabilityType.ORGAN_LOSS,
                DisabilityType.MULTIPLE,
            ],
            "conditional_rtd": {
                DisabilityType.HEARING_LOSS: "non_combat_role",
                DisabilityType.PSYCHOLOGICAL: "after_treatment",
                DisabilityType.BURNS_SEVERE: "if_less_than_20_percent",
            },
        }

    def assess_permanent_disability(
        self, injury_code: str, severity: str, treatments_applied: List[str]
    ) -> Tuple[bool, Optional[DisabilityType], Dict]:
        """
        Assess if an injury results in permanent disability.

        Args:
            injury_code: SNOMED code of injury
            severity: Injury severity level
            treatments_applied: List of treatments received

        Returns:
            Tuple of (has_disability, disability_type, disability_info)
        """
        if injury_code not in self.injury_disability_map:
            # Unknown injury - assume no permanent disability
            return False, None, {"rtd_possible": True}

        injury_data = self.injury_disability_map[injury_code]

        # Check if disability occurs (probabilistic)
        import random

        disability_occurs = random.random() < injury_data["disability_chance"]

        # Severity modifier
        if severity == "Severe":
            disability_occurs = disability_occurs or (random.random() < 0.3)  # Extra 30% chance

        # Treatment can sometimes prevent disability
        if "tourniquet" in treatments_applied and injury_code == "284551006":
            # Tourniquet on amputation doesn't prevent disability
            disability_occurs = True
        elif "major_surgery" in treatments_applied:
            # Surgery might prevent some disabilities
            disability_occurs = disability_occurs and (random.random() < 0.8)  # 20% reduction

        if disability_occurs:
            return True, injury_data["disability_type"], injury_data
        return False, None, {"rtd_possible": True, "max_recovery_health": 90}

    def can_return_to_duty(
        self,
        patient_disabilities: List[DisabilityType],
        current_health: int,
        days_since_injury: int,
        psychological_status: str = "stable",
    ) -> Tuple[bool, str]:
        """
        Determine if a patient can return to duty based on military standards.

        Args:
            patient_disabilities: List of permanent disabilities
            current_health: Current health level (0-100)
            days_since_injury: Days since initial injury
            psychological_status: Mental health status

        Returns:
            Tuple of (can_rtd, reason)
        """
        criteria = self.rtd_criteria

        # Check for disqualifying disabilities
        for disability in patient_disabilities:
            if disability in criteria["disqualifying_disabilities"]:
                return False, f"Permanent disability: {disability.value}"

        # Check health threshold
        if current_health < criteria["minimum_health"]:
            return False, f"Insufficient recovery: {current_health}% (need {criteria['minimum_health']}%)"

        # Check recovery time
        if days_since_injury < criteria["minimum_recovery_days"]:
            return (
                False,
                f"Insufficient recovery time: {days_since_injury} days (need {criteria['minimum_recovery_days']})",
            )

        # Check psychological fitness
        if psychological_status in ["severe_ptsd", "psychosis", "severe_depression"]:
            return False, f"Psychological unfitness: {psychological_status}"

        # Check conditional RTD
        for disability in patient_disabilities:
            if disability in criteria["conditional_rtd"]:
                condition = criteria["conditional_rtd"][disability]
                if condition == "non_combat_role":
                    return True, f"RTD to non-combat role only ({disability.value})"
                if condition == "after_treatment" and psychological_status == "treated":
                    return True, "RTD after successful treatment"

        # All criteria met
        if patient_disabilities:
            return True, "RTD with minor limitations"
        return True, "Full RTD - combat ready"

    def get_evacuation_priority(self, injury_code: str) -> str:
        """
        Get medical evacuation priority for an injury.

        Returns:
            Priority level: immediate, urgent, priority, routine
        """
        if injury_code in self.injury_disability_map:
            return self.injury_disability_map[injury_code].get("evacuation_priority", "routine")
        return "routine"

    def get_max_recovery_potential(self, injury_codes: List[str], disabilities: List[DisabilityType]) -> int:
        """
        Calculate maximum possible recovery health based on injuries.

        Args:
            injury_codes: List of SNOMED injury codes
            disabilities: List of permanent disabilities

        Returns:
            Maximum health patient can achieve (0-100)
        """
        if not injury_codes and not disabilities:
            return 100

        # Start with 100% potential
        max_health = 100

        # Reduce based on specific injuries
        for code in injury_codes:
            if code in self.injury_disability_map:
                injury_max = self.injury_disability_map[code].get("max_recovery_health", 100)
                max_health = min(max_health, injury_max)

        # Further reduce based on disabilities
        disability_limits = {
            DisabilityType.AMPUTATION: 60,
            DisabilityType.PARALYSIS: 40,
            DisabilityType.TBI_SEVERE: 50,
            DisabilityType.VISION_LOSS: 65,
            DisabilityType.HEARING_LOSS: 80,
            DisabilityType.BURNS_SEVERE: 65,
            DisabilityType.ORGAN_LOSS: 55,
            DisabilityType.PSYCHOLOGICAL: 75,
            DisabilityType.MULTIPLE: 45,
        }

        for disability in disabilities:
            if disability in disability_limits:
                max_health = min(max_health, disability_limits[disability])

        return max_health


if __name__ == "__main__":
    # Test the disability tracker
    tracker = DisabilityTracker()

    # Test amputation case
    print("Testing amputation injury:")
    has_disability, disability_type, info = tracker.assess_permanent_disability(
        "284551006",  # Traumatic amputation
        "Severe",
        ["tourniquet", "surgical_stabilization"],
    )
    print(f"  Has disability: {has_disability}")
    print(f"  Type: {disability_type}")
    print(f"  RTD possible: {info.get('rtd_possible')}")

    # Test RTD assessment
    print("\nTesting RTD eligibility:")
    can_rtd, reason = tracker.can_return_to_duty(
        [DisabilityType.AMPUTATION], current_health=75, days_since_injury=45, psychological_status="stable"
    )
    print(f"  Can RTD: {can_rtd}")
    print(f"  Reason: {reason}")

    # Test fracture case (usually recoverable)
    print("\nTesting fracture injury:")
    has_disability, disability_type, info = tracker.assess_permanent_disability(
        "37782003",  # Fracture
        "Moderate",
        ["surgical_stabilization"],
    )
    print(f"  Has disability: {has_disability}")
    print(f"  RTD possible: {info.get('rtd_possible')}")

    # Test max recovery
    print("\nTesting max recovery potential:")
    max_health = tracker.get_max_recovery_potential(
        ["284551006", "19130008"],  # Amputation + TBI
        [DisabilityType.AMPUTATION, DisabilityType.TBI_SEVERE],
    )
    print(f"  Maximum recovery: {max_health}%")
