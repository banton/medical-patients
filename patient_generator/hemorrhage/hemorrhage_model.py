"""
Hemorrhage model implementation based on SIMEDIS research.
Maps injury types and body locations to bleeding rates.
"""

from dataclasses import dataclass
from enum import Enum
import random
from typing import Dict, List, Optional

from .body_regions import BodyLocation, BodyRegion, VesselType, get_affected_vessel_type, get_body_location


class HemorrhageCategory(Enum):
    """Categories of hemorrhage based on severity and location."""

    SMALL_LIMB = "small_limb_wounds"
    MAJOR_LIMB_ARTERY = "major_limb_artery"
    TORSO_WOUND = "torso_wound"
    MULTIPLE_PENETRATING = "multiple_penetrating"
    MASSIVE_HEMORRHAGE = "massive_hemorrhage"
    NO_HEMORRHAGE = "no_hemorrhage"


@dataclass
class HemorrhageProfile:
    """Complete hemorrhage profile for a patient injury."""

    category: HemorrhageCategory
    alpha_0: float  # Initial bleeding rate (hr^-1)
    k: float  # Lethal triad progression factor
    body_location: BodyLocation
    vessel_type: VesselType
    controllable: bool  # Can be controlled with tourniquet
    blood_loss_ml_per_min: float  # Estimated ml/min blood loss
    time_to_exsanguination_min: float  # Without intervention


class HemorrhageModel:
    """Model for calculating hemorrhage parameters based on injury and location."""

    # Table 1 parameters from research
    HEMORRHAGE_PARAMETERS = {
        HemorrhageCategory.SMALL_LIMB: {
            "alpha_0_range": (0.1, 0.3),
            "k": 0.02,
            "blood_loss_ml_min": (10, 30),  # 10-30 ml/min
            "description": "Small limb wounds (shrapnel, soft tissue)",
        },
        HemorrhageCategory.MAJOR_LIMB_ARTERY: {
            "alpha_0_range": (2.0, 5.0),
            "k": 0.05,
            "blood_loss_ml_min": (200, 500),  # Femoral can lose 500ml/min
            "description": "Major limb artery (femoral, brachial)",
        },
        HemorrhageCategory.TORSO_WOUND: {
            "alpha_0_range": (0.5, 2.0),
            "k": 0.1,
            "blood_loss_ml_min": (50, 200),
            "description": "Torso wound (lung, liver, kidney)",
        },
        HemorrhageCategory.MULTIPLE_PENETRATING: {
            "alpha_0_range": (1.0, 3.0),
            "k": 0.15,
            "blood_loss_ml_min": (100, 300),
            "description": "Multiple penetrating wounds (moderate bleeding)",
        },
        HemorrhageCategory.MASSIVE_HEMORRHAGE: {
            "alpha_0_range": (10.0, 20.0),  # >10 as per research
            "k": 0.3,
            "blood_loss_ml_min": (1000, 2500),  # Can lose 2.5L in minutes
            "description": "Massive hemorrhage (aorta, iliac artery)",
        },
        HemorrhageCategory.NO_HEMORRHAGE: {
            "alpha_0_range": (0.0, 0.0),
            "k": 0.0,
            "blood_loss_ml_min": (0, 0),
            "description": "No significant hemorrhage",
        },
    }

    # Map SNOMED codes to hemorrhage risk and typical locations
    INJURY_HEMORRHAGE_MAP = {
        # Battle trauma conditions
        "262574004": {  # Bullet wound
            "hemorrhage_risk": "high",
            "typical_locations": [BodyRegion.CHEST, BodyRegion.ABDOMEN, BodyRegion.LEFT_LEG, BodyRegion.RIGHT_LEG],
            "vessel_damage": "deep",
        },
        "125689001": {  # Shrapnel injury
            "hemorrhage_risk": "moderate",
            "typical_locations": [BodyRegion.LEFT_ARM, BodyRegion.RIGHT_ARM, BodyRegion.LEFT_LEG, BodyRegion.RIGHT_LEG],
            "vessel_damage": "moderate",
        },
        "125596004": {  # Injury by explosive
            "hemorrhage_risk": "high",
            "typical_locations": [BodyRegion.CHEST, BodyRegion.ABDOMEN, BodyRegion.PELVIS],
            "vessel_damage": "deep",
        },
        "284551006": {  # Traumatic amputation
            "hemorrhage_risk": "critical",
            "typical_locations": [BodyRegion.LEFT_LEG, BodyRegion.RIGHT_LEG, BodyRegion.LEFT_ARM, BodyRegion.RIGHT_ARM],
            "vessel_damage": "deep",
        },
        "361220002": {  # Penetrating injury
            "hemorrhage_risk": "high",
            "typical_locations": [BodyRegion.CHEST, BodyRegion.ABDOMEN],
            "vessel_damage": "deep",
        },
        "7200002": {  # Burn of skin
            "hemorrhage_risk": "low",
            "typical_locations": [BodyRegion.CHEST, BodyRegion.BACK],
            "vessel_damage": "superficial",
        },
        "2055003": {  # Laceration of hand
            "hemorrhage_risk": "low",
            "typical_locations": [BodyRegion.LEFT_ARM, BodyRegion.RIGHT_ARM],
            "vessel_damage": "moderate",
        },
        "19130008": {  # Traumatic brain injury
            "hemorrhage_risk": "moderate",  # Internal bleeding
            "typical_locations": [BodyRegion.HEAD],
            "vessel_damage": "deep",
        },
        "125605004": {  # Traumatic shock
            "hemorrhage_risk": "high",  # Usually indicates significant blood loss
            "typical_locations": [BodyRegion.CHEST, BodyRegion.ABDOMEN, BodyRegion.PELVIS],
            "vessel_damage": "deep",
        },
        # Non-battle injuries
        "37782003": {  # Fracture
            "hemorrhage_risk": "low",
            "typical_locations": [BodyRegion.LEFT_LEG, BodyRegion.RIGHT_LEG, BodyRegion.LEFT_ARM, BodyRegion.RIGHT_ARM],
            "vessel_damage": "moderate",
        },
        "275272006": {  # Crush injury
            "hemorrhage_risk": "moderate",
            "typical_locations": [BodyRegion.CHEST, BodyRegion.ABDOMEN, BodyRegion.PELVIS],
            "vessel_damage": "deep",
        },
        "409711008": {  # Vehicle accident
            "hemorrhage_risk": "moderate",
            "typical_locations": [BodyRegion.CHEST, BodyRegion.HEAD, BodyRegion.ABDOMEN],
            "vessel_damage": "moderate",
        },
    }

    @classmethod
    def calculate_hemorrhage_profile(
        cls,
        injury_code: str,
        body_region: Optional[BodyRegion] = None,
        severity: str = "Moderate",
        multiple_injuries: bool = False,
    ) -> HemorrhageProfile:
        """
        Calculate hemorrhage profile for a given injury.

        Args:
            injury_code: SNOMED code of the injury
            body_region: Specific body region affected (if None, will be randomly selected)
            severity: Injury severity ("Mild to moderate", "Moderate", "Moderate to severe", "Severe")
            multiple_injuries: Whether patient has multiple injuries

        Returns:
            HemorrhageProfile with all parameters
        """
        # Get injury characteristics
        injury_info = cls.INJURY_HEMORRHAGE_MAP.get(
            injury_code,
            {"hemorrhage_risk": "low", "typical_locations": [BodyRegion.CHEST], "vessel_damage": "superficial"},
        )

        # Determine body region if not specified
        if body_region is None:
            typical_locations = injury_info.get("typical_locations", [BodyRegion.CHEST])
            body_region = random.choice(typical_locations)

        # Get body location details
        body_location = get_body_location(body_region)

        # Determine vessel type based on injury
        vessel_type = get_affected_vessel_type(body_region, injury_info.get("vessel_damage", "moderate"))

        # Determine hemorrhage category
        category = cls._determine_hemorrhage_category(
            injury_info["hemorrhage_risk"], vessel_type, body_region, severity, multiple_injuries
        )

        # Get parameters for this category
        params = cls.HEMORRHAGE_PARAMETERS[category]

        # Calculate specific values within ranges
        if category == HemorrhageCategory.NO_HEMORRHAGE:
            alpha_0 = 0.0
            blood_loss = 0.0
        else:
            # Use severity to position within range
            severity_factor = cls._get_severity_factor(severity)

            alpha_range = params["alpha_0_range"]
            alpha_0 = alpha_range[0] + (alpha_range[1] - alpha_range[0]) * severity_factor

            blood_range = params["blood_loss_ml_min"]
            blood_loss = blood_range[0] + (blood_range[1] - blood_range[0]) * severity_factor

        # Calculate time to exsanguination (5000ml blood, 40% loss = 2000ml)
        if blood_loss > 0:
            time_to_exsanguination = 2000 / blood_loss  # minutes
        else:
            time_to_exsanguination = float("inf")

        return HemorrhageProfile(
            category=category,
            alpha_0=alpha_0,
            k=params["k"],
            body_location=body_location,
            vessel_type=vessel_type,
            controllable=body_location.tourniquetable and vessel_type != VesselType.MAJOR_ARTERY,
            blood_loss_ml_per_min=blood_loss,
            time_to_exsanguination_min=time_to_exsanguination,
        )

    @classmethod
    def _determine_hemorrhage_category(
        cls,
        hemorrhage_risk: str,
        vessel_type: VesselType,
        body_region: BodyRegion,
        severity: str,
        multiple_injuries: bool,
    ) -> HemorrhageCategory:
        """
        Determine hemorrhage category based on injury characteristics.
        """
        # No hemorrhage cases
        if hemorrhage_risk == "low" and severity in ["Mild to moderate", "Moderate"]:
            return HemorrhageCategory.NO_HEMORRHAGE

        # Multiple injuries
        if multiple_injuries and (severity == "Severe" or hemorrhage_risk in ["high", "critical"]):
            return HemorrhageCategory.MULTIPLE_PENETRATING

        # Massive hemorrhage cases
        if vessel_type == VesselType.MAJOR_ARTERY and severity == "Severe":
            return HemorrhageCategory.MASSIVE_HEMORRHAGE
        if hemorrhage_risk == "critical" and severity in ["Severe", "Moderate to severe"]:
            return HemorrhageCategory.MASSIVE_HEMORRHAGE

        # Major limb artery
        if vessel_type == VesselType.LIMB_ARTERY:
            if severity in ["Severe", "Moderate to severe"]:
                return HemorrhageCategory.MAJOR_LIMB_ARTERY
            return HemorrhageCategory.SMALL_LIMB

        # Torso wounds
        if body_region in [BodyRegion.CHEST, BodyRegion.ABDOMEN, BodyRegion.PELVIS]:
            if vessel_type == VesselType.ORGAN or hemorrhage_risk == "high":
                return HemorrhageCategory.TORSO_WOUND

        # Small limb wounds (default for extremities)
        if body_region in [BodyRegion.LEFT_ARM, BodyRegion.RIGHT_ARM, BodyRegion.LEFT_LEG, BodyRegion.RIGHT_LEG]:
            return HemorrhageCategory.SMALL_LIMB

        # Default based on risk
        if hemorrhage_risk == "high":
            return HemorrhageCategory.TORSO_WOUND
        if hemorrhage_risk == "moderate":
            return HemorrhageCategory.SMALL_LIMB
        return HemorrhageCategory.NO_HEMORRHAGE

    @staticmethod
    def _get_severity_factor(severity: str) -> float:
        """Convert severity string to 0-1 factor."""
        severity_map = {"Mild to moderate": 0.25, "Moderate": 0.5, "Moderate to severe": 0.75, "Severe": 1.0}
        return severity_map.get(severity, 0.5)

    @classmethod
    def generate_multiple_hemorrhages(
        cls, injuries: List[Dict], body_regions: Optional[List[BodyRegion]] = None
    ) -> List[HemorrhageProfile]:
        """
        Generate hemorrhage profiles for multiple injuries.

        Args:
            injuries: List of injury dictionaries with 'code' and 'severity'
            body_regions: Optional list of affected body regions

        Returns:
            List of HemorrhageProfile objects
        """
        profiles = []

        # If no body regions specified, distribute injuries
        if body_regions is None:
            body_regions = cls._distribute_injuries_to_regions(len(injuries))

        for i, injury in enumerate(injuries):
            region = body_regions[i] if i < len(body_regions) else None

            profile = cls.calculate_hemorrhage_profile(
                injury_code=injury.get("code", "125670008"),  # Default war injury
                body_region=region,
                severity=injury.get("severity", "Moderate"),
                multiple_injuries=len(injuries) > 1,
            )
            profiles.append(profile)

        return profiles

    @staticmethod
    def _distribute_injuries_to_regions(num_injuries: int) -> List[BodyRegion]:
        """Realistically distribute injuries across body regions."""
        # Common injury patterns in combat
        if num_injuries == 1:
            # Single injuries often to extremities or torso
            return [
                random.choice(
                    [
                        BodyRegion.CHEST,
                        BodyRegion.ABDOMEN,
                        BodyRegion.LEFT_LEG,
                        BodyRegion.RIGHT_LEG,
                        BodyRegion.LEFT_ARM,
                        BodyRegion.RIGHT_ARM,
                    ]
                )
            ]

        if num_injuries == 2:
            # Often bilateral or adjacent regions
            patterns = [
                [BodyRegion.LEFT_LEG, BodyRegion.RIGHT_LEG],  # Bilateral lower
                [BodyRegion.LEFT_ARM, BodyRegion.RIGHT_ARM],  # Bilateral upper
                [BodyRegion.CHEST, BodyRegion.ABDOMEN],  # Torso
                [BodyRegion.CHEST, BodyRegion.LEFT_ARM],  # Mixed
            ]
            return random.choice(patterns)

        # Multiple injuries - blast pattern
        regions = [
            BodyRegion.CHEST,
            BodyRegion.ABDOMEN,
            random.choice([BodyRegion.LEFT_LEG, BodyRegion.RIGHT_LEG]),
            random.choice([BodyRegion.LEFT_ARM, BodyRegion.RIGHT_ARM]),
        ]
        return regions[:num_injuries]
